"""Voice provider registry: STT, TTS, LLM provider abstraction with fallback."""

from __future__ import annotations

from app.core.config import settings

# ---------------------------------------------------------------------------
# Provider Registry (dict-based, adapted from reference nlp_router.py pattern)
# ---------------------------------------------------------------------------

STT_PROVIDERS = {
    "deepgram": {
        "label": "Deepgram Nova-3",
        "api_key_env": "DEEPGRAM_API_KEY",
        "cost_per_minute": 0.0043,
        "streaming": True,
        "languages": ["tr", "en", "es", "de", "fr", "zh", "ko"],
        "description": "Fastest real-time STT, excellent Turkish support.",
    },
    "voxtral": {
        "label": "Mistral Voxtral STT",
        "api_key_env": "MISTRAL_API_KEY",
        "cost_per_minute": 0.002,
        "streaming": True,
        "languages": ["en", "es", "fr", "pt", "hi", "de", "nl", "it", "ar"],
        "description": "Beats Whisper & GPT-4o. Native function calling from voice. No Turkish yet.",
        "supports_function_calling": True,
        "self_hostable": True,
    },
    "groq": {
        "label": "Groq Whisper",
        "api_key_env": "GROQ_API_KEY",
        "cost_per_minute": 0.0007,
        "streaming": False,
        "languages": ["tr", "en", "es", "de", "fr", "zh", "ko"],
        "description": "Ultra-cheap batch STT via Groq inference.",
    },
    "openai": {
        "label": "OpenAI Whisper",
        "api_key_env": "OPENAI_API_KEY",
        "cost_per_minute": 0.006,
        "streaming": False,
        "languages": ["tr", "en", "es", "de", "fr"],
        "description": "Reliable fallback STT.",
    },
}

TTS_PROVIDERS = {
    "voxtral": {
        "label": "Mistral Voxtral TTS",
        "api_key_env": "MISTRAL_API_KEY",
        "cost_per_char": 0.000016,
        "voices": {"en": "default", "fr": "default", "de": "default", "es": "default"},
        "description": "ElevenLabs quality, open-source, self-hostable. 9 languages, voice cloning. No Turkish yet.",
        "latency_ms": 90,
        "self_hostable": True,
    },
    "openai": {
        "label": "OpenAI TTS-1",
        "api_key_env": "OPENAI_API_KEY",
        "cost_per_char": 0.000015,
        "voices": {"tr": "nova", "en": "alloy"},
        "description": "Good quality, reliable. Turkish supported.",
    },
    "elevenlabs": {
        "label": "ElevenLabs Flash",
        "api_key_env": "ELEVENLABS_API_KEY",
        "cost_per_char": 0.0000003,
        "voices": {"tr": settings.elevenlabs_voice_id, "en": settings.elevenlabs_voice_id},
        "description": "Premium voice quality, custom voices.",
    },
    "edge": {
        "label": "Edge TTS (Free)",
        "api_key_env": None,
        "cost_per_char": 0,
        "voices": {"tr": "tr-TR-EmelNeural", "en": "en-US-JennyNeural"},
        "description": "Free Microsoft Neural TTS. No API key needed.",
    },
}

LLM_PROVIDERS = {
    "claude": {
        "label": "Claude Sonnet",
        "api_key_env": "ANTHROPIC_API_KEY",
        "model": "claude-sonnet-4-20250514",
        "cost_per_1k_input": 0.003,
        "cost_per_1k_output": 0.015,
        "supports_function_calling": True,
        "description": "Best for complex ticket classification and structured output.",
    },
    "mistral": {
        "label": "Mistral Large 3",
        "api_key_env": "MISTRAL_API_KEY",
        "model": "mistral-large-latest",
        "cost_per_1k_input": 0.002,
        "cost_per_1k_output": 0.006,
        "supports_function_calling": True,
        "description": "Strong reasoning, open-weight MoE. Good cost/performance.",
    },
    "openai": {
        "label": "GPT-4o Mini",
        "api_key_env": "OPENAI_API_KEY",
        "model": "gpt-4o-mini",
        "cost_per_1k_input": 0.00015,
        "cost_per_1k_output": 0.0006,
        "supports_function_calling": True,
        "description": "Cheapest option with function calling.",
    },
    "groq": {
        "label": "Groq Llama-3.3-70B",
        "api_key_env": "GROQ_API_KEY",
        "model": "llama-3.3-70b-versatile",
        "cost_per_1k_input": 0.00059,
        "cost_per_1k_output": 0.00079,
        "supports_function_calling": True,
        "description": "Fastest inference, good for simple ticket intake.",
    },
}


def get_available_providers(registry: dict) -> list[dict]:
    """Return providers with availability and full metadata."""
    available = []
    for name, config in registry.items():
        key_env = config.get("api_key_env")
        has_key = True
        if key_env:
            has_key = bool(getattr(settings, key_env.lower(), ""))
        available.append({
            "name": name,
            "label": config["label"],
            "available": has_key,
            "api_key_env": key_env,
            "description": config.get("description", ""),
            "cost": config.get("cost_per_minute") or config.get("cost_per_char") or config.get("cost_per_1k_input"),
            "self_hostable": config.get("self_hostable", False),
            "languages": config.get("languages"),
        })
    return available


def get_provider_config(registry: dict, provider_name: str) -> dict | None:
    """Get config for a specific provider."""
    return registry.get(provider_name)
