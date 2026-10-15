import { NavLink } from "react-router-dom";

const workspace = [["/workspace", "Dashboard"], ["/benchmark", "Test a model"], ["/import", "Import your model"], ["/models", "Model library"]] as const;
const metrics = [
  ["/reviews", "Scientific reviews"], ["/metrics/bsda", "BSDA"], ["/metrics/recovery", "Recovery capability"], ["/metrics/saea", "SAEA"],
  ["/metrics/draa", "DRAA"], ["/metrics/pri", "PRI"], ["/metrics/dqi", "DQI"], ["/ml", "ML prediction"], ["/statistics", "Statistical analysis"],
] as const;

function NavigationLinks({ items }: { items: readonly (readonly [string, string])[] }) {
  return <>{items.map(([to, label]) => <NavLink key={to} to={to} end={to === "/"}>{label}</NavLink>)}</>;
}

export function Sidebar() {
  return <nav className="sidebar" aria-label="Primary navigation">
    <NavLink className="brand" to="/">SecureLLMBench<span>MODEL SECURITY STUDIO</span></NavLink>
    <div className="nav-group"><span className="nav-label">Workspace</span><NavigationLinks items={workspace} /></div>
    <div className="nav-group history-nav"><span className="nav-label">Your activity</span><NavLink to="/history">Test history</NavLink></div>
    <div className="nav-group research-nav"><span className="nav-label">Metrics &amp; research</span><NavigationLinks items={metrics} /></div>
    <div className="sidebar-note"><span className="connection-dot" /><strong>Your next step</strong><span>Choose a model. Run a test. Read the results.</span><NavLink to="/benchmark">Start testing ↗</NavLink></div>
  </nav>;
}
