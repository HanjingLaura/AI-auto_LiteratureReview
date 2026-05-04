"use client";

import React, { useMemo } from "react";
import { marked } from "marked";
import { useTask } from "./TaskProvider";

function download(filename: string, content: string, type = "text/plain") {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

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

function normalizeRows(rows: string[][]): string[][] {
  if (rows.length === 0) return rows;
  const headerLen = rows[0].length;
  return rows.map((row, idx) => {
    if (idx === 0) return row;
    if (row.length === headerLen) return row;
    if (row.length < headerLen) return [...row, ...Array(headerLen - row.length).fill("")];
    if (headerLen === 6 && row.length > 6) {
      const last = (row[row.length - 1] || "").trim();
      const lastLower = last.toLowerCase();
      const isBool = ["是", "否", "yes", "no", "true", "false", "1", "0"].includes(lastLower) || ["是", "否"].includes(last);
      if (isBool) {
        const head = row.slice(0, 4);
        const prosCons = row.slice(4, -1).join(", ");
        return [...head, prosCons, row[row.length - 1]];
      }
    }
    const head = row.slice(0, headerLen - 1);
    const tail = row.slice(headerLen - 1).join(", ");
    return [...head, tail];
  });
}

function limitLines(text: string, maxLines: number): string {
  if (!text) return "";
  const lines = text.split(/\r?\n/);
  return lines.slice(0, maxLines).join("\n");
}

export default function PapersView() {
  const { latestTaskId, getResults } = useTask();
  const taskId = latestTaskId;
  const res = taskId ? getResults(taskId) : null;
  const previewMeta = useMemo(() => (res?.rawPapers || []).slice(0, 5), [res]);
  const fullMeta = useMemo(() => res?.rawPapers || [], [res]);
  const previewCards = useMemo(() => (res?.paperCards || []).slice(0, 5), [res]);
  const fullCards = useMemo(() => res?.paperCards || [], [res]);
  const metaJsonPreview = useMemo(() => JSON.stringify(previewMeta, null, 2), [previewMeta]);
  const metaJsonExport = useMemo(() => JSON.stringify(fullMeta, null, 2), [fullMeta]);
  const cardsJsonPreview = useMemo(() => JSON.stringify(previewCards, null, 2), [previewCards]);
  const cardsJsonExport = useMemo(() => JSON.stringify(fullCards, null, 2), [fullCards]);

  const taxonomyPreview = useMemo(() => limitLines(res?.taxonomyMd || "", 5), [res]);
  const taxonomyExport = useMemo(() => res?.taxonomyMd || "", [res]);
  const taxonomyHtml = useMemo(() => (taxonomyPreview ? marked.parse(taxonomyPreview) : ""), [taxonomyPreview]);

  const rawRows = useMemo(() => parseCsv(res?.comparisonCsv || ""), [res]);
  const csvRows = useMemo(() => normalizeRows(rawRows), [rawRows]);
  const csvPreviewRows = useMemo(() => (csvRows.length > 0 ? csvRows.slice(0, 1 + 5) : []), [csvRows]);
  const csvExportText = useMemo(() => {
    if (!csvRows.length) return "";
    return csvRows.map((row) => row.map((cell) => {
      const safe = cell ?? "";
      if (/[",\n\r]/.test(safe)) {
        return `"${safe.replace(/"/g, '""')}"`;
      }
      return safe;
    }).join(",")).join("\n");
  }, [csvRows]);

  return (
    <div>
      <header className="header">
        <h2>论文数据与导出</h2>
      </header>

      <section className="section">
        <h3>论文元数据 (JSON)</h3>
        {previewMeta.length > 0 ? (
          <pre className="mono code-block">{metaJsonPreview}</pre>
        ) : (
          <p className="mono">-</p>
        )}
        <button
          className="button"
          onClick={() => download(`metadata-${taskId || "none"}.json`, metaJsonExport, "application/json")}
        >
          下载 JSON
        </button>
      </section>

      <section className="section">
        <h3>论文卡片 (JSON)</h3>
        {previewCards.length > 0 ? (
          <pre className="mono code-block">{cardsJsonPreview}</pre>
        ) : (
          <p className="mono">-</p>
        )}
        <button
          className="button"
          onClick={() => download(`paper-cards-${taskId || "none"}.json`, cardsJsonExport, "application/json")}
        >
          下载 JSON
        </button>
      </section>

      <section className="section">
        <h3>分类体系 (MD)</h3>
        {taxonomyHtml ? (
          <div className="markdown" dangerouslySetInnerHTML={{ __html: taxonomyHtml }} />
        ) : (
          <p className="mono">-</p>
        )}
        <button
          className="button"
          onClick={() => download(`taxonomy-${taskId || "none"}.md`, taxonomyExport, "text/markdown")}
        >
          下载 MD
        </button>
      </section>

      <section className="section">
        <h3>方法对比 (CSV)</h3>
        {csvPreviewRows.length > 0 ? (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  {csvPreviewRows[0].map((cell, index) => (
                    <th key={`h-${index}`}>{cell || "-"}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {csvPreviewRows.slice(1).map((row, rowIndex) => (
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
        <button
          className="button"
          onClick={() => download(`comparison-${taskId || "none"}.csv`, csvExportText, "text/csv")}
        >
          下载 CSV
        </button>
      </section>
    </div>
  );
}
