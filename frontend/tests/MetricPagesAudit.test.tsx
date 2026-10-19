import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import * as echarts from "echarts";
import { BSDAPage, RecoveryPage, SAEAPage, DRAAPage, PRIPage, DQIPage, MatchedHallucinationPage, MLPredictionPage, StatisticalPage } from "../src/pages/MetricPages";
import { StoredMetricEvidence } from "../src/components/metrics/StoredMetricEvidence";
import { renderWithProviders } from "./test-utils";

vi.mock("echarts", () => ({ init: vi.fn(() => ({ setOption: vi.fn(), resize: vi.fn(), dispose: vi.fn() })) }));

const empty = { records: [], total: 0, limit: 25, offset: 0, evidence_needed: "qualified measured inputs with source provenance" };
const source = {
  id: "synthetic-source", family: "statistics", status: "computed", schema_version: "test-v1", scope: "SYNTHETIC_TEST",
  provenance: { source_sha256: "synthetic-source-hash", units: "ms" }, unavailable: ["Inferential conclusions need a design-checked plan."],
  series: [{ name: "Synthetic measured latency", unit: "ms", kind: "line", points: [
    { label: "Measured zero", value: 0, reason: null }, { label: "Missing observation", value: null, reason: "needs a completed observation" },
    { label: "Measured latency", value: 8, reason: null },
  ] }],
};
function response(body: unknown, status = 200) { return Promise.resolve(new Response(JSON.stringify(body), { status })); }

afterEach(() => { cleanup(); vi.unstubAllGlobals(); vi.clearAllMocks(); });

it.each([
  ["bsda", BSDAPage], ["recovery", RecoveryPage], ["saea", SAEAPage], ["draa", DRAAPage], ["pri", PRIPage],
  ["dqi", DQIPage], ["mchl", MatchedHallucinationPage], ["ml", MLPredictionPage], ["statistics", StatisticalPage],
] as const)("connects the %s page to its own stored evidence API with honest calibration", async (metric, Page) => {
  const fetcher = vi.fn((url: string) => response(url.includes("/evidence?") ? { ...empty, metric } : { items: [], limit: 25, offset: 0 }));
  vi.stubGlobal("fetch", fetcher);
  renderWithProviders(<Page />);
  expect(await screen.findByText(/Unavailable: needs qualified measured inputs/)).toBeInTheDocument();
  expect(screen.getByText("Not established")).toBeInTheDocument();
  expect(screen.queryByText(/^Established$/)).not.toBeInTheDocument();
  expect(fetcher).toHaveBeenCalledWith(expect.stringContaining(`/metrics/compute/${metric}/evidence?`), expect.objectContaining({ credentials: "include" }));
  expect(screen.getByText(`Calculate ${metric.toUpperCase()} from measured inputs`)).toBeInTheDocument();
  expect(echarts.init).not.toHaveBeenCalled();
});

it("preserves genuine zero, null chart gaps, units and inspectable source provenance", async () => {
  vi.stubGlobal("fetch", vi.fn(() => response({ ...empty, records: [source], total: 1 })));
  renderWithProviders(<StoredMetricEvidence metric="statistics" />);
  expect(await screen.findByRole("img", { name: /Synthetic measured latency; ms/ })).toBeInTheDocument();
  expect(screen.getByText("Measured zero")).toBeInTheDocument();
  expect(screen.getByText("Unavailable", { selector: "td" })).toBeInTheDocument();
  expect(screen.getByText("needs a completed observation")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Provenance" }));
  expect(screen.getByText(/synthetic-source-hash/)).toBeInTheDocument();
  const chart = vi.mocked(echarts.init).mock.results[0].value;
  const option = vi.mocked(chart.setOption).mock.calls[0][0] as { series: { data: (number | null)[]; connectNulls: boolean }[] };
  expect(option.series[0].data).toEqual([0, null, 8]);
  expect(option.series[0].connectNulls).toBe(false);
});

it("shows loading without substituting numeric measurements", () => {
  vi.stubGlobal("fetch", vi.fn(() => new Promise(() => {})));
  renderWithProviders(<StoredMetricEvidence metric="bsda" />);
  expect(screen.getByRole("status")).toHaveTextContent("Loading backend data");
  expect(echarts.init).not.toHaveBeenCalled();
});

it("keeps API failures distinct from scientific unavailability", async () => {
  vi.stubGlobal("fetch", vi.fn(() => response({}, 503)));
  renderWithProviders(<StoredMetricEvidence metric="recovery" />);
  expect(await screen.findByRole("alert")).toHaveTextContent("stored measurements could not be loaded");
  expect(screen.getByText("BACKEND/API FAILURE")).toBeInTheDocument();
  expect(echarts.init).not.toHaveBeenCalled();
});

it("rejects an incompatible API response instead of crashing or inventing a zero", async () => {
  vi.stubGlobal("fetch", vi.fn(() => response({ items: [] })));
  renderWithProviders(<StoredMetricEvidence metric="dqi" />);
  expect(await screen.findByRole("alert")).toHaveTextContent("needs a successful evidence API response");
  expect(echarts.init).not.toHaveBeenCalled();
});

it("retains blocked source status and evidence requirements without a chart", async () => {
  vi.stubGlobal("fetch", vi.fn(() => response({ ...empty, total: 1, records: [{ ...source, status: "blocked", series: [], unavailable: ["needs independent outcome labels"] }] })));
  renderWithProviders(<StoredMetricEvidence metric="ml" />);
  expect(await screen.findByText("Unavailable: needs independent outcome labels")).toBeInTheDocument();
  expect(screen.getByText("blocked", { selector: ".status" })).toBeInTheDocument();
  expect(echarts.init).not.toHaveBeenCalled();
});

it("paginates source records without mixing their measurements", async () => {
  const fetcher = vi.fn((url: string) => response({ ...empty, total: 26, offset: url.includes("offset=25") ? 25 : 0,
    records: [{ ...source, id: url.includes("offset=25") ? "synthetic-next-source" : source.id }] }));
  vi.stubGlobal("fetch", fetcher);
  renderWithProviders(<StoredMetricEvidence metric="statistics" />);
  await screen.findByRole("img");
  fireEvent.click(screen.getByRole("button", { name: "Next evidence" }));
  await waitFor(() => expect(screen.getByLabelText("Saved evidence record")).toHaveValue("synthetic-next-source"));
  expect(fetcher).toHaveBeenCalledWith(expect.stringContaining("offset=25"), expect.anything());
  expect(screen.getByRole("button", { name: "Next evidence" })).toBeDisabled();
});
