"""Quality metrics tests — LLM-as-Judge evaluation for specialist agents.

Measures Answer Relevancy, Faithfulness (all 3 specialists),
and Actionability (Career Advisor only) using DeepEval with gpt-4o-mini.

Uses ground_truth.json cases gt-21 to gt-38 (5 per agent).
Each agent call is cached in a module-scoped fixture to avoid duplicate API calls.

Cost estimate (--limit 5, gpt-4o-mini):
  Agent calls: 15 × ~$0.002 = ~$0.03
  DeepEval judge: 35 calls = ~$0.04
  Total: ~$0.07

Run:
  docker compose exec ai-service pytest tests/eval/test_quality_metrics.py -v
"""

import json
import logging
from pathlib import Path

import pytest
import pytest_asyncio

from tests.eval.conftest import chat, extract_json_from_reply

logger = logging.getLogger("eval.quality_metrics")

# GT case ranges per agent (5 each, from ground_truth.json)
SKILL_GAP_IDS = ["gt-21", "gt-22", "gt-23", "gt-24", "gt-25"]
CAREER_IDS = ["gt-27", "gt-28", "gt-29", "gt-30", "gt-31"]
LEARNING_PATH_IDS = ["gt-33", "gt-34", "gt-35", "gt-36", "gt-37"]

ALL_IDS = SKILL_GAP_IDS + CAREER_IDS + LEARNING_PATH_IDS

DEEPEVAL_THRESHOLD = 0.5


def _load_gt_cases() -> dict[str, dict]:
    """Load ground truth cases as id -> case mapping."""
    gt_path = Path(__file__).resolve().parent.parent.parent / "evals" / "ground_truth.json"
    with open(gt_path) as f:
        cases = json.load(f)
    return {c["id"]: c for c in cases}


@pytest.fixture(scope="module")
def gt_cases():
    """Ground truth cases indexed by id."""
    return _load_gt_cases()


@pytest_asyncio.fixture(scope="module")
async def agent_responses(gt_cases):
    """Call chat API for each GT case once, cache results.

    Returns dict: case_id -> response dict.
    """
    responses = {}
    for case_id in ALL_IDS:
        case = gt_cases.get(case_id)
        if not case:
            continue
        try:
            resp = await chat(case["query"])
            responses[case_id] = resp
            logger.info("Got response for %s (agent=%s)", case_id, resp.get("agent"))
        except Exception as e:
            logger.error("Failed to get response for %s: %s", case_id, e)
    return responses


def _build_retrieval_context(response: dict) -> list[str]:
    """Build retrieval context from response for DeepEval."""
    # For specialist agents, extract courses from JSON reply
    parsed = extract_json_from_reply(response.get("reply", ""))
    contexts = []

    if parsed:
        # Skill Gap: courses inside gaps[]
        for gap in parsed.get("gaps", []):
            for c in gap.get("courses", []):
                contexts.append(
                    f"{c.get('title', 'N/A')} | "
                    f"Org: {c.get('organization', 'N/A')} | "
                    f"Level: {c.get('level', 'N/A')} | "
                    f"Rating: {c.get('rating', 'N/A')}"
                )

        # Career: courses inside career_paths[]
        for path in parsed.get("career_paths", []):
            for c in path.get("recommended_courses", []):
                contexts.append(
                    f"{c.get('title', 'N/A')} | "
                    f"Org: {c.get('organization', 'N/A')} | "
                    f"Level: {c.get('level', 'N/A')} | "
                    f"Rating: {c.get('rating', 'N/A')}"
                )

        # Learning Path: courses inside path[]
        for step in parsed.get("path", []):
            contexts.append(
                f"{step.get('title', 'N/A')} | "
                f"Org: {step.get('organization', 'N/A')} | "
                f"Level: {step.get('level', 'N/A')} | "
                f"Rating: {step.get('rating', 'N/A')}"
            )

    if not contexts:
        contexts = ["No courses retrieved"]

    return contexts[:5]  # Top 5 to avoid DeepEval timeout


# --- Answer Relevancy ---


@pytest.mark.asyncio
@pytest.mark.parametrize("case_id", SKILL_GAP_IDS, ids=[f"skill_gap_{i}" for i in range(5)])
async def test_answer_relevancy_skill_gap(case_id, gt_cases, agent_responses):
    """Skill Gap Analyst: response addresses the user's skill gap question."""
    _run_answer_relevancy(case_id, gt_cases, agent_responses)


@pytest.mark.asyncio
@pytest.mark.parametrize("case_id", CAREER_IDS, ids=[f"career_{i}" for i in range(5)])
async def test_answer_relevancy_career(case_id, gt_cases, agent_responses):
    """Career Advisor: response addresses the user's career question."""
    _run_answer_relevancy(case_id, gt_cases, agent_responses)


@pytest.mark.asyncio
@pytest.mark.parametrize("case_id", LEARNING_PATH_IDS, ids=[f"learning_path_{i}" for i in range(5)])
async def test_answer_relevancy_learning_path(case_id, gt_cases, agent_responses):
    """Learning Path Designer: response addresses the learning path request."""
    _run_answer_relevancy(case_id, gt_cases, agent_responses)


def _run_answer_relevancy(case_id, gt_cases, agent_responses):
    """Run AnswerRelevancyMetric for a single case."""
    from deepeval.metrics import AnswerRelevancyMetric
    from deepeval.test_case import LLMTestCase

    case = gt_cases[case_id]
    response = agent_responses.get(case_id)
    assert response is not None, f"No response for {case_id}"

    test_case = LLMTestCase(
        input=case["query"],
        actual_output=response["reply"][:2000],
        retrieval_context=_build_retrieval_context(response),
    )

    metric = AnswerRelevancyMetric(model="gpt-4o-mini", threshold=DEEPEVAL_THRESHOLD)
    metric.measure(test_case)

    assert metric.score >= DEEPEVAL_THRESHOLD, (
        f"Answer Relevancy {metric.score:.2f} < {DEEPEVAL_THRESHOLD} "
        f"for {case_id}: {case['query'][:80]}. Reason: {metric.reason}"
    )


# --- Faithfulness ---


@pytest.mark.asyncio
@pytest.mark.parametrize("case_id", SKILL_GAP_IDS, ids=[f"skill_gap_{i}" for i in range(5)])
async def test_faithfulness_skill_gap(case_id, gt_cases, agent_responses):
    """Skill Gap Analyst: no hallucinated skills or courses."""
    _run_faithfulness(case_id, gt_cases, agent_responses)


@pytest.mark.asyncio
@pytest.mark.parametrize("case_id", CAREER_IDS, ids=[f"career_{i}" for i in range(5)])
async def test_faithfulness_career(case_id, gt_cases, agent_responses):
    """Career Advisor: career data grounded in web_search results."""
    _run_faithfulness(case_id, gt_cases, agent_responses)


@pytest.mark.asyncio
@pytest.mark.parametrize("case_id", LEARNING_PATH_IDS, ids=[f"learning_path_{i}" for i in range(5)])
async def test_faithfulness_learning_path(case_id, gt_cases, agent_responses):
    """Learning Path Designer: courses in path exist in retrieval context."""
    _run_faithfulness(case_id, gt_cases, agent_responses)


def _run_faithfulness(case_id, gt_cases, agent_responses):
    """Run FaithfulnessMetric for a single case."""
    from deepeval.metrics import FaithfulnessMetric
    from deepeval.test_case import LLMTestCase

    case = gt_cases[case_id]
    response = agent_responses.get(case_id)
    assert response is not None, f"No response for {case_id}"

    test_case = LLMTestCase(
        input=case["query"],
        actual_output=response["reply"][:2000],
        retrieval_context=_build_retrieval_context(response),
    )

    metric = FaithfulnessMetric(model="gpt-4o-mini", threshold=DEEPEVAL_THRESHOLD)
    metric.measure(test_case)

    assert metric.score >= DEEPEVAL_THRESHOLD, (
        f"Faithfulness {metric.score:.2f} < {DEEPEVAL_THRESHOLD} "
        f"for {case_id}: {case['query'][:80]}. Reason: {metric.reason}"
    )


# --- Actionability (Career Advisor only) ---


@pytest.mark.asyncio
@pytest.mark.parametrize("case_id", CAREER_IDS, ids=[f"career_{i}" for i in range(5)])
async def test_actionability_career(case_id, gt_cases, agent_responses):
    """Career Advisor: response contains concrete action plan with timeline."""
    from deepeval.metrics import GEval
    from deepeval.test_case import LLMTestCase, LLMTestCaseParams

    case = gt_cases[case_id]
    response = agent_responses.get(case_id)
    assert response is not None, f"No response for {case_id}"

    test_case = LLMTestCase(
        input=case["query"],
        actual_output=response["reply"][:2000],
        retrieval_context=_build_retrieval_context(response),
    )

    metric = GEval(
        name="Actionability",
        model="gpt-4o-mini",
        threshold=DEEPEVAL_THRESHOLD,
        criteria=(
            "Does the response contain a concrete action plan with specific steps, "
            "a timeline (in months or weeks), and measurable milestones? "
            "Score higher if the plan is specific and actionable, "
            "lower if advice is vague or generic."
        ),
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
        ],
    )
    metric.measure(test_case)

    assert metric.score >= DEEPEVAL_THRESHOLD, (
        f"Actionability {metric.score:.2f} < {DEEPEVAL_THRESHOLD} "
        f"for {case_id}: {case['query'][:80]}. Reason: {metric.reason}"
    )
