"""Analyze endpoints — individual sub-agent calls for the Analysis page.

Three separate endpoints allow the frontend to run each analysis independently:
  - POST /analyze/skill-gap
  - POST /analyze/career
  - POST /analyze/learning-path

Also keeps the combined POST /analyze for backward compatibility.
"""

import asyncio
import json
import logging
import re
import time

from fastapi import APIRouter
from pydantic import BaseModel, Field, field_validator

from app.agent.career import career_agent
from app.agent.context import (
    reset_all_tool_calls,
    reset_collected_courses,
    reset_retrieval_args,
    reset_retrieval_tool_calls,
)
from app.agent.learning_path import learning_path_agent
from app.agent.skill_gap import skill_gap_agent
from app.config import settings
from app.observability import observe_function

router = APIRouter(tags=["analyze"])
logger = logging.getLogger("ai-service.analyze")

_OBJECT_ID_RE = re.compile(r"^[0-9a-fA-F]{24}$")
_JSON_BLOCK_RE = re.compile(r"```json\s*(.*?)\s*```", re.DOTALL)


class AnalyzeRequest(BaseModel):
    """Request body for the analyze endpoint."""

    user_id: str = Field(..., min_length=1)

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v: str) -> str:
        """Ensure user_id is a valid MongoDB ObjectId format."""
        if not _OBJECT_ID_RE.match(v):
            raise ValueError(
                "user_id must be a 24-character hex string (MongoDB ObjectId)"
            )
        return v


class SingleAnalyzeResponse(BaseModel):
    """Response from a single agent analysis."""

    result: dict = {}
    evidence: str = ""
    latency_ms: float = 0.0


class AnalyzeResponse(BaseModel):
    """Structured analysis response from all 3 sub-agents."""

    skill_gap: dict = {}
    career: dict = {}
    learning_path: dict = {}
    latency_ms: float = 0.0


def _extract_json_and_evidence(text: str) -> tuple[dict, str]:
    """Extract JSON and human-readable evidence from agent output.

    Returns:
        Tuple of (parsed_json, evidence_text).
        Evidence is the text after the JSON block.
    """
    match = _JSON_BLOCK_RE.search(text)
    if match:
        try:
            parsed = json.loads(match.group(1))
            # Evidence is everything after the JSON block
            evidence = text[match.end() :].strip()
            return parsed, evidence
        except json.JSONDecodeError:
            pass
    try:
        return json.loads(text), ""
    except (json.JSONDecodeError, TypeError):
        return {"raw_response": text}, text


async def _run_single_agent(agent, message: str, agent_name: str) -> tuple[dict, str]:
    """Run a single agent and return parsed JSON result + evidence.

    Returns:
        Tuple of (parsed_result, evidence_text).
    """
    from agents import Runner

    try:
        reset_collected_courses()
        reset_retrieval_tool_calls()
        reset_retrieval_args()
        reset_all_tool_calls()

        result = await Runner.run(agent, input=message)
        parsed, evidence = _extract_json_and_evidence(result.final_output)
        logger.info(
            "Agent completed",
            extra={"agent": agent_name, "output_keys": list(parsed.keys())},
        )
        return parsed, evidence
    except Exception as e:
        logger.error(
            "Agent failed",
            extra={"agent": agent_name, "error": str(e)},
        )
        return {"error": f"{agent_name} temporarily unavailable"}, ""


# --- Individual endpoints ---


@router.post("/analyze/skill-gap", response_model=SingleAnalyzeResponse)
@observe_function(name="analyze_skill_gap")
async def analyze_skill_gap(request: AnalyzeRequest):
    """Run Skill Gap Analyst for a single user."""
    start = time.perf_counter()
    user_context = f"[user_id: {request.user_id}]"

    result, evidence = await _run_single_agent(
        skill_gap_agent,
        f"{user_context} Analyze my skill gaps",
        "Skill Gap Analyst",
    )

    latency_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "Skill gap analysis completed",
        extra={"user_id": request.user_id, "latency_ms": round(latency_ms, 2)},
    )

    return SingleAnalyzeResponse(
        result=result,
        evidence=evidence,
        latency_ms=round(latency_ms, 2),
    )


@router.post("/analyze/career", response_model=SingleAnalyzeResponse)
@observe_function(name="analyze_career")
async def analyze_career(request: AnalyzeRequest):
    """Run Career Advisor for a single user."""
    start = time.perf_counter()
    user_context = f"[user_id: {request.user_id}]"

    result, evidence = await _run_single_agent(
        career_agent,
        f"{user_context} What career paths fit my profile?",
        "Career Advisor",
    )

    latency_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "Career analysis completed",
        extra={"user_id": request.user_id, "latency_ms": round(latency_ms, 2)},
    )

    return SingleAnalyzeResponse(
        result=result,
        evidence=evidence,
        latency_ms=round(latency_ms, 2),
    )


@router.post("/analyze/learning-path", response_model=SingleAnalyzeResponse)
@observe_function(name="analyze_learning_path")
async def analyze_learning_path(request: AnalyzeRequest):
    """Run Learning Path Designer for a single user."""
    start = time.perf_counter()
    user_context = f"[user_id: {request.user_id}]"

    result, evidence = await _run_single_agent(
        learning_path_agent,
        f"{user_context} Create a learning path",
        "Learning Path Designer",
    )

    latency_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "Learning path analysis completed",
        extra={"user_id": request.user_id, "latency_ms": round(latency_ms, 2)},
    )

    return SingleAnalyzeResponse(
        result=result,
        evidence=evidence,
        latency_ms=round(latency_ms, 2),
    )


# --- Combined endpoint (backward compatibility) ---


@router.post("/analyze", response_model=AnalyzeResponse)
@observe_function(name="analyze_request")
async def analyze(request: AnalyzeRequest):
    """Run all 3 sub-agents in parallel for comprehensive analysis."""
    start = time.perf_counter()
    user_id = request.user_id
    user_context = f"[user_id: {user_id}]"

    results = await asyncio.gather(
        _run_single_agent(
            skill_gap_agent,
            f"{user_context} Analyze my skill gaps",
            "Skill Gap Analyst",
        ),
        _run_single_agent(
            career_agent,
            f"{user_context} What career paths fit my profile?",
            "Career Advisor",
        ),
        _run_single_agent(
            learning_path_agent,
            f"{user_context} Create a learning path",
            "Learning Path Designer",
        ),
    )

    latency_ms = (time.perf_counter() - start) * 1000

    logger.info(
        "Analysis completed",
        extra={
            "user_id": user_id,
            "latency_ms": round(latency_ms, 2),
            "model": settings.openai_model,
        },
    )

    return AnalyzeResponse(
        skill_gap=results[0][0],
        career=results[1][0],
        learning_path=results[2][0],
        latency_ms=round(latency_ms, 2),
    )
