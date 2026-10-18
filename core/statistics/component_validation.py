"""Phase 10D metadata guards; no experiment execution or validation verdict."""
from dataclasses import dataclass,field
from enum import StrEnum
from typing import Mapping
class ValidationMode(StrEnum): SYNTHETIC_SANITY="synthetic_sanity"; PILOT="pilot"; PREREGISTERED_CONFIRMATORY="preregistered_confirmatory"; REPLICATION_GENERALIZATION="replication_generalization"
class ValidationGate(StrEnum): PLAN_GATE="plan_gate"; DATA_GATE="data_gate"; ANALYSIS_GATE="analysis_gate"; REPLICATION_GATE="replication_gate"; CLAIM_REVIEW_GATE="claim_review_gate"
@dataclass(frozen=True,slots=True)
class ExperimentMatrixRow:
 experiment_id:str;component:str;scientific_question:str;claim_type:str;primary_estimand:str;secondary_estimand:str|None;experimental_unit:str|None;sampling_unit:str|None;pairing:Mapping[str,object];grouping:Mapping[str,object];conditions:Mapping[str,object];controls:Mapping[str,object];independent_variables:tuple[str,...];dependent_variables:tuple[str,...];covariates:tuple[str,...]=();candidate_analysis:str|None=None;effect_measure:str|None=None;uncertainty_method:str|None=None;multiplicity_family:str|None=None;missingness_plan:str|None=None;sensitivity_analysis:tuple[str,...]=();generalization_plan:str|None=None;evidence_required:tuple[str,...]=();readiness_blockers:tuple[str,...]=()
@dataclass(frozen=True,slots=True)
class ComponentValidationPlan:
 plan_id:str;component:str;mode:ValidationMode;matrix_row:ExperimentMatrixRow;gates:Mapping[ValidationGate,bool];provenance:Mapping[str,object]=field(default_factory=dict)
 def __post_init__(self):
  if self.component=="bsda" and self.provenance.get("validation_target")=="composite":raise ValueError("bsda composite validation blocked")
  if self.component=="rc" and self.provenance.get("degradation_threshold") is not None and not self.provenance.get("calibration_artifact_id"):raise ValueError("rc threshold requires calibration provenance")
  if self.component=="draa" and self.provenance.get("risk_validation"):raise ValueError("draa Mode A/B risk validation blocked")
  if self.component=="pri" and self.provenance.get("scalar_or_ranking"):raise ValueError("pri scalar/ranking validation blocked")
  if self.component=="ml" and self.provenance.get("synthetic_fixture") and self.provenance.get("scientific_claim"):raise ValueError("synthetic ML claim blocked")
  if self.component=="layer2" and self.provenance.get("reference_source")=="same_judge":raise ValueError("judge-derived reference blocked")
@dataclass(frozen=True,slots=True)
class ScientificReviewRecord:
 review_id:str;claim_id:str;evidence_bundle_id:str;reviewer_protocol:str;decision:str;rationale:str;timestamp:str|None=None;provenance:Mapping[str,object]=field(default_factory=dict)
