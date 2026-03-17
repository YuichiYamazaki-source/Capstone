# ADR: Hybrid Search for Course Retrieval

## Status

Accepted (2026-03-16)

## Context

v2.0 multi-agent evaluation (3 test cases, gpt-4o) revealed structural issues
with the LLM-driven tool selection approach:

### Evaluation Results (v2.0-multi-agent)

| Metric | Value | Issue |
|---|---|---|
| Retrieval Tool Selection Accuracy | 0.67 | LLM chose wrong search tool 1/3 times |
| Hit Rate | 0.67 | 1/3 cases returned zero relevant results |
| Precision@5 | 0.27 | Most retrieved courses were irrelevant |
| Recall@5 | 0.44 | Missing relevant courses |
| Avg Latency | 15.4s | 2x Runner.run() (Learning Advisor + Course Retrieval Agent) |

### Root Causes

1. **gt-02** ("I want to learn machine learning from scratch"):
   Course Retrieval Agent chose `filter_courses` instead of `search_courses_semantic`.
   The LLM interpreted "from scratch" as a level constraint instead of recognizing
   the conceptual/intent nature of the query. Semantic search would have found
   ML-related courses via embedding similarity.

2. **gt-03** ("beginner courses with rating above 4.8"):
   Course Retrieval Agent correctly chose `filter_courses`, but the filter returned
   topically irrelevant courses (Laravel, Hydrocarbon) because the query had no
   topic constraint. Combining filter with semantic search would have brought
   topic-relevant results to the top.

3. **Latency**: The Course Retrieval Agent required its own LLM call (Runner.run)
   just to decide which search tool to use. This added ~7s of latency with no
   retrieval quality benefit.

### Core Insight

The keyword vs semantic vs filter decision is not a judgment call that benefits
from LLM reasoning. It is a retrieval strategy question with a known-good answer:
**run all methods and merge results**.

## Decision

Replace the 3 separate search tools + LLM-based tool selection with a single
**hybrid search tool** that runs keyword + semantic search in parallel and merges
results using Reciprocal Rank Fusion (RRF).

### Before (v2.0)

```
Learning Advisor Agent (LLM call #1)
  → Course Retrieval Agent (LLM call #2)
    → LLM decides: keyword OR semantic OR filter
    → Executes one search method
```

### After (v2.1)

```
Learning Advisor Agent (LLM call #1)
  → retrieve_courses (rule-based, no LLM)
    → keyword search (MongoDB)     ┐
    → semantic search (Qdrant)     ├ parallel
    → filters applied to both      ┘
    → RRF merge → top-K results
```

## Consequences

### Positive

- **Eliminates tool selection error**: No LLM choosing between keyword/semantic/filter
- **Improves recall**: Union of keyword + semantic results covers more relevant courses
- **Improves precision for filtered queries**: Semantic reranking surfaces topically
  relevant results even within structural filters (the gt-03 problem)
- **Reduces latency**: One LLM call instead of two (Runner.run drops from 2 to 1)
- **Simplifies evaluation**: No "retrieval tool selection accuracy" metric needed;
  IR metrics directly measure retrieval quality

### Negative

- **Increased DB load per request**: Two searches instead of one (mitigated by
  parallel execution; total wall time ≈ max(keyword_time, semantic_time))
- **Embedding cost per request**: Every query now generates an embedding vector
  (was conditional on LLM choosing semantic search)
- **Less interpretable ranking**: RRF score is a composite — harder to explain
  why a specific course ranked where it did

### Trade-off Assessment

| Axis | Before (v2.0) | After (v2.1) |
|---|---|---|
| LLM calls | 2 | 1 |
| Search calls | 1 | 2 (parallel) |
| Embedding calls | 0-1 (LLM decides) | 1 (always) |
| Tool selection risk | High (LLM error) | None (deterministic) |
| Estimated latency | ~15s | ~7-9s |
| DB load | 1 query | 2 queries (parallel) |

The embedding cost (~$0.00002 per query with text-embedding-3-small) is negligible
compared to the LLM call it replaces (~$0.01+ per Runner.run with gpt-4o).

## Alternatives Considered

### 1. Better prompting for Course Retrieval Agent

Improve the system prompt to make tool selection more reliable.

Rejected: Tool selection is inherently non-deterministic with LLMs. Even with
perfect prompting, edge cases (gt-02 style) will always exist. The problem is
structural, not prompt-level.

### 2. Weighted score normalization instead of RRF

Normalize keyword and semantic scores to 0-1, then weighted average.

Rejected: Score distributions differ between keyword (BM25) and semantic (cosine).
Normalization requires per-query min/max which is unstable. RRF uses rank position
only, avoiding the scale mismatch entirely.

### 3. Cross-encoder reranking

Use a cross-encoder model to rerank merged results.

Deferred: Good for future accuracy improvement, but adds latency and cost.
RRF provides a strong baseline without additional model calls. Cross-encoder
can be layered on top of RRF results later.
