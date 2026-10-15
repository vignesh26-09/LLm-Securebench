export interface HealthStatus {
  service: string;
  status: string;
  [key: string]: unknown;
}

export interface ReadinessStatus {
  status: "ready" | "unavailable";
}

export interface ScientificRecord {
  id: string;
  family: string;
  schema_version: string;
  scope: string;
  status: string | null;
  payload: Record<string, unknown>;
  provenance: Record<string, unknown>;
}

export interface PaginatedScientificRecords {
  items: ScientificRecord[];
  limit: number;
  offset: number;
}

export interface MetricCatalog {
  items: {
    metric: string;
    compute_path: string;
    required_fields: string[];
    ordinary_run_persists_family: boolean;
    records: number;
    statuses: Record<string, number>;
    scientific_validation: string;
  }[];
}

export interface ModelScore {
  id: string;
  run_id: string;
  model_name: string;
  status: string;
  model_score: number | null;
  mean_threat_score: number | null;
  worst_case_threat_score: number | null;
  coverage: number;
  completed_evaluations: number;
  total_evaluations: number;
  formula_version: string;
  formula: Record<string, string>;
  warnings: string[];
  created_at: string;
  provenance: Record<string, unknown>;
}

export interface PaginatedModelScores {
  items: ModelScore[];
  total: number;
  limit: number;
  offset: number;
}

export interface RuntimeModel {
  name: string;
  digest: string;
  details?: { parameter_size?: string; quantization_level?: string };
}

export interface RuntimeModelsResponse {
  available: boolean;
  execution_enabled: boolean;
  reason?: string;
  items: RuntimeModel[];
}

export interface ShowcaseModel {
  id: string;
  name: string;
  ollama_model: string;
  description: string;
  access: string;
}

export interface ShowcaseModelsResponse {
  items: ShowcaseModel[];
  remote_execution_enabled: boolean;
  note: string;
}

export interface BenchmarkJob {
  id: string;
  model: string;
  provider: "ollama-local" | "openai-compatible";
  status: string;
  error?: string;
  stage?: string;
  submitted_at?: string;
  completed_at?: string;
  completed_cases?: number;
  total_cases?: number;
  planned_target_calls?: number;
  planned_judge_calls?: number;
  judge_model?: string;
  context_window?: number;
  last_case_id?: string | null;
  last_latency_ms?: number | null;
}

export interface CalibrationSummary {
  status: string;
  result: { source_n: number; usable_n: number; coverage: number; raw_agreement: number; cohen_kappa: number; confusion_matrix: { pred_0_label_0: number; pred_0_label_1: number; pred_1_label_0: number; pred_1_label_1: number } };
  source_manifest: { dataset_revision: string; sha256: string; source_name: string };
  interpretation: string;
}

export interface BenchmarkRunInput {
  model: string;
  provider: "ollama-local" | "openai-compatible";
  dataset_key: "repository-example" | "mixed-source-10000-v1";
  case_offset: number;
  case_count: number;
  judge_model?: string;
  context_window?: number;
  confirm_full_corpus?: boolean;
  resume_run_id?: string;
  endpoint?: string;
  api_key?: string;
}

export interface BenchmarkDataset {
  id: BenchmarkRunInput["dataset_key"];
  name: string;
  case_count: number;
  available: boolean;
  category_counts: Record<string, number>;
  evidence_class: string;
  max_cases_per_job: number;
  note: string;
}

export interface BenchmarkRunReport {
  metric_profiles?: { family: string; record_count: number; status: string | null; status_counts?: Record<string, number>; measured_case_count?: number; value: number | null; components?: Record<string, number | null>; measurements?: { label: string; value: number; unit: string; sample_count?: number }[]; note?: string | null }[];
  run: { id: string; status: string; model_name: string | null; model_config_id: string; created_at: string };
  execution: { total_cases: number; completed_cases: number; failed_cases: number; coverage: number; mean_latency_ms: number | null };
  detector_summary: { detector: string; max_score: number; observed_signal_count: number }[];
  cases: { id: string; case_id: string | null; execution_status: string; latency_ms: number | null; finish_reason: string | null; response_available: boolean; observed_detector_signals: { detector: string; score: number; confidence: number | null }[] }[];
  model_score: { status: string; value: number | null; mean_threat_score: number | null; worst_case_threat_score: number | null; formula_version: string | null; formula: Record<string, string> | null; warnings: string[] };
  selection: { status: "evidence_review_required"; label: string; reason: string };
  interpretation: { observed_detector_signals: string; model_score: string };
}

export type ApiState = "loading" | "success" | "not_found" | "failure";

export class ApiError extends Error {
  constructor(
    public readonly status: number | undefined,
    message: string,
    public readonly requestId?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}
