import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import * as echarts from "echarts";
import { ChartContainer } from "../charts/ChartContainer";
import { ErrorState, LoadingState } from "../common/AsyncState";
import { ProvenanceBadge } from "../common/ProvenanceBadge";
import { StatusBadge } from "../common/StatusBadge";
import { CalibrationDetails, type Calibration } from "./CalibrationDetails";

type Series = { name: string; unit: string; kind: "bar" | "line"; points: { label: string; value: number | null; reason: string | null }[] };
type Evidence = { id: string; family: string; status: string; schema_version: string; scope: string; series: Series[]; unavailable: string[]; provenance: Record<string, unknown> };
type EvidencePage = { metric: string; records: Evidence[]; total: number; limit: number; offset: number; evidence_needed: string; calibration?: Calibration };

function MeasurementChart({ series }: { series: Series }) {
  const host = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!host.current) return;
    const chart = echarts.init(host.current);
    chart.setOption({
      textStyle: { color: "#d6d6d6" },
      tooltip: { trigger: "axis", valueFormatter: (value: unknown) => value == null ? "Unavailable" : `${String(value)} ${series.unit}` },
      grid: { left: 20, right: 24, top: 24, bottom: 24, containLabel: true },
      xAxis: { type: "category", data: series.points.map(point => point.label), axisLabel: { rotate: 25, hideOverlap: true } },
      yAxis: { type: "value", name: series.unit, nameLocation: "middle", nameGap: 55, splitLine: { lineStyle: { color: "#343434" } } },
      series: [{ type: series.kind, data: series.points.map(point => point.value), connectNulls: false, itemStyle: { color: "#ff7a21" } }],
    });
    const resize = () => chart.resize();
    window.addEventListener("resize", resize);
    const observer = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(resize);
    if (host.current) observer?.observe(host.current);
    return () => { observer?.disconnect(); window.removeEventListener("resize", resize); chart.dispose(); };
  }, [series]);
  return <ChartContainer><div className="chart" ref={host} role="img" aria-label={`${series.name}; ${series.unit}; missing points remain unavailable`} /></ChartContainer>;
}

export function StoredMetricEvidence({ metric }: { metric: string }) {
  const [offset, setOffset] = useState(0);
  const [identity, setIdentity] = useState("");
  const family = metric === "recovery" ? "rc" : metric;
  const query = useQuery<EvidencePage>({
    queryKey: ["scientific-records", family, "stored-metric-evidence", offset], retry: false,
    queryFn: async () => {
      const response = await fetch(`${import.meta.env.VITE_SECURELLM_API_BASE_URL ?? ""}/metrics/compute/${metric}/evidence?limit=25&offset=${offset}`, { credentials: "include", headers: { Accept: "application/json" } });
      if (!response.ok) throw new Error(`Stored metric evidence request failed: HTTP ${response.status}`);
      const data = await response.clone().json() as EvidencePage;
      if (!Array.isArray(data.records) || typeof data.total !== "number" || typeof data.evidence_needed !== "string") throw new Error("Stored evidence API returned an invalid contract");
      return data;
    },
  });
  const record = query.data?.records.find(item => item.id === identity) ?? query.data?.records[0];
  function move(next: number) { setIdentity(""); setOffset(next); }
  return <><CalibrationDetails calibration={query.data?.calibration} loading={query.isLoading} error={query.isError} /><section className="research-note" aria-label="Stored metric measurements">
    <h2>Stored metric measurements</h2>
    <p>Source-native values from one saved record at a time; no cross-run averaging, new estimator, or scientific calibration is inferred.</p>
    {query.isLoading && <LoadingState />}
    {query.isError && <><ErrorState error={query.error} /><p role="alert">Unavailable: stored measurements could not be loaded; needs a successful evidence API response.</p></>}
    {query.data && <>
      {!query.data.records.length && <p role="status">Unavailable: needs {query.data.evidence_needed}. No measurements are substituted.</p>}
      {record && <>
        <label>Saved evidence record<select value={record.id} onChange={event => setIdentity(event.target.value)}>{query.data.records.map(item => <option key={item.id} value={item.id}>{item.id} · {item.status}</option>)}</select></label>
        <p>Source record: <code>{record.id}</code> · {record.family} · schema {record.schema_version} · {record.scope}</p>
        <StatusBadge status={record.status} /><ProvenanceBadge value={record.provenance} />
        {record.unavailable.map(reason => <p key={reason}>Unavailable: {reason}</p>)}
        {record.series.map((series, index) => <article key={`${series.name}:${index}`}>
          <h3>{series.name}</h3><p>Units: {series.unit}. Source: <code>{record.id}</code>.</p>
          {series.points.some(point => point.value !== null) ? <MeasurementChart series={series} /> : <p>No finite measured values for this chart; the missing evidence is listed below.</p>}
          <div className="table-wrap"><table><caption>{series.name} source values</caption><thead><tr><th>Measurement</th><th>Value</th><th>Units</th><th>Missing-evidence reason</th></tr></thead><tbody>{series.points.map((point, pointIndex) => <tr key={`${point.label}:${pointIndex}`}><td>{point.label}</td><td>{point.value === null ? "Unavailable" : String(point.value)}</td><td>{series.unit}</td><td>{point.reason ?? "Measured source value"}</td></tr>)}</tbody></table></div>
        </article>)}
      </>}
      <nav className="pagination" aria-label="Stored metric evidence pagination"><button type="button" disabled={!offset} onClick={() => move(Math.max(0, offset - query.data!.limit))}>Previous evidence</button><span>{query.data.total ? offset + 1 : 0}–{Math.min(offset + query.data.limit, query.data.total)} of {query.data.total} records</span><button type="button" disabled={offset + query.data.limit >= query.data.total} onClick={() => move(offset + query.data!.limit)}>Next evidence</button></nav>
    </>}
  </section></>;
}
