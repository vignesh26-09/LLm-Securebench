import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import type { ReactElement } from "react";
import { MemoryRouter } from "react-router-dom";

export function renderWithProviders(ui: ReactElement, initialPath = "/") {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  // These page tests exercise an authenticated shared research workspace.
  client.setQueryData(["account"], { user: { name: "Test Researcher", email: "researcher@example.test" } });
  return render(<QueryClientProvider client={client}><MemoryRouter initialEntries={[initialPath]}>{ui}</MemoryRouter></QueryClientProvider>);
}
