import { endpoints } from "./endpoints";
import { ApiError, type BenchmarkDataset, type BenchmarkJob, type BenchmarkRunInput, type BenchmarkRunReport, type CalibrationSummary, type HealthStatus, type MetricCatalog, type PaginatedModelScores, type PaginatedScientificRecords, type ReadinessStatus, type RuntimeModelsResponse, type ShowcaseModelsResponse } from "./types";

const baseUrl = import.meta.env.VITE_SECURELLM_API_BASE_URL ?? "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${baseUrl}${path}`, {
      ...init,
      credentials: "include",
      headers: { Accept: "application/json", ...init?.headers },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Network request failed";
    throw new ApiError(undefined, message);
  }

  if (!response.ok) {
    let message = `API request failed with HTTP ${response.status}`;
    try { const problem = await response.json(); if (typeof problem.detail === "string") message = problem.detail; } catch { /* Keep the HTTP fallback. */ }
    throw new ApiError(response.status, message, response.headers.get("X-Request-ID") ?? undefined);
  }
  return (await response.json()) as T;
}

export const apiClient = {
  connectModel: (input: Pick<BenchmarkRunInput, "model" | "provider" | "endpoint" | "api_key">) => request<{ id: string; model: string; verified: boolean; message: string }>("/internal/model-connections", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(input) }),
  runtimeModels: () => request<RuntimeModelsResponse>("/runtime-models"),
  showcaseModels: () => request<ShowcaseModelsResponse>("/showcase-models"),
  benchmarkDatasets: () => request<{ items: BenchmarkDataset[]; note: string }>("/benchmark-datasets"),
  jobs: () => request<{ items: BenchmarkJob[] }>("/benchmark-jobs"),
  job: (jobId: string) => request<BenchmarkJob>(`/benchmark-jobs/${encodeURIComponent(jobId)}`),
  calibrationSummary: () => request<CalibrationSummary>("/calibration-summary"),
  startRun: (input: BenchmarkRunInput) => request<BenchmarkJob>("/internal/benchmark-jobs", { method: "POST", headers: { "Content-Type": "application/json", "X-SecureLLM-Local": "1" }, body: JSON.stringify(input) }),
  resources: (resource: string, offset = 0, filterBy?: string, value?: string) => {
    const query = new URLSearchParams({ limit: "25", offset: String(offset) });
    if (filterBy && value !== undefined) { query.set("filter_by", filterBy); query.set("value", value); }
    return request<{ items: Record<string, unknown>[]; total: number; limit: number; offset: number }>(`/${resource}?${query}`);
  },
  summary: () => request<{ counts: Record<string, number> }>("/dashboard-summary"),
  metricCatalog: () => request<MetricCatalog>("/metrics/catalog"),
  computeMetric: (metric: string, input: Record<string, unknown>) => request<Record<string, unknown>>(`/metrics/compute/${encodeURIComponent(metric)}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(input) }),
  saveMetric: (metric: string, input: Record<string, unknown>) => request<Record<string, unknown>>(`/metrics/compute/${encodeURIComponent(metric)}/save`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(input) }),
  modelScores: (limit = 10, offset = 0) => request<PaginatedModelScores>(`/model-scores?limit=${limit}&offset=${offset}`),
  runReport: (runId: string) => request<BenchmarkRunReport>(`/benchmark-runs/${encodeURIComponent(runId)}/report`),
  health: () => request<HealthStatus>(endpoints.health),
  ready: () => request<ReadinessStatus>(endpoints.ready),
  scientificRecords: (options: { family?: string; limit: number; offset: number }) => {
    const query = new URLSearchParams({ limit: String(options.limit), offset: String(options.offset) });
    if (options.family) query.set("family", options.family);
    return request<PaginatedScientificRecords>(`${endpoints.scientificRecords}?${query.toString()}`);
  },
};
