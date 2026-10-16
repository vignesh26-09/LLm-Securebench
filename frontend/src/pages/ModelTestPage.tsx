import { useEffect, useMemo, useState, type ChangeEvent, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { ArrowRight, Check, FileJson, FlaskConical, History, Layers, Plug, Upload } from "lucide-react";
import { motion } from "framer-motion";
import { apiClient } from "../api/client";
import type { BenchmarkRunInput } from "../api/types";
import { ErrorState, LoadingState } from "../components/common/AsyncState";

export function ModelTestPage() {
  const custom = useLocation().pathname === "/import";
  const [search] = useSearchParams();
  const navigate = useNavigate();
  const client = useQueryClient();
  const account = useQuery<{ user: { name: string } | null }>({ queryKey: ["account"], queryFn: async () => {
    const result = await fetch(`${import.meta.env.VITE_SECURELLM_API_BASE_URL ?? ""}/auth/session`, { credentials: "include" });
    if (!result.ok) throw new Error("Could not check your sign-in");
    return result.json();
  }, staleTime: 30000 });
  const guest = !account.data?.user;
  const [model, setModel] = useState(search.get("model") ?? "");
  const [provider, setProvider] = useState<BenchmarkRunInput["provider"]>(search.get("provider") === "openai-compatible" ? "openai-compatible" : "ollama-local");
  const [endpoint, setEndpoint] = useState("");
  const [apiKey, setApiKey] = useState("");
  const dataset: BenchmarkRunInput["dataset_key"] = "mixed-source-10000-v1";
  const first = 1;
  const [runSize, setRunSize] = useState<10 | 50 | 10000>(search.get("count") === "10000" ? 10000 : search.get("count") === "50" ? 50 : 10);
  const count = runSize;
  const [judgeModel, setJudgeModel] = useState(search.get("judge") ?? "");
  const [confirmed, setConfirmed] = useState(false);
  const [importMessage, setImportMessage] = useState("");
  const [verifiedSignature, setVerifiedSignature] = useState("");
  const signature = JSON.stringify([model, provider, provider === "openai-compatible" ? endpoint : "", provider === "openai-compatible" ? apiKey : ""]);
  const runtime = useQuery({ queryKey: ["runtime-models"], queryFn: apiClient.runtimeModels, refetchInterval: 15000 });
  const presets = useQuery({ queryKey: ["showcase-models"], queryFn: apiClient.showcaseModels });
  const datasets = useQuery({ queryKey: ["benchmark-datasets"], queryFn: apiClient.benchmarkDatasets });
  const jobs = useQuery({ queryKey: ["benchmark-jobs"], queryFn: apiClient.jobs, refetchInterval: 2500 });
  const installed = useMemo(() => new Set(runtime.data?.items.map(item => item.name) ?? []), [runtime.data]);
  const chosenJudge = judgeModel || (installed.has(model) ? model : "");
  const selectedDataset = datasets.data?.items.find(item => item.id === dataset);
  const activeJob = jobs.data?.items.find(item => ["running", "stopping"].includes(item.status));
  const connect = useMutation({ mutationFn: apiClient.connectModel, onSuccess: (_result, input) => {
    setVerifiedSignature(JSON.stringify([input.model, input.provider, input.endpoint ?? "", input.api_key ?? ""])); void client.invalidateQueries({ queryKey: ["models"] });
  } });
  const start = useMutation({ mutationFn: apiClient.startRun, onSuccess: job => {
    void client.invalidateQueries({ queryKey: ["benchmark-jobs"] });
    navigate(`/testing/${encodeURIComponent(job.id)}`);
  } });
  useEffect(() => { if (search.get("model")) setModel(search.get("model")!); }, [search]);
  const verified = verifiedSignature === signature;
  const validModel = provider === "ollama-local" ? installed.has(model) : Boolean(endpoint.trim()) && Boolean(presets.data?.remote_execution_enabled);
  const canRun = Boolean(model.trim()) && runtime.data?.execution_enabled && !activeJob && !start.isPending && Boolean(selectedDataset?.available)
    && Number.isInteger(first) && first >= 1 && Number.isInteger(count) && count >= 1 && count <= (selectedDataset?.max_cases_per_job ?? 0)
    && first + count - 1 <= (selectedDataset?.case_count ?? 0) && validModel && (!custom || verified)
    && (count === 10 || installed.has(chosenJudge)) && (count !== 10000 || confirmed)
    && (!guest || (provider === "ollama-local" && presets.data?.items.some(item => item.ollama_model === model)));
  useEffect(() => { setConfirmed(false); }, [signature, chosenJudge]);
  async function importFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      if (file.size > 100000) throw new Error("Use a connection JSON file smaller than 100 KB.");
      const value = JSON.parse(await file.text());
      if (!value || typeof value.model !== "string" || !value.model.trim() || !["ollama-local", "openai-compatible"].includes(value.provider)) throw new Error("The JSON needs a model name and a supported provider.");
      setModel(value.model); setProvider(value.provider); setEndpoint(typeof value.endpoint === "string" ? value.endpoint : ""); setApiKey("");
      setImportMessage(`Loaded ${file.name}. Verify and save the connection below. Enter API keys separately.`);
    } catch (error) { setImportMessage(error instanceof Error ? error.message : "Could not read this connection file."); }
    event.target.value = "";
  }
  function submit(event: FormEvent) {
    event.preventDefault(); if (!canRun) return;
    start.mutate({ model, provider, dataset_key: dataset, case_offset: first - 1, case_count: count,
      ...(count === 10 ? {} : { judge_model: chosenJudge }), context_window: 4096, confirm_full_corpus: count === 10000,
      ...(search.get("resume") ? { resume_run_id: search.get("resume")! } : {}),
      ...(provider === "openai-compatible" ? { endpoint, api_key: apiKey || undefined } : {}) });
  }
  return <motion.section initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="model-test-page">
    <div className="test-page-top"><div><span className="studio-eyebrow">STEP 01 / CHOOSE & CONFIGURE</span><h1>{custom ? "Bring your own model." : "Choose your next test."}</h1><p>{custom ? "Connect, verify, and save your model before testing it." : "Pick a predefined model. We will take you from a live test to an easy-to-read report."}</p></div><Link className="history-shortcut" to="/history"><History size={17} />Test history</Link></div>
    <nav className="flow-stepper" aria-label="Evaluation steps"><span className="current"><b>01</b> Choose model</span><span><b>02</b> Live testing</span><span><b>03</b> Charts & results</span></nav>
    {search.get("resume") && <p className="full-run-budget">Resuming saved run {search.get("resume")}. Use its original model, judge, run size, endpoint, and settings. Committed cases will not run again. Re-enter any API key; keys are not saved.</p>}
        <div className="test-choice-tabs"><Link className={!custom ? "active" : ""} to="/benchmark"><Layers size={17} />Predefined models<small>No sign-in needed</small></Link><Link className={custom ? "active" : ""} to="/import"><Plug size={17} />Import your model<small>Sign in or use the sample account</small></Link></div>
    {activeJob && <div className="active-run-strip"><span className="work-spinner" /><span>{activeJob.model} is currently running.</span><Link to={`/testing/${activeJob.id}`}>Watch this test →</Link></div>}
    <div className="test-workbench">
      <div className="model-choice-column">
        {!custom ? <><div className="choice-column-heading"><span className="studio-eyebrow">MODEL LIBRARY</span><h2>Pick a model</h2><p>Available models run on this server.</p></div>{presets.isLoading && <LoadingState />}{presets.isError && <ErrorState error={presets.error} />}<div className="preset-tiles">{presets.data?.items.map((item, index) => <article key={item.id} className={`preset-tile ${model === item.ollama_model ? "selected" : ""}`}><div className="preset-tile-top"><Layers size={24} /><span>0{index + 1}</span></div><span className="status">Showcase preset</span><h3>{item.name}</h3><p>{item.description}</p><div className="preset-availability">{installed.has(item.ollama_model) ? <Check size={14} /> : <Layers size={14} />}{installed.has(item.ollama_model) ? "Installed · ready to test" : "Install in Ollama first"}</div><button type="button" disabled={!installed.has(item.ollama_model)} onClick={() => { setModel(item.ollama_model); setProvider("ollama-local"); }}>{model === item.ollama_model ? "Selected" : installed.has(item.ollama_model) ? "Select" : "Not installed"}<ArrowRight size={15} /></button></article>)}</div></> : <article className="connection-explainer"><span className="studio-eyebrow">YOUR MODEL, CONNECTED</span><Upload size={38} /><h2>Import a model connection</h2><p>Use any model already installed in Ollama, or connect a compatible API when enabled on this server.</p><label className="connection-upload"><FileJson size={24} /><strong>Choose a connection JSON</strong><span>Or enter the details in the form</span><input aria-label="Import model connection JSON" type="file" accept=".json,application/json" onChange={event => { void importFile(event); }} /></label><details><summary>See a sample connection file</summary><pre>{'{\n  "model": "gemma3:4b",\n  "provider": "ollama-local"\n}'}</pre><p>This imports connection settings. Install model weights through Ollama or your inference server.</p></details>{importMessage && <p role="status">{importMessage}</p>}<h3>Installed on this server</h3><div className="installed-model-chips">{runtime.data?.items.map(item => <button type="button" key={item.name} onClick={() => { setModel(item.name); setProvider("ollama-local"); setEndpoint(""); }}>{item.name}</button>)}</div></article>}
      </div>
      <form className="test-configuration" onSubmit={submit}><span className="studio-eyebrow">{custom ? "CONNECTION & TEST SETTINGS" : "YOUR TEST SETTINGS"}</span><h2>{custom ? "Verify your connection" : "Ready, set, evaluate."}</h2><p>Run a ten-prompt response check first, then choose the controlled 50-prompt pilot or full corpus when needed.</p>
        <label><span>Provider</span><select value={provider} disabled={!custom && guest} onChange={event => setProvider(event.target.value as BenchmarkRunInput["provider"])}><option value="ollama-local">Local Ollama</option><option value="openai-compatible" disabled={guest}>OpenAI-compatible endpoint</option></select></label>
        <label><span>Model identifier</span><input value={model} readOnly={!custom && guest} onChange={event => setModel(event.target.value)} placeholder={custom ? "Enter your installed model name" : "Select a model to get started"} required /></label>
        {provider === "openai-compatible" && <><label><span>HTTPS endpoint</span><input value={endpoint} onChange={event => setEndpoint(event.target.value)} placeholder="https://your-provider.example/v1" required /></label><label><span>API key (optional)</span><input type="password" autoComplete="off" value={apiKey} onChange={event => setApiKey(event.target.value)} placeholder="Used only for this connection and run" /></label>{!presets.data?.remote_execution_enabled && <p className="form-help">Remote endpoint execution is disabled on this server.</p>}</>}
        {custom && <><button type="button" className="verify-connection" disabled={!validModel || connect.isPending || !model.trim()} onClick={() => connect.mutate({ model, provider, ...(provider === "openai-compatible" ? { endpoint, api_key: apiKey || undefined } : {}) })}><Plug size={16} />{connect.isPending ? "Checking connection…" : verified ? "Connection saved" : "Verify & save model"}</button>{verified && <p className="form-help" role="status">Connection verified and saved. Choose your test below.</p>}{connect.isError && <ErrorState error={connect.error} />}</>}
        {model && provider === "ollama-local" && <p className="form-help">{installed.has(model) ? "Model found in Ollama." : "This model is not installed. Start Ollama and select an installed model."}</p>}
        <div className="form-rule" /><label><span>Benchmark dataset</span><select value={dataset} disabled><option value="mixed-source-10000-v1">10,000 sourced prompts</option></select></label>
        <label><span>Test size</span><select value={runSize} disabled={Boolean(search.get("resume"))} onChange={event => { setRunSize(event.target.value === "10000" ? 10000 : event.target.value === "50" ? 50 : 10); setConfirmed(false); }}><option value={10}>Fast response check · 10 rotating prompts</option><option value={50}>Controlled pilot · 50 rotating prompts</option><option value={10000}>Full corpus · 10,000 prompts</option></select></label>
        <div className="batch-fields"><label><span>Source pool</span><input value="10,000 verified source prompts" readOnly /></label><label><span>Cases in this test</span><input type="number" value={count} readOnly /></label></div>
        <p className="form-help">{selectedDataset?.available ? count === 10 ? "Ten source prompts are selected without replacement within their rotation: five benign, five red-team. Each receives one direct model response. This checks connection, responses and latency; it cannot produce BSDA, recovery or SAEA." : count === 50 ? "The server randomly assigns 25 benign and 25 red-team source prompts, without reuse until the pool cycle is exhausted. The selection is saved for resume." : "All 10,000 source prompts will be checked against the pinned corpus checksum." : "The verified 10,000-prompt corpus is not available yet. Tests cannot start."}</p>
        {count !== 10 && <label><span>Local judge model</span><select value={chosenJudge} onChange={event => setJudgeModel(event.target.value)}><option value="" disabled>Choose an installed judge</option>{runtime.data?.items.map(item => <option value={item.name} key={item.name}>{item.name}{item.name === model ? " · self-judge (exploratory)" : ""}</option>)}</select></label>}
        <div className="full-run-budget"><strong>{count === 10 ? "Fast check: 10 direct model calls, no judge calls" : count === 50 ? "Pilot budget: up to 1,500 model calls" : "Full run budget: up to 300,000 model calls"}</strong><p>{count === 10 ? "Each response is limited to 64 output tokens and a 20-second call timeout. This is a bounded connection check, not a full benchmark or safety rating; model loading can add time." : "Each prompt can require 10 target calls and up to 20 judge calls for paired, isolated, sequential and recovery observations. Local context setting: 4,096 tokens."}</p><p>{count === 10 ? "Use the controlled pilot when you need paired metric evidence." : count === 50 ? "A pilot can still take time on local hardware. Its 50 cases do not represent a validated model-safety verdict." : "The full corpus may take days on local hardware."} No automatic downloads. Judge scores are exploratory, not human-validated safety labels. Recovery indices still require calibration.</p>{count === 10000 && <label><input type="checkbox" checked={confirmed} onChange={event => setConfirmed(event.target.checked)} /><span>I understand the full 10,000-prompt workload and want to run it.</span></label>}</div>
        {(datasets.isError || runtime.isError) && <ErrorState error={datasets.error ?? runtime.error} />}
        {runtime.data && !runtime.data.execution_enabled && <p className="form-help">Benchmark execution is disabled. Enable local execution on the backend.</p>}
        <button className="studio-primary" type="submit" disabled={!canRun}><FlaskConical size={17} />{start.isPending ? "Starting your test…" : activeJob ? "A benchmark is running" : count === 10 ? "Run fast response check" : count === 50 ? "Run rotating 50-prompt pilot" : "Run all 10,000 prompts"}<ArrowRight size={17} /></button>{start.isError && <ErrorState error={start.error} />}
        <div className="test-next"><span>WHAT HAPPENS NEXT</span><p>A live testing screen shows actual progress, then opens your model's charts and full results.</p></div>
      </form>
    </div>
  </motion.section>;
}
