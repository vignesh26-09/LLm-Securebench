import { Component, type ReactNode } from "react";

class Boundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  componentDidCatch() { /* chart failure stays local */ }
  render() { return this.state.failed ? <p className="notice error">Chart rendering failed; source records remain available below.</p> : this.props.children; }
}

export function ChartContainer({ children }: { children: ReactNode }) { return <Boundary><div className="chart-container">{children}</div></Boundary>; }
