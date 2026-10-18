import math,unittest
from core.statistics.models import ResultStatus
from core.statistics.numeric import finite_values,OmissionMetadata
from core.statistics.descriptive import summarize
from core.statistics.differences import differences,paired_differences,DifferenceOrientation
from core.statistics.correlation import pearson,spearman
class BasicStatisticsTests(unittest.TestCase):
 def test_strict_numeric(self):
  self.assertEqual(finite_values((1,2.5)),(1.,2.5))
  for x in (True,None,float("nan"),float("inf"),"1"): 
   with self.assertRaises(ValueError):finite_values((x,))
 def test_descriptive(self):
  self.assertIs(summarize(()).computation_status,ResultStatus.INSUFFICIENT_DATA)
  one=summarize((3,));self.assertEqual(one.values["mean"],3);self.assertIsNone(one.values["sample_variance"])
  s=summarize((1,2,3,4));self.assertEqual(s.values["sample_variance"],5/3);self.assertEqual(s.values["q1"],1.75)
 def test_differences_pairing(self):
  self.assertEqual(differences(5,2,DifferenceOrientation.X_MINUS_Y).estimate,3)
  self.assertEqual(differences((5,),(2,),DifferenceOrientation.Y_MINUS_X).values["differences"],(-3.,))
  self.assertIs(paired_differences((1,),(1,),DifferenceOrientation.X_MINUS_Y).computation_status,ResultStatus.NOT_APPLICABLE)
  r=paired_differences((2,3),(1,1),DifferenceOrientation.X_MINUS_Y,explicit_positional_pairing=True);self.assertEqual(r.values["mean_difference"],1.5)
 def test_correlations(self):
  self.assertEqual(pearson((1,2),(3,4),pairing_declared=True).estimate,1)
  self.assertEqual(pearson((1,2),(4,3),pairing_declared=True).estimate,-1)
  self.assertIs(pearson((1,1),(2,3),pairing_declared=True).computation_status,ResultStatus.UNDEFINED)
  self.assertAlmostEqual(spearman((1,1,2),(1,2,3),pairing_declared=True).estimate,math.sqrt(.75))
  self.assertIs(pearson((1,2),(3,4)).computation_status,ResultStatus.NOT_APPLICABLE)
if __name__=="__main__":unittest.main()
