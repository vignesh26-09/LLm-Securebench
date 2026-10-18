import { screen } from "@testing-library/react";
import { DqiSummary } from "../src/components/common/DqiSummary";
import { renderWithProviders } from "./test-utils";

it("keeps example DQI and missing embedding limitations visible", () => {
  renderWithProviders(<DqiSummary record={{ id: "fixture", family: "dqi", schema_version: "v1", scope: "DATASET_VERSION", status: "computed", payload: { score: 0.5, components: { novelty: 0 } }, provenance: { source: "example.json", kind: "repository_example_analysis", embeddings_supplied: false } }} />);
  expect(screen.getByText(/Repository example only/)).toBeInTheDocument();
  expect(screen.getByText(/not a measured semantic-novelty result/)).toBeInTheDocument();
  expect(screen.getByText(/NOT SCIENTIFICALLY VALIDATED/)).toBeInTheDocument();
  expect(screen.queryByText("0.5000")).not.toBeInTheDocument();
  expect(screen.queryByText("0.0000")).not.toBeInTheDocument();
  expect(screen.getByText("Unavailable (no embeddings)")).toBeInTheDocument();
});
