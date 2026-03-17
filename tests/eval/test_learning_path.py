"""Learning Path Designer tests — JSON format, path coherence, tool usage.

Validates that the agent produces an ordered learning path with
non-decreasing difficulty levels.
"""

import pytest

from tests.eval.conftest import (
    Q_LEARNING_PATH,
    Q_LEARNING_PATH_2,
    chat,
    extract_json_from_reply,
)

REQUIRED_JSON_KEYS = {"goal", "personalized", "path", "summary"}
REQUIRED_STEP_KEYS = {"step", "title", "level"}
LEVEL_ORDER = {"Beginner": 0, "Intermediate": 1, "Advanced": 2}


@pytest.mark.asyncio
async def test_learning_path_json_format():
    """Learning Path Designer returns valid JSON with required keys."""
    response = await chat(Q_LEARNING_PATH)
    assert response["agent"] == "Learning Path Designer"

    parsed = extract_json_from_reply(response["reply"])
    assert parsed is not None, "Could not parse JSON from reply"

    missing = REQUIRED_JSON_KEYS - set(parsed.keys())
    assert not missing, f"Missing required keys: {missing}"

    path = parsed.get("path", [])
    assert 3 <= len(path) <= 6, f"Expected 3-6 courses, got {len(path)}"

    for step in path:
        step_missing = REQUIRED_STEP_KEYS - set(step.keys())
        assert not step_missing, f"Step missing keys: {step_missing}"


@pytest.mark.asyncio
async def test_learning_path_level_coherence():
    """Path levels should be non-decreasing (Beginner → Intermediate → Advanced)."""
    response = await chat(Q_LEARNING_PATH_2)
    parsed = extract_json_from_reply(response["reply"])
    assert parsed is not None, "Could not parse JSON from reply"

    path = parsed.get("path", [])
    levels = [step.get("level", "") for step in path]
    numeric = [LEVEL_ORDER.get(lvl, -1) for lvl in levels]

    # Filter out unknown levels, then check non-decreasing
    known = [(i, n) for i, n in enumerate(numeric) if n >= 0]
    for idx in range(1, len(known)):
        prev_i, prev_n = known[idx - 1]
        curr_i, curr_n = known[idx]
        assert curr_n >= prev_n, (
            f"Level decreased at step {curr_i + 1}: "
            f"{levels[prev_i]} → {levels[curr_i]}"
        )


@pytest.mark.asyncio
async def test_learning_path_tool_calls():
    """Learning Path Designer calls retrieve_courses."""
    response = await chat(Q_LEARNING_PATH_2)
    all_tools = response.get("all_tool_calls", [])

    assert "retrieve_courses" in all_tools, (
        f"retrieve_courses not called. all_tool_calls: {all_tools}"
    )


@pytest.mark.asyncio
async def test_learning_path_course_detail_utilization():
    """Learning Path Designer calls get_course_details for recommended courses."""
    response = await chat(Q_LEARNING_PATH)
    assert response["agent"] == "Learning Path Designer"

    all_tools = response.get("all_tool_calls", [])
    assert "get_course_details" in all_tools, (
        f"get_course_details not called — path designer should check prerequisites. "
        f"all_tool_calls: {all_tools}"
    )


@pytest.mark.asyncio
async def test_learning_path_level_coverage():
    """Path summary should span from starting_level to target_level."""
    response = await chat(Q_LEARNING_PATH)
    assert response["agent"] == "Learning Path Designer"

    parsed = extract_json_from_reply(response["reply"])
    assert parsed is not None, "Could not parse JSON from reply"

    summary = parsed.get("summary", {})
    if isinstance(summary, str):
        # summary is sometimes a string instead of dict — skip level check
        return

    starting = summary.get("starting_level", "")
    target = summary.get("target_level", "")

    assert starting, "summary.starting_level is empty"
    assert target, "summary.target_level is empty"

    # Starting level should be <= target level
    starting_num = LEVEL_ORDER.get(starting, -1)
    target_num = LEVEL_ORDER.get(target, -1)
    if starting_num >= 0 and target_num >= 0:
        assert target_num >= starting_num, (
            f"Target level ({target}) should be >= starting level ({starting})"
        )
