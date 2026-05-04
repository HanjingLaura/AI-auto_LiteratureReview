"use client";

import React, { useEffect, useMemo, useState } from "react";
import { marked } from "marked";
import { useTask } from "./TaskProvider";

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
    if (!text) return "";
    const trimmed = text.trim();
    const lastChar = trimmed[trimmed.length - 1];
    if (/[。.!?！？]$/.test(lastChar)) return marked.parse(trimmed);
    const lastStop = Math.max(
      trimmed.lastIndexOf("。"),
      trimmed.lastIndexOf("."),
      trimmed.lastIndexOf("!"),
      trimmed.lastIndexOf("?"),
      trimmed.lastIndexOf("！"),
      trimmed.lastIndexOf("？")
    );
    const cleaned = lastStop > 0 ? trimmed.slice(0, lastStop + 1) : trimmed;
    return marked.parse(cleaned);
  }, [res, cachedDigest]);

  const digestText = useMemo(() => {
    const text = res?.digest || cachedDigest || "";
    if (!text) return "";
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
    return lastStop > 0 ? trimmed.slice(0, lastStop + 1) : trimmed;
  }, [res, cachedDigest]);

  return (
    <div>
      <header className="header">
        <h2>GraphRAG 每周综述</h2>
        <p className="mono">关键词: GraphRAG</p>
      </header>

      <section className="section">
        <button className="button" onClick={refresh} disabled={loading}>{loading ? "刷新中..." : "立即刷新"}</button>
        <button
          className="button"
          onClick={() => {
            if (!digestText) return;
            const blob = new Blob([digestText], { type: "text/markdown" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `graphrag-${taskId || "latest"}.md`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(url);
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
