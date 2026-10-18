"""Repositories receive sessions and never own commits or scientific computations."""
from sqlalchemy import select
from sqlalchemy.orm import Session
from core.persistence.models import ScientificRecordEntity
class ScientificRecordRepository:
 def __init__(self,session:Session):self.session=session
 def add(self,record:ScientificRecordEntity):self.session.add(record)
 def get(self,record_id:str):return self.session.get(ScientificRecordEntity,record_id)
 def list(self,*,family:str|None=None,limit:int=50,offset:int=0):
  statement=select(ScientificRecordEntity).order_by(ScientificRecordEntity.created_at).limit(limit).offset(offset)
  if family is not None:statement=statement.where(ScientificRecordEntity.family==family)
  return tuple(self.session.scalars(statement))
