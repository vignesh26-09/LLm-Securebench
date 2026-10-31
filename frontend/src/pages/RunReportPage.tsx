import { Link, useParams } from "react-router-dom";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../api/client";
import { ErrorState, LoadingState } from "../components/common/AsyncState";
import { ResponseTimePlot } from "../components/charts/ResponseTimePlot";
import { RunMetricPlots } from "../components/charts/RunMetricPlots";
import { ModelMetricInventory } from "../components/metrics/ModelMetricInventory";
import { PuzzleMetricsGrid } from "../components/charts/PuzzleMetricsGrid";
import { ModelSelectionCard } from "../components/metrics/ModelSelectionCard";
import { ChevronDown, ChevronUp, MessageSquare, Terminal, Clock, ShieldAlert } from "lucide-react";

function percent(value: number | null | undefined) {
  return typeof value === "number" ? `${(value * 100).toFixed(1)}%` : "Not computed";
}

export function RunReportPage() {
  const { runId } = useParams();
  const [caseLimit, setCaseLimit] = useState(50);
  const [expandedCase, setExpandedCase] = useState<string | null>(null);
  const report = useQuery({ 
    queryKey: ["benchmark-run-report", runId], 
    queryFn: () => apiClient.runReport(runId ?? ""), 
    enabled: Boolean(runId), 
    retry: false 
  });

  return (
    <section className="run-report">
      <nav className="flow-stepper" aria-label="Evaluation steps">
        <span><b>01</b> Choose model</span>
        <span><b>02</b> Live testing</span>
        <span className="current"><b>03</b> Charts & results</span>
      </nav>

      <div className="report-hero">
        <div>
          <div className="eyebrow">Benchmark result</div>
          <h1>{report.data?.run.model_name ?? "Run report"}</h1>
          <p>Completed benchmark evidence, ready for inspection.</p>
        </div>
        {report.data && (
          <div className="run-id">
            <span>Run ID</span>
            <code>{report.data.run.id.slice(0, 12)}</code>
          </div>
        )}
      </div>

      {report.isLoading && <LoadingState />}
      {report.isError && <ErrorState error={report.error} />}

      {report.data && (
        <>
          <div className="stat-grid run-report-stats">
            <article>
              <span>Answers saved</span>
              <strong>{report.data.execution.completed_cases}/{report.data.execution.total_cases}</strong>
              <small>{percent(report.data.execution.coverage)} of planned test cases finished</small>
            </article>
            <article>
              <span>Average response time</span>
              <strong>{report.data.execution.mean_latency_ms === null ? "—" : `${(report.data.execution.mean_latency_ms / 1000).toFixed(2)}s`}</strong>
              <small>Time taken to produce one answer</small>
            </article>
            <article>
              <span>Automated score</span>
              <strong>{percent(report.data.model_score.value)}</strong>
              <small>Safety rule summary across cases</small>
            </article>
          </div>

          {/* Executive Model Selection Card */}
          <ModelSelectionCard report={report.data} />

          {/* 10-Prompt Puzzle Box Breakdown */}
          <PuzzleMetricsGrid report={report.data} />

          {/* Interactive Metric Charts */}
          <RunMetricPlots report={report.data} />
          <ResponseTimePlot cases={report.data.cases} />
          <ModelMetricInventory report={report.data} />

          {/* Detailed Prompts & LLM Responses Table */}
          <div className="report-section-heading" style={{ marginTop: "2.5rem" }}>
            <div>
              <div className="eyebrow">PROMPT & RESPONSE INSPECTION</div>
              <h2>Model Responses & Attack Transcripts</h2>
              <p style={{ color: "var(--muted, #94a3b8)", fontSize: "0.88rem", margin: "0.25rem 0 0" }}>
                Click any case to inspect the exact input prompt, model output, and threat indicators.
              </p>
            </div>
            <span>{report.data.execution.completed_cases}/{report.data.execution.total_cases} cases</span>
          </div>

          {report.data.cases.length === 0 && <p className="empty">No case results were saved for this run.</p>}

          <div className="case-transcript-table" style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            {report.data.cases.slice(0, caseLimit).map((item, index) => {
              const isExpanded = expandedCase === item.id;
              const hasSignals = item.observed_detector_signals && item.observed_detector_signals.length > 0;

              return (
                <div 
                  key={item.id} 
                  style={{
                    background: "#141414",
                    border: isExpanded ? "1px solid #ff7a2160" : "1px solid #272727",
                    borderRadius: "10px",
                    overflow: "hidden",
                    transition: "all 0.15s ease"
                  }}
                >
                  {/* Case Header Strip */}
                  <div 
                    onClick={() => setExpandedCase(isExpanded ? null : item.id)}
                    style={{
                      padding: "14px 18px",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      cursor: "pointer",
                      background: isExpanded ? "rgba(255, 122, 33, 0.05)" : "transparent"
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: "14px", flex: 1, minWidth: 0 }}>
                      <span style={{ 
                        fontFamily: "monospace", 
                        fontSize: "0.85rem", 
                        color: "#ff7a21", 
                        background: "rgba(255, 122, 33, 0.1)", 
                        padding: "2px 8px", 
                        borderRadius: "4px" 
                      }}>
                        #{String(index + 1).padStart(2, "0")}
                      </span>
                      <strong style={{ fontSize: "0.95rem", color: "#f3f4f6" }}>
                        {item.case_id ?? item.id}
                      </strong>
                      <span style={{ 
                        fontSize: "0.78rem", 
                        padding: "2px 8px", 
                        borderRadius: "12px", 
                        background: hasSignals ? "rgba(239, 68, 68, 0.15)" : "rgba(16, 185, 129, 0.15)",
                        color: hasSignals ? "#ef4444" : "#10b981",
                        border: hasSignals ? "1px solid rgba(239, 68, 68, 0.3)" : "1px solid rgba(16, 185, 129, 0.3)"
                      }}>
                        {hasSignals ? "Threat Detected" : "Safe Refusal / Pass"}
                      </span>
                    </div>

                    <div style={{ display: "flex", alignItems: "center", gap: "18px" }}>
                      <span style={{ display: "flex", alignItems: "center", gap: "5px", color: "#9ca3af", fontSize: "0.82rem" }}>
                        <Clock size={14} />
                        {item.latency_ms === null ? "—" : `${(item.latency_ms / 1000).toFixed(2)}s`}
                      </span>
                      <button 
                        type="button" 
                        style={{ background: "none", border: "none", color: "#888", cursor: "pointer", display: "flex", alignItems: "center" }}
                      >
                        {isExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                      </button>
                    </div>
                  </div>

                  {/* Expanded Prompt & LLM Response Box */}
                  {isExpanded && (
                    <div style={{ padding: "0 18px 18px", borderTop: "1px solid #222", background: "#0d0d0d" }}>
                      {/* Input Prompt */}
                      <div style={{ marginTop: "14px" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "#ff944d", fontSize: "0.8rem", fontWeight: 600, marginBottom: "6px" }}>
                          <Terminal size={14} /> INPUT PROMPT / ATTACK PAYLOAD
                        </div>
                        <div style={{
                          background: "#181818",
                          border: "1px solid #2e2e2e",
                          borderRadius: "8px",
                          padding: "12px 14px",
                          fontFamily: "monospace",
                          fontSize: "0.86rem",
                          lineHeight: 1.5,
                          color: "#e5e7eb",
                          maxHeight: "180px",
                          overflowY: "auto",
                          whiteSpace: "pre-wrap"
                        }}>
                          {item.prompt ?? "(Prompt payload stored in benchmark corpus)"}
                        </div>
                      </div>

                      {/* LLM Response */}
                      <div style={{ marginTop: "14px" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "#38bdf8", fontSize: "0.8rem", fontWeight: 600, marginBottom: "6px" }}>
                          <MessageSquare size={14} /> MODEL OUTPUT / RESPONSE
                        </div>
                        <div style={{
                          background: "#161b22",
                          border: "1px solid #1e293b",
                          borderRadius: "8px",
                          padding: "12px 14px",
                          fontFamily: "inherit",
                          fontSize: "0.88rem",
                          lineHeight: 1.6,
                          color: "#f1f5f9",
                          maxHeight: "240px",
                          overflowY: "auto",
                          whiteSpace: "pre-wrap"
                        }}>
                          {item.response ?? "(Model output was empty or timed out)"}
                        </div>
                      </div>

                      {/* Detector Warning Signals */}
                      {hasSignals && (
                        <div style={{ marginTop: "14px" }}>
                          <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "#ef4444", fontSize: "0.8rem", fontWeight: 600, marginBottom: "6px" }}>
                            <ShieldAlert size={14} /> DETECTOR FLAGS
                          </div>
                          <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
                            {item.observed_detector_signals.map(s => (
                              <span key={s.detector} style={{
                                background: "rgba(239, 68, 68, 0.15)",
                                border: "1px solid rgba(239, 68, 68, 0.3)",
                                color: "#f87171",
                                padding: "4px 10px",
                                borderRadius: "6px",
                                fontSize: "0.78rem"
                              }}>
                                {s.detector}: <strong>{(s.score * 100).toFixed(1)}% threat</strong>
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {report.data.cases.length > caseLimit && (
            <button 
              className="verify-connection" 
              type="button" 
              onClick={() => setCaseLimit(current => current + 50)}
              style={{ marginTop: "1rem" }}
            >
              Show next 50 cases ({caseLimit.toLocaleString()} of {report.data.cases.length.toLocaleString()} shown)
            </button>
          )}

          <div className="report-actions" style={{ marginTop: "2rem" }}>
            <Link className="primary-button inline-action" to="/benchmark">
              Run another benchmark →
            </Link>
            <Link to="/history">Browse All Benchmark Runs</Link>
          </div>
        </>
      )}
    </section>
  );
}
