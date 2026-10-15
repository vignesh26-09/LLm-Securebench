import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../../api/client";
import { Link } from "react-router-dom";
import { CheckCircle2, CircleAlert } from "lucide-react";

export function LiveProgress({ runId }: { runId: string }) {
  const job = useQuery({ queryKey: ["benchmark-job", runId], queryFn: () => apiClient.job(runId), refetchInterval: 1000, retry: false });
  if (job.isError) return <div className="progress-container" role="alert">Could not load progress. <button onClick={() => { void job.refetch(); }}>Retry</button></div>;
  if (!job.data) return <div className="progress-container"><span className="work-spinner" /> Connecting to the test…</div>;
  const total = job.data.total_cases ?? 0;
  const completed = job.data.completed_cases ?? 0;
  const percentage = total ? Math.min(100, Math.round((completed / total) * 100)) : 0;
  const running = job.data.status === "running";
  const failed = job.data.status === "failed";
  return <div className="progress-container" aria-live="polite"><div className="work-stage"><span className={running ? "work-spinner" : failed ? "text-red" : "text-green"}>{running ? null : failed ? <CircleAlert size={23} /> : <CheckCircle2 size={23} />}</span><div><strong>{running ? "Your model is working" : failed ? "This test needs attention" : "Your results are ready"}</strong><p>{running ? "Sending prompts, collecting answers, and checking for warning patterns." : failed ? job.data.error ?? "Inspect the failure in the job details." : "Open the report to read the measurements and what they mean."}</p></div></div><div className="progress-text"><strong>{completed} of {total || "…"} cases saved</strong><span>{percentage}% complete</span></div><div className="progress-bar" role="progressbar" aria-valuenow={percentage} aria-valuemin={0} aria-valuemax={100} aria-label="Test completion"><i className={running ? "progress-fill active" : "progress-fill"} style={{ width: `${percentage}%` }} /></div><div className="stage-indicator"><span>{job.data.stage ?? "Preparing"}</span>{typeof job.data.last_latency_ms === "number" && <span>Last answer: {(job.data.last_latency_ms / 1000).toFixed(1)} seconds</span>}</div>{!running && !failed && <Link className="studio-primary" to={`/results/${encodeURIComponent(runId)}`}>See the result →</Link>}</div>;
}
