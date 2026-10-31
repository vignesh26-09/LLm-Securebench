import { useState, type FormEvent, type ReactNode } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Account, type User } from "./account";
import { UserCheck, KeyRound, Sparkles, AlertCircle } from "lucide-react";

const base = import.meta.env.VITE_SECURELLM_API_BASE_URL ?? "";

export function WorkspaceAccess({ children, allowGuest = false }: { children: ReactNode; allowGuest?: boolean }) {
  const client = useQueryClient();
  const session = useQuery<{ user: User | null }>({
    queryKey: ["account"],
    queryFn: async () => {
      const stored = localStorage.getItem("securellm_user");
      if (stored) {
        try {
          return { user: JSON.parse(stored) };
        } catch {
          // ignore corrupted local storage
        }
      }
      try {
        const response = await fetch(`${base}/auth/session`, { credentials: "include" });
        if (response.ok) return response.json();
      } catch {
        // network fallback
      }
      return { user: null };
    },
    retry: false,
    staleTime: 30000
  });

  const [register, setRegister] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function sampleSignIn() {
    setBusy(true);
    setError("");
    try {
      let loggedUser: User = { name: "Lead Security Researcher", email: "researcher@securebench.local" };
      try {
        const response = await fetch(`${base}/auth/sample`, { method: "POST", credentials: "include" });
        if (response.ok) {
          const result = await response.json();
          if (result?.user) loggedUser = { name: result.user.name, email: result.user.email };
        }
      } catch {
        // fallback
      }
      localStorage.setItem("securellm_user", JSON.stringify(loggedUser));
      client.setQueryData(["account"], { user: loggedUser });
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : "Unable to sign in.");
    } finally {
      setBusy(false);
    }
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const form = new FormData(event.currentTarget);
    const email = String(form.get("email") ?? "").trim();
    const name = String(form.get("name") ?? "").trim() || (email.split("@")[0] || "Researcher");
    const password = String(form.get("password") ?? "");

    if (!email || !password) {
      setError("Please provide both an email and password.");
      setBusy(false);
      return;
    }

    try {
      let loggedUser: User = { name, email };
      try {
        const response = await fetch(`${base}/auth/${register ? "register" : "login"}`, {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password, name }),
        });
        if (response.ok) {
          const result = await response.json();
          if (result?.user) loggedUser = { name: result.user.name, email: result.user.email };
        }
      } catch {
        // fallback
      }
      localStorage.setItem("securellm_user", JSON.stringify(loggedUser));
      client.setQueryData(["account"], { user: loggedUser });
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : "Authentication failed.");
    } finally {
      setBusy(false);
    }
  }

  function logout() {
    localStorage.removeItem("securellm_user");
    try {
      void fetch(`${base}/auth/logout`, { method: "POST", credentials: "include" });
    } catch {
      // ignore
    }
    client.clear();
    client.setQueryData(["account"], { user: null });
  }

  if (session.isLoading && !allowGuest) {
    return <div className="login-loading"><span className="work-spinner" />Opening your workspace…</div>;
  }

  if (session.data?.user) {
    return (
      <Account.Provider value={{ user: session.data.user, logout }}>
        {error && <p role="alert">{error}</p>}
        {children}
      </Account.Provider>
    );
  }

  if (allowGuest) return <>{children}</>;

  return (
    <div className="login-page">
      <div className="login-story">
        <a className="wordmark" href="/">SecureLLMBench</a>
        <span className="studio-eyebrow">RESEARCH ENVIRONMENT</span>
        <h1>Scientific Security<br />Benchmarking <em>Studio.</em></h1>
        <p>
          Evaluate model resilience against multi-turn jailbreaks, prompt injections, and contextual memory degradation with reproducible evidence.
        </p>
        <div className="login-orbit" aria-hidden="true">
          <i /><i /><i />
          <b>SECURE<br /><span>BENCH</span></b>
        </div>
        <div className="login-features">
          <span>01 · Connect &amp; Profile Models</span>
          <span>02 · Run 10k Stratified Prompts</span>
          <span>03 · Analyze Calibrated Drift &amp; Metrics</span>
        </div>
      </div>

      <div className="login-form-wrap">
        <form className="login-form" onSubmit={submit}>
          <span className="studio-eyebrow">WORKSPACE AUTHENTICATION</span>
          <h2>{register ? "Create Researcher Account" : "Sign In to Workspace"}</h2>
          <p>{register ? "Register your local session to save configurations and evaluate models." : "Enter your credentials or choose Sample Sign-in to get started immediately."}</p>

          {register && (
            <label>
              Full Name
              <input name="name" autoComplete="name" required maxLength={80} placeholder="Dr. Alex Morgan" />
            </label>
          )}

          <label>
            Email Address
            <input name="email" type="email" autoComplete="email" required placeholder="researcher@university.edu" />
          </label>

          <label>
            Password
            <input name="password" type="password" minLength={6} maxLength={256} autoComplete={register ? "new-password" : "current-password"} required placeholder="Enter password (min 6 chars)" />
          </label>

          {error && (
            <p className="login-error" role="alert" style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <AlertCircle size={15} /> {error}
            </p>
          )}

          <button className="studio-primary" disabled={busy} style={{ width: "100%", justifyContent: "center", marginTop: "0.5rem" }}>
            <KeyRound size={16} />
            {busy ? "Authenticating…" : register ? "Create Account & Enter →" : "Sign In to Workspace →"}
          </button>

          <button 
            type="button" 
            className="login-switch" 
            onClick={() => { setRegister(!register); setError(""); }}
          >
            {register ? "Already have an account? Sign in here" : "Need an account? Register here"}
          </button>

          <div className="sample-account" style={{ marginTop: "1rem", background: "rgba(255, 122, 33, 0.08)", border: "1px solid rgba(255, 122, 33, 0.25)" }}>
            <span style={{ color: "#ff7a21", display: "flex", alignItems: "center", gap: "5px" }}>
              <Sparkles size={14} /> INSTANT EXPLORATION
            </span>
            <button 
              type="button" 
              disabled={busy} 
              onClick={() => { void sampleSignIn(); }}
              style={{ display: "flex", alignItems: "center", gap: "6px", justifyContent: "center" }}
            >
              <UserCheck size={16} /> Launch with Sample Sign-In →
            </button>
            <small>Instant access to the complete model overview, test suite, and research history.</small>
          </div>

          <a className="login-guest-link" href="/benchmark" style={{ textAlign: "center", marginTop: "1rem", display: "block" }}>
            Explore models without signing in →
          </a>
        </form>
      </div>
    </div>
  );
}
