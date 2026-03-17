"""Online observability: request-level tracing.

Provides visibility into WHAT happens inside each request:
  - LangFuse auto-instrumentation for OpenAI Agents SDK (traces, spans)
  - Phoenix OTEL exporter for local trace visualization
  - measure_latency() for non-LLM steps (embedding, Qdrant, MongoDB)

Environment variables:
  LANGFUSE_PUBLIC_KEY  - LangFuse cloud public key
  LANGFUSE_SECRET_KEY  - LangFuse cloud secret key
  LANGFUSE_BASE_URL    - defaults to https://us.cloud.langfuse.com
  PHOENIX_COLLECTOR_ENDPOINT - Phoenix OTEL endpoint (optional)
"""

import logging
import os
import time
from contextlib import contextmanager

logger = logging.getLogger("ai-service.observability")

_initialized = False
_tracing_enabled = False
_phoenix_enabled = False


def _init_phoenix():
    """Initialize Arize Phoenix OTEL exporter if endpoint is configured."""
    global _phoenix_enabled
    phoenix_endpoint = os.getenv("PHOENIX_COLLECTOR_ENDPOINT")
    if not phoenix_endpoint:
        logger.info("Phoenix disabled: PHOENIX_COLLECTOR_ENDPOINT not set")
        return

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SimpleSpanProcessor

        exporter = OTLPSpanExporter(endpoint=phoenix_endpoint)
        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        _phoenix_enabled = True
        logger.info(
            "Phoenix initialized",
            extra={"endpoint": phoenix_endpoint},
        )
    except ImportError:
        logger.warning("Phoenix disabled: opentelemetry packages not installed")
    except Exception as e:
        logger.error("Phoenix init error", extra={"error": str(e)})


def init_tracing():
    """Initialize LangFuse + Phoenix + OpenAI Agents SDK instrumentation.

    Safe to call multiple times (idempotent).
    Degrades gracefully if keys/packages are missing.
    """
    global _initialized, _tracing_enabled
    if _initialized:
        return

    _init_phoenix()

    # Disable SDK built-in tracing to avoid duplicate traces
    # (LangFuse/Phoenix handle tracing via OpenInference instrumentation)
    try:
        from agents.tracing import set_tracing_disabled

        set_tracing_disabled(True)
        logger.info("SDK built-in tracing disabled (using LangFuse/Phoenix instead)")
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


def is_phoenix_enabled() -> bool:
    """Check if Phoenix OTEL tracing is active."""
    return _phoenix_enabled


def get_tracer(name: str):
    """Get an OTEL tracer. Returns no-op tracer if Phoenix is disabled."""
    from opentelemetry import trace

    return trace.get_tracer(name)


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
