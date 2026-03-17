# Evaluation Metrics

## Overview

Metrics are organized by the 6 Key Capabilities defined in
[Requirements.md](../../requirements/Requirements.md). Each capability lists
adopted metrics with their test locations, and not-adopted metrics with rationale.

Cross-cutting concerns (Guardrails, System Performance) are in separate sections.

## 1. Semantic Course Retrieval

Measures whether the hybrid search pipeline (BM25 + dense + RRF) returns
relevant courses for a user query.

### Adopted

| Metric | Method | Test | Detects |
|--------|--------|------|---------|
| Hit Rate | Ground Truth | `test_e2e_handoff.py` | Search completely missing relevant results (binary) |
| Recall@K | Ground Truth | `evals/metrics.py` | How many relevant courses are retrieved out of all relevant ones (coverage) |
| Precision@K | Ground Truth | `evals/metrics.py` | How many retrieved courses are actually relevant (noise) |
| Filter Satisfaction | Deterministic | `evals/metrics.py` | Whether all returned courses match filter constraints (level, org, rating) |
| Faithfulness | LLM-as-Judge (DeepEval) | `test_quality_metrics.py` | Whether the response is grounded in retrieved context — detects hallucinated courses |

### Not adopted

| Metric | Rationale | Reconsider when |
|--------|-----------|-----------------|
| MRR | Ranking position matters less in list UI. Hit Rate + Precision@K cover discovery. | Re-Ranking layer introduction |
| NDCG | Requires graded relevance labels (0/1/2/3). Binary relevant/not-relevant is sufficient for course recommendation. | Re-Ranking layer introduction |
| MAP | Rank-weighted precision average. Same rationale as MRR — ranking order has low UX impact in list display. | Re-Ranking layer introduction |
| F1@K | Harmonic mean of Precision@K and Recall@K. Viewing both individually is more diagnostic. | Production release (composite health metric) |
| BERTScore | Requires reference text. Search results are structured data, not text-to-text comparison. | N/A |
| Contextual Relevancy | Replaced by Faithfulness in Multi-Agent architecture. Faithfulness directly measures whether the response is grounded in retrieved context, while Contextual Relevancy measured whether retrieved docs are relevant to the query — a concern now handled by IR metrics (Hit Rate, Precision@K). | N/A |

## 2. Relevance Assistance

Measures overall response quality — whether the system's answer is relevant,
grounded, and useful regardless of which agent handles it.

### Adopted

| Metric | Method | Test | Detects |
|--------|--------|------|---------|
| Answer Relevancy | LLM-as-Judge (DeepEval) | `test_quality_metrics.py` — 15 cases (5 per specialist) | Response does not address the user's question |
| Faithfulness | LLM-as-Judge (DeepEval) | `test_quality_metrics.py` — 15 cases (5 per specialist) | Hallucinated content not grounded in retrieved context |
| Routing Accuracy | Deterministic | `test_routing.py` — 4 cases | Wrong specialist handles the query (prerequisite for relevance) |
| Direct Handling | Deterministic | `test_direct_handling.py` — 5 cases | Greetings/off-topic incorrectly delegated to specialists |
| Guardrail Pass-Through | Deterministic | `test_guardrails.py` — 5 on-topic cases | Legitimate queries incorrectly blocked by guardrails |

### Not adopted

| Metric | Rationale | Reconsider when |
|--------|-----------|-----------------|
| BLEU / ROUGE | Requires reference answers. Course recommendations are free-form with no single "correct" answer. | N/A |
| BERTScore | Same as above — no reference text available for comparison. | N/A |
| Completeness | Answer Relevancy + agent-specific JSON structure validation cover this. Independent LLM-as-Judge metric would double evaluation cost with marginal diagnostic value. | Production release (composite health metric) |
| Coherence | Agent output is structured JSON, not free-form prose. JSON Format Compliance tests validate structure; Coherence would assess natural language quality that has low UX impact in structured output. | Free-form response mode |
| Helpfulness | Composite of Answer Relevancy + Completeness + Coherence. Individual metrics are more diagnostic for root-cause analysis. | Production release (composite health metric) |
| Toxicity / Bias | Course recommendation output is formulaic and structured. Low structural risk. Rule-based guardrails (`test_guardrails.py`) handle content safety. | User-generated content integration |
| Conciseness | Would conflict with Completeness (detail vs brevity trade-off). Structured JSON output has inherently controlled length. | N/A |

## 3. Prerequisite Awareness

Measures whether the system considers course prerequisites, difficulty
progression, and learner readiness when recommending courses.

### Adopted

| Metric | Method | Test | Detects |
|--------|--------|------|---------|
| Path Coherence | Deterministic | `test_learning_path.py:test_learning_path_level_coherence` | Levels go backwards (e.g., Advanced → Beginner) |
| Level Coverage | Deterministic | `test_learning_path.py:test_learning_path_level_coverage` | Path does not span from starting_level to target_level |
| Course Detail Utilization | Deterministic | `test_learning_path.py:test_learning_path_course_detail_utilization` | `get_course_details` (prerequisite-checking tool) not called |
| Path Length | Deterministic | `test_learning_path.py:test_learning_path_json_format` — `3 <= len(path) <= 6` | Too few courses (gaps) or too many (overwhelming) |

### Not adopted

| Metric | Rationale | Reconsider when |
|--------|-----------|-----------------|
| Prerequisite Graph Validation | Dataset lacks course-to-course prerequisite relationship data. `get_course_details` call verification is an indirect proxy. | Prerequisite data available in dataset |
| Skill Overlap Detection | Requires reliable skill data per course. Embedding analysis confirmed skill clustering is weak (805/1000 courses = "Other" in skill field). | Skill metadata quality improvement |
| Profile Utilization | Requires seeded test user in MongoDB with known skills. Current tests run as anonymous user. | Phase 5 (profile-dependent tests) |

## 4. Skill Gap Identification

Measures whether the Skill Gap Analyst correctly identifies missing skills,
uses market data (web search), and recommends relevant courses for each gap.

### Adopted

| Metric | Method | Test | Detects |
|--------|--------|------|---------|
| JSON Format Compliance | Deterministic | `test_skill_gap.py:test_skill_gap_json_format` | Missing required keys (`target_role`, `current_skills`, `gaps[]`, `summary`) or invalid `match_type` |
| Tool Call Presence | Deterministic | `test_skill_gap.py:test_skill_gap_tool_calls` | `web_search` or `retrieve_courses` not called |
| Web Search Utilization | Deterministic | `test_web_search.py:test_skill_gap_uses_web_search` | Skill requirements not grounded in market data |
| Web Search Data Reflection | Deterministic | `test_web_search.py:test_skill_gap_web_search_reflected_in_output` | `web_search` called but results not reflected in gaps |
| Answer Relevancy | LLM-as-Judge (DeepEval) | `test_quality_metrics.py` — 5 Skill Gap cases | Response does not address skill gap question |
| Faithfulness | LLM-as-Judge (DeepEval) | `test_quality_metrics.py` — 5 Skill Gap cases | Hallucinated skills or courses |
| match_type Validity | Deterministic | `test_skill_gap.py:test_skill_gap_json_format` | Dishonest course matching (claiming exact match when only alternative exists) |

### Not adopted

| Metric | Rationale | Reconsider when |
|--------|-----------|-----------------|
| Skill Coverage | Ground truth lacks `expected_skills` field. "Correct" skills for a role are subjective and change with market conditions. Web search results vary per run, making fixed GT comparison unreliable. | Stable skill taxonomy + `expected_skills` in GT |
| Priority Ordering Accuracy | Skill priority depends on user's current skills. Anonymous test user has no profile, so "correct" priority is undefined. | Profile Utilization tests (Phase 5) |
| Profile Utilization | Requires seeded test user in MongoDB. Current tests run as anonymous user. | Phase 5 (profile-dependent tests) |
| Tool Argument Quality | Ground truth for free-form `retrieve_courses` query arguments is expensive to create. Indirectly measured by IR metrics — bad arguments produce bad search results. | Structured tool argument schema |

## 5. Learning Path Recommendations

Measures whether the Learning Path Designer creates a coherent, progressive
curriculum with appropriate course selection and ordering.

### Adopted

| Metric | Method | Test | Detects |
|--------|--------|------|---------|
| JSON Format Compliance | Deterministic | `test_learning_path.py:test_learning_path_json_format` | Missing required keys (`goal`, `personalized`, `path[]`, `summary`) |
| Path Coherence | Deterministic | `test_learning_path.py:test_learning_path_level_coherence` | Non-monotonic difficulty progression |
| Level Coverage | Deterministic | `test_learning_path.py:test_learning_path_level_coverage` | Path does not span requested level range |
| Tool Call Presence | Deterministic | `test_learning_path.py:test_learning_path_tool_calls` | `retrieve_courses` not called |
| Course Detail Utilization | Deterministic | `test_learning_path.py:test_learning_path_course_detail_utilization` | `get_course_details` not called (prerequisite check skipped) |
| Answer Relevancy | LLM-as-Judge (DeepEval) | `test_quality_metrics.py` — 5 Learning Path cases | Response does not address learning path request |
| Faithfulness | LLM-as-Judge (DeepEval) | `test_quality_metrics.py` — 5 Learning Path cases | Courses in path not from retrieval results |

### Not adopted

| Metric | Rationale | Reconsider when |
|--------|-----------|-----------------|
| Actionability | Career Advisor uses this (concrete steps + timeline). Learning Path's structured JSON (`step`/`title`/`level`) inherently provides actionability. Additional GEval cost is not justified. | Free-form path descriptions |
| Completeness | JSON structure validation (3-6 courses, level span) already checks coverage. LLM-as-Judge would add cost with marginal diagnostic value. | Production release |
| Course Diversity (Provider) | Embedding analysis confirmed courses cluster by topic, not provider. Topic relevance should take priority over provider diversity. | Provider-aware recommendation feature |
| Skill Overlap Detection | Same as Prerequisite Awareness — skill metadata is unreliable (805/1000 = "Other"). | Skill metadata quality improvement |

## 6. Career-Oriented Course Exploration

Measures whether the Career Advisor provides market-grounded career guidance
with actionable plans, using web search as the primary data source.

### Adopted

| Metric | Method | Test | Detects |
|--------|--------|------|---------|
| JSON Format Compliance | Deterministic | `test_career.py:test_career_json_format` | Missing required keys (`career_paths[]`, `recommendation`, `data_source`) |
| Web Search Utilization | Deterministic | `test_web_search.py:test_career_uses_web_search` | Career advice not grounded in current market data |
| Web Search → data_source | Deterministic | `test_web_search.py:test_career_web_search_reflected_in_output` | `web_search` called but `data_source` not set to `"web_search"` |
| Action Plan Structure | Deterministic | `test_career.py:test_career_action_plan_structure` | `action_plan` missing `month`/`action`/`milestone` fields |
| Actionability | LLM-as-Judge (GEval) | `test_quality_metrics.py:test_actionability_career` — 5 cases | Vague advice without concrete steps, timeline, or milestones |
| Answer Relevancy | LLM-as-Judge (DeepEval) | `test_quality_metrics.py` — 5 Career cases | Response does not address career question |
| Faithfulness | LLM-as-Judge (DeepEval) | `test_quality_metrics.py` — 5 Career cases | Career data not grounded in web search results |

### Not adopted

| Metric | Rationale | Reconsider when |
|--------|-----------|-----------------|
| Salary Accuracy | Web search results vary per run. Fixed ground truth for salary data becomes stale quickly. Faithfulness metric verifies data is grounded in web search output. | Stable salary data API integration |
| Multi-Path Comparison Quality | Requires subjective judgment on "good comparison". JSON structure (`career_paths[]` with multiple entries) ensures multiple paths are presented. Quality is covered by Answer Relevancy. | User satisfaction surveys |
| Profile Utilization | Requires seeded test user. Career advice personalization is tested indirectly through `get_user_profile` tool call presence. | Phase 5 (profile-dependent tests) |

## Cross-Cutting: Web Search

Web search (`web_search` tool via OpenAI) is a critical data source for
Skill Gap Analyst and Career Advisor. Dedicated tests in `test_web_search.py`
validate:

1. **Tool invocation** — `web_search` appears in `all_tool_calls`
2. **Data reflection** — Web search data is reflected in agent output (gaps/data_source)
3. **Negative case** — Agents that should NOT use web search (Learning Path Designer) do not call it

See also: `test_skill_gap.py:test_skill_gap_tool_calls`,
`test_career.py:test_career_uses_web_search` (agent-specific tests that also
check web search as part of broader tool call validation).

## Cross-Cutting: Guardrails

Input/output guardrails protect the system boundary. Tested in `test_guardrails.py`:

| Test Group | Cases | Detects |
|------------|-------|---------|
| Off-topic rejection | 5 | Unrelated queries (geography, cooking, jokes) not redirected |
| Prompt injection blocking | 5 | Injection attempts (role override, DAN mode) not blocked |
| On-topic pass-through | 5 | Legitimate learning queries incorrectly blocked |
| Output sanitization | 3 | PII (email, phone) or stack traces leaked in output |

## Cross-Cutting: System Performance

Measured via LangFuse traces (online) and `response.latency_ms` (offline).

| Metric | Measures | Purpose |
|--------|----------|---------|
| E2E Latency (p50/p95/p99) | Request to response complete | User-perceived performance |
| LLM Latency | Agent LLM call time | Largest bottleneck. Model comparison |
| Tool Execution Latency | Per-tool execution time | DB performance degradation |
| Embedding Latency | OpenAI Embedding API call time | Semantic search fixed cost |
| Token Usage (input/output/total) | Tokens consumed per request | Cost calculation, prompt optimization |

### Not adopted

| Metric | Rationale | Reconsider when |
|--------|-----------|-----------------|
| Throughput (RPS) | Single-user PoC. Load testing (locust) is separate. | Load testing phase |
| TTFB | Requires streaming response. Current architecture returns complete response. | Streaming implementation |
| Cold Start Latency | One-time container startup cost. Health checks cover this. | N/A |

## Ground Truth Dataset

- **Source**: Coursera Course Dataset 2024 (6,645 courses)
- **Sample**: 1,000 courses via stratified sampling (Level x Domain)
- **Sampling method**: Proportional allocation preserving original Level and Domain distribution
- **Deduplication**: Title-based dedup at sampling and ingestion stages
- **GT cases**: 38 total (20 search + 18 multi-agent routing)

## Model Comparison Strategy

When comparing models (e.g., gpt-4o vs gpt-4o-mini), the key trade-off axes are:

| Axis | Metrics |
|------|---------|
| Accuracy | Faithfulness, Answer Relevancy, Actionability |
| Search Quality | Precision@K, Recall@K, Hit Rate |
| Structure | JSON Format Compliance, Path Coherence |
| Speed | E2E Latency, LLM Latency |
| Cost | Token Usage x model pricing |
