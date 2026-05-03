"use client";

import { useEffect, useMemo, useState } from "react";
import { marked } from "marked";
import { fetchAnalysis, fetchDigest, fetchPaperCards, fetchStatus, runTask } from "../lib/api";

type PaperCard = {
  title?: string;
  problem?: string;
  key_idea?: string;
  method?: string;
  dataset_or_scenario?: string;
  metrics?: string;
  results_summary?: string;
  innovation_type?: string;
  limitations?: string;
  best_fit_category?: string;
  confidence_level?: number;
  [key: string]: unknown;
};

type StatusPayload = {
  status?: string;
  current_status?: string;
  error?: string | null;
};

function parseCsv(text: string): string[][] {
  if (!text.trim()) return [];
  const rows: string[][] = [];
  let row: string[] = [];
  let cell = "";
  let inQuotes = false;

  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];
    const next = text[i + 1];

    if (char === '"') {
      if (inQuotes && next === '"') {
        cell += '"';
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
      continue;
    }

    if (char === "," && !inQuotes) {
      row.push(cell);
      cell = "";
      continue;
    }

    if ((char === "\n" || char === "\r") && !inQuotes) {
      if (cell.length || row.length) {
        row.push(cell);
        rows.push(row);
      }
      cell = "";
      row = [];
      if (char === "\r" && next === "\n") i += 1;
      continue;
    }

    cell += char;
  }

  if (cell.length || row.length) {
    row.push(cell);
    rows.push(row);
  }

  return rows;
}

function statusProgress(status: string): number {
  if (status === "pending") return 10;
  if (status === "running") return 60;
  if (status === "completed") return 100;
  if (status === "failed") return 100;
  return 0;
}

export default function HomePage() {
  const [taskId, setTaskId] = useState<string | null>(null);
  const [status, setStatus] = useState<string>("idle");
  const [currentStatus, setCurrentStatus] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [paperCards, setPaperCards] = useState<PaperCard[]>([]);
  const [taxonomyMd, setTaxonomyMd] = useState<string>("");
  const [comparisonCsv, setComparisonCsv] = useState<string>("");
  const [digest, setDigest] = useState<string>("");

  const progress = useMemo(() => statusProgress(status), [status]);
  const taxonomyHtml = useMemo(() => (taxonomyMd ? marked.parse(taxonomyMd) : ""), [taxonomyMd]);
  const digestHtml = useMemo(() => (digest ? marked.parse(digest) : ""), [digest]);
  const csvRows = useMemo(() => parseCsv(comparisonCsv), [comparisonCsv]);

  useEffect(() => {
    if (!taskId) return;
    setError(null);
    setIsRunning(true);

    const timer = setInterval(async () => {
      try {
        const data = (await fetchStatus(taskId)) as StatusPayload;
        if (!data) return;
        const nextStatus = data.status || "unknown";
        setStatus(nextStatus);
        setCurrentStatus(data.current_status || "");

        if (nextStatus === "completed") {
          clearInterval(timer);
          const [cards, analysis, summary] = await Promise.all([
            fetchPaperCards(taskId),
            fetchAnalysis(taskId),
            fetchDigest(taskId),
          ]);
          setPaperCards(cards?.paper_cards || []);
          setTaxonomyMd(analysis?.taxonomy_md || "");
          setComparisonCsv(analysis?.comparison_table_csv || "");
          setDigest(summary?.weekly_digest || "");
          setIsRunning(false);
        }

        if (nextStatus === "failed") {
          clearInterval(timer);
          setIsRunning(false);
          setError(data.error || "任务执行失败");
        }
      } catch (err: any) {
        clearInterval(timer);
        setIsRunning(false);
        setError(err?.message || "任务状态获取失败");
      }
    }, 1500);

    return () => clearInterval(timer);
  }, [taskId]);

  const handleRun = async (queries: string[]) => {
    setStatus("pending");
    setError(null);
    setPaperCards([]);
    setTaxonomyMd("");
    setComparisonCsv("");
    setDigest("");
    setCurrentStatus("");

    const data = await runTask(queries);
    if (!data?.task_id) {
      setError(data?.message || "任务创建失败");
      return;
    }
    setTaskId(data.task_id);
    setStatus(data.status || "pending");
  };

  return (
    <main className="page">
      <header className="header">
        <div>
          <p className="eyebrow">AI Literature Review</p>
          <h1 className="title">Graph Pipeline Console</h1>
        </div>
        <p className="subtitle">Minimal interface for your LangGraph workflow.</p>
      </header>

      <section className="panel">
        <form className="section" onSubmit={(event) => {
          event.preventDefault();
          const form = event.currentTarget;
          const input = form.querySelector("input");
          const value = (input?.value || "").toString();
          const queries = value
            .split(",")
            .map((item) => item.trim())
            .filter(Boolean);
          if (queries.length === 0) return;
          handleRun(queries);
        }}>
          <h2>关键词</h2>
          <div className="input-row">
            <input
              className="input"
              placeholder="graph neural network, knowledge graph"
              defaultValue=""
              disabled={isRunning}
            />
            <button className="button" type="submit" disabled={isRunning}>
              {isRunning ? "运行中" : "开始分析"}
            </button>
          </div>
        </form>

        <section className="section">
          <h2>任务状态</h2>
          <div className="grid">
            <div>
              <p className="eyebrow">Task ID</p>
              <p className="mono">{taskId || "-"}</p>
            </div>
            <div>
              <p className="eyebrow">Status</p>
              <p className="badge">{currentStatus || status || "idle"}</p>
            </div>
          </div>
          <div className="progress">
            <div className="progress-bar" style={{ width: `${progress}%` }} />
          </div>
          {currentStatus ? <p className="mono">{currentStatus}</p> : null}
          {error ? <p className="mono">{error}</p> : null}
        </section>
      </section>

      <section className="grid">
        <div className="section">
          <h2>分类体系 (Markdown)</h2>
          {taxonomyHtml ? (
            <div className="markdown" dangerouslySetInnerHTML={{ __html: taxonomyHtml }} />
          ) : (
            <p className="mono">-</p>
          )}
        </div>

        <div className="section">
          <h2>综述报告 (Markdown)</h2>
          {digestHtml ? (
            <div className="markdown" dangerouslySetInnerHTML={{ __html: digestHtml }} />
          ) : (
            <p className="mono">-</p>
          )}
        </div>

        <div className="section">
          <h2>方法对比 CSV</h2>
          {csvRows.length > 0 ? (
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    {csvRows[0].map((cell, index) => (
                      <th key={`h-${index}`}>{cell || "-"}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {csvRows.slice(1).map((row, rowIndex) => (
                    <tr key={`r-${rowIndex}`}>
                      {row.map((cell, cellIndex) => (
                        <td key={`c-${rowIndex}-${cellIndex}`}>{cell || "-"}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="mono">-</p>
          )}
        </div>

        <div className="section">
          <h2>论文卡片</h2>
          {paperCards.length === 0 ? (
            <p className="mono">-</p>
          ) : (
            <div className="card-grid">
              {paperCards.map((card, index) => (
                <article className="card" key={`${card.title || "card"}-${index}`}>
                  <h3>{card.title || `Paper ${index + 1}`}</h3>
                  <dl>
                    <dt>Problem</dt>
                    <dd>{card.problem || "-"}</dd>
                    <dt>Key idea</dt>
                    <dd>{card.key_idea || "-"}</dd>
                    <dt>Method</dt>
                    <dd>{card.method || "-"}</dd>
                    <dt>Dataset/Scenario</dt>
                    <dd>{card.dataset_or_scenario || "-"}</dd>
                    <dt>Metrics</dt>
                    <dd>{card.metrics || "-"}</dd>
                    <dt>Results</dt>
                    <dd>{card.results_summary || "-"}</dd>
                    <dt>Innovation type</dt>
                    <dd>{card.innovation_type || "-"}</dd>
                    <dt>Limitations</dt>
                    <dd>{card.limitations || "-"}</dd>
                    <dt>Best fit category</dt>
                    <dd>{card.best_fit_category || "-"}</dd>
                    <dt>Confidence</dt>
                    <dd>{card.confidence_level ?? "-"}</dd>
                  </dl>
                </article>
              ))}
            </div>
          )}
        </div>
      </section>
    </main>
  );
}
