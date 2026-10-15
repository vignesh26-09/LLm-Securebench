import { fireEvent, screen } from "@testing-library/react";
import App from "../src/App";
import { renderWithProviders } from "./test-utils";

const response = (body: unknown) => Promise.resolve(new Response(JSON.stringify(body), { status: 200, headers: { "Content-Type": "application/json" } }));

describe("model connection workflow", () => {
  afterEach(() => vi.unstubAllGlobals());
  function mockService() {
    vi.stubGlobal("fetch", vi.fn((url: string) => {
      if (url.includes("internal/model-connections")) return response({ id: "connection-1", model: "custom:1b", verified: true, message: "Saved" });
      if (url.includes("runtime-models")) return response({ available: true, execution_enabled: true, items: [{ name: "custom:1b", digest: "a" }, { name: "another:2b", digest: "b" }] });
      if (url.includes("showcase-models")) return response({ items: [], remote_execution_enabled: false });
      if (url.includes("benchmark-datasets")) return response({ items: [{ id: "mixed-source-10000-v1", name: "10,000 sourced prompts", available: true, case_count: 10000, max_cases_per_job: 10000 }] });
      if (url.includes("benchmark-jobs")) return response({ items: [] });
      return response({ status: "ready" });
    }));
  }
  it("requires a saved connection and invalidates it when model details change", async () => {
    mockService(); renderWithProviders(<App />, "/import");
    fireEvent.click(await screen.findByRole("button", { name: "custom:1b" }));
    expect(screen.getByRole("button", { name: "Run all 10,000 prompts" })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "Verify & save model" }));
    expect(await screen.findByText("Connection verified and saved. Choose your test below.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("checkbox", { name: /I understand the full/ }));
    expect(screen.getByRole("button", { name: "Run all 10,000 prompts" })).toBeEnabled();
    fireEvent.change(screen.getByLabelText("Model identifier"), { target: { value: "another:2b" } });
    expect(screen.getByRole("button", { name: "Run all 10,000 prompts" })).toBeDisabled();
  });
  it("loads an imported JSON connection but still requires verification", async () => {
    mockService(); renderWithProviders(<App />, "/import");
    const file = new File(['{}'], 'connection.json', { type: 'application/json' });
    Object.defineProperty(file, "text", { value: async () => JSON.stringify({ model: "custom:1b", provider: "ollama-local" }) });
    fireEvent.change(await screen.findByLabelText("Import model connection JSON"), { target: { files: [file] } });
    expect(await screen.findByText(/Loaded connection.json/)).toBeInTheDocument();
    expect(screen.getByLabelText("Model identifier")).toHaveValue("custom:1b");
    expect(screen.getByRole("button", { name: "Run all 10,000 prompts" })).toBeDisabled();
  });
});
