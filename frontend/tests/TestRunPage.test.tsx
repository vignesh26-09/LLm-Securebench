import { screen } from "@testing-library/react";
import { Route, Routes } from "react-router-dom";
import { TestRunPage } from "../src/pages/TestRunPage";
import { renderWithProviders } from "./test-utils";

describe("completed test navigation", () => {
  afterEach(() => vi.unstubAllGlobals());
  it("automatically opens the report once the server marks the run complete", async () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(new Response(JSON.stringify({ id: "run-1", status: "completed", model: "test-model", total_cases: 3, completed_cases: 3 }), { status: 200, headers: { "Content-Type": "application/json" } }))));
    renderWithProviders(<Routes><Route path="/testing/:runId" element={<TestRunPage />} /><Route path="/results/:runId" element={<p>Charts and model dashboard</p>} /></Routes>, "/testing/run-1");
    expect(await screen.findByText("Charts and model dashboard", {}, { timeout: 2500 })).toBeInTheDocument();
  });
});
