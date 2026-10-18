import { Link } from "react-router-dom";
import type { ModelScore } from "../../api/types";

function pct(value: number | null | undefined) {
  return typeof value === "number" ? `${(value * 100).toFixed(1)}%` : "not computed";
}

export function ModelScoreboard({ scores }: { scores: ModelScore[] }) {
  if (!scores.length) {
    return <p className="empty">No completed model scores yet. Run an installed model from the Models page.</p>;
  }
  return <div className="scoreboard">
    {scores.map(score => <article key={score.id} className="score-card">
      <div>
        <span className="eyebrow">{score.status} · {score.formula_version}</span>
        <h2>{score.model_name}</h2>
        <p>Run <Link to={`/results/${encodeURIComponent(score.run_id)}`}>{score.run_id}</Link></p>
        <small className="tested-at">Tested {new Date(score.created_at).toLocaleString()}</small>
      </div>
      <div className="score-meter" aria-label={`Model score ${pct(score.model_score)}`}>
        <strong>{pct(score.model_score)}</strong>
        <span>detector summary</span>
        <div><i style={{ width: pct(score.model_score).replace("not computed", "0%") }} /></div>
      </div>
      <dl>
        <div><dt>Mean threat</dt><dd>{pct(score.mean_threat_score)}</dd></div>
        <div><dt>Worst case</dt><dd>{pct(score.worst_case_threat_score)}</dd></div>
        <div><dt>Coverage</dt><dd>{score.completed_evaluations}/{score.total_evaluations} ({pct(score.coverage)})</dd></div>
      </dl>
      <p className="muted"><strong>Selection:</strong> evidence review required. This engineering summary cannot decide whether a model is safe to choose.</p>
      <details><summary>Formula and provenance</summary><pre>{JSON.stringify({ formula: score.formula, warnings: score.warnings, provenance: score.provenance }, null, 2)}</pre></details>
    </article>)}
  </div>;
}
