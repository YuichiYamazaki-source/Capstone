import logging

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger("ai-service.clients.openai")

_client: AsyncOpenAI | None = None


def get_openai_client() -> AsyncOpenAI:
    """Return the OpenAI client, initializing it on first call.

    Returns:
        The singleton AsyncOpenAI client instance.
    """
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            timeout=60.0,
        )
        logger.info("OpenAI client initialized")
    return _client
