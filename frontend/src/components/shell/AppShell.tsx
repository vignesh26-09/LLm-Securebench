import type { ReactNode } from "react";
import { Header } from "./Header";
import { Sidebar } from "./Sidebar";

export function AppShell({ children }: { children: ReactNode }) { return <div className="app-shell"><Sidebar /><div className="main-area"><Header /><main>{children}</main><footer>SecureLLMBench research interface · upstream statuses and provenance are preserved.</footer></div></div>; }
