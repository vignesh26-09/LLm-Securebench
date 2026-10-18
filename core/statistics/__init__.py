"""Statistical analysis boundaries."""
"""Phase 10A statistical planning metadata; no inferential computation."""
from core.statistics.analysis import StatisticalAnalyzer
from core.statistics.models import StatisticalAnalysisPlan, StatisticalExperimentArtifact, StatisticalResultRecord
from core.statistics.paired import AnalysisRecord, PairedValue, grouped_paired_analyses, paired_difference_analysis
from core.statistics.complementarity import ComplementarityRow, complementarity_table
__all__=["StatisticalAnalyzer","StatisticalAnalysisPlan","StatisticalExperimentArtifact","StatisticalResultRecord",
         "AnalysisRecord","PairedValue","paired_difference_analysis","grouped_paired_analyses",
         "ComplementarityRow","complementarity_table"]
