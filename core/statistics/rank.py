"""Phase 10B.3 rank statistics only; no p-values."""
from core.statistics.models import ResultStatus
from core.statistics.numeric import ComputedResult,finite_values
from core.statistics.differences import differences,DifferenceOrientation
def average_ranks(values):
 data=finite_values(values);out=[0.]*len(data);items=sorted(enumerate(data),key=lambda x:x[1]);i=0
 while i<len(items):
  j=i
  while j+1<len(items) and items[j+1][1]==items[i][1]:j+=1
  rank=(i+j+2)/2
  for k in range(i,j+1):out[items[k][0]]=rank
  i=j+1
 return tuple(out)
def mann_whitney(x,y,*,independent_declared=False):
 if not independent_declared:return ComputedResult("mann_whitney_u",ResultStatus.NOT_APPLICABLE,0,0,warnings=("independent_groups_must_be_declared",))
 try:a=finite_values(x);b=finite_values(y)
 except ValueError as e:return ComputedResult("mann_whitney_u",ResultStatus.INVALID_INPUT,0,0,warnings=(str(e),))
 if not a or not b:return ComputedResult("mann_whitney_u",ResultStatus.INSUFFICIENT_DATA,len(a)+len(b),len(a)+len(b))
 ranks=average_ranks(a+b);u1=sum(ranks[:len(a)])-len(a)*(len(a)+1)/2;u2=len(a)*len(b)-u1;return ComputedResult("mann_whitney_u",ResultStatus.COMPUTED,len(a)+len(b),len(a)+len(b),estimate=u1,values={"u1":u1,"u2":u2,"rank_biserial":(u1-u2)/(len(a)*len(b)),"orientation":"first_group"})
def wilcoxon(x,y,orientation,*,pairing_declared=False):
 if not pairing_declared:return ComputedResult("wilcoxon_signed_rank",ResultStatus.NOT_APPLICABLE,0,0,warnings=("explicit_pairing_required",))
 r=differences(x,y,orientation)
 if r.computation_status is not ResultStatus.COMPUTED:return ComputedResult("wilcoxon_signed_rank",r.computation_status,r.n_total,r.n_valid,warnings=r.warnings)
 d=r.values["differences"];nonzero=[v for v in d if v!=0]
 if not nonzero:return ComputedResult("wilcoxon_signed_rank",ResultStatus.UNDEFINED,len(d),0,warnings=("all_differences_zero_after_discard_policy",),values={"discarded_zero_count":len(d)})
 ranks=average_ranks(tuple(abs(v) for v in nonzero));wp=sum(rank for value,rank in zip(nonzero,ranks,strict=True) if value>0);wm=sum(rank for value,rank in zip(nonzero,ranks,strict=True) if value<0);return ComputedResult("wilcoxon_signed_rank",ResultStatus.COMPUTED,len(d),len(nonzero),estimate=min(wp,wm),values={"w_plus":wp,"w_minus":wm,"reported_w":min(wp,wm),"rank_biserial":(wp-wm)/(wp+wm),"discarded_zero_count":len(d)-len(nonzero),"zero_policy":"discard"})
def cliffs_delta(x,y,*,independent_declared=False):
 if not independent_declared:return ComputedResult("cliffs_delta",ResultStatus.NOT_APPLICABLE,0,0,warnings=("independent_groups_must_be_declared",))
 try:a=finite_values(x);b=finite_values(y)
 except ValueError as e:return ComputedResult("cliffs_delta",ResultStatus.INVALID_INPUT,0,0,warnings=(str(e),))
 if not a or not b:return ComputedResult("cliffs_delta",ResultStatus.INSUFFICIENT_DATA,len(a)+len(b),len(a)+len(b))
 score=sum((u>v)-(u<v) for u in a for v in b)/(len(a)*len(b));return ComputedResult("cliffs_delta",ResultStatus.COMPUTED,len(a)+len(b),len(a)+len(b),estimate=score,values={"orientation":"first_group"})
