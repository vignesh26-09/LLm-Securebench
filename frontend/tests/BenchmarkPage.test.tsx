import { fireEvent, screen, waitFor } from "@testing-library/react";
import App from "../src/App";
import { renderWithProviders } from "./test-utils";

const response = (payload: unknown) => Promise.resolve(new Response(JSON.stringify(payload), { status: 200, headers: { "Content-Type": "application/json" } }));
const datasets = { items: [
  { id: "repository-example", name: "Repository example", case_count: 3, available: true, category_counts: { example: 3 }, evidence_class: "engineering_example", max_cases_per_job: 3, note: "Example cases." },
  { id: "mixed-source-10000-v1", name: "10,000 sourced prompts", case_count: 10000, available: true, category_counts: { benign_control_source: 5000, red_team_source_seed: 5000 }, evidence_class: "unvalidated_mixed_source", max_cases_per_job: 1000, note: "Engineering source corpus." },
], note: "Source count only." };

describe("benchmark workspace", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("shows three presets as untested choices and only enables an installed local model", async () => {
    vi.stubGlobal("fetch", vi.fn((input: string) => {
      if (input.includes("benchmark-datasets")) return response(datasets);
      if (input.includes("showcase-models")) return response({ items: [
        { id: "gemma3:4b", name: "Gemma 3 4B", ollama_model: "gemma3:4b", description: "Preset", access: "Install locally" },
        { id: "qwen3.5:2b", name: "Qwen 3.5 2B", ollama_model: "qwen3.5:2b", description: "Preset", access: "Install locally" },
        { id: "llama3.2:3b", name: "Llama 3.2 3B", ollama_model: "llama3.2:3b", description: "Preset", access: "Install locally" },
      ], remote_execution_enabled: false, note: "Presets are not tested." });
      if (input.includes("runtime-models")) return response({ available: true, execution_enabled: true, items: [{ name: "gemma3:4b", digest: "a" }] });
      if (input.includes("benchmark-jobs")) return response({ items: [] });
      return response({ status: "ready" });
    }));
    renderWithProviders(<App />, "/benchmark");
    expect(await screen.findByText("Gemma 3 4B")).toBeInTheDocument();
    expect(screen.getAllByText("Showcase preset")).toHaveLength(3);
    expect(screen.getByRole("button", { name: "Run selected batch" })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "Select" }));
    expect(screen.getByRole("button", { name: "Run selected batch" })).toBeEnabled();
  });

  it("requires an enabled server before allowing a remote endpoint run", async () => {
    vi.stubGlobal("fetch", vi.fn((input: string) => {
      if (input.includes("benchmark-datasets")) return response(datasets);
      if (input.includes("showcase-models")) return response({ items: [], remote_execution_enabled: false, note: "Remote disabled." });
      if (input.includes("runtime-models")) return response({ available: true, execution_enabled: true, items: [] });
      if (input.includes("benchmark-jobs")) return response({ items: [] });
      return response({ status: "ready" });
    }));
    renderWithProviders(<App />, "/benchmark");
    await screen.findByLabelText("Provider");
    fireEvent.change(screen.getByLabelText("Provider"), { target: { value: "openai-compatible" } });
    fireEvent.change(screen.getByLabelText("Model identifier"), { target: { value: "external-model" } });
    fireEvent.change(screen.getByLabelText("HTTPS endpoint"), { target: { value: "https://provider.example/v1" } });
    expect(await screen.findByText("Remote endpoint execution is disabled on this server.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Run selected batch" })).toBeDisabled();
  });

  it("shows 10,000 distinct source cases and sends a bounded selected window", async () => {
    const fetchMock = vi.fn((input: string, init?: RequestInit) => {
      if (input.includes("benchmark-datasets")) return response(datasets);
      if (input.includes("showcase-models")) return response({ items: [
        { id: "gemma3:4b", name: "Gemma 3 4B", ollama_model: "gemma3:4b", description: "Preset", access: "Installed" },
      ], remote_execution_enabled: false, note: "Presets only." });
      if (input.includes("runtime-models")) return response({ available: true, execution_enabled: true, items: [{ name: "gemma3:4b", digest: "a" }] });
      if (input.includes("internal/benchmark-jobs") && init?.method === "POST") return response({ id: "job-1", model: "gemma3:4b", status: "running" });
      if (input.includes("benchmark-jobs")) return response({ items: [] });
      return response({ status: "ready" });
    });
    vi.stubGlobal("fetch", fetchMock);
    renderWithProviders(<App />, "/benchmark");
    expect(await screen.findByText(/10,000 sourced prompts/)).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Benchmark dataset"), { target: { value: "mixed-source-10000-v1" } });
    fireEvent.click(screen.getByRole("button", { name: "Select" }));
    fireEvent.change(screen.getByLabelText("Start case (1-based)"), { target: { value: "1001" } });
    fireEvent.change(screen.getByLabelText("Cases in this batch"), { target: { value: "1000" } });
    expect(screen.getByText(/cases 1,001–2,000 of 10,000/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Run selected batch" }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("internal/benchmark-jobs"),
      expect.objectContaining({ method: "POST", body: JSON.stringify({ model: "gemma3:4b", provider: "ollama-local", dataset_key: "mixed-source-10000-v1", case_offset: 1000, case_count: 1000 }) })));
  });
});
