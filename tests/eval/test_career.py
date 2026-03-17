"""Career Advisor tests — JSON format, tool usage, output structure.

Validates that the agent produces structured career guidance with
web search data and action plans.
"""

import pytest

from tests.eval.conftest import Q_CAREER, Q_CAREER_2, chat, extract_json_from_reply

REQUIRED_JSON_KEYS = {"career_paths", "recommendation", "data_source"}
REQUIRED_PATH_KEYS = {"role", "required_skills", "recommended_courses", "action_plan"}


@pytest.mark.asyncio
async def test_career_json_format():
    """Career Advisor returns valid JSON with required keys."""
    response = await chat(Q_CAREER)
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
    response = await chat(Q_CAREER_2)
    all_tools = response.get("all_tool_calls", [])

    assert "web_search" in all_tools, (
        f"web_search not called. all_tool_calls: {all_tools}"
    )


@pytest.mark.asyncio
async def test_career_web_search_utilization():
    """Career Advisor reflects web_search results in data_source field."""
    response = await chat(Q_CAREER_2)
    assert response["agent"] == "Career Advisor"

    all_tools = response.get("all_tool_calls", [])
    assert "web_search" in all_tools, (
        f"web_search not called — career advice must be grounded in market data. "
        f"all_tool_calls: {all_tools}"
    )

    parsed = extract_json_from_reply(response["reply"])
    assert parsed is not None, "Could not parse JSON from reply"
    assert parsed.get("data_source") == "web_search", (
        f"data_source should be 'web_search' when web_search succeeds, "
        f"got: {parsed.get('data_source')}"
    )


@pytest.mark.asyncio
async def test_career_action_plan_structure():
    """Career Advisor provides action plans with timeline."""
    response = await chat(Q_CAREER)
    assert response["agent"] == "Career Advisor"

    parsed = extract_json_from_reply(response["reply"])
    assert parsed is not None, "Could not parse JSON from reply"

    paths = parsed.get("career_paths", [])
    assert len(paths) > 0, "No career paths provided"

    for path in paths:
        action_plan = path.get("action_plan", [])
        assert len(action_plan) > 0, (
            f"Career path '{path.get('role')}' has no action plan"
        )
        for step in action_plan:
            assert "month" in step, f"Action plan step missing 'month': {step}"
            assert "action" in step, f"Action plan step missing 'action': {step}"
