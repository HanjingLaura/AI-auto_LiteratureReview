"use client";

import { createContext, useContext, useState } from "react";
import { runTask as apiRunTask, fetchStatus as apiFetchStatus, fetchPaperCards, fetchRawPapers, fetchAnalysis, fetchDigest } from "../lib/api";

type ResultSet = {
  rawPapers: any[];
  paperCards: any[];
  taxonomyMd: string;
  comparisonCsv: string;
  digest: string;
  status: string;
  current_status?: string;
  statusHistory?: string[];
  error?: string | null;
};

type TaskContextType = {
  startTask: (queries: string[]) => Promise<string | null>;
  getResults: (taskId: string) => ResultSet | null;
  latestTaskId: string | null;
};

const TaskContext = createContext<TaskContextType | null>(null);

export function TaskProvider({ children }: { children: React.ReactNode }) {
  const [latestTaskId, setLatestTaskId] = useState<string | null>(null);
  const [resultsMap, setResultsMap] = useState<Record<string, ResultSet>>({});

  function updateHistory(prev: ResultSet | undefined, current_status: string) {
    if (!current_status) return prev?.statusHistory || [];
    const prevHistory = prev?.statusHistory || [];
    if (prevHistory[prevHistory.length - 1] === current_status) return prevHistory;
    const next = [...prevHistory, current_status];
    return next.length > 8 ? next.slice(-8) : next;
  }

  async function startTask(queries: string[]) {
    try {
      const data = await apiRunTask(queries);
      const taskId = data?.task_id;
      if (!taskId) return null;
      setLatestTaskId(taskId);

      // start polling for this task
      const timer = setInterval(async () => {
        try {
          const s = await apiFetchStatus(taskId);
          const status = s?.status || "unknown";
          const current_status = s?.current_status || "";

          if (status === "completed" || status === "failed") {
            clearInterval(timer);
            if (status === "completed") {
              const [raw, cards, analysis, summary] = await Promise.all([
                fetchRawPapers(taskId),
                fetchPaperCards(taskId),
                fetchAnalysis(taskId),
                fetchDigest(taskId),
              ]);
              setResultsMap((m) => {
                const prev = m[taskId];
                return {
                  ...m,
                  [taskId]: {
                    rawPapers: raw?.raw_papers || [],
                    paperCards: cards?.paper_cards || [],
                    taxonomyMd: analysis?.taxonomy_md || "",
                    comparisonCsv: analysis?.comparison_table_csv || "",
                    digest: summary?.weekly_digest || "",
                    status,
                    current_status,
                    statusHistory: updateHistory(prev, current_status),
                  },
                };
              });
            } else {
              setResultsMap((m) => {
                const prev = m[taskId];
                return {
                  ...m,
                  [taskId]: {
                    rawPapers: [],
                    paperCards: [],
                    taxonomyMd: "",
                    comparisonCsv: "",
                    digest: "",
                    status,
                    current_status,
                    statusHistory: updateHistory(prev, current_status),
                    error: s?.error || "failed",
                  },
                };
              });
            }
          } else {
            setResultsMap((m) => {
              const prev = m[taskId];
              return {
                ...m,
                [taskId]: {
                  ...(prev || {
                    rawPapers: [],
                    paperCards: [],
                    taxonomyMd: "",
                    comparisonCsv: "",
                    digest: "",
                  }),
                  status,
                  current_status,
                  statusHistory: updateHistory(prev, current_status),
                },
              };
            });
          }
        } catch (e) {
          clearInterval(timer);
          setResultsMap((m) => ({
            ...m,
            [taskId]: {
              rawPapers: [],
              paperCards: [],
              taxonomyMd: "",
              comparisonCsv: "",
              digest: "",
              status: "failed",
              current_status: "",
              error: (e as any)?.message || "poll error",
            },
          }));
        }
      }, 4000);

      return taskId;
    } catch (e) {
      return null;
    }
  }

  function getResults(taskId: string) {
    return resultsMap[taskId] || null;
  }

  return (
    <TaskContext.Provider value={{ startTask, getResults, latestTaskId }}>
      {children}
    </TaskContext.Provider>
  );
}

export function useTask() {
  const ctx = useContext(TaskContext);
  if (!ctx) throw new Error("useTask must be used within TaskProvider");
  return ctx;
}
