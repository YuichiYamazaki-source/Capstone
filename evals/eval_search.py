"""Evaluation runner for course search pipeline.

Runs IR metrics (no LLM cost) and optionally LLM-as-Judge via DeepEval.
Results are saved locally and optionally uploaded to LangFuse.

Usage (from project root):
    # IR metrics only (no API cost)
    python -m evals.eval_search --hit-rate-only

    # Full evaluation with LLM-as-Judge (~$0.05-0.10 per case with gpt-4o-mini)
    python -m evals.eval_search

    # Limit test cases for debugging
    python -m evals.eval_search --limit 3

    # Tag version for LangFuse comparison
    python -m evals.eval_search --version v1.0
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Fix Windows cp932 encoding: DeepEval outputs Unicode (emojis etc.)
# that cannot be encoded in the default Windows console encoding.
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv

load_dotenv("local/.env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("eval")

GROUND_TRUTH_PATH = Path(__file__).parent / "ground_truth.json"
RESULTS_DIR = Path(__file__).parent / "results"


def load_ground_truth(limit: int | None = None) -> list[dict]:
    """Load ground truth test cases."""
    with open(GROUND_TRUTH_PATH) as f:
        cases = json.load(f)
    if limit:
        cases = cases[:limit]
    logger.info("Loaded %d ground truth cases", len(cases))
    return cases


async def search_courses(query: str) -> dict:
    """Call the chat API and return structured response."""
    import httpx

    gateway_url = os.getenv("GATEWAY_URL", "http://localhost:8000")

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{gateway_url}/api/v1/chat",
            json={"message": query},
        )
        resp.raise_for_status()
        data = resp.json()

    return {
        "reply": data.get("reply", ""),
        "courses": data.get("courses", []),
        "tool_calls": data.get("tool_calls", []),
        "retrieval_tool_calls": data.get("retrieval_tool_calls", []),
        "retrieval_args": data.get("retrieval_args", {}),
        "latency_ms": data.get("latency_ms", 0),
        "agent": data.get("agent", "Learning Advisor"),
    }


def run_ir_eval(cases: list[dict], results_map: dict) -> dict:
    """Compute IR metrics (Hit Rate, Precision@K, Recall@K) for each case.

    Skips filter-only cases (empty expected_titles) — those are evaluated
    by run_filter_eval instead.
    """
    from evals.metrics import hit_rate, precision_at_k, recall_at_k

    ir_details = []
    total_hit = 0.0
    total_precision = 0.0
    total_recall = 0.0

    for case in cases:
        case_id = case["id"]
        result = results_map.get(case_id)
        if not result:
            continue

        expected_titles = case["expected_titles"]
        if not expected_titles:
            continue  # Filter-only case — skip IR metrics

        retrieved_titles = [c.get("title", "") for c in result["courses"]]

        hr = hit_rate(retrieved_titles, expected_titles)
        pk = precision_at_k(retrieved_titles, expected_titles, k=5)
        rk = recall_at_k(retrieved_titles, expected_titles, k=5)

        total_hit += hr
        total_precision += pk
        total_recall += rk

        ir_details.append(
            {
                "id": case_id,
                "query": case["query"],
                "hit_rate": hr,
                "precision_at_5": round(pk, 4),
                "recall_at_5": round(rk, 4),
                "retrieved_count": len(retrieved_titles),
                "retrieved_titles": retrieved_titles[:5],
                "expected_titles": expected_titles,
            }
        )

    n = len(ir_details) or 1
    return {
        "total_cases": len(ir_details),
        "avg_hit_rate": round(total_hit / n, 4),
        "avg_precision_at_5": round(total_precision / n, 4),
        "avg_recall_at_5": round(total_recall / n, 4),
        "details": ir_details,
    }


def run_filter_eval(cases: list[dict], results_map: dict) -> dict:
    """Evaluate filter-type queries: parameter extraction + result satisfaction.

    Only runs on cases that have filter_check defined.
    """
    from evals.metrics import filter_param_accuracy, filter_satisfaction

    details = []
    total_satisfaction = 0.0
    total_param_accuracy = 0.0

    for case in cases:
        filter_check = case.get("filter_check")
        if not filter_check:
            continue

        case_id = case["id"]
        result = results_map.get(case_id)
        if not result:
            continue

        courses = result.get("courses", [])
        retrieval_args = result.get("retrieval_args", {})
        expected_params = case.get("filter_params", {})

        # Check: did ALL returned courses satisfy the filter?
        fs = filter_satisfaction(courses, filter_check)

        # Check: did the LLM extract the right parameters?
        pa = filter_param_accuracy(retrieval_args, expected_params)

        total_satisfaction += fs
        total_param_accuracy += pa["accuracy"]

        details.append(
            {
                "id": case_id,
                "query": case["query"],
                "filter_satisfaction": round(fs, 4),
                "param_accuracy": round(pa["accuracy"], 4),
                "param_details": pa["details"],
                "expected_params": expected_params,
                "actual_args": {
                    "level": retrieval_args.get("level", ""),
                    "min_rating": retrieval_args.get("min_rating", 0.0),
                    "organization": retrieval_args.get("organization", ""),
                },
                "retrieved_count": len(courses),
                "retrieved_titles": [c.get("title", "") for c in courses[:5]],
            }
        )

    n = len(details) or 1
    return {
        "total_cases": len(details),
        "avg_filter_satisfaction": round(total_satisfaction / n, 4),
        "avg_param_accuracy": round(total_param_accuracy / n, 4),
        "details": details,
    }


def run_tool_selection_eval(cases: list[dict], results_map: dict) -> dict:
    """Evaluate tool selection at the Learning Advisor level.

    Checks: did Learning Advisor call retrieve_courses for course queries?
    Retrieval-level tool selection is no longer evaluated because hybrid search
    is deterministic (always runs keyword + semantic + filter).
    """
    advisor_correct = 0
    details = []

    for case in cases:
        case_id = case["id"]
        result = results_map.get(case_id)
        if not result:
            continue

        advisor_tools = result.get("tool_calls", [])
        advisor_match = "retrieve_courses" in advisor_tools
        if advisor_match:
            advisor_correct += 1

        details.append(
            {
                "id": case_id,
                "query": case["query"],
                "advisor_tools": advisor_tools,
                "advisor_match": advisor_match,
                "retrieval_method": result.get("retrieval_tool_calls", []),
            }
        )

    n = len(details) or 1
    return {
        "total_cases": len(details),
        "advisor_accuracy": round(advisor_correct / n, 4),
        "details": details,
    }


def run_agent_routing_eval(cases: list[dict], results_map: dict) -> dict:
    """Evaluate agent routing accuracy.

    Checks: did the orchestrator hand off to the expected specialist agent?
    Only runs on cases that have expected_agent defined.
    """
    routing_cases = [c for c in cases if c.get("expected_agent")]
    if not routing_cases:
        return {"total_cases": 0, "routing_accuracy": 0, "details": []}

    correct = 0
    details = []

    for case in routing_cases:
        case_id = case["id"]
        result = results_map.get(case_id)
        if not result:
            continue

        expected = case["expected_agent"]
        actual = result.get("agent", "Learning Advisor")
        match = actual == expected

        if match:
            correct += 1

        details.append(
            {
                "id": case_id,
                "query": case["query"],
                "expected_agent": expected,
                "actual_agent": actual,
                "match": match,
            }
        )

    n = len(details) or 1
    return {
        "total_cases": len(details),
        "routing_accuracy": round(correct / n, 4),
        "details": details,
    }


def run_deepeval(cases: list[dict], results_map: dict) -> dict:
    """Run LLM-as-Judge evaluation using DeepEval."""
    from deepeval import evaluate
    from deepeval.evaluate.configs import AsyncConfig, DisplayConfig
    from deepeval.metrics import (
        AnswerRelevancyMetric,
        ContextualRelevancyMetric,
        FaithfulnessMetric,
    )
    from deepeval.test_case import LLMTestCase

    test_cases = []
    case_ids = []

    for case in cases:
        case_id = case["id"]
        result = results_map.get(case_id)
        if not result:
            continue

        # Truncate actual_output to avoid DeepEval timeout on long agent responses
        actual_output = result["reply"][:2000]
        courses = result["courses"][:5]  # Top 5 only for evaluation

        retrieval_context = [
            f"{c.get('title', 'N/A')} | "
            f"Org: {c.get('organization', 'N/A')} | "
            f"Level: {c.get('level', 'N/A')} | "
            f"Rating: {c.get('rating', 'N/A')} | "
            f"Skills: {', '.join(c.get('skills', [])[:3])}"
            for c in courses
        ]

        if not retrieval_context:
            retrieval_context = ["No courses retrieved"]

        test_cases.append(
            LLMTestCase(
                input=case["query"],
                actual_output=actual_output,
                retrieval_context=retrieval_context,
            )
        )
        case_ids.append(case_id)

    if not test_cases:
        return {"total_cases": 0, "details": [], "aggregate": {}}

    metrics = [
        AnswerRelevancyMetric(model="gpt-4o-mini", threshold=0.5),
        FaithfulnessMetric(model="gpt-4o-mini", threshold=0.5),
        ContextualRelevancyMetric(model="gpt-4o-mini", threshold=0.5),
    ]

    logger.info(
        "Running DeepEval with %d test cases and %d metrics",
        len(test_cases),
        len(metrics),
    )

    eval_results = evaluate(
        test_cases=test_cases,
        metrics=metrics,
        async_config=AsyncConfig(run_async=False),
        display_config=DisplayConfig(print_results=False),
    )

    # Parse results
    per_case = []
    totals = {"answer_relevancy": 0, "faithfulness": 0, "contextual_relevancy": 0}

    for i, result in enumerate(eval_results.test_results):
        scores = {}
        for metric_result in result.metrics_data:
            metric_name = metric_result.name.lower().replace(" ", "_")
            score = metric_result.score or 0.0
            scores[metric_name] = round(score, 4)
            if metric_name in totals:
                totals[metric_name] += score

        per_case.append(
            {
                "id": case_ids[i] if i < len(case_ids) else f"case-{i}",
                "scores": scores,
            }
        )

    n = len(per_case) or 1
    aggregate = {k: round(v / n, 4) for k, v in totals.items()}

    return {
        "total_cases": len(per_case),
        "per_case": per_case,
        "aggregate": aggregate,
    }


def _save_results(output: dict) -> Path:
    """Save results to JSON file. Always succeeds or raises to stderr."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    result_path = RESULTS_DIR / f"{timestamp}.json"
    with open(result_path, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    return result_path


async def main():  # noqa: C901
    """CLI entry point for running course search evaluation."""
    parser = argparse.ArgumentParser(description="Run course search evaluation")
    parser.add_argument(
        "--hit-rate-only",
        action="store_true",
        help="Skip LLM-as-Judge (IR metrics only)",
    )
    parser.add_argument(
        "--version", default="v1.0", help="Version tag for LangFuse tracking"
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="Limit number of test cases"
    )
    args = parser.parse_args()

    cases = load_ground_truth(args.limit)

    # Accumulate output incrementally so partial results are never lost
    output = {
        "timestamp": datetime.now(UTC).isoformat(),
        "version": args.version,
        "errors": [],
    }

    # Phase 1: Run queries through the API
    results_map = {}
    try:
        logger.info("Running %d queries through chat API...", len(cases))
        for case in cases:
            logger.info("  Query: %s", case["query"][:60])
            try:
                result = await search_courses(case["query"])
                results_map[case["id"]] = result
            except Exception as e:
                logger.error("  Failed: %s", e)
                results_map[case["id"]] = {
                    "reply": "",
                    "courses": [],
                    "tool_calls": [],
                    "latency_ms": 0,
                }
                output["errors"].append(
                    {"phase": "api_call", "case": case["id"], "error": str(e)}
                )
    except Exception as e:
        logger.error("API phase crashed: %s", e)
        output["errors"].append({"phase": "api_calls", "error": str(e)})

    # Phase 2: IR metrics (no cost)
    try:
        logger.info("Computing IR metrics...")
        ir_results = run_ir_eval(cases, results_map)
        output["ir_metrics"] = ir_results
        logger.info(
            "IR Results: hit_rate=%.2f, precision@5=%.4f, recall@5=%.4f",
            ir_results["avg_hit_rate"],
            ir_results["avg_precision_at_5"],
            ir_results["avg_recall_at_5"],
        )
    except Exception as e:
        logger.error("IR metrics failed: %s", e)
        output["errors"].append({"phase": "ir_metrics", "error": str(e)})

    # Phase 3: Tool Selection eval (no cost)
    try:
        logger.info("Computing Tool Selection metrics...")
        tool_results = run_tool_selection_eval(cases, results_map)
        output["tool_selection"] = tool_results
        logger.info(
            "Tool Selection: advisor=%.2f",
            tool_results["advisor_accuracy"],
        )
    except Exception as e:
        logger.error("Tool Selection eval failed: %s", e)
        output["errors"].append({"phase": "tool_selection", "error": str(e)})

    # Phase 3b: Filter evaluation (no cost)
    filter_cases = [c for c in cases if c.get("filter_check")]
    if filter_cases:
        try:
            logger.info("Computing Filter metrics (%d cases)...", len(filter_cases))
            filter_results = run_filter_eval(cases, results_map)
            output["filter_eval"] = filter_results
            logger.info(
                "Filter: satisfaction=%.2f, param_accuracy=%.2f",
                filter_results["avg_filter_satisfaction"],
                filter_results["avg_param_accuracy"],
            )
        except Exception as e:
            logger.error("Filter eval failed: %s", e)
            output["errors"].append({"phase": "filter_eval", "error": str(e)})

    # Phase 3c: Agent routing evaluation (no cost)
    routing_cases = [c for c in cases if c.get("expected_agent")]
    if routing_cases:
        try:
            logger.info(
                "Computing Agent Routing metrics (%d cases)...", len(routing_cases)
            )
            routing_results = run_agent_routing_eval(cases, results_map)
            output["agent_routing"] = routing_results
            logger.info(
                "Agent Routing: accuracy=%.2f",
                routing_results["routing_accuracy"],
            )
        except Exception as e:
            logger.error("Agent Routing eval failed: %s", e)
            output["errors"].append({"phase": "agent_routing", "error": str(e)})

    # Phase 4: Latency stats
    try:
        latencies = [
            r["latency_ms"] for r in results_map.values() if r["latency_ms"] > 0
        ]
        latency_stats = {}
        if latencies:
            latencies_sorted = sorted(latencies)
            latency_stats = {
                "p50": round(latencies_sorted[len(latencies_sorted) // 2], 2),
                "p95": round(latencies_sorted[int(len(latencies_sorted) * 0.95)], 2),
                "p99": round(latencies_sorted[int(len(latencies_sorted) * 0.99)], 2),
                "avg": round(sum(latencies) / len(latencies), 2),
            }
            logger.info(
                "Latency: p50=%.0fms, p95=%.0fms, avg=%.0fms",
                latency_stats["p50"],
                latency_stats["p95"],
                latency_stats["avg"],
            )
        output["latency"] = latency_stats
    except Exception as e:
        logger.error("Latency stats failed: %s", e)
        output["errors"].append({"phase": "latency", "error": str(e)})

    # Phase 5: LLM-as-Judge (optional, costs money)
    if not args.hit_rate_only:
        try:
            logger.info("Running LLM-as-Judge evaluation...")
            llm_judge_results = run_deepeval(cases, results_map)
            output["llm_judge"] = llm_judge_results
            if llm_judge_results.get("aggregate"):
                agg = llm_judge_results["aggregate"]
                logger.info(
                    "DeepEval: answer_relevancy=%.4f, faithfulness=%.4f, contextual_relevancy=%.4f",
                    agg.get("answer_relevancy", 0),
                    agg.get("faithfulness", 0),
                    agg.get("contextual_relevancy", 0),
                )
        except Exception as e:
            logger.error("DeepEval failed: %s", e)
            output["errors"].append({"phase": "deepeval", "error": str(e)})

    # Always save results (even if some phases failed)
    if not output["errors"]:
        del output["errors"]

    result_path = _save_results(output)
    logger.info("Results saved to %s", result_path)

    # Print final JSON to stdout for easy capture
    print("\n=== EVAL RESULTS ===")
    print(json.dumps(output, indent=2, ensure_ascii=False))
    print("=== END RESULTS ===")

    # Upload to LangFuse (best-effort, never blocks result output)
    if os.getenv("LANGFUSE_PUBLIC_KEY"):
        try:
            from evals.langfuse_upload import upload_results

            upload_results(output, args.version)
            logger.info("Results uploaded to LangFuse (version=%s)", args.version)
        except Exception as e:
            logger.error("LangFuse upload failed: %s", e)


if __name__ == "__main__":
    asyncio.run(main())
