"""End-to-end handoff tests — full flow from chat input to structured output.

Each test validates the complete pipeline:
  Explore page input → Learning Advisor → handoff → Specialist → structured JSON

Uses canonical queries (cached) to avoid redundant API calls.
"""

import pytest

from tests.eval.conftest import (
    Q_CAREER,
    Q_LEARNING_PATH,
    Q_SKILL_GAP,
    chat,
    extract_json_from_reply,
)


@pytest.mark.asyncio
async def test_e2e_skill_gap():
    """Full handoff: user asks about skill gaps → Skill Gap Analyst responds."""
    response = await chat(Q_SKILL_GAP)

    # Routing
    assert response["agent"] == "Skill Gap Analyst"

    # Tool usage
    all_tools = response.get("all_tool_calls", [])
    assert "web_search" in all_tools
    assert "retrieve_courses" in all_tools

    # Output structure
    parsed = extract_json_from_reply(response["reply"])
    assert parsed is not None
    assert "gaps" in parsed
    assert len(parsed["gaps"]) > 0


@pytest.mark.asyncio
async def test_e2e_career():
    """Full handoff: user asks about careers → Career Advisor responds."""
    response = await chat(Q_CAREER)

    # Routing
    assert response["agent"] == "Career Advisor"

    # Tool usage
    all_tools = response.get("all_tool_calls", [])
    assert "web_search" in all_tools

    # Output structure
    parsed = extract_json_from_reply(response["reply"])
    assert parsed is not None
    assert "career_paths" in parsed


@pytest.mark.asyncio
async def test_e2e_learning_path():
    """Full handoff: user asks for a study plan → Learning Path Designer responds."""
    response = await chat(Q_LEARNING_PATH)

    # Routing
    assert response["agent"] == "Learning Path Designer"

    # Tool usage
    all_tools = response.get("all_tool_calls", [])
    assert "retrieve_courses" in all_tools

    # Output structure
    parsed = extract_json_from_reply(response["reply"])
    assert parsed is not None
    assert "path" in parsed
    assert len(parsed["path"]) >= 3
