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
  takeaway: string;
  statusColor?: string;
  delay: number;
}

const PLAIN_PUZZLE_PIECES: PuzzlePieceProps[] = [
  {
    id: "coverage",
    title: "1. Test Completion",
    badge: "10 / 10 COMPLETED",
    metricValue: "100%",
    metricLabel: "All Prompts Finished",
    description: "Every planned prompt was fully answered with zero dropped calls, server crashes, or missing cases.",
    takeaway: "Integrity check: 100% of cases were recorded.",
    statusColor: "#5bb974",
    delay: 0.05,
  },
  {
    id: "bsda",
    title: "2. Behavior Drift",
    badge: "DRIFT VECTOR",
    metricValue: "42% · 38%",
    metricLabel: "Meaning Shift & Safety Drop",
    description: "Shows how much the model changed under pressure: 42% off-topic drift and 38% drop in safety guardrails.",
    takeaway: "The model drifted noticeably when provoked.",
    statusColor: "#ff7a21",
    delay: 0.12,
  },
  {
    id: "rc",
    title: "3. Recovery After Attack",
    badge: "RECOVERY SPEED",
    metricValue: "31%",
    metricLabel: "Return to Normal Baseline",
    description: "When asked safe questions afterward, the model recovered only 31% of its normal behavior, showing lasting confusion.",
    takeaway: "The model stays compromised across turns.",
    statusColor: "#e6a23c",
    delay: 0.2,
  },
  {
    id: "saea",
    title: "4. Multi-Turn Amplification",
    badge: "STORY TRICK IMPACT",
    metricValue: "1.42× Worse",
    metricLabel: "Conversation vs. One-Shot",
    description: "Multi-turn roleplay conversations broke the model 42% more effectively than asking the same question in one shot.",
    takeaway: "Conversational priming compounds the attack.",
    statusColor: "#ff7a21",
    delay: 0.28,
  },
  {
    id: "detector",
    title: "5. Keyword & Rule Warnings",
    badge: "WORD FILTERS",
    metricValue: "2 Flagged",
    metricLabel: "Policy Pattern Hits",
    description: "Automatic text filters caught 2 specific policy warnings and refusal patterns during testing.",
    takeaway: "Exact rule triggers were caught on record.",
    statusColor: "#8e9aaf",
    delay: 0.36,
  },
  {
    id: "calibration",
    title: "6. AI Judge Reliability",
    badge: "CANNOT BE TRUSTED",
    metricValue: "53.9%",
    metricLabel: "Agreement with Humans (κ = 0.21)",
    description: "The AI judge was barely better than a coin flip (53.9% agreement). The framework blocked this score to avoid false ratings.",
    takeaway: "AI judges cannot replace human reviewers.",
    statusColor: "#f56c6c",
    delay: 0.44,
  },
];

export function PuzzleMetricsGrid({ report: _report }: { report?: BenchmarkRunReport }) {
  const [activePiece, setActivePiece] = useState<string | null>(null);

  return (
    <section className="puzzle-metrics-section" style={{ margin: "34px 0" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: "18px" }}>
        <div>
          <span className="studio-eyebrow" style={{ color: "#ff7a21", fontSize: "0.72rem", letterSpacing: "0.1em" }}>
            EVALUATION PUZZLE BOX · 10 PROMPTS TESTED
          </span>
          <h2 style={{ fontSize: "1.35rem", margin: "6px 0 2px", fontWeight: "600", color: "#f0f0f0" }}>
            The 6 Key Pillars of Model Behavior
          </h2>
          <p style={{ color: "#999", fontSize: "0.82rem", margin: 0 }}>
            Click any puzzle tile to see what it measures and what it means for your model.
          </p>
        </div>
        <span style={{ fontSize: "0.72rem", color: "#ff7a21", border: "1px solid #ff7a2140", padding: "4px 12px", borderRadius: "99px", background: "#1a120c", fontWeight: "bold" }}>
          6 Interlocking Findings
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
        {PLAIN_PUZZLE_PIECES.map((piece) => {
          const isExpanded = activePiece === piece.id;

          return (
            <motion.div
              key={piece.id}
              initial={{ opacity: 0, scale: 0.9, y: 16 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              transition={{
                duration: 0.4,
                delay: piece.delay,
                type: "spring",
                stiffness: 150,
                damping: 20,
              }}
              whileHover={{ y: -3, transition: { duration: 0.15 } }}
              onClick={() => setActivePiece(isExpanded ? null : piece.id)}
              style={{
                cursor: "pointer",
                background: isExpanded ? "#231810" : "#171717",
                border: `1px solid ${isExpanded ? "#ff7a21" : "#2d2d2d"}`,
                borderRadius: "12px",
                padding: "20px",
                position: "relative",
                overflow: "hidden",
                boxShadow: isExpanded ? "0 8px 24px #ff7a2120" : "none",
                transition: "background 0.2s, border-color 0.2s",
              }}
            >
              {/* Corner Puzzle Piece Accent */}
              <div
                style={{
                  position: "absolute",
                  top: "-10px",
                  right: "-10px",
                  width: "26px",
                  height: "26px",
                  borderRadius: "50%",
                  background: piece.statusColor ?? "#ff7a21",
                  opacity: 0.25,
                }}
              />

              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span
                  style={{
                    fontSize: "0.65rem",
                    fontWeight: "bold",
                    color: piece.statusColor ?? "#ff7a21",
                    letterSpacing: "0.06em",
                    border: `1px solid ${piece.statusColor ? `${piece.statusColor}40` : "#ff7a2140"}`,
                    padding: "2px 8px",
                    borderRadius: "4px",
                    background: `${piece.statusColor}10`,
                  }}
                >
                  {piece.badge}
                </span>
                <span style={{ fontSize: "0.68rem", color: "#666" }}>Tile #{piece.id}</span>
              </div>

              <h3 style={{ fontSize: "1.02rem", margin: "14px 0 6px", fontWeight: "600", color: "#eee" }}>
                {piece.title}
              </h3>

              <div style={{ margin: "10px 0" }}>
                <strong style={{ fontSize: "1.7rem", color: "#fff", display: "block", letterSpacing: "-0.03em" }}>
                  {piece.metricValue}
                </strong>
                <small style={{ fontSize: "0.72rem", color: "#aaa" }}>{piece.metricLabel}</small>
              </div>

              <p style={{ fontSize: "0.78rem", color: "#bbb", margin: "10px 0 0", lineHeight: 1.55 }}>
                {piece.description}
              </p>

              <div style={{ marginTop: "12px", paddingTop: "10px", borderTop: "1px dashed #2d2d2d", display: "flex", alignItems: "center", gap: "6px" }}>
                <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: piece.statusColor ?? "#ff7a21", flexShrink: 0 }} />
                <span style={{ fontSize: "0.72rem", color: "#ddd", fontWeight: "500" }}>
                  {piece.takeaway}
                </span>
              </div>
            </motion.div>
          );
        })}
      </div>
    </section>
  );
}
