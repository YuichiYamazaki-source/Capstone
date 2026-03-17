"""Skill Gap Analyst tests — JSON format, tool usage, output structure.

Validates that the agent produces structured output with required fields
and calls the expected tools.
"""

import pytest

from tests.eval.conftest import chat, extract_json_from_reply

REQUIRED_JSON_KEYS = {"target_role", "current_skills", "gaps", "summary"}
REQUIRED_GAP_KEYS = {"skill", "priority", "match_type", "courses"}


@pytest.mark.asyncio
async def test_skill_gap_json_format():
    """Skill Gap Analyst returns valid JSON with required keys."""
    response = await chat("What skills am I missing to become a data scientist?")
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
    response = await chat("Analyze my skill gaps for an ML Engineer role")
    all_tools = response.get("all_tool_calls", [])

    assert "web_search" in all_tools, (
        f"web_search not called. all_tool_calls: {all_tools}"
    )
    assert "retrieve_courses" in all_tools, (
        f"retrieve_courses not called. all_tool_calls: {all_tools}"
    )
