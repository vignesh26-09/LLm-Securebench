import type { BenchmarkRunReport } from "../../api/types";

export function ResponseTimePlot({ cases }: { cases: BenchmarkRunReport["cases"] }) {
  const maximum = Math.max(1, ...cases.map(item => item.latency_ms ?? 0));
  const width = 700, height = 200, left = 50, top = 20, bottom = 165;
  const x = (index: number) => left + index * (width - left - 20) / Math.max(1, cases.length - 1);
  const y = (value: number) => bottom - value / maximum * (bottom - top);
  return <article className="studio-panel response-plot"><span className="studio-eyebrow">RESPONSE SPEED</span><h2>How long did each answer take?</h2><p>Each dot is one test case. Lower dots mean faster answers. Missing times are left blank.</p><svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Response time in seconds for each test case">
    {[0, .5, 1].map(fraction => <g key={fraction}><line x1={left} x2={width - 20} y1={y(maximum * fraction)} y2={y(maximum * fraction)} stroke="#333333" strokeDasharray="3 5" /><text x={left - 10} y={y(maximum * fraction) + 4} textAnchor="end" fill="#aaaaaa" fontSize="11">{(maximum * fraction / 1000).toFixed(1)}s</text></g>)}
    {cases.map((item, index) => item.latency_ms == null ? null : <g key={item.id}>{index > 0 && cases[index - 1].latency_ms != null && <line x1={x(index - 1)} x2={x(index)} y1={y(cases[index - 1].latency_ms!)} y2={y(item.latency_ms)} stroke="#ff7a21" strokeWidth="2" />}<circle cx={x(index)} cy={y(item.latency_ms)} r="3.5" fill="#ff7a21"><title>{item.case_id ?? item.id}: {(item.latency_ms / 1000).toFixed(2)} seconds</title></circle>{cases.length <= 15 && <text x={x(index)} y={190} textAnchor="middle" fill="#aaaaaa" fontSize="11">{index + 1}</text>}</g>)}
  </svg><small>Horizontal axis: test case order · Vertical axis: seconds per answer</small></article>;
}
