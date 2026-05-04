const BASE_URL = "http://localhost:8000";

async function request(path: string, options?: RequestInit) {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || response.statusText);
  }
  return response.json();
}

export function runTask(queries: string[]) {
  return request("/api/v1/graph/run", {
    method: "POST",
    body: JSON.stringify({ queries }),
  });
}

export function fetchStatus(taskId: string) {
  return request(`/api/v1/graph/status?task_id=${encodeURIComponent(taskId)}`);
}

export function fetchPaperCards(taskId: string) {
  return request(`/api/v1/graph/paper-cards?task_id=${encodeURIComponent(taskId)}`);
}

export function fetchRawPapers(taskId: string) {
  return request(`/api/v1/graph/raw-papers?task_id=${encodeURIComponent(taskId)}`);
}

export function fetchAnalysis(taskId: string) {
  return request(`/api/v1/graph/analysis?task_id=${encodeURIComponent(taskId)}`);
}

export function fetchDigest(taskId: string) {
  return request(`/api/v1/graph/digest?task_id=${encodeURIComponent(taskId)}`);
}

export function fetchDiagram() {
  return request("/api/v1/graph/diagram");
}
