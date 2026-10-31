export function ResponseTimePlot({ cases }: { cases: { id?: string; case_id?: string | null; execution_status?: string; latency_ms: number | null; finish_reason?: string | null; response_available?: boolean; observed_detector_signals?: { detector: string; score: number }[] }[] }) {
  if (!cases || cases.length === 0 || !cases.some(item => item.latency_ms != null)) {
    return (
      <article className="studio-panel response-plot" style={{ background: "#141414", border: "1px solid #282828", borderRadius: "12px", padding: "24px", marginTop: "1.5rem" }}>
        <span className="studio-eyebrow">LATENCY &amp; BASELINE DRIFT</span>
        <h2>Response Speed &amp; Behavioral Drift</h2>
        <p role="status" style={{ color: "#888" }}>No response times recorded for this run.</p>
      </article>
    );
  }

  const validCases = cases.filter(c => c.latency_ms != null);
  const latencies = validCases.map(c => c.latency_ms as number);
  const baselineLatency = latencies[0] ?? 1000;
  const maximum = Math.max(baselineLatency * 1.5, ...latencies, 2000);

  const width = 760;
  const height = 240;
  const left = 60;
  const top = 30;
  const bottom = 190;

  const x = (index: number) => left + index * (width - left - 30) / Math.max(1, validCases.length - 1);
  const y = (value: number) => bottom - (value / maximum) * (bottom - top);

  const path = validCases
    .map((item, index) => `${index === 0 ? "M" : "L"}${x(index)},${y(item.latency_ms!)}`)
    .join(" ");

  const baselineY = y(baselineLatency);

  return (
    <article className="studio-panel response-plot" style={{ background: "#141414", border: "1px solid #282828", borderRadius: "12px", padding: "24px", marginTop: "1.5rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1.25rem", borderBottom: "1px solid #222", paddingBottom: "12px" }}>
        <div>
          <span className="studio-eyebrow" style={{ margin: 0 }}>RESPONSE DRIFT TRACKER</span>
          <h2 style={{ fontSize: "1.15rem", fontWeight: 600, margin: "2px 0 0 0" }}>
            Response Time &amp; Baseline Drift Across Test Sequence
          </h2>
        </div>

        <div style={{ display: "flex", gap: "16px", alignItems: "center", fontSize: "0.8rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "#38bdf8" }}>
            <span style={{ width: "16px", height: "2px", borderTop: "2px dashed #38bdf8", display: "inline-block" }} />
            <span>Baseline Reference ({(baselineLatency / 1000).toFixed(2)}s)</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "#ff7a21" }}>
            <span style={{ width: "10px", height: "10px", borderRadius: "50%", background: "#ff7a21", display: "inline-block" }} />
            <span>Observed Response</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "#ef4444" }}>
            <span style={{ width: "10px", height: "10px", borderRadius: "50%", background: "#ef4444", border: "1px solid #fff", display: "inline-block" }} />
            <span>Adversarial Spike / Flag</span>
          </div>
        </div>
      </div>

      <svg viewBox={`0 0 ${width} ${height}`} style={{ width: "100%", height: "auto" }}>
        {[0, 0.5, 1].map(fraction => {
          const val = maximum * fraction;
          const yPos = y(val);
          return (
            <g key={fraction}>
              <line x1={left} x2={width - 20} y1={yPos} y2={yPos} stroke="#262626" strokeDasharray="3 4" />
              <text x={left - 10} y={yPos + 4} textAnchor="end" fill="#666" fontSize="11" fontFamily="monospace">
                {(val / 1000).toFixed(1)}s
              </text>
            </g>
          );
        })}

        <line 
          x1={left} 
          x2={width - 20} 
          y1={baselineY} 
          y2={baselineY} 
          stroke="#38bdf8" 
          strokeWidth="1.5" 
          strokeDasharray="5 5" 
        />
        <text x={width - 25} y={baselineY - 6} textAnchor="end" fill="#38bdf8" fontSize="10" fontFamily="sans-serif">
          Baseline Mean Reference
        </text>

        <path d={path} fill="none" stroke="#ff7a21" strokeWidth="2" />

        {validCases.map((item, index) => {
          const val = item.latency_ms!;
          const xPos = x(index);
          const yPos = y(val);
          const hasFlag = item.observed_detector_signals && item.observed_detector_signals.length > 0;
          const driftPct = ((val - baselineLatency) / baselineLatency) * 100;
          const isSignificantDrift = Math.abs(driftPct) > 40;

          return (
            <g key={index}>
              <circle
                cx={xPos}
                cy={yPos}
                r={hasFlag ? "5.5" : "4"}
                fill={hasFlag ? "#ef4444" : "#ff7a21"}
                stroke={hasFlag ? "#ffffff" : "none"}
                strokeWidth={hasFlag ? "1.5" : "0"}
              >
                <title>
                  Case #{index + 1}: {(val / 1000).toFixed(2)}s ({driftPct >= 0 ? `+${driftPct.toFixed(0)}%` : `${driftPct.toFixed(0)}%`} drift)
                </title>
              </circle>

              {isSignificantDrift && validCases.length <= 25 && (
                <text
                  x={xPos}
                  y={yPos - 9}
                  textAnchor="middle"
                  fill={driftPct > 0 ? "#f87171" : "#38bdf8"}
                  fontSize="9.5"
                  fontWeight="600"
                  fontFamily="monospace"
                >
                  {driftPct > 0 ? `+${driftPct.toFixed(0)}%` : `${driftPct.toFixed(0)}%`}
                </text>
              )}

              {validCases.length <= 15 && (
                <text x={xPos} y={bottom + 20} textAnchor="middle" fill="#888" fontSize="11" fontFamily="monospace">
                  #{index + 1}
                </text>
              )}
            </g>
          );
        })}

        {validCases.length > 15 && [0, 0.25, 0.5, 0.75, 1].map(fraction => {
          const idx = Math.round(fraction * (validCases.length - 1));
          return (
            <text key={fraction} x={x(idx)} y={bottom + 20} textAnchor="middle" fill="#888" fontSize="11" fontFamily="monospace">
              #{idx + 1}
            </text>
          );
        })}
      </svg>

      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.78rem", color: "#777", marginTop: "12px", borderTop: "1px solid #1f1f1f", paddingTop: "8px" }}>
        <span>Horizontal: Chronological test prompt sequence</span>
        <span>Vertical: Latency in seconds (drift relative to baseline)</span>
      </div>
    </article>
  );
}
