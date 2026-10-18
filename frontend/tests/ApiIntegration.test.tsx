import { screen } from "@testing-library/react";
import App from "../src/App";
import { renderWithProviders } from "./test-utils";

describe("Phase 11 API integration", () => {
  afterEach(() => vi.unstubAllGlobals());
  it("uses the actual paginated scientific-record response shape", async () => {
    vi.stubGlobal("fetch", vi.fn((input: string) => {
      if (input.includes("scientific-records")) return Promise.resolve(new Response(JSON.stringify({ items: [{ id: "artifact-1", family: "draa", schema_version: "draa-evidence-v1", scope: "EVALUATION", status: "uncalibrated", payload: { risk_score: null }, provenance: { source: "test" } }], limit: 25, offset: 0 }), { status: 200, headers: { "Content-Type": "application/json" } }));
      if (input.endsWith("/ready")) return Promise.resolve(new Response(JSON.stringify({ status: "ready" }), { status: 200, headers: { "Content-Type": "application/json" } }));
      return Promise.resolve(new Response(JSON.stringify({ service: "securellmbench", status: "ok" }), { status: 200, headers: { "Content-Type": "application/json" } }));
    }));
    renderWithProviders(<App />, "/records");
    expect(await screen.findByText("artifact-1")).toBeInTheDocument();
    expect(screen.getByText("uncalibrated")).toBeInTheDocument();
  });
  it("distinguishes an API failure from a successful scientific null", async () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(new Response("down", { status: 503 }))));
    renderWithProviders(<App />, "/records");
    expect(await screen.findByText("BACKEND/API FAILURE")).toBeInTheDocument();
  });
  it("distinguishes a 404 response from a scientific null value", async () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(new Response("missing", { status: 404 }))));
    renderWithProviders(<App />, "/records");
    expect(await screen.findByText("BACKEND RECORD NOT FOUND")).toBeInTheDocument();
  });
  it("renders an upstream null without converting it into a zero", async () => {
    vi.stubGlobal("fetch", vi.fn((input: string) => {
      if (input.includes("scientific-records")) return Promise.resolve(new Response(JSON.stringify({ items: [{ id: "artifact-null", family: "rc", schema_version: "lossless-payload-v1", scope: "EVALUATION", status: "undefined", payload: { raw_measurement: null }, provenance: {} }], limit: 25, offset: 0 }), { status: 200, headers: { "Content-Type": "application/json" } }));
      return Promise.resolve(new Response(JSON.stringify({ status: "ready" }), { status: 200, headers: { "Content-Type": "application/json" } }));
    }));
    renderWithProviders(<App />, "/records");
    expect(await screen.findByText("artifact-null")).toBeInTheDocument();
    expect(screen.getByText("undefined")).toBeInTheDocument();
    expect(screen.queryByText("0")).not.toBeInTheDocument();
  });
});
