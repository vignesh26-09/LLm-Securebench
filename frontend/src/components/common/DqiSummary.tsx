import type { ScientificRecord } from "../../api/types";

export function DqiSummary({ record }: { record: ScientificRecord }) {
  const components = record.payload.components;
  if (components === null || typeof components !== "object" || Array.isArray(components)) return null;
  return <article className="research-note"><h2>Exploratory dataset diagnostic</h2><p>Source: {String(record.provenance.source ?? "See record provenance")}. {record.provenance.kind === "repository_example_analysis" && "Repository example only; not a validated research corpus."}</p>
    {record.provenance.embeddings_supplied !== false && typeof record.payload.score === "number" && <p>Source DQI value: <strong>{record.payload.score.toFixed(4)}</strong></p>}
    <dl className="dqi-components">{Object.entries(components).map(([name, value]) => <div key={name}><dt>{name.replaceAll("_", " ")}</dt><dd>{name === "novelty" && record.provenance.embeddings_supplied === false ? "Unavailable (no embeddings)" : typeof value === "number" ? value.toFixed(4) : JSON.stringify(value)}</dd></div>)}</dl>
    {record.provenance.embeddings_supplied === false && <p>No embeddings were supplied. The novelty component uses the existing implementation’s zero default; it is not a measured semantic-novelty result.</p>}
    <p>EXPLORATORY / NOT SCIENTIFICALLY VALIDATED. Full precision, weights and provenance are preserved in the stored record below.</p>
  </article>;
}
