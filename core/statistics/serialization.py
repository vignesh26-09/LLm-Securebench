"""Deterministic JSON serialization for statistical planning metadata."""
import json, hashlib
from dataclasses import asdict,is_dataclass
from enum import Enum
from core.statistics.models import *
def dumps(value): return json.dumps(_ready(value),sort_keys=True,separators=(",",":"))
def schema_hash(value): return hashlib.sha256(dumps(value).encode()).hexdigest()
def loads_plan(payload):
 d=json.loads(payload); d["hypotheses"]=tuple(HypothesisDefinition(**{**x,"analysis_mode":AnalysisMode(x["analysis_mode"]),"scientific_status":ScientificStatus(x["scientific_status"])}) for x in d["hypotheses"]); d["estimands"]=tuple(EstimandDefinition(**x) for x in d["estimands"]); d["units"]=AnalysisUnitDefinition(**d["units"]); d["grouping"]=GroupingDefinition(**{**d["grouping"],"purpose":GroupingPurpose(d["grouping"]["purpose"]),"grouping_keys":tuple(d["grouping"]["grouping_keys"]),"hierarchy_order":tuple(d["grouping"].get("hierarchy_order",())),"assumptions":tuple(d["grouping"].get("assumptions",()))}) if d["grouping"] else None; d["pairing"]=PairingDefinition(**{**d["pairing"],"status":PairingStatus(d["pairing"]["status"]),"pairing_keys":tuple(d["pairing"].get("pairing_keys",())),"condition_labels":tuple(d["pairing"].get("condition_labels",()))}) if d["pairing"] else None; d["resampling"]=ResamplingPlan(**{**d["resampling"],"method":ResamplingMethod(d["resampling"]["method"]),"grouping_hierarchy":tuple(d["resampling"].get("grouping_hierarchy",())),"assumptions":tuple(d["resampling"].get("assumptions",()))}); d["multiplicity"]=MultiplicityPlan(**{**d["multiplicity"],"method":MultiplicityMethod(d["multiplicity"]["method"]),"scope":AnalysisMode(d["multiplicity"]["scope"])}); d["effect_size"]=EffectSizePlan(**d["effect_size"]); d["missingness"]=MissingnessPlan(**d["missingness"]); d["assumptions"]=tuple(AssumptionRecord(**{**x,"status":AssumptionStatus(x["status"])}) for x in d["assumptions"]); d["preregistration"]=PreregistrationMetadata(**{**d["preregistration"],"status":RegistrationStatus(d["preregistration"]["status"]),"frozen_fields":tuple(d["preregistration"].get("frozen_fields",())),"amendment_history":tuple(d["preregistration"].get("amendment_history",())),"exploratory_deviations":tuple(d["preregistration"].get("exploratory_deviations",()))}); d["readiness"]=ReadinessStates(**d["readiness"]); d["scientific_status"]=ScientificStatus(d["scientific_status"]); d["components"]=tuple(d["components"]); d["inclusion_rules"]=tuple(d.get("inclusion_rules",())); d["exclusion_rules"]=tuple(d.get("exclusion_rules",())); return StatisticalAnalysisPlan(**d)
def _ready(v):
 if isinstance(v,Enum): return v.value
 if is_dataclass(v): return _ready(asdict(v))
 if isinstance(v,dict): return {str(k):_ready(x) for k,x in v.items()}
 if isinstance(v,(tuple,list)): return [_ready(x) for x in v]
 return v
