from sqlalchemy.orm import Session
from core.persistence.models import ScientificRecordEntity,ScientificReviewEntity
class PersistenceService:
 def __init__(self,session:Session):self.session=session
 def append_record(self,record:ScientificRecordEntity):
  self.session.add(record);self.session.commit();return record
 def create_review(self,review:ScientificReviewEntity):
  self.session.add(review);self.session.commit();return review
 def append_layer_two(self,record):
  if record.status in {"skipped","failed","refused"} and record.score is not None: raise ValueError("non-completed Layer 2 results must have null score")
  self.session.add(record);self.session.commit();return record
