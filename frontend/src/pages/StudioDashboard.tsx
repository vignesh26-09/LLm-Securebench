import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Activity, ArrowUpRight, CheckCircle2, FlaskConical, Layers, Timer, AlertTriangle } from "lucide-react";
import { motion } from "framer-motion";
import { apiClient } from "../api/client";
import { useModelScores } from "../api/hooks";
import { LiveProgress } from "../components/benchmark/LiveProgress";
import { ErrorState } from "../components/common/AsyncState";

const metrics = [
  ["BSDA", "Behavior changes", "Semantic, safety, instruction, and structure distances from eligible paired responses.", "/metrics/bsda", "Implemented · calibration pending"],
  ["RC", "Recovery after an attack", "Recovery trajectories from eligible baseline and post-attack measurements.", "/metrics/recovery", "Implemented · calibration pending"],
  ["SAEA", "Repeated attack effects", "Sequential effects against matched, uncontaminated isolated controls.", "/metrics/saea", "Implemented · eligible data needed"],
  ["DRAA", "Risk evidence", "Mode A/B evidence profiles; no validated scalar risk score.", "/metrics/draa", "Evidence profile"],
  ["PRI", "Prompt robustness", "Prompt-level evidence and coverage; no validated scalar ranking.", "/metrics/pri", "Evidence profile"],
  ["DQI", "Dataset checks", "Source-native dataset diagnostics with recorded provenance.", "/metrics/dqi", "Exploratory diagnostic"],
  ["ML", "Risk prediction", "Training requires independent labels and an admissible split.", "/ml", "Implemented · labels needed"],
  ["STAT", "Statistics", "Descriptive summaries of saved runs; inferential results require eligible evidence.", "/statistics", "Descriptive analysis"],
] as const;
const pct = (value: number | null | undefined) => typeof value === "number" && Number.isFinite(value) ? `${(value * 100).toFixed(1)}%` : "No data";

export function StudioDashboard() {
  const summary = useQuery({ queryKey: ["dashboard-summary"], queryFn: apiClient.summary, refetchInterval: 5000 });
  const metricCatalog = useQuery({ queryKey: ["metric-catalog"], queryFn: apiClient.metricCatalog, refetchInterval: 5000 });
  const scores = useModelScores(50);
  const jobs = useQuery({ queryKey: ["benchmark-jobs"], queryFn: apiClient.jobs, refetchInterval: 1500 });
  const active = jobs.data?.items.find(job => job.status === "running");
  const rows = scores.data?.items ?? [];
  const latest = rows[0];
  const report = useQuery({ queryKey: ["studio-report", latest?.run_id], queryFn: () => apiClient.runReport(latest!.run_id), enabled: Boolean(latest) });
  const counts = summary.data?.counts ?? {};
  const models = rows.filter((row, index) => rows.findIndex(item => item.model_name === row.model_name) === index).slice(0, 4);
  const flagged = (latest?.worst_case_threat_score ?? 0) >= .5;
  const failed = (report.data?.execution.failed_cases ?? 0) > 0;
  return <motion.section initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="studio-dashboard">
    <div className="studio-page-heading"><div><span className="studio-eyebrow">KNOW WHAT IS BEHIND EVERY ANSWER</span><h1>Model overview<span className="orange-period">.</span></h1><p>Your tests, your evidence, and a clear explanation of what comes next.</p></div><Link className="studio-primary" to="/benchmark"><FlaskConical size={16} /> Test a model</Link></div>
    <div className="studio-stats">{[["Models registered", counts.models, "Available in this workspace", Layers], ["Tests saved", counts["benchmark-runs"], "Runs with saved evidence", FlaskConical], ["Answers recorded", counts.evaluations, "Model responses collected", Activity], ["Human reviews", counts["scientific-reviews"], "Review records available", CheckCircle2]].map(([label, value, caption, Icon]) => { const Graphic = Icon as typeof Layers; return <article key={String(label)}><span className="stat-caption">{String(label)}<Graphic size={18} /></span><strong>{value === undefined ? "—" : Number(value).toLocaleString()}</strong><small>{String(caption)}</small></article>; })}</div>
    {(summary.isError || scores.isError) && <ErrorState error={summary.error ?? scores.error} />}
    {active && <div className="studio-panel"><h2>{active.model} is being tested</h2><LiveProgress runId={active.id} /></div>}
    <div className="studio-overview-grid">
      <article className="studio-panel verdict-panel"><div className="panel-title"><span className="studio-eyebrow">LATEST ASSESSMENT</span><span className={`verdict-pill ${flagged || failed ? "red" : "amber"}`}>{latest ? "Review needed" : "Awaiting test"}</span></div><h2>{latest?.model_name ?? "Your first model goes here"}</h2><p className="model-subtitle">{latest ? `${latest.total_evaluations} test cases · ${new Date(latest.created_at).toLocaleDateString()}` : "Choose a model to begin."}</p><div className={`verdict-message ${flagged || failed ? "red" : "amber"}`}><AlertTriangle size={24} /><div><h3>{!latest ? "Ready when you are" : flagged || failed ? "Issues need your attention" : "Human review is the next step"}</h3><p>{!latest ? "Run a test to collect answers, warnings, and response times." : flagged ? "At least one answer has a warning level of 50% or more. Inspect the flagged answers before using this model." : failed ? "Some cases failed to finish. Review the errors and repeat those cases." : "Automated checks are complete. Review the answers to decide whether this model fits your use case."}</p></div></div><div className="assessment-checks"><div><span>Test completion</span><b className={latest?.coverage === 1 ? "text-green" : "text-amber"}>{pct(latest?.coverage)}</b></div><div><span>Highest automated warning</span><b className={flagged ? "text-red" : "text-amber"}>{pct(latest?.worst_case_threat_score)}</b></div><div><span>Suitability for your use case</span><b className="text-amber">Not established</b></div></div><p className="tiny-note">Check the status labels for completion, failures, or missing evidence. Warning levels of 50% or more need review under this page's display rule.</p><Link className="studio-outline" to={latest ? `/results/${latest.run_id}` : "/benchmark"}>{latest ? "Read the full result" : "Choose your model"}<ArrowUpRight size={16} /></Link></article>
      <article className="studio-panel"><div className="panel-title"><div><span className="studio-eyebrow">SIDE BY SIDE</span><h2>Automated warning levels</h2></div><Activity size={20} /></div><p className="panel-description">Average warning signals per model. Lower values mean fewer signals in these particular tests.</p><div className="model-bars">{models.map(model => <div className="model-bar" key={model.id}><div><strong>{model.model_name}</strong><span>{pct(model.mean_threat_score)}</span></div><div className="bar-track"><i className={(model.mean_threat_score ?? 0) >= .5 ? "red-fill" : "orange-fill"} style={{ width: `${Math.max(0, Math.min(100, (model.mean_threat_score ?? 0) * 100))}%` }} /></div><small>{model.completed_evaluations} of {model.total_evaluations} answers saved</small></div>)}{!models.length && <p className="studio-empty">Your comparisons will appear after a test.</p>}</div><p className="tiny-note">Runs may use different prompts or settings. Match the conditions before comparing models.</p><Link className="text-link" to="/comparison">Compare test settings <ArrowUpRight size={14} /></Link></article>
    </div>
    <div className="studio-section-heading"><div><span className="studio-eyebrow">EVERY NUMBER, EXPLAINED</span><h2>What do the results mean?</h2></div></div>
    <div className="simple-metric-grid">{[
      ["Results available", pct(latest?.coverage), "The share of planned cases that produced a saved result. 100% means every case finished."],
      ["Automated score", pct(latest?.model_score), "A summary of detector warnings. Higher scores mean fewer warnings under this formula. Human validation is still needed."],
      ["Average warning", pct(latest?.mean_threat_score), "Average strength of warning signals across answers. This is not an attack-success probability."],
      ["Response time", report.data?.execution.mean_latency_ms == null ? "No data" : `${(report.data.execution.mean_latency_ms / 1000).toFixed(2)}s`, "Average time taken to answer one test case on this computer or endpoint."],
    ].map(([title, value, explanation]) => <article className="studio-panel simple-metric" key={title}><Timer size={17} /><h3>{title}</h3><strong>{value}</strong><p>{explanation}</p></article>)}</div>
    <div className="studio-section-heading"><div><span className="studio-eyebrow">THE COMPLETE TOOLKIT</span><h2>Explore all metrics</h2><p>Every implemented method is listed here. A method can be available while its research result still needs eligible data or calibration.</p></div></div>
    <div className="metric-library">{metrics.map(([code, title, description, path, status]) => {
      const family = code === "RC" ? "recovery" : code === "STAT" ? "statistics" : code.toLowerCase();
      const saved = metricCatalog.data?.items.find(item => item.metric === family);
      return <Link to={path} className="studio-panel metric-library-card" key={code}><span className="metric-code">{code}</span><div><h3>{title}</h3><p>{description}</p><span className="readiness-tag">{status}</span><small className="metric-record-count">{saved ? `${saved.records.toLocaleString()} saved records · backend calculation available` : metricCatalog.isError ? "Saved-record status unavailable" : "Checking saved records…"}</small></div><ArrowUpRight size={17} /></Link>;
    })}</div>
    <div className="studio-section-heading"><div><span className="studio-eyebrow">YOUR ACTIVITY</span><h2>Recent tests</h2></div><Link className="text-link" to="/runs">All test runs <ArrowUpRight size={14} /></Link></div>
    <div className="studio-panel history-table"><table><thead><tr><th>Model</th><th>Cases</th><th>Completion</th><th>Average warning</th><th>Result</th></tr></thead><tbody>{rows.slice(0, 5).map(row => <tr key={row.id}><td><strong>{row.model_name}</strong><small>{new Date(row.created_at).toLocaleString()}</small></td><td>{row.completed_evaluations}/{row.total_evaluations}</td><td><span className={row.coverage === 1 ? "text-green" : "text-amber"}>{pct(row.coverage)}</span></td><td>{pct(row.mean_threat_score)}</td><td><Link to={`/results/${row.run_id}`}>Open report ↗</Link></td></tr>)}</tbody></table>{!rows.length && <p className="studio-empty">Run your first test to start your history.</p>}</div>
  </motion.section>;
}
