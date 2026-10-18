import math
from core.statistics.models import ResultStatus
from core.statistics.numeric import ComputedResult,finite_values
_EPS=32*math.ulp(1.0)
def pearson(x,y,*,pairing_declared=False,independent_reduction=None):
 return _correlate(x,y,"pearson_correlation",pairing_declared,independent_reduction,False)
def spearman(x,y,*,pairing_declared=False,independent_reduction=None):
 return _correlate(x,y,"spearman_correlation",pairing_declared,independent_reduction,True)
def _correlate(x,y,name,pairing,reduce,ranks):
 if not pairing:return ComputedResult(name,ResultStatus.NOT_APPLICABLE,0,0,warnings=("explicit_pair_alignment_required",))
 if reduce is not None and not all(key in reduce for key in ("original_grouping_structure","reduction_procedure","resulting_analysis_unit","rationale","provenance")):return ComputedResult(name,ResultStatus.NOT_APPLICABLE,0,0,warnings=("structured_independence_reduction_required",))
 try:a=finite_values(x);b=finite_values(y)
 except ValueError as e:return ComputedResult(name,ResultStatus.INVALID_INPUT,0,0,warnings=(str(e),))
 if len(a)!=len(b):return ComputedResult(name,ResultStatus.INVALID_INPUT,max(len(a),len(b)),0,warnings=("aligned_lengths_required",))
 if len(a)<2:return ComputedResult(name,ResultStatus.INSUFFICIENT_DATA,len(a),len(a),warnings=("at_least_two_pairs_required",))
 if ranks:a,b=_ranks(a),_ranks(b)
 ma=sum(a)/len(a);mb=sum(b)/len(b);xx=sum((v-ma)**2 for v in a);yy=sum((v-mb)**2 for v in b)
 if xx==0 or yy==0:return ComputedResult(name,ResultStatus.UNDEFINED,len(a),len(a),warnings=("zero_variance",))
 r=sum((u-ma)*(v-mb) for u,v in zip(a,b,strict=True))/math.sqrt(xx*yy)
 if r < -1-_EPS or r > 1+_EPS:return ComputedResult(name,ResultStatus.NUMERICAL_FAILURE,len(a),len(a),warnings=("coefficient_outside_theoretical_bounds",))
 r=min(1.0,max(-1.0,r));return ComputedResult(name,ResultStatus.COMPUTED,len(a),len(a),estimate=r,values={"coefficient":r},pairing_provenance={"explicit_pairing":pairing,"independence_reduction":reduce})
def _ranks(values):
 result=[0.]*len(values);ordered=sorted(enumerate(values),key=lambda x:x[1]);i=0
 while i<len(ordered):
  j=i
  while j+1<len(ordered) and ordered[j+1][1]==ordered[i][1]:j+=1
  rank=(i+1+j+1)/2
  for k in range(i,j+1):result[ordered[k][0]]=rank
  i=j+1
 return tuple(result)
