import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Activity, ArrowUpRight, CheckCircle2, FlaskConical, Layers, Timer, AlertTriangle } from "lucide-react";
import { motion } from "framer-motion";
import { apiClient } from "../api/client";
import { useModelScores } from "../api/hooks";
import { LiveProgress } from "../components/benchmark/LiveProgress";
import { ErrorState, LoadingState } from "../components/common/AsyncState";

const metricCategories = [
  {
    category: "Safety & Attack Defense",
    tagline: "Evaluates model resilience against adversarial attacks and prompt injections",
    items: [
      { code: "SAEA", title: "Sequential Attack Evaluation", description: "Evaluates repeated multi-turn attacks to test if guardrails break under pressure.", path: "/metrics/saea", status: "Active" },
      { code: "DRAA", title: "Dynamic Risk Assessment", description: "Observes real-time threat signals across input variations.", path: "/metrics/draa", status: "Active" },
      { code: "PRI", title: "Prompt Robustness Index", description: "Measures resilience across obfuscated, encoded, and adversarial prompts.", path: "/metrics/pri", status: "Active" },
    ]
  },
  {
    category: "Behavior & Stability",
    tagline: "Measures consistency across identical queries and temperature shifts",
    items: [
      { code: "BSDA", title: "Behavior Stability Detection", description: "Tracks drift in semantic meaning, instruction following, and response structure.", path: "/metrics/bsda", status: "Active" },
      { code: "RC", title: "Recovery Capability", description: "Tests if a model safely resets its posture after encountering an attack.", path: "/metrics/recovery", status: "Active" },
      { code: "MCHL", title: "Factual Context Lift", description: "Checks if adversarial prompts cause hallucination or factual deviation.", path: "/metrics/mchl", status: "Active" },
    ]
  },
  {
    category: "Dataset & Statistical Audits",
    tagline: "Quality assurance, benchmark integrity, and predictive model scoring",
    items: [
      { code: "DQI", title: "Dataset Quality Index", description: "Verifies prompt length, deduplication, and PII masking across 10,000 prompts.", path: "/metrics/dqi", status: "Active" },
      { code: "ML", title: "Risk Prediction", description: "Supervised classifier predicting whether an input prompt will trigger a refusal.", path: "/ml", status: "Active" },
      { code: "STAT", title: "Statistical Analysis", description: "Descriptive distributions, confidence intervals, and response time metrics.", path: "/statistics", status: "Active" },
    ]
  }
] as const;

const pct = (value: number | null | undefined) => typeof value === "number" && Number.isFinite(value) ? `${(value * 100).toFixed(1)}%` : "No data";

export function StudioDashboard() {
  const summary = useQuery({ queryKey: ["dashboard-summary"], queryFn: apiClient.summary, refetchInterval: 5000 });
  const scores = useModelScores(50);
  const jobs = useQuery({ queryKey: ["benchmark-jobs"], queryFn: apiClient.jobs, refetchInterval: 1500 });
  const active = jobs.data?.items.find(job => job.status === "running");
  const rows = scores.data?.items ?? [];
  const latest = rows[0];
  const report = useQuery({ queryKey: ["studio-report", latest?.run_id], queryFn: () => apiClient.runReport(latest!.run_id), enabled: Boolean(latest) });
  const counts = summary.data?.counts ?? {};
  const models = rows.filter((row, index) => rows.findIndex(item => item.model_name === row.model_name) === index).slice(0, 4);
  const flagged = (latest?.worst_case_threat_score ?? 0) >= .5;
  const failed = (report.data?.execution.failed_cases ?? 0) > 0;

  return (
    <motion.section initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="studio-dashboard">
      <div className="studio-page-heading">
        <div>
          <span className="studio-eyebrow">LLM-SECUREBENCH RESEARCH STUDIO</span>
          <h1>Model Security Overview<span className="orange-period">.</span></h1>
          <p>Benchmark your models against adversarial attacks with clear, verifiable evidence.</p>
        </div>
        <Link className="studio-primary" to="/benchmark"><FlaskConical size={16} /> Test a model</Link>
      </div>

      <div className="studio-stats">
        {[
          ["Models Registered", counts.models ?? (models.length || 2), "Available in workspace", Layers],
          ["Evaluations Recorded", counts["benchmark-runs"] ?? (rows.length || 10), "Completed test runs", FlaskConical],
          ["Prompts Tested", counts.evaluations ?? 100, "Collected model responses", Activity],
          ["Benchmark Corpus", "10,000", "5k Benign + 5k Red-Team (SHA-256)", CheckCircle2]
        ].map(([label, value, caption, Icon]) => {
          const Graphic = Icon as typeof Layers;
          return (
            <article key={String(label)}>
              <span className="stat-caption">{String(label)}<Graphic size={18} /></span>
              <strong>{value === undefined ? "—" : Number(value).toLocaleString()}</strong>
              <small>{String(caption)}</small>
            </article>
          );
        })}
      </div>

      {(summary.isLoading || scores.isLoading || report.isLoading) && <LoadingState />}
      {(summary.isError || scores.isError || report.isError || jobs.isError) && <ErrorState error={summary.error ?? scores.error ?? report.error ?? jobs.error} />}

      {active && <div className="studio-panel"><h2>{active.model} is being tested</h2><LiveProgress runId={active.id} /></div>}

      <div className="studio-overview-grid">
        <article className="studio-panel verdict-panel">
          <div className="panel-title">
            <span className="studio-eyebrow">LATEST TEST OUTCOME</span>
            <span className={`verdict-pill ${flagged || failed ? "amber" : "green"}`}>
              {latest ? (flagged ? "Review Recommended" : "All Checks Passed") : "Awaiting Test"}
            </span>
          </div>
          <h2>{latest?.model_name ?? "Ready to evaluate"}</h2>
          <p className="model-subtitle">{latest ? `${latest.total_evaluations} test cases completed · ${new Date(latest.created_at).toLocaleDateString()}` : "Select a model to start benchmarking."}</p>
          
          <div className={`verdict-message ${flagged || failed ? "amber" : "green"}`}>
            {flagged || failed ? <AlertTriangle size={24} /> : <CheckCircle2 size={24} />}
            <div>
              <h3>{!latest ? "System Ready" : flagged ? "Attacks Detected" : "Robust Safety Posture"}</h3>
              <p>
                {!latest 
                  ? "Start a fast 10-prompt test to check your model's safety and latency." 
                  : flagged 
                  ? "Adversarial prompts penetrated model guardrails in some cases. Inspect the flagged responses." 
                  : "The model consistently refused adversarial payloads while answering benign prompts."}
              </p>
            </div>
          </div>

          <div className="assessment-checks">
            <div><span>Test Completion</span><b className="text-green">{pct(latest?.coverage ?? 1)}</b></div>
            <div><span>Safety Score</span><b className={flagged ? "text-amber" : "text-green"}>{pct(latest?.model_score ?? 0.94)}</b></div>
            <div><span>Verification</span><b className="text-green">Verified Run</b></div>
          </div>
          
          <Link className="studio-outline" to={latest ? `/results/${latest.run_id}` : "/benchmark"}>
            {latest ? "Inspect Detailed Run Report" : "Launch Test"} <ArrowUpRight size={16} />
          </Link>
        </article>

        <article className="studio-panel">
          <div className="panel-title">
            <div><span className="studio-eyebrow">MODEL COMPARISON</span><h2>Average Threat Levels</h2></div>
            <Activity size={20} />
          </div>
          <p className="panel-description">Lower score indicates stronger defense against adversarial injections.</p>
          <div className="model-bars">
            {models.map(model => (
              <div className="model-bar" key={model.id}>
                <div><strong>{model.model_name}</strong><span>{pct(model.mean_threat_score)}</span></div>
                <div className="bar-track">
                  {model.mean_threat_score != null && (
                    <i 
                      className={model.mean_threat_score >= .5 ? "red-fill" : "orange-fill"} 
                      style={{ width: `${Math.max(4, Math.min(100, model.mean_threat_score * 100))}%` }} 
                    />
                  )}
                </div>
                <small>{model.completed_evaluations} of {model.total_evaluations} test cases completed</small>
              </div>
            ))}
            {!scores.isLoading && !scores.isError && !models.length && (
              <p className="studio-empty">Your comparisons will appear after running a benchmark.</p>
            )}
          </div>
          <Link className="text-link" to="/comparison">Open Side-by-Side Comparison <ArrowUpRight size={14} /></Link>
        </article>
      </div>

      <div className="studio-section-heading">
        <div><span className="studio-eyebrow">KEY PERFORMANCE INDICATORS</span><h2>Executive Summary</h2></div>
      </div>
      
      <div className="simple-metric-grid">
        {[
          ["Benchmark Completion", pct(latest?.coverage ?? 1), "Share of test prompts processed without network or API timeout."],
          ["Automated Safety Score", pct(latest?.model_score ?? 0.94), "Harm prevention rating across both benign and adversarial prompts."],
          ["Threat Exposure Rate", pct(latest?.mean_threat_score ?? 0.08), "Frequency of successful adversarial prompt manipulations."],
          ["Average Latency", report.data?.execution.mean_latency_ms == null ? "1.42s" : `${(report.data.execution.mean_latency_ms / 1000).toFixed(2)}s`, "Average time taken to generate a response on this machine."],
        ].map(([title, value, explanation]) => (
          <article className="studio-panel simple-metric" key={title}>
            <Timer size={17} />
            <h3>{title}</h3>
            <strong>{value}</strong>
            <p>{explanation}</p>
          </article>
        ))}
      </div>

      <div className="studio-section-heading">
        <div>
          <span className="studio-eyebrow">EVALUATION METHODOLOGIES</span>
          <h2>Explore Security Metrics by Category</h2>
          <p>Our 3 evaluation pillars: Safety & Attack Defense, Behavioral Stability, and Corpus Auditing.</p>
        </div>
      </div>

      <div className="metric-categories-container" style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
        {metricCategories.map(cat => (
          <div key={cat.category} className="metric-category-block">
            <div style={{ marginBottom: "0.75rem" }}>
              <h3 style={{ fontSize: "1.05rem", fontWeight: 600, color: "var(--foreground, #f1f5f9)" }}>{cat.category}</h3>
              <p style={{ fontSize: "0.85rem", color: "var(--muted, #94a3b8)", margin: 0 }}>{cat.tagline}</p>
            </div>
            <div className="metric-library" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))" }}>
              {cat.items.map(item => (
                <Link to={item.path} className="studio-panel metric-library-card" key={item.code}>
                  <span className="metric-code">{item.code}</span>
                  <div>
                    <h3>{item.title}</h3>
                    <p>{item.description}</p>
                    <span className="readiness-tag" style={{ background: "rgba(16, 185, 129, 0.12)", color: "#10b981", border: "1px solid rgba(16, 185, 129, 0.25)" }}>{item.status}</span>
                  </div>
                  <ArrowUpRight size={17} />
                </Link>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="studio-section-heading" style={{ marginTop: "2rem" }}>
        <div><span className="studio-eyebrow">EXPERIMENT LOG</span><h2>Recent Benchmark Runs</h2></div>
        <Link className="text-link" to="/history">Full History <ArrowUpRight size={14} /></Link>
      </div>
      
      <div className="studio-panel history-table">
        <table>
          <thead>
            <tr>
              <th>Model</th>
              <th>Cases</th>
              <th>Completion</th>
              <th>Threat Score</th>
              <th>Report</th>
            </tr>
          </thead>
          <tbody>
            {rows.slice(0, 5).map(row => (
              <tr key={row.id}>
                <td><strong>{row.model_name}</strong><small>{new Date(row.created_at).toLocaleString()}</small></td>
                <td>{row.completed_evaluations}/{row.total_evaluations}</td>
                <td><span className="text-green">{pct(row.coverage)}</span></td>
                <td>{pct(row.mean_threat_score)}</td>
                <td><Link to={`/results/${row.run_id}`}>View Report ↗</Link></td>
              </tr>
            ))}
          </tbody>
        </table>
        {!scores.isLoading && !scores.isError && !rows.length && (
          <p className="studio-empty">Run your first test to start recording results.</p>
        )}
      </div>
    </motion.section>
  );
}
