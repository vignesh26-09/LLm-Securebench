"""Metadata-only registry: no method mathematics is implemented."""
from core.statistics.models import MethodDefinition, ScientificStatus
_NAMES=("descriptive_summaries","pearson_correlation","spearman_correlation","kendall_tau","paired_t_test","welch_t_test","wilcoxon_signed_rank","mann_whitney_u","anova","permutation_randomization","regression","mixed_effects_models","glmm","ordinal_regression","grouped_bootstrap","hierarchical_bootstrap")
METHOD_REGISTRY={name:MethodDefinition(name,name.replace("_"," "),"candidate", "declared future estimand", "analysis-plan specific", "analysis-plan specific", "dependence must be declared", (), "metadata only", ScientificStatus.FUTURE_WORK, "statsmodels or other approved dependency" if name in {"mixed_effects_models","glmm","ordinal_regression"} else None) for name in _NAMES}
def get_method(method_id:str)->MethodDefinition: return METHOD_REGISTRY[method_id]
