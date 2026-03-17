"""Upload evaluation results to LangFuse v4 Dataset API.

Creates versioned dataset runs for side-by-side comparison.
Each ground truth case becomes a dataset item; each eval run
creates per-case scores via create_score() with Score Config binding.

LangFuse v4 API:
  - create_score(trace_id, name, value, data_type, config_id)
  - api.score_configs.create(name, data_type, min_value, max_value)
  - start_as_current_observation() for trace creation
"""

import json
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv("local/.env")

logger = logging.getLogger("eval.langfuse_upload")

DATASET_NAME = "course-search-eval"

# All evaluation metrics: name -> description.
# Used to create Score Configs (0-1 range) in LangFuse.
SCORE_CONFIGS = {
    # Per-case IR metrics
    "hit_rate": "Whether at least one relevant result was retrieved (0 or 1)",
    "precision_at_5": "Fraction of top-5 results that are relevant",
    "recall_at_5": "Fraction of relevant results found in top-5",
    "advisor_tool_correct": "Whether advisor selected correct tool (0 or 1)",
    # Per-case LLM-as-Judge metrics (DeepEval)
    "answer_relevancy": "DeepEval LLM-as-Judge: relevancy of answer to query",
    "faithfulness": "DeepEval LLM-as-Judge: faithfulness to retrieval context",
    "contextual_relevancy": "DeepEval LLM-as-Judge: relevancy of retrieved context",
    # Aggregate metrics
    "avg_hit_rate": "Average hit rate across all test cases",
    "avg_precision_at_5": "Average precision@5 across all test cases",
    "avg_recall_at_5": "Average recall@5 across all test cases",
    "advisor_accuracy": "Fraction of cases with correct tool selection",
    "avg_answer_relevancy": "Average answer relevancy (LLM-as-Judge)",
    "avg_faithfulness": "Average faithfulness (LLM-as-Judge)",
    "avg_contextual_relevancy": "Average contextual relevancy (LLM-as-Judge)",
    # Agent routing
    "agent_routing_correct": "Whether orchestrator routed to expected agent (0 or 1)",
    "agent_routing_accuracy": "Fraction of cases routed to correct specialist agent",
}


def _get_client():
    """Get LangFuse v4 client."""
    from langfuse import Langfuse

    return Langfuse(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        host=os.getenv("LANGFUSE_BASE_URL", "https://us.cloud.langfuse.com"),
    )


def _ensure_dataset(client) -> None:
    """Create dataset if it doesn't exist (idempotent)."""
    try:
        client.get_dataset(name=DATASET_NAME)
        logger.info("Dataset '%s' already exists", DATASET_NAME)
    except Exception:
        client.create_dataset(name=DATASET_NAME)
        logger.info("Created dataset '%s'", DATASET_NAME)


def _ensure_score_configs(client) -> dict[str, str]:
    """Create Score Configs (0-1 NUMERIC) if they don't exist.

    Returns name -> config_id mapping for use in create_score().
    Idempotent: catches conflict on duplicate names, then fetches existing.
    """
    config_map: dict[str, str] = {}

    for name, description in SCORE_CONFIGS.items():
        try:
            config = client.api.score_configs.create(
                name=name,
                data_type="NUMERIC",
                min_value=0.0,
                max_value=1.0,
                description=description,
            )
            config_map[name] = config.id
        except Exception:
            pass  # Already exists — will fetch below

    # Fill in any configs that already existed
    if len(config_map) < len(SCORE_CONFIGS):
        try:
            all_configs = client.api.score_configs.get()
            for cfg in all_configs.data:
                if cfg.name in SCORE_CONFIGS and cfg.name not in config_map:
                    config_map[cfg.name] = cfg.id
        except Exception as e:
            logger.warning("Could not fetch score configs: %s", e)

    logger.info("Score configs ready: %d/%d", len(config_map), len(SCORE_CONFIGS))
    return config_map


def _score(client, trace_id: str, name: str, value: float, config_map: dict) -> None:
    """Create a single score with config binding."""
    client.create_score(
        trace_id=trace_id,
        name=name,
        value=value,
        data_type="NUMERIC",
        config_id=config_map.get(name),
    )


def _upsert_ground_truth(client, ground_truth_path: str) -> dict:
    """Upsert ground truth items into the dataset.

    Returns:
        Mapping of case_id (e.g. "gt-01") to LangFuse dataset_item_id.
    """
    with open(ground_truth_path) as f:
        cases = json.load(f)

    id_map = {}
    for case in cases:
        item = client.create_dataset_item(
            dataset_name=DATASET_NAME,
            input={"query": case["query"]},
            expected_output={
                "titles": case["expected_titles"],
                "tool": case.get("expected_tool", ""),
                "description": case.get("description", ""),
            },
            metadata={"ground_truth_id": case["id"]},
        )
        id_map[case["id"]] = item.id

    logger.info("Upserted %d ground truth items", len(cases))
    return id_map


def upload_results(results: dict, version: str) -> None:
    """Upload evaluation results to LangFuse v4.

    Creates Score Configs (idempotent), then attaches per-case and
    aggregate scores with config_id binding for consistent graph display.
    """
    client = _get_client()

    if not client.auth_check():
        logger.error("LangFuse auth failed, skipping upload")
        return

    _ensure_dataset(client)
    config_map = _ensure_score_configs(client)

    ground_truth_path = Path(__file__).parent / "ground_truth.json"
    _upsert_ground_truth(client, str(ground_truth_path))

    ir_details = results.get("ir_metrics", {}).get("details", [])
    tool_details = results.get("tool_selection", {}).get("details", [])
    llm_per_case = {
        item["id"]: item["scores"]
        for item in results.get("llm_judge", {}).get("per_case", [])
    }
    tool_map = {item["id"]: item for item in tool_details}

    for ir_case in ir_details:
        case_id = ir_case["id"]

        with client.start_as_current_observation(
            name=f"eval_{case_id}",
            as_type="span",
            input={"query": ir_case["query"]},
            output={
                "retrieved_titles": ir_case.get("retrieved_titles", []),
                "retrieved_count": ir_case.get("retrieved_count", 0),
            },
            metadata={"version": version, "case_id": case_id},
        ):
            trace_id = client.get_current_trace_id()

            # IR scores
            _score(client, trace_id, "hit_rate", ir_case["hit_rate"], config_map)
            _score(
                client,
                trace_id,
                "precision_at_5",
                ir_case["precision_at_5"],
                config_map,
            )
            _score(client, trace_id, "recall_at_5", ir_case["recall_at_5"], config_map)

            # Tool selection
            tool_case = tool_map.get(case_id)
            if tool_case:
                _score(
                    client,
                    trace_id,
                    "advisor_tool_correct",
                    1.0 if tool_case.get("advisor_match", False) else 0.0,
                    config_map,
                )

            # DeepEval LLM-as-Judge scores
            for metric_name, score in llm_per_case.get(case_id, {}).items():
                _score(client, trace_id, metric_name, score, config_map)

    # Aggregate summary observation
    with client.start_as_current_observation(
        name=f"eval_summary_{version}",
        as_type="span",
        metadata={"version": version, "type": "summary"},
        output={
            "ir_metrics": {
                k: v for k, v in results.get("ir_metrics", {}).items() if k != "details"
            },
            "tool_selection": {
                "advisor_accuracy": results.get("tool_selection", {}).get(
                    "advisor_accuracy", 0
                ),
            },
            "latency": results.get("latency", {}),
            "llm_judge": results.get("llm_judge", {}).get("aggregate", {}),
        },
    ):
        summary_id = client.get_current_trace_id()

        ir = results.get("ir_metrics", {})
        _score(
            client, summary_id, "avg_hit_rate", ir.get("avg_hit_rate", 0), config_map
        )
        _score(
            client,
            summary_id,
            "avg_precision_at_5",
            ir.get("avg_precision_at_5", 0),
            config_map,
        )
        _score(
            client,
            summary_id,
            "avg_recall_at_5",
            ir.get("avg_recall_at_5", 0),
            config_map,
        )
        _score(
            client,
            summary_id,
            "advisor_accuracy",
            results.get("tool_selection", {}).get("advisor_accuracy", 0),
            config_map,
        )

        for metric_name, score in (
            results.get("llm_judge", {}).get("aggregate", {}).items()
        ):
            _score(client, summary_id, f"avg_{metric_name}", score, config_map)

        routing = results.get("agent_routing", {})
        if routing.get("routing_accuracy") is not None:
            _score(
                client,
                summary_id,
                "agent_routing_accuracy",
                routing["routing_accuracy"],
                config_map,
            )

    client.flush()
    logger.info(
        "Uploaded %d case scores + summary to LangFuse v4 (version=%s)",
        len(ir_details),
        version,
    )
