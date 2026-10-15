import type { BenchmarkRunReport } from "../../api/types";

export function RunMetricPlots({ report }: { report: BenchmarkRunReport }) {
  const values = [
    ["Automated score", report.model_score.value],
    ["Average warning", report.model_score.mean_threat_score],
    ["Highest warning", report.model_score.worst_case_threat_score],
  ] as const;
  const maximumSignals = Math.max(1, ...report.detector_summary.map(item => item.observed_signal_count));
  return <div className="run-plot-pair"><article className="studio-panel"><span className="studio-eyebrow">CHART 01 / AUTOMATED MEASUREMENTS</span><h2>What did the checks find?</h2><p>Higher score means fewer rule warnings. Higher warning bars mean more detected concerns—not confirmed attacks.</p><div className="simple-column-chart" role="img" aria-label={values.map(([name, value]) => `${name}: ${value == null ? "not measured" : `${(value * 100).toFixed(1)} percent`}`).join("; ")}><div className="column-axis"><span>100%</span><span>50%</span><span>0%</span></div>{values.map(([name, value]) => <div className="column-series" key={name}><div className="column-track"><i style={{ height: `${Math.max(0, Math.min(100, (value ?? 0) * 100))}%` }} /><strong>{value == null ? "N/A" : `${(value * 100).toFixed(1)}%`}</strong></div><span>{name}</span></div>)}</div><small>Same 0–100% display scale, different meanings. These bars are not safety probabilities.</small></article><article className="studio-panel"><span className="studio-eyebrow">CHART 02 / DETECTOR WARNINGS</span><h2>Which rules raised a warning?</h2><p>Each bar counts matches from one detector across this run.</p><div className="report-metric-bars">{report.detector_summary.length === 0 && <p>No detector observations were saved.</p>}{report.detector_summary.map(item => <div key={item.detector}><div><strong>{item.detector}</strong><span>{item.observed_signal_count} matches</span></div><div className="bar-track"><i style={{ width: `${item.observed_signal_count / maximumSignals * 100}%` }} /></div></div>)}</div><small>A match is a reason to inspect the answer. Zero matches does not prove the response is safe.</small></article></div>;
}
