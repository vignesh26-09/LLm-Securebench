import { useEffect, useMemo, useRef } from "react";
import * as echarts from "echarts";
import type { ModelScore } from "../../api/types";

export function BenchmarkTrendChart({ scores }: { scores: ModelScore[] }) {
  const host = useRef<HTMLDivElement>(null);
  const points = useMemo(() => scores
    .filter((score) => score.formula_version === "engineering-detector-score-v1" && score.model_score !== null && Number.isFinite(score.model_score))
    .slice()
    .reverse(), [scores]);

  useEffect(() => {
    if (!host.current || points.length === 0) return undefined;
    const chart = echarts.init(host.current);
    chart.setOption({
      backgroundColor: "transparent",
      grid: { top: 42, right: 25, bottom: 64, left: 76 },
      tooltip: {
        trigger: "axis",
        formatter: (params: unknown) => {
          const entry = (params as Array<{ dataIndex: number }>)[0];
          const score = points[entry.dataIndex];
          return `${score.model_name}<br/>${new Date(score.created_at).toLocaleString()}<br/>Detector summary: ${(score.model_score! * 100).toFixed(1)}%<br/>${score.completed_evaluations}/${score.total_evaluations} cases`;
        },
      },
      xAxis: {
        type: "category",
        data: points.map((score) => new Date(score.created_at).toLocaleDateString()),
        axisLabel: { color: "#94aac1", rotate: points.length > 8 ? 35 : 0 },
        axisLine: { lineStyle: { color: "#50627b" } },
      },
      yAxis: {
        type: "value", min: 0, max: 100,
        nameTextStyle: { color: "#a4b8cf" },
        axisLabel: { color: "#94aac1", formatter: "{value}%" },
        splitLine: { lineStyle: { color: "rgba(149,184,224,.14)" } },
      },
      series: [{
        type: "line", smooth: false, showSymbol: true, symbol: "circle", symbolSize: 9,
        lineStyle: { width: 3, color: "#65cbb8" },
        itemStyle: { color: "#65cbb8", borderColor: "#e8fbf6", borderWidth: 2 },
        areaStyle: { color: "rgba(101,203,184,.08)" },
        data: points.map((score) => Number((score.model_score! * 100).toFixed(2))),
      }],
    });
    const resize = () => chart.resize();
    window.addEventListener("resize", resize);
    return () => { window.removeEventListener("resize", resize); chart.dispose(); };
  }, [points]);

  return <article className="visual-card benchmark-trend">
    <div className="card-heading"><div><span className="visual-label">Saved benchmark runs</span><h3>Detector summary over time</h3></div><span className="status status-uncalibrated">Engineering only</span></div>
    {points.length === 0 ? <p>No completed detector summaries are available to plot.</p> : <div className="benchmark-line-chart" ref={host} role="img" aria-label={`Line graph of ${points.length} saved benchmark detector summaries with a marked point for each run`} />}
    <p className="chart-note">Each marker is a completed repository-example run using detector formula v1. Other formula versions are excluded. Repeated model runs may use different cases or settings; this line is an activity trend, not a measured attack trajectory or safety ranking.</p>
  </article>;
}
