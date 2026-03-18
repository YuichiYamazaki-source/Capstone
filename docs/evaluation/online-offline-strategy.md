# Evaluation Strategy: Online vs Offline

## Overview

Evaluation is split into two complementary approaches based on whether
ground truth (GT) is available and when evaluation runs.

| | Online (per-request) | Offline (batch, GT-based) |
|---|---|---|
| **Trigger** | Every chat request | Manual / CI pipeline |
| **Ground Truth** | Not available | 38 GT cases |
| **LLM-as-Judge** | LangFuse Evaluator | DeepEval (pytest) |
| **Deterministic** | Score from code | Score from code |
| **Result storage** | LangFuse (automatic) | JSON files + LangFuse upload |
| **CI/CD** | — | pytest + thresholds.yaml |

## Online Evaluation

### LangFuse Evaluators (LLM-as-a-Judge)

Configured in the LangFuse dashboard. Runs automatically on traces.
No application code changes needed to adjust evaluation criteria.

| Evaluator | Target span | Evaluates |
|---|---|---|
| `skill_gap_answer_relevancy` | Skill Gap Analyst | Response relevance to skill gap query |
| `skill_gap_faithfulness` | Skill Gap Analyst | Response grounded in retrieved context |
| `career_answer_relevancy` | Career Advisor | Response relevance to career query |
| `career_faithfulness` | Career Advisor | Response grounded in retrieved context |
| `career_actionability` | Career Advisor | Concrete steps, timelines, resources |
| `learning_path_answer_relevancy` | Learning Path Designer | Response relevance to learning path query |
| `learning_path_faithfulness` | Learning Path Designer | Response grounded in retrieved context |
| `retrieval_contextual_relevancy` | retrieve_courses | Retrieved courses relevant to query |
| `web_search_relevancy` | web_search | Search results relevant to query |

### Score from Code (deterministic)

Sent from `app/scoring.py` after each request. No LLM cost.

| Score | Source | Logic |
|---|---|---|
| `tool_selection_correct` | chat.py | `retrieve_courses` in tool_calls → 1.0, else 0.0 |

### Metadata (not scores)

Already recorded in `app/monitoring.py` as LangFuse span metadata:

- `latency_ms`, `courses_count`, `agent`, `tool_calls`, `user_id`

## Offline Evaluation

### Score from Code (deterministic, GT-based)

Computed in `evals/eval_search.py` and uploaded via `evals/langfuse_upload.py`.

| Score | GT field used | Logic |
|---|---|---|
| `retrieval_hit_rate` | `expected_titles` | At least one relevant course in results |
| `retrieval_precision_at_5` | `expected_titles` | Fraction of top-5 that are relevant |
| `retrieval_recall_at_5` | `expected_titles` | Fraction of relevant found in top-5 |
| `tool_selection_correct` | `expected_tool` | retrieve_courses called for search queries |
| `agent_routing_correct` | `expected_agent` | Orchestrator routed to correct specialist |
| `filter_satisfaction` | `filter_check` | All returned courses match filter constraints |
| `filter_param_accuracy` | `filter_params` | LLM-extracted params match expected params |

### DeepEval (LLM-as-Judge, pytest)

Run via `pytest tests/eval/test_quality_metrics.py`. Uses gpt-4o-mini.

| Metric | Agent | Cases | Threshold |
|---|---|---|---|
| Answer Relevancy | Skill Gap Analyst | 5 | 0.5 |
| Answer Relevancy | Career Advisor | 5 | 0.5 |
| Answer Relevancy | Learning Path Designer | 5 | 0.5 |
| Faithfulness | Skill Gap Analyst | 5 | 0.5 |
| Faithfulness | Career Advisor | 5 | 0.5 |
| Faithfulness | Learning Path Designer | 5 | 0.5 |
| Actionability | Career Advisor | 5 | 0.5 |

Results are uploaded to LangFuse via `langfuse_upload.py` for Score graph visualization.

## Why Both?

- **Online** catches production regressions in real-time (no GT needed).
- **Offline** provides precise, reproducible metrics with GT comparison.
- **LLM-as-Judge (LangFuse)** is flexible and code-change-free.
- **Deterministic scores** are exact and free (no LLM cost).
- **DeepEval** integrates with pytest for CI/CD threshold enforcement.
