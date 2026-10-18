import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { apiClient } from "../api/client";
import { useModelScores } from "../api/hooks";
import { ErrorState, LoadingState } from "../components/common/AsyncState";
import { ModelScoreboard } from "../components/common/ModelScoreboard";
import { LiveProgress } from "../components/benchmark/LiveProgress";
import { CalibrationResults } from "../components/metrics/CalibrationResults";
import { MetricStatusBoard } from "../components/metrics/MetricStatusBoard";
import { ResearchDashboard } from "../components/dashboard/ResearchDashboard";
import "../components/dashboard/research-dashboard.css";

const catalogue = [
  ["/models", "Model library", "Installed models and saved model configurations"],
  ["/runs", "Benchmark runs", "Execution status and run provenance"],
  ["/evaluations", "Evaluation results", "Responses, latency, and execution records"],
  ["/security", "Layer 1 analysis", "Detector-native observations"],
  ["/layer2", "Layer 2 evidence", "Source-native judge dimensions"],
  ["/datasets", "Datasets & versions", "Source inputs and immutable snapshots"],
  ["/comparison", "Configuration comparison", "Saved settings side by side"],
  ["/records", "Experiment details", "Raw scientific-record families"],
] as const;
export function Overview() {
  const query = useQuery({ queryKey: ["dashboard-summary"], queryFn: apiClient.summary, retry: false, refetchInterval: 4000 });
  const scores = useModelScores(50);
  const jobs = useQuery({ queryKey: ["benchmark-jobs"], queryFn: apiClient.jobs, refetchInterval: 1000, retry: false });
  const activeJob = jobs.data?.items.find(job => job.status === "running");
  return <section className="overview-page">
    {query.isLoading && <LoadingState />}{query.isError && <ErrorState error={query.error} />}
    {query.data && scores.data && <ResearchDashboard counts={query.data.counts} scores={scores.data.items} activeJob={activeJob} />}
    {activeJob && <section className="active-test"><LiveProgress runId={activeJob.id} /></section>}
    <div className="section-divider" />
    <CalibrationResults />
    <MetricStatusBoard />
    <div className="section-divider" />
    <h2>Detailed detector summaries</h2>
    {scores.isLoading && <LoadingState />}{scores.isError && <ErrorState error={scores.error} />}{scores.data && <ModelScoreboard scores={scores.data.items} />}
    <div className="section-divider" />
    <div className="catalogue-heading"><div><div className="eyebrow">Evidence catalogue</div><h2>Explore saved data and reports</h2></div><p>These pages are grouped here to keep the sidebar focused on testing and metrics.</p></div>
    <div className="catalogue-grid">{catalogue.map(([path, title, description]) => <Link key={path} to={path}><article><h3>{title}</h3><p>{description}</p><span>Open →</span></article></Link>)}</div>
    <div className="research-note"><div className="eyebrow">Reading this workspace</div><h2>Availability is not validation.</h2><p>These are database counts, not quality or security scores. Example datasets remain labelled in provenance. Scientific results appear only when persisted from an identified source.</p><Link to="/records">Browse scientific evidence →</Link></div>
  </section>;
}
