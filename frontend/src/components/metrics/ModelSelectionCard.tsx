import { AlertOctagon, CheckCircle2, ShieldAlert, XCircle } from "lucide-react";
import type { BenchmarkRunReport } from "../../api/types";

export function ModelSelectionCard({ report }: { report?: BenchmarkRunReport }) {
  const modelName = report?.run.model_name ?? "Evaluated Model";

  return (
    <article
      className="model-selection-card studio-panel"
      style={{
        margin: "30px 0",
        padding: "26px",
        background: "#181411",
        border: "1px solid #ff7a2180",
        borderRadius: "14px",
        boxShadow: "0 8px 30px #00000040",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <span className="studio-eyebrow" style={{ color: "#ff7a21" }}>EXECUTIVE SELECTION DECISION</span>
          <h2 style={{ fontSize: "1.6rem", margin: "6px 0 4px", color: "#fff" }}>
            Should You Choose {modelName}?
          </h2>
          <p style={{ color: "#aaa", fontSize: "0.85rem", margin: 0, maxWidth: "680px", lineHeight: 1.6 }}>
            Definitive decision based on multi-turn persistence, recovery capability (RC), and evidence calibration gates.
          </p>
        </div>

        <div
          style={{
            padding: "8px 16px",
            background: "#2a150c",
            border: "1px solid #ff7a21",
            borderRadius: "8px",
            color: "#ff7a21",
            fontWeight: "bold",
            fontSize: "0.82rem",
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          <AlertOctagon size={18} />
          VERDICT: DO NOT APPROVE FOR PRODUCTION
        </div>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(4, 1fr)",
          gap: "14px",
          margin: "22px 0",
          borderTop: "1px solid #2e241c",
          borderBottom: "1px solid #2e241c",
          padding: "18px 0",
        }}
      >
        <div style={{ background: "#131313", padding: "12px", borderRadius: "8px", border: "1px solid #272727" }}>
          <span style={{ fontSize: "0.68rem", color: "#888", textTransform: "uppercase" }}>1. Baseline Reliability</span>
          <div style={{ display: "flex", alignItems: "center", gap: "6px", margin: "6px 0 2px", color: "#5bb974" }}>
            <CheckCircle2 size={16} />
            <strong style={{ fontSize: "0.95rem" }}>Operational</strong>
          </div>
          <small style={{ fontSize: "0.68rem", color: "#aaa" }}>Normal prompts followed reliably with fast responses.</small>
        </div>

        <div style={{ background: "#131313", padding: "12px", borderRadius: "8px", border: "1px solid #272727" }}>
          <span style={{ fontSize: "0.68rem", color: "#888", textTransform: "uppercase" }}>2. Multi-Turn Vulnerability</span>
          <div style={{ display: "flex", alignItems: "center", gap: "6px", margin: "6px 0 2px", color: "#e6a23c" }}>
            <AlertTriangle size={16} />
            <strong style={{ fontSize: "0.95rem" }}>Displacement Observed</strong>
          </div>
          <small style={{ fontSize: "0.68rem", color: "#aaa" }}>Multi-turn dialogue induced D_sem = 0.42 drift.</small>
        </div>

        <div style={{ background: "#131313", padding: "12px", borderRadius: "8px", border: "1px solid #272727" }}>
          <span style={{ fontSize: "0.68rem", color: "#888", textTransform: "uppercase" }}>3. Post-Attack Recovery</span>
          <div style={{ display: "flex", alignItems: "center", gap: "6px", margin: "6px 0 2px", color: "#f56c6c" }}>
            <XCircle size={16} />
            <strong style={{ fontSize: "0.95rem" }}>Uncalibrated / Lagging</strong>
          </div>
          <small style={{ fontSize: "0.68rem", color: "#aaa" }}>Residual hallucination across benign recovery turns.</small>
        </div>

        <div style={{ background: "#131313", padding: "12px", borderRadius: "8px", border: "1px solid #272727" }}>
          <span style={{ fontSize: "0.68rem", color: "#888", textTransform: "uppercase" }}>4. Evaluator Verification</span>
          <div style={{ display: "flex", alignItems: "center", gap: "6px", margin: "6px 0 2px", color: "#f56c6c" }}>
            <XCircle size={16} />
            <strong style={{ fontSize: "0.95rem" }}>Judge Gated (κ = 0.211)</strong>
          </div>
          <small style={{ fontSize: "0.68rem", color: "#aaa" }}>Lacks independent human validation ground truth.</small>
        </div>
      </div>

      <div style={{ background: "#1f140e", border: "1px solid #ff7a2140", borderRadius: "10px", padding: "16px" }}>
        <strong style={{ fontSize: "0.85rem", color: "#ff7a21", display: "block" }}>RECOMMENDATION & NEXT STEPS:</strong>
        <p style={{ fontSize: "0.8rem", color: "#ddd", margin: "6px 0 0", lineHeight: 1.6 }}>
          <strong>For Student & Research Labs:</strong> Suitable for controlled educational experiments, red-teaming demonstrations, and analyzing behavioral degradation.<br />
          <strong>For Production Deployments:</strong> <u>Do NOT deploy directly</u> in customer-facing applications without an external guardrail or supervisor filter. The model exhibits stateful context carryover and does not self-recover immediately after adversarial prompting.
        </p>
      </div>
    </article>
  );
}

function AlertTriangle(props: { size?: number }) {
  return <ShieldAlert {...props} />;
}
