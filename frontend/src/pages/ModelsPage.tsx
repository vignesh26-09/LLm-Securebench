import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { apiClient } from "../api/client";
import { useModelScores } from "../api/hooks";
import { ErrorState, LoadingState } from "../components/common/AsyncState";
import { ModelScoreboard } from "../components/common/ModelScoreboard";
import { EntityPage } from "./EntityPage";

export function ModelsPage() {
  const runtime = useQuery({ queryKey: ["runtime-models"], queryFn: apiClient.runtimeModels, refetchInterval: 15000, retry: false });
  const jobs = useQuery({ queryKey: ["benchmark-jobs"], queryFn: apiClient.jobs, refetchInterval: 3000, retry: false });
  const scores = useModelScores(25);
  return <><section><div className="eyebrow">Model catalog / Persisted configurations</div><h1>Models and evidence</h1><p>Inspect installed local models and the exact configurations saved with benchmark runs. Launch a new run from the dedicated <Link to="/benchmark">Benchmark workspace</Link>.</p><p className="notice">Pilot data only. The example corpus and detector signals are not validated security assessments. Model scores are engineering summaries, not model rankings.</p>
    {runtime.isLoading && <LoadingState />}{runtime.isError && <ErrorState error={runtime.error} />}
    {runtime.data && <>{!runtime.data.available && <p>{runtime.data.reason}</p>}{runtime.data.available && runtime.data.items.length === 0 && <p>No models are installed in the local Ollama service.</p>}
      {!runtime.data.execution_enabled && <p>Execution is disabled on this server. Start the local workspace using scripts/start_local.ps1.</p>}
      <div className="stat-grid">{runtime.data.items.map(model => <article key={model.digest}><h2>{model.name}</h2><p>{model.details?.parameter_size} · {model.details?.quantization_level}</p><small>Installed locally · digest {model.digest.slice(0, 12)}</small><p><Link to={`/benchmark?model=${encodeURIComponent(model.name)}`}>Configure benchmark →</Link></p></article>)}</div>
    </>}
    {jobs.isError && <ErrorState error={jobs.error} />}{jobs.data && jobs.data.items.length > 0 && <div className="research-note"><h2>Session execution jobs</h2><p>Completed evidence is retained under Benchmark runs. This live job list resets when the server restarts.</p>{jobs.data.items.map(job => <p key={job.id}><strong>{job.model}</strong> · {job.status} {job.error ?? ""} {job.status !== "running" && <Link to={`/evaluations?filter_by=benchmark_run_id&value=${job.id}`}>View results →</Link>}</p>)}</div>}
    <div className="section-divider" />
    <h2>Scored benchmark runs</h2>
    <p>The detector summary shows fewer or more detector-native signals in completed example evaluations. Every model still requires evidence review before selection: independent outcome labels and a validated decision rule are not available.</p>
    {scores.isLoading && <LoadingState />}{scores.isError && <ErrorState error={scores.error} />}{scores.data && <ModelScoreboard scores={scores.data.items} />}
  </section><div className="section-divider" /><EntityPage title="Saved model configurations" resource="models" description="Exact model digests and generation settings used in persisted benchmark runs." /></>;
}
