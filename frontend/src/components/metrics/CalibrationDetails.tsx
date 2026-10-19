import { useQuery } from "@tanstack/react-query";

type Criterion = { text: string; met: boolean | null; measured_value: unknown; threshold: string | number | null; source_path: string };
type ObjectiveMetrics = { pr_auc: number | null; recall: number | null; precision: number | null; accuracy: number | null };
type Objective = {
  kind: "hallucination_proxy" | "prediction"; scope: string; source_run: string; source_path: string; limitations: string[];
  gate?: { completed: number; failed: number; positives: number; mixed_template_groups: number };
  hallucination_proxy?: Record<string, { assigned_pairs: number; complete_pairs: number; lift: number | null; ci95: number[] | null; counts: Record<string, Record<string, number>> }>;
  prediction?: Record<string, { logistic: ObjectiveMetrics; majority: ObjectiveMetrics; comparison: string; folds: { threshold_train_only?: number }[]; bootstrap: Record<string, Record<string, { ci95: number[] | null; undefined_resamples: number }>> }>;
};
export type Calibration = {
  status: "established" | "not_established"; scope: string | null; evidence_scope?: string;
  criteria: Criterion[]; missing_evidence: string[];
  measurements: { name: string; value: unknown; unit: string; source_path: string; scope: string }[];
  artifact_sha256?: Record<string, string>;
  objective_evidence?: Objective | null;
};

function measured(value: unknown, unit?: string): string {
  if (value === null || value === undefined) return "Unavailable";
  if (typeof value === "number" && unit === "ratio") return `${(value * 100).toFixed(2)}%`;
  return typeof value === "object" ? JSON.stringify(value) : String(value);
}

export function CalibrationDetails({ calibration, loading, error }: { calibration?: Calibration; loading?: boolean; error?: boolean }) {
  const valid = calibration && Array.isArray(calibration.criteria) && Array.isArray(calibration.missing_evidence) && Array.isArray(calibration.measurements);
  const established = valid && calibration.status === "established" && Boolean(calibration.scope) && calibration.criteria.length > 0 && calibration.criteria.every(item => item.met === true);
  return <details className="research-note">
    <summary>Calibration details</summary>
    {loading ? <p>Loading calibration criteria and evidence.</p> : error ? <p>Unavailable: calibration evidence could not be loaded. Needs a successful evidence API response.</p> : !valid ? <p>Unavailable: needs a calibration checklist and source evidence from the API.</p> : <>
      <p>Scientific calibration: {established ? `Established (scope: ${calibration.scope})` : "Not established; the required scientific gates are not all met."}</p>
      <p>{calibration.evidence_scope ?? "Evidence scope unavailable; no general calibration claim is inferred."}</p>
      {calibration.objective_evidence && <ObjectiveEvidence evidence={calibration.objective_evidence} />}
      {!calibration.criteria.length && <p>Unavailable: needs documented calibration criteria.</p>}
      <ul>{calibration.criteria.map((item, index) => <li key={index}>
        <strong>{item.met === true ? "Pass" : item.met === false ? "Fail" : "Unknown"}</strong>: {item.text}
        <p>Measured: {measured(item.measured_value)}. Required: {measured(item.threshold)}. Source: <code>{item.source_path}</code>.</p>
      </li>)}</ul>
      <h3>Available measurements</h3>
      {!calibration.measurements.length ? <p>Unavailable: no measured calibration evidence is recorded.</p> : <div className="table-wrap"><table>
        <caption>Descriptive calibration evidence; not automatic scientific approval</caption>
        <thead><tr><th>Measurement</th><th>Value</th><th>Units</th><th>Evidence scope and limitations</th><th>Source</th></tr></thead>
        <tbody>{calibration.measurements.map((item, index) => <tr key={index}><td>{item.name}</td><td>{measured(item.value, item.unit)}</td><td>{item.unit}</td><td>{item.scope}</td><td><code>{item.source_path}</code></td></tr>)}</tbody>
      </table></div>}
      <h3>Missing evidence</h3>
      {calibration.missing_evidence.length ? <ul>{calibration.missing_evidence.map((item, index) => <li key={index}>{item}</li>)}</ul> : <p>No unmet criteria in the stated scope. This does not establish other claims.</p>}
      {calibration.artifact_sha256 && Object.keys(calibration.artifact_sha256).length > 0 && <details><summary>Source artifact hashes</summary><ul>{Object.entries(calibration.artifact_sha256).map(([path, hash]) => <li key={path}><code>{path}</code>: <code>{hash}</code></li>)}</ul></details>}
    </>}
  </details>;
}

function interval(value: number[] | null | undefined): string {
  return value ? `[${value.map(v => v.toFixed(4)).join(", ")}]` : "Unavailable";
}

function ObjectiveEvidence({ evidence }: { evidence: Objective }) {
  return <section aria-label="Objective calibration experiment">
    <h3>Objective synthetic experiment</h3><p>{evidence.scope}</p>
    <p>Source: <code>{evidence.source_path}</code>; raw local run: <code>{evidence.source_run}</code>. Scientific calibration remains Not established.</p>
    {evidence.gate && <p>Separate oracle-emission dataset: {evidence.gate.completed} completed, {evidence.gate.failed} failed/incomplete excluded, {evidence.gate.positives} objective positives, {evidence.gate.mixed_template_groups} mixed-class template groups. Prediction metrics apply only to completed outputs.</p>}
    {evidence.kind === "hallucination_proxy" && evidence.hallucination_proxy && <>
      <p>Ungrounded minus grounded hallucinated-answer rate over complete pairs. This is a context-availability proxy, not canonical adversarial MCHL. Abstention is not proof of factual competence; malformed and failed responses are excluded.</p>
      <div className="table-wrap"><table><caption>Objective context proxy by model</caption>
        <thead><tr><th>Model</th><th>Complete / assigned pairs</th><th>Lift</th><th>Bootstrap 95% CI</th></tr></thead>
        <tbody>{Object.entries(evidence.hallucination_proxy).map(([model, item]) => <tr key={model}><td>{model}</td><td>{item.complete_pairs} / {item.assigned_pairs}</td><td>{measured(item.lift, "ratio")}</td><td>{interval(item.ci95)}</td></tr>)}</tbody>
      </table></div>
      <div className="table-wrap"><table><caption>Answer outcomes, including abstentions and failures</caption>
        <thead><tr><th>Model</th><th>Condition</th><th>Correct</th><th>Abstain</th><th>Hallucinated</th><th>Failed/unscored</th></tr></thead>
        <tbody>{Object.entries(evidence.hallucination_proxy).flatMap(([model, item]) => Object.entries(item.counts).map(([arm, counts]) => <tr key={`${model}:${arm}`}><td>{model}</td><td>{arm}</td>{["correct", "abstain", "hallucinated", "failed"].map(name => <td key={name}>{measured(counts[name])}</td>)}</tr>))}</tbody>
      </table></div>
    </>}
    {evidence.kind === "prediction" && evidence.prediction && Object.entries(evidence.prediction).map(([group, result]) => <article key={group}>
      <h4>Leave one {group === "template_id" ? "template" : "model"} out</h4>
      <p>{result.comparison}. Model holdouts share prompt instances; template holdouts test unseen templates.</p>
      <div className="table-wrap"><table><caption>{group} holdout: logistic versus training-majority baseline</caption>
        <thead><tr><th>Metric</th><th>Logistic</th><th>95% CI</th><th>Majority baseline</th><th>95% CI</th><th>Paired difference CI</th></tr></thead>
        <tbody>{(["pr_auc", "recall", "precision", "accuracy"] as const).map(name => <tr key={name}><td>{name === "pr_auc" ? "PR-AUC (Average Precision)" : name}</td><td>{measured(result.logistic[name], "ratio")}</td><td>{interval(result.bootstrap.logistic[name].ci95)}</td><td>{measured(result.majority[name], "ratio")}</td><td>{interval(result.bootstrap.majority[name].ci95)}</td><td>{interval(result.bootstrap.difference[name].ci95)}</td></tr>)}</tbody>
      </table></div>
      <p>Operating thresholds are chosen from training scores only: {result.folds.map(fold => fold.threshold_train_only === undefined ? "Unavailable" : String(fold.threshold_train_only)).join(", ")}. CI resampling uses whole template clusters of fixed out-of-fold predictions; undefined intervals remain unavailable.</p>
      {result.bootstrap.difference.pr_auc.ci95 && result.bootstrap.difference.pr_auc.ci95[0] <= 0 && <p>No clear PR-AUC improvement: the paired difference interval includes zero or negative values.</p>}
    </article>)}
    <ul>{evidence.limitations.map((text, index) => <li key={index}>{text}</li>)}</ul>
  </section>;
}

export function ReviewCalibrationDetails() {
  const query = useQuery<{ calibration?: Calibration }>({
    queryKey: ["metric-calibration", "reviews"], retry: false,
    queryFn: async () => {
      const response = await fetch(`${import.meta.env.VITE_SECURELLM_API_BASE_URL ?? ""}/metrics/compute/reviews/evidence`, { credentials: "include", headers: { Accept: "application/json" } });
      if (!response.ok) throw new Error(`Calibration evidence HTTP ${response.status}`);
      return response.clone().json();
    },
  });
  return <CalibrationDetails calibration={query.data?.calibration} loading={query.isLoading} error={query.isError} />;
}
