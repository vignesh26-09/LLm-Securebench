import { fireEvent, screen } from "@testing-library/react";
import App from "../src/App";
import { renderWithProviders } from "./test-utils";

describe("persisted entity browsing", () => {
  afterEach(() => vi.unstubAllGlobals());
  it("renders source records and linked version navigation", async () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(new Response(JSON.stringify({ items: [{ id: "source", name: "Repository example", provenance: { kind: "repository_example" } }], total: 1, offset: 0, limit: 25 })))));
    renderWithProviders(<App />, "/datasets");
    expect(await screen.findByText("Repository example")).toBeInTheDocument();
    expect(screen.getByText("View linked records →")).toHaveAttribute("href", "/dataset-versions?filter_by=dataset_id&value=source");
    expect(screen.getByRole("button", { name: "Next" })).toBeDisabled();
  });
  it("passes relationship filters and pages using total count", async () => {
    const fetchMock = vi.fn(() => Promise.resolve(new Response(JSON.stringify({ items: [{ id: "e", execution_status: "failed", response: null }], total: 26, offset: 0, limit: 25 }))));
    vi.stubGlobal("fetch", fetchMock);
    renderWithProviders(<App />, "/evaluations?filter_by=benchmark_run_id&value=run-1");
    expect(await screen.findByText("failed")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("filter_by=benchmark_run_id&value=run-1"), expect.anything());
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    await screen.findByText("26–26 of 26");
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("offset=25"), expect.anything());
  });
  it("distinguishes empty data from API failure", async () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(new Response(JSON.stringify({ items: [], total: 0, limit: 25, offset: 0 })))));
    renderWithProviders(<App />, "/models");
    expect(await screen.findByText(/No model configurations have been saved/)).toBeInTheDocument();
    expect(screen.queryByText("BACKEND ENDPOINT UNAVAILABLE")).not.toBeInTheDocument();
  });
  it("shows API failure instead of reporting zero records", async () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(new Response("", { status: 503 }))));
    renderWithProviders(<App />, "/models");
    expect(await screen.findByText("BACKEND/API FAILURE")).toBeInTheDocument();
    expect(screen.queryByText("0 persisted records")).not.toBeInTheDocument();
  });
});
