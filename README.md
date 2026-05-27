 # AI-auto_LiteratureReview

 基于 LangGraph 的自动化文献综述系统，负责论文抓取、结构化提取、聚类/对比分析以及每周综述报告生成。

 ## 技术栈

 - 后端：FastAPI、LangGraph、OpenAI SDK、Pydantic
 - 前端：Next.js（App Router）、React、TypeScript、marked（Markdown 渲染）
 - 数据来源：arXiv API；输出格式包含 CSV、Markdown、JSON

 ## 项目结构（概览）

 - backend：API 服务与 LangGraph 工作流节点实现
 - frontend：Next.js Web 前端（任务控制、结果预览与导出）

 ## 快速开始

 ### 后端

 1. 创建 Python 虚拟环境并安装依赖：

 ```powershell
 cd backend
 pip install -r requirements.txt
 ```

 2. 配置环境变量（示例）：

 ```powershell
 # 请替换为你的实际密钥与地址
 $env:API_KEY = "your-api-key"
 $env:BASE_URL = "https://api.openai.com/v1"
 $env:MODEL_NAME = "gpt-4o-mini"
 ```

 3. 启动后端服务：

 ```powershell
 uvicorn main:app --reload --host 0.0.0.0 --port 8000
 ```

 ### 前端

 ```powershell
 cd frontend
 npm install
 npm run dev
 ```

 然后在浏览器打开 http://localhost:3000

 ## 运行与配置说明

 - 使用本地或远端 LLM：
	 - 若需使用本地模型，设置 `USE_LOCAL_LLM=true`，并提供 `LOCAL_API_KEY`、`LOCAL_BASE_URL`、`LOCAL_MODEL_NAME`。
 - 后端任务执行：
	 - POST `/api/v1/graph/run` 启动任务，返回 `task_id`。
	 - GET `/api/v1/graph/status?task_id=...` 可轮询获取 `current_status` 与任务进度。
	 - 任务完成后可通过 `/raw-papers`、`/paper-cards`、`/analysis`、`/digest` 获取产出。
 - 前端已实现：任务启动、轮询状态、展示/导出 JSON/CSV/Markdown、以及流程图渲染。