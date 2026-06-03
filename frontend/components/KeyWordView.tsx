"use client";

import { useEffect, useMemo, useState } from "react";
import { marked } from "marked";
import { useTask } from "./TaskProvider";
import { downloadText, trimTrailingFragment } from "../lib/utils";

const STORAGE_KEY = "graphRagTask";
const STORAGE_DIGEST_KEY = "graphRagDigest";
const STORAGE_KEYWORD_KEY = "graphRagKeyword";
const DEFAULT_KEYWORD = "GraphRAG";
const SCHEDULE_DAY = 1; // Monday (Beijing)
const SCHEDULE_HOUR = 8; // 08:00 Beijing
const BEIJING_OFFSET_MS = 8 * 60 * 60 * 1000;

function normalizeKeyword(value: string) {
  return value.trim();
}

function getWeekdayAtHourBeijing(nowMs: number, weekday: number, hour: number) {
  const beijingNow = new Date(nowMs + BEIJING_OFFSET_MS);
  const day = beijingNow.getUTCDay();
  const diff = (day - weekday + 7) % 7;
  const scheduled = new Date(beijingNow);
  scheduled.setUTCDate(scheduled.getUTCDate() - diff);
  scheduled.setUTCHours(hour, 0, 0, 0);
  return scheduled.getTime() - BEIJING_OFFSET_MS;
}

function shouldAutoRefresh(nowMs: number, lastTs?: number) {
  const scheduledTs = getWeekdayAtHourBeijing(nowMs, SCHEDULE_DAY, SCHEDULE_HOUR);
  if (nowMs < scheduledTs) return false;
  if (!lastTs) return true;
  return lastTs < scheduledTs;
}

export default function KeyWordView() {
  const { startTask, getResults } = useTask();
  const [taskId, setTaskId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [cachedDigest, setCachedDigest] = useState<string>("");
  const [keyword, setKeyword] = useState(DEFAULT_KEYWORD);
  const [editingKeyword, setEditingKeyword] = useState(false);

  useEffect(() => {
    const savedKeyword = localStorage.getItem(STORAGE_KEYWORD_KEY);
    const initialKeyword = normalizeKeyword(savedKeyword || DEFAULT_KEYWORD) || DEFAULT_KEYWORD;
    setKeyword(initialKeyword);

    const saved = localStorage.getItem(STORAGE_KEY);
    const savedDigest = localStorage.getItem(STORAGE_DIGEST_KEY);
    if (savedDigest) {
      setCachedDigest(savedDigest);
    }
    const nowMs = Date.now();
    if (saved) {
      try {
        const obj = JSON.parse(saved);
        const ts = Number(obj?.ts) || 0;
        const id = obj?.taskId || null;
        if (!id) {
          refresh(initialKeyword);
          return;
        }
        if (shouldAutoRefresh(nowMs, ts)) {
          refresh(initialKeyword);
          return;
        }
        setTaskId(id);
      } catch {
        refresh(initialKeyword);
      }
    } else {
      refresh(initialKeyword);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function refresh(overrideKeyword?: string) {
    const query = normalizeKeyword(overrideKeyword ?? keyword);
    if (!query) return;
    setLoading(true);
    const id = await startTask([query]);
    if (id) {
      setTaskId(id);
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ taskId: id, ts: Date.now() }));
      localStorage.setItem(STORAGE_KEYWORD_KEY, query);
    }
    setLoading(false);
  }

  async function applyKeyword() {
    const nextKeyword = normalizeKeyword(keyword);
    if (!nextKeyword) return;
    setKeyword(nextKeyword);
    setEditingKeyword(false);
    setCachedDigest("");
    localStorage.setItem(STORAGE_KEYWORD_KEY, nextKeyword);
    localStorage.removeItem(STORAGE_DIGEST_KEY);
    await refresh(nextKeyword);
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
        <h1 className="title">{keyword} 每周综述</h1>
        <div className="subtitle" style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
          <span>关键词: {keyword}</span>
          {!editingKeyword && (
            <button
              className="button"
              type="button"
              onClick={() => {
                setEditingKeyword(true);
              }}
            >
              更改关键词
            </button>
          )}
        </div>
        {editingKeyword && (
          <div className="input-row">
            <input
              className="input"
              value={keyword}
              onChange={(event) => setKeyword(event.target.value)}
              placeholder="输入关键词"
            />
            <button className="button" type="button" onClick={applyKeyword}>确认</button>
          </div>
        )}
      </header>

      <section className="section">
        <button className="button" onClick={() => refresh()} disabled={loading}>{loading ? "刷新中..." : "立即刷新"}</button>
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
