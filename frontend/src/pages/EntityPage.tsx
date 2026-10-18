import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";
import { apiClient } from "../api/client";
import { ErrorState, LoadingState } from "../components/common/AsyncState";
import { DataRequirement } from "../components/common/DataRequirement";

const relationships: Record<string, [string, string]> = {
  datasets: ["/dataset-versions", "dataset_id"], models: ["/runs", "model_config_id"],
  "dataset-versions": ["/runs", "dataset_version_id"], "benchmark-runs": ["/evaluations", "benchmark_run_id"],
};

export function EntityPage({ title, resource, description }: { title: string; resource: string; description: string }) {
  const [params] = useSearchParams();
  const filterBy = params.get("filter_by") ?? undefined;
  const value = params.get("value") ?? undefined;
  return <EntityBrowser key={`${resource}:${filterBy}:${value}`} title={title} resource={resource} description={description} filterBy={filterBy} value={value} />;
}

function EntityBrowser({ title, resource, description, filterBy, value }: { title: string; resource: string; description: string; filterBy?: string; value?: string }) {
  const [offset, setOffset] = useState(0);
  const query = useQuery({ queryKey: [resource, offset, filterBy, value], queryFn: () => apiClient.resources(resource, offset, filterBy, value), retry: false });
  const relation = relationships[resource];
  return <section><div className="eyebrow">Research workspace / Evidence catalogue</div><h1>{title}</h1><p>{description}</p>
    {filterBy && <p className="filter-context">Filtered by {filterBy}: <code>{value}</code></p>}
    {query.isLoading && <LoadingState />}{query.isError && <ErrorState error={query.error} />}
    {query.data && <><p className="result-count">{query.data.total} persisted records{filterBy ? " matching this filter" : ""}</p>
      {query.data.items.length === 0 ? <DataRequirement resource={resource} filtered={Boolean(filterBy)} /> :
        <div className="table-wrap"><table className="entity-table"><thead><tr><th>Record</th><th>Source status / identity</th><th>Evidence & provenance</th><th>Explore</th></tr></thead><tbody>{query.data.items.map(row => <tr key={String(row.id)}>
          <td><strong>{String(row.name ?? row.model_name ?? row.id)}</strong><small>{String(row.id)}</small></td>
          <td>{String(row.status ?? row.execution_status ?? row.version ?? "Source record")}<small>{resource === "evaluations" && typeof row.latency_ms === "number" ? `${row.latency_ms.toFixed(1)} ms` : ""}</small></td>
          <td>{resource === "evaluations" && <div className="response-preview"><strong>Prompt</strong><p>{String(row.prompt ?? "Not supplied")}</p><strong>Model response</strong><p>{row.response === null ? "No response returned" : String(row.response)}</p></div>}{resource === "layer1-results" && <p>Detector-native signal: {String(row.score)} · uncalibrated</p>}<details><summary>Inspect stored record</summary><pre>{JSON.stringify(row, null, 2)}</pre></details></td>
          <td>{relation && <Link to={`${relation[0]}?filter_by=${relation[1]}&value=${encodeURIComponent(String(row.id))}`}>View linked records →</Link>}
          {resource === "evaluations" && <><Link to={`/security?filter_by=evaluation_result_id&value=${encodeURIComponent(String(row.id))}`}>Layer 1 evidence</Link><br /><Link to={`/layer2?filter_by=evaluation_result_id&value=${encodeURIComponent(String(row.id))}`}>Layer 2 evidence</Link></>}</td>
        </tr>)}</tbody></table></div>}
      <nav className="pagination" aria-label={`${title} pagination`}><button disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - 25))}>Previous</button><span>{query.data.total === 0 ? "0" : `${offset + 1}–${Math.min(offset + 25, query.data.total)}`} of {query.data.total}</span><button disabled={offset + 25 >= query.data.total} onClick={() => setOffset(offset + 25)}>Next</button></nav>
    </>}
  </section>;
}
