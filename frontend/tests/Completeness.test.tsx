import { fireEvent, screen, within } from "@testing-library/react";
import { StudioDashboard } from "../src/pages/StudioDashboard";
import { TestHistoryPage } from "../src/pages/TestHistoryPage";
import { ResponseTimePlot } from "../src/components/charts/ResponseTimePlot";
import { renderWithProviders } from "./test-utils";

describe("history and missing chart observations", () => {
  afterEach(() => vi.unstubAllGlobals());
  it("paginates recent tests and exposes the empty saved-run state", async () => {
    const jobs = Array.from({ length: 12 }, (_, i) => ({ id: `fixture-${i}`, model: `mock-${i}`, status: "completed" }));
    vi.stubGlobal("fetch", vi.fn((url: string) => Promise.resolve(new Response(JSON.stringify(
      url.includes("/auth/session") ? { user: { name: "Fixture researcher" } } : url.includes("/model-scores") ? { items: [], total: 0 } : { items: jobs }
    ), { status: 200 }))));
    renderWithProviders(<TestHistoryPage />);
    expect(await screen.findByText("mock-0")).toBeInTheDocument();
    expect(screen.queryByText("mock-10")).not.toBeInTheDocument();
    fireEvent.click(within(screen.getByRole("navigation", { name: "Recent test pagination" })).getByRole("button", { name: "Next" }));
    expect(screen.getByText("mock-10")).toBeInTheDocument();
    expect(screen.queryByText("mock-0")).not.toBeInTheDocument();
    expect(await screen.findByText("No earlier saved runs on this page.")).toBeInTheDocument();
  });
  it("requests the next page of saved runs", async () => {
    const fetch = vi.fn((url: string) => Promise.resolve(new Response(JSON.stringify(
      url.includes("/auth/session") ? { user: {} } : url.includes("/model-scores") ? { items: [], total: 11 } : { items: [] }
    ), { status: 200 })));
    vi.stubGlobal("fetch", fetch);
    renderWithProviders(<TestHistoryPage />);
    const nav = await screen.findByRole("navigation", { name: "Saved run pagination" });
    fireEvent.click(within(nav).getByRole("button", { name: "Next" }));
    await screen.findByText("11–11 of 11");
    expect(fetch.mock.calls.some(([url]) => url === "/model-scores?limit=10&offset=10")).toBe(true);
  });
  it("distinguishes loading dashboard records from an empty history", () => {
    vi.stubGlobal("fetch", vi.fn(() => new Promise<Response>(() => {})));
    renderWithProviders(<StudioDashboard />);
    expect(screen.getByRole("status")).toHaveTextContent("Loading backend data");
    expect(screen.queryByText("Run your first test to start your history.")).not.toBeInTheDocument();
  });
  it("shows dashboard API failures instead of an empty history", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("Fixture offline")));
    renderWithProviders(<StudioDashboard />);
    expect(await screen.findByRole("heading", { name: "BACKEND/API FAILURE" })).toBeInTheDocument();
    expect(screen.queryByText("Run your first test to start your history.")).not.toBeInTheDocument();
  });
  it("leaves all-missing response times unavailable rather than plotting zeros", () => {
    renderWithProviders(<ResponseTimePlot cases={[{ id: "missing", case_id: null, execution_status: "failed", latency_ms: null, finish_reason: null, response_available: false, observed_detector_signals: [] }]} />);
    expect(screen.getByRole("status")).toHaveTextContent("No response times available");
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });
});
