"""Online observability: request-level tracing via LangFuse.

Provides visibility into WHAT happens inside each request:
  - LangFuse auto-instrumentation for OpenAI Agents SDK (traces, spans)
  - measure_latency() for non-LLM steps (embedding, Qdrant, MongoDB)

Environment variables:
  LANGFUSE_PUBLIC_KEY  - LangFuse cloud public key
  LANGFUSE_SECRET_KEY  - LangFuse cloud secret key
  LANGFUSE_BASE_URL    - defaults to https://us.cloud.langfuse.com
"""

import logging
import os
import time
from contextlib import contextmanager

logger = logging.getLogger("ai-service.observability")

_initialized = False
_tracing_enabled = False


def init_tracing():
    """Initialize LangFuse + OpenAI Agents SDK instrumentation.

    Safe to call multiple times (idempotent).
    Degrades gracefully if keys/packages are missing.
    """
    global _initialized, _tracing_enabled
    if _initialized:
        return

    # Disable SDK built-in tracing to avoid duplicate traces
    # (LangFuse handles tracing via OpenInference instrumentation)
    try:
        from agents.tracing import set_tracing_disabled

        set_tracing_disabled(True)
        logger.info("SDK built-in tracing disabled (using LangFuse instead)")
    except ImportError:
        pass

    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    if not public_key:
        logger.warning("LangFuse disabled: LANGFUSE_PUBLIC_KEY not set")
        _initialized = True
        return

    try:
        # Patch OpenAI client to auto-capture model, token usage, and cost
        # in LangFuse. Must import BEFORE any AsyncOpenAI is instantiated.
        import langfuse.openai  # noqa: F401 — side-effect import
        from openinference.instrumentation.openai_agents import (
            OpenAIAgentsInstrumentor,
        )

        OpenAIAgentsInstrumentor().instrument()

        from langfuse import get_client

        client = get_client()
        if client.auth_check():
            logger.info("LangFuse initialized (cost tracking enabled)")
            _tracing_enabled = True
        else:
            logger.error("LangFuse auth failed")
    except Exception as e:
        logger.error("LangFuse init error", extra={"error": str(e)})

    _initialized = True


def is_tracing_enabled() -> bool:
    """Check if LangFuse tracing is active."""
    return _tracing_enabled


def observe_function(name: str = None):
    """Decorator that creates a LangFuse trace grouping all child operations.

    No-op if langfuse is not installed or not configured.

    Usage:
        @observe_function(name="chat_request")
        async def run_agent(...):
            ...
    """
    try:
        from langfuse import observe

        return observe(name=name)
    except ImportError:
        return lambda func: func


@contextmanager
def measure_latency(step_name: str):
    """Context manager that measures and logs step latency.

    Always logs to structured JSON.
    Use for non-LLM steps: embedding, Qdrant search, MongoDB queries.

    Usage:
        with measure_latency("qdrant_search"):
            results = qdrant.query_points(...)
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "Step latency",
            extra={"step": step_name, "duration_ms": round(duration_ms, 2)},
        )
