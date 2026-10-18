import { fireEvent, screen } from "@testing-library/react";
import App from "../src/App";
import { renderWithProviders } from "./test-utils";

describe("configuration comparison", () => {
  afterEach(() => vi.unstubAllGlobals());
  it("compares actual settings while keeping null and missing distinct", async () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(new Response(JSON.stringify({ items: [
      { id: "a", model_name: "Alpha", payload: { temperature: null } },
      { id: "b", model_name: "Beta", payload: { max_tokens: 20 } },
    ], total: 2, limit: 25, offset: 0 })))));
    renderWithProviders(<App />, "/comparison");
    fireEvent.click(await screen.findByRole("checkbox", { name: "Alpha a" }));
    fireEvent.click(screen.getByRole("checkbox", { name: "Beta b" }));
    expect(screen.getByText("null")).toBeInTheDocument();
    expect(screen.getAllByText("Not supplied")).toHaveLength(2);
    expect(screen.getByText("20")).toBeInTheDocument();
    expect(screen.getAllByText("View linked runs →")).toHaveLength(2);
  });
  it("explains missing models without claiming a missing endpoint", async () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(new Response(JSON.stringify({ items: [], total: 0, limit: 25, offset: 0 })))));
    renderWithProviders(<App />, "/comparison");
    expect(await screen.findByText("No model configurations saved yet")).toBeInTheDocument();
    expect(screen.queryByText("BACKEND ENDPOINT UNAVAILABLE")).not.toBeInTheDocument();
  });
  it("does not misreport an unknown URL as a backend failure", () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(new Response(JSON.stringify({ status: "ready" })))));
    renderWithProviders(<App />, "/missing-page");
    expect(screen.getByText("Page not found")).toBeInTheDocument();
    expect(screen.queryByText("BACKEND ENDPOINT UNAVAILABLE")).not.toBeInTheDocument();
  });
});
