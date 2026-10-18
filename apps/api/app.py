"""Compatibility entry point for the Phase 11 FastAPI application."""
from apps.api.main import app, create_app
class ApiApplication:
 def health(self): return {"service":"securellmbench","status":"ok"}
