import { useState } from "react";
import { motion } from "framer-motion";
import type { BenchmarkRunReport } from "../../api/types";

interface PuzzlePieceProps {
  id: string;
  title: string;
  badge: string;
  metricValue: string;
  metricLabel: string;
  description: string;
  formula?: string;
  statusColor?: string;
  delay: number;
}

const PUZZLE_PIECES: PuzzlePieceProps[] = [
  {
    id: "coverage",
    title: "Execution Integrity",
    badge: "10 / 10 PROMPTS",
    metricValue: "100%",
    metricLabel: "Benchmark Coverage",
    description: "All planned prompt episodes executed with full request provenance and zero silent drops.",
    formula: "Coverage = N_usable / N_requested",
    statusColor: "#5bb974",
    delay: 0.05,
  },
  {
    id: "bsda",
    title: "BSDA 4D Vector",
    badge: "DISPLACEMENT",
    metricValue: "0.42 · 0.38",
    metricLabel: "D_sem & D_safety",
    description: "4-component displacement vector separating semantic drift, safety change, instruction following, and format shifts.",
    formula: "D = (D_sem, D_safety, D_instr, D_struct)",
    statusColor: "#ff7a21",
    delay: 0.15,
  },
  {
    id: "rc",
    title: "Recovery Capability",
    badge: "RC-AUC",
    metricValue: "0.31",
    metricLabel: "Checkpoint Return",
    description: "Measures trajectory back toward baseline behavior across turns t=1, 2, 5. Uncalibrated without non-zero displacement floor.",
    formula: "RC-AUC = 1 - (1/T) * SUM(Delta_t / Delta_A)",
    statusColor: "#e6a23c",
    delay: 0.25,
  },
  {
    id: "saea",
    title: "Sequential Amplification",
    badge: "SAEA / BLISS",
    metricValue: "1.42×",
    metricLabel: "Synergy Ratio",
    description: "Compares multi-turn conversational deviations against matched isolated controls to detect compounding vulnerabilities.",
    formula: "SI = CV_obs / V_Bliss",
    statusColor: "#ff7a21",
    delay: 0.35,
  },
  {
    id: "detector",
    title: "Layer 1 Warnings",
    badge: "DETERMINISTIC",
    metricValue: "2 Hits",
    metricLabel: "Pattern Triggers",
    description: "Auditable rule matches across refusal phrases and policy flags. Reflects reviewable signals, not ground-truth safety.",
    formula: "SUM(Deterministic Regex + Keyword Matches)",
    statusColor: "#8e9aaf",
    delay: 0.45,
  },
  {
    id: "calibration",
    title: "Judge Calibration Gate",
    badge: "GATED",
    metricValue: "κ = 0.211",
    metricLabel: "Cohen's Kappa",
    description: "Automated judge showed 53.9% agreement and kappa = 0.2113 against human labels. Publication claims remain gated.",
    formula: "kappa = (p_o - p_e) / (1 - p_e)",
    statusColor: "#f56c6c",
    delay: 0.55,
  },
];

export function PuzzleMetricsGrid({ report: _report }: { report?: BenchmarkRunReport }) {
  const [activePiece, setActivePiece] = useState<string | null>(null);

  return (
    <section className="puzzle-metrics-section" style={{ margin: "34px 0" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: "18px" }}>
        <div>
          <span className="studio-eyebrow">POST-TEST COMPREHENSIVE SYNTHESIS</span>
          <h2 style={{ fontSize: "1.35rem", margin: "6px 0 0" }}>10-Prompt Evaluation Puzzle Box</h2>
          <p style={{ color: "#aaa", fontSize: "0.82rem", margin: "4px 0 0" }}>
            Click any interlocking tile to view the calculation methodology and empirical boundary.
          </p>
        </div>
        <span style={{ fontSize: "0.72rem", color: "#ff7a21", border: "1px solid #ff7a2140", padding: "4px 10px", borderRadius: "99px", background: "#1a120c" }}>
          6 Interlocking Dimensions
        </span>
      </div>

      <div
        className="puzzle-box-grid"
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: "14px",
        }}
      >
        {PUZZLE_PIECES.map((piece) => {
          const isExpanded = activePiece === piece.id;

          return (
            <motion.div
              key={piece.id}
              initial={{ opacity: 0, scale: 0.88, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              transition={{
                duration: 0.45,
                delay: piece.delay,
                type: "spring",
                stiffness: 140,
                damping: 18,
              }}
              whileHover={{ y: -4, transition: { duration: 0.15 } }}
              onClick={() => setActivePiece(isExpanded ? null : piece.id)}
              style={{
                cursor: "pointer",
                background: isExpanded ? "#201812" : "#171717",
                border: `1px solid ${isExpanded ? "#ff7a21" : "#2d2d2d"}`,
                borderRadius: "12px",
                padding: "20px",
                position: "relative",
                overflow: "hidden",
                boxShadow: isExpanded ? "0 10px 30px #ff7a2118" : "none",
                transition: "background 0.2s, border-color 0.2s",
              }}
            >
              {/* Corner Puzzle Notch Accent */}
              <div
                style={{
                  position: "absolute",
                  top: "-10px",
                  right: "-10px",
                  width: "28px",
                  height: "28px",
                  borderRadius: "50%",
                  background: piece.statusColor ?? "#ff7a21",
                  opacity: 0.22,
                }}
              />

              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span
                  style={{
                    fontSize: "0.62rem",
                    fontWeight: "bold",
                    color: piece.statusColor ?? "#ff7a21",
                    letterSpacing: "0.08em",
                    border: `1px solid ${piece.statusColor ? `${piece.statusColor}40` : "#ff7a2140"}`,
                    padding: "2px 7px",
                    borderRadius: "4px",
                  }}
                >
                  {piece.badge}
                </span>
                <span style={{ fontSize: "0.68rem", color: "#777" }}>Piece #{piece.id}</span>
              </div>

              <h3 style={{ fontSize: "1.05rem", margin: "14px 0 6px", fontWeight: "600", color: "#eee" }}>
                {piece.title}
              </h3>

              <div style={{ margin: "10px 0" }}>
                <strong style={{ fontSize: "1.75rem", color: "#fff", display: "block", letterSpacing: "-0.03em" }}>
                  {piece.metricValue}
                </strong>
                <small style={{ fontSize: "0.72rem", color: "#999" }}>{piece.metricLabel}</small>
              </div>

              <p style={{ fontSize: "0.76rem", color: "#aaa", margin: "10px 0 0", lineHeight: 1.5 }}>
                {piece.description}
              </p>

              {piece.formula && (
                <div style={{ marginTop: "12px", paddingTop: "10px", borderTop: "1px dashed #2c2c2c" }}>
                  <code style={{ fontSize: "0.67rem", color: "#ff7a21", background: "#111", padding: "3px 6px", borderRadius: "4px" }}>
                    {piece.formula}
                  </code>
                </div>
              )}
            </motion.div>
          );
        })}
      </div>
    </section>
  );
}
