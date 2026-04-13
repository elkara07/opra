"""System topology and pipeline health endpoints."""

from __future__ import annotations

import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import require_min_role
from app.models.user import User

router = APIRouter()


async def _check_postgres(db: AsyncSession) -> dict:
    try:
        t0 = time.monotonic()
        await db.execute(text("SELECT 1"))
        latency = round((time.monotonic() - t0) * 1000, 1)
        return {"status": "ok", "latency_ms": latency, "error": None}
    except Exception as e:
        return {"status": "error", "latency_ms": None, "error": str(e)}


async def _check_redis() -> dict:
    try:
        from app.core.events import get_redis
        t0 = time.monotonic()
        r = await get_redis()
        await r.ping()
        latency = round((time.monotonic() - t0) * 1000, 1)
        return {"status": "ok", "latency_ms": latency, "error": None}
    except Exception as e:
        return {"status": "error", "latency_ms": None, "error": str(e)}


async def _check_celery() -> dict:
    try:
        from workers.celery_app import app as celery_app
        insp = celery_app.control.inspect(timeout=3)
        active = insp.active()
        if active is None:
            return {"status": "warning", "latency_ms": None, "error": "No workers responding"}
        worker_count = len(active)
        return {"status": "ok", "latency_ms": None, "error": None, "workers": worker_count}
    except Exception as e:
        return {"status": "error", "latency_ms": None, "error": str(e)}


async def _check_livekit() -> dict:
    try:
        import httpx
        t0 = time.monotonic()
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(settings.livekit_url.replace("ws://", "http://").replace("wss://", "https://"))
            latency = round((time.monotonic() - t0) * 1000, 1)
        if r.status_code < 500:
            return {"status": "ok", "latency_ms": latency, "error": None}
        return {"status": "error", "latency_ms": latency, "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"status": "error", "latency_ms": None, "error": str(e)}


async def _check_graph_api() -> dict:
    if not settings.ms_graph_client_id:
        return {"status": "not_configured", "latency_ms": None, "error": "MS Graph credentials not set"}
    try:
        from app.modules.email.graph_client import _get_access_token
        t0 = time.monotonic()
        await _get_access_token()
        latency = round((time.monotonic() - t0) * 1000, 1)
        return {"status": "ok", "latency_ms": latency, "error": None}
    except Exception as e:
        return {"status": "error", "latency_ms": None, "error": str(e)}


async def _check_jira(db: AsyncSession) -> dict:
    from sqlalchemy import select
    from app.models.jira_config import JiraConfig
    result = await db.execute(select(JiraConfig).limit(1))
    config = result.scalar_one_or_none()
    if not config:
        return {"status": "not_configured", "latency_ms": None, "error": "Jira not configured"}
    if not config.sync_enabled:
        return {"status": "disabled", "latency_ms": None, "error": None}
    last = config.last_sync_at
    if last:
        age_min = (datetime.now(timezone.utc) - last).total_seconds() / 60
        if age_min > 30:
            return {"status": "warning", "latency_ms": None, "error": f"Last sync {int(age_min)}m ago"}
    return {"status": "ok", "latency_ms": None, "error": None}


async def _check_ldap(db: AsyncSession) -> dict:
    from sqlalchemy import select
    from app.models.ldap_config import LDAPConfig
    result = await db.execute(select(LDAPConfig).limit(1))
    config = result.scalar_one_or_none()
    if not config:
        return {"status": "not_configured", "latency_ms": None, "error": "LDAP not configured"}
    if not config.sync_enabled:
        return {"status": "disabled", "latency_ms": None, "error": None}
    return {"status": "ok", "latency_ms": None, "error": None}


def _check_stt_provider() -> dict:
    if settings.deepgram_api_key:
        return {"status": "ok", "provider": "deepgram", "error": None}
    if settings.openai_api_key:
        return {"status": "ok", "provider": "openai_whisper", "error": None}
    return {"status": "not_configured", "provider": None, "error": "No STT API key configured"}


def _check_llm_provider() -> dict:
    if settings.anthropic_api_key:
        return {"status": "ok", "provider": "claude", "error": None}
    if settings.openai_api_key:
        return {"status": "ok", "provider": "openai", "error": None}
    return {"status": "not_configured", "provider": None, "error": "No LLM API key configured"}


def _check_tts_provider() -> dict:
    if settings.openai_api_key:
        return {"status": "ok", "provider": "openai_tts", "error": None}
    if settings.elevenlabs_api_key:
        return {"status": "ok", "provider": "elevenlabs", "error": None}
    return {"status": "warning", "provider": "edge_free", "error": "Using free Edge TTS (no API key needed)"}


@router.get("/health")
async def get_system_health(
    current_user: User = Depends(require_min_role("viewer")),
    db: AsyncSession = Depends(get_db),
):
    """Simplified health check returning service statuses for SystemHealthPage."""
    import platform

    pg = await _check_postgres(db)
    rd = await _check_redis()
    lk = await _check_livekit()

    services = [
        {"name": "PostgreSQL", "status": pg["status"], "latency": pg.get("latency_ms"), "error": pg.get("error")},
        {"name": "Redis", "status": rd["status"], "latency": rd.get("latency_ms"), "error": rd.get("error")},
        {"name": "LiveKit", "status": lk["status"], "latency": lk.get("latency_ms"), "error": lk.get("error")},
        {"name": "Celery", "status": "ok", "latency": None, "error": None},
    ]

    overall = "ok" if all(s["status"] == "ok" for s in services[:2]) else "degraded"

    return {
        "status": overall,
        "services": services,
        "uptime": int(time.time() - _start_time),
        "version": "0.1.0",
        "python": platform.python_version(),
    }


_start_time = time.time()


@router.get("/topology")
async def get_topology(
    current_user: User = Depends(require_min_role("viewer")),
    db: AsyncSession = Depends(get_db),
):
    """Return full system topology with health status for each component.

    Each node has: id, label, group, status (ok/warning/error/not_configured), error, latency_ms.
    Edges define the pipeline flow between nodes.
    """
    # Check all components
    pg = await _check_postgres(db)
    rd = await _check_redis()
    lk = await _check_livekit()
    graph = await _check_graph_api()
    jira = await _check_jira(db)
    ldap_status = await _check_ldap(db)
    stt = _check_stt_provider()
    llm = _check_llm_provider()
    tts = _check_tts_provider()

    nodes = [
        # Infrastructure
        {"id": "postgres", "label": "PostgreSQL", "group": "infra", **pg},
        {"id": "redis", "label": "Redis", "group": "infra", **rd},

        # Voice pipeline
        {"id": "pbx", "label": "PBX / Santral", "group": "voice", "status": "ok", "error": None, "latency_ms": None},
        {"id": "sip_bridge", "label": "LiveKit SIP Bridge", "group": "voice", **lk},
        {"id": "livekit", "label": "LiveKit Server", "group": "voice", **lk},
        {"id": "pipecat", "label": "Pipecat Agent", "group": "voice", "status": "ok", "error": None, "latency_ms": None},
        {"id": "stt", "label": f"STT ({stt.get('provider', '?')})", "group": "voice", "status": stt["status"], "error": stt["error"], "latency_ms": None},
        {"id": "llm", "label": f"LLM ({llm.get('provider', '?')})", "group": "voice", "status": llm["status"], "error": llm["error"], "latency_ms": None},
        {"id": "tts", "label": f"TTS ({tts.get('provider', '?')})", "group": "voice", "status": tts["status"], "error": tts["error"], "latency_ms": None},

        # Ticket pipeline
        {"id": "email_ingest", "label": "Email (Graph API)", "group": "ticket", **graph},
        {"id": "phone_ingest", "label": "Phone (Voice)", "group": "ticket", "status": "ok", "error": None, "latency_ms": None},
        {"id": "ticket_engine", "label": "Ticket Engine", "group": "ticket", "status": "ok", "error": None, "latency_ms": None},
        {"id": "sla_engine", "label": "SLA Engine", "group": "ticket", "status": "ok", "error": None, "latency_ms": None},
        {"id": "escalation_engine", "label": "Escalation Engine", "group": "ticket", "status": "ok", "error": None, "latency_ms": None},
        {"id": "notification", "label": "Notifications", "group": "ticket", "status": "ok", "error": None, "latency_ms": None},

        # Integrations
        {"id": "jira", "label": "Jira Cloud", "group": "integration", **jira},
        {"id": "ldap", "label": "LDAP / AD", "group": "integration", **ldap_status},
        {"id": "minio", "label": "MinIO (Storage)", "group": "infra", "status": "ok", "error": None, "latency_ms": None},
    ]

    edges = [
        # Voice pipeline flow
        {"from": "pbx", "to": "sip_bridge", "label": "SIP INVITE"},
        {"from": "sip_bridge", "to": "livekit", "label": "WebRTC"},
        {"from": "livekit", "to": "pipecat", "label": "Audio stream"},
        {"from": "pipecat", "to": "stt", "label": "Audio"},
        {"from": "stt", "to": "llm", "label": "Transcript"},
        {"from": "llm", "to": "tts", "label": "Response text"},
        {"from": "tts", "to": "livekit", "label": "Audio response"},
        {"from": "pipecat", "to": "ticket_engine", "label": "create_ticket()"},

        # Ticket pipeline flow
        {"from": "email_ingest", "to": "ticket_engine", "label": "Parsed email"},
        {"from": "phone_ingest", "to": "ticket_engine", "label": "Voice ticket"},
        {"from": "ticket_engine", "to": "sla_engine", "label": "Apply SLA"},
        {"from": "sla_engine", "to": "escalation_engine", "label": "Check thresholds"},
        {"from": "escalation_engine", "to": "notification", "label": "Alerts"},
        {"from": "ticket_engine", "to": "jira", "label": "Sync"},
        {"from": "ticket_engine", "to": "notification", "label": "Confirmation"},
        {"from": "notification", "to": "email_ingest", "label": "Send email"},

        # Data stores
        {"from": "ticket_engine", "to": "postgres", "label": "CRUD"},
        {"from": "sla_engine", "to": "redis", "label": "Cache"},
        {"from": "ldap", "to": "postgres", "label": "User sync"},
        {"from": "ticket_engine", "to": "minio", "label": "Attachments"},
    ]

    return {
        "nodes": nodes,
        "edges": edges,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/topology/{node_id}")
async def get_node_detail(
    node_id: str,
    current_user: User = Depends(require_min_role("viewer")),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed status and configuration for a specific topology node."""
    detail_handlers = {
        "postgres": lambda: _detail_postgres(db),
        "redis": lambda: _detail_redis(),
        "stt": lambda: _detail_stt(),
        "llm": lambda: _detail_llm(),
        "tts": lambda: _detail_tts(),
        "jira": lambda: _detail_jira(db),
        "ldap": lambda: _detail_ldap(db),
        "sla_engine": lambda: _detail_sla(db),
        "escalation_engine": lambda: _detail_escalation(db),
        "email_ingest": lambda: _detail_email(db),
        "livekit": lambda: _detail_livekit(),
        "sip_bridge": lambda: _detail_livekit(),
        "pipecat": lambda: _detail_pipecat(),
        "pbx": lambda: _detail_pbx(),
        "phone_ingest": lambda: _detail_voice_ingest(),
        "ticket_engine": lambda: _detail_ticket_engine(db),
        "notification": lambda: _detail_notification(db),
        "minio": lambda: _detail_minio(),
    }

    handler = detail_handlers.get(node_id)
    if handler:
        return await handler()

    return {"node_id": node_id, "detail": "No extended detail available", "config_url": "/system"}


async def _detail_postgres(db):
    from sqlalchemy import text
    result = await db.execute(text("SELECT count(*) FROM information_schema.tables WHERE table_schema='public'"))
    table_count = result.scalar()
    pg = await _check_postgres(db)
    return {
        "node_id": "postgres",
        "tables": table_count,
        "status": pg["status"],
        "latency_ms": pg.get("latency_ms"),
        "description": "Primary data store for tickets, users, SLA configs, and all transactional data.",
        "config_url": "/system",
    }


async def _detail_redis():
    try:
        from app.core.events import get_redis
        r = await get_redis()
        info = await r.info("memory")
        rd = await _check_redis()
        return {
            "node_id": "redis",
            "used_memory": info.get("used_memory_human"),
            "status": rd["status"],
            "latency_ms": rd.get("latency_ms"),
            "description": "Cache, Celery broker, PubSub for SSE events, session store.",
            "config_url": "/system",
        }
    except Exception as e:
        return {"node_id": "redis", "error": str(e), "config_url": "/system"}


async def _detail_stt():
    from app.modules.voice.providers import STT_PROVIDERS, get_available_providers
    return {"node_id": "stt", "providers": get_available_providers(STT_PROVIDERS), "config_url": "/settings/voice"}


async def _detail_llm():
    from app.modules.voice.providers import LLM_PROVIDERS, get_available_providers
    return {"node_id": "llm", "providers": get_available_providers(LLM_PROVIDERS), "config_url": "/settings/voice"}


async def _detail_tts():
    from app.modules.voice.providers import TTS_PROVIDERS, get_available_providers
    return {"node_id": "tts", "providers": get_available_providers(TTS_PROVIDERS), "config_url": "/settings/voice"}


async def _detail_jira(db):
    from sqlalchemy import select
    from app.models.jira_config import JiraConfig
    result = await db.execute(select(JiraConfig).limit(1))
    config = result.scalar_one_or_none()
    if not config:
        return {"node_id": "jira", "configured": False, "config_url": "/settings/jira"}
    return {
        "node_id": "jira", "configured": True, "sync_enabled": config.sync_enabled,
        "site_url": config.site_url, "last_sync": str(config.last_sync_at),
        "config_url": "/settings/jira",
    }


async def _detail_ldap(db):
    from sqlalchemy import select
    from app.models.ldap_config import LDAPConfig
    result = await db.execute(select(LDAPConfig).limit(1))
    config = result.scalar_one_or_none()
    if not config:
        return {"node_id": "ldap", "configured": False, "config_url": "/settings/ldap"}
    return {
        "node_id": "ldap", "configured": True, "sync_enabled": config.sync_enabled,
        "server_url": config.server_url, "last_sync": str(config.last_sync_at),
        "config_url": "/settings/ldap",
    }


async def _detail_sla(db):
    from sqlalchemy import select, func
    from app.models.sla import SLAConfig
    result = await db.execute(select(func.count(SLAConfig.id)))
    count = result.scalar()
    return {"node_id": "sla_engine", "config_count": count, "config_url": "/settings/sla"}


async def _detail_escalation(db):
    from sqlalchemy import select, func
    from app.models.escalation import EscalationRule
    result = await db.execute(select(func.count(EscalationRule.id)))
    count = result.scalar()
    return {"node_id": "escalation_engine", "rule_count": count, "config_url": "/settings/escalation"}


async def _detail_email(db):
    from sqlalchemy import select, func
    from app.models.email_message import EmailMailbox
    result = await db.execute(select(func.count(EmailMailbox.id)))
    count = result.scalar()
    return {"node_id": "email_ingest", "mailbox_count": count, "config_url": "/settings/email"}


async def _detail_livekit():
    lk = await _check_livekit()
    return {
        "node_id": "livekit",
        "livekit_url": settings.livekit_url,
        "status": lk["status"],
        "latency_ms": lk.get("latency_ms"),
        "error": lk.get("error"),
        "description": "LiveKit provides WebRTC media transport and SIP bridge for voice calls.",
        "config_url": "/settings/voice",
        "troubleshooting": [
            "Verify LIVEKIT_URL environment variable is correct",
            "Check if livekit-server container is running: docker ps | grep livekit",
            "Check port 7880 is accessible from the API server",
            "Review livekit/livekit.yaml configuration file",
        ],
    }


async def _detail_pipecat():
    stt = _check_stt_provider()
    llm = _check_llm_provider()
    tts = _check_tts_provider()
    return {
        "node_id": "pipecat",
        "description": "Pipecat voice agent handles STT→LLM→TTS pipeline for phone ticket intake.",
        "stt_status": stt["status"],
        "stt_provider": stt.get("provider"),
        "llm_status": llm["status"],
        "llm_provider": llm.get("provider"),
        "tts_status": tts["status"],
        "tts_provider": tts.get("provider"),
        "config_url": "/settings/voice",
    }


async def _detail_pbx():
    return {
        "node_id": "pbx",
        "description": "External PBX/Santral connected via SIP trunk to LiveKit SIP Bridge.",
        "sip_port": 5060,
        "protocol": "SIP (UDP/TCP)",
        "config_url": "/settings/voice",
        "troubleshooting": [
            "Verify SIP trunk registration on PBX side",
            "Check DID mappings are configured: Settings → Voice → DID Mappings",
            "Test SIP connectivity: telnet livekit-sip 5060",
        ],
    }


async def _detail_voice_ingest():
    from sqlalchemy import select, func
    return {
        "node_id": "phone_ingest",
        "description": "Phone calls enter via PBX→SIP→LiveKit→Pipecat and create tickets.",
        "config_url": "/settings/voice",
    }


async def _detail_ticket_engine(db):
    from sqlalchemy import select, func
    from app.models.ticket import Ticket
    total = (await db.execute(select(func.count(Ticket.id)))).scalar() or 0
    active = (await db.execute(
        select(func.count(Ticket.id)).where(Ticket.status.notin_(["closed", "cancelled"]))
    )).scalar() or 0
    return {
        "node_id": "ticket_engine",
        "total_tickets": total,
        "active_tickets": active,
        "description": "Core ticket CRUD, ITIL state machine, assignment, SLA integration.",
        "config_url": "/tickets",
    }


async def _detail_notification(db):
    from sqlalchemy import select, func
    from app.models.notification import NotificationLog
    total = (await db.execute(select(func.count(NotificationLog.id)))).scalar() or 0
    return {
        "node_id": "notification",
        "total_sent": total,
        "description": "Email/SMS notification dispatch via Microsoft Graph and other channels.",
        "config_url": "/settings/email",
    }


async def _detail_minio():
    return {
        "node_id": "minio",
        "endpoint": settings.minio_endpoint,
        "bucket_attachments": settings.minio_bucket_attachments,
        "bucket_recordings": settings.minio_bucket_recordings,
        "use_ssl": settings.minio_use_ssl,
        "description": "S3-compatible object storage for email attachments and call recordings.",
        "config_url": "/system",
    }
