import { useState } from "react";

export function ProvenanceBadge({ value }: { value: Record<string, unknown> }) {
  const [open, setOpen] = useState(false);
  return <div className="provenance"><button type="button" onClick={() => setOpen((current) => !current)}>Provenance</button>{open && <pre>{JSON.stringify(value, null, 2)}</pre>}</div>;
}
