import unittest
from core.persistence.mapping import rc_lossless_record,metric_record
class PersistenceMappingTests(unittest.TestCase):
 def test_rc_is_lossless_and_blocked_for_typed_mapping(self):
  record=rc_lossless_record(record_id="r",scope="session_sequence",payload={"trajectory":[1]},status="uncalibrated");self.assertEqual(record.provenance["typed_mapping"],"blocked_for_typed_mapping")
 def test_draa_pri_scalar_invariants(self):
  with self.assertRaises(ValueError):metric_record(record_id="d",family="draa",scope="evaluation",domain={"risk_score":.1})
  with self.assertRaises(ValueError):metric_record(record_id="p",family="pri",scope="model_configuration",domain={"scalar_pri":.1})
if __name__=="__main__":unittest.main()
