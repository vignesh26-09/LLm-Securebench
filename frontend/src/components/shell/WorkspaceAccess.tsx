import { useState, type FormEvent, type ReactNode } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { Account, type User } from "./account";
const base = import.meta.env.VITE_SECURELLM_API_BASE_URL ?? "";

export function WorkspaceAccess({ children, allowGuest = false }: { children: ReactNode; allowGuest?: boolean }) {
  const client = useQueryClient();
  const session = useQuery<{ user: User | null }>({ queryKey: ["account"], queryFn: async () => {
    const response = await fetch(`${base}/auth/session`, { credentials: "include" });
    if (!response.ok) throw new Error("Unable to connect to the account service");
    return response.json();
  }, retry: false, staleTime: 30000 });
  const [register, setRegister] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function sampleSignIn() {
    setBusy(true); setError("");
    try {
      const response = await fetch(`${base}/auth/sample`, { method: "POST", credentials: "include" });
      const result = await response.json();
      if (!response.ok) throw new Error(typeof result.detail === "string" ? result.detail : "Sample sign-in is unavailable.");
      client.clear(); client.setQueryData(["account"], result);
    } catch (failure) { setError(failure instanceof Error ? failure.message : "Unable to open the sample workspace"); }
    finally { setBusy(false); }
  }
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError("");
    const form = new FormData(event.currentTarget);
    try {
      const response = await fetch(`${base}/auth/${register ? "register" : "login"}`, {
        method: "POST", credentials: "include", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: form.get("email"), password: form.get("password"), name: form.get("name") || "Researcher" }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(typeof result.detail === "string" ? result.detail : "Check your account details and try again.");
      client.clear(); client.setQueryData(["account"], result);
    } catch (failure) { setError(failure instanceof Error ? failure.message : "Unable to sign in"); }
    finally { setBusy(false); }
  }
  async function logout() {
    try {
      const response = await fetch(`${base}/auth/logout`, { method: "POST", credentials: "include" });
      if (!response.ok) throw new Error("Could not sign out. Try again.");
      client.clear(); client.setQueryData(["account"], { user: null });
    } catch (failure) { setError(failure instanceof Error ? failure.message : "Could not sign out"); }
  }
  if (session.isLoading && !allowGuest) return <div className="login-loading"><span className="work-spinner" />Opening your workspace…</div>;
  if (session.data?.user) return <Account.Provider value={{ user: session.data.user, logout: () => { void logout(); } }}>{error && <p role="alert">{error}</p>}{children}</Account.Provider>;
  if (allowGuest) return <>{children}</>;
  return <div className="login-page">
    <div className="login-story"><a className="wordmark" href="/">SecureLLMBench</a><span className="studio-eyebrow">KNOW YOUR MODEL</span><h1>Trust starts<br />with a <em>test.</em></h1><p>A clear view of how your model responds under pressure. Connect a model, run security checks, and understand every result.</p><div className="login-orbit" aria-hidden="true"><i /><i /><i /><b>SECURE<br /><span>LLM</span></b></div><div className="login-features"><span>01 · Connect your model</span><span>02 · Watch the test</span><span>03 · Read the results</span></div></div>
    <div className="login-form-wrap"><form className="login-form" onSubmit={submit}><span className="studio-eyebrow">YOUR RESEARCH WORKSPACE</span><h2>{register ? "Create your account" : "Welcome back."}</h2><p>{register ? "Create a local account to connect your model and explore the workspace." : "Sign in to connect your model and explore saved results."}</p>
      {register && <label>Your name<input name="name" autoComplete="name" required maxLength={80} placeholder="Alex Morgan" /></label>}
      <label>Email address<input name="email" type="email" autoComplete="email" required placeholder="you@example.com" /></label>
      <label>Password<input name="password" type="password" minLength={10} maxLength={256} autoComplete={register ? "new-password" : "current-password"} required placeholder="At least 10 characters" /></label>
      {(error || session.isError) && <p className="login-error" role="alert">{error || "Account service unavailable. Start the backend, then retry."}</p>}
      <button className="studio-primary" disabled={busy || session.isError}>{busy ? "Please wait…" : register ? "Create account →" : "Sign in →"}</button>
      {session.isError && <button type="button" onClick={() => { void session.refetch(); }}>Retry connection</button>}
      <button type="button" className="login-switch" onClick={() => { setRegister(!register); setError(""); }}>{register ? "Already have an account? Sign in" : "New here? Create an account"}</button>
      <div className="sample-account"><span>JUST EXPLORING?</span><button type="button" disabled={busy || session.isError} onClick={() => { void sampleSignIn(); }}>Use sample sign-in →</button><small>Opens a shared local sample account. No password needed.</small></div>
      <a className="login-guest-link" href="/benchmark">Try a predefined model without signing in →</a>
      <small>Local workspace · Accounts are stored on this server. Signed-in users share this research workspace.</small>
    </form></div>
  </div>;
}
