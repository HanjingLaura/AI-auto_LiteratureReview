"use client";

import { useState, useMemo } from "react";
import { marked } from "marked";
import { useTask } from "./TaskProvider";

function trimTrailingFragment(text: string): string {
  if (!text) return text;
  const trimmed = text.trim();
  const lastChar = trimmed[trimmed.length - 1];
  if (/[。.!?！？]$/.test(lastChar)) return trimmed;
  const lastStop = Math.max(
    trimmed.lastIndexOf("。"),
    trimmed.lastIndexOf("."),
    trimmed.lastIndexOf("!"),
    trimmed.lastIndexOf("?"),
    trimmed.lastIndexOf("！"),
    trimmed.lastIndexOf("？")
  );
  if (lastStop > 0) return trimmed.slice(0, lastStop + 1);
  return trimmed;
}

export default function RunConsole() {
  const { startTask, latestTaskId, getResults } = useTask();
  const [input, setInput] = useState("");
  const [runningTask, setRunningTask] = useState<string | null>(null);

  const result = runningTask ? getResults(runningTask) : latestTaskId ? getResults(latestTaskId) : null;

  const progressDetail = useMemo(() => {
    const s = result?.status || "idle";
    const curRaw = result?.current_status || "";
    const cur = curRaw.toLowerCase();
    const pctMatch = cur.match(/(\d{1,3})%/);
    if (pctMatch) {
      return { pct: Math.min(100, Math.max(0, parseInt(pctMatch[1], 10))), label: "进度" };
    }

    const stages: Array<{ keys: string[]; label: string; pct: number }> = [
      { keys: ["等待执行", "等待"], label: "等待执行", pct: 5 },
      { keys: ["正在抓取关键词", "抓取成功"], label: "抓取论文", pct: 25 },
      { keys: ["正在解析论文", "结构化解析", "完成结构化解析"], label: "解析论文", pct: 50 },
      { keys: ["聚类分析跳过"], label: "聚类分析跳过", pct: 75 },
      { keys: ["分类体系与方法对比表已生成", "聚类分析"], label: "分类/对比", pct: 80 },
      { keys: ["综述报告生成完毕"], label: "综述生成", pct: 100 },
    ];

    for (const stage of stages) {
      if (stage.keys.some((k) => curRaw.includes(k) || cur.includes(k.toLowerCase()))) {
        return { pct: stage.pct, label: stage.label };
      }
    }

    if (cur.includes("综述报告生成完毕")) return { pct: 100, label: "综述生成" };
    if (s === "completed" || cur.includes("完成") || cur.includes("complete")) return { pct: 100, label: "完成" };
    if (s === "failed" || cur.includes("失败") || cur.includes("error")) return { pct: 100, label: "失败" };
    if (s === "running" || cur.includes("执行") || cur.includes("running")) return { pct: 60, label: "执行中" };
    if (s === "pending") return { pct: 10, label: "等待执行" };
    return { pct: 0, label: "未开始" };
  }, [result]);

  const digestHtml = useMemo(() => {
    const cleaned = trimTrailingFragment(result?.digest || "");
    return cleaned ? marked.parse(cleaned) : "";
  }, [result]);
  const history = result?.statusHistory || [];

  async function handleRun(e?: React.FormEvent) {
    if (e) e.preventDefault();
    const queries = input
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    if (queries.length === 0) return;
    const id = await startTask(queries);
    if (id) setRunningTask(id);
  }

  return (
    <main className="page">
      <header className="page-header">
        <h1 className="title">AI Literature Review</h1>
        <p className="subtitle">Automated Literature Review System Based on LangGraph</p>
      </header>

      <section className="panel">
        <form className="section" onSubmit={handleRun}>
          <h2>关键词</h2>
          <div className="input-row">
            <input className="input" placeholder="graph neural network, knowledge graph" value={input} onChange={(e) => setInput(e.target.value)} />
            <button className="button" type="submit">开始分析</button>
          </div>
        </form>

        <section className="section">
          <h2>任务状态</h2>
          <div className="grid">
            <div>
              <p className="eyebrow">Task ID</p>
              <p className="mono">{runningTask || latestTaskId || "-"}</p>
            </div>
          </div>
          <div className="progress">
            <div className="progress-bar" style={{ width: `${progressDetail.pct}%` }} />
          </div>
          <div className="progress-meta">
            <span className="badge">{progressDetail.label}</span>
            <span className="mono">{progressDetail.pct}%</span>
          </div>
          {result?.current_status ? <p className="mono">{result.current_status}</p> : null}
          {history.length > 0 ? (
            <div className="status-steps">
              {history.map((item, index) => (
                <div key={`${item}-${index}`} className={`status-step ${index === history.length - 1 ? "active" : ""}`}>
                  <span className="step-index">{index + 1}</span>
                  <span className="step-text">{item}</span>
                </div>
              ))}
            </div>
          ) : null}
          {result?.error ? <p className="mono">{result.error}</p> : null}
        </section>
      </section>

      <section className="section">
        <h2>综述报告 (Markdown)</h2>
        {digestHtml ? (
          <div className="markdown" dangerouslySetInnerHTML={{ __html: digestHtml }} />
        ) : (
          <p className="mono">-</p>
        )}
      </section>
    </main>
  );
}
