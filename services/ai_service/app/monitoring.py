"""Online monitoring: per-request metrics recorded to LangFuse.

Records quantitative data for each chat request:
  - Tool calls (names, count)
  - Latency (end-to-end)
  - Model version
  - Course results count

Scores are attached to the active LangFuse trace created by
@observe_function() in chat.py router.

Cost tracking:
  Token-level cost is captured automatically by LangFuse auto-instrumentation
  (OpenAI Agents SDK). This module records request-level metadata and scores.
"""

import logging

logger = logging.getLogger("ai-service.monitoring")


def record_request_metrics(
    query: str,
    result: dict,
    user_id: str | None,
    latency_ms: float,
) -> None:
    """Record metrics for a chat request.

    Always logs to structured JSON.
    When called inside an @observe_function() context, attaches scores
    and metadata to the active LangFuse trace.

    Args:
        query: Original user message.
        result: Full result dict from run_agent().
        user_id: User identifier (optional).
        latency_ms: End-to-end request latency in milliseconds.
    """
    tool_calls = result.get("tool_calls", [])
    retrieval_tool_calls = result.get("retrieval_tool_calls", [])
    courses_count = len(result.get("courses", []))
    agent_name = result.get("agent", "Learning Advisor")

    # Structured log (always available)
    logger.info(
        "Request metrics",
        extra={
            "query": query[:100],
            "user_id": user_id,
            "agent": agent_name,
            "advisor_tools": tool_calls,
            "retrieval_tools": retrieval_tool_calls,
            "courses_count": courses_count,
            "latency_ms": round(latency_ms, 2),
        },
    )

    # Attach scores to LangFuse trace
    from app.observability import is_tracing_enabled

    if not is_tracing_enabled():
        return

    try:
        from langfuse import get_client

        client = get_client()

        # Operational metrics go in metadata (not scores) to avoid
        # distorting the Score graph Y-axis. Scores should be 0-1 only.
        client.update_current_span(
            metadata={
                "user_id": str(user_id or "anonymous"),
                "agent": agent_name,
                "advisor_tools": ", ".join(tool_calls),
                "retrieval_tools": ", ".join(retrieval_tool_calls),
                "courses_count": courses_count,
                "advisor_tool_count": len(tool_calls),
                "retrieval_tool_count": len(retrieval_tool_calls),
                "latency_ms": round(latency_ms, 2),
            },
        )

    except Exception as e:
        logger.debug("LangFuse metrics skip", extra={"reason": str(e)})
