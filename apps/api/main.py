"""FastAPI surface for persisted evidence, local runs, and ephemeral metric computation."""
import uuid
import os
import json
from pathlib import Path
from fastapi import FastAPI,Request,HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import text
from core.persistence.database import make_engine,Base
from sqlalchemy.orm import sessionmaker,Session
from core.persistence.models import ScientificRecordEntity
from core.persistence.repositories import ScientificRecordRepository
from core.persistence.models import ScientificReviewEntity
from core.persistence.service import PersistenceService
from pydantic import BaseModel,Field
from core.health import health_status
from apps.api.resources import register_resources,project
from sqlalchemy.exc import SQLAlchemyError
from apps.api.local_execution import register_execution
from apps.api.auth import register_auth
from apps.api.metric_compute import register_metric_compute
def create_app(database_url:str="sqlite:///./securellmbench.db", *, enable_local_runs:bool=False, enable_remote_runs:bool=False, require_auth:bool=False):
 app=FastAPI(title="SecureLLMBench API"); engine=make_engine(database_url); factory=sessionmaker(engine,expire_on_commit=False,class_=Session)
 if database_url.startswith("sqlite"): Base.metadata.create_all(engine)
 app.state.session_factory=factory
 register_auth(app,engine,required=require_auth)
 register_resources(app,factory)
 register_metric_compute(app,factory)
 register_execution(app,database_url,enable_local_runs,enable_remote_runs)
 @app.exception_handler(SQLAlchemyError)
 async def database_error(request,exc):
  return JSONResponse(status_code=503,content={"code":"database_unavailable","message":"Database unavailable"})
 @app.middleware("http")
 async def request_id(request:Request,call_next):
  response=await call_next(request);response.headers["X-Request-ID"]=request.headers.get("X-Request-ID",str(uuid.uuid4()));return response
 @app.get("/health")
 def health():return health_status()
 @app.get("/ready")
 def ready():
  try:
   with factory() as session:session.execute(text("SELECT 1"))
   return {"status":"ready"}
  except Exception:return JSONResponse(status_code=503,content={"status":"unavailable"})
 @app.get("/calibration-summary")
 def calibration_summary():
  """Read-only aggregate calibration projection from the verified evidence artifact."""
  path=Path(__file__).resolve().parents[2]/"artifacts"/"paper_evidence"/"calibration_verification.json"
  try:
   value=json.loads(path.read_text(encoding="utf-8"))
   return {"status":value["status"],"result":value["recomputed"],"source_manifest":value["source_manifest"],"interpretation":"The current Gemma-based judge under the fixed predeclared mapping is not sufficiently validated to replace independent human outcome labels."}
  except (OSError,KeyError,ValueError):raise HTTPException(503,"Verified calibration artifact is unavailable")
 @app.get("/scientific-records")
 def scientific_records(family:str|None=None,limit:int=50,offset:int=0):
  if limit<1 or limit>100 or offset<0:return JSONResponse(status_code=422,content={"code":"invalid_pagination"})
  with factory() as session:
   rows=ScientificRecordRepository(session).list(family=family,limit=limit,offset=offset)
   return {"items":[{"id":row.id,"family":row.family,"schema_version":row.schema_version,"scope":row.scope,"status":row.status,"payload":row.payload,"provenance":row.provenance} for row in rows],"limit":limit,"offset":offset}
 @app.get("/scientific-records/{record_id}")
 def scientific_record(record_id:str):
  with factory() as session:
   row=ScientificRecordRepository(session).get(record_id)
   if row is None:raise HTTPException(404,"Record not found")
   return project(row)
 class ReviewInput(BaseModel):
  review_id:str;claim_id:str;evidence_bundle_id:str;reviewer_protocol:str;decision:str;rationale:str=Field(min_length=1);provenance:dict[str,object]={}
 @app.post("/internal/scientific-reviews",status_code=201)
 def internal_review(input:ReviewInput):
  with factory() as session:
   review=PersistenceService(session).create_review(ScientificReviewEntity(id=input.review_id,claim_id=input.claim_id,evidence_bundle_id=input.evidence_bundle_id,reviewer_protocol=input.reviewer_protocol,decision=input.decision,rationale=input.rationale,provenance=input.provenance))
   return {"review_id":review.id,"decision":review.decision,"claim_validated":False}
 return app
app=create_app(enable_local_runs=os.environ.get('SECURELLM_ENABLE_LOCAL_RUNS')=='1',
               enable_remote_runs=os.environ.get('SECURELLM_ENABLE_REMOTE_RUNS')=='1',require_auth=True)
