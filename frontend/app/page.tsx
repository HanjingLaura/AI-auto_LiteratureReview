"use client";

import { useState } from "react";
import { TaskProvider } from "../components/TaskProvider";
import Sidebar from "../components/Sidebar";
import RunConsole from "../components/RunConsole";
import PapersView from "../components/PapersView";
import GraphRagView from "../components/GraphRagView";

export default function Page() {
  const [tab, setTab] = useState<number>(1);

  return (
    <TaskProvider>
      <div className="app-shell">
        <Sidebar selected={tab} onSelect={setTab} />
        <main className="main-content">
          {tab === 1 && <RunConsole />}
          {tab === 2 && <PapersView />}
          {tab === 3 && <GraphRagView />}
        </main>
      </div>
    </TaskProvider>
  );
}
