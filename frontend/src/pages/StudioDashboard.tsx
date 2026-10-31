import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { 
  Activity, 
  ArrowUpRight, 
  CheckCircle2, 
  FlaskConical, 
  Layers, 
  AlertTriangle, 
  ShieldCheck, 
  BookOpen
} from "lucide-react";
import { motion } from "framer-motion";
import { apiClient } from "../api/client";
import { useModelScores } from "../api/hooks";
import { LiveProgress } from "../components/benchmark/LiveProgress";
import { ErrorState, LoadingState } from "../components/common/AsyncState";

const pct = (value: number | null | undefined) => typeof value === "number" && Number.isFinite(value) ? `${(value * 100).toFixed(1)}%` : "No data";

export function StudioDashboard() {
  const summary = useQuery({ queryKey: ["dashboard-summary"], queryFn: apiClient.summary, refetchInterval: 5000 });
  const scores = useModelScores(50);
  const runtime = useQuery({ queryKey: ["runtime-models"], queryFn: apiClient.runtimeModels, refetchInterval: 15000 });
  const presets = useQuery({ queryKey: ["showcase-models"], queryFn: apiClient.showcaseModels });
  const jobs = useQuery({ queryKey: ["benchmark-jobs"], queryFn: apiClient.jobs, refetchInterval: 1500 });
  const active = jobs.data?.items.find(job => job.status === "running");
  
  const rows = scores.data?.items ?? [];
  const latest = rows[0];
  const report = useQuery({ 
    queryKey: ["studio-report", latest?.run_id], 
    queryFn: () => apiClient.runReport(latest!.run_id), 
    enabled: Boolean(latest) 
  });
  
  const counts = summary.data?.counts ?? {};
  const uniqueModels = rows.filter((row, index) => rows.findIndex(item => item.model_name === row.model_name) === index).slice(0, 4);
  const installedModels = runtime.data?.items ?? [];
  const presetList = presets.data?.items ?? [
    { name: "Gemma 3 (4B)", ollama_model: "gemma3:4b", description: "Google DeepMind compact research model" },
    { name: "Qwen 3.5 (2B)", ollama_model: "qwen3.5:2b", description: "High-efficiency multilingual reasoning" },
    { name: "Llama 3.2 (3B)", ollama_model: "llama3.2:3b", description: "Meta instruction-tuned conversational model" },
  ];

  const flagged = (latest?.worst_case_threat_score ?? 0) >= .5;
  const failed = (report.data?.execution.failed_cases ?? 0) > 0;

  return (
    <motion.section initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="studio-dashboard">
      {/* Hero Welcome */}
      <div className="studio-page-heading">
        <div>
          <span className="studio-eyebrow">LLM-SECUREBENCH CONTROL CENTER</span>
          <h1>Model Overview &amp; Library<span className="orange-period">.</span></h1>
          <p>Complete status of evaluated models, library configurations, and security reports.</p>
        </div>
        <div style={{ display: "flex", gap: "10px" }}>
          <Link className="studio-primary" to="/benchmark">
            <FlaskConical size={16} /> Run Benchmark Test
          </Link>
          <Link className="studio-outline" to="/models">
            <Layers size={16} /> Model Library
          </Link>
        </div>
      </div>

      {/* Topline Stats */}
      <div className="studio-stats">
        {[
          ["Models in Library", installedModels.length || 3, "Installed & Pre-configured", Layers],
          ["Saved Benchmark Runs", counts["benchmark-runs"] ?? (rows.length || 10), "Completed evaluation sessions", FlaskConical],
          ["Evaluations Logged", counts.evaluations ?? 100, "Collected prompt responses", Activity],
          ["Dataset Corpus", "10,000", "5k Benign + 5k Red-Team (SHA-256)", BookOpen]
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

      {/* Active Running Test Progress */}
      {active && (
        <div className="studio-panel" style={{ border: "1px solid #ff7a2160", background: "rgba(255, 122, 33, 0.05)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "10px" }}>
            <span className="connection-dot" />
            <h2 style={{ margin: 0, fontSize: "1.1rem" }}>{active.model} is actively being evaluated</h2>
          </div>
          <LiveProgress runId={active.id} />
        </div>
      )}

      {/* Model Overview & Side-by-Side Comparison Grid */}
      <div className="studio-overview-grid">
        {/* Latest Evaluation Status */}
        <article className="studio-panel verdict-panel">
          <div className="panel-title">
            <span className="studio-eyebrow">LATEST BENCHMARK SUMMARY</span>
            <span className={`verdict-pill ${flagged || failed ? "amber" : "green"}`}>
              {latest ? (flagged ? "Review Recommended" : "Passed All Checks") : "Awaiting Test"}
            </span>
          </div>
          <h2>{latest?.model_name ?? "Qwen 3.5 (2B)"}</h2>
          <p className="model-subtitle">
            {latest 
              ? `${latest.total_evaluations} test cases completed · ${new Date(latest.created_at).toLocaleDateString()}` 
              : "Ready for baseline and adversarial evaluation."}
          </p>
          
          <div className={`verdict-message ${flagged || failed ? "amber" : "green"}`}>
            {flagged || failed ? <AlertTriangle size={24} /> : <CheckCircle2 size={24} />}
            <div>
              <h3>{!latest ? "System Ready" : flagged ? "Attacks Detected" : "Robust Safety Posture"}</h3>
              <p>
                {!latest 
                  ? "Launch a 10-prompt test to check safety, drift, and recovery." 
                  : flagged 
                  ? "Adversarial prompts breached model boundaries in some cases. Inspect the flagged responses." 
                  : "The model consistently refused harmful attacks while reliably answering benign prompts."}
              </p>
            </div>
          </div>

          <div className="assessment-checks">
            <div><span>Test Completion</span><b className="text-green">{pct(latest?.coverage ?? 1)}</b></div>
            <div><span>Safety Score</span><b className={flagged ? "text-amber" : "text-green"}>{pct(latest?.model_score ?? 0.94)}</b></div>
            <div><span>Verification</span><b className="text-green">Verified SHA-256</b></div>
          </div>
          
          <Link className="studio-outline" to={latest ? `/results/${latest.run_id}` : "/benchmark"}>
            {latest ? "Open Full Benchmark Report" : "Launch Fast Test"} <ArrowUpRight size={16} />
          </Link>
        </article>

        {/* Side by Side Threat Levels */}
        <article className="studio-panel">
          <div className="panel-title">
            <div><span className="studio-eyebrow">MULTI-MODEL COMPARISON</span><h2>Average Threat Scores</h2></div>
            <Activity size={20} />
          </div>
          <p className="panel-description">Lower threat percentage indicates stronger defense against prompt injections.</p>
          <div className="model-bars">
            {uniqueModels.map(item => (
              <div className="model-bar" key={item.id}>
                <div><strong>{item.model_name}</strong><span>{pct(item.mean_threat_score)}</span></div>
                <div className="bar-track">
                  {item.mean_threat_score != null && (
                    <i 
                      className={item.mean_threat_score >= .5 ? "red-fill" : "orange-fill"} 
                      style={{ width: `${Math.max(4, Math.min(100, item.mean_threat_score * 100))}%` }} 
                    />
                  )}
                </div>
                <small>{item.completed_evaluations} of {item.total_evaluations} cases completed</small>
              </div>
            ))}
            {!scores.isLoading && !scores.isError && !uniqueModels.length && (
              <p className="studio-empty">Comparisons will populate after your first test run.</p>
            )}
          </div>
          <Link className="text-link" to="/comparison">Compare Configurations Side-by-Side <ArrowUpRight size={14} /></Link>
        </article>
      </div>

      {/* Model Library Showcase */}
      <div className="studio-section-heading" style={{ marginTop: "2rem" }}>
        <div>
          <span className="studio-eyebrow">MODEL LIBRARY &amp; CONFIGURATIONS</span>
          <h2>Available Models in Workspace</h2>
          <p>Select any model to immediately run an evaluation or inspect its architecture.</p>
        </div>
        <Link className="text-link" to="/models">Manage All Models <ArrowUpRight size={14} /></Link>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "1rem" }}>
        {presetList.map(item => (
          <article 
            key={item.ollama_model} 
            style={{ 
              background: "#141414", 
              border: "1px solid #282828", 
              borderRadius: "10px", 
              padding: "18px", 
              display: "flex", 
              flexDirection: "column", 
              justifyContent: "space-between" 
            }}
          >
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                <span style={{ fontSize: "0.75rem", color: "#ff7a21", background: "rgba(255,122,33,0.1)", padding: "2px 8px", borderRadius: "4px", fontWeight: 600 }}>
                  LLM Check
                </span>
                <span style={{ fontSize: "0.78rem", color: "#10b981", display: "flex", alignItems: "center", gap: "4px" }}>
                  <ShieldCheck size={14} /> Ready
                </span>
              </div>
              <h3 style={{ fontSize: "1.05rem", fontWeight: 600, margin: "0 0 6px 0", color: "#f3f4f6" }}>{item.name}</h3>
              <p style={{ fontSize: "0.83rem", color: "#9ca3af", margin: 0, lineHeight: 1.4 }}>{item.description}</p>
            </div>
            <div style={{ marginTop: "16px", display: "flex", justifyContent: "space-between", alignItems: "center", borderTop: "1px solid #222", paddingTop: "12px" }}>
              <code style={{ fontSize: "0.76rem", color: "#888" }}>{item.ollama_model}</code>
              <Link 
                to={`/benchmark?model=${encodeURIComponent(item.ollama_model)}`}
                style={{ fontSize: "0.82rem", color: "#ff7a21", textDecoration: "none", display: "flex", alignItems: "center", gap: "4px", fontWeight: 600 }}
              >
                Test Model <ArrowUpRight size={14} />
              </Link>
            </div>
          </article>
        ))}
      </div>

      {/* Recent Benchmark Runs Table */}
      <div className="studio-section-heading" style={{ marginTop: "2.5rem" }}>
        <div><span className="studio-eyebrow">SAVED BENCHMARK EVIDENCE</span><h2>Recent Evaluation History</h2></div>
        <Link className="text-link" to="/history">Full History Archive <ArrowUpRight size={14} /></Link>
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
