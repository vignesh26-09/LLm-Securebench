import type { ScientificRecord } from "../../api/types";
import { Link } from "react-router-dom";

function objects(value: unknown): Record<string, unknown>[] {
  return Array.isArray(value) ? value.filter((item): item is Record<string, unknown> => item !== null && typeof item === "object") : [];
}

export function EvidenceSummary({ record }: { record: ScientificRecord }) {
  const payload = record.payload;
  const rows = record.family === "draa" ? objects(payload.features).map(f => [String(f.namespace), String(f.name), JSON.stringify(f.raw_value), String(f.status)])
    : record.family === "pri" ? objects(payload.cells).map(f => [String(f.benchmark_category ?? "No category"), String(f.source_feature_name), JSON.stringify(f.value), String(f.status)])
    : record.family === "ml" && payload.metric_formulas && typeof payload.metric_formulas === "object" ? Object.entries(payload.metric_formulas).map(([key, value]) => ["supervised ML", key, String(value), String(payload.status)])
    : record.family === "model_score" && payload.formula && typeof payload.formula === "object" ? Object.entries(payload.formula).map(([key, value]) => ["engineering detector score", key, String(value), String(record.status)])
    : record.family === "statistics" && payload.values && typeof payload.values === "object" ? Object.entries(payload.values).map(([key, value]) => [String(record.provenance.units ?? "source units"), key, value === null ? "null" : typeof value === "number" ? value.toFixed(3) : JSON.stringify(value), String(payload.computation_status)]) : [];
  if (!rows.length) return null;
  const run = record.provenance.benchmark_run_id;
  return <article className="research-note evidence-summary"><h2>{record.family === "statistics" ? "Descriptive execution measurements" : record.family === "pri" ? "Observed profile cells" : "Source evidence features"}</h2><p>{String(record.provenance.kind ?? "Source-native artifact")} · {record.status}</p>
    {record.provenance.kind === "local_model_pilot" && <p>Actual local-model output on the repository example. Detector signals use existing engineering smoke rules and are not security verdicts.</p>}
    {record.family === "ml" && <p>Supervised ML is blocked until independent labels are supplied. Detector outputs can be features, but they are not labels.</p>}
    {record.family === "statistics" && <p>Measurements: {String(payload.n_valid)}. Latency includes model loading; this is not a controlled speed comparison.</p>}
    <div className="table-wrap"><table className="entity-table"><thead><tr><th>Source / units</th><th>Measurement</th><th>Value</th><th>Status</th></tr></thead><tbody>{rows.map((row, i) => <tr key={i}>{row.map((cell, j) => <td key={j}>{cell}</td>)}</tr>)}</tbody></table></div>
    {typeof run === "string" && <p><Link to={`/evaluations?filter_by=benchmark_run_id&value=${encodeURIComponent(run)}`}>Inspect originating responses →</Link></p>}
  </article>;
}
