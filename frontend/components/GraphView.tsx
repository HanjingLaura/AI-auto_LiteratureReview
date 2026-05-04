"use client";

import { useEffect, useMemo, useState } from "react";
import { fetchDiagram } from "../lib/api";

type MermaidApi = {
  initialize: (config: Record<string, unknown>) => void;
  render: (id: string, code: string) => Promise<{ svg: string }>;
};

async function ensureMermaid(): Promise<MermaidApi> {
  const existing = (window as any).mermaid as MermaidApi | undefined;
  if (existing) return existing;
  await new Promise<void>((resolve, reject) => {
    const script = document.createElement("script");
    script.src = "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js";
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Failed to load Mermaid"));
    document.body.appendChild(script);
  });
  const mermaid = (window as any).mermaid as MermaidApi;
  mermaid.initialize({
    startOnLoad: false,
    theme: "base",
    themeVariables: {
      primaryColor: "#ffffff",
      primaryTextColor: "#111111",
      primaryBorderColor: "#111111",
      lineColor: "#444444",
      secondaryColor: "#ffffff",
      secondaryTextColor: "#111111",
      secondaryBorderColor: "#111111",
      tertiaryColor: "#ffffff",
      tertiaryTextColor: "#111111",
      tertiaryBorderColor: "#111111",
      nodeBorder: "#111111",
      mainBkg: "#ffffff",
      edgeLabelBackground: "#ffffff",
      clusterBkg: "#ffffff",
      clusterBorder: "#111111",
      nodeTextColor: "#111111",
      nodeBkg: "#ffffff",
      nodeShadow: "0",
      nodeStrokeWidth: "1",
    },
    themeCSS: `
      .node rect, .node circle, .node ellipse, .node polygon {
        fill: #ffffff !important;
        stroke: #111111 !important;
      }
      .edgePath path, .edgePath marker {
        stroke: #444444 !important;
      }
      .label text, .node text {
        fill: #111111 !important;
      }
      .edgeLabel {
        background: #ffffff !important;
      }
    `,
  });
  return mermaid;
}

export default function GraphView() {
  const [diagramText, setDiagramText] = useState<string>("");
  const [svg, setSvg] = useState<string>("");
  const [error, setError] = useState<string>("");

  useEffect(() => {
    let mounted = true;
    fetchDiagram()
      .then((data) => {
        if (!mounted) return;
        setDiagramText(data?.mermaid || "");
      })
      .catch((err) => {
        if (!mounted) return;
        setError(err?.message || "无法加载流程图");
      });
    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    if (!diagramText) return;
    let cancelled = false;
    ensureMermaid()
      .then((mermaid) => mermaid.render(`graph-${Date.now()}`, diagramText))
      .then((result) => {
        if (!cancelled) setSvg(result.svg);
      })
      .catch((err) => {
        if (!cancelled) setError(err?.message || "流程图渲染失败");
      });
    return () => {
      cancelled = true;
    };
  }, [diagramText]);

  const content = useMemo(() => {
    if (error) return <pre className="mono">{error}</pre>;
    if (!diagramText) return <p className="mono">加载中...</p>;
    if (!svg) return <p className="mono">渲染中...</p>;
    return <div className="diagram" dangerouslySetInnerHTML={{ __html: svg }} />;
  }, [error, diagramText, svg]);

  return (
    <main className="page">
      <header className="page-header">
        <h1 className="title">Workflow Diagram</h1>
        <p className="subtitle">LangGraph flow visualization</p>
      </header>

      <section className="section">
        <div className="diagram-container">
          {content}
        </div>
      </section>
    </main>
  );
}
