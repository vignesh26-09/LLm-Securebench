from dataclasses import dataclass
from enum import StrEnum
from statistics import fmean,median,stdev
from core.statistics.models import ResultStatus
from core.statistics.numeric import ComputedResult,finite_values
class DifferenceOrientation(StrEnum): X_MINUS_Y="x_minus_y";Y_MINUS_X="y_minus_x"
def differences(x,y,orientation):
 try:
  left=_as_tuple(x);right=_as_tuple(y)
  if len(left)!=len(right):return ComputedResult("raw_difference",ResultStatus.INVALID_INPUT,max(len(left),len(right)),0,warnings=("aligned_lengths_required",))
  a=finite_values(left);b=finite_values(right); sign=1 if orientation is DifferenceOrientation.X_MINUS_Y else -1; vals=tuple(sign*(u-v) for u,v in zip(a,b,strict=True))
  return ComputedResult("raw_difference",ResultStatus.COMPUTED,len(vals),len(vals),estimate=vals[0] if len(vals)==1 else None,values={"differences":vals,"orientation":orientation.value})
 except (ValueError,TypeError) as e:return ComputedResult("raw_difference",ResultStatus.INVALID_INPUT,0,0,warnings=(str(e),))
def paired_differences(x,y,orientation,*,explicit_positional_pairing=False,pairing_declared=False,allow_complete_case=False):
 if not (explicit_positional_pairing or pairing_declared):return ComputedResult("paired_difference",ResultStatus.NOT_APPLICABLE,0,0,warnings=("explicit_pairing_required",))
 r=differences(x,y,orientation)
 if r.computation_status is not ResultStatus.COMPUTED:return r
 vals=r.values["differences"];out={"differences":vals,"orientation":orientation.value,"mean_difference":fmean(vals) if vals else None,"median_difference":median(vals) if vals else None,"sample_standard_deviation":stdev(vals) if len(vals)>=2 else None}
 return ComputedResult("paired_difference",ResultStatus.COMPUTED,len(vals),len(vals),estimate=out["mean_difference"],values=out,numerical_notes=("sample_standard_deviation_undefined_for_one_pair",) if len(vals)==1 else (),pairing_provenance={"explicit_positional_pairing":explicit_positional_pairing,"pairing_declared":pairing_declared})
def _as_tuple(value):return tuple(value) if isinstance(value,(tuple,list)) else (value,)
