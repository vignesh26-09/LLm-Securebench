import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { apiClient } from "../api/client";
import { ErrorState, LoadingState } from "../components/common/AsyncState";

export function ComparisonPage() {
  const [offset, setOffset] = useState(0);
  const [selected, setSelected] = useState<Record<string, unknown>[]>([]);
  const query = useQuery({ queryKey: ["models", offset], queryFn: () => apiClient.resources("models", offset), retry: false });
  const fields = Array.from(new Set(selected.flatMap(row => Object.keys((row.payload ?? {}) as Record<string, unknown>)))).sort();
  return <section><div className="eyebrow">Research workspace / Comparison</div><h1>Model comparison</h1><p>Select up to three stored model configurations to inspect their settings side by side. Values come directly from saved configurations; this view does not rank model performance.</p>
    {query.isLoading && <LoadingState />}{query.isError && <ErrorState error={query.error} />}
    {query.data && <>{query.data.total === 0 ? <div className="research-note"><h2>No model configurations saved yet</h2><p>Comparison is ready to use once model configurations have been persisted. The repository currently contains a dataset example, but no model configurations or benchmark results.</p><Link to="/datasets">Explore the existing dataset →</Link></div> : <>
      <fieldset className="comparison-picker"><legend>Choose configurations ({selected.length}/3)</legend>{query.data.items.map(row => {
        const checked = selected.some(item => item.id === row.id);
        return <label key={String(row.id)}><input type="checkbox" checked={checked} disabled={!checked && selected.length >= 3} onChange={() => setSelected(current => checked ? current.filter(item => item.id !== row.id) : [...current, row])} />{String(row.model_name)} <small>{String(row.id)}</small></label>;
      })}</fieldset>
      <nav className="pagination" aria-label="Model selection pagination"><button disabled={!offset} onClick={() => setOffset(offset - 25)}>Previous</button><span>{offset + 1}–{Math.min(offset + 25, query.data.total)} of {query.data.total}</span><button disabled={offset + 25 >= query.data.total} onClick={() => setOffset(offset + 25)}>Next</button></nav>
    </>}</>}
    {selected.length > 0 && <><button className="clear-selection" onClick={() => setSelected([])}>Clear selection</button><div className="table-wrap"><table className="entity-table"><caption>Stored configuration values</caption><thead><tr><th>Setting</th>{selected.map(row => <th key={String(row.id)}>{String(row.model_name)}<br />{String(row.id)}</th>)}</tr></thead><tbody>
      {fields.map(field => <tr key={field}><th>{field}</th>{selected.map(row => { const payload = (row.payload ?? {}) as Record<string, unknown>; return <td key={String(row.id)}><pre>{Object.hasOwn(payload, field) ? JSON.stringify(payload[field], null, 2) : "Not supplied"}</pre></td>; })}</tr>)}
      <tr><th>Recorded runs</th>{selected.map(row => <td key={String(row.id)}><Link to={`/runs?filter_by=model_config_id&value=${encodeURIComponent(String(row.id))}`}>View linked runs →</Link></td>)}</tr>
    </tbody></table></div></>}
  </section>;
}
