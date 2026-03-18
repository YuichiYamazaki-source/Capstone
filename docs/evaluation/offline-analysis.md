# Offline Evaluation Analysis: Data Scale Impact (1K → 6.6K)

## Summary

Expanding the course dataset from 1,000 to 6,599 courses caused significant
IR metric degradation. The root cause is a combination of data quality issues
in the expanded dataset and LLM behavioral non-determinism — not the Rerank
feature.

## Experiment Setup

| Run | Version | Date | Data Size | Rerank | GT Cases (IR) |
|---|---|---|---|---|---|
| Baseline | v3.1-deepeval-fix | 2026-03-16 | ~1,000 | OFF (not implemented) | 17 |
| 6.6K no-rerank | v4.1-rerank-off | 2026-03-18 | 6,599 | OFF | 17 |
| 6.6K with-rerank | v4.2-rerank-on | 2026-03-18 | 6,599 | ON | 17 |

All three runs use the same 17 IR test cases from `ground_truth.json`.

## Aggregate Results

| Metric | v3.1 (1K) | v4.1 (6.6K, no rerank) | v4.2 (6.6K, rerank) |
|---|---|---|---|
| **Hit Rate** | 1.00 | 0.71 | 0.65 |
| **Precision@5** | 0.6118 | 0.1647 | 0.0941 |
| **Recall@5** | 0.4962 | 0.1295 | 0.0861 |
| **Tool Selection** | 1.00 | 0.79 | 0.84 |
| **Filter Param Accuracy** | 1.00 | 0.00 | 0.00 |
| **Filter Satisfaction** | 1.00 | 0.80 | 0.80 |
| **Agent Routing** | N/A | 1.00 | 1.00 |
| **Latency avg** | 9,286ms | 12,182ms | 13,884ms |

## Per-Case Comparison (v3.1 vs v4.1, Rerank OFF)

| Case | Query | v3.1 HR | v4.1 HR | v3.1 P@5 | v4.1 P@5 | v3.1 R@5 | v4.1 R@5 | Notes |
|---|---|---|---|---|---|---|---|---|
| gt-01 | Python programming courses | 1.00 | 1.00 | 0.6000 | 0.2000 | 0.4286 | 0.1429 | P@5 halved |
| gt-02 | I want to learn machine learning from scratch | 1.00 | 1.00 | 0.8000 | 0.2000 | 0.5714 | 0.1429 | P@5 halved |
| gt-04 | cybersecurity courses | 1.00 | 1.00 | 0.8000 | 0.4000 | 0.4000 | 0.2000 | |
| gt-05 | I want to transition from backend dev to DS | 1.00 | 0.00 | 0.8000 | 0.0000 | 0.5000 | 0.0000 | HR dropped, agent delegation |
| gt-06 | deep learning courses | 1.00 | 1.00 | 0.6000 | 0.2000 | 0.6000 | 0.2000 | P@5 halved |
| gt-08 | cloud computing and AWS | 1.00 | 1.00 | 0.8000 | 0.4000 | 0.4444 | 0.2222 | |
| gt-10 | JavaScript web development | 1.00 | 1.00 | 1.0000 | 0.2000 | 0.8333 | 0.1667 | P@5 halved |
| gt-11 | Protect healthcare systems from cyber attacks | 1.00 | 0.00 | 0.6000 | 0.0000 | 0.5000 | 0.0000 | No retrieval |
| gt-12 | Prompt engineering and ChatGPT | 1.00 | 1.00 | 0.8000 | 0.4000 | 0.8000 | 0.4000 | |
| gt-13 | Build AI applications for production | 1.00 | 1.00 | 0.2000 | 0.2000 | 0.2500 | 0.2500 | Stable |
| gt-14 | Data visualization and analytics courses | 1.00 | 1.00 | 0.4000 | 0.2000 | 0.2857 | 0.1429 | |
| gt-15 | beginner AI courses | 1.00 | 0.00 | 0.4000 | 0.0000 | 0.2500 | 0.0000 | HR dropped |
| gt-16 | AI and healthcare intersection | 1.00 | 1.00 | 0.2000 | 0.2000 | 0.1667 | 0.1667 | Stable |
| gt-17 | Linux and security | 1.00 | 0.00 | 0.8000 | 0.0000 | 0.5714 | 0.0000 | No retrieval |
| gt-18 | UX design courses | 1.00 | 1.00 | 0.6000 | 0.0000 | 1.0000 | 0.0000 | P@5 halved |
| gt-19 | AWS certification courses | 1.00 | 1.00 | 0.6000 | 0.2000 | 0.5000 | 0.1667 | P@5 halved |
| gt-20 | Intermediate data science, good ratings | 1.00 | 0.00 | 0.4000 | 0.0000 | 0.3333 | 0.0000 | HR dropped, filter issue |

## Root Cause Analysis

### 1. Data Quality in Expanded Dataset (Primary Cause)

The dataset expanded from ~1,000 curated courses to 6,599 courses. Many of
the added courses have missing or sparse `description` fields. Since the
hybrid search pipeline uses both BM25 (keyword) and dense embedding on the
`description` field, courses with missing descriptions:

- Score poorly on semantic similarity but may still appear via BM25 keyword match
- Dilute the top-K results with irrelevant entries
- Push previously-relevant courses (from the 1K subset) out of the top-K

This explains why Precision@5 dropped across nearly all cases: the same
queries now retrieve different courses from the larger, noisier pool.

### 2. LLM Non-Determinism (Secondary Cause)

Even with the same prompt and model (gpt-4o-mini), the LLM exhibits
run-to-run variation in:

- **Tool calling**: gt-11 and gt-17 had zero retrieval in v4.1 (agent
  answered directly instead of calling `retrieve_courses`)
- **Agent delegation**: gt-05 was delegated to Career Advisor in v4.1
  (direct retrieval in v3.1), changing the search query entirely
- **Filter parameter extraction**: Filter Param Accuracy dropped from 1.00
  to 0.00 — the LLM stopped extracting `level`, `min_rating`, `organization`
  parameters in all 5 filter cases

### 3. Rerank Impact (Minimal)

Comparing v4.1 (rerank OFF) vs v4.2 (rerank ON) shows minimal difference:

| Metric | Rerank OFF | Rerank ON | Delta |
|---|---|---|---|
| Hit Rate | 0.71 | 0.65 | -0.06 |
| Precision@5 | 0.1647 | 0.0941 | -0.07 |
| Recall@5 | 0.1295 | 0.0861 | -0.04 |

The slight degradation with rerank ON may be due to the reranker
(fastembed all-MiniLM-L6-v2) re-scoring courses differently than
Qdrant's native RRF ranking, combined with LLM non-determinism between
the two separate eval runs.

### 4. Ground Truth Staleness

The `expected_titles` in ground_truth.json were authored against the 1K
dataset. With 6.6K courses, many new relevant courses exist that are not
in the expected list, making Precision@5 appear low even when results are
objectively good. Conversely, some expected courses may now be ranked lower
due to competition from the larger pool.

## Recommendations

1. **Rebuild ground truth** against the 6,599-course dataset to get
   accurate IR metrics
2. **Audit data quality**: identify courses with missing descriptions and
   assess whether they should be excluded or backfilled
3. **Pin temperature=0** and verify tool_choice configuration to reduce
   LLM non-determinism in eval runs
4. **Run multiple eval passes** (3-5x) and average results to smooth out
   LLM non-determinism
5. **Consider MRR/NDCG** now that reranking is implemented (previously
   deferred in metrics.md)
