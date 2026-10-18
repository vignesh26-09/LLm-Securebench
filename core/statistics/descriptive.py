"""Dependency-free descriptive summaries with an explicit quantile convention."""
import math
from statistics import fmean,median
from core.statistics.models import ResultStatus
from core.statistics.numeric import ComputedResult,OmissionMetadata,finite_values
def summarize(values, *, omission:OmissionMetadata=OmissionMetadata(), descriptive_only:bool=True):
 try: data=finite_values(values)
 except ValueError as e: return ComputedResult("descriptive_summary",ResultStatus.INVALID_INPUT,0,0,warnings=(str(e),))
 total=omission.original_count if omission.original_count is not None else len(data)
 if not data:return ComputedResult("descriptive_summary",ResultStatus.INSUFFICIENT_DATA,total,0,total,warnings=("no_valid_observations",))
 avg=fmean(data); result={"minimum":min(data),"maximum":max(data),"mean":avg,"median":median(data),"q1":_quantile(data,.25),"q3":_quantile(data,.75)}; result["iqr"]=result["q3"]-result["q1"]
 notes=[]
 if len(data)==1: result.update({"sample_variance":None,"sample_standard_deviation":None});notes.append("sample_variance_undefined_for_one_observation")
 else:
  var=sum((x-avg)*(x-avg) for x in data)/(len(data)-1); result.update({"sample_variance":var,"sample_standard_deviation":math.sqrt(var)})
 return ComputedResult("descriptive_summary",ResultStatus.COMPUTED,total,len(data),total-len(data),avg,result,numerical_notes=tuple(notes),grouping_provenance={"descriptive_only":descriptive_only,**dict(omission.missingness_plan_provenance)})
def _quantile(values,q):
 ordered=sorted(values); pos=(len(ordered)-1)*q; low=int(math.floor(pos));high=int(math.ceil(pos));return ordered[low]+(ordered[high]-ordered[low])*(pos-low)
