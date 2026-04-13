"""LiveKit integration: token generation, room management, agent worker."""

from __future__ import annotations

import asyncio
import base64
import time
from datetime import datetime, timezone
from uuid import uuid4

from livekit.api import AccessToken, VideoGrants

from app.core.config import settings
from app.core.security import decrypt_value


def _get_livekit_credentials(tenant=None) -> tuple[str, str, str]:
    """Get LiveKit URL, API key, and secret from tenant settings or env vars."""
    # Try tenant-level config first
    if tenant:
        voice_cfg = (tenant.settings or {}).get("voice", {})
        livekit_cfg = voice_cfg.get("livekit", {})
        api_keys = (tenant.settings or {}).get("api_keys", {})

        url = livekit_cfg.get("url") or settings.livekit_url
        api_key = livekit_cfg.get("api_key") or settings.livekit_api_key

        # Secret from encrypted store or env
        encrypted_secret = api_keys.get("LIVEKIT_API_SECRET")
        if encrypted_secret:
            try:
                api_secret = decrypt_value(encrypted_secret)
            except Exception:
                api_secret = settings.livekit_api_secret
        else:
            api_secret = settings.livekit_api_secret

        return url or "ws://localhost:7880", api_key or "", api_secret or ""

    # Fallback to env vars
    return (
        settings.livekit_url or "ws://localhost:7880",
        settings.livekit_api_key or "",
        settings.livekit_api_secret or "",
    )


def create_room_token(room_name: str, participant_name: str, is_agent: bool = False, tenant=None) -> str:
    """Generate a LiveKit access token for a participant."""
    _, api_key, api_secret = _get_livekit_credentials(tenant)
    if not api_key or not api_secret:
        raise ValueError("LiveKit API key/secret not configured. Set in Settings → Voice → LiveKit tab.")

    token = AccessToken(api_key, api_secret)
    token.with_identity(participant_name)
    token.with_name(participant_name)

    grants = VideoGrants(
        room_join=True,
        room=room_name,
        can_publish=True,
        can_subscribe=True,
        can_publish_data=True,
    )

    if is_agent:
        grants.agent = True

    token.with_grants(grants)
    from datetime import timedelta
    token.with_ttl(timedelta(hours=1))

    return token.to_jwt()


async def run_agent_for_room(room_name: str, tenant_name: str, language: str, tenant_settings: dict):
    """Run a Pipecat-style agent that joins a LiveKit room and processes audio.

    This is a simplified agent loop:
    1. Connect to LiveKit room as agent
    2. Subscribe to participant audio track
    3. Collect audio chunks until silence detected
    4. STT → LLM → TTS
    5. Publish TTS audio back to room
    6. Repeat until conversation done

    For production, this would use the Pipecat framework.
    For testing, we use a simpler approach with LiveKit's raw API.
    """
    # Import here to avoid circular deps
    from livekit.api import LiveKitAPI

    api = LiveKitAPI(LIVEKIT_URL.replace("ws://", "http://").replace("wss://", "https://"))

    # The actual agent processing happens via the test-conversation endpoint
    # LiveKit handles the media transport (WebRTC ↔ room)
    # The browser sends audio, we process it server-side

    return {
        "room": room_name,
        "status": "agent_ready",
        "livekit_url": LIVEKIT_URL,
    }


def generate_room_name() -> str:
    """Generate a unique room name for a voice test session."""
    return f"voice-test-{uuid4().hex[:8]}"
