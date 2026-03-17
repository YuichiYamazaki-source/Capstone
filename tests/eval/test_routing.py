"""Routing accuracy tests — verify Learning Advisor delegates to the correct agent.

Each test sends a query through the Chat API (same as Explore page)
and asserts that the response's `agent` field matches the expected specialist.
"""

import pytest

from tests.eval.conftest import (
    Q_CAREER,
    Q_COURSE_SEARCH,
    Q_LEARNING_PATH,
    Q_SKILL_GAP,
    chat,
)

ROUTING_CASES = [
    (Q_SKILL_GAP, "Skill Gap Analyst"),
    (Q_CAREER, "Career Advisor"),
    (Q_LEARNING_PATH, "Learning Path Designer"),
    (Q_COURSE_SEARCH, "Learning Advisor"),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("query, expected_agent", ROUTING_CASES, ids=[
    "skill_gap",
    "career",
    "learning_path",
    "direct_search",
])
async def test_routing_accuracy(query, expected_agent):
    """Query is routed to the expected agent."""
    response = await chat(query)
    assert response["agent"] == expected_agent, (
        f"Expected agent '{expected_agent}', got '{response['agent']}' "
        f"for query: {query}"
    )
