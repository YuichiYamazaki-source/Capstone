"""Web search for external knowledge (career requirements, trends, etc.).

V1: Uses OpenAI's built-in web search tool via a sub-agent call.
V2: Can be swapped to Tavily/SerpAPI for more control.
"""

import asyncio
import logging

from agents import function_tool
from openai import AsyncOpenAI

from app.agent.context import add_tool_call
from app.clients.openai_client import get_openai_client

logger = logging.getLogger("ai-service.tools.web_search")

_MAX_RETRIES = 2
_RETRY_BACKOFF_BASE = 2  # seconds


@function_tool
async def web_search(query: str, max_results: int = 3) -> str:  # LLM-facing: changes affect model behavior
    """Search the web for external information not in the course database.

    Use for career requirements, industry trends, or skill demand data.

    Args:
        query: Search query (e.g. 'skills needed for AI Engineer at Google 2025').
        max_results: Maximum number of results to summarize (default 3).
    """
    add_tool_call("web_search")
    client: AsyncOpenAI = get_openai_client()

    last_error: Exception | None = None

    for attempt in range(_MAX_RETRIES + 1):
        try:
            response = await client.responses.create(
                model="gpt-4o-mini",
                tools=[{"type": "web_search_preview"}],
                input=f"Search the web and summarize the top {max_results} results for: {query}",
            )

            result_text = ""
            for item in response.output:
                if hasattr(item, "content"):
                    for content in item.content:
                        if hasattr(content, "text"):
                            result_text += content.text

            logger.info(
                "Web search completed",
                extra={
                    "query": query,
                    "result_length": len(result_text),
                    "attempt": attempt + 1,
                },
            )

            return result_text if result_text else "No relevant web results found."

        except Exception as e:
            last_error = e
            if attempt < _MAX_RETRIES:
                wait = _RETRY_BACKOFF_BASE**attempt
                logger.warning(
                    "Web search retry",
                    extra={
                        "query": query,
                        "attempt": attempt + 1,
                        "wait_s": wait,
                        "error": str(e),
                    },
                )
                await asyncio.sleep(wait)
            else:
                logger.error(
                    "Web search failed after retries",
                    extra={
                        "query": query,
                        "attempts": _MAX_RETRIES + 1,
                        "error": str(e),
                    },
                )

    return f"[ERROR] web_search: {last_error}"
