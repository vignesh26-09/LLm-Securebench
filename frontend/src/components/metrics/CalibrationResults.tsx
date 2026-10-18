import { useQuery } from "@tanstack/react-query";
import type { CSSProperties } from "react";
import { apiClient } from "../../api/client";
import { ErrorState, LoadingState } from "../common/AsyncState";

const pct = (value: number) => `${(value * 100).toFixed(1)}%`;

export function CalibrationResults() {
  const query = useQuery({ queryKey: ["calibration-summary"], queryFn: apiClient.calibrationSummary, retry: false });
  if (query.isLoading) return <LoadingState />;
  if (query.isError) return <ErrorState error={query.error} />;
  if (!query.data) return null;
  const { result, source_manifest: source } = query.data;
  const cells = [["Predicted 0 / Human 0", result.confusion_matrix.pred_0_label_0], ["Predicted 0 / Human 1", result.confusion_matrix.pred_0_label_1], ["Predicted 1 / Human 0", result.confusion_matrix.pred_1_label_0], ["Predicted 1 / Human 1", result.confusion_matrix.pred_1_label_1]];
  const max = Math.max(...cells.map(([, value]) => Number(value)));
  return <section className="calibration-results"><div className="section-title"><div><div className="eyebrow">Verified external calibration</div><h2>Judge–human alignment</h2></div><span className="status status-uncalibrated">Human replacement blocked</span></div><div className="metrics-row"><article><span>Source records</span><strong>{result.source_n}</strong><small>{result.usable_n} usable pairs</small></article><article><span>Coverage</span><strong>{pct(result.coverage)}</strong><small>Usable / source records</small></article><article><span>Raw agreement</span><strong>{pct(result.raw_agreement)}</strong><small>Not a safety percentage</small></article><article><span>Cohen’s κ</span><strong>{result.cohen_kappa.toFixed(3)}</strong><small>No confidence interval is available</small></article></div><div className="calibration-grid"><article className="heatmap-panel"><h3>Observed confusion matrix</h3><div className="heatmap">{cells.map(([label, value]) => <div key={String(label)} className="heat-cell" style={{ "--heat": String(Number(value) / max) } as CSSProperties}><span>{label}</span><strong>{value}</strong></div>)}</div><small>Rows are displayed as recorded prediction/human label pairs across usable records.</small></article><article className="calibration-note"><h3>Interpretation</h3><p>{query.data.interpretation}</p><dl><div><dt>Dataset revision</dt><dd><code>{source.dataset_revision.slice(0, 12)}</code></dd></div><div><dt>Source checksum</dt><dd><code>{source.sha256.slice(0, 12)}</code></dd></div></dl></article></div></section>;
}
