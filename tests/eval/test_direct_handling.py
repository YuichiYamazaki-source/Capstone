"""Direct handling tests — verify Learning Advisor handles these WITHOUT handoff.

These queries should NOT be delegated to any specialist agent.
"""

import pytest

from tests.eval.conftest import Q_COURSE_SEARCH, Q_GREETING, chat

DIRECT_CASES = [
    (Q_GREETING, "greeting"),
    ("What's the weather like today?", "unrelated"),
    (Q_COURSE_SEARCH, "course_search"),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("query, case_type", DIRECT_CASES, ids=[
    "greeting",
    "unrelated",
    "course_search",
])
async def test_direct_handling(query, case_type):
    """Learning Advisor handles directly without delegating."""
    response = await chat(query)
    assert response["agent"] == "Learning Advisor", (
        f"Expected direct handling by Learning Advisor, "
        f"but got '{response['agent']}' for {case_type} query: {query}"
    )


@pytest.mark.asyncio
async def test_greeting_no_tool_calls():
    """Greetings should not trigger any tool calls."""
    response = await chat(Q_GREETING)
    assert len(response.get("all_tool_calls", [])) == 0, (
        f"Greeting triggered tool calls: {response.get('all_tool_calls')}"
    )


@pytest.mark.asyncio
async def test_course_search_uses_retrieve():
    """Course search should call retrieve_courses."""
    response = await chat(Q_COURSE_SEARCH)
    assert "retrieve_courses" in response.get("all_tool_calls", []), (
        f"Course search did not call retrieve_courses. "
        f"all_tool_calls: {response.get('all_tool_calls')}"
    )
