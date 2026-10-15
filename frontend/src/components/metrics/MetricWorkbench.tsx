import { useState } from "react";
import { apiClient } from "../../api/client";

const fields: Record<string, string> = {
  bsda: "value (matched baseline and perturbed responses)",
  recovery: "value (baseline, attack and recovery states); calibration optional",
  saea: "value (sequence and matched isolated controls)",
  draa: "records (typed evidence records)",
  pri: "profile (typed robustness profile)",
  dqi: "dataset; embeddings optional for semantic novelty",
  ml: "experiment_id, task, schema, features, targets, manifest, logistic_config",
  statistics: "values (finite numbers in one unit)",
};

export function MetricWorkbench({ fixedMetric, onSaved }: { fixedMetric?: string; onSaved?: () => void } = {}) {
  const [selectedMetric, setSelectedMetric] = useState("statistics");
  const metric = fixedMetric ?? selectedMetric;
  const [input, setInput] = useState("");
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [saved, setSaved] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  function parseInput(): Record<string, unknown> {
    const parsed: unknown = JSON.parse(input);
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      throw new Error("Supply a JSON object with the required fields.");
    }
    return parsed as Record<string, unknown>;
  }

  async function compute() {
    setError(""); setResult(null); setSaved(null); setBusy(true);
    try { setResult(await apiClient.computeMetric(metric, parseInput())); }
    catch (problem) { setError(problem instanceof Error ? problem.message : "Calculation failed."); }
    finally { setBusy(false); }
  }

  async function save() {
    setError(""); setBusy(true);
    try {
      const response = await apiClient.saveMetric(metric, parseInput());
      setSaved(String(response.record_id));
      onSaved?.();
    } catch (problem) { setError(problem instanceof Error ? problem.message : "Saving failed."); }
    finally { setBusy(false); }
  }

  return <details className="metric-workbench" open={fixedMetric ? true : undefined}>
    <summary>{fixedMetric ? `Calculate ${fixedMetric.toUpperCase()} from measured inputs` : "Calculate an additional metric from your own inputs"}</summary>
    <p>The backend runs the existing metric engine. Caller-supplied calculations remain engineering evidence until inputs and calibration are independently verified.</p>
    {!fixedMetric && <label>Metric engine<select value={metric} disabled={busy} onChange={event => { setSelectedMetric(event.target.value); setResult(null); setSaved(null); setError(""); }}>{Object.keys(fields).map(engine => <option key={engine} value={engine}>{engine.toUpperCase()}</option>)}</select></label>}
    <p className="tiny-note">Required input: {fields[metric]}. The typed contract and examples are in <code>docs/METRIC_BACKEND_API.md</code>.</p>
    <label>Metric input JSON<textarea rows={7} disabled={busy} value={input} onChange={event => { setInput(event.target.value); setResult(null); setSaved(null); setError(""); }} placeholder={metric === "statistics" ? '{"values": [your measured values]}' : "Paste a JSON object with the required measured inputs"} /></label>
    <label className="metric-upload">Or import a JSON file<input type="file" disabled={busy} accept=".json,application/json" onChange={async event => { const file = event.target.files?.[0]; if (!file) return; setResult(null); setSaved(null); if (file.size > 2_000_000) { setError("Choose a JSON file smaller than 2 MB."); return; } try { setInput(await file.text()); setError(""); } catch { setError("Unable to read this file."); } }} /></label>
    <button className="primary-button" type="button" disabled={busy || !input.trim()} onClick={compute}>{busy ? "Calculating…" : "Calculate metric"}</button>
    <div aria-live="polite">{error && <p role="alert">{error}</p>}{result && <><h3>Calculation result: {String(result.status).replaceAll("_", " ")}</h3><p>Caller-supplied inputs · not independently verified · not saved to this model run.</p><pre>{JSON.stringify(result.result ?? result, null, 2)}</pre>{!saved && <button type="button" disabled={busy} onClick={save}>Save as engineering record</button>}{saved && <p>Saved engineering record <code>{saved}</code>. This does not validate the metric or attach it to a model run.</p>}</>}</div>
  </details>;
}
