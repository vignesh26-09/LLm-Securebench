"""Lossless adapters from existing scientific dataclasses to persistence payloads."""
from dataclasses import asdict,is_dataclass
from enum import Enum
from core.persistence.models import ScientificRecordEntity
def _ready(value):
 if isinstance(value,Enum):return value.value
 if is_dataclass(value):return _ready(asdict(value))
 if isinstance(value,dict):return {str(k):_ready(v) for k,v in value.items()}
 if isinstance(value,(tuple,list)):return [_ready(v) for v in value]
 return value
def metric_record(*,record_id,family,scope,domain,schema_version="v1",owner_id=None,status=None,provenance=None):
 payload=_ready(domain)
 if family=="draa" and payload.get("risk_score") is not None:raise ValueError("DRAA Mode A/B risk_score must remain null")
 if family=="pri" and payload.get("scalar_pri") is not None:raise ValueError("PRI scalar_pri must remain null")
 return ScientificRecordEntity(id=record_id,family=family,schema_version=schema_version,scope=scope,owner_id=owner_id,status=status,payload=payload,provenance=dict(provenance or {}))
def rc_lossless_record(*,record_id,scope,payload,status,provenance=None):
 return ScientificRecordEntity(id=record_id,family="rc",schema_version="lossless-payload-v1",scope=scope,status=status,payload=_ready(payload),provenance={"typed_mapping":"blocked_for_typed_mapping",**dict(provenance or {})})
