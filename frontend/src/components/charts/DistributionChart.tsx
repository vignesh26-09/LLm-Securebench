import { useEffect, useRef } from "react";
import * as echarts from "echarts";
import { ChartContainer } from "./ChartContainer";

export function DistributionChart({ values, title }: { values: number[]; title: string }) {
  const host = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!host.current || values.length === 0) return undefined;
    const chart = echarts.init(host.current);
    chart.setOption({ title: { text: title }, xAxis: { type: "category", data: values.map((_, index) => String(index + 1)) }, yAxis: { type: "value" }, series: [{ type: "bar", data: values }] });
    const resize = () => chart.resize(); window.addEventListener("resize", resize);
    return () => { window.removeEventListener("resize", resize); chart.dispose(); };
  }, [title, values]);
  if (values.length === 0) return <p className="empty">No numeric values were supplied by the backend.</p>;
  return <ChartContainer><div className="chart" ref={host} aria-label={title} /></ChartContainer>;
}
