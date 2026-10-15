import { useEffect, useMemo, useRef, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import * as echarts from "echarts";
import { Link } from "react-router-dom";
import { apiClient } from "../../api/client";
import type { BenchmarkJob, ModelScore } from "../../api/types";

type Counts = Record<string, number>;

const PALETTE = ["#ff8a3d", "#4aa8ff", "#7a79ff", "#ffbe68"];

function finite(value: number | null | undefined) {
  return typeof value === "number" && Number.isFinite(value);
}

function percentage(value: number | null | undefined) {
  return finite(value) ? Math.round((value as number) * 100) : null;
}

function signedDelta(current: number | null, previous: number | null) {
  if (current === null || previous === null) return "No earlier run to compare";
  const delta = current - previous;
  if (delta === 0) return "Same as the previous run";
  return `${Math.abs(delta)} points ${delta > 0 ? "higher" : "lower"} than the previous run`;
}

function GlassIcon({ children }: { children: ReactNode }) {
  return <span className="glass-icon" aria-hidden="true">{children}</span>;
}

function AnalyticsDonut({ counts }: { counts: Counts }) {
  const host = useRef<HTMLDivElement>(null);
  const data = useMemo(() => [
    { name: "Test results", value: counts.evaluations ?? 0 },
    { name: "Test runs", value: counts["benchmark-runs"] ?? 0 },
    { name: "Analysis records", value: counts["scientific-records"] ?? 0 },
    { name: "Human reviews", value: counts["scientific-reviews"] ?? 0 },
  ], [counts]);
  const total = data.reduce((sum, item) => sum + item.value, 0);

  useEffect(() => {
    if (!host.current) return undefined;
    const chart = echarts.init(host.current);
    chart.setOption({
      animationDuration: 700,
      color: PALETTE,
      tooltip: { trigger: "item", formatter: "{b}<br/><strong>{c}</strong> records · {d}%" },
      series: [{
        type: "pie",
        radius: ["67%", "88%"],
        center: ["50%", "50%"],
        startAngle: 96,
        minAngle: 4,
        padAngle: 3,
        itemStyle: { borderRadius: 12, borderColor: "#0b1830", borderWidth: 3 },
        label: { show: false },
        emphasis: { scale: true, scaleSize: 5 },
        data,
      }],
      graphic: [{
        type: "group", left: "center", top: "center", bounding: "raw",
        children: [
          { type: "text", style: { text: total.toLocaleString(), fill: "#f8fbff", font: "700 34px Inter, sans-serif", textAlign: "center", textVerticalAlign: "middle", y: -8 } },
          { type: "text", style: { text: "SAVED RECORDS", fill: "#adc3dc", font: "700 10px Inter, sans-serif", textAlign: "center", textVerticalAlign: "middle", y: 24, letterSpacing: 1.5 } },
        ],
      }],
    });
    const resize = () => chart.resize();
    window.addEventListener("resize", resize);
    return () => { window.removeEventListener("resize", resize); chart.dispose(); };
  }, [data, total]);

  return <article className="dash-card donut-card span-4 row-2">
    <div className="dash-card-heading"><div><span className="dash-kicker">Saved in this workspace</span><h2>What data do we have?</h2><p className="card-intro">A count of the records created while models are tested and reviewed.</p></div><span className="live-pill"><i /> up to date</span></div>
    <div className="donut-chart" ref={host} role="img" aria-label={`Donut chart showing ${total} records across evaluations, runs, scientific records, and reviews`} />
    <div className="donut-legend">{data.map((item, index) => <div key={item.name}><i style={{ background: PALETTE[index] }} /><span>{item.name}</span><strong>{item.value.toLocaleString()}</strong></div>)}</div>
  </article>;
}

function ComparisonLineChart({ scores }: { scores: ModelScore[] }) {
  const host = useRef<HTMLDivElement>(null);
  const points = useMemo(() => scores
    .filter((score) => finite(score.model_score) || finite(score.coverage) || finite(score.mean_threat_score))
    .slice(0, 12)
    .reverse(), [scores]);

  useEffect(() => {
    if (!host.current || points.length === 0) return undefined;
    const chart = echarts.init(host.current);
    chart.setOption({
      color: ["#ff8a3d", "#54aaff", "#8a82ff"],
      grid: { top: 48, right: 22, bottom: 52, left: 48 },
      legend: { top: 2, right: 0, textStyle: { color: "#9db3cc", fontSize: 11 }, itemWidth: 18, itemHeight: 3 },
      tooltip: {
        trigger: "axis", backgroundColor: "rgba(8,18,36,.96)", borderColor: "rgba(114,162,215,.3)", textStyle: { color: "#eef6ff" },
        formatter: (params: unknown) => {
          const items = params as Array<{ dataIndex: number; marker: string; seriesName: string; value: number }>;
          const score = points[items[0]?.dataIndex ?? 0];
          return `<strong>${score?.model_name ?? "Run"}</strong><br/>${items.map((item) => `${item.marker}${item.seriesName}: ${item.value ?? "—"}%`).join("<br/>")}`;
        },
      },
      xAxis: {
        type: "category",
        boundaryGap: false,
        data: points.map((_, index) => String(index + 1).padStart(2, "0")),
        axisLine: { lineStyle: { color: "rgba(145,178,214,.24)" } },
        axisTick: { show: false },
        axisLabel: { color: "#8098b4", fontSize: 10, interval: 0 },
      },
      yAxis: {
        type: "value", min: 0, max: 100,
        axisLabel: { color: "#8098b4", formatter: "{value}%" },
        splitLine: { lineStyle: { color: "rgba(145,178,214,.11)" } },
      },
      series: [
        { name: "Automated score", type: "line", smooth: .32, symbolSize: 7, lineStyle: { width: 3 }, areaStyle: { color: "rgba(255,138,61,.07)" }, data: points.map((score) => percentage(score.model_score)) },
        { name: "Results available", type: "line", smooth: .32, symbolSize: 6, lineStyle: { width: 2 }, data: points.map((score) => percentage(score.coverage)) },
        { name: "Average warning", type: "line", smooth: .32, symbolSize: 6, lineStyle: { width: 2, type: "dashed" }, data: points.map((score) => percentage(score.mean_threat_score)) },
      ],
    });
    const resize = () => chart.resize();
    window.addEventListener("resize", resize);
    return () => { window.removeEventListener("resize", resize); chart.dispose(); };
  }, [points]);

  return <article className="dash-card comparison-chart-card span-8 row-2">
    <div className="dash-card-heading"><div><span className="dash-kicker">Recent test history</span><h2>How did recent runs compare?</h2><p className="card-intro">Each number on the bottom is one saved test run. Hover over a point to see its model and values.</p></div><Link to="/comparison" className="ghost-link">Open comparison ↗</Link></div>
    {points.length === 0 ? <div className="chart-empty">Run a benchmark to populate the comparison graph.</div> : <div className="comparison-chart" ref={host} role="img" aria-label="Line graph comparing detector summary, coverage, and mean threat score across recent model runs" />}
    <p className="dash-footnote"><strong>Read this carefully:</strong> “Results available” means the test completed. The automated score and warning level come from rules; they do not prove that a model is safe.</p>
  </article>;
}

function MetricCard({ label, value, detail, meaning, tone, children }: { label: string; value: string; detail: string; meaning: string; tone: "orange" | "blue" | "violet"; children: ReactNode }) {
  return <article className={`dash-card metric-card tone-${tone} span-3`}>
    <div className="metric-card-top"><GlassIcon>{children}</GlassIcon><span className="metric-spark" /></div>
    <span>{label}</span><strong>{value}</strong><small>{detail}</small><p>{meaning}</p>
  </article>;
}

function LatestRunCard({ score }: { score?: ModelScore }) {
  const coverage = percentage(score?.coverage);
  return <article className="dash-card latest-card span-4">
    <div className="dash-card-heading"><div><span className="dash-kicker">Most recent completed test</span><h2>{score?.model_name ?? "No test run yet"}</h2><p className="card-intro">Shows how much of the planned test finished and was saved.</p></div>{score && <span className="status status-completed">Saved</span>}</div>
    <div className="latest-score"><strong>{coverage === null ? "—" : `${coverage}%`}</strong><span>of expected results are available</span></div>
    <div className="mini-progress"><i style={{ width: `${coverage ?? 0}%` }} /></div>
    <div className="latest-meta"><span>{score ? `${score.completed_evaluations} of ${score.total_evaluations} test cases saved` : "Run a benchmark to begin"}</span>{score && <Link to={`/results/${encodeURIComponent(score.run_id)}`}>See what happened →</Link>}</div>
  </article>;
}

function RecentRuns({ scores }: { scores: ModelScore[] }) {
  return <article className="dash-card recent-card span-8">
    <div className="dash-card-heading"><div><span className="dash-kicker">Test history</span><h2>Recent model tests</h2><p className="card-intro">Open a row to see the prompts, model answers, warnings, and saved evidence.</p></div><Link to="/runs" className="ghost-link">View every run</Link></div>
    <div className="run-list">{scores.length === 0 ? <div className="chart-empty compact">No persisted benchmark activity yet.</div> : scores.slice(0, 4).map((score, index) => <Link to={`/results/${encodeURIComponent(score.run_id)}`} className="run-item" key={score.id}>
      <span className={`run-rank rank-${index + 1}`}>{String(index + 1).padStart(2, "0")}</span>
      <span className="run-name"><strong>{score.model_name}</strong><small>{new Date(score.created_at).toLocaleString()}</small></span>
      <span className="run-value"><strong>{percentage(score.model_score) ?? "—"}{percentage(score.model_score) === null ? "" : "%"}</strong><small>automated score</small></span>
      <span className="run-value"><strong>{percentage(score.coverage) === null ? "—" : `${percentage(score.coverage)}%`}</strong><small>results available</small></span>
      <span className="run-arrow">↗</span>
    </Link>)}</div>
  </article>;
}

function ReportPlot({ option, label, className = "" }: { option: echarts.EChartsOption; label: string; className?: string }) {
  const host = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!host.current) return undefined;
    const chart = echarts.init(host.current);
    chart.setOption(option);
    const resize = () => chart.resize();
    window.addEventListener("resize", resize);
    return () => { window.removeEventListener("resize", resize); chart.dispose(); };
  }, [option]);
  return <div className={`report-plot ${className}`} ref={host} role="img" aria-label={label} />;
}

function MetricsReport({ scores }: { scores: ModelScore[] }) {
  const selected = useMemo(() => {
    const seen = new Set<string>();
    return scores.filter((score) => {
      if (seen.has(score.model_name)) return false;
      seen.add(score.model_name);
      return true;
    }).slice(0, 3);
  }, [scores]);
  const ids = selected.map((score) => score.run_id);
  const reports = useQuery({
    queryKey: ["dashboard-metrics-report", ids],
    queryFn: () => Promise.all(ids.map((id) => apiClient.runReport(id))),
    enabled: ids.length > 0,
    retry: false,
  });
  const rows = useMemo(() => reports.data ?? [], [reports.data]);

  const metricOption = useMemo<echarts.EChartsOption>(() => ({
    color: ["#ff8a3d", "#55adff", "#958cff"],
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    legend: { top: 0, textStyle: { color: "#92aac5", fontSize: 10 } },
    grid: { top: 48, left: 42, right: 14, bottom: 36 },
    xAxis: { type: "category", data: rows.map((report) => report.run.model_name), axisLabel: { color: "#8aa1bd" }, axisLine: { lineStyle: { color: "rgba(145,178,214,.2)" } } },
    yAxis: { type: "value", min: 0, max: 100, axisLabel: { color: "#8aa1bd", formatter: "{value}%" }, splitLine: { lineStyle: { color: "rgba(145,178,214,.1)" } } },
    series: [
      { name: "Automated score", type: "bar", barMaxWidth: 24, data: rows.map((report) => percentage(report.model_score.value)) },
      { name: "Average warning", type: "bar", barMaxWidth: 24, data: rows.map((report) => percentage(report.model_score.mean_threat_score)) },
      { name: "Highest warning", type: "bar", barMaxWidth: 24, data: rows.map((report) => percentage(report.model_score.worst_case_threat_score)) },
    ],
  }), [rows]);

  const latencyOption = useMemo<echarts.EChartsOption>(() => ({
    color: ["#ff8a3d", "#55adff", "#958cff"],
    tooltip: { trigger: "axis", valueFormatter: (value: unknown) => `${Number(value).toFixed(0)} ms` },
    legend: { top: 0, textStyle: { color: "#92aac5", fontSize: 10 } },
    grid: { top: 48, left: 58, right: 14, bottom: 36 },
    xAxis: { type: "category", data: rows[0]?.cases.map((item) => item.case_id ?? item.id) ?? [], axisLabel: { color: "#8aa1bd" }, axisLine: { lineStyle: { color: "rgba(145,178,214,.2)" } } },
    yAxis: { type: "value", axisLabel: { color: "#8aa1bd", formatter: (value: number) => `${Math.round(value / 1000)}s` }, splitLine: { lineStyle: { color: "rgba(145,178,214,.1)" } } },
    series: rows.map((report) => ({ name: report.run.model_name ?? "model", type: "line", smooth: .3, symbolSize: 8, lineStyle: { width: 3 }, data: report.cases.map((item) => item.latency_ms === null ? null : Math.round(item.latency_ms)) })),
  }), [rows]);

  const detectorNames = useMemo(() => Array.from(new Set(rows.flatMap((report) => report.detector_summary.map((item) => item.detector)))), [rows]);
  const detectorOption = useMemo<echarts.EChartsOption>(() => ({
    color: ["#ff8a3d", "#55adff", "#958cff"],
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    legend: { top: 0, textStyle: { color: "#92aac5", fontSize: 10 } },
    grid: { top: 48, left: 42, right: 14, bottom: 36 },
    xAxis: { type: "category", data: detectorNames, axisLabel: { color: "#8aa1bd" }, axisLine: { lineStyle: { color: "rgba(145,178,214,.2)" } } },
    yAxis: { type: "value", minInterval: 1, axisLabel: { color: "#8aa1bd" }, splitLine: { lineStyle: { color: "rgba(145,178,214,.1)" } } },
    series: rows.map((report) => ({ name: report.run.model_name ?? "model", type: "bar", barMaxWidth: 30, data: detectorNames.map((name) => report.detector_summary.find((item) => item.detector === name)?.observed_signal_count ?? 0) })),
  }), [detectorNames, rows]);

  if (reports.isLoading) return <section className="metrics-report-section"><div className="dash-kicker">Generated metrics report</div><h2>Preparing persisted run plots…</h2></section>;
  if (!rows.length) return null;
  return <section className="metrics-report-section">
    <div className="metrics-report-heading"><div><span className="dash-kicker">Simple model comparison</span><h2>What did the latest tests show?</h2><p>These charts compare the newest saved run for each model. They show automated warnings and speed—not a final judgment that one model is safer.</p></div><div className="report-run-links">{rows.map((report) => <Link key={report.run.id} to={`/results/${report.run.id}`}>Open {report.run.model_name} results ↗</Link>)}</div></div>
    <div className="report-plot-grid">
      <article className="dash-card report-plot-card"><span className="plot-number">01</span><div><span className="dash-kicker">Automated checks</span><h3>Scores and warning levels</h3><p className="plot-explanation">Compares the rule-based score, the average warning, and the highest warning found in one answer. Higher warning bars mean the rules found more potentially risky text.</p></div><ReportPlot option={metricOption} label="Grouped bar chart comparing automated score, average warning, and highest warning for the latest model runs" /></article>
      <article className="dash-card report-plot-card"><span className="plot-number">02</span><div><span className="dash-kicker">Response speed</span><h3>Time taken for each test case</h3><p className="plot-explanation">Each line is a model. Lower points mean a faster answer for that test case. Speed depends on the local computer and does not measure safety.</p></div><ReportPlot option={latencyOption} label="Line graph comparing response time for each benchmark case by model" /></article>
      <article className="dash-card report-plot-card"><span className="plot-number">03</span><div><span className="dash-kicker">Rule matches</span><h3>Warnings found by each detector</h3><p className="plot-explanation">Counts how many times each automated rule matched a response. A match asks for review; it is not proof that an attack succeeded.</p></div><ReportPlot option={detectorOption} label="Grouped bar chart comparing automated warning counts by model and detector" /></article>
    </div>
    <div className="report-summary-table" role="table" aria-label="Latest model comparison summary"><div className="report-summary-row report-summary-head" role="row"><span>Model</span><span>Coverage</span><span>Mean latency</span><span>Signals</span><span>Status</span></div>{rows.map((report) => <div className="report-summary-row" role="row" key={report.run.id}><strong>{report.run.model_name}</strong><span>{percentage(report.execution.coverage)}%</span><span>{report.execution.mean_latency_ms === null ? "—" : `${(report.execution.mean_latency_ms / 1000).toFixed(2)}s`}</span><span>{report.detector_summary.reduce((sum, item) => sum + item.observed_signal_count, 0)}</span><Link to={`/results/${report.run.id}`}>Evidence report →</Link></div>)}</div>
    <p className="report-caution"><strong>What this report cannot tell you yet:</strong> Runs may use different datasets or case windows. These results cannot provide a validated attack-success rate, a safety ranking, or a recommendation about which model to deploy.</p>
  </section>;
}

export function ResearchDashboard({ counts, scores, activeJob }: { counts: Counts; scores: ModelScore[]; activeJob?: BenchmarkJob }) {
  const latest = scores[0];
  const previous = scores[1];
  const totalCases = scores.reduce((sum, score) => sum + score.completed_evaluations, 0);
  const meanCoverage = scores.length ? Math.round(scores.reduce((sum, score) => sum + score.coverage, 0) / scores.length * 100) : null;
  const latestSummary = percentage(latest?.model_score);
  const previousSummary = percentage(previous?.model_score);
  const threat = percentage(latest?.mean_threat_score);

  return <div className="research-dashboard">
    <section className="dashboard-hero">
      <div><span className="dash-kicker">SecureLLMBench / Model security testing</span><h1>Test a model.<br/><em>Understand the result.</em></h1><p>Choose a prompt source and case window, see what automated warnings were found, and open the saved evidence behind every number.</p></div>
      <div className="hero-actions"><Link className="hero-primary" to="/benchmark">Start a model test <span>↗</span></Link><Link className="hero-secondary" to="/records">View saved evidence</Link></div>
    </section>

    <section className="plain-guide" aria-labelledby="dashboard-guide-title">
      <div className="plain-guide-title"><span className="guide-badge">Start here</span><div><h2 id="dashboard-guide-title">How to read this dashboard</h2><p>The page separates completed work from automated warnings and human conclusions.</p></div></div>
      <div className="plain-guide-steps">
        <div><strong>1. Results available</strong><span>How many planned model answers were successfully generated and saved.</span></div>
        <div><strong>2. Automated warnings</strong><span>Patterns found by rules. They tell you what to inspect, not whether an attack definitely worked.</span></div>
        <div><strong>3. Validated conclusion</strong><span>A safety claim needs human review or a judge already proven reliable for this task.</span></div>
      </div>
    </section>

    {activeJob && <Link to={`/results/${encodeURIComponent(activeJob.id)}`} className="live-run-banner"><span className="live-pulse" /><div><strong>{activeJob.model} is running</strong><small>{activeJob.stage ?? "Benchmark execution in progress"}</small></div><b>{activeJob.completed_cases ?? 0}/{activeJob.total_cases ?? 0}</b><span>View live run →</span></Link>}

    <section className="dashboard-grid" aria-label="Benchmark analytics overview">
      <MetricCard label="Model answers tested" value={totalCases.toLocaleString()} detail={`From ${scores.length} saved test runs`} meaning="The total number of completed test cases shown on this page." tone="orange"><svg viewBox="0 0 24 24"><path d="M5 12l4 4L19 6"/><path d="M4 4h16v16H4z"/></svg></MetricCard>
      <MetricCard label="Results available" value={meanCoverage === null ? "—" : `${meanCoverage}%`} detail="Average across the saved runs" meaning="100% means every planned case produced a stored result." tone="blue"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"/><path d="M12 4v8l5 3"/></svg></MetricCard>
      <MetricCard label="Latest automated score" value={latestSummary === null ? "—" : `${latestSummary}%`} detail={signedDelta(latestSummary, previousSummary)} meaning="A rule-based summary for quick comparison—not a human safety rating." tone="violet"><svg viewBox="0 0 24 24"><path d="M4 17l5-5 4 3 7-8"/><path d="M16 7h4v4"/></svg></MetricCard>
      <MetricCard label="Average warning level" value={threat === null ? "—" : `${threat}%`} detail={latest?.formula_version ? "Calculated with the current rule formula" : "No measurement yet"} meaning="Higher values mean the rules found more potentially risky response patterns." tone="orange"><svg viewBox="0 0 24 24"><path d="M12 3l9 16H3L12 3z"/><path d="M12 9v4m0 3h.01"/></svg></MetricCard>

      <AnalyticsDonut counts={counts} />
      <ComparisonLineChart scores={scores} />
      <LatestRunCard score={latest} />
      <RecentRuns scores={scores} />
    </section>
    <MetricsReport scores={scores} />
  </div>;
}
