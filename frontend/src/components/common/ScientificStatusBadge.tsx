import { scientificMaturityLabel } from "../../config/constants";

export function ScientificStatusBadge({ status }: { status?: string | null }) {
  return <span className="status status-uncalibrated">{status ?? scientificMaturityLabel}</span>;
}
