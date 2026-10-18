import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../../api/client";
import { Link } from "react-router-dom";
import { CheckCircle2 } from "lucide-react";

export function LiveProgress({ runId }: { runId: string }) {
  const client = useQueryClient();
  const job = useQuery({ queryKey: ["benchmark-job", runId], queryFn: () => apiClient.job(runId),
    refetchInterval: query => ["running", "stopping"].includes(query.state.data?.status ?? "running") ? 1000 : false, retry: false });
  const stop = useMutation({ mutationFn: () => apiClient.stopRun(runId), onSuccess: value => {
    client.setQueryData(["benchmark-job", runId], value);
    void client.invalidateQueries({ queryKey: ["benchmark-jobs"] });
  } });
  if (job.isError) return <div className="progress-container" role="alert">Could not load progress. <button onClick={() => { void job.refetch(); }}>Retry</button></div>;
  if (!job.data) return <div className="progress-container"><span className="work-spinner" /> Connecting to the test…</div>;
  const total = job.data.total_cases ?? 0;
  const completed = job.data.completed_cases ?? 0;
  const percentage = total ? Math.min(100, Math.floor((completed / total) * 100)) : 0;
  const running = job.data.status === "running";
  const stopping = job.data.status === "stopping";
  const failed = ["failed", "interrupted", "stopped"].includes(job.data.status);
  if (failed) return <div className="progress-container" role="status"><h2>{job.data.status === "stopped" ? "Test stopped—saved work retained" : "Test interrupted—not erased"}</h2><p>{job.data.error ?? (job.data.status === "stopped" ? "Stopped at your request." : "The server could not finish this test.")}</p><p>{completed.toLocaleString()} of {total.toLocaleString()} source cases committed. {total === 10 ? "Start a new quick check to draw a fresh sample." : "Resuming reuses saved observations and skips committed cases; it does not overwrite failed measurements."}</p>{total !== 10 && <Link className="studio-primary" to={`${job.data.provider === "openai-compatible" ? "/import" : "/benchmark"}?${new URLSearchParams({ model: job.data.model, provider: job.data.provider, judge: job.data.judge_model ?? job.data.model, count: String(total), resume: runId })}`}>Review settings & resume this run →</Link>}</div>;
  return <div className="progress-container" aria-live="polite"><div className="work-stage"><span className={running || stopping ? "work-spinner" : "text-green"}>{running || stopping ? null : <CheckCircle2 size={23} />}</span><div><strong>{stopping ? "Stopping after the current call" : running ? "Your model is working" : "Your results are ready"}</strong><p>{stopping ? "The current model request may finish or time out; saved observations and completed cases remain available." : running ? total === 10 ? "Collecting ten direct responses; no judge or controlled safety metric is run." : "Sending prompts, collecting answers, and checking for warning patterns." : "Open the report to read the measurements and what they mean."}</p></div></div><div className="progress-text"><strong>{completed} of {total || "…"} cases saved</strong><span>{percentage}% complete</span></div><div className="progress-bar" role="progressbar" aria-valuenow={percentage} aria-valuemin={0} aria-valuemax={100} aria-label="Test completion"><i className={running ? "progress-fill active" : "progress-fill"} style={{ width: `${percentage}%` }} /></div><div className="stage-indicator"><span>{job.data.stage ?? "Preparing"}</span>{typeof job.data.last_latency_ms === "number" && <span>Last answer: {(job.data.last_latency_ms / 1000).toFixed(1)} seconds</span>}</div>{running && total !== 10 && <button className="stop-run-button" type="button" disabled={stop.isPending} onClick={() => stop.mutate()}>{stop.isPending ? "Requesting stop…" : "Stop test and keep saved work"}</button>}{stop.isError && <p role="alert">{stop.error instanceof Error ? stop.error.message : "Could not stop the test."}</p>}{!running && !stopping && <Link className="studio-primary" to={`/results/${encodeURIComponent(runId)}`}>See the result →</Link>}</div>;
}
