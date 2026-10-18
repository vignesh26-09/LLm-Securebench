import { fireEvent, render, screen } from "@testing-library/react";
import { MetricWorkbench } from "../src/components/metrics/MetricWorkbench";
import { BSDAPage } from "../src/pages/MetricPages";
import { renderWithProviders } from "./test-utils";

describe("metric calculator", () => {
  afterEach(() => vi.unstubAllGlobals());
  it("validates JSON before contacting a metric engine", async () => {
    const fetch = vi.fn(); vi.stubGlobal("fetch", fetch);
    render(<MetricWorkbench />);
    fireEvent.change(screen.getByLabelText("Metric input JSON"), { target: { value: "[]" } });
    fireEvent.click(screen.getByRole("button", { name: "Calculate metric" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Supply a JSON object");
    expect(fetch).not.toHaveBeenCalled();
  });
  it("uses the real endpoint and keeps supplied calculations separate from the report", async () => {
    const fetch = vi.fn().mockResolvedValue(new Response(JSON.stringify({ status: "computed", result: { values: { mean: 20 } } }), { status: 200 }));
    vi.stubGlobal("fetch", fetch); render(<MetricWorkbench />);
    fireEvent.change(screen.getByLabelText("Metric input JSON"), { target: { value: '{"values":[10,20,30]}' } });
    fireEvent.click(screen.getByRole("button", { name: "Calculate metric" }));
    expect(await screen.findByText("Calculation result: computed")).toBeInTheDocument();
    expect(fetch.mock.calls[0][0]).toBe("/metrics/compute/statistics");
    expect(screen.getByText(/not saved to this model run/)).toBeInTheDocument();
  });
  it("uses the selected page engine and saves only an engineering record", async () => {
    const fetch = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ status: "component_vector_computed", result: { components: {} } }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ status: "component_vector_computed", record_id: "metric-api:bsda:abc" }), { status: 201 }));
    vi.stubGlobal("fetch", fetch);
    const onSaved = vi.fn();
    render(<MetricWorkbench fixedMetric="bsda" onSaved={onSaved} />);
    fireEvent.change(screen.getByLabelText("Metric input JSON"), { target: { value: '{"value":{"n_runs":1}}' } });
    fireEvent.click(screen.getByRole("button", { name: "Calculate metric" }));
    expect(await screen.findByText("Calculation result: component vector computed")).toBeInTheDocument();
    expect(fetch.mock.calls[0][0]).toBe("/metrics/compute/bsda");
    fireEvent.click(screen.getByRole("button", { name: "Save as engineering record" }));
    expect(await screen.findByText(/Saved engineering record/)).toBeInTheDocument();
    expect(fetch.mock.calls[1][0]).toBe("/metrics/compute/bsda/save");
    expect(onSaved).toHaveBeenCalledOnce();
  });
  it("keeps the BSDA calculator available when there are no stored BSDA records", async () => {
    const fetch = vi.fn().mockResolvedValue(new Response(JSON.stringify({ items: [], total: 0, limit: 25, offset: 0 }), { status: 200 }));
    vi.stubGlobal("fetch", fetch);
    renderWithProviders(<BSDAPage />, "/metrics/bsda");
    expect(await screen.findByText("No records saved yet")).toBeInTheDocument();
    expect(screen.getByText("Calculate BSDA from measured inputs")).toBeInTheDocument();
  });
});
