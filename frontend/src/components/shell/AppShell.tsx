import { useState, type ReactNode } from "react";
import { Header } from "./Header";
import { Sidebar } from "./Sidebar";

export function AppShell({ children }: { children: ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div 
      className={`app-shell ${collapsed ? "sidebar-collapsed" : "sidebar-expanded"}`}
      style={{
        display: "grid",
        gridTemplateColumns: collapsed ? "68px minmax(0, 1fr)" : "260px minmax(0, 1fr)",
        transition: "grid-template-columns 0.22s cubic-bezier(0.4, 0, 0.2, 1)",
        minHeight: "100vh",
        background: "#0d0d0d"
      }}
    >
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed(prev => !prev)} />
      <div className="main-area" style={{ minWidth: 0, display: "flex", flexDirection: "column" }}>
        <Header />
        <main style={{ flex: 1, padding: "28px 32px" }}>{children}</main>
        <footer>SecureLLMBench research interface · upstream statuses and provenance are preserved.</footer>
      </div>
    </div>
  );
}
