"""Strict finite-numeric validation for Phase 10B.1."""
import math
from dataclasses import dataclass,field
from typing import Iterable,Mapping
from core.statistics.models import ResultStatus
@dataclass(frozen=True,slots=True)
class OmissionMetadata:
 original_count:int|None=None; excluded_by_status:Mapping[str,int]=field(default_factory=dict); reasons:Mapping[str,str]=field(default_factory=dict); missingness_plan_provenance:Mapping[str,object]=field(default_factory=dict)
@dataclass(frozen=True,slots=True)
class ComputedResult:
 method_id:str; computation_status:ResultStatus; n_total:int; n_valid:int; missing_count:int=0; estimate:float|None=None; values:Mapping[str,object]=field(default_factory=dict); warnings:tuple[str,...]=(); numerical_notes:tuple[str,...]=(); backend:str="python_standard_library"; assumption_reference:str|None=None; plan_hash:str|None=None; grouping_provenance:Mapping[str,object]=field(default_factory=dict); pairing_provenance:Mapping[str,object]=field(default_factory=dict); p_value:None=None; adjusted_p_value:None=None; interval:None=None
def finite_values(values:Iterable[object])->tuple[float,...]:
 out=[]
 for value in values:
  if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value): raise ValueError("observations must be finite int or float, excluding bool")
  out.append(float(value))
 return tuple(out)
