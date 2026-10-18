const supported = new Set([
  "applicable", "not_applicable", "undefined", "unavailable", "insufficient_data", "failed", "skipped",
  "uncalibrated", "computed", "not_computed", "absent", "not_evaluated", "incompatible", "refused",
  "calibration_unavailable", "failed_evaluation",
]);

export function StatusBadge({ status }: { status: string | null | undefined }) {
  const normalized = status && supported.has(status) ? status : "unspecified";
  const label = status ? status.replaceAll("_", " ") : "not supplied";
  return <span className={`status status-${normalized}`}>{label}</span>;
}
