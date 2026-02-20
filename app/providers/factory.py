import logging
import time

import httpx

from app.config import get_settings
from app.providers.anthropic_provider import AnthropicProvider
from app.providers.base import ModelProvider
from app.providers.ollama_provider import OllamaProvider

logger = logging.getLogger(__name__)

# Cached health-check result: (is_healthy, timestamp)
_ollama_health: tuple[bool, float] = (False, 0.0)
_HEALTH_TTL = 30.0  # seconds


async def check_ollama_health() -> bool:
    """Check if Ollama is reachable. Cached for _HEALTH_TTL seconds."""
    global _ollama_health
    now = time.time()
    if now - _ollama_health[1] < _HEALTH_TTL:
        return _ollama_health[0]

    settings = get_settings()
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            healthy = resp.status_code == 200
    except Exception:
        healthy = False

    _ollama_health = (healthy, now)
    if not healthy:
        logger.warning("Ollama is not available — will fall back to Anthropic")
    return healthy


async def get_provider(provider_name: str) -> ModelProvider:
    """Return the requested provider, falling back to Anthropic if Ollama is unavailable."""
    if provider_name == "ollama":
        if await check_ollama_health():
            return OllamaProvider()
        logger.info("Falling back to Anthropic for agent requesting Ollama")
        return AnthropicProvider()

    return AnthropicProvider()
