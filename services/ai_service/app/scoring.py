"""Online scoring: deterministic metrics sent to LangFuse per request.

Quality metrics (answer_relevancy, faithfulness, actionability, etc.)
are handled by LangFuse Evaluators (LLM-as-a-Judge configured in dashboard).

This module only sends deterministic, code-computable scores:
  - agent_routing_correct: did orchestrator route to expected agent?
  - tool_selection_correct: did agent call retrieve_courses?
"""

import logging

logger = logging.getLogger("ai-service.scoring")


def _send_score(trace_id: str, name: str, value: float) -> None:
    """Send a single deterministic score to LangFuse.

    Args:
        trace_id: LangFuse trace ID to attach the score to.
        name: Score metric name.
        value: Score value (0.0-1.0).
    """
    try:
        from langfuse import get_client

        client = get_client()
        client.create_score(
            trace_id=trace_id,
            name=name,
            value=value,
            data_type="NUMERIC",
        )
        client.flush()
        logger.info("Score sent: %s=%.2f (trace=%s)", name, value, trace_id)
    except Exception as e:
        logger.warning("LangFuse score send failed: %s", e)


def send_deterministic_scores(
    trace_id: str | None,
    tool_calls: list[str],
    agent: str,
) -> None:
    """Send deterministic online scores to LangFuse.

    Called after each chat response. Only sends scores that can be
    computed without ground truth or LLM judgment.

    Args:
        trace_id: LangFuse trace ID (None if tracing disabled).
        tool_calls: List of tool names called by the agent.
        agent: Agent name that handled the request.
    """
    if not trace_id:
        return

    # Tool selection: did the agent call retrieve_courses?
    has_retrieval = "retrieve_courses" in tool_calls
    _send_score(trace_id, "tool_selection_correct", 1.0 if has_retrieval else 0.0)

    logger.info(
        "Deterministic scores sent for %s (trace=%s)",
        agent,
        trace_id,
    )
