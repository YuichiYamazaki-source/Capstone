"""Career Advisor tests — JSON format, tool usage, output structure.

Validates that the agent produces structured career guidance with
web search data and action plans.
"""

import pytest

from tests.eval.conftest import chat, extract_json_from_reply

REQUIRED_JSON_KEYS = {"career_paths", "recommendation", "data_source"}
REQUIRED_PATH_KEYS = {"role", "required_skills", "recommended_courses", "action_plan"}


@pytest.mark.asyncio
async def test_career_json_format():
    """Career Advisor returns valid JSON with required keys."""
    response = await chat("What career path should I take in AI?")
    assert response["agent"] == "Career Advisor"

    parsed = extract_json_from_reply(response["reply"])
    assert parsed is not None, "Could not parse JSON from reply"

    missing = REQUIRED_JSON_KEYS - set(parsed.keys())
    assert not missing, f"Missing required keys: {missing}"

    paths = parsed.get("career_paths", [])
    assert len(paths) > 0, "career_paths array is empty"
    for path in paths:
        path_missing = REQUIRED_PATH_KEYS - set(path.keys())
        assert not path_missing, f"Career path missing keys: {path_missing}"


@pytest.mark.asyncio
async def test_career_uses_web_search():
    """Career Advisor calls web_search for market data."""
    response = await chat("What's the job market like for data engineers?")
    all_tools = response.get("all_tool_calls", [])

    assert "web_search" in all_tools, (
        f"web_search not called. all_tool_calls: {all_tools}"
    )
