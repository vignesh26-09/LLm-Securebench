import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";
import { motion, useReducedMotion } from "framer-motion";
import { Activity, Layers, ScanLine, ShieldCheck } from "lucide-react";
import { apiClient } from "../api/client";
import { LiveProgress } from "../components/benchmark/LiveProgress";

export function TestRunPage() {
  const { runId = "" } = useParams();
  const navigate = useNavigate();
  const reduce = useReducedMotion();
  const query = useQuery({ queryKey: ["benchmark-job", runId], queryFn: () => apiClient.job(runId), refetchInterval: entry => ["running", "stopping"].includes(entry.state.data?.status ?? "running") ? 1000 : false });
  const done = query.data && ["completed", "partial", "completed_with_errors"].includes(query.data.status);
  useEffect(() => { if (done) { const timer = window.setTimeout(() => navigate(`/results/${encodeURIComponent(runId)}`, { replace: true }), 900); return () => window.clearTimeout(timer); } }, [done, navigate, runId]);
  return <section className="testing-page"><nav className="flow-stepper" aria-label="Evaluation steps"><span><b>01</b> Choose model</span><span className="current"><b>02</b> Live testing</span><span><b>03</b> Charts & results</span></nav><span className="studio-eyebrow">STEP 02 / LIVE TESTING</span><h1>{done ? "Your report is ready." : query.data?.status === "stopped" ? "This test was stopped." : query.data?.status === "stopping" ? "Stopping this test safely." : ["failed", "interrupted"].includes(query.data?.status ?? "") ? "This test needs attention." : "Putting your model through its paces."}</h1><p>{query.data?.model ?? "Connecting to your test"} · Each completed case is saved as the test runs.</p><div className="testing-stage"><div className="testing-illustration" aria-hidden="true"><motion.div className="test-orbit" animate={!reduce && query.data?.status === "running" ? { rotate: 360 } : {}} transition={{ duration: 18, repeat: Infinity, ease: "linear" }} /><div className="test-core"><ShieldCheck size={49} strokeWidth={1.2} /><span>MODEL TEST</span></div></div><div className="test-pipeline">{[[Layers,"Load prompts"],[ScanLine,"Collect answers"],[Activity,"Check patterns"]].map(([Icon,title])=>{const Graphic=Icon as typeof Layers;return <div key={String(title)}><Graphic size={19}/><span>{String(title)}</span></div>;})}</div><p className="pipeline-caption">Pipeline animation · The counts below show actual progress.</p><LiveProgress runId={runId} /></div><div className="testing-bottom"><Link to="/history">Open test history</Link><span>{query.data?.status === "stopped" ? "Saved work is retained for a later resume." : "You can leave this page. The server continues the test."}</span></div></section>;
}
