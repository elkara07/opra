"""Voice pipeline test: real STT, LLM, TTS calls for debugging without SIP."""

from __future__ import annotations

import base64
import io
import time
from typing import Optional

import httpx

from app.core.config import settings
from app.core.security import decrypt_value
from app.models.tenant import Tenant


def _get_key(tenant: Tenant, env_name: str) -> str:
    """Get API key: tenant encrypted store → env var fallback."""
    # Try tenant-level encrypted key
    api_keys = (tenant.settings or {}).get("api_keys", {})
    encrypted = api_keys.get(env_name)
    if encrypted:
        try:
            return decrypt_value(encrypted)
        except Exception:
            pass
    # Fallback to env var
    return getattr(settings, env_name.lower(), "") or ""


# ---------------------------------------------------------------------------
# STT — Speech to Text
# ---------------------------------------------------------------------------

# Known Whisper hallucination patterns (phantom text on silence/noise)
HALLUCINATION_PATTERNS = [
    "altyazı m.k.",
    "altyazı m.k",
    "altyazılar",
    "alt yazı",
    "subtitles by",
    "thank you for watching",
    "izlediğiniz için teşekkürler",
    "abone olmayı unutmayın",
    "www.",
    "http",
    ".com",
    "amara.org",
]


def _is_hallucination(text: str) -> bool:
    """Check if STT output is a known Whisper hallucination."""
    if not text:
        return True
    lower = text.lower().strip()
    if len(lower) < 3:
        return True
    for pattern in HALLUCINATION_PATTERNS:
        if pattern in lower:
            return True
    # Repetition check: same word/phrase repeated 3+ times
    words = lower.split()
    if len(words) >= 3 and len(set(words)) == 1:
        return True
    return False


def _check_audio_energy(audio_bytes: bytes) -> bool:
    """Check if audio has enough energy to contain speech.

    Returns True if audio likely contains speech, False if too quiet.
    """
    import struct

    try:
        # Try to parse as WAV
        if audio_bytes[:4] == b'RIFF':
            import wave
            buf = io.BytesIO(audio_bytes)
            with wave.open(buf, 'rb') as w:
                frames = w.readframes(w.getnframes())
                if w.getsampwidth() == 2:
                    samples = struct.unpack(f'<{len(frames)//2}h', frames)
                else:
                    samples = frames
        else:
            # For webm/opus, can't easily parse — assume it has speech
            return True

        if not samples:
            return False

        # RMS energy
        rms = (sum(s*s for s in samples) / len(samples)) ** 0.5
        return rms > 50  # Threshold: above noise floor

    except Exception:
        # If we can't parse, assume it has speech (let STT decide)
        return True


def _convert_to_wav(audio_bytes: bytes) -> bytes:
    """Convert any audio format to 16kHz mono PCM WAV using ffmpeg.

    This ensures STT providers get a clean, standard format regardless
    of what the browser records (webm/opus, ogg, mp4, etc).
    """
    import subprocess
    import tempfile
    import os

    # Detect if already WAV
    if audio_bytes[:4] == b'RIFF':
        return audio_bytes

    try:
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as inp:
            inp.write(audio_bytes)
            inp_path = inp.name

        out_path = inp_path.replace('.webm', '.wav')

        result = subprocess.run([
            'ffmpeg', '-y', '-i', inp_path,
            '-ar', '16000',      # 16kHz sample rate
            '-ac', '1',          # mono
            '-sample_fmt', 's16', # 16-bit PCM
            '-f', 'wav',
            out_path,
        ], capture_output=True, timeout=10)

        if result.returncode != 0:
            # ffmpeg failed — return original
            return audio_bytes

        with open(out_path, 'rb') as f:
            wav_bytes = f.read()

        os.unlink(inp_path)
        os.unlink(out_path)
        return wav_bytes

    except Exception:
        return audio_bytes


async def test_stt(audio_bytes: bytes, tenant: Tenant, language: str = "tr") -> dict:
    """Transcribe audio using configured STT provider."""
    voice_cfg = (tenant.settings or {}).get("voice", {})
    provider = voice_cfg.get("stt_provider", "groq")

    # Convert browser audio (webm/opus) to WAV for reliable STT
    wav_bytes = _convert_to_wav(audio_bytes)

    # Energy check
    if wav_bytes[:4] == b'RIFF' and not _check_audio_energy(wav_bytes):
        return {"transcript": "", "provider": provider, "latency_ms": 0,
                "note": "Audio too quiet — no speech detected"}

    t0 = time.monotonic()

    if provider == "groq":
        result = await _stt_groq(wav_bytes, tenant, language, t0)
    elif provider == "deepgram":
        result = await _stt_deepgram(wav_bytes, tenant, language, t0)
    elif provider == "openai" or provider == "voxtral":
        result = await _stt_openai_compat(wav_bytes, tenant, language, t0, provider)
    else:
        return {"error": f"Unknown STT provider: {provider}", "provider": provider}

    # Post-process: filter hallucinations
    if not result.get("error") and _is_hallucination(result.get("transcript", "")):
        result["transcript"] = ""
        result["note"] = "Filtered: STT hallucination detected (no real speech)"

    return result


async def _stt_groq(audio_bytes: bytes, tenant: Tenant, language: str, t0: float) -> dict:
    key = _get_key(tenant, "GROQ_API_KEY")
    if not key:
        return {"error": "GROQ_API_KEY not configured", "provider": "groq"}

    # Detect format from header
    is_wav = audio_bytes[:4] == b'RIFF'
    filename = "audio.wav" if is_wav else "audio.webm"
    mime = "audio/wav" if is_wav else "audio/webm"

    async with httpx.AsyncClient(timeout=30.0) as client:
        files = {"file": (filename, io.BytesIO(audio_bytes), mime)}
        # Technical vocabulary prompt — forces Whisper to prefer these terms
        tech_prompt = (
            "Teknik destek çağrısı. Terimler: sunucu, server, veritabanı, database, "
            "ağ, network, firewall, DNS, CPU, RAM, disk, cluster, container, "
            "deployment, API, endpoint, latency, timeout, SSL, VPN, "
            "load balancer, kubernetes, docker, redis, postgres, nginx, "
            "monitoring, alert, incident, SLA, eskalasyon, ticket, "
            "konfigürasyon, production, staging, rollback, migration, backup, "
            "servis, uygulama, application, bağlantı, connection, hata, error, "
            "çöktü, down, erişilemiyor, unreachable, yavaş, slow, "
            "restart, reboot, log, trace, debug."
        ) if language == "tr" else (
            "Technical support call. Terms: server, database, network, firewall, "
            "DNS, CPU, RAM, disk, cluster, container, deployment, API, endpoint, "
            "latency, timeout, SSL, VPN, load balancer, kubernetes, docker, "
            "monitoring, alert, incident, SLA, escalation, ticket, "
            "configuration, production, staging, rollback, migration, backup."
        )
        data = {
            "model": "whisper-large-v3-turbo",
            "language": language,
            "prompt": tech_prompt,
        }
        resp = await client.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {key}"},
            files=files, data=data,
        )
    latency = round((time.monotonic() - t0) * 1000)

    if resp.status_code != 200:
        return {"error": f"Groq STT error {resp.status_code}: {resp.text[:200]}", "provider": "groq"}

    result = resp.json()
    return {
        "transcript": result.get("text", ""),
        "provider": "groq",
        "model": "whisper-large-v3-turbo",
        "latency_ms": latency,
    }


async def _stt_deepgram(audio_bytes: bytes, tenant: Tenant, language: str, t0: float) -> dict:
    key = _get_key(tenant, "DEEPGRAM_API_KEY")
    if not key:
        return {"error": "DEEPGRAM_API_KEY not configured", "provider": "deepgram"}

    is_wav = audio_bytes[:4] == b'RIFF'
    content_type = "audio/wav" if is_wav else "audio/webm"

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"https://api.deepgram.com/v1/listen?model=nova-3&language={language}&smart_format=true",
            headers={"Authorization": f"Token {key}", "Content-Type": content_type},
            content=audio_bytes,
        )
    latency = round((time.monotonic() - t0) * 1000)

    if resp.status_code != 200:
        return {"error": f"Deepgram error {resp.status_code}: {resp.text[:200]}", "provider": "deepgram"}

    result = resp.json()
    transcript = ""
    try:
        transcript = result["results"]["channels"][0]["alternatives"][0]["transcript"]
    except (KeyError, IndexError):
        pass
    return {"transcript": transcript, "provider": "deepgram", "model": "nova-3", "latency_ms": latency}


async def _stt_openai_compat(audio_bytes: bytes, tenant: Tenant, language: str, t0: float, provider: str) -> dict:
    if provider == "voxtral":
        key = _get_key(tenant, "MISTRAL_API_KEY")
        url = "https://api.mistral.ai/v1/audio/transcriptions"
        model = "voxtral-v1"
    else:
        key = _get_key(tenant, "OPENAI_API_KEY")
        url = "https://api.openai.com/v1/audio/transcriptions"
        model = "whisper-1"

    if not key:
        return {"error": f"{provider} API key not configured", "provider": provider}

    is_wav = audio_bytes[:4] == b'RIFF'
    filename = "audio.wav" if is_wav else "audio.webm"
    mime = "audio/wav" if is_wav else "audio/webm"

    async with httpx.AsyncClient(timeout=30.0) as client:
        files = {"file": (filename, io.BytesIO(audio_bytes), mime)}
        data = {"model": model, "language": language}
        resp = await client.post(url, headers={"Authorization": f"Bearer {key}"}, files=files, data=data)
    latency = round((time.monotonic() - t0) * 1000)

    if resp.status_code != 200:
        return {"error": f"{provider} error {resp.status_code}: {resp.text[:200]}", "provider": provider}

    return {"transcript": resp.json().get("text", ""), "provider": provider, "model": model, "latency_ms": latency}


# ---------------------------------------------------------------------------
# LLM — Language Model
# ---------------------------------------------------------------------------

async def test_llm(text: str, tenant: Tenant, system_prompt: str | None = None) -> dict:
    """Send text to configured LLM, return response."""
    voice_cfg = (tenant.settings or {}).get("voice", {})
    provider = voice_cfg.get("llm_provider", "groq")

    if not system_prompt:
        system_prompt = (
            "You are a support agent for a 24/7 operations center. "
            "The user is calling to report an issue. Respond concisely and helpfully. "
            "Ask clarifying questions to understand the issue."
        )

    t0 = time.monotonic()

    if provider in ("groq", "mistral", "openai"):
        return await _llm_openai_compat(text, tenant, system_prompt, t0, provider)
    elif provider == "claude":
        return await _llm_claude(text, tenant, system_prompt, t0)
    else:
        return {"error": f"Unknown LLM provider: {provider}", "provider": provider}


async def _llm_openai_compat(text: str, tenant: Tenant, system_prompt: str, t0: float, provider: str) -> dict:
    config = {
        "groq": ("GROQ_API_KEY", "https://api.groq.com/openai/v1/chat/completions", "llama-3.3-70b-versatile"),
        "mistral": ("MISTRAL_API_KEY", "https://api.mistral.ai/v1/chat/completions", "mistral-large-latest"),
        "openai": ("OPENAI_API_KEY", "https://api.openai.com/v1/chat/completions", "gpt-4o-mini"),
    }
    key_env, url, model = config[provider]
    key = _get_key(tenant, key_env)
    if not key:
        return {"error": f"{key_env} not configured", "provider": provider}

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        "max_tokens": 300,
        "temperature": 0.7,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, json=payload)
    latency = round((time.monotonic() - t0) * 1000)

    if resp.status_code != 200:
        return {"error": f"{provider} error {resp.status_code}: {resp.text[:200]}", "provider": provider}

    result = resp.json()
    response_text = result["choices"][0]["message"]["content"]
    tokens = result.get("usage", {})
    return {
        "response": response_text,
        "provider": provider,
        "model": model,
        "latency_ms": latency,
        "tokens": {"input": tokens.get("prompt_tokens"), "output": tokens.get("completion_tokens")},
    }


async def _llm_claude(text: str, tenant: Tenant, system_prompt: str, t0: float) -> dict:
    key = _get_key(tenant, "ANTHROPIC_API_KEY")
    if not key:
        return {"error": "ANTHROPIC_API_KEY not configured", "provider": "claude"}

    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 300,
        "system": system_prompt,
        "messages": [{"role": "user", "content": text}],
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"},
            json=payload,
        )
    latency = round((time.monotonic() - t0) * 1000)

    if resp.status_code != 200:
        return {"error": f"Claude error {resp.status_code}: {resp.text[:200]}", "provider": "claude"}

    result = resp.json()
    response_text = result["content"][0]["text"]
    usage = result.get("usage", {})
    return {
        "response": response_text,
        "provider": "claude",
        "model": "claude-sonnet-4-20250514",
        "latency_ms": latency,
        "tokens": {"input": usage.get("input_tokens"), "output": usage.get("output_tokens")},
    }


# ---------------------------------------------------------------------------
# TTS — Text to Speech
# ---------------------------------------------------------------------------

async def test_tts(text: str, tenant: Tenant, language: str = "tr") -> dict:
    """Convert text to speech using configured TTS provider. Returns base64 audio."""
    voice_cfg = (tenant.settings or {}).get("voice", {})
    provider = voice_cfg.get("tts_provider", "edge")

    t0 = time.monotonic()

    if provider == "edge":
        return await _tts_edge(text, language, t0)
    elif provider == "openai":
        return await _tts_openai(text, tenant, t0)
    elif provider == "elevenlabs":
        return await _tts_elevenlabs(text, tenant, t0)
    elif provider == "voxtral":
        return await _tts_voxtral(text, tenant, t0)
    else:
        return await _tts_edge(text, language, t0)  # fallback to free


async def _tts_edge(text: str, language: str, t0: float) -> dict:
    """Free Edge TTS — uses edge-tts Python package or direct API."""
    try:
        import edge_tts
        voice = "tr-TR-EmelNeural" if language == "tr" else "en-US-JennyNeural"
        communicate = edge_tts.Communicate(text, voice)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        latency = round((time.monotonic() - t0) * 1000)
        return {
            "audio_base64": base64.b64encode(audio_data).decode(),
            "content_type": "audio/mp3",
            "provider": "edge",
            "voice": voice,
            "latency_ms": latency,
        }
    except ImportError:
        return {"error": "edge-tts package not installed (pip install edge-tts)", "provider": "edge"}
    except Exception as e:
        return {"error": f"Edge TTS error: {str(e)}", "provider": "edge"}


async def _tts_openai(text: str, tenant: Tenant, t0: float) -> dict:
    key = _get_key(tenant, "OPENAI_API_KEY")
    if not key:
        return {"error": "OPENAI_API_KEY not configured", "provider": "openai"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            "https://api.openai.com/v1/audio/speech",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": "tts-1", "input": text, "voice": "nova", "response_format": "mp3"},
        )
    latency = round((time.monotonic() - t0) * 1000)

    if resp.status_code != 200:
        return {"error": f"OpenAI TTS error {resp.status_code}: {resp.text[:200]}", "provider": "openai"}

    return {
        "audio_base64": base64.b64encode(resp.content).decode(),
        "content_type": "audio/mp3",
        "provider": "openai",
        "voice": "nova",
        "latency_ms": latency,
    }


async def _tts_elevenlabs(text: str, tenant: Tenant, t0: float) -> dict:
    key = _get_key(tenant, "ELEVENLABS_API_KEY")
    voice_id = settings.elevenlabs_voice_id or "21m00Tcm4TlvDq8ikWAM"  # default Rachel
    if not key:
        return {"error": "ELEVENLABS_API_KEY not configured", "provider": "elevenlabs"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={"xi-api-key": key, "Content-Type": "application/json"},
            json={"text": text, "model_id": "eleven_flash_v2_5"},
        )
    latency = round((time.monotonic() - t0) * 1000)

    if resp.status_code != 200:
        return {"error": f"ElevenLabs error {resp.status_code}: {resp.text[:200]}", "provider": "elevenlabs"}

    return {
        "audio_base64": base64.b64encode(resp.content).decode(),
        "content_type": "audio/mpeg",
        "provider": "elevenlabs",
        "latency_ms": latency,
    }


async def _tts_voxtral(text: str, tenant: Tenant, t0: float) -> dict:
    key = _get_key(tenant, "MISTRAL_API_KEY")
    if not key:
        return {"error": "MISTRAL_API_KEY not configured", "provider": "voxtral"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            "https://api.mistral.ai/v1/audio/speech",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": "voxtral-tts-v1", "input": text},
        )
    latency = round((time.monotonic() - t0) * 1000)

    if resp.status_code != 200:
        return {"error": f"Voxtral TTS error {resp.status_code}: {resp.text[:200]}", "provider": "voxtral"}

    return {
        "audio_base64": base64.b64encode(resp.content).decode(),
        "content_type": "audio/mp3",
        "provider": "voxtral",
        "latency_ms": latency,
    }
