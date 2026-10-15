import { useHealth, useReadiness } from "../../api/hooks";
import { useAccount } from "./account";
import { Link } from "react-router-dom";

function label(loading: boolean, error: unknown, status?: string) {
  if (loading) return "API CHECKING";
  if (error) return "API UNREACHABLE";
  return status === "ready" ? "API READY" : status?.toUpperCase() ?? "API STATUS UNKNOWN";
}

export function Header() {
  const account = useAccount();
  const health = useHealth();
  const readiness = useReadiness();
  return <header><div className="header-location"><span className="connection-dot" />Model evaluation</div><div className="account-actions"><span className="connection-label">{label(health.isLoading || readiness.isLoading, health.error ?? readiness.error, readiness.data?.status)}</span>{account ? <><span className="account-avatar">{account.user.name.slice(0, 1).toUpperCase()}</span><span>{account.user.name}</span><button onClick={account.logout}>Sign out</button></> : <Link to="/workspace">Sign in to workspace ↗</Link>}</div></header>;
}
