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
        for key in ("rc_auc_raw", "terminal_recovery_raw", "rc_auc_bounded", "terminal_recovery_bounded"):
            add(key.replace("_", " "), payload.get(key), "recovery ratio")
    elif family == "saea":
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
