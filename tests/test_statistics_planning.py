import unittest
from core.statistics.models import *
from core.statistics.registry import METHOD_REGISTRY
from core.statistics.serialization import dumps,loads_plan,schema_hash
from core.statistics.validation import validate_plan
class StatisticsPlanningTests(unittest.TestCase):
 def plan(self,**prov):
  h=HypothesisDefinition("h","bsda","question","estimation",AnalysisMode.DESCRIPTIVE,ScientificStatus.EMPIRICAL_HYPOTHESIS,None,None,provenance={"estimand_id":"e"})
  e=EstimandDefinition("e","raw","desc","paired raw difference","distance",None,None,None)
  return StatisticalAnalysisPlan("p","v1","title","desc",("bsda",),(h,),(e,),AnalysisUnitDefinition(experimental_unit="base_case"),GroupingDefinition("g",("base_case_id",),GroupingPurpose.PAIRING),PairingDefinition("pair",PairingStatus.PAIRED,("base_case_id",)),"paired_t_test",ResamplingPlan("r",ResamplingMethod.GROUPED_BOOTSTRAP,"base_case",("base_case_id",),"pair"),MultiplicityPlan("m",None,None,MultiplicityMethod.NONE),EffectSizePlan("x","paired_difference",raw_scale_effect="difference"),MissingnessPlan("miss",{"failed":"summarize","uncalibrated":"retain"}),(),readiness=ReadinessStates(True,True,False,False,False),provenance=prov)
 def test_readiness_separation(self):
  state=ReadinessStates(True,True,False,False,False,True); self.assertTrue(state.plan_ready); self.assertFalse(state.data_ready)
  with self.assertRaises(ValueError): ReadinessStates(True,True,False,True,False)
  with self.assertRaises(ValueError): ReadinessStates(True,True,True,True,True,True,"review")
 def test_plan_round_trip_hash_and_unspecified_resampling(self):
  plan=self.plan(); self.assertEqual(plan.resampling.confidence_level,None); self.assertEqual(plan.resampling.resample_count,None); self.assertEqual(loads_plan(dumps(plan)),plan); self.assertEqual(schema_hash(plan),schema_hash(plan))
 def test_registry_metadata_only(self):
  self.assertIn("pearson_correlation",METHOD_REGISTRY); self.assertEqual(METHOD_REGISTRY["mixed_effects_models"].implementation_status,ScientificStatus.FUTURE_WORK)
 def test_component_guards(self):
  self.assertIn("bsda_composite_validation_blocked",validate_plan(self.plan(validation_target="composite")).errors)
  rc=self.plan(degradation_threshold=.1); rc=StatisticalAnalysisPlan(*[getattr(rc,x) for x in rc.__dataclass_fields__])
  # Component guards are checked through an RC-declared plan.
  plan=StatisticalAnalysisPlan("r","v","t","d",("rc",),rc.hypotheses,rc.estimands,rc.units,rc.grouping,rc.pairing,rc.method_id,rc.resampling,rc.multiplicity,rc.effect_size,rc.missingness,rc.assumptions,readiness=rc.readiness,provenance={"degradation_threshold":.1})
  self.assertIn("rc_threshold_requires_calibration_provenance",validate_plan(plan).errors)
 def test_result_is_not_computed(self):
  r=StatisticalResultRecord("r","e"); self.assertIs(r.result_status,ResultStatus.NOT_COMPUTED); self.assertIsNone(r.p_value)
if __name__=="__main__": unittest.main()
