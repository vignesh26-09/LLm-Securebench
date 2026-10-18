"""Phase 10A immutable statistical-planning contracts; no inference is performed."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Mapping

class ScientificStatus(StrEnum):
    FORMALLY_DEFINED="formally_defined"; IMPLEMENTATION_DEFAULT="implementation_default"; CALIBRATION_DEPENDENT="calibration_dependent"; EMPIRICAL_HYPOTHESIS="empirical_hypothesis"; DIAGNOSTIC="diagnostic"; FUTURE_WORK="future_work"; BLOCKER="blocker"
class ReadinessFlag(StrEnum): YES="yes"; NO="no"
class AnalysisMode(StrEnum): CONFIRMATORY="confirmatory"; EXPLORATORY="exploratory"; DESCRIPTIVE="descriptive"; DIAGNOSTIC="diagnostic"
class PairingStatus(StrEnum): PAIRED="paired"; UNPAIRED="unpaired"; PARTIALLY_PAIRED="partially_paired"; UNKNOWN="unknown"
class GroupingPurpose(StrEnum): DESIGN="design"; PAIRING="pairing"; RESAMPLING="resampling"; MODEL_TERM="model_term"; SPLITTING="splitting"; DESCRIPTIVE_ONLY="descriptive_only"
class ResamplingMethod(StrEnum): NONE="none"; PAIRED_BOOTSTRAP="paired_bootstrap"; GROUPED_BOOTSTRAP="grouped_bootstrap"; HIERARCHICAL_BOOTSTRAP="hierarchical_bootstrap"; PERCENTILE_BOOTSTRAP="percentile_bootstrap"; BCA_BOOTSTRAP="bca_bootstrap"; PERMUTATION="permutation"; RANDOMIZATION="randomization"; CUSTOM="custom"
class MultiplicityMethod(StrEnum): NONE="none"; HOLM="holm"; BONFERRONI="bonferroni"; BENJAMINI_HOCHBERG="benjamini_hochberg"; HIERARCHICAL="hierarchical"; PREREGISTERED_PRIMARY="preregistered_primary"; CUSTOM="custom"
class AssumptionStatus(StrEnum): UNASSESSED="unassessed"; SATISFIED="satisfied"; VIOLATED="violated"; UNCERTAIN="uncertain"; NOT_APPLICABLE="not_applicable"
class ResultStatus(StrEnum): NOT_COMPUTED="not_computed"; COMPUTED="computed"; UNDEFINED="undefined"; INSUFFICIENT_DATA="insufficient_data"; INVALID_INPUT="invalid_input"; NOT_APPLICABLE="not_applicable"; NUMERICAL_FAILURE="numerical_failure"
class RegistrationStatus(StrEnum): DRAFT="draft"; FROZEN="frozen"; AMENDED="amended"; SUPERSEDED="superseded"

@dataclass(frozen=True, slots=True)
class ReadinessStates:
    engineering_ready: bool; plan_ready: bool; data_ready: bool; analysis_ready: bool; claim_validated: bool
    synthetic_fixture: bool=False; scientific_review_decision_id: str|None=None
    def __post_init__(self):
        if self.analysis_ready and not (self.plan_ready and self.data_ready): raise ValueError("analysis_ready requires plan_ready and data_ready")
        if self.claim_validated and (not self.analysis_ready or not self.scientific_review_decision_id or self.synthetic_fixture): raise ValueError("claim_validated requires analysis readiness and external review, never synthetic fixtures")

@dataclass(frozen=True, slots=True)
class HypothesisDefinition:
    hypothesis_id:str; component:str; research_question:str; claim_type:str; analysis_mode:AnalysisMode; scientific_status:ScientificStatus; target_population:str|None; claim_scope:str|None; null_hypothesis:str|None=None; alternative_hypothesis:str|None=None; provenance:Mapping[str,object]=field(default_factory=dict); version:str="v1"
@dataclass(frozen=True, slots=True)
class EstimandDefinition:
    estimand_id:str; name:str; description:str; target_quantity:str; scale_units:str|None; orientation:str|None; population:str|None; comparison:str|None; condition_definitions:Mapping[str,object]=field(default_factory=dict); effect_interpretation:str|None=None; scientific_role:str|None=None; provenance:Mapping[str,object]=field(default_factory=dict); version:str="v1"
@dataclass(frozen=True, slots=True)
class AnalysisUnitDefinition:
    experimental_unit:str|None=None; sampling_unit:str|None=None; observation_unit:str|None=None; resampling_unit:str|None=None; pairing_unit:str|None=None; parent_group_unit:str|None=None; hierarchy:Mapping[str,str|None]=field(default_factory=dict)
@dataclass(frozen=True, slots=True)
class GroupingDefinition:
    grouping_id:str; grouping_keys:tuple[str,...]; purpose:GroupingPurpose; hierarchy_order:tuple[str,...]=(); parent_child:Mapping[str,str]=field(default_factory=dict); repeated_measure_status:str="unknown"; structure:str="unknown"; assumptions:tuple[str,...]=(); provenance:Mapping[str,object]=field(default_factory=dict)
@dataclass(frozen=True, slots=True)
class PairingDefinition:
    pairing_id:str; status:PairingStatus; pairing_keys:tuple[str,...]=(); condition_labels:tuple[str,...]=(); rationale:str|None=None; completeness_requirement:str|None=None; unmatched_handling:str|None=None; provenance:Mapping[str,object]=field(default_factory=dict)
@dataclass(frozen=True, slots=True)
class ResamplingPlan:
    plan_id:str; method:ResamplingMethod; resampling_unit:str|None=None; grouping_hierarchy:tuple[str,...]=(); pairing_id:str|None=None; preserve_nested_structure:bool=False; confidence_level:float|None=None; resample_count:int|None=None; seed:int|None=None; interval_method:str|None=None; assumptions:tuple[str,...]=(); applicability_status:str="unassessed"; rationale:str|None=None; provenance:Mapping[str,object]=field(default_factory=dict)
    def __post_init__(self):
        if self.confidence_level is not None and not 0 < self.confidence_level < 1: raise ValueError("confidence level must be in (0,1)")
        if self.resample_count is not None and self.resample_count <= 0: raise ValueError("resample count must be positive")
@dataclass(frozen=True, slots=True)
class MultiplicityPlan:
    plan_id:str; hypothesis_family_id:str|None; family_description:str|None; method:MultiplicityMethod; error_rate_target:float|None=None; scope:AnalysisMode=AnalysisMode.EXPLORATORY; rationale:str|None=None; provenance:Mapping[str,object]=field(default_factory=dict)
@dataclass(frozen=True, slots=True)
class EffectSizePlan:
    plan_id:str; effect_family:str; raw_scale_effect:str|None=None; standardized_companion:str|None=None; interpretation:str|None=None; practical_significance_policy:str|None=None; threshold_or_margin:float|None=None; provenance:Mapping[str,object]=field(default_factory=dict)
@dataclass(frozen=True, slots=True)
class MissingnessPlan:
    plan_id:str; state_handling:Mapping[str,str]; inferential_hypothesis:str|None=None; provenance:Mapping[str,object]=field(default_factory=dict)
    def __post_init__(self):
        allowed={"exclude","retain","summarize","sensitivity_analysis","blocked","custom"}
        if any(value not in allowed for value in self.state_handling.values()): raise ValueError("invalid missingness handling")
@dataclass(frozen=True, slots=True)
class AssumptionRecord:
    assumption_id:str; method_family:str; assumption_name:str; description:str; required:bool; status:AssumptionStatus=AssumptionStatus.UNASSESSED; evidence_procedure:str|None=None; notes:str|None=None; provenance:Mapping[str,object]=field(default_factory=dict)
@dataclass(frozen=True, slots=True)
class MethodDefinition:
    method_id:str; name:str; family:str; intended_estimand:str; design_structure:str; pairing_requirement:str; grouping_considerations:str; key_assumptions:tuple[str,...]; output_semantics:str; implementation_status:ScientificStatus; dependency_requirement:str|None=None; scientific_notes:str|None=None
@dataclass(frozen=True, slots=True)
class PreregistrationMetadata:
    status:RegistrationStatus; registration_timestamp:str|None=None; version_hash:str|None=None; frozen_fields:tuple[str,...]=(); amendment_history:tuple[Mapping[str,object],...]=(); exploratory_deviations:tuple[str,...]=(); rationale:str|None=None
@dataclass(frozen=True, slots=True)
class StatisticalAnalysisPlan:
    plan_id:str; plan_version:str; title:str; description:str; components:tuple[str,...]; hypotheses:tuple[HypothesisDefinition,...]; estimands:tuple[EstimandDefinition,...]; units:AnalysisUnitDefinition; grouping:GroupingDefinition|None; pairing:PairingDefinition|None; method_id:str; resampling:ResamplingPlan; multiplicity:MultiplicityPlan; effect_size:EffectSizePlan; missingness:MissingnessPlan; assumptions:tuple[AssumptionRecord,...]; inclusion_rules:tuple[str,...]=(); exclusion_rules:tuple[str,...]=(); dataset_identity:Mapping[str,object]=field(default_factory=dict); benchmark_identity:Mapping[str,object]=field(default_factory=dict); taxonomy_version:str|None=None; model_population:Mapping[str,object]=field(default_factory=dict); evaluation_stage:str|None=None; preregistration:PreregistrationMetadata=field(default_factory=lambda: PreregistrationMetadata(RegistrationStatus.DRAFT)); readiness:ReadinessStates=field(default_factory=lambda: ReadinessStates(True,False,False,False,False)); scientific_status:ScientificStatus=ScientificStatus.EMPIRICAL_HYPOTHESIS; provenance:Mapping[str,object]=field(default_factory=dict); created_timestamp:str|None=None
@dataclass(frozen=True, slots=True)
class StatisticalExperimentArtifact:
    experiment_id:str; analysis_plan_id:str; analysis_plan_hash:str; analysis_plan_version:str; component:str; readiness:ReadinessStates; data_provenance:Mapping[str,object]; grouping_pairing_provenance:Mapping[str,object]; software_versions:Mapping[str,str]; execution_status:str; dataset_identity:Mapping[str,object]=field(default_factory=dict); benchmark_identity:Mapping[str,object]=field(default_factory=dict); model_identities:Mapping[str,object]=field(default_factory=dict); taxonomy_version:str|None=None; effective_rules:Mapping[str,object]=field(default_factory=dict); seed_configuration:Mapping[str,object]=field(default_factory=dict); missingness_summary:Mapping[str,object]=field(default_factory=dict); scientific_status:ScientificStatus=ScientificStatus.EMPIRICAL_HYPOTHESIS; warnings:tuple[str,...]=(); errors:tuple[str,...]=()
@dataclass(frozen=True, slots=True)
class StatisticalResultRecord:
    result_id:str; experiment_id:str; hypothesis_id:str|None=None; estimand_id:str|None=None; method_id:str|None=None; result_status:ResultStatus=ResultStatus.NOT_COMPUTED; estimate:float|None=None; effect_size:float|None=None; standard_error:float|None=None; interval:tuple[float,float]|None=None; p_value:float|None=None; adjusted_p_value:float|None=None; diagnostics:Mapping[str,object]=field(default_factory=dict); assumptions:tuple[str,...]=(); multiplicity_provenance:Mapping[str,object]=field(default_factory=dict); resampling_provenance:Mapping[str,object]=field(default_factory=dict); warnings:tuple[str,...]=(); scientific_interpretation_status:ScientificStatus=ScientificStatus.FUTURE_WORK
