"use client";

import React from "react";

export default function Sidebar({ selected, onSelect }: { selected: number; onSelect: (n: number) => void }) {
  return (
    <aside className="sidebar">
      <div className="brand">AI Review</div>
      <nav>
        <button className={`nav-item ${selected === 1 ? "active" : ""}`} onClick={() => onSelect(1)}>
          Run & Review
        </button>
        <button className={`nav-item ${selected === 2 ? "active" : ""}`} onClick={() => onSelect(2)}>
          Data & Table
        </button>
        <button className={`nav-item ${selected === 3 ? "active" : ""}`} onClick={() => onSelect(3)}>
          GraphRAG Weekly
        </button>
      </nav>
    </aside>
  );
}
