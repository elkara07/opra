"""Pipecat-style agent worker: joins LiveKit room, processes voice pipeline.

This worker:
1. Connects to LiveKit room via WebSocket
2. Receives audio from participant (browser)
3. Buffers audio → STT when silence detected
4. Sends transcript to LLM with conversation context
5. Takes LLM response → TTS → publishes audio back
6. Manages conversation state (required fields, guardrails)

For production, replace with actual Pipecat pipeline.
For testing, this simplified version demonstrates the full flow.
"""

from __future__ import annotations

import asyncio
import base64
import io
import json
import struct
import time
import wave

from app.modules.voice.conversation import (
    ConversationContext, ConvState, check_guardrails,
    build_system_prompt, process_llm_response,
)
from app.modules.voice.livekit_service import _get_livekit_credentials, create_room_token


async def agent_process_audio(
    audio_base64: str,
    context_dict: dict | None,
    tenant,
    language: str = "tr",
) -> dict:
    """Process a chunk of audio through the full pipeline.

    This is called from the frontend via the test endpoint.
    In production, this would run inside a Pipecat pipeline connected to LiveKit.

    Flow: audio → STT → guardrail check → LLM (with conversation context) → TTS → audio response

    Args:
        audio_base64: Base64-encoded audio from browser (webm/opus)
        context_dict: Previous conversation state (or None for new)
        tenant: Tenant model with settings
        language: Conversation language

    Returns:
        Full pipeline result with audio response, updated context, field extraction
    """
    from app.modules.voice.test_pipeline import test_stt, test_llm, test_tts
    from app.modules.voice.conversation import ConversationContext, ConvState

    timings = {}
    t_total = time.monotonic()

    # Restore conversation context
    if context_dict:
        ctx = ConversationContext(
            state=ConvState(context_dict.get("state", "collect")),
            turn_count=context_dict.get("turn_count", 0),
            language=language,
            fields=context_dict.get("fields", {}),
            history=context_dict.get("history", []),
            guardrail_warnings=context_dict.get("guardrail_warnings", 0),
            confirmed=context_dict.get("confirmed", False),
        )
    else:
        ctx = ConversationContext(language=language)

    # --- Step 1: STT ---
    t0 = time.monotonic()
    audio_bytes = base64.b64decode(audio_base64)
    stt_result = await test_stt(audio_bytes, tenant, language)
    timings["stt_ms"] = round((time.monotonic() - t0) * 1000)

    if stt_result.get("error"):
        return {
            "step": "stt",
            "error": stt_result["error"],
            "pipeline": "livekit → pipecat → stt (failed)",
            "timings": timings,
            "context": ctx.to_dict(),
        }

    transcript = stt_result.get("transcript", "").strip()
    if not transcript:
        return {
            "step": "stt",
            "error": "No speech detected",
            "pipeline": "livekit → pipecat → stt (empty)",
            "timings": timings,
            "context": ctx.to_dict(),
        }

    # --- Step 2: Guardrails ---
    guardrail = check_guardrails(transcript, ctx)
    if not guardrail["safe"]:
        ctx.add_turn("user", transcript)
        redirect_text = guardrail["message"]
        ctx.add_turn("assistant", redirect_text)

        # TTS for redirect message
        t0 = time.monotonic()
        tts_result = await test_tts(redirect_text, tenant, language)
        timings["tts_ms"] = round((time.monotonic() - t0) * 1000)

        return {
            "success": True,
            "pipeline": "livekit → pipecat → stt → guardrail (blocked) → tts",
            "transcript": transcript,
            "agent_text": redirect_text,
            "guardrail": guardrail,
            "tts": tts_result if not tts_result.get("error") else None,
            "timings": timings,
            "context": ctx.to_dict(),
        }

    # --- Step 3: LLM with conversation context ---
    ctx.add_turn("user", transcript)
    system_prompt = build_system_prompt(ctx, tenant.name)

    t0 = time.monotonic()
    llm_result = await test_llm(transcript, tenant, system_prompt)
    timings["llm_ms"] = round((time.monotonic() - t0) * 1000)

    if llm_result.get("error"):
        return {
            "step": "llm",
            "error": llm_result["error"],
            "pipeline": "livekit → pipecat → stt → guardrail → llm (failed)",
            "transcript": transcript,
            "timings": timings,
            "context": ctx.to_dict(),
        }

    # Process LLM response: extract fields, detect confirmation
    processed = process_llm_response(llm_result["response"], ctx)
    ctx.add_turn("assistant", processed["text"])

    # --- Step 4: TTS ---
    t0 = time.monotonic()
    tts_result = await test_tts(processed["text"], tenant, language)
    timings["tts_ms"] = round((time.monotonic() - t0) * 1000)
    timings["total_ms"] = round((time.monotonic() - t_total) * 1000)

    return {
        "success": True,
        "pipeline": "livekit → pipecat → stt → guardrail → llm → tts",
        "transcript": transcript,
        "agent_text": processed["text"],
        "extracted_fields": processed["extracted_fields"],
        "confirmed": processed["confirmed"],
        "guardrail": guardrail,
        "stt": {"provider": stt_result["provider"], "latency_ms": stt_result.get("latency_ms")},
        "llm": {"provider": llm_result["provider"], "latency_ms": llm_result.get("latency_ms"), "tokens": llm_result.get("tokens")},
        "tts": {
            "audio_base64": tts_result.get("audio_base64"),
            "content_type": tts_result.get("content_type"),
            "provider": tts_result.get("provider"),
            "latency_ms": tts_result.get("latency_ms"),
        } if not tts_result.get("error") else {"error": tts_result["error"]},
        "timings": timings,
        "context": ctx.to_dict(),
    }
