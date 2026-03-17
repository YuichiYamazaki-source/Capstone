"""Routing accuracy tests — verify Learning Advisor delegates to the correct agent.

Each test sends a query through the Chat API (same as Explore page)
and asserts that the response's `agent` field matches the expected specialist.

To add cases: append to the parametrize list below, or add GT entries
with `expected_agent` to evals/ground_truth.json.
"""

import pytest

from tests.eval.conftest import chat

# (query, expected_agent)
# Minimal set: 1 case per agent.  Add more via parametrize or GT file.
ROUTING_CASES = [
    (
        "What skills am I missing to become a machine learning engineer?",
        "Skill Gap Analyst",
    ),
    (
        "What career path should I take to become an AI engineer?",
        "Career Advisor",
    ),
    (
        "Create a learning path for machine learning from beginner to advanced",
        "Learning Path Designer",
    ),
    (
        "Find me Python programming courses",
        "Learning Advisor",
    ),
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
