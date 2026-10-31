import type { BenchmarkRunReport } from "../../api/types";
import { useState } from "react";
import { AlertOctagon, TrendingUp } from "lucide-react";

export function RunMetricPlots({ report }: { report: BenchmarkRunReport }) {
  const [activeTab, setActiveTab] = useState<"overview" | "detectors">("overview");

  const values = [
    { name: "Automated Safety Score", value: report.model_score.value, desc: "Harm prevention rate across test prompts" },
    { name: "Mean Threat Score", value: report.model_score.mean_threat_score, desc: "Average detected adversarial signal strength" },
    { name: "Worst-Case Threat", value: report.model_score.worst_case_threat_score, desc: "Highest single-case adversarial exposure" },
  ] as const;

  const maximumSignals = Math.max(1, ...report.detector_summary.map(item => item.observed_signal_count));

  return (
    <div className="run-plot-pair" style={{ display: "grid", gridTemplateColumns: "1fr", gap: "1.5rem", marginTop: "1.5rem" }}>
      <article className="studio-panel" style={{ background: "#141414", border: "1px solid #282828", borderRadius: "12px", padding: "24px" }}>
        {/* Tab Header */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1.25rem", borderBottom: "1px solid #222", paddingBottom: "12px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span className="studio-eyebrow" style={{ margin: 0 }}>METRIC VISUALIZATION</span>
            <h2 style={{ fontSize: "1.15rem", margin: 0, fontWeight: 600 }}>Security Metrics & Detector Distribution</h2>
          </div>
          <div style={{ display: "flex", gap: "8px" }}>
            <button
              type="button"
              onClick={() => setActiveTab("overview")}
              style={{
                background: activeTab === "overview" ? "rgba(255, 122, 33, 0.15)" : "transparent",
                border: activeTab === "overview" ? "1px solid #ff7a21" : "1px solid #333",
                color: activeTab === "overview" ? "#ff7a21" : "#888",
                padding: "5px 12px",
                borderRadius: "6px",
                cursor: "pointer",
                fontSize: "0.82rem",
                display: "flex",
                alignItems: "center",
                gap: "5px"
              }}
            >
              <TrendingUp size={14} /> Metric Summary
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("detectors")}
              style={{
                background: activeTab === "detectors" ? "rgba(255, 122, 33, 0.15)" : "transparent",
                border: activeTab === "detectors" ? "1px solid #ff7a21" : "1px solid #333",
                color: activeTab === "detectors" ? "#ff7a21" : "#888",
                padding: "5px 12px",
                borderRadius: "6px",
                cursor: "pointer",
                fontSize: "0.82rem",
                display: "flex",
                alignItems: "center",
                gap: "5px"
              }}
            >
              <AlertOctagon size={14} /> Detector Triggers ({report.detector_summary.length})
            </button>
          </div>
        </div>

        {/* Tab 1: Column Metric Overview */}
        {activeTab === "overview" && (
          <div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "1rem", marginBottom: "1.5rem" }}>
              {values.map(({ name, value, desc }) => {
                const pctVal = value != null ? (value * 100).toFixed(1) : "—";
                const isSafety = name.includes("Safety");
                return (
                  <div key={name} style={{ background: "#1c1c1c", border: "1px solid #303030", borderRadius: "8px", padding: "16px" }}>
                    <span style={{ fontSize: "0.82rem", color: "#9ca3af" }}>{name}</span>
                    <div style={{ fontSize: "1.8rem", fontWeight: 700, margin: "6px 0", color: isSafety ? "#10b981" : value && value > 0.4 ? "#ef4444" : "#f59e0b" }}>
                      {value != null ? `${pctVal}%` : "Not computed"}
                    </div>
                    <div style={{ height: "6px", background: "#282828", borderRadius: "3px", overflow: "hidden", margin: "8px 0" }}>
                      <div 
                        style={{ 
                          width: `${Math.max(4, Math.min(100, Number(pctVal)))}%`, 
                          height: "100%", 
                          background: isSafety ? "#10b981" : value && value > 0.4 ? "#ef4444" : "#f59e0b" 
                        }} 
                      />
                    </div>
                    <small style={{ color: "#6b7280", fontSize: "0.75rem" }}>{desc}</small>
                  </div>
                );
              })}
            </div>
            <p style={{ fontSize: "0.82rem", color: "#64748b", margin: 0 }}>
              💡 <strong>Interpretation:</strong> A higher Safety Score indicates reliable refusal of harmful queries. Mean Threat Score reflects how close the model came to partial jailbreak compliance.
            </p>
          </div>
        )}

        {/* Tab 2: Detector Warning Breakdown */}
        {activeTab === "detectors" && (
          <div>
            {report.detector_summary.length === 0 ? (
              <p style={{ color: "#888", padding: "1.5rem 0", textAlign: "center" }}>
                ✅ Zero detector triggers recorded for this benchmark run. All safety filters held firm.
              </p>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                {report.detector_summary.map(item => (
                  <div key={item.detector} style={{ background: "#1c1c1c", border: "1px solid #2e2e2e", borderRadius: "8px", padding: "12px 16px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                      <strong style={{ fontSize: "0.9rem", color: "#e5e7eb" }}>{item.detector}</strong>
                      <span style={{ fontSize: "0.82rem", color: "#ff7a21", fontWeight: 600 }}>
                        {item.observed_signal_count} {item.observed_signal_count === 1 ? "trigger" : "triggers"} (max threat: {(item.max_score * 100).toFixed(0)}%)
                      </span>
                    </div>
                    <div style={{ height: "6px", background: "#262626", borderRadius: "3px", overflow: "hidden" }}>
                      <div style={{ width: `${(item.observed_signal_count / maximumSignals) * 100}%`, height: "100%", background: "#ff7a21" }} />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </article>
    </div>
  );
}
