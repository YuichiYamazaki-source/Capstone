"""Prompt management via LangFuse.

Fetches versioned prompts from LangFuse at runtime.
Falls back to hardcoded defaults if LangFuse is unavailable.

Usage:
    prompt_text = get_prompt("learning-advisor")
"""

import logging
import os

logger = logging.getLogger("ai-service.prompts")

# Cache fetched prompts to avoid repeated API calls
_prompt_cache: dict[str, str] = {}


def get_prompt(name: str, fallback: str = "") -> str:
    """Fetch a prompt from LangFuse by name.

    Creates its own Langfuse client (independent of observability init)
    so prompts can be loaded at module import time.

    Returns the latest production version. Falls back to the provided
    default string if LangFuse is unavailable or the prompt is not found.

    Args:
        name: Prompt name in LangFuse (e.g. "learning-advisor").
        fallback: Default prompt text if LangFuse fetch fails.

    Returns:
        Prompt text string.
    """
    if name in _prompt_cache:
        return _prompt_cache[name]

    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    if not public_key:
        logger.warning("LangFuse prompt disabled: LANGFUSE_PUBLIC_KEY not set")
        _prompt_cache[name] = fallback
        return fallback

    try:
        from langfuse import Langfuse

        client = Langfuse(
            public_key=public_key,
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_BASE_URL", "https://us.cloud.langfuse.com"),
        )
        prompt = client.get_prompt(name)
        text = prompt.compile()
        _prompt_cache[name] = text
        logger.info(
            "Prompt loaded from LangFuse: %s (v%s)",
            name,
            prompt.version,
        )
        return text
    except Exception as e:
        logger.warning(
            "LangFuse prompt fetch failed for '%s', using fallback: %s",
            name,
            e,
        )
        _prompt_cache[name] = fallback
        return fallback
