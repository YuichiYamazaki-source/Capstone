"""Skill Gap Analyst tests — JSON format, tool usage, output structure.

Validates that the agent produces structured output with required fields
and calls the expected tools.
"""

import pytest

from tests.eval.conftest import Q_SKILL_GAP, Q_SKILL_GAP_2, chat, extract_json_from_reply

REQUIRED_JSON_KEYS = {"target_role", "current_skills", "gaps", "summary"}
REQUIRED_GAP_KEYS = {"skill", "priority", "match_type", "courses"}


@pytest.mark.asyncio
async def test_skill_gap_json_format():
    """Skill Gap Analyst returns valid JSON with required keys."""
    response = await chat(Q_SKILL_GAP)
    assert response["agent"] == "Skill Gap Analyst"

    parsed = extract_json_from_reply(response["reply"])
    assert parsed is not None, "Could not parse JSON from reply"

    missing = REQUIRED_JSON_KEYS - set(parsed.keys())
    assert not missing, f"Missing required keys: {missing}"

    # Validate gaps array structure
    gaps = parsed.get("gaps", [])
    assert len(gaps) > 0, "gaps array is empty"
    for gap in gaps:
        gap_missing = REQUIRED_GAP_KEYS - set(gap.keys())
        assert not gap_missing, f"Gap entry missing keys: {gap_missing}"
        assert gap["match_type"] in ("matched", "alternative"), (
            f"Invalid match_type: {gap['match_type']}"
        )


@pytest.mark.asyncio
async def test_skill_gap_tool_calls():
    """Skill Gap Analyst calls web_search and retrieve_courses."""
    response = await chat(Q_SKILL_GAP_2)
    all_tools = response.get("all_tool_calls", [])

    assert "web_search" in all_tools, (
        f"web_search not called. all_tool_calls: {all_tools}"
    )
    assert "retrieve_courses" in all_tools, (
        f"retrieve_courses not called. all_tool_calls: {all_tools}"
    )


@pytest.mark.asyncio
async def test_skill_gap_web_search_utilization():
    """Skill Gap Analyst uses web_search for market-driven skill requirements."""
    response = await chat(Q_SKILL_GAP_2)
    assert response["agent"] == "Skill Gap Analyst"

    all_tools = response.get("all_tool_calls", [])
    assert "web_search" in all_tools, (
        f"web_search not called — skill requirements should come from web search. "
        f"all_tool_calls: {all_tools}"
    )

    # Verify web_search data is reflected in output
    parsed = extract_json_from_reply(response["reply"])
    assert parsed is not None, "Could not parse JSON from reply"
    assert len(parsed.get("gaps", [])) > 0, "No gaps identified despite web_search call"
