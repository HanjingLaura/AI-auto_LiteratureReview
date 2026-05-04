import asyncio
from datetime import datetime
from typing import Dict, Optional
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

import app.graph.workflow as workflow

router = APIRouter(prefix="/api/v1/graph", tags=["graph"])
TASK_STORE: Dict[str, dict] = {}


class GraphRunRequest(BaseModel):
    queries: list[str] = Field(..., description="搜索关键词列表")

# 初始化state
def _build_initial_state(queries: list[str]) -> dict:
    return {
        "queries": queries,
        "iteration_count": 0,
        "current_status": "等待执行",
        "error_log": [],
        "raw_papers": [],
        "paper_cards": [],
        "taxonomy_md": "",
        "comparison_table_csv": "",
        "weekly_digest": ""
    }

# 创建任务
def _create_task_entry(task_id: str, queries: list[str]) -> None:
    now = datetime.utcnow().isoformat() + "Z"
    TASK_STORE[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "current_status": "等待执行",
        "queries": queries,
        "result": None,
        "error": None,
        "created_at": now,
        "updated_at": now,
    }

# 更新任务状态
def _update_task_status(
    task_id: str,
    status: str,
    result: Optional[dict] = None,
    error: Optional[str] = None,
    current_status: Optional[str] = None,
) -> None:
    task = TASK_STORE.get(task_id)
    if not task:
        return
    task["status"] = status
    task["updated_at"] = datetime.utcnow().isoformat() + "Z"
    task["result"] = result if result is not None else task.get("result")
    task["error"] = error
    if current_status is not None:
        task["current_status"] = current_status


async def _execute_task(task_id: str, initial_state: dict) -> None:
    _update_task_status(task_id, "running", current_status="执行中")
    try:
        def _run_with_stream() -> dict:
            final_state: Optional[dict] = None
            try:
                for state in workflow.app.stream(initial_state, stream_mode="values"):
                    if isinstance(state, dict):
                        current_status = state.get("current_status")
                        if current_status:
                            _update_task_status(task_id, "running", current_status=current_status)
                        final_state = state
            except Exception:
                final_state = None

            if final_state is None:
                final_state = workflow.app.invoke(initial_state)
            return final_state

        result = await asyncio.to_thread(_run_with_stream)
        _update_task_status(
            task_id,
            "completed",
            result=result,
            current_status=(result or {}).get("current_status", "完成"),
        )
    except Exception as exc:
        _update_task_status(task_id, "failed", error=str(exc), current_status="执行失败")

# 启动 Graph 工作流
@router.post("/run")
async def run_graph_task(body: GraphRunRequest, background_tasks: BackgroundTasks):
    task_id = uuid4().hex
    _create_task_entry(task_id, body.queries)
    background_tasks.add_task(_execute_task, task_id, _build_initial_state(body.queries))
    return {"success": True, "task_id": task_id, "status": "pending"}

# 获取任务状态
@router.get("/status")
async def get_graph_status(task_id: str):
    task = TASK_STORE.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="找不到对应任务")
    return {
        "success": True,
        "task_id": task_id,
        "status": task["status"],
        "current_status": task.get("current_status"),
        "created_at": task["created_at"],
        "updated_at": task["updated_at"],
        "error": task["error"],
    }

# 获取原始论文元数据
@router.get("/raw-papers")
async def get_raw_papers(task_id: str):
    task = TASK_STORE.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="找不到对应任务")
    if task["status"] != "completed":
        return {"success": False, "status": task["status"], "raw_papers": []}
    return {"success": True, "raw_papers": task["result"].get("raw_papers", [])}

# 获取结构化 JSON 论文卡片
@router.get("/paper-cards")
async def get_paper_cards(task_id: str):
    task = TASK_STORE.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="找不到对应任务")
    if task["status"] != "completed":
        return {"success": False, "status": task["status"], "paper_cards": []}
    return {"success": True, "paper_cards": task["result"].get("paper_cards", [])}

# 获取分类 Markdown 和对比 CSV
@router.get("/analysis")
async def get_analysis(task_id: str):
    task = TASK_STORE.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="找不到对应任务")
    if task["status"] != "completed":
        return {
            "success": False,
            "status": task["status"],
            "taxonomy_md": "",
            "comparison_table_csv": ""
        }
    result = task["result"] or {}
    taxonomy_md = result.get("taxonomy_md", "")
    comparison_table_csv = result.get("comparison_table_csv", "")
    if not taxonomy_md and not comparison_table_csv:
        return {
            "success": False,
            "status": task["status"],
            "taxonomy_md": taxonomy_md,
            "comparison_table_csv": comparison_table_csv,
            "message": "分析结果为空，请检查 LLM 调用或节点输出",
            "error_log": result.get("error_log", [])
        }
    return {
        "success": True,
        "taxonomy_md": taxonomy_md,
        "comparison_table_csv": comparison_table_csv
    }

# 获取最终综述论文
@router.get("/digest")
async def get_digest(task_id: str):
    task = TASK_STORE.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="找不到对应任务")
    if task["status"] != "completed":
        return {"success": False, "status": task["status"], "weekly_digest": ""}
    weekly_digest = task["result"].get("weekly_digest", "")
    if not weekly_digest:
        return {
            "success": False,
            "status": task["status"],
            "weekly_digest": weekly_digest,
            "message": "最终综述为空，请检查 LLM 输出或模型调用结果",
            "error_log": task["result"].get("error_log", [])
        }
    return {"success": True, "weekly_digest": weekly_digest}

# 获取完整任务结果
@router.get("/result")
async def get_result(task_id: str):
    task = TASK_STORE.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="找不到对应任务")
    return {
        "success": True,
        "task_id": task_id,
        "status": task["status"],
        "result": task["result"],
        "error": task["error"],
        "error_log": (task["result"] or {}).get("error_log", [])
    }

# 获取 LangGraph 流程图
@router.get("/diagram")
async def get_graph_diagram():
    try:
        graph = workflow.app.get_graph(xray=True)
        mermaid = graph.draw_mermaid()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"工作流图生成失败: {exc}")
    return {"success": True, "mermaid": mermaid}