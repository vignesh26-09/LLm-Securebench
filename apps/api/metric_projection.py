"""Small, allowlisted report projections; never manufacture aggregate scores."""
import math


def measurements(family, payload, *, units="source units"):
    result = []

    def add(label, value, unit="source units"):
        if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value):
            result.append({"label": label, "value": value, "unit": unit})

    components = payload.get("components", {})
    if isinstance(components, dict):
        for key, component in components.items():
            if isinstance(component, dict):
                if not component.get("unmeasurable", False):
                    add(key.replace("_", " ") + " raw distance", component.get("raw_distance"), "distance")
            else:
                add(key.replace("_", " "), component, "ratio")
    if family == "rc":
        add("Initial attack deviation", payload.get("delta_a"), "distance")
        for step, distance in payload.get("recovery_deltas", []):
            add(f"Recovery step {step} deviation", distance, "distance")
        for key in ("rc_auc_raw", "terminal_recovery_raw", "rc_auc_bounded", "terminal_recovery_bounded"):
            add(key.replace("_", " "), payload.get(key), "recovery ratio")
    elif family == "saea":
        add("Sequence mean deviation", (payload.get("trajectory") or {}).get("cumulative_vulnerability"), "distance")
        for index, step in enumerate(payload.get("per_step", [])):
            if isinstance(step, dict):
                add(f"Step {index + 1} context effect", step.get("context_effect"), "distance difference")
    elif family == "draa":
        add("Evidence features", len(payload["features"]) if isinstance(payload.get("features"), list) else payload.get("feature_count"), "count")
    elif family == "pri":
        add("Profile observations", len(payload["cells"]) if isinstance(payload.get("cells"), list) else None, "count")
        coverage = payload.get("coverage") or payload
        for key in ("requested_categories", "observed_categories"):
            value = coverage.get(key)
            add(key.replace("_", " "), len(value) if isinstance(value, list) else value, "count")
    elif family == "statistics":
        for key, value in (payload.get("values") or {}).items():
            add(key.replace("_", " "), value, f"{units} squared" if key == "sample_variance" else units)
        add("Valid observations", payload.get("n_valid"), "count")
    # ML can be blocked, or can contain held-out metrics. No fixture metric is a safety rating.
    elif family == "ml":
        for model, metrics in (payload.get("metrics") or {}).items():
            if isinstance(metrics, dict):
                for name, item in metrics.items():
                    add(f"{model}: {name}".replace("_", " "), item.get("value") if isinstance(item, dict) else item)
    return result


def project_profiles(session, owners, evaluation_ids):
    """Stream large runs; average each source-native field, never mixed metrics."""
    from collections import Counter, defaultdict
    from sqlalchemy import select
    from core.persistence.models import ScientificRecordEntity

    families = ("bsda", "rc", "saea", "draa", "pri", "dqi", "ml", "statistics")
    counts = Counter()
    statuses = defaultdict(Counter)
    latest, aggregates = {}, defaultdict(dict)
    case_owners = defaultdict(set)
    evaluation_ids = set(evaluation_ids)
    rows = session.scalars(select(ScientificRecordEntity).where(
        ScientificRecordEntity.owner_id.in_(owners),
        ScientificRecordEntity.family.in_((*families, "recovery")),
    ).order_by(ScientificRecordEntity.created_at.desc(), ScientificRecordEntity.id.desc()).execution_options(yield_per=200))
    for row in rows:
        family = "rc" if row.family == "recovery" else row.family
        counts[family] += 1
        statuses[family][row.status or "unspecified"] += 1
        latest.setdefault(family, row)
        if row.owner_id in evaluation_ids:
            case_owners[family].add(row.owner_id)
        for item in measurements(family, row.payload, units=str(row.provenance.get("units", "source units"))):
            key = (item["label"], item["unit"])
            amount, n = aggregates[family].get(key, (0., 0))
            aggregates[family][key] = (amount + item["value"], n + 1)
    result = []
    for family in families:
        row = latest.get(family)
        payload = row.payload if row else {}
        score = payload.get("score") if family == "dqi" else None
        if isinstance(score, bool) or not isinstance(score, (int, float)):
            score = None
        components = payload.get("components") or {}
        components = {key: value for key, value in components.items()
                      if value is None or isinstance(value, (int, float)) and not isinstance(value, bool)}
        note = payload.get("reason")
        if family == "dqi" and row and row.provenance.get("embeddings_supplied") is False:
            note = "Legacy dataset diagnostic: novelty used an implementation default, not supplied embeddings."
        if family in {"saea", "rc"} and row and row.provenance.get("protocol"):
            note = (str(note).replace("_", " ") + ". " if note else "") + "Automated judge measurements are exploratory, not independently validated."
        result.append({"family": family, "record_count": counts[family],
            "status": "mixed_statuses" if len(statuses[family]) > 1 else row.status if row else "not_measured",
            "status_counts": dict(statuses[family]), "measured_case_count": len(case_owners[family]),
            "value": score, "components": components,
            "measurement_scope": "mean_of_available_records",
            "measurements": [{"label": label, "unit": unit, "value": amount / n, "sample_count": n}
                for (label, unit), (amount, n) in aggregates[family].items()], "note": note})
    return result
