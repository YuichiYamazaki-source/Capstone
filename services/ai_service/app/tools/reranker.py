"""Profile-based reranking for course search results.

Boosts courses matching user skills/interests and weights by success rate (rating).
"""

import logging

logger = logging.getLogger("ai-service.tools.reranker")


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
