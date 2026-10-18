"""Phase 10B.2 t statistics only; no distribution CDF or p-values."""
import math
from statistics import fmean
from core.statistics.models import ResultStatus
from core.statistics.numeric import ComputedResult,finite_values
from core.statistics.differences import DifferenceOrientation,paired_differences
def paired_t(x,y,orientation,*,pairing_declared=False,independent_reduction=None,alternative="two_sided"):
 if not pairing_declared:return ComputedResult("paired_t_test",ResultStatus.NOT_APPLICABLE,0,0,warnings=("explicit_pairing_required",))
 if independent_reduction is not None and not all(k in independent_reduction for k in ("original_grouping_structure","reduction_procedure","resulting_analysis_unit","rationale","provenance")):return ComputedResult("paired_t_test",ResultStatus.NOT_APPLICABLE,0,0,warnings=("structured_independence_reduction_required",))
 r=paired_differences(x,y,orientation,pairing_declared=True)
 if r.computation_status is not ResultStatus.COMPUTED:return ComputedResult("paired_t_test",r.computation_status,r.n_total,r.n_valid,warnings=r.warnings)
 d=r.values["differences"];n=len(d)
 if n<2:return ComputedResult("paired_t_test",ResultStatus.INSUFFICIENT_DATA,n,n,warnings=("at_least_two_pairs_required",))
 mean=fmean(d);var=sum((v-mean)**2 for v in d)/(n-1)
 if var==0:return ComputedResult("paired_t_test",ResultStatus.UNDEFINED,n,n,warnings=("zero_variance_differences",),values={"mean_difference":mean,"degrees_of_freedom":n-1,"alternative":alternative})
 se=math.sqrt(var/n);return ComputedResult("paired_t_test",ResultStatus.COMPUTED,n,n,estimate=mean,values={"statistic":mean/se,"degrees_of_freedom":n-1,"alternative":alternative,"mean_difference":mean,"sample_standard_deviation":math.sqrt(var)},pairing_provenance={"explicit_pairing":True,"independence_reduction":independent_reduction})
def welch_t(x,y,*,independent_declared=False,independent_reduction=None,alternative="two_sided"):
 if not independent_declared:return ComputedResult("welch_t_test",ResultStatus.NOT_APPLICABLE,0,0,warnings=("independent_groups_must_be_declared",))
 if independent_reduction is not None and not all(k in independent_reduction for k in ("original_grouping_structure","reduction_procedure","resulting_analysis_unit","rationale","provenance")):return ComputedResult("welch_t_test",ResultStatus.NOT_APPLICABLE,0,0,warnings=("structured_independence_reduction_required",))
 try:a=finite_values(x);b=finite_values(y)
 except ValueError as e:return ComputedResult("welch_t_test",ResultStatus.INVALID_INPUT,0,0,warnings=(str(e),))
 if len(a)<2 or len(b)<2:return ComputedResult("welch_t_test",ResultStatus.INSUFFICIENT_DATA,len(a)+len(b),len(a)+len(b),warnings=("at_least_two_per_group_required",))
 ma=fmean(a);mb=fmean(b);va=sum((v-ma)**2 for v in a)/(len(a)-1);vb=sum((v-mb)**2 for v in b)/(len(b)-1);q=va/len(a)+vb/len(b)
 if q==0:return ComputedResult("welch_t_test",ResultStatus.UNDEFINED,len(a)+len(b),len(a)+len(b),warnings=("zero_standard_error",),values={"mean_difference":ma-mb,"alternative":alternative})
 df=q*q/((va/len(a))**2/(len(a)-1)+(vb/len(b))**2/(len(b)-1));return ComputedResult("welch_t_test",ResultStatus.COMPUTED,len(a)+len(b),len(a)+len(b),estimate=ma-mb,values={"statistic":(ma-mb)/math.sqrt(q),"degrees_of_freedom":df,"mean_difference":ma-mb,"alternative":alternative})
