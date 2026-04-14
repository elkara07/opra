"""Voice API endpoints: SIP incoming, call records, DID management, agent status."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_tenant, require_min_role, verify_service_key
from app.models.audit import DIDMapping
from app.models.call_record import CallRecord
from app.models.tenant import Tenant
from app.models.user import User
from app.modules.voice.providers import (
    STT_PROVIDERS, TTS_PROVIDERS, LLM_PROVIDERS, get_available_providers,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# SIP Incoming (called by LiveKit SIP bridge)
# ---------------------------------------------------------------------------

class SIPIncomingRequest(BaseModel):
    call_sid: str
    caller_number: str
    did_number: str


@router.post("/sip/incoming")
async def sip_incoming(
    body: SIPIncomingRequest,
    _=Depends(verify_service_key),
    db: AsyncSession = Depends(get_db),
):
    """Handle incoming SIP call from LiveKit SIP bridge.

    1. Resolve tenant from DID
    2. Create call record
    3. Return voice agent config for the Pipecat agent to use
    """
    from app.modules.voice.sip_handler import resolve_tenant_from_did

    tenant_data = await resolve_tenant_from_did(db, body.did_number)
    if not tenant_data:
        return {"action": "reject", "reason": "unknown_did"}

    # Create call record
    record = CallRecord(
        tenant_id=UUID(tenant_data["tenant_id"]),
        call_sid=body.call_sid,
        caller_number=body.caller_number,
        did_number=body.did_number,
        direction="inbound",
        status="ringing",
    )
    db.add(record)
    await db.flush()

    return {
        "action": "accept",
        "tenant_id": tenant_data["tenant_id"],
        "tenant_name": tenant_data["tenant_name"],
        "project_id": tenant_data.get("project_id"),
        "call_record_id": str(record.id),
    }


# ---------------------------------------------------------------------------
# Call Records
# ---------------------------------------------------------------------------

class CallRecordResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    ticket_id: UUID | None
    call_sid: str
    caller_number: str | None
    did_number: str | None
    direction: str
    status: str
    duration_seconds: int | None
    transcript: str | None
    stt_provider: str | None
    tts_provider: str | None
    llm_provider: str | None
    created_at: str | None

    model_config = {"from_attributes": True}


@router.get("/calls")
async def list_calls(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(require_min_role("viewer")),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    count_result = await db.execute(
        select(func.count(CallRecord.id)).where(CallRecord.tenant_id == tenant.id)
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(CallRecord)
        .where(CallRecord.tenant_id == tenant.id)
        .order_by(CallRecord.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    calls = list(result.scalars().all())
    return {"items": calls, "total": total, "page": page, "size": size}


@router.get("/calls/{call_id}", response_model=CallRecordResponse)
async def get_call(
    call_id: UUID,
    current_user: User = Depends(require_min_role("viewer")),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CallRecord).where(
            CallRecord.id == call_id,
            CallRecord.tenant_id == tenant.id,
        )
    )
    call = result.scalar_one_or_none()
    if not call:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("CallRecord")
    return call


# ---------------------------------------------------------------------------
# DID Mappings
# ---------------------------------------------------------------------------

class DIDMappingCreate(BaseModel):
    did_number: str
    project_id: UUID | None = None
    description: str | None = None


class DIDMappingResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    did_number: str
    project_id: UUID | None
    description: str | None

    model_config = {"from_attributes": True}


@router.get("/did-mappings", response_model=list[DIDMappingResponse])
async def list_did_mappings(
    current_user: User = Depends(require_min_role("manager")),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DIDMapping).where(DIDMapping.tenant_id == tenant.id)
    )
    return list(result.scalars().all())


@router.post("/did-mappings", response_model=DIDMappingResponse, status_code=201)
async def create_did_mapping(
    body: DIDMappingCreate,
    current_user: User = Depends(require_min_role("tenant_admin")),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    from app.modules.voice.sip_handler import register_did_mapping
    return await register_did_mapping(
        db, tenant.id, body.did_number, body.project_id, body.description,
    )


# ---------------------------------------------------------------------------
# Provider Status
# ---------------------------------------------------------------------------

@router.get("/providers")
async def list_providers(
    current_user: User = Depends(require_min_role("viewer")),
):
    return {
        "stt": get_available_providers(STT_PROVIDERS),
        "tts": get_available_providers(TTS_PROVIDERS),
        "llm": get_available_providers(LLM_PROVIDERS),
    }


# ---------------------------------------------------------------------------
# Voice Configuration (per-tenant, stored in tenant.settings JSONB)
# ---------------------------------------------------------------------------

class VoiceConfigUpdate(BaseModel):
    stt_provider: str | None = None
    tts_provider: str | None = None
    llm_provider: str | None = None
    stt_fallback: str | None = None
    tts_fallback: str | None = None
    llm_fallback: str | None = None
    language: str | None = None
    # Turn detection
    min_endpointing_delay: int | None = None  # ms
    max_endpointing_delay: int | None = None  # ms
    interruption_mode: str | None = None  # eager, adaptive, conservative
    backchannel_threshold: int | None = None  # ms
    # Transfer & on-call
    transfer_phone: str | None = None  # PBX extension or phone to transfer calls
    transfer_ring_timeout: int | None = None  # seconds to wait before giving up
    oncall_email: str | None = None  # email to notify when transfer fails


class ApiKeyUpdate(BaseModel):
    key_name: str  # e.g. "DEEPGRAM_API_KEY", "ANTHROPIC_API_KEY", "MISTRAL_API_KEY"
    key_value: str


@router.get("/config")
async def get_voice_config(
    current_user: User = Depends(require_min_role("viewer")),
    tenant: Tenant = Depends(get_current_tenant),
):
    """Get tenant's voice pipeline configuration."""
    voice_cfg = (tenant.settings or {}).get("voice", {})
    return {
        "stt_provider": voice_cfg.get("stt_provider", "deepgram"),
        "tts_provider": voice_cfg.get("tts_provider", "openai"),
        "llm_provider": voice_cfg.get("llm_provider", "claude"),
        "stt_fallback": voice_cfg.get("stt_fallback", "groq"),
        "tts_fallback": voice_cfg.get("tts_fallback", "edge"),
        "llm_fallback": voice_cfg.get("llm_fallback", "groq"),
        "language": voice_cfg.get("language", "tr"),
        "min_endpointing_delay": voice_cfg.get("min_endpointing_delay", 500),
        "max_endpointing_delay": voice_cfg.get("max_endpointing_delay", 3000),
        "interruption_mode": voice_cfg.get("interruption_mode", "adaptive"),
        "backchannel_threshold": voice_cfg.get("backchannel_threshold", 300),
        "transfer_phone": voice_cfg.get("transfer", {}).get("phone", ""),
        "transfer_ring_timeout": voice_cfg.get("transfer", {}).get("ring_timeout", 30),
        "oncall_email": voice_cfg.get("oncall_email", ""),
    }


@router.put("/config")
async def update_voice_config(
    body: VoiceConfigUpdate,
    current_user: User = Depends(require_min_role("manager")),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Update tenant's voice pipeline configuration."""
    current_settings = tenant.settings or {}
    voice_cfg = current_settings.get("voice", {})
    for field, value in body.model_dump(exclude_unset=True).items():
        # Nested transfer config
        if field == "transfer_phone":
            transfer = voice_cfg.get("transfer", {})
            transfer["phone"] = value
            voice_cfg["transfer"] = transfer
        elif field == "transfer_ring_timeout":
            transfer = voice_cfg.get("transfer", {})
            transfer["ring_timeout"] = value
            voice_cfg["transfer"] = transfer
        else:
            voice_cfg[field] = value
    current_settings["voice"] = voice_cfg
    tenant.settings = current_settings
    # Force SQLAlchemy to detect JSONB mutation
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(tenant, "settings")
    await db.flush()
    return voice_cfg


@router.post("/api-keys")
async def save_api_key(
    body: ApiKeyUpdate,
    current_user: User = Depends(require_min_role("tenant_admin")),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Save an API key (encrypted) in tenant settings."""
    from app.core.security import encrypt_value
    current_settings = tenant.settings or {}
    api_keys = current_settings.get("api_keys", {})
    api_keys[body.key_name] = encrypt_value(body.key_value)
    current_settings["api_keys"] = api_keys
    tenant.settings = current_settings
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(tenant, "settings")
    await db.flush()
    return {"key_name": body.key_name, "status": "saved"}


@router.get("/api-keys")
async def list_api_keys(
    current_user: User = Depends(require_min_role("manager")),
    tenant: Tenant = Depends(get_current_tenant),
):
    """List configured API keys (names only, not values)."""
    api_keys = (tenant.settings or {}).get("api_keys", {})
    return {
        name: {"configured": True, "masked": "****" + name[-4:]}
        for name in api_keys
    }


# ---------------------------------------------------------------------------
# LiveKit Integration
# ---------------------------------------------------------------------------

class LiveKitConfigUpdate(BaseModel):
    url: str | None = None
    api_key: str | None = None
    api_secret: str | None = None


@router.get("/livekit/config")
async def get_livekit_config(
    current_user: User = Depends(require_min_role("manager")),
    tenant: Tenant = Depends(get_current_tenant),
):
    """Get LiveKit configuration (secret masked)."""
    from app.modules.voice.livekit_service import _get_livekit_credentials
    url, api_key, api_secret = _get_livekit_credentials(tenant)
    return {
        "url": url,
        "api_key": api_key,
        "api_secret_configured": bool(api_secret),
    }


@router.put("/livekit/config")
async def update_livekit_config(
    body: LiveKitConfigUpdate,
    current_user: User = Depends(require_min_role("tenant_admin")),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Update LiveKit configuration."""
    from app.core.security import encrypt_value
    from sqlalchemy.orm.attributes import flag_modified

    current_settings = tenant.settings or {}
    voice_cfg = current_settings.get("voice", {})
    livekit_cfg = voice_cfg.get("livekit", {})

    if body.url is not None:
        livekit_cfg["url"] = body.url
    if body.api_key is not None:
        livekit_cfg["api_key"] = body.api_key
    if body.api_secret is not None:
        # Store encrypted
        api_keys = current_settings.get("api_keys", {})
        api_keys["LIVEKIT_API_SECRET"] = encrypt_value(body.api_secret)
        current_settings["api_keys"] = api_keys

    voice_cfg["livekit"] = livekit_cfg
    current_settings["voice"] = voice_cfg
    tenant.settings = current_settings
    flag_modified(tenant, "settings")
    await db.flush()

    return {
        "url": livekit_cfg.get("url", ""),
        "api_key": livekit_cfg.get("api_key", ""),
        "api_secret_configured": bool(body.api_secret or current_settings.get("api_keys", {}).get("LIVEKIT_API_SECRET")),
        "status": "saved",
    }


@router.post("/livekit/test")
async def test_livekit_connection(
    current_user: User = Depends(require_min_role("manager")),
    tenant: Tenant = Depends(get_current_tenant),
):
    """Test LiveKit server connectivity."""
    from app.modules.voice.livekit_service import _get_livekit_credentials
    import httpx

    url, api_key, api_secret = _get_livekit_credentials(tenant)
    if not url:
        return {"status": "error", "message": "LiveKit URL not configured"}
    if not api_key or not api_secret:
        return {"status": "error", "message": "LiveKit API key/secret not configured"}

    http_url = url.replace("ws://", "http://").replace("wss://", "https://")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(http_url)
        if resp.status_code < 500:
            return {"status": "ok", "message": f"LiveKit reachable at {url}", "http_status": resp.status_code}
        return {"status": "error", "message": f"LiveKit returned HTTP {resp.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/livekit/token")
async def create_livekit_token(
    current_user: User = Depends(require_min_role("viewer")),
    tenant: Tenant = Depends(get_current_tenant),
):
    """Create a LiveKit room + token for browser WebRTC connection."""
    from app.modules.voice.livekit_service import create_room_token, generate_room_name, _get_livekit_credentials

    url, _, _ = _get_livekit_credentials(tenant)
    room_name = generate_room_name()
    participant_name = f"user-{current_user.name}"

    try:
        token = create_room_token(room_name, participant_name, tenant=tenant)
    except ValueError as e:
        from app.core.exceptions import ValidationError
        raise ValidationError(str(e))

    return {
        "token": token,
        "room_name": room_name,
        "livekit_url": url,
        "participant_name": participant_name,
    }


class FullPipelineRequest(BaseModel):
    audio_base64: str
    context: dict | None = None
    language: str = "tr"


@router.post("/livekit/process")
async def livekit_pipeline_process(
    body: FullPipelineRequest,
    current_user: User = Depends(require_min_role("viewer")),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Full pipeline through LiveKit→Pipecat path: audio → STT → guardrail → LLM → TTS → audio.

    This simulates what the Pipecat agent does when connected to a LiveKit room.
    Browser sends audio (base64), gets back processed response with audio.
    """
    from app.modules.voice.agent_worker import agent_process_audio
    return await agent_process_audio(body.audio_base64, body.context, tenant, body.language)


# ---------------------------------------------------------------------------
# Individual Pipeline Test Endpoints
# ---------------------------------------------------------------------------

@router.post("/test-stt")
async def test_stt_endpoint(
    file: UploadFile = File(...),
    language: str = Query("tr"),
    current_user: User = Depends(require_min_role("viewer")),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Test STT: upload audio file → get transcript."""
    from app.modules.voice.test_pipeline import test_stt
    audio_bytes = await file.read()
    return await test_stt(audio_bytes, tenant, language)


class LLMTestRequest(BaseModel):
    text: str
    system_prompt: str | None = None


@router.post("/test-llm")
async def test_llm_endpoint(
    body: LLMTestRequest,
    current_user: User = Depends(require_min_role("viewer")),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Test LLM: send text → get AI response."""
    from app.modules.voice.test_pipeline import test_llm
    return await test_llm(body.text, tenant, body.system_prompt)


class ConversationTurnRequest(BaseModel):
    text: str
    context: dict | None = None  # Previous ConversationContext state


# In-memory conversation store (per session, for test only)
_test_conversations: dict[str, "ConversationContext"] = {}


@router.post("/test-conversation")
async def test_conversation_turn(
    body: ConversationTurnRequest,
    current_user: User = Depends(require_min_role("viewer")),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Managed conversation turn with guardrails and field extraction.

    Send user text + previous context → get agent response + updated context.
    First call without context starts a new conversation.
    """
    from app.modules.voice.conversation import (
        ConversationContext, ConvState, check_guardrails,
        build_system_prompt, process_llm_response, REQUIRED_FIELDS,
    )
    from app.modules.voice.test_pipeline import test_llm, test_tts

    # Restore or create context
    if body.context:
        ctx = ConversationContext(
            state=ConvState(body.context.get("state", "greeting")),
            turn_count=body.context.get("turn_count", 0),
            language=body.context.get("language", "tr"),
            fields=body.context.get("fields", {}),
            history=body.context.get("history", []),
            guardrail_warnings=body.context.get("guardrail_warnings", 0),
            confirmed=body.context.get("confirmed", False),
        )
    else:
        voice_cfg = (tenant.settings or {}).get("voice", {})
        ctx = ConversationContext(language=voice_cfg.get("language", "tr"))

    # First turn: generate greeting
    if ctx.turn_count == 0 and not body.text.strip():
        greeting = "Hoş geldiniz, 7/24 destek hattına ulaştınız. Size nasıl yardımcı olabilirim?" if ctx.language == "tr" else "Welcome to the 24/7 support line. How can I help you?"
        ctx.state = ConvState.COLLECT
        ctx.add_turn("assistant", greeting)

        # TTS for greeting
        tts_result = await test_tts(greeting, tenant, ctx.language)

        return {
            "agent_text": greeting,
            "context": ctx.to_dict(),
            "guardrail": {"safe": True},
            "extracted_fields": {},
            "tts": {
                "audio_base64": tts_result.get("audio_base64"),
                "content_type": tts_result.get("content_type"),
                "provider": tts_result.get("provider"),
                "latency_ms": tts_result.get("latency_ms"),
            } if not tts_result.get("error") else None,
        }

    # Guardrail check
    guardrail = check_guardrails(body.text, ctx)
    if not guardrail["safe"]:
        redirect_text = guardrail["message"]
        ctx.add_turn("user", body.text)
        ctx.add_turn("assistant", redirect_text)

        tts_result = await test_tts(redirect_text, tenant, ctx.language)

        return {
            "agent_text": redirect_text,
            "context": ctx.to_dict(),
            "guardrail": guardrail,
            "extracted_fields": {},
            "tts": {
                "audio_base64": tts_result.get("audio_base64"),
                "content_type": tts_result.get("content_type"),
            } if not tts_result.get("error") else None,
        }

    # Add user turn
    ctx.add_turn("user", body.text)

    # Build prompt and call LLM
    system_prompt = build_system_prompt(ctx, tenant.name)

    # Send conversation history to LLM
    history_for_llm = ctx.history[-10:]  # Keep last 10 turns for context
    combined_text = "\n".join(f"{'User' if m['role']=='user' else 'Agent'}: {m['content']}" for m in history_for_llm)

    llm_result = await test_llm(body.text, tenant, system_prompt)

    if llm_result.get("error"):
        return {
            "agent_text": None,
            "error": llm_result["error"],
            "context": ctx.to_dict(),
            "guardrail": guardrail,
        }

    # Process response: extract fields, detect confirmation
    processed = process_llm_response(llm_result["response"], ctx)

    agent_text = processed["text"]
    transfer_info = None

    # --- Post-confirmation flow: CREATE → TRANSFER → (fail) → NOTIFY ---
    if ctx.state == ConvState.TRANSFER:
        # Ticket created, now attempt transfer to live agent
        transfer_result = await _attempt_transfer(tenant, ctx)
        transfer_info = transfer_result

        if transfer_result["reached"]:
            agent_text = (agent_text + " " if agent_text else "") + \
                ("Sizi şimdi temsilciye aktarıyorum." if ctx.language == "tr" else "Transferring you to an agent now.")
        else:
            # Transfer failed → notify on-call team
            ctx.state = ConvState.TRANSFER_FAILED
            await _notify_oncall(tenant, ctx, db)
            agent_text = (
                "Şu anda temsilciye ulaşamadık. Nöbetçi ekibe bildirim gönderildi, "
                "en kısa sürede sizi arayacaklar. Ticket numaranız kayıtlıdır."
            ) if ctx.language == "tr" else (
                "We couldn't reach an agent right now. The on-call team has been notified "
                "and will call you back shortly. Your ticket number is on file."
            )

    ctx.add_turn("assistant", agent_text)

    # Generate TTS
    tts_result = await test_tts(agent_text, tenant, ctx.language)

    return {
        "agent_text": agent_text,
        "context": ctx.to_dict(),
        "guardrail": guardrail,
        "extracted_fields": processed["extracted_fields"],
        "confirmed": processed["confirmed"],
        "transfer": transfer_info,
        "llm": {
            "provider": llm_result.get("provider"),
            "latency_ms": llm_result.get("latency_ms"),
            "tokens": llm_result.get("tokens"),
        },
        "tts": {
            "audio_base64": tts_result.get("audio_base64"),
            "content_type": tts_result.get("content_type"),
            "provider": tts_result.get("provider"),
            "latency_ms": tts_result.get("latency_ms"),
        } if not tts_result.get("error") else None,
    }


async def _attempt_transfer(tenant, ctx) -> dict:
    """Attempt to transfer call to a live agent.

    In production: SIP REFER to PBX queue, or LiveKit room invite.
    For now: check if any on-call agent is configured and simulate.
    """
    voice_cfg = (tenant.settings or {}).get("voice", {})
    transfer_cfg = voice_cfg.get("transfer", {})
    transfer_phone = transfer_cfg.get("phone")  # e.g. PBX extension or phone number
    ring_timeout = transfer_cfg.get("ring_timeout", 30)

    if not transfer_phone:
        # No transfer target configured
        return {"reached": False, "reason": "no_transfer_target_configured"}

    # In production: initiate SIP transfer via LiveKit or Twilio
    # For test: simulate — always fail (so we can test the fallback)
    # TODO: Replace with actual SIP REFER / LiveKit room transfer
    return {"reached": False, "reason": "agent_unavailable", "phone": transfer_phone, "timeout": ring_timeout}


async def _notify_oncall(tenant, ctx, db):
    """Send notification to on-call team when transfer fails.

    Sends email with caller info + ticket details to configured on-call address.
    """
    voice_cfg = (tenant.settings or {}).get("voice", {})
    oncall_email = voice_cfg.get("oncall_email")  # e.g. oncall@company.com
    caller_phone = ctx.fields.get("contact_phone", "unknown")
    caller_name = ctx.fields.get("caller_name", "unknown")
    company = ctx.fields.get("company_or_project", "unknown")
    issue = ctx.fields.get("issue_summary", "unknown")
    urgency = ctx.fields.get("urgency", "unknown")

    if not oncall_email:
        # Log but continue — notification is best-effort
        return

    # Queue email notification via Celery
    try:
        from workers.tasks.notification_tasks import send_notification
        subject = f"[OPRA] Transfer Failed — {urgency.upper()} — {caller_name} / {company}"
        body = (
            f"Temsilciye aktarma başarısız oldu.\n\n"
            f"Arayan: {caller_name}\n"
            f"Firma/Proje: {company}\n"
            f"Telefon: {caller_phone}\n"
            f"Sorun: {issue}\n"
            f"Aciliyet: {urgency}\n"
            f"Etkilenen Sistem: {ctx.fields.get('affected_system', 'unknown')}\n\n"
            f"Lütfen en kısa sürede geri arayın."
        )
        send_notification.delay(
            str(tenant.id), "email", oncall_email, subject, body,
        )
    except Exception:
        pass  # Best effort — don't break the call flow


class TTSTestRequest(BaseModel):
    text: str
    language: str = "tr"


@router.post("/test-tts")
async def test_tts_endpoint(
    body: TTSTestRequest,
    current_user: User = Depends(require_min_role("viewer")),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Test TTS: send text → get audio (base64)."""
    from app.modules.voice.test_pipeline import test_tts
    return await test_tts(body.text, tenant, body.language)


@router.post("/test-full")
async def test_full_pipeline(
    file: UploadFile = File(...),
    language: str = Query("tr"),
    current_user: User = Depends(require_min_role("viewer")),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Full pipeline test: audio → STT → LLM → TTS → audio response."""
    from app.modules.voice.test_pipeline import test_stt, test_llm, test_tts
    import time

    t0 = time.monotonic()
    audio_bytes = await file.read()

    # Step 1: STT
    stt_result = await test_stt(audio_bytes, tenant, language)
    if stt_result.get("error"):
        return {"step": "stt", "error": stt_result["error"]}

    transcript = stt_result.get("transcript", "")
    if not transcript:
        return {"step": "stt", "error": "Empty transcript — no speech detected"}

    # Step 2: LLM
    llm_result = await test_llm(transcript, tenant)
    if llm_result.get("error"):
        return {"step": "llm", "error": llm_result["error"], "stt": stt_result}

    response_text = llm_result.get("response", "")

    # Step 3: TTS
    tts_result = await test_tts(response_text, tenant, language)
    if tts_result.get("error"):
        return {"step": "tts", "error": tts_result["error"], "stt": stt_result, "llm": llm_result}

    total_latency = round((time.monotonic() - t0) * 1000)

    return {
        "success": True,
        "total_latency_ms": total_latency,
        "stt": stt_result,
        "llm": llm_result,
        "tts": {
            "audio_base64": tts_result.get("audio_base64"),
            "content_type": tts_result.get("content_type"),
            "provider": tts_result.get("provider"),
            "latency_ms": tts_result.get("latency_ms"),
        },
    }


@router.get("/agent/status")
async def agent_status(
    tenant: Tenant = Depends(get_current_tenant),
):
    """Voice agent health check with active provider info."""
    voice_cfg = (tenant.settings or {}).get("voice", {})
    return {
        "status": "ok",
        "stt_provider": voice_cfg.get("stt_provider", "deepgram"),
        "tts_provider": voice_cfg.get("tts_provider", "openai"),
        "llm_provider": voice_cfg.get("llm_provider", "claude"),
    }
