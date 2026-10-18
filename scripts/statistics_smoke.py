"""Phase 10A metadata-only smoke check; it performs no statistical inference."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.statistics.models import *
from core.statistics.serialization import dumps,loads_plan,schema_hash
from core.statistics.descriptive import summarize
from core.statistics.differences import paired_differences,DifferenceOrientation
from core.statistics.correlation import pearson,spearman
from core.statistics.parametric import paired_t,welch_t
from core.statistics.rank import mann_whitney,wilcoxon
from core.statistics.bootstrap import BootstrapConfig,bootstrap
def main():
 h=HypothesisDefinition("bsda-h","bsda","Do components change under matched attack?","estimation",AnalysisMode.DESCRIPTIVE,ScientificStatus.EMPIRICAL_HYPOTHESIS,"declared future population","matched base cases",provenance={"estimand_id":"bsda-e"})
 e=EstimandDefinition("bsda-e","paired component difference","raw source-native component difference","matched component difference","distance",None,"declared future population","baseline vs attacked")
 plan=StatisticalAnalysisPlan("statistics-smoke","v1","BSDA component plan","metadata only",("bsda",),(h,),(e,),AnalysisUnitDefinition(experimental_unit="base_case",pairing_unit="base_case",resampling_unit="base_case"),GroupingDefinition("base-cases",("base_case_id",),GroupingPurpose.PAIRING),PairingDefinition("matched",PairingStatus.PAIRED,("base_case_id",),("baseline","attacked")),"paired_t_test",ResamplingPlan("resampling",ResamplingMethod.GROUPED_BOOTSTRAP,"base_case",("base_case_id",),"matched"),MultiplicityPlan("multiplicity",None,None,MultiplicityMethod.NONE),EffectSizePlan("effect","paired_difference",raw_scale_effect="raw difference"),MissingnessPlan("missing",{"failed":"summarize","uncalibrated":"retain"}),(),readiness=ReadinessStates(True,True,False,False,False))
 assert loads_plan(dumps(plan))==plan
 artifact=StatisticalExperimentArtifact("statistics-smoke-experiment",plan.plan_id,schema_hash(plan),plan.plan_version,"bsda",plan.readiness,{}, {},{"python":"3.11"},"metadata_created")
 result=StatisticalResultRecord("statistics-smoke-result",artifact.experiment_id,h.hypothesis_id,e.estimand_id,"paired_t_test")
 d=summarize((1,2,3)); pair=paired_differences((2,4,6),(1,2,3),DifferenceOrientation.X_MINUS_Y,explicit_positional_pairing=True); p=pearson((1,2,3),(2,4,6),pairing_declared=True); s=spearman((1,2,3),(3,2,1),pairing_declared=True)
 t=paired_t((2,4),(1,2),DifferenceOrientation.X_MINUS_Y,pairing_declared=True);u=mann_whitney((3,4),(1,2),independent_declared=True);b=bootstrap((1,2,3),lambda x:sum(x)/len(x),BootstrapConfig(10,.8,"mean",seed=1),independent_declared=True)
 print({"phase_10b2":t.computation_status.value=="computed","phase_10b3":u.computation_status.value=="computed","phase_10b4":b.status.value=="computed","phase_10c_safe_subset":False,"phase_10d_infrastructure":True,"scientific_claims_validated":False})
if __name__=="__main__": main()
