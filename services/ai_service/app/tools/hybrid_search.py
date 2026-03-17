"""Hybrid search: BM25 sparse + dense semantic with server-side RRF fusion.

Uses Qdrant's Query API to run keyword (BM25) and semantic (dense) search
in a single API call, with server-side Reciprocal Rank Fusion.

Architecture:
  query_points(prefetch=[bm25, dense], fusion=RRF) → merged results
"""

import logging

from qdrant_client import models
from qdrant_client.models import FieldCondition, Filter, MatchText, Range

from app.agent.context import add_collected_courses
from app.clients.openai_client import get_openai_client
from app.clients.qdrant import get_qdrant_client
from app.config import settings
from app.observability import measure_latency

logger = logging.getLogger("ai-service.tools.hybrid_search")

QDRANT_COLLECTION = "courses"
PREFETCH_LIMIT = 20
# RRF weights: [BM25, Dense]. Boost semantic for intent-based queries.
RRF_WEIGHTS = [1.0, 1.5]

# Normalize LLM-extracted level names to actual DB values.
# DB stores "Beginner level", "Intermediate level", "Advanced level".
_LEVEL_MAP = {
    "beginner": "Beginner level",
    "intermediate": "Intermediate level",
    "advanced": "Advanced level",
}


def _normalize_level(level: str) -> str:
    """Map short level names to the full form stored in the database."""
    if not level:
        return level
    key = level.strip().lower()
    return _LEVEL_MAP.get(key, level)


def _build_filter(
    level: str,
    min_rating: float,
    organization: str,
) -> Filter | None:
    """Build Qdrant payload filter from structured constraints."""
    conditions = []

    if level:
        conditions.append(
            FieldCondition(key="level", match=MatchText(text=level)),
        )
    if min_rating > 0:
        conditions.append(
            FieldCondition(key="rating", range=Range(gte=min_rating)),
        )
    if organization:
        conditions.append(
            FieldCondition(
                key="organization",
                match=MatchText(text=organization),
            ),
        )

    return Filter(must=conditions) if conditions else None


async def hybrid_search(
    query: str,
    level: str = "",
    min_rating: float = 0.0,
    organization: str = "",
    skill: str = "",
    top_k: int = 10,
) -> list[dict]:
    """Run hybrid search via Qdrant Query API (BM25 + dense + RRF).

    Single API call to Qdrant that:
    1. Runs BM25 sparse search (keyword relevance with IDF scoring)
    2. Runs dense vector search (semantic similarity)
    3. Fuses results using server-side RRF
    4. Applies payload filters (level, rating, organization)

    Args:
        query: Natural language search query.
        level: Course level filter (Beginner, Intermediate, Advanced).
        min_rating: Minimum rating threshold.
        organization: Organization name filter.
        skill: Specific skill filter (included in BM25 query text).
        top_k: Number of results to return.

    Returns:
        List of course dicts sorted by RRF score.
    """
    qdrant = get_qdrant_client()
    openai = get_openai_client()

    # Enrich BM25 query with skill term for keyword matching
    bm25_query = f"{query} {skill}" if skill else query

    # Generate dense embedding for semantic search
    with measure_latency("hybrid_embedding"):
        embed_resp = await openai.embeddings.create(
            model=settings.openai_embedding_model,
            input=query,
        )
    query_vector = embed_resp.data[0].embedding

    # Normalize level name before building filter
    level = _normalize_level(level)

    # Build payload filter (applied to both prefetches)
    qdrant_filter = _build_filter(level, min_rating, organization)

    # Single Qdrant call: BM25 + dense + server-side RRF fusion
    with measure_latency("hybrid_qdrant_query"):
        results = qdrant.query_points(
            collection_name=QDRANT_COLLECTION,
            prefetch=[
                models.Prefetch(
                    query=models.Document(
                        text=bm25_query,
                        model="Qdrant/bm25",
                    ),
                    using="bm25",
                    limit=PREFETCH_LIMIT,
                    filter=qdrant_filter,
                ),
                models.Prefetch(
                    query=query_vector,
                    using="dense",
                    limit=PREFETCH_LIMIT,
                    filter=qdrant_filter,
                ),
            ],
            query=models.RrfQuery(
                rrf=models.Rrf(weights=RRF_WEIGHTS),
            ),
            limit=top_k,
            with_payload=True,
        )

    # Format results
    courses = []
    for point in results.points:
        p = point.payload
        courses.append(
            {
                "id": p.get("mongo_id", ""),
                "title": p.get("title", "Unknown"),
                "organization": p.get("organization", "N/A"),
                "level": p.get("level", "N/A"),
                "rating": p.get("rating"),
                "skills": p.get("skills", []),
                "url": p.get("url"),
            }
        )

    # Collect for API response
    add_collected_courses(courses)

    logger.info(
        "Hybrid search completed",
        extra={
            "query": query[:100],
            "result_count": len(courses),
            "filters": {
                "level": level,
                "min_rating": min_rating,
                "organization": organization,
                "skill": skill,
            },
        },
    )

    return courses
