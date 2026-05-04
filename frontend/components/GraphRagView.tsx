"use client";

import { useEffect, useMemo, useState } from "react";
import { marked } from "marked";
import { useTask } from "./TaskProvider";
import { downloadText, trimTrailingFragment } from "../lib/utils";

const STORAGE_KEY = "graphRagTask";
const STORAGE_DIGEST_KEY = "graphRagDigest";

export default function GraphRagView() {
  const { startTask, getResults } = useTask();
  const [taskId, setTaskId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [cachedDigest, setCachedDigest] = useState<string>("");

  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    const savedDigest = localStorage.getItem(STORAGE_DIGEST_KEY);
    if (savedDigest) {
      setCachedDigest(savedDigest);
    }
    if (saved) {
      try {
        const obj = JSON.parse(saved);
        const ts = obj?.ts || 0;
        const id = obj?.taskId || null;
        const age = Date.now() - ts;
        const sevenDays = 7 * 24 * 60 * 60 * 1000;
        if (!id || age > sevenDays) {
          // start new
          refresh();
        } else {
          setTaskId(id);
        }
      } catch {
        refresh();
      }
    } else {
      refresh();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function refresh() {
    setLoading(true);
    const id = await startTask(["GraphRAG"]);
    if (id) {
      setTaskId(id);
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ taskId: id, ts: Date.now() }));
    }
    setLoading(false);
  }

  const res = taskId ? getResults(taskId) : null;
  useEffect(() => {
    if (res?.digest) {
      setCachedDigest(res.digest);
      localStorage.setItem(STORAGE_DIGEST_KEY, res.digest);
    }
  }, [res]);
  const digestHtml = useMemo(() => {
    const text = res?.digest || cachedDigest || "";
    const cleaned = trimTrailingFragment(text);
    return cleaned ? marked.parse(cleaned) : "";
  }, [res, cachedDigest]);

  const digestText = useMemo(() => {
    const text = res?.digest || cachedDigest || "";
    return trimTrailingFragment(text);
  }, [res, cachedDigest]);

  return (
    <div>
      <header className="page-header">
        <h1 className="title">GraphRAG 每周综述</h1>
        <p className="subtitle">关键词: GraphRAG</p>
      </header>

      <section className="section">
        <button className="button" onClick={refresh} disabled={loading}>{loading ? "刷新中..." : "立即刷新"}</button>
        <button
          className="button"
          onClick={() => {
            if (!digestText) return;
            downloadText(`graphrag-${taskId || "latest"}.md`, digestText, "text/markdown");
          }}
        >
          导出 Markdown
        </button>
      </section>

      <section className="section">
        <h3>最新综述</h3>
        {digestHtml ? (
          <div className="markdown" dangerouslySetInnerHTML={{ __html: digestHtml }} />
        ) : (
          <p className="mono">仍在生成或暂无数据 (任务ID: {taskId || "-"})</p>
        )}
      </section>
    </div>
  );
}
