import unittest
from core.statistics.differences import DifferenceOrientation
from core.statistics.parametric import paired_t,welch_t
from core.statistics.rank import mann_whitney,wilcoxon,cliffs_delta
from core.statistics.bootstrap import BootstrapConfig,bootstrap
from core.statistics.models import ResultStatus
class RemainingStatisticsTests(unittest.TestCase):
 def test_b2(self):
  self.assertEqual(paired_t((2,4),(1,2),DifferenceOrientation.X_MINUS_Y,pairing_declared=True).values["degrees_of_freedom"],1)
  self.assertIs(paired_t((1,),(1,),DifferenceOrientation.X_MINUS_Y,pairing_declared=True).computation_status,ResultStatus.INSUFFICIENT_DATA)
  self.assertIs(welch_t((1,2),(3,4),independent_declared=True).p_value,None)
 def test_b3(self):
  self.assertEqual(mann_whitney((3,4),(1,2),independent_declared=True).values["u1"],4)
  self.assertIs(wilcoxon((1,1),(1,1),DifferenceOrientation.X_MINUS_Y,pairing_declared=True).computation_status,ResultStatus.UNDEFINED)
  self.assertEqual(cliffs_delta((3,),(1,),independent_declared=True).estimate,1)
 def test_b4(self):
  c=BootstrapConfig(10,.8,"mean",seed=1);r=bootstrap((1,2,3),lambda x:sum(x)/len(x),c,independent_declared=True);self.assertIs(r.status,ResultStatus.COMPUTED);self.assertEqual(r,bootstrap((1,2,3),lambda x:sum(x)/len(x),c,independent_declared=True))
if __name__=="__main__":unittest.main()
