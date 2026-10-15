"""Local workspace accounts with hashed passwords and expiring server sessions."""
import hashlib
import hmac
import secrets
import time
from collections import defaultdict

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import Column, Float, MetaData, String, Table, delete, insert, select
from sqlalchemy.exc import IntegrityError


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=10, max_length=256)
    name: str = Field(default="Researcher", min_length=1, max_length=80)


def register_auth(app, engine, *, required=False):
    metadata = MetaData()
    users = Table("workspace_users", metadata,
                  Column("email", String(254), primary_key=True),
                  Column("name", String(80), nullable=False),
                  Column("salt", String(64), nullable=False),
                  Column("password_hash", String(128), nullable=False))
    sessions = Table("workspace_sessions", metadata,
                     Column("token_hash", String(64), primary_key=True),
                     Column("email", String(254), nullable=False),
                     Column("expires", Float, nullable=False))
    metadata.create_all(engine)
    attempts = defaultdict(list)

    def digest(token):
        return hashlib.sha256(token.encode()).hexdigest()

    def identity(request):
        token = request.cookies.get("securellm_session", "")
        if not token:
            return None
        with engine.connect() as conn:
            row = conn.execute(select(users.c.email, users.c.name).join(
                sessions, users.c.email == sessions.c.email).where(
                    sessions.c.token_hash == digest(token), sessions.c.expires > time.time())).first()
            return {"email": row.email, "name": row.name} if row else None

    @app.middleware("http")
    async def workspace_access(request: Request, call_next):
        public_reads = {"/health", "/ready", "/runtime-models", "/showcase-models", "/benchmark-datasets", "/benchmark-jobs"}
        path = request.url.path
        guest_read = request.method == "GET" and (path in public_reads or path.startswith("/benchmark-jobs/") or (path.startswith("/benchmark-runs/") and path.endswith("/report")))
        if required and not path.startswith("/auth/") and not guest_read:
            if not identity(request):
                if path.startswith("/internal/benchmark-jobs/") and path.endswith("/stop") and request.method == "POST":
                    request.state.guest_stop = True
                elif path == "/internal/benchmark-jobs" and request.method == "POST":
                    try:
                        body = await request.json()
                    except ValueError:
                        return JSONResponse(status_code=422, content={"detail": "Invalid test configuration"})
                    if not isinstance(body, dict):
                        return JSONResponse(status_code=422, content={"detail": "Invalid test configuration"})
                    if body.get("provider", "ollama-local") != "ollama-local" or body.get("model") not in {"gemma3:4b", "qwen3.5:2b", "llama3.2:3b"}:
                        return JSONResponse(status_code=401, content={"detail": "Sign in to connect your own model."})
                    if body.get("dataset_key") != "mixed-source-10000-v1" or body.get("case_count") != 10000 or body.get("case_offset", 0) != 0 or body.get("confirm_full_corpus") is not True:
                        return JSONResponse(status_code=422, content={"detail": "Predefined tests use all 10,000 prompts. Confirm the full run budget before starting."})
                else:
                    return JSONResponse(status_code=401, content={"detail": "Please sign in to your workspace."})
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            origin = request.headers.get("origin")
            # The Vite proxy keeps the browser origin but forwards the backend host.
            allowed = {str(request.base_url).rstrip("/"), "http://127.0.0.1:5173", "http://localhost:5173"}
            if origin and origin not in allowed:
                return JSONResponse(status_code=403, content={"detail": "Origin is not allowed."})
        return await call_next(request)

    def establish(response, email, request):
        token = secrets.token_urlsafe(40)
        with engine.begin() as conn:
            conn.execute(delete(sessions).where(sessions.c.expires <= time.time()))
            conn.execute(insert(sessions).values(token_hash=digest(token), email=email, expires=time.time() + 28800))
        response.set_cookie("securellm_session", token, httponly=True, samesite="strict", max_age=28800, secure=request.url.scheme == "https")

    @app.get("/auth/session")
    def session(request: Request):
        return {"user": identity(request)}

    @app.post("/auth/sample")
    def sample_session(request: Request, response: Response):
        """An explicit sample account for the loopback-only local demonstration."""
        if request.client is None or request.client.host not in {"127.0.0.1", "::1"}:
            raise HTTPException(403, "Sample sign-in is available only on the local workspace")
        email = "sample@securellm.local"
        with engine.begin() as conn:
            exists = conn.execute(select(users.c.email).where(users.c.email == email)).first()
            if not exists:
                salt = secrets.token_hex(32)
                password_hash = hashlib.pbkdf2_hmac("sha256", secrets.token_bytes(48), bytes.fromhex(salt), 310000).hex()
                conn.execute(insert(users).values(email=email, name="Sample Researcher", salt=salt, password_hash=password_hash))
        establish(response, email, request)
        return {"user": identity_from_email(email)}

    @app.post("/auth/login")
    @app.post("/auth/register")
    def authenticate(credentials: Credentials, request: Request, response: Response):
        action = request.url.path.rsplit("/", 1)[-1]
        key = request.client.host if request.client else "local"
        attempts[key] = [stamp for stamp in attempts[key] if stamp > time.time() - 300]
        if len(attempts[key]) >= 15:
            raise HTTPException(429, "Too many attempts. Try again in five minutes.")
        attempts[key].append(time.time())
        email = credentials.email.strip().lower()
        if "@" not in email or not credentials.name.strip():
            raise HTTPException(422, "Enter a valid email and name")
        if action == "register":
            if email == "sample@securellm.local":
                raise HTTPException(409, "This address is reserved for the sample account")
            salt = secrets.token_hex(32)
            password_hash = hashlib.pbkdf2_hmac("sha256", credentials.password.encode(), bytes.fromhex(salt), 310000).hex()
            try:
                with engine.begin() as conn:
                    conn.execute(insert(users).values(email=email, name=credentials.name.strip(), salt=salt, password_hash=password_hash))
            except IntegrityError:
                raise HTTPException(409, "This email already has an account. Sign in instead.") from None
        else:
            with engine.connect() as conn:
                row = conn.execute(select(users).where(users.c.email == email)).first()
            salt = row.salt if row else "00" * 32
            candidate = hashlib.pbkdf2_hmac("sha256", credentials.password.encode(), bytes.fromhex(salt), 310000).hex()
            if not row or not hmac.compare_digest(candidate, row.password_hash):
                raise HTTPException(401, "Email or password is incorrect")
        establish(response, email, request)
        return {"user": identity_from_email(email)}

    def identity_from_email(email):
        with engine.connect() as conn:
            row = conn.execute(select(users.c.email, users.c.name).where(users.c.email == email)).one()
            return {"email": row.email, "name": row.name}

    @app.post("/auth/logout")
    def logout(request: Request, response: Response):
        with engine.begin() as conn:
            conn.execute(delete(sessions).where(sessions.c.token_hash == digest(request.cookies.get("securellm_session", ""))))
        response.delete_cookie("securellm_session")
        return {"ok": True}
