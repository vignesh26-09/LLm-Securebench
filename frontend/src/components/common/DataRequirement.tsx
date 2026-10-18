import { Link } from "react-router-dom";

const requirements: Record<string, [string, string, string]> = {
  models: ["No model configurations have been saved. A configuration identifies the model and generation settings used for a run.", "/datasets", "Explore source datasets"],
  "benchmark-runs": ["No benchmark runs have been persisted. Runs need a saved model configuration and an identified input dataset.", "/models", "View model configurations"],
  evaluations: ["No evaluation results have been persisted. They are produced by benchmark execution and retain the original run identity.", "/runs", "View benchmark runs"],
  "layer1-results": ["No detector evidence has been persisted for these evaluations.", "/evaluations", "View evaluations"],
  "layer2-results": ["No judge evidence has been persisted for these evaluations.", "/evaluations", "View evaluations"],
  "scientific-reviews": ["No explicit scientific reviews have been recorded. Results do not automatically create review decisions.", "/records", "Inspect scientific evidence"],
};
const scientific: Record<string, string> = {
  bsda: "No matched baseline and perturbed response measurements are saved yet. Use the calculator above with actual paired observations; scientific eligibility still requires validated measurements.",
  rc: "No qualified baseline, attack and recovery trajectory is saved yet. Use the calculator above with measured states; a missing calibration keeps recovery indices undefined.",
  saea: "No matched sequential and isolated-control measurements are saved yet. Use the calculator above with actual state evidence; contaminated or missing controls remain blocked.",
  draa: "DRAA requires persisted Mode A/B evidence. Mode C remains deferred by the research specification.",
  pri: "PRI requires persisted descriptive profile records and their coverage metadata.",
  dqi: "DQI requires a persisted output from the existing exploratory dataset analysis. Importing a dataset alone does not calculate DQI.",
  ml: "No eligible labeled experiment is saved yet. The calculator requires independent labels, admissible features and an explicit split; existing readiness records are not model predictions.",
  statistics: "Statistical analysis requires a saved computation artifact with source data and protocol provenance.",
};
export function DataRequirement({ resource, filtered = false }: { resource: string; filtered?: boolean }) {
  const info = requirements[resource];
  return <div className="research-note"><h2>{filtered ? "No records match this view" : "No records saved yet"}</h2><p>{filtered ? "This query has no matching persisted records. Browse the source records to check the selected identity." : info?.[0] ?? scientific[resource] ?? "This view is connected. Records will appear when source artifacts are persisted with their identity and provenance."}</p><Link to={info?.[1] ?? (resource === "dqi" ? "/datasets" : "/records")}>{info?.[2] ?? (resource === "dqi" ? "Explore source datasets" : "Browse scientific records")} →</Link></div>;
}
