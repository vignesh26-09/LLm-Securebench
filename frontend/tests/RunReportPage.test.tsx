import { fireEvent, screen } from "@testing-library/react";
import App from "../src/App";
import { renderWithProviders } from "./test-utils";

const response = (payload: unknown) => Promise.resolve(new Response(JSON.stringify(payload), { status: 200, headers: { "Content-Type": "application/json" } }));

describe("run report", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("presents detector signals as observations and blocks a selection decision", async () => {
    vi.stubGlobal("fetch", vi.fn(() => response({
      run: { id: "run-1", status: "completed", model_name: "qwen3.5:2b", model_config_id: "config-1", created_at: "2026-01-01" },
      execution: { total_cases: 3, completed_cases: 3, failed_cases: 0, coverage: 1, mean_latency_ms: 42 },
      detector_summary: [{ detector: "synthetic-override", max_score: 0.8, observed_signal_count: 1 }],
      cases: [{ id: "evaluation-1", case_id: "case-1", execution_status: "completed", latency_ms: 42, finish_reason: "stop", response_available: true, observed_detector_signals: [{ detector: "synthetic-override", score: 0.8, confidence: null }] }],
      model_score: { status: "computed", value: 0.73, mean_threat_score: 0.27, worst_case_threat_score: 0.8, formula_version: "engineering-detector-score-v1", formula: {}, warnings: [] },
      selection: { status: "evidence_review_required", label: "More evidence required before model selection", reason: "No validated rule." },
      interpretation: { observed_detector_signals: "Detector signals are observations, not confirmed successful attacks or ground-truth safety outcomes.", model_score: "Engineering summary only." },
    })));
    renderWithProviders(<App />, "/results/run-1");
    expect(await screen.findByText("More evidence required before model selection")).toBeInTheDocument();
    expect(screen.getByText(/not confirmed successful attacks/i)).toBeInTheDocument();
    expect(screen.getAllByText("synthetic-override").length).toBeGreaterThan(0);
    expect(screen.getByText("case-1")).toBeInTheDocument();
    const conclusion = screen.getByRole("region", { name: "Final model conclusion" });
    expect(conclusion).toHaveTextContent("Do not approve for production");
    expect(screen.getByText("case-1").compareDocumentPosition(conclusion) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Clear" }));
    expect(screen.getByText("Choose a tile to show its metric details.")).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Behavior changes" })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Select all" }));
    expect(screen.getByRole("heading", { name: "Behavior changes" })).toBeInTheDocument();
  });
});
