import { NavLink } from "react-router-dom";
import { useState } from "react";
import { 
  ChevronLeft, 
  ChevronRight, 
  LayoutDashboard, 
  FlaskConical, 
  PlusCircle, 
  Layers, 
  History, 
  ShieldAlert, 
  Activity, 
  FileCheck2, 
  BrainCircuit, 
  BarChart3,
  BookOpen
} from "lucide-react";

const workspaceLinks = [
  { to: "/workspace", label: "Dashboard", icon: LayoutDashboard },
  { to: "/benchmark", label: "Test a model", icon: FlaskConical },
  { to: "/import", label: "Import model", icon: PlusCircle },
  { to: "/models", label: "Model library", icon: Layers },
] as const;

const metricLinks = [
  { to: "/reviews", label: "Scientific Reviews", icon: FileCheck2 },
  { to: "/metrics/saea", label: "Sequential Attack (SAEA)", icon: ShieldAlert },
  { to: "/metrics/bsda", label: "Behavior Stability (BSDA)", icon: Activity },
  { to: "/metrics/recovery", label: "Recovery Capability (RC)", icon: Activity },
  { to: "/metrics/draa", label: "Dynamic Risk (DRAA)", icon: ShieldAlert },
  { to: "/metrics/pri", label: "Prompt Robustness (PRI)", icon: ShieldAlert },
  { to: "/metrics/dqi", label: "Dataset Quality (DQI)", icon: BookOpen },
  { to: "/metrics/mchl", label: "Hallucination Lift (MCHL)", icon: BrainCircuit },
  { to: "/ml", label: "ML Risk Prediction", icon: BrainCircuit },
  { to: "/statistics", label: "Statistical Analysis", icon: BarChart3 },
] as const;

export function Sidebar({ 
  collapsed, 
  onToggle 
}: { 
  collapsed: boolean; 
  onToggle: () => void; 
}) {
  const [hovered, setHovered] = useState(false);
  const isExpanded = !collapsed || hovered;

  return (
    <nav 
      className={`sidebar modern-sidebar ${collapsed ? "collapsed" : "expanded"} ${hovered ? "hover-expanded" : ""}`} 
      aria-label="Primary navigation"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        width: isExpanded ? "260px" : "68px",
        transition: "width 0.22s cubic-bezier(0.4, 0, 0.2, 1), background 0.2s ease",
        overflowX: "hidden",
        position: "sticky",
        top: 0,
        height: "100vh",
        display: "flex",
        flexDirection: "column",
        gap: "1.25rem",
        padding: isExpanded ? "20px 14px" : "20px 10px",
        zIndex: 50,
        background: "#0d0d0d",
        borderRight: "1px solid #262626",
      }}
    >
      {/* Brand & Toggle Button */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: isExpanded ? "space-between" : "center", marginBottom: "0.5rem" }}>
        {isExpanded ? (
          <NavLink className="brand" to="/" style={{ padding: 0, border: 0, background: "none" }}>
            SecureLLMBench<span style={{ display: "block" }}>MODEL SECURITY STUDIO</span>
          </NavLink>
        ) : (
          <span style={{ fontSize: "1.1rem", fontWeight: 800, color: "#ff7a21" }}>SB</span>
        )}
        <button
          type="button"
          onClick={onToggle}
          title={collapsed ? "Pin sidebar open" : "Collapse sidebar"}
          style={{
            background: "transparent",
            border: "1px solid #333",
            color: "#888",
            cursor: "pointer",
            borderRadius: "6px",
            padding: "4px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            transition: "all 0.15s ease"
          }}
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>

      {/* Main Workspace Navigation */}
      <div className="nav-group" style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
        {isExpanded && <span className="nav-label" style={{ paddingLeft: "10px" }}>Workspace</span>}
        {workspaceLinks.map(({ to, label, icon: Icon }) => (
          <NavLink 
            key={to} 
            to={to} 
            title={!isExpanded ? label : undefined}
            style={{ 
              display: "flex", 
              alignItems: "center", 
              gap: "10px",
              padding: isExpanded ? "9px 12px" : "9px",
              justifyContent: isExpanded ? "flex-start" : "center",
              borderRadius: "8px"
            }}
          >
            <Icon size={18} style={{ flexShrink: 0 }} />
            {isExpanded && <span style={{ whiteSpace: "nowrap" }}>{label}</span>}
          </NavLink>
        ))}
      </div>

      {/* Activity Navigation */}
      <div className="nav-group history-nav" style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
        {isExpanded && <span className="nav-label" style={{ paddingLeft: "10px" }}>Activity</span>}
        <NavLink 
          to="/history" 
          title={!isExpanded ? "Test history" : undefined}
          style={{ 
            display: "flex", 
            alignItems: "center", 
            gap: "10px",
            padding: isExpanded ? "9px 12px" : "9px",
            justifyContent: isExpanded ? "flex-start" : "center",
            borderRadius: "8px"
          }}
        >
          <History size={18} style={{ flexShrink: 0 }} />
          {isExpanded && <span style={{ whiteSpace: "nowrap" }}>Test History</span>}
        </NavLink>
      </div>

      {/* Metrics & Research Navigation */}
      <div 
        className="nav-group research-nav" 
        style={{ 
          display: "flex", 
          flexDirection: "column", 
          gap: "3px", 
          overflowY: "auto", 
          flexGrow: 1, 
          paddingRight: "2px" 
        }}
      >
        {isExpanded && <span className="nav-label" style={{ paddingLeft: "10px" }}>Metrics & Evidence</span>}
        {metricLinks.map(({ to, label, icon: Icon }) => (
          <NavLink 
            key={to} 
            to={to}
            title={!isExpanded ? label : undefined}
            style={{ 
              display: "flex", 
              alignItems: "center", 
              gap: "10px",
              padding: isExpanded ? "7px 12px" : "7px",
              justifyContent: isExpanded ? "flex-start" : "center",
              borderRadius: "8px",
              fontSize: "0.82rem"
            }}
          >
            <Icon size={16} style={{ flexShrink: 0, opacity: 0.85 }} />
            {isExpanded && <span style={{ whiteSpace: "nowrap" }}>{label}</span>}
          </NavLink>
        ))}
      </div>

      {/* Bottom Action Note */}
      {isExpanded ? (
        <div className="sidebar-note" style={{ marginTop: "auto" }}>
          <span className="connection-dot" />
          <strong>Quick Action</strong>
          <span>Ready to evaluate a new model or attack vector?</span>
          <NavLink to="/benchmark" style={{ color: "#ff7a21", fontWeight: 600, padding: 0 }}>Start testing ↗</NavLink>
        </div>
      ) : (
        <NavLink 
          to="/benchmark" 
          title="Start testing"
          style={{ 
            marginTop: "auto", 
            display: "flex", 
            justifyContent: "center", 
            padding: "8px", 
            color: "#ff7a21" 
          }}
        >
          <FlaskConical size={18} />
        </NavLink>
      )}
    </nav>
  );
}
