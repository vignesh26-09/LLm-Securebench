"""Contract validation only; it does not assess data or compute inference."""
from dataclasses import dataclass
from core.statistics.models import *
from core.statistics.registry import METHOD_REGISTRY
@dataclass(frozen=True, slots=True)
class PlanValidation: valid:bool; errors:tuple[str,...]=(); warnings:tuple[str,...]=()
def validate_plan(plan:StatisticalAnalysisPlan)->PlanValidation:
    errors=[]; warnings=[]; estimands={item.estimand_id for item in plan.estimands}
    if not plan.hypotheses or not plan.estimands: errors.append("hypotheses_and_estimands_required_for_plan_ready")
    if plan.method_id not in METHOD_REGISTRY: errors.append("method_not_in_registry")
    if plan.readiness.plan_ready and errors: errors.append("plan_ready_contract_incomplete")
    if plan.pairing and plan.pairing.status is PairingStatus.PAIRED and not plan.pairing.pairing_keys: errors.append("paired_plan_requires_pairing_keys")
    if plan.resampling.method in {ResamplingMethod.GROUPED_BOOTSTRAP,ResamplingMethod.HIERARCHICAL_BOOTSTRAP} and not plan.resampling.grouping_hierarchy: errors.append("grouped_resampling_requires_grouping")
    if plan.resampling.method is ResamplingMethod.PAIRED_BOOTSTRAP and not plan.resampling.pairing_id: errors.append("paired_bootstrap_requires_pairing")
    if plan.multiplicity.method is not MultiplicityMethod.NONE and not plan.multiplicity.hypothesis_family_id: errors.append("multiplicity_method_requires_family")
    for h in plan.hypotheses:
        ref=h.provenance.get("estimand_id")
        if ref is not None and ref not in estimands: errors.append("hypothesis_references_unknown_estimand")
    _component_guards(plan,errors,warnings)
    return PlanValidation(not errors,tuple(sorted(set(errors))),tuple(sorted(set(warnings))))
def _component_guards(plan,errors,warnings):
    p=plan.provenance; component=" ".join(plan.components).lower(); target=str(p.get("validation_target",""))
    if "bsda" in component and ("composite" in target): errors.append("bsda_composite_validation_blocked")
    if "rc" in component and p.get("degradation_threshold") is not None and not p.get("calibration_artifact_id"): errors.append("rc_threshold_requires_calibration_provenance")
    if "saea" in component and "hazard" in target: errors.append("saea_hazard_not_approved")
    if "saea" in component and p.get("shapley_interpretation")=="causal": errors.append("shapley_causal_interpretation_blocked")
    if "draa" in component and ("risk" in target or p.get("uses_risk_score")): errors.append("draa_mode_a_b_risk_validation_blocked")
    if "pri" in component and ("scalar" in target or "rank" in target): errors.append("pri_scalar_or_ranking_validation_blocked")
    if "ml" in component and p.get("synthetic_fixture") and p.get("scientific_prediction_claim"): errors.append("synthetic_ml_claim_validation_blocked")
    if "layer2" in component and p.get("reference_label_source")=="same_judge": errors.append("judge_derived_reference_blocked")
    if "dqi" in component and p.get("target_derived_from_dqi"): warnings.append("dqi_circular_validation_flagged")
