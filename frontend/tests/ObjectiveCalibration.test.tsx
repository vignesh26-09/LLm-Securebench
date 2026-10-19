import { cleanup, screen } from "@testing-library/react";
import { CalibrationDetails, type Calibration } from "../src/components/metrics/CalibrationDetails";
import { renderWithProviders } from "./test-utils";

afterEach(() => cleanup());
const base: Calibration = { status: "not_established", scope: null, criteria: [], missing_evidence: ["Needs independent claim review"], measurements: [] };

it("shows the context proxy scope, abstentions and failed/unscored outcomes without fabricating a lift", () => {
  renderWithProviders(<CalibrationDetails calibration={{ ...base, objective_evidence: {
    kind: "hallucination_proxy", scope: "Synthetic context proxy only", source_path: "synthetic-summary.json", source_run: "synthetic-run", limitations: ["Not canonical MCHL"],
    hallucination_proxy: { "synthetic-model": { assigned_pairs: 2, complete_pairs: 0, lift: null, ci95: null,
      counts: { grounded: { correct: 0, abstain: 0, hallucinated: 0, failed: 2 }, ungrounded: { correct: 0, abstain: 2, hallucinated: 0, failed: 0 } } } },
  } }} />);
  expect(screen.getByText("Synthetic context proxy only")).toBeInTheDocument();
  expect(screen.getByText(/not canonical adversarial MCHL/)).toBeInTheDocument();
  expect(screen.getAllByText("Unavailable", { selector: "td" })).toHaveLength(2);
  expect(screen.getByText("Failed/unscored")).toBeInTheDocument();
  expect(screen.getByText("0 / 2")).toBeInTheDocument();
});

it("shows weak prediction performance and uncertainty against the majority baseline", () => {
  const metric = { pr_auc: null, recall: 0, precision: null, accuracy: .5 };
  const interval = { ci95: [-.1, .1], undefined_resamples: 0 };
  const intervals = { pr_auc: interval, recall: interval, precision: { ci95: null, undefined_resamples: 1000 }, accuracy: interval };
  renderWithProviders(<CalibrationDetails calibration={{ ...base, objective_evidence: {
    kind: "prediction", scope: "Synthetic oracle target only", source_path: "synthetic-summary.json", source_run: "synthetic-run", limitations: [],
    gate: { completed: 8, failed: 2, positives: 3, mixed_template_groups: 1 },
    prediction: { template_id: { logistic: metric, majority: metric, comparison: "Logistic does not beat the majority baseline on PR-AUC", folds: [{ threshold_train_only: .4 }], bootstrap: { logistic: intervals, majority: intervals, difference: intervals } } },
  } }} />);
  expect(screen.getByText(/Logistic does not beat the majority baseline/)).toBeInTheDocument();
  expect(screen.getByText(/No clear PR-AUC improvement/)).toBeInTheDocument();
  expect(screen.getByText(/training scores only: 0.4/)).toBeInTheDocument();
  expect(screen.getByText(/8 completed, 2 failed\/incomplete excluded/)).toBeInTheDocument();
  expect(screen.getAllByText("Unavailable", { selector: "td" }).length).toBeGreaterThan(0);
});
