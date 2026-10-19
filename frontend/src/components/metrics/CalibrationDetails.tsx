import { useQuery } from "@tanstack/react-query";

type Criterion = { text: string; met: boolean | null; measured_value: unknown; threshold: string | number | null; source_path: string };
export type Calibration = {
  status: "established" | "not_established"; scope: string | null; evidence_scope?: string;
  criteria: Criterion[]; missing_evidence: string[];
  measurements: { name: string; value: unknown; unit: string; source_path: string; scope: string }[];
  artifact_sha256?: Record<string, string>;
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
