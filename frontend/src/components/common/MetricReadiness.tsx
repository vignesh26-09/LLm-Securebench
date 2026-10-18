export function MetricReadiness({ implementation, calibration, detail }: { implementation: string; calibration: string; detail: string }) {
  return <div className="metric-readiness">
    <div><span>Implementation</span><strong>{implementation}</strong></div>
    <div><span>Scientific calibration</span><strong>{calibration}</strong></div>
    <p>{detail}</p>
  </div>;
}
