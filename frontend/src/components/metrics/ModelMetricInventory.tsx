import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import type { BenchmarkRunReport } from "../../api/types";
import { apiClient } from "../../api/client";
import { MetricWorkbench } from "./MetricWorkbench";

const families = [
  ["bsda", "BSDA", "Behavior changes", "How much did meaning, safety, instructions, or answer format change after an attack? Raw distances stay separate; no validated total exists.", "Needs matched baseline and attacked answers"],
  ["rc", "RC", "Recovery after an attack", "Did the model return toward normal behavior? Recovery ratios need matched states and calibration; they are not safety probabilities.", "Needs recovery observations and calibration"],
  ["saea", "SAEA", "Repeated attack effects", "Do repeated attacks differ from isolated attacks? Positive context effects mean more deviation in the sequence; negative effects mean less.", "Needs sequential and isolated controls"],
  ["draa", "DRAA", "Risk evidence", "Collects observations for risk analysis. Feature counts describe evidence volume, not how dangerous the model is.", "Evidence profile; no scalar risk score"],
  ["pri", "PRI", "Prompt robustness", "Shows which prompts and categories were observed. More observations mean more coverage, not necessarily better robustness.", "Evidence profile; no overall robustness score"],
  ["dqi", "DQI", "Dataset quality", "Describes test-data coverage, duplication, and semantic novelty. This describes the dataset, not model safety.", "Needs a dataset and semantic embeddings"],
  ["ml", "ML", "Risk prediction", "Tests a predictor against held-out labels. Fixture performance is engineering evidence; real use needs independent labels and validation.", "Needs labels, features, and a held-out split"],
  ["statistics", "STAT", "Response-time statistics", "Summarizes observed answer times. Lower times mean faster responses; they say nothing about answer quality or safety.", "Needs numeric observations"],
] as const;
const metricPages: Record<string, string> = { bsda: "/metrics/bsda", rc: "/metrics/recovery", saea: "/metrics/saea", draa: "/metrics/draa", pri: "/metrics/pri", dqi: "/metrics/dqi", ml: "/ml", statistics: "/statistics" };

export function ModelMetricInventory({ report }: { report: BenchmarkRunReport }) {
  const [selected, setSelected] = useState<string[]>(families.map(item => item[0]));
  const catalog = useQuery({ queryKey: ["metric-catalog"], queryFn: apiClient.metricCatalog, retry: false });
  const profileFor = (family: string) => report.metric_profiles?.find(item => item.family === family);
  const recorded = families.filter(([family]) => (profileFor(family)?.record_count ?? 0) > 0).length;
  const toggle = (family: string) => setSelected(current => current.includes(family) ? current.filter(item => item !== family) : [...current, family]);
  return <section className="model-metric-inventory">
    <div className="studio-section-heading"><div><span className="studio-eyebrow">EVERY METRIC / THIS RUN ONLY</span><h2>Your complete metric dashboard</h2><p>Eight metric engines. Separate measurements, clear explanations, no invented scores.</p></div></div>
    <div className="metric-observatory">
      <div className="metric-galaxy"><svg viewBox="0 0 440 280" role="img" aria-label={`${recorded} of eight metric families have linked records. Filled stars indicate records, not safety.`}>
        {[0, 1, 2].map(arm => <path key={arm} d="M220 140 C260 60 365 90 365 170 C365 260 100 275 65 140" transform={`rotate(${arm * 120} 220 140)`} />)}
        <circle className="galaxy-core" cx="220" cy="140" r="28" /><text x="220" y="145" textAnchor="middle">{recorded}/8</text>
        {families.map(([family, code], index) => {
          const angle = index * Math.PI / 4 - Math.PI / 2;
          const x = 220 + Math.cos(angle) * 145; const y = 140 + Math.sin(angle) * 100;
          return <g key={family}><circle className={profileFor(family)?.record_count ? "galaxy-recorded" : "galaxy-missing"} cx={x} cy={y} r="6" /><text x={x} y={y + 23} textAnchor="middle">{code}</text></g>;
        })}
      </svg></div>
      <div><span className="studio-eyebrow">EVIDENCE MAP</span><h3>{recorded} of 8 families have linked records</h3><p>Each star is a metric family. A filled star means this run has a saved record—even if that record says blocked or uncalibrated. It does not mean the model passed.</p><p className="tiny-note">Hollow star = no linked record. Unrelated model records are never included.</p><strong className="engine-status">{catalog.data?.items ? `${catalog.data.items.length} compute endpoints available` : "Sign in to check compute access"}</strong></div>
    </div>
    <div className="metric-toolbar" role="group" aria-label="Choose metric cards"><span>{selected.length} metrics selected</span><button type="button" onClick={() => setSelected(families.map(item => item[0]))}>Select all</button><button type="button" onClick={() => setSelected(families.filter(([family]) => profileFor(family)?.record_count).map(item => item[0]))}>With records</button><button type="button" onClick={() => setSelected([])}>Clear</button></div>
    <div className="metric-file-tiles">{families.map(([family, code, title]) => <button type="button" key={family} aria-pressed={selected.includes(family)} onClick={() => toggle(family)}><span className="tile-check">{selected.includes(family) ? "✓" : "+"}</span><span>{code}<small>{title}</small></span><span className="tile-count">{profileFor(family)?.record_count ?? 0} records</span></button>)}</div>
    {selected.length === 0 && <p className="empty">Choose a tile to show its metric details.</p>}
    <p className="tiny-note">Each measurement is the mean of its available linked records, with its own sample count—not a combined safety score. Missing or failed values are excluded, never replaced by zero. Dataset measurements describe the test dataset.</p>
    <div className="model-metric-cards">{families.filter(([family]) => selected.includes(family)).map(([family, code, title, description, missing]) => {
      const profile = profileFor(family);
      const timing = family === "statistics" && report.execution.mean_latency_ms != null;
      const measurements = profile?.measurements ?? Object.entries(profile?.components ?? {}).filter(([, value]) => value != null).map(([label, value]) => ({ label, value: value!, unit: "source units", sample_count: undefined }));
      return <article key={family}>
        <div className="inventory-card-heading"><span className="metric-code">{code}</span><span className="readiness-tag">{profile?.status?.replaceAll("_", " ") ?? "not measured"}</span></div>
        <h3>{title}</h3><strong className="inventory-value">{timing ? `${(report.execution.mean_latency_ms! / 1000).toFixed(2)}s` : typeof profile?.value === "number" ? `${(profile.value * 100).toFixed(1)}%` : measurements.length ? `${measurements.length} measurement${measurements.length === 1 ? "" : "s"}` : profile?.record_count ? "Record available" : "Not measured"}</strong>
        <p>{description}</p>
        {profile?.status_counts && <p className="tiny-note">{Object.entries(profile.status_counts).map(([status, n]) => `${n.toLocaleString()} ${status.replaceAll("_", " ")}`).join(" · ")}</p>}
        {measurements.length > 0 && <dl className="inventory-components">{measurements.map(item => <div key={item.label}><dt>{item.label.replaceAll("_", " ")}</dt><dd>{Number(item.value.toFixed(4))}<small> {item.unit}{item.sample_count != null ? ` · n=${item.sample_count.toLocaleString()}` : ""}</small></dd></div>)}</dl>}
        {profile?.note && <p className="tiny-note">{profile.note}</p>}
        <div className="inventory-card-note">{timing ? "Average seconds per answer; saved statistics retain their original source units" : missing} · {profile?.record_count ?? 0} linked records{profile?.measured_case_count ? ` · ${profile.measured_case_count.toLocaleString()} cases represented` : ""}</div>
        <Link to={metricPages[family]}>Open metric page and calculator →</Link>
      </article>;
    })}</div>
    <MetricWorkbench />
    <p className="tiny-note">Attack success rate is not inferred from detector matches. Independently validated outcome labels are required.</p>
  </section>;
}
