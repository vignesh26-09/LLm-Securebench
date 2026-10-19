import { cleanup, fireEvent, screen } from "@testing-library/react";
import { CalibrationDetails, ReviewCalibrationDetails, type Calibration } from "../src/components/metrics/CalibrationDetails";
import { renderWithProviders } from "./test-utils";

const source: Calibration = {
  status: "not_established", scope: null, criteria: [
    { text: "Synthetic available measurement", met: true, measured_value: 0, threshold: "Source record", source_path: "synthetic-source.json" },
    { text: "Independent reference required", met: null, measured_value: null, threshold: null, source_path: "synthetic-spec.md:1" },
    { text: "Explicit review required", met: false, measured_value: 0, threshold: "Scoped review", source_path: "synthetic-spec.md:2" },
  ], missing_evidence: ["Needs independent reference study"], measurements: [
    { name: "Synthetic V0 recall", value: .05, unit: "ratio", source_path: "synthetic-verdicts.json", scope: "Synthetic fixture; not a true holdout" },
    { name: "Synthetic recall without positives", value: null, unit: "ratio", source_path: "synthetic-labels.csv", scope: "No positive reference labels" },
  ],
};
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

it("shows criterion pass/fail/unknown, missing values, thresholds, weak results and sources", () => {
  renderWithProviders(<CalibrationDetails calibration={source} />);
  fireEvent.click(screen.getByText("Calibration details"));
  expect(screen.getByText("Pass")).toBeInTheDocument();
  expect(screen.getByText("Fail")).toBeInTheDocument();
  expect(screen.getByText("Unknown")).toBeInTheDocument();
  expect(screen.getAllByText(/Measured: 0/)).toHaveLength(2);
  expect(screen.getByText("5.00%")).toBeInTheDocument();
  expect(screen.getByText("Unavailable", { selector: "td" })).toBeInTheDocument();
  expect(screen.getByText("Needs independent reference study")).toBeInTheDocument();
  expect(screen.getByText("synthetic-verdicts.json")).toBeInTheDocument();
  expect(screen.queryByText(/Established \(scope/)).not.toBeInTheDocument();
});

it("shows an established status only alongside its explicit narrow scope and all met criteria", () => {
  renderWithProviders(<CalibrationDetails calibration={{ ...source, status: "established", scope: "synthetic narrow test scope", criteria: [source.criteria[0]], missing_evidence: [] }} />);
  expect(screen.getByText("Scientific calibration: Established (scope: synthetic narrow test scope)")).toBeInTheDocument();
});

it.each([null, "synthetic scope"])("rejects a status upgrade with missing scope or unmet gates (%s)", scope => {
  renderWithProviders(<CalibrationDetails calibration={{ ...source, status: "established", scope }} />);
  expect(screen.queryByText(/Established \(scope/)).not.toBeInTheDocument();
});

it("has loading, error and empty states without fabricating a value", () => {
  const view = renderWithProviders(<CalibrationDetails loading />);
  expect(screen.getByText(/Loading calibration/)).toBeInTheDocument();
  view.rerender(<CalibrationDetails error />);
  expect(screen.getByText(/calibration evidence could not be loaded/)).toBeInTheDocument();
  view.rerender(<CalibrationDetails />);
  expect(screen.getByText(/needs a calibration checklist/)).toBeInTheDocument();
  expect(screen.queryByText("0")).not.toBeInTheDocument();
});

it("connects scientific reviews to the metric-only evidence endpoint", async () => {
  const fetcher = vi.fn(async () => new Response(JSON.stringify({ calibration: source }), { status: 200 }));
  vi.stubGlobal("fetch", fetcher);
  renderWithProviders(<ReviewCalibrationDetails />);
  expect(await screen.findByText("Synthetic V0 recall")).toBeInTheDocument();
  expect(fetcher).toHaveBeenCalledWith(expect.stringContaining("/metrics/compute/reviews/evidence"), expect.objectContaining({ credentials: "include" }));
});
