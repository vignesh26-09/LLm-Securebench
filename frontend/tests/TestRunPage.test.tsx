import { fireEvent, screen } from "@testing-library/react";
import { Route, Routes } from "react-router-dom";
import { TestRunPage } from "../src/pages/TestRunPage";
import { LiveProgress } from "../src/components/benchmark/LiveProgress";
import { renderWithProviders } from "./test-utils";

describe("completed test navigation", () => {
  afterEach(() => vi.unstubAllGlobals());
  it("automatically opens the report once the server marks the run complete", async () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(new Response(JSON.stringify({ id: "run-1", status: "completed", model: "test-model", total_cases: 3, completed_cases: 3 }), { status: 200, headers: { "Content-Type": "application/json" } }))));
    renderWithProviders(<Routes><Route path="/testing/:runId" element={<TestRunPage />} /><Route path="/results/:runId" element={<p>Charts and model dashboard</p>} /></Routes>, "/testing/run-1");
    expect(await screen.findByText("Charts and model dashboard", {}, { timeout: 2500 })).toBeInTheDocument();
  });
  it("requests a cooperative stop and shows the stopping state", async () => {
    const fetch = vi.fn((_url: string, init?: RequestInit) => Promise.resolve(new Response(JSON.stringify(
      init?.method === "POST"
        ? { id: "run-1", status: "stopping", model: "test-model", total_cases: 10000, completed_cases: 4, stage: "Stop requested; finishing the current model call" }
        : { id: "run-1", status: "running", model: "test-model", total_cases: 10000, completed_cases: 4 }),
      { status: 200, headers: { "Content-Type": "application/json" } })));
    vi.stubGlobal("fetch", fetch);
    renderWithProviders(<LiveProgress runId="run-1" />);
    fireEvent.click(await screen.findByRole("button", { name: "Stop test and keep saved work" }));
    expect(await screen.findByText("Stopping after the current call")).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith("/internal/benchmark-jobs/run-1/stop", expect.objectContaining({ method: "POST" }));
  });
  it("offers resume instead of a completed report after a stop", async () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(new Response(JSON.stringify({
      id: "run-1", status: "stopped", model: "test-model", provider: "ollama-local",
      total_cases: 10000, completed_cases: 4,
    }), { status: 200, headers: { "Content-Type": "application/json" } }))));
    renderWithProviders(<LiveProgress runId="run-1" />);
    expect(await screen.findByText("Test stopped—saved work retained")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Review settings & resume/ })).toHaveAttribute("href", expect.stringContaining("resume=run-1"));
    expect(screen.queryByRole("link", { name: "See the result" })).not.toBeInTheDocument();
  });
});
