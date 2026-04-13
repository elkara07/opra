"""CallCenter Ticket Management System — FastAPI Application."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from app.core.config import settings
from app.core.database import engine
from app.core.events import subscribe_events
from app.core.dependencies import get_current_user, get_current_tenant

# Module routers
from app.modules.auth.router import router as auth_router
from app.modules.tickets.router import router as tickets_router
from app.modules.contacts.router import router as contacts_router
from app.modules.sla.router import router as sla_router
from app.modules.escalation.router import router as escalation_router
from app.modules.email.router import router as email_router
from app.modules.voice.router import router as voice_router
from app.modules.jira.router import router as jira_router
from app.modules.ldap.router import router as ldap_router
from app.modules.reporting.router import router as reporting_router
from app.modules.system.router import router as system_router
from app.modules.projects.router import router as projects_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: OpenTelemetry
    from app.core.observability import setup_otel
    setup_otel(settings.app_name)
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title="CallCenter Ticket Management System",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Health endpoints
# ---------------------------------------------------------------------------

@app.get("/metrics")
async def metrics():
    from app.core.observability import get_metrics
    return Response(content=get_metrics(), media_type="text/plain; charset=utf-8")


@app.get("/health")
async def health():
    return {"status": "ok", "service": settings.app_name}


@app.get("/health/ready")
async def readiness():
    from sqlalchemy import text
    from app.core.database import async_session_factory
    from app.core.events import get_redis

    checks = {}
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"

    try:
        r = await get_redis()
        await r.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"

    all_ok = all(v == "ok" for v in checks.values())
    return JSONResponse(
        status_code=200 if all_ok else 503,
        content={"status": "ready" if all_ok else "degraded", "checks": checks},
    )


# ---------------------------------------------------------------------------
# SSE event stream
# ---------------------------------------------------------------------------

@app.get(f"{settings.api_v1_prefix}/events/stream")
async def event_stream(request: Request):
    """Server-Sent Events stream, tenant-scoped via JWT."""
    from fastapi import Depends
    # Inline auth check for SSE (can't use Depends in streaming)
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

    from app.core.security import decode_token
    from jose import JWTError
    try:
        payload = decode_token(auth_header[7:])
        tenant_id = payload.get("tenant_id")
        if not tenant_id:
            return JSONResponse(status_code=403, content={"detail": "No tenant"})
    except JWTError:
        return JSONResponse(status_code=401, content={"detail": "Invalid token"})

    return StreamingResponse(
        subscribe_events(tenant_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# Register routers
# ---------------------------------------------------------------------------

app.include_router(auth_router, prefix=f"{settings.api_v1_prefix}/auth", tags=["Auth"])
app.include_router(tickets_router, prefix=f"{settings.api_v1_prefix}/tickets", tags=["Tickets"])
app.include_router(contacts_router, prefix=f"{settings.api_v1_prefix}/contacts", tags=["Contacts"])
app.include_router(sla_router, prefix=f"{settings.api_v1_prefix}/sla-configs", tags=["SLA"])
app.include_router(escalation_router, prefix=f"{settings.api_v1_prefix}/escalation-rules", tags=["Escalation"])
app.include_router(email_router, prefix=f"{settings.api_v1_prefix}/email", tags=["Email"])
app.include_router(voice_router, prefix=f"{settings.api_v1_prefix}/voice", tags=["Voice"])
app.include_router(jira_router, prefix=f"{settings.api_v1_prefix}/jira", tags=["Jira"])
app.include_router(ldap_router, prefix=f"{settings.api_v1_prefix}/ldap", tags=["LDAP"])
app.include_router(reporting_router, prefix=f"{settings.api_v1_prefix}/reports", tags=["Reports"])
app.include_router(system_router, prefix=f"{settings.api_v1_prefix}/system", tags=["System"])
app.include_router(projects_router, prefix=f"{settings.api_v1_prefix}/projects", tags=["Projects"])


# ---------------------------------------------------------------------------
# Global exception handler for DB connectivity
# ---------------------------------------------------------------------------

@app.exception_handler(OSError)
async def db_connection_error_handler(request: Request, exc: OSError):
    return JSONResponse(
        status_code=503,
        content={"detail": "Service temporarily unavailable — database connection failed"},
    )
