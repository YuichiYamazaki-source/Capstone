"""Cross-encoder-style and profile-based reranking for course search results.

Two reranking strategies:
  1. Embedding-based: Uses fastembed TextEmbedding to compute query-document
     cosine similarity and re-score results (lightweight cross-encoder alternative).
  2. Profile-based: Boosts courses matching user skills/interests and
     weights by success rate (rating).
"""

import logging

import numpy as np
from fastembed import TextEmbedding

logger = logging.getLogger("ai-service.tools.reranker")

# Lazy-loaded embedding model for reranking
_rerank_model: TextEmbedding | None = None
_RERANK_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def _get_rerank_model() -> TextEmbedding:
    """Return the reranking embedding model, loading on first call."""
    global _rerank_model
    if _rerank_model is None:
        logger.info(
            "Loading reranking model",
            extra={"model": _RERANK_MODEL_NAME},
        )
        _rerank_model = TextEmbedding(model_name=_RERANK_MODEL_NAME)
        logger.info("Reranking model loaded")
    return _rerank_model


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    dot = np.dot(a, b)
    norm = np.linalg.norm(a) * np.linalg.norm(b)
    if norm == 0:
        return 0.0
    return float(dot / norm)


def cross_encoder_rerank(
    query: str,
    courses: list[dict],
    top_k: int = 10,
) -> list[dict]:
    """Rerank courses using embedding-based similarity scoring.

    Embeds both the query and each course document with a local model,
    then sorts by cosine similarity. This provides a cross-encoder-like
    reranking effect using a lightweight bi-encoder.

    Args:
        query: User search query.
        courses: List of course dicts from hybrid search.
        top_k: Maximum number of results to return.

    Returns:
        Reranked list of course dicts.
    """
    if not courses:
        return courses

    model = _get_rerank_model()

    # Build documents: title + skills summary for richer context
    documents = []
    for c in courses:
        parts = [c.get("title", "")]
        skills = c.get("skills", [])
        if skills:
            parts.append(" ".join(skills[:5]))
        documents.append(" | ".join(parts))

    # Embed query and all documents
    all_texts = [query] + documents
    embeddings = list(model.embed(all_texts))

    query_emb = np.array(embeddings[0])
    doc_embs = [np.array(e) for e in embeddings[1:]]

    # Score by cosine similarity
    scored = []
    for course, doc_emb in zip(courses, doc_embs, strict=True):
        score = _cosine_similarity(query_emb, doc_emb)
        scored.append((course, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    reranked = [c for c, _s in scored[:top_k]]

    logger.info(
        "Reranked courses",
        extra={
            "query": query[:80],
            "input_count": len(courses),
            "output_count": len(reranked),
        },
    )
    return reranked


def profile_rerank(
    courses: list[dict],
    user_skills: list[str] | None = None,
    user_interests: list[str] | None = None,
) -> list[dict]:
    """Rerank courses by learner preference and success rate.

    Scoring:
      - skill_overlap: fraction of course skills matching user skills
      - interest_boost: bonus if course title/skills match user interests
      - success_rate: rating / 5.0 (normalized)
      - final_score = 0.4 * skill_overlap + 0.3 * interest_boost + 0.3 * success_rate

    Args:
        courses: List of course dicts.
        user_skills: User's current skills (from profile).
        user_interests: User's interest areas (from profile).

    Returns:
        Courses sorted by personalized relevance score.
    """
    if not courses:
        return courses

    user_skills_lower = {s.lower() for s in (user_skills or [])}
    user_interests_lower = {s.lower() for s in (user_interests or [])}

    scored = []
    for course in courses:
        # Skill overlap score
        course_skills = {s.lower() for s in course.get("skills", [])}
        if course_skills and user_skills_lower:
            skill_overlap = len(course_skills & user_skills_lower) / len(
                course_skills
            )
        else:
            skill_overlap = 0.0

        # Interest boost
        title_lower = course.get("title", "").lower()
        interest_match = any(
            interest in title_lower or interest in course_skills
            for interest in user_interests_lower
        )
        interest_boost = 1.0 if interest_match else 0.0

        # Success rate (rating normalized to 0-1)
        rating = course.get("rating") or 0.0
        success_rate = min(rating / 5.0, 1.0)

        # Weighted final score
        final_score = (
            0.4 * skill_overlap + 0.3 * interest_boost + 0.3 * success_rate
        )

        scored.append((course, final_score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [c for c, _s in scored]
