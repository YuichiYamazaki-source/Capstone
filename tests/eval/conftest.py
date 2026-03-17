"""Shared fixtures for agent evaluation tests.

All tests call the Chat API through the gateway, same as a real user
on the Explore page. The OPENAI_MODEL env var controls which model
the agents use (default: gpt-4o-mini for testing).

Response caching: chat() caches responses by query string so that
identical queries across test files only hit the API once per session.

To add new test cases:
  1. Add entries to tests/eval/cases/*.json (or inline via pytest.mark.parametrize)
  2. Run: docker compose exec ai-service pytest tests/eval/ -v
"""

import json
import os
import re
from pathlib import Path

import httpx
import pytest

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://gateway:8000")
TIMEOUT = 180.0

# --- Canonical queries (shared across test files for cache hits) ---

Q_SKILL_GAP = "What skills am I missing to become a data scientist?"
Q_SKILL_GAP_2 = "Analyze my skill gaps for an ML Engineer role"
Q_CAREER = "What career path should I take in AI?"
Q_CAREER_2 = "What's the job market like for data engineers?"
Q_LEARNING_PATH = "Create a learning path for web development from beginner to advanced"
Q_LEARNING_PATH_2 = "Build a step-by-step curriculum for data science"
Q_GREETING = "Hello!"
Q_COURSE_SEARCH = "Find me Python courses"


# --- Response cache ---

_response_cache: dict[str, dict] = {}


@pytest.fixture(scope="session")
def gateway_url():
    """Base URL for the gateway API."""
    return GATEWAY_URL


@pytest.fixture(scope="session")
def ground_truth():
    """Load full ground truth dataset."""
    gt_path = Path(__file__).resolve().parent.parent.parent / "evals" / "ground_truth.json"
    with open(gt_path) as f:
        return json.load(f)


async def chat(message: str, user_id: str | None = None) -> dict:
    """Send a message to the chat API and return the response.

    This is the same entry point as the Explore page.
    Responses are cached by (message, user_id) to avoid duplicate API calls.
    """
    cache_key = f"{message}|{user_id or ''}"
    if cache_key in _response_cache:
        return _response_cache[cache_key]

    payload = {"message": message}
    if user_id:
        payload["user_id"] = user_id

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(
            f"{GATEWAY_URL}/api/v1/chat",
            json=payload,
        )
        resp.raise_for_status()
        result = resp.json()

    _response_cache[cache_key] = result
    return result


def extract_json_from_reply(reply: str) -> dict | None:
    """Extract JSON object from agent reply text.

    Agents wrap JSON in markdown code blocks (```json ... ```).
    Falls back to finding the first { ... } block.
    """
    # Try markdown code block first
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", reply, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Fallback: find outermost { ... }
    match = re.search(r"\{.*\}", reply, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return None
