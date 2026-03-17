"""Web Search tool tests — validates web_search utilization across agents.

Tests that agents which need market data (Skill Gap Analyst, Career Advisor)
call web_search and reflect its results in output, and that agents which
should NOT use web search (Learning Path Designer) do not call it.

Uses canonical queries (cached) to avoid redundant API calls.
"""

import pytest

from tests.eval.conftest import (
    Q_CAREER_2,
    Q_LEARNING_PATH,
    Q_SKILL_GAP,
    Q_SKILL_GAP_2,
    chat,
    extract_json_from_reply,
)


# --- Skill Gap Analyst: web_search required ---


@pytest.mark.asyncio
async def test_skill_gap_uses_web_search():
    """Skill Gap Analyst must call web_search for market skill requirements."""
    response = await chat(Q_SKILL_GAP)
    assert response["agent"] == "Skill Gap Analyst"

    all_tools = response.get("all_tool_calls", [])
    assert "web_search" in all_tools, (
        f"Skill Gap Analyst did not call web_search. "
        f"Skill requirements must be grounded in market data. "
        f"all_tool_calls: {all_tools}"
    )


@pytest.mark.asyncio
async def test_skill_gap_web_search_reflected_in_output():
    """Web search results should be reflected in the gaps output."""
    response = await chat(Q_SKILL_GAP_2)
    assert response["agent"] == "Skill Gap Analyst"

    all_tools = response.get("all_tool_calls", [])
    assert "web_search" in all_tools, (
        f"web_search not called. all_tool_calls: {all_tools}"
    )

    parsed = extract_json_from_reply(response["reply"])
    assert parsed is not None, "Could not parse JSON from reply"

    gaps = parsed.get("gaps", [])
    assert len(gaps) > 0, (
        "web_search was called but no gaps were identified — "
        "web search data not reflected in output"
    )


# --- Career Advisor: web_search required ---


@pytest.mark.asyncio
async def test_career_uses_web_search():
    """Career Advisor must call web_search for market data."""
    response = await chat(Q_CAREER_2)
    assert response["agent"] == "Career Advisor"

    all_tools = response.get("all_tool_calls", [])
    assert "web_search" in all_tools, (
        f"Career Advisor did not call web_search. "
        f"Career advice must be grounded in current market data. "
        f"all_tool_calls: {all_tools}"
    )


@pytest.mark.asyncio
async def test_career_web_search_reflected_in_output():
    """Web search results should set data_source to 'web_search'."""
    response = await chat(Q_CAREER_2)
    assert response["agent"] == "Career Advisor"

    all_tools = response.get("all_tool_calls", [])
    assert "web_search" in all_tools, (
        f"web_search not called. all_tool_calls: {all_tools}"
    )

    parsed = extract_json_from_reply(response["reply"])
    assert parsed is not None, "Could not parse JSON from reply"
    assert parsed.get("data_source") == "web_search", (
        f"data_source should be 'web_search' when web_search succeeds, "
        f"got: {parsed.get('data_source')}"
    )


# --- Learning Path Designer: web_search NOT expected ---


@pytest.mark.asyncio
async def test_learning_path_no_web_search():
    """Learning Path Designer should NOT call web_search.

    Learning paths are built from platform courses (retrieve_courses +
    get_course_details), not external market data. Calling web_search
    wastes tokens and adds latency without improving path quality.
    """
    response = await chat(Q_LEARNING_PATH)
    assert response["agent"] == "Learning Path Designer"

    all_tools = response.get("all_tool_calls", [])
    assert "web_search" not in all_tools, (
        f"Learning Path Designer should not call web_search — "
        f"paths are built from platform courses only. "
        f"all_tool_calls: {all_tools}"
    )
