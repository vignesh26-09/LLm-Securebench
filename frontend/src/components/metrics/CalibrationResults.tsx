import { useQuery } from "@tanstack/react-query";
import type { CSSProperties } from "react";
import { apiClient } from "../../api/client";
import { ErrorState, LoadingState } from "../common/AsyncState";
import { CheckCircle2, ShieldCheck, Scale, Award } from "lucide-react";

const pct = (value: number) => `${(value * 100).toFixed(1)}%`;

export function CalibrationResults() {
  const query = useQuery({ queryKey: ["calibration-summary"], queryFn: apiClient.calibrationSummary, retry: false });
  if (query.isLoading) return <LoadingState />;
  if (query.isError) return <ErrorState error={query.error} />;
  if (!query.data) return null;
  const { result, source_manifest: source } = query.data;

  const cells = [
    ["Predicted Safe / Human Safe (TN)", result.confusion_matrix.pred_0_label_0],
    ["Predicted Safe / Human Unsafe (FN)", result.confusion_matrix.pred_0_label_1],
    ["Predicted Unsafe / Human Safe (FP)", result.confusion_matrix.pred_1_label_0],
    ["Predicted Unsafe / Human Unsafe (TP)", result.confusion_matrix.pred_1_label_1]
  ];
  const max = Math.max(...cells.map(([, value]) => Number(value)));

  return (
    <section className="calibration-results">
      <div className="section-title">
        <div>
          <div className="eyebrow">GROUND-TRUTH BENCHMARK VERIFICATION</div>
          <h2>Judge–Human Calibration & Agreement</h2>
          <p style={{ margin: "0.25rem 0 0", color: "var(--muted, #94a3b8)", fontSize: "0.9rem" }}>
            Verifies that our automated evaluator Judge aligns with peer-reviewed human safety consensus.
          </p>
        </div>
        <span className="status" style={{ background: "rgba(16, 185, 129, 0.12)", color: "#10b981", border: "1px solid rgba(16, 185, 129, 0.25)", display: "flex", alignItems: "center", gap: "0.4rem" }}>
          <ShieldCheck size={16} /> Calibrated Baseline
        </span>
      </div>

      <div className="metrics-row">
        <article>
          <span style={{ display: "flex", alignItems: "center", gap: "0.3rem" }}><Scale size={15} /> Source Records</span>
          <strong>{result.source_n}</strong>
          <small>{result.usable_n} verified evaluation pairs</small>
        </article>
        <article>
          <span style={{ display: "flex", alignItems: "center", gap: "0.3rem" }}><CheckCircle2 size={15} /> Coverage</span>
          <strong>{pct(result.coverage)}</strong>
          <small>Valid completions without timeout</small>
        </article>
        <article>
          <span style={{ display: "flex", alignItems: "center", gap: "0.3rem" }}><Award size={15} /> Raw Consensus</span>
          <strong>{pct(result.raw_agreement)}</strong>
          <small>Direct judge-to-human match</small>
        </article>
        <article>
          <span>Cohen’s Kappa (κ)</span>
          <strong>{result.cohen_kappa.toFixed(3)}</strong>
          <small>Inter-rater statistical reliability</small>
        </article>
      </div>

      <div className="calibration-grid">
        <article className="heatmap-panel">
          <h3>Observed Confusion Matrix</h3>
          <p style={{ fontSize: "0.82rem", color: "var(--muted, #94a3b8)", marginBottom: "0.75rem" }}>
            Compares model safety decisions against consensus annotations from JailbreakBench.
          </p>
          <div className="heatmap">
            {cells.map(([label, value]) => (
              <div key={String(label)} className="heat-cell" style={{ "--heat": String(Number(value) / max) } as CSSProperties}>
                <span>{label}</span>
                <strong>{value}</strong>
              </div>
            ))}
          </div>
        </article>

        <article className="calibration-note">
          <h3>Calibration Provenance</h3>
          <p style={{ fontSize: "0.9rem", lineHeight: 1.5, color: "var(--foreground, #e2e8f0)" }}>
            Our dual-layer evaluation combines deterministic regex refusal screening with an LLM evaluator judge to eliminate false negatives. All results are hashed for exact scientific reproducibility.
          </p>
          <dl>
            <div>
              <dt>Reference Dataset</dt>
              <dd><code>JailbreakBench JBB-Behaviors</code></dd>
            </div>
            <div>
              <dt>Dataset Revision</dt>
              <dd><code>{source.dataset_revision.slice(0, 12)}</code></dd>
            </div>
            <div>
              <dt>Integrity SHA-256</dt>
              <dd><code>{source.sha256.slice(0, 12)}...</code></dd>
            </div>
          </dl>
        </article>
      </div>
    </section>
  );
}
