import { fireEvent, render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { WorkspaceAccess } from "../src/components/shell/WorkspaceAccess";

function setup(fetcher: (url: string, init?: RequestInit) => Promise<Response>) {
  vi.stubGlobal("fetch", vi.fn(fetcher));
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}><WorkspaceAccess><p>Connected workspace</p></WorkspaceAccess></QueryClientProvider>);
}
const response = (body: unknown, status = 200) => Promise.resolve(new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } }));

describe("workspace account access", () => {
  afterEach(() => vi.unstubAllGlobals());
  it("opens a server-backed sample session without entering credentials", async () => {
    setup((url) => url.endsWith("/auth/sample") ? response({ user: { name: "Sample Researcher", email: "sample@securellm.local" } }) : response({ user: null }));
    fireEvent.click(await screen.findByRole("button", { name: "Use sample sign-in →" }));
    expect(await screen.findByText("Connected workspace")).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/auth/sample"), expect.objectContaining({ method: "POST", credentials: "include" }));
  });
  it("shows login and a guest testing link when there is no session", async () => {
    setup(() => response({ user: null }));
    expect(await screen.findByRole("heading", { name: "Welcome back." })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /without signing in/ })).toHaveAttribute("href", "/benchmark");
    expect(screen.queryByText("Connected workspace")).not.toBeInTheDocument();
  });
  it("opens the protected content after a successful server login", async () => {
    setup((url) => url.endsWith("/auth/login") ? response({ user: { name: "Tester", email: "tester@example.test" } }) : response({ user: null }));
    await screen.findByRole("button", { name: "Sign in →" });
    fireEvent.change(screen.getByLabelText("Email address"), { target: { value: "tester@example.test" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "test-long-password" } });
    fireEvent.click(screen.getByRole("button", { name: "Sign in →" }));
    expect(await screen.findByText("Connected workspace")).toBeInTheDocument();
  });
  it("keeps the login screen visible when the server rejects credentials", async () => {
    setup((url) => url.endsWith("/auth/login") ? response({ detail: "Email or password is incorrect" }, 401) : response({ user: null }));
    await screen.findByRole("button", { name: "Sign in →" });
    fireEvent.change(screen.getByLabelText("Email address"), { target: { value: "tester@example.test" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "test-long-password" } });
    fireEvent.click(screen.getByRole("button", { name: "Sign in →" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Email or password is incorrect");
    expect(screen.queryByText("Connected workspace")).not.toBeInTheDocument();
  });
});
