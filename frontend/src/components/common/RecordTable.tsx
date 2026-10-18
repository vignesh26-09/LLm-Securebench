import type { ScientificRecord } from "../../api/types";
import { ProvenanceBadge } from "./ProvenanceBadge";
import { StatusBadge } from "./StatusBadge";

export function RecordTable({ records }: { records: ScientificRecord[] }) {
  return <div className="table-wrap"><table><thead><tr><th>ID</th><th>Family</th><th>Scope</th><th>Schema</th><th>Result status</th><th>Payload</th><th>Evidence</th></tr></thead><tbody>{records.map((record) => <tr key={record.id}><td><code>{record.id}</code></td><td>{record.family}</td><td>{record.scope}</td><td>{record.schema_version}</td><td><StatusBadge status={record.status} /></td><td><details><summary>Inspect source payload</summary><pre>{JSON.stringify(record.payload, null, 2)}</pre></details></td><td><ProvenanceBadge value={record.provenance} /></td></tr>)}</tbody></table></div>;
}
