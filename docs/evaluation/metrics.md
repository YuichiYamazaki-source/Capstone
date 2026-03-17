# Evaluation Metrics

## Overview

Metrics are organized into 4 categories. Each metric includes measurement method,
what it detects, and when to use it for model/pipeline comparison.

## 1. RAG Retrieval

Measures whether the search pipeline returns relevant courses.

| Metric | Method | Detects |
|--------|--------|---------|
| Hit Rate | Ground Truth | Search completely missing relevant results (binary) |
| Recall@K | Ground Truth | How many relevant courses are retrieved out of all relevant ones (coverage) |
| Precision@K | Ground Truth | How many retrieved courses are actually relevant (noise) |
| Contextual Relevancy | LLM-as-Judge | Whether retrieved documents are relevant to the query (qualitative) |
| Faithfulness (Retrieval) | Ground Truth + DB lookup | Whether search result metadata matches source data (embedding/payload drift) |

### Not adopted (with rationale)

| Metric | Rationale | Future adoption |
|--------|-----------|-----------------|
| MRR | Ranking position matters less in list UI. Hit Rate + Precision@K cover this. | Re-Ranking layer introduction |
| NDCG | Requires graded relevance labels (0/1/2/3). Binary relevant/not-relevant is sufficient for course recommendation. | Re-Ranking layer introduction |
| MAP | Rank-weighted precision average. Same rationale as MRR — ranking order has low UX impact in list display. | Re-Ranking layer introduction |
| F1@K | Harmonic mean of Precision@K and Recall@K. Viewing both individually is more diagnostic. | Production release (composite health metric) |
| BERTScore | Requires reference text. Search results are structured data, not text-to-text comparison. | N/A |

## 2. Agent Response

Measures the quality of the LLM's final answer. Critical for model comparison (e.g., gpt-4o vs gpt-4o-mini).

| Metric | Method | Detects |
|--------|--------|---------|
| Answer Relevancy | LLM-as-Judge | Whether the response answers the user's question |
| Faithfulness | LLM-as-Judge | Whether the response is grounded in retrieved context (hallucination detection) |
| Completeness | LLM-as-Judge | Whether the response covers all aspects of the query |
| Coherence | LLM-as-Judge | Whether the response is logically structured and readable |

### Not adopted (with rationale)

| Metric | Rationale | Future adoption |
|--------|-----------|-----------------|
| BLEU / ROUGE | Requires reference answers. Course recommendations are free-form with no single "correct" answer. | N/A |
| BERTScore | Same as above — no reference text available. | N/A |
| Toxicity / Bias | Course recommendation output is formulaic. Low structural risk. Guardrails (rule-based) handle this. | N/A |
| Conciseness | Subsumed by Coherence. Independent metric would conflict with Completeness (detail vs brevity trade-off). | N/A |
| Helpfulness | Composite of Answer Relevancy + Completeness + Coherence. Individual metrics are more diagnostic. | Production release (composite health metric) |

## 3. Tool Selection

Measures whether the Agent chooses the right tools for the query.

| Metric | Method | Detects |
|--------|--------|---------|
| Tool Selection Accuracy | Ground Truth (query-tool pairs) | Whether the correct tool was selected for a given query type |
| Tool Call Count | Log analysis | Excessive or missing tool calls per request |
| Unnecessary Tool Call Rate | Ground Truth + Log analysis | Tools called when not needed (cost/latency waste) |

### Not adopted (with rationale)

| Metric | Rationale | Future adoption |
|--------|-----------|-----------------|
| Tool Argument Quality | Ground truth for free-form arguments is expensive to create. Indirectly measured by Retrieval metrics (bad args = bad results). | Multi-Agent architecture (V1.1+) |
| Tool Ordering Accuracy | Single Agent has high freedom in call ordering. "Correct order" is hard to define. | Multi-Agent architecture (V1.1+) |

## 4. System Performance

Measures latency, cost, and resource consumption.

| Metric | Measures | Purpose |
|--------|----------|---------|
| E2E Latency (p50/p95/p99) | Request to response complete | User-perceived performance. Checklist requirement. |
| LLM Latency | Agent LLM call time (total) | Largest bottleneck. Model comparison. |
| Tool Execution Latency | Per-tool execution time | DB performance degradation detection |
| Embedding Latency | OpenAI Embedding API call time | Semantic search fixed cost |
| TTFB (Time to First Byte) | Time until first response byte | Gateway proxy overhead. Streaming readiness. |
| Token Usage (input/output/total) | Tokens consumed per request | Cost calculation, model comparison, prompt optimization. Recorded in traces/logs. |

### Not adopted (with rationale)

| Metric | Rationale | Future adoption |
|--------|-----------|-----------------|
| Throughput (RPS) | Single-user PoC. Load testing (locust) is a separate concern. | Load testing phase |
| Cold Start Latency | One-time container startup cost. Health checks cover this. | N/A |

## Ground Truth Dataset

- **Source**: Coursera Course Dataset 2024 (6,645 courses)
- **Sample**: 1,000 courses via stratified sampling (Level x Domain)
- **Sampling method**: Proportional allocation preserving original Level and Domain distribution
- **Deduplication**: Title-based dedup at sampling and ingestion stages

## Model Comparison Strategy

When comparing models (e.g., gpt-4o vs gpt-4o-mini), the key trade-off axes are:

| Axis | Metrics |
|------|---------|
| Accuracy | Faithfulness, Answer Relevancy, Completeness |
| Readability | Coherence |
| Search Quality | Precision@K, Recall@K |
| Speed | E2E Latency, LLM Latency |
| Cost | Token Usage x model pricing |

## Single-Agent Evaluation Limits

Evaluating a single agent that handles all tools (search, filter, semantic)
reveals structural challenges that motivate multi-agent architecture:

### Problem: Output size explosion

A single agent receives the full retrieval context and generates a long natural
language response covering all retrieved courses. This causes:

1. **DeepEval timeout**: LLM-as-Judge metrics (Answer Relevancy, Faithfulness,
   Contextual Relevancy) send the full `actual_output` + `retrieval_context` to
   the judge LLM. With 10 courses x detailed fields, token counts explode and
   evaluation calls time out (observed: 180s+ per case).
2. **Mitigation required**: Truncating `actual_output` to 2000 chars and limiting
   `retrieval_context` to top 5 courses. This loses evaluation granularity.
3. **Cost scaling**: 2 cases x 3 metrics = ~$0.005 with gpt-4o-mini, but each
   case triggers 10+ judge LLM calls internally due to long context.

### Problem: RAG and LLM metrics are inseparable

With a single agent, DeepEval's LLM-as-Judge metrics conflate retrieval quality
and generation quality:

| Metric | What it actually measures in Single-Agent |
|--------|------------------------------------------|
| Contextual Relevancy | RAG retrieval quality (are retrieved docs relevant?) |
| Faithfulness | LLM generation quality (is response grounded in context?) |
| Answer Relevancy | Mix of both (response relevance depends on what was retrieved AND how it was summarized) |

When a score drops, there is no way to determine whether the cause is:
- Poor retrieval (RAG problem — wrong courses returned)
- Poor generation (LLM problem — hallucination, irrelevant summary)
- Both

In a multi-agent architecture, each agent has a focused scope, so metrics
directly attribute to the responsible component.

### Why multi-agent helps

| Aspect | Single Agent | Multi-Agent |
|--------|-------------|-------------|
| Output per agent | All courses in one response | Focused response per tool |
| Evaluation scope | Entire pipeline at once | Per-agent, per-tool evaluation |
| Context to judge LLM | Large (all tools, all results) | Small (one tool, focused results) |
| Metric attribution | Ambiguous (which tool caused failure?) | Clear (agent X failed on metric Y) |
| Timeout risk | High (long context = slow judge) | Low (small context per evaluation) |

This is documented as a key architectural driver for the multi-agent transition.
