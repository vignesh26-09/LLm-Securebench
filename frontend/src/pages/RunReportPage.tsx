import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../api/client";
import { ErrorState, LoadingState } from "../components/common/AsyncState";
import { ResponseTimePlot } from "../components/charts/ResponseTimePlot";
import { RunMetricPlots } from "../components/charts/RunMetricPlots";
import { ModelMetricInventory } from "../components/metrics/ModelMetricInventory";

function percent(value: number | null | undefined) {
  return typeof value === "number" ? `${(value * 100).toFixed(1)}%` : "Not computed";
}

export function RunReportPage() {
  const { runId } = useParams();
  const report = useQuery({ queryKey: ["benchmark-run-report", runId], queryFn: () => apiClient.runReport(runId ?? ""), enabled: Boolean(runId), retry: false });
  return <section className="run-report">
    <nav className="flow-stepper" aria-label="Evaluation steps"><span><b>01</b> Choose model</span><span><b>02</b> Live testing</span><span className="current"><b>03</b> Charts & results</span></nav>
    <div className="report-hero"><div><div className="eyebrow">Benchmark result</div><h1>{report.data?.run.model_name ?? "Run report"}</h1><p>Completed benchmark evidence, ready for inspection.</p></div>{report.data && <div className="run-id"><span>Run ID</span><code>{report.data.run.id.slice(0, 12)}</code></div>}</div>
    {report.isLoading && <LoadingState />}{report.isError && <ErrorState error={report.error} />}
    {report.data && <>
      <div className="stat-grid run-report-stats">
        <article><span>Answers saved</span><strong>{report.data.execution.completed_cases}/{report.data.execution.total_cases}</strong><small>{percent(report.data.execution.coverage)} of planned test cases finished</small></article>
        <article><span>Average response time</span><strong>{report.data.execution.mean_latency_ms === null ? "—" : `${(report.data.execution.mean_latency_ms / 1000).toFixed(2)}s`}</strong><small>Time taken to produce one answer</small></article>
        <article><span>Automated score</span><strong>{percent(report.data.model_score.value)}</strong><small>Rule summary; requires human validation</small></article>
      </div>
      <RunMetricPlots report={report.data} />
      <ResponseTimePlot cases={report.data.cases} />
      <ModelMetricInventory report={report.data} />
      <details className="assessment-source"><summary>How this assessment is determined</summary><div className="decision-card"><span>Selection status</span><h2>{report.data.selection.label}</h2><p>{report.data.selection.reason}</p></div><p className="tiny-note">Warning values describe rule matches. Values of 50% or more need review under the display rule; this is not a validated safety cutoff.</p></details>
      <div className="report-reading"><div><h2>Read this carefully</h2><p>{report.data.interpretation.observed_detector_signals}</p></div><div><h2>What the summary means</h2><p>{report.data.interpretation.model_score}</p></div></div>
      <div className="report-section-heading"><div><div className="eyebrow">Layer 1 observations</div><h2>Observed detector signals</h2></div><span>{report.data.detector_summary.reduce((total, item) => total + item.observed_signal_count, 0)} signals recorded</span></div>
      {report.data.detector_summary.length === 0 ? <p className="empty">No Layer 1 detector records were persisted for this run.</p> : <div className="signal-grid">{report.data.detector_summary.map(item => <article key={item.detector}><div><span>{item.detector}</span><strong>{item.max_score.toFixed(3)}</strong></div><div className="signal-scale"><i style={{ width: `${item.max_score * 100}%` }} /></div><small>{item.observed_signal_count} observed {item.observed_signal_count === 1 ? "signal" : "signals"}</small></article>)}</div>}
      <div className="report-section-heading"><div><div className="eyebrow">Case by case</div><h2>Execution timeline</h2></div><span>{report.data.execution.completed_cases}/{report.data.execution.total_cases} complete</span></div>
      <div className="case-list">{report.data.cases.map((item, index) => <article key={item.id}><div className="case-index">{String(index + 1).padStart(2, "0")}</div><div className="case-main"><strong>{item.case_id ?? item.id}</strong><small>{item.execution_status}{item.finish_reason ? ` · ${item.finish_reason}` : ""}</small></div><div><span>Latency</span><strong>{item.latency_ms === null ? "—" : `${item.latency_ms.toFixed(0)} ms`}</strong></div><div><span>Signals</span><strong>{item.observed_detector_signals.length ? item.observed_detector_signals.map(signal => `${signal.detector} ${signal.score.toFixed(2)}`).join(" · ") : "None recorded"}</strong></div></article>)}</div>
      <div className="report-actions"><Link className="primary-button inline-action" to={`/evaluations?filter_by=benchmark_run_id&value=${encodeURIComponent(report.data.run.id)}`}>Inspect full responses</Link><Link to="/benchmark">Run another benchmark →</Link></div>
      <section className="usage-assessment final-model-conclusion" aria-label="Final model conclusion"><span className="studio-eyebrow">FINAL CONCLUSION / {report.data.run.model_name}</span><h2>{report.data.execution.failed_cases || report.data.execution.coverage < 1 ? "Not ready to choose: complete the failed or missing tests." : "Do not approve for production from this run alone."}</h2><p>{report.data.execution.failed_cases || report.data.execution.coverage < 1 ? "Fix the incomplete tests and rerun them. Missing results cannot be treated as successful checks." : "You can continue controlled research with this model. A completed benchmark and a high automated score do not establish that it is safe for your application."}</p><div><span>Testing: {report.data.execution.coverage === 1 && !report.data.execution.failed_cases ? "complete" : "incomplete"}</span><span>Human validation: not established</span><span>Production approval: not established</span></div><h3>What to do next</h3><p>Review flagged responses, collect independently validated outcomes, complete missing metric inputs, and evaluate against your intended use case before choosing this model.</p></section>
    </>}
  </section>;
}
