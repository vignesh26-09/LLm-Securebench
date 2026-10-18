import { ApiError } from "../../api/types";

export function LoadingState() { return <p role="status">Loading backend data…</p>; }
export function EmptyState({ message }: { message: string }) { return <p className="empty">{message}</p>; }
export function BackendUnavailable({ resource, endpoint }: { resource: string; endpoint: string }) {
  return <section className="notice unavailable"><h2>BACKEND ENDPOINT UNAVAILABLE</h2><p>{resource} requires <code>{endpoint}</code>, which is not implemented by the current Phase 11 API.</p><p>No demo data is substituted for this unavailable integration.</p></section>;
}
export function ErrorState({ error }: { error: unknown }) {
  const apiError = error instanceof ApiError ? error : undefined;
  if (apiError?.status === 404) return <section className="notice error"><h2>BACKEND RECORD NOT FOUND</h2><p>The API returned HTTP 404. This is distinct from a scientific value that is unavailable or undefined.</p></section>;
  return <section className="notice error"><h2>BACKEND/API FAILURE</h2><p>{apiError?.message ?? "The request could not be completed."}</p>{apiError?.requestId && <p>Request ID: <code>{apiError.requestId}</code></p>}</section>;
}
