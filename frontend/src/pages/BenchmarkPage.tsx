import { FormEvent, useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useSearchParams, useLocation } from "react-router-dom";
import { apiClient } from "../api/client";
import type { BenchmarkRunInput } from "../api/types";
import { ErrorState, LoadingState } from "../components/common/AsyncState";
import { LiveProgress } from "../components/benchmark/LiveProgress";

type Provider = BenchmarkRunInput["provider"];

export function BenchmarkPage() {
  const location = useLocation();
  const custom = location.pathname === "/import";
  const account = useQuery<{ user: { name: string } | null }>({ queryKey: ["account"], queryFn: async () => {
    const response = await fetch(`${import.meta.env.VITE_SECURELLM_API_BASE_URL ?? ""}/auth/session`, { credentials: "include" });
    if (!response.ok) throw new Error("Account service unavailable");
    return response.json();
  }, retry: false, staleTime: 30000 });
  const client = useQueryClient();
  const [search] = useSearchParams();
  const [provider, setProvider] = useState<Provider>("ollama-local");
  const [model, setModel] = useState(search.get("model") ?? "");
  const [endpoint, setEndpoint] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [datasetKey, setDatasetKey] = useState<BenchmarkRunInput["dataset_key"]>("repository-example");
  const [startCase, setStartCase] = useState(1);
  const [caseCount, setCaseCount] = useState(3);
  const runtime = useQuery({ queryKey: ["runtime-models"], queryFn: apiClient.runtimeModels, refetchInterval: 15000, retry: false });
  const showcase = useQuery({ queryKey: ["showcase-models"], queryFn: apiClient.showcaseModels, retry: false });
  const datasets = useQuery({ queryKey: ["benchmark-datasets"], queryFn: apiClient.benchmarkDatasets, retry: false });
  const jobs = useQuery({ queryKey: ["benchmark-jobs"], queryFn: apiClient.jobs, refetchInterval: 2500, retry: false });
  const running = jobs.data?.items.some((job) => job.status === "running") ?? false;
  const installed = useMemo(() => new Set(runtime.data?.items.map((item) => item.name) ?? []), [runtime.data]);
  const selectedDataset = datasets.data?.items.find((item) => item.id === datasetKey);
  const guest = !account.data?.user;
  const start = useMutation({
    mutationFn: apiClient.startRun,
    onSuccess: () => { void client.invalidateQueries({ queryKey: ["benchmark-jobs"] }); },
  });

  useEffect(() => {
    const requested = search.get("model");
    if (requested) setModel(requested);
  }, [search]);

  function chooseShowcase(name: string) {
    setProvider("ollama-local");
    setModel(name);
    setEndpoint("");
    setApiKey("");
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const selection = { dataset_key: datasetKey, case_offset: startCase - 1, case_count: caseCount };
    const input: BenchmarkRunInput = provider === "ollama-local"
      ? { provider, model, ...selection }
      : { provider, model, endpoint, api_key: apiKey || undefined, ...selection };
    start.mutate(input);
  }

  const guestAllowed = !guest || (provider === "ollama-local" && Boolean(showcase.data?.items.some(item => item.ollama_model === model)) && caseCount <= 10);
  const canSubmit = guestAllowed && Boolean(model.trim()) && runtime.data?.execution_enabled && !running && !start.isPending &&
    Boolean(selectedDataset?.available) && Number.isInteger(startCase) && startCase >= 1 &&
    Number.isInteger(caseCount) && caseCount >= 1 && caseCount <= (selectedDataset?.max_cases_per_job ?? 0) &&
    startCase + caseCount - 1 <= (selectedDataset?.case_count ?? 0) &&
    (provider === "ollama-local" ? installed.has(model) : Boolean(endpoint.trim()) && Boolean(showcase.data?.remote_execution_enabled));

  return <section className="benchmark-workspace">
    <div className="eyebrow">{custom ? "CONNECT YOUR MODEL" : "NO LOGIN NEEDED FOR PREDEFINED MODELS"}</div>
    <h1>{custom ? "Your model. The same clear checks." : "Put a model to the test."}</h1>
    <p className="lede">Choose a model, select your test prompts, and watch the results arrive. Each run records actual answers, response times, and automated warnings.</p>
    <div className="test-mode-tabs"><Link className={!custom ? "active" : ""} to="/benchmark">Predefined models</Link><Link className={custom ? "active" : ""} to="/import">Connect / import a model <span>Sign in</span></Link></div>
    <div className="notice"><h2>{custom ? "How model import works" : "A quick test, explained"}</h2><p>{custom ? "Connect a model already installed in Ollama or enter a compatible API endpoint. Model weight files are not uploaded through this form. Use your own model identifier below." : "Start with the three-case example. We check the responses for warning patterns and measure speed. Your report explains every measurement."}</p>{guest && <p>Guest tests support up to 10 cases. <Link to="/workspace">Sign in</Link> for larger tests and custom models.</p>}</div>

    <div className="benchmark-grid">
      <div className="benchmark-panel"><h2>1. Choose a predefined model</h2>
        {showcase.isLoading && <LoadingState />}{showcase.isError && <ErrorState error={showcase.error} />}
        {showcase.data && <><p className="muted">{showcase.data.note}</p><div className="showcase-list">{showcase.data.items.map((item) => {
          const isInstalled = installed.has(item.ollama_model);
          return <article className={model === item.ollama_model && provider === "ollama-local" ? "showcase-card selected" : "showcase-card"} key={item.id}>
            <div><span className="status status-unspecified">Showcase preset</span><h3>{item.name}</h3><p>{item.description}</p><small>{isInstalled ? "Installed locally and ready to configure" : item.access}</small></div>
            <button type="button" onClick={() => chooseShowcase(item.ollama_model)}>{isInstalled ? "Select" : "Select preset"}</button>
          </article>;
        })}</div></>}
      </div>

      <form className="benchmark-panel run-form" onSubmit={submit}>
        <h2>2. Set up your test</h2>
        <label><span>Provider</span><select value={provider} onChange={(event) => setProvider(event.target.value as Provider)}>
          <option value="ollama-local">Local Ollama</option><option value="openai-compatible" disabled={guest}>OpenAI-compatible endpoint</option>
        </select></label>
        <label><span>Model identifier</span><input value={model} readOnly={guest} onChange={(event) => setModel(event.target.value)} placeholder={guest ? "Select a predefined model on the left" : provider === "ollama-local" ? "e.g. gemma3:4b" : "e.g. your-model-id"} required /></label>
        {model && <div className="model-connection-state" role="status"><span className={provider === "ollama-local" && installed.has(model) ? "text-green" : "text-amber"}>{provider === "ollama-local" ? installed.has(model) ? "✓ Model found in Ollama" : "Model is not installed on this server" : "Endpoint will be checked when the test starts"}</span><small>{provider === "ollama-local" && installed.has(model) ? "The model is available to run. This is a connection check; test results assess its behavior." : "Check the model name and provider before starting."}</small></div>}
        <label><span>Benchmark dataset</span><select value={datasetKey} onChange={(event) => {
          const key = event.target.value as BenchmarkRunInput["dataset_key"];
          setDatasetKey(key); setStartCase(1); setCaseCount(key === "repository-example" ? 3 : guest ? 10 : 100);
        }}>
          {datasets.data?.items.map((item) => <option value={item.id} key={item.id} disabled={!item.available}>{item.name} · {item.case_count.toLocaleString()} prompts{item.available ? "" : " · unavailable"}</option>)}
        </select></label>
        {datasets.isError && <ErrorState error={datasets.error} />}
        {selectedDataset && <p className="muted">{selectedDataset.note} {selectedDataset.available && `Source groups: ${Object.entries(selectedDataset.category_counts).map(([name, count]) => `${name} ${count.toLocaleString()}`).join(" · ")}.`}</p>}
        <label><span>Start case (1-based)</span><input type="number" min={1} max={selectedDataset?.case_count ?? 1} value={startCase} onChange={(event) => setStartCase(Number(event.target.value))} required /></label>
        <label><span>Cases in this batch</span><input type="number" min={1} max={guest ? Math.min(10, selectedDataset?.max_cases_per_job ?? 1) : selectedDataset?.max_cases_per_job ?? 1} value={caseCount} onChange={(event) => setCaseCount(Number(event.target.value))} required /></label>
        {selectedDataset && <p className="muted">This job covers cases {startCase.toLocaleString()}–{(startCase + caseCount - 1).toLocaleString()} of {selectedDataset.case_count.toLocaleString()}. Maximum {(guest ? Math.min(10, selectedDataset.max_cases_per_job) : selectedDataset.max_cases_per_job).toLocaleString()} per job.{selectedDataset.id === "mixed-source-10000-v1" && " Covering all 10,000 requires multiple jobs and may take substantial time."}</p>}
        {provider === "ollama-local" && <p className="muted">Only models discovered from the local Ollama service can run. No model is downloaded by this application.</p>}
        {provider === "openai-compatible" && <><label><span>HTTPS endpoint</span><input value={endpoint} onChange={(event) => setEndpoint(event.target.value)} placeholder="https://provider.example/v1" required /></label>
          <label><span>API key (optional)</span><input type="password" value={apiKey} onChange={(event) => setApiKey(event.target.value)} autoComplete="off" placeholder="Sent only for this run" /></label>
          <p className="muted">Remote execution must be enabled by the server operator. API keys are used only by the active job and are excluded from job responses, persistence, logs, and dashboard records.</p></>}
        {!runtime.data?.execution_enabled && runtime.data && <p className="notice">Benchmark execution is disabled. Start the backend with local execution enabled.</p>}
        {provider === "openai-compatible" && showcase.data && !showcase.data.remote_execution_enabled && <p className="notice">Remote endpoint execution is disabled on this server.</p>}
        <button className="primary-button" type="submit" disabled={!canSubmit}>{start.isPending ? "Submitting…" : running ? "A benchmark is running" : "Run selected batch"}</button>
        {start.isError && <ErrorState error={start.error} />}
        {start.data && <p className="success-message" role="status">Benchmark submitted for <strong>{start.data.model}</strong>. The live job is shown below.</p>}
      </form>
    </div>

      <div className="benchmark-panel job-panel"><h2>3. Watch your test work</h2>
      {start.data && <LiveProgress runId={start.data.id} />}
      {jobs.isLoading && <LoadingState />}{jobs.isError && <ErrorState error={jobs.error} />}
      {jobs.data?.items.length === 0 && <p className="muted">No live jobs in this server session. Completed runs remain in the dashboard.</p>}
      {jobs.data?.items.map((job) => <div className="job-row" key={job.id}><div><strong>{job.model}</strong><small>{job.provider} · {job.id}</small><p className="job-stage">{job.stage ?? "Awaiting status"}</p><small>{job.submitted_at ? `Started ${new Date(job.submitted_at).toLocaleString()}` : "Session job"}{job.completed_at ? ` · finished ${new Date(job.completed_at).toLocaleString()}` : ""}</small></div><span className={`status status-${job.status}`}>{job.status}</span>{job.error && <p>{job.error}</p>}{job.status !== "running" && job.status !== "failed" && <Link to={`/results/${job.id}`}>Open run report →</Link>}</div>)}
      <p><Link to="/runs">Browse persisted benchmark runs →</Link> · <Link to="/comparison">Compare saved model evidence →</Link></p>
    </div>
  </section>;
}
