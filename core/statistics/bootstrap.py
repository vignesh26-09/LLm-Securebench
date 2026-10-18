"""Phase 10B.4 explicit IID/paired percentile bootstrap."""
import math,random
from dataclasses import dataclass,field
from typing import Callable,Sequence
from core.statistics.models import ResultStatus
@dataclass(frozen=True,slots=True)
class BootstrapConfig:
 resample_count:int; confidence_level:float; statistic_id:str; paired:bool=False; seed:int|None=None
 def __post_init__(self):
  if self.resample_count<=0:raise ValueError("resample_count must be positive")
  if not 0<self.confidence_level<1:raise ValueError("confidence_level must be in (0,1)")
@dataclass(frozen=True,slots=True)
class BootstrapResult:
 status:ResultStatus; requested:int; valid:int; failed:int; interval:tuple[float,float]|None; config:BootstrapConfig; warnings:tuple[str,...]=(); provenance:dict[str,object]=field(default_factory=dict)
def bootstrap(values:Sequence[object], statistic:Callable[[tuple[object,...]],object], config:BootstrapConfig, *, independent_declared=False):
 if not independent_declared:return BootstrapResult(ResultStatus.NOT_APPLICABLE,config.resample_count,0,0,None,config,("independent_units_must_be_declared",))
 if not values:return BootstrapResult(ResultStatus.INSUFFICIENT_DATA,config.resample_count,0,0,None,config,("no_units",))
 rng=random.Random(config.seed);out=[];failed=0
 for _ in range(config.resample_count):
  sample=tuple(values[rng.randrange(len(values))] for _ in values)
  try:
   value=statistic(sample)
   if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):raise ValueError()
   out.append(float(value))
  except Exception:failed+=1
 if failed:return BootstrapResult(ResultStatus.NOT_COMPUTED,config.resample_count,len(out),failed,None,config,("failed_replicates_require_explicit_failure_policy",))
 out.sort();q=(1-config.confidence_level)/2;return BootstrapResult(ResultStatus.COMPUTED,config.resample_count,len(out),0,(_q(out,q),_q(out,1-q)),config)
def paired_bootstrap(x,y,statistic,config,*,pairing_declared=False):
 if len(x)!=len(y):return BootstrapResult(ResultStatus.INVALID_INPUT,config.resample_count,0,0,None,config,("aligned_pairs_required",))
 if not pairing_declared:return BootstrapResult(ResultStatus.NOT_APPLICABLE,config.resample_count,0,0,None,config,("explicit_pairing_required",))
 return bootstrap(tuple(zip(x,y,strict=True)),statistic,config,independent_declared=True)
def _q(v,q):
 p=(len(v)-1)*q;i=int(math.floor(p));j=int(math.ceil(p));return v[i]+(v[j]-v[i])*(p-i)
