"""End-to-end handoff tests — full flow from chat input to structured output.

Each test validates the complete pipeline:
  Explore page input → Learning Advisor → handoff → Specialist → structured JSON

These are integration tests that check routing + tool usage + output format
in a single pass.
"""

import pytest

from tests.eval.conftest import chat, extract_json_from_reply


@pytest.mark.asyncio
async def test_e2e_skill_gap():
    """Full handoff: user asks about skill gaps → Skill Gap Analyst responds."""
    response = await chat("What skills do I need to become a cloud architect?")

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
    response = await chat("Should I pursue a career in cybersecurity or cloud?")

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
    response = await chat("Design a 6-month study plan for AI and machine learning")

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
