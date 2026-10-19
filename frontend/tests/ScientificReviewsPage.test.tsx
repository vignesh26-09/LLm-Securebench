import { cleanup, screen } from "@testing-library/react";
import { ScientificReviewsPage } from "../src/pages/ScientificReviewsPage";
import { renderWithProviders } from "./test-utils";

afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

it("keeps review readiness honest and reuses the explicit empty-state browser", async () => {
  vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(new Response(JSON.stringify({ items: [], total: 0, limit: 25, offset: 0 }), { status: 200 }))));
  renderWithProviders(<ScientificReviewsPage />, "/reviews");
  expect(screen.getByText("Implemented review records")).toBeInTheDocument();
  expect(screen.getByText("Not established")).toBeInTheDocument();
  expect(await screen.findByText(/No explicit scientific reviews have been recorded/)).toBeInTheDocument();
  expect(screen.getByText(/needs documented independent review decisions/)).toBeInTheDocument();
});

it("does not promote an existing review decision into established calibration", async () => {
  vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(new Response(JSON.stringify({ items: [
    { id: "synthetic-review", decision: "reviewed", claim_id: "synthetic-claim", evidence_bundle_id: "synthetic-bundle", provenance: { synthetic_fixture: true } },
  ], total: 1, limit: 25, offset: 0 }), { status: 200 }))));
  renderWithProviders(<ScientificReviewsPage />, "/reviews");
  expect(await screen.findByText("synthetic-review", { selector: "strong" })).toBeInTheDocument();
  expect(screen.getByText("Not established")).toBeInTheDocument();
  expect(screen.queryByText(/^Established$/)).not.toBeInTheDocument();
});

it("preserves the shared review browser API error state", async () => {
  vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(new Response(JSON.stringify({ detail: "synthetic failure" }), { status: 503 }))));
  renderWithProviders(<ScientificReviewsPage />, "/reviews");
  expect(await screen.findByText("BACKEND/API FAILURE")).toBeInTheDocument();
});
