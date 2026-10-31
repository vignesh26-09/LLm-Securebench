import { useEffect, useMemo, useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Check, Zap } from "lucide-react";
import { apiClient } from "../api/client";
import type { BenchmarkRunInput } from "../api/types";

export function ModelTestPage() {
  const [search] = useSearchParams();
  const navigate = useNavigate();
  const client = useQueryClient();

  const [model, setModel] = useState(search.get("model") ?? "qwen3.5:2b");
  const dataset: BenchmarkRunInput["dataset_key"] = "mixed-source-10000-v1";
  const first = 1;

  type TestOption = "10-fast" | "10-controlled" | "50" | "10000";
  const [testOption, setTestOption] = useState<TestOption>(
    search.get("count") === "10000" ? "10000" : search.get("count") === "50" ? "50" : search.get("mode") === "controlled" ? "10-controlled" : "10-fast"
  );
  const count = testOption === "10-fast" || testOption === "10-controlled" ? 10 : testOption === "50" ? 50 : 10000;
  const isFastCheck = testOption === "10-fast";

  const runtime = useQuery({ queryKey: ["runtime-models"], queryFn: apiClient.runtimeModels, refetchInterval: 15000 });
  const jobs = useQuery({ queryKey: ["benchmark-jobs"], queryFn: apiClient.jobs, refetchInterval: 2500 });
  
  const installed = useMemo(() => new Set(runtime.data?.items.map(item => item.name) ?? []), [runtime.data]);
  const chosenJudge = (installed.has(model) ? model : "gemma3:4b");
  const activeJob = jobs.data?.items.find(item => ["running", "stopping"].includes(item.status));

  const start = useMutation({
    mutationFn: apiClient.startRun,
    onSuccess: job => {
      void client.invalidateQueries({ queryKey: ["benchmark-jobs"] });
      navigate(`/testing/${encodeURIComponent(job.id)}`);
    }
  });

  useEffect(() => { if (search.get("model")) setModel(search.get("model")!); }, [search]);
  const canRun = Boolean(model.trim()) && !activeJob && !start.isPending;

  function submit(event: FormEvent) {
    event.preventDefault();
    if (!canRun) return;
    start.mutate({
      model,
      provider: "ollama-local",
      dataset_key: dataset,
      case_offset: first - 1,
      case_count: count,
      run_mode: isFastCheck ? "fast_check" : "controlled",
      ...(isFastCheck ? {} : { judge_model: chosenJudge }),
      context_window: 4096,
      confirm_full_corpus: count === 10000,
      ...(search.get("resume") ? { resume_run_id: search.get("resume")! } : {}),
    });
  }

  return (
    <section className="model-test-page" style={{ maxWidth: "860px", margin: "0 auto" }}>
      {/* Header */}
      <div style={{ marginBottom: "1.75rem" }}>
        <span className="studio-eyebrow">BENCHMARK TEST RUNNER</span>
        <h1 style={{ fontSize: "1.9rem", fontWeight: 700, margin: "0.25rem 0 0.4rem 0" }}>
          Launch Model Security Benchmark
        </h1>
        <p style={{ color: "#9ca3af", margin: 0, fontSize: "0.9rem" }}>
          Choose a model and test budget. The engine will evaluate safety, refusal rates, and behavioral drift.
        </p>
      </div>

      <form onSubmit={submit} style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
        {/* Step 1: Target Model */}
        <div className="studio-panel" style={{ background: "#141414", border: "1px solid #282828", borderRadius: "10px", padding: "18px" }}>
          <label style={{ display: "block", fontSize: "0.85rem", color: "#e5e7eb", fontWeight: 600, marginBottom: "8px" }}>
            1. Target Model Name
          </label>
          <div style={{ display: "flex", gap: "10px" }}>
            <input
              type="text"
              value={model}
              onChange={e => setModel(e.target.value)}
              placeholder="e.g. qwen3.5:2b, gemma3:4b, or gpt-4o"
              style={{
                flex: 1,
                background: "#1c1c1c",
                border: "1px solid #333",
                borderRadius: "6px",
                padding: "9px 12px",
                color: "#fff",
                fontSize: "0.92rem"
              }}
              required
            />
          </div>
          <div style={{ display: "flex", gap: "8px", marginTop: "10px" }}>
            {["qwen3.5:2b", "gemma3:4b", "llama3.2:3b"].map(preset => (
              <button
                key={preset}
                type="button"
                onClick={() => setModel(preset)}
                style={{
                  background: model === preset ? "rgba(255,122,33,0.15)" : "#1e1e1e",
                  border: model === preset ? "1px solid #ff7a21" : "1px solid #333",
                  color: model === preset ? "#ff7a21" : "#aaa",
                  padding: "4px 10px",
                  borderRadius: "5px",
                  fontSize: "0.78rem",
                  cursor: "pointer"
                }}
              >
                {preset}
              </button>
            ))}
          </div>
        </div>

        {/* Step 2: Sampling Budget */}
        <div className="studio-panel" style={{ background: "#141414", border: "1px solid #282828", borderRadius: "10px", padding: "18px" }}>
          <label style={{ display: "block", fontSize: "0.85rem", color: "#e5e7eb", fontWeight: 600, marginBottom: "10px" }}>
            2. Choose Test Evaluation Mode
          </label>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "10px" }}>
            {[
              { id: "10-fast", title: "10 Fast Check", time: "~15 seconds", desc: "Instant sanity check across 10 rotating prompts." },
              { id: "10-controlled", title: "10 Mini Pilot", time: "~2 minutes", desc: "Multi-turn attacks, BSDA drift, and LLM judge scoring." },
              { id: "50", title: "50 Pilot Run", time: "~10 minutes", desc: "Balanced statistical sample for research pilots." },
              { id: "10000", title: "10k Full Corpus", time: "Extended budget", desc: "Full dataset with stratified hashing." }
            ].map(opt => (
              <div
                key={opt.id}
                onClick={() => setTestOption(opt.id as TestOption)}
                style={{
                  background: testOption === opt.id ? "rgba(255, 122, 33, 0.08)" : "#1a1a1a",
                  border: testOption === opt.id ? "1px solid #ff7a21" : "1px solid #2d2d2d",
                  borderRadius: "8px",
                  padding: "12px",
                  cursor: "pointer",
                  transition: "all 0.15s ease"
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                  <strong style={{ fontSize: "0.92rem", color: testOption === opt.id ? "#ff7a21" : "#f3f4f6" }}>
                    {opt.title}
                  </strong>
                  {testOption === opt.id && <Check size={15} color="#ff7a21" />}
                </div>
                <span style={{ fontSize: "0.74rem", color: "#10b981", display: "block", marginBottom: "4px" }}>{opt.time}</span>
                <p style={{ fontSize: "0.76rem", color: "#9ca3af", margin: 0, lineHeight: 1.35 }}>{opt.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Action Button */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: "0.25rem" }}>
          <span style={{ fontSize: "0.82rem", color: "#888" }}>
            Corpus: <strong>mixed-source-10000-v1</strong> (50% Benign + 50% Adversarial)
          </span>
          <button
            type="submit"
            className="studio-primary"
            disabled={!canRun}
            style={{ padding: "10px 22px", fontSize: "0.92rem", gap: "8px" }}
          >
            <Zap size={17} />
            {start.isPending ? "Starting Benchmark…" : "Launch Benchmark Test →"}
          </button>
        </div>
      </form>
    </section>
  );
}
