"""Course Retrieval — Qdrant hybrid search (BM25 + dense + RRF).

Exposed to Learning Advisor as a function_tool.
No LLM call — deterministic retrieval, lower latency.
"""

import logging

from agents import function_tool

from app.agent.context import (
    add_retrieval_tool_calls,
    add_tool_call,
    set_retrieval_args,
)
from app.tools.hybrid_search import hybrid_search
from app.tools.reranker import cross_encoder_rerank

logger = logging.getLogger("ai-service.agent.retrieval")


@function_tool  # LLM-facing: changes affect model behavior
async def retrieve_courses(
    query: str,
    level: str = "",
    min_rating: float = 0.0,
    organization: str = "",
    skill: str = "",
    top_k: int = 10,
) -> str:
    """Search the course database using hybrid search (keyword + semantic + filters).

    Args:
        query: What courses to find (e.g. 'Python courses', 'machine learning').
        level: Course level filter (e.g. 'Beginner', 'Intermediate', 'Advanced').
        min_rating: Minimum course rating (0.0 to 5.0).
        organization: Filter by organization name (e.g. 'Google', 'IBM').
        skill: Filter by specific skill name.
        top_k: Number of results to return (default 10).
    """
    add_tool_call("retrieve_courses")

    # Capture tool call arguments for evaluation
    set_retrieval_args(
        {
            "query": query,
            "level": level,
            "min_rating": min_rating,
            "organization": organization,
            "skill": skill,
            "top_k": top_k,
        }
    )

    try:
        results = await hybrid_search(
            query=query,
            level=level,
            min_rating=min_rating,
            organization=organization,
            skill=skill,
            top_k=max(top_k, 20),  # Fetch extra for reranking
        )
    except Exception as e:
        logger.error("Hybrid search failed", extra={"query": query, "error": str(e)})
        return f"[ERROR] retrieve_courses: {e}"

    # Cross-encoder reranking for improved relevance
    if results:
        try:
            results = cross_encoder_rerank(query, results, top_k=top_k)
        except Exception as e:
            logger.warning(
                "Cross-encoder rerank failed, using original order",
                extra={"error": str(e)},
            )
            results = results[:top_k]

    # Record retrieval method for evaluation metrics
    add_retrieval_tool_calls(["hybrid_search", "cross_encoder_rerank"])

    if not results:
        return "No courses found matching your query."

    # Format results for the Learning Advisor
    lines = []
    for course in results:
        lines.append(
            f"- {course.get('title', 'Unknown')} "
            f"(Organization: {course.get('organization', 'N/A')}, "
            f"Level: {course.get('level', 'N/A')}, "
            f"Rating: {course.get('rating', 'N/A')}, "
            f"Skills: {', '.join(course.get('skills', [])[:5])})"
        )

    return f"Found {len(results)} courses:\n" + "\n".join(lines)
