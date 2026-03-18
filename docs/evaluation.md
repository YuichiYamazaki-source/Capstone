# Evaluation Framework

---

## Overview

- **Architecture**: Star topology — Learning Advisor (orchestrator) routes to 3 specialists via `handoff()`
- **Framework**: Pytest + DeepEval (Pytest plugin) + custom IR metrics (`evals/metrics.py`)
- **Principle**: Deterministic tests first, LLM-as-Judge only where necessary
- **Model for judge**: gpt-4o-mini (cost control, per project convention)
- **Entry point**: `POST /api/v1/chat` returns `ChatResponse` with `agent`, `tool_calls`, `retrieval_tool_calls`, `retrieval_args`, `courses`, `reply`

Metrics are organized by the 6 Key Capabilities defined in
[Requirements.md](../../requirements/Requirements.md). Each capability lists
adopted metrics with their test locations, and not-adopted metrics with rationale.

### Requirements ↔ Agent Mapping

| Requirements Key Capability | Agent |
|---|---|
| 1. Semantic Course Retrieval | Learning Advisor (direct) + all agents via `retrieve_courses` tool |
| 2. Relevance Assistance | All agents (cross-cutting) |
| 3. Prerequisite Awareness | Learning Path Designer |
| 4. Skill Gap Identification | Skill Gap Analyst |
| 5. Learning Path Recommendations | Learning Path Designer |
| 6. Career-Oriented Course Exploration | Career Advisor |

### Tool ↔ Agent Mapping

| Tool | Learning Advisor | Skill Gap Analyst | Career Advisor | Learning Path Designer |
|------|:---:|:---:|:---:|:---:|
| `retrieve_courses` (hybrid search) | ✅ | ✅ | ✅ | ✅ |
| `get_user_profile` | ✅ | ✅ | ✅ | ✅ |
| `update_user_profile` | ✅ | — | — | — |
| `web_search` | ✅ | ✅ | ✅ | — |
| `get_course_details` | — | — | — | ✅ |

---

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
| Contextual Relevancy | Replaced by Faithfulness in Multi-Agent architecture. | N/A |

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
| Completeness | Answer Relevancy + agent-specific JSON structure validation cover this. | Production release |
| Coherence | Agent output is structured JSON, not free-form prose. | Free-form response mode |
| Helpfulness | Composite of Answer Relevancy + Completeness + Coherence. Individual metrics are more diagnostic. | Production release |
| Toxicity / Bias | Course recommendation output is formulaic and structured. Low structural risk. Rule-based guardrails handle content safety. | User-generated content integration |
| Conciseness | Would conflict with Completeness. Structured JSON output has inherently controlled length. | N/A |

## 3. Prerequisite Awareness

Measures whether the system considers course prerequisites, difficulty
progression, and learner readiness.

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
| Prerequisite Graph Validation | Dataset lacks course-to-course prerequisite relationship data. | Prerequisite data available in dataset |
| Skill Overlap Detection | Skill clustering is weak (805/1000 courses = "Other" in skill field). | Skill metadata quality improvement |
| Profile Utilization | Requires seeded test user in MongoDB. Current tests run as anonymous user. | Phase 5 (profile-dependent tests) |

## 4. Skill Gap Identification

Measures whether the Skill Gap Analyst correctly identifies missing skills,
uses market data (web search), and recommends relevant courses for each gap.

### Adopted

| Metric | Method | Test | Detects |
|--------|--------|------|---------|
| JSON Format Compliance | Deterministic | `test_skill_gap.py:test_skill_gap_json_format` | Missing required keys or invalid `match_type` |
| Tool Call Presence | Deterministic | `test_skill_gap.py:test_skill_gap_tool_calls` | `web_search` or `retrieve_courses` not called |
| Web Search Utilization | Deterministic | `test_web_search.py:test_skill_gap_uses_web_search` | Skill requirements not grounded in market data |
| Web Search Data Reflection | Deterministic | `test_web_search.py:test_skill_gap_web_search_reflected_in_output` | `web_search` called but results not reflected in gaps |
| Answer Relevancy | LLM-as-Judge (DeepEval) | `test_quality_metrics.py` — 5 Skill Gap cases | Response does not address skill gap question |
| Faithfulness | LLM-as-Judge (DeepEval) | `test_quality_metrics.py` — 5 Skill Gap cases | Hallucinated skills or courses |
| match_type Validity | Deterministic | `test_skill_gap.py:test_skill_gap_json_format` | Dishonest course matching |

### Not adopted

| Metric | Rationale | Reconsider when |
|--------|-----------|-----------------|
| Skill Coverage | GT lacks `expected_skills`. "Correct" skills are subjective and change with market. | Stable skill taxonomy + `expected_skills` in GT |
| Priority Ordering Accuracy | Depends on user's current skills. Anonymous test user has no profile. | Profile Utilization tests (Phase 5) |

## 5. Learning Path Recommendations

Measures whether the Learning Path Designer creates a coherent, progressive
curriculum with appropriate course selection and ordering.

### Adopted

| Metric | Method | Test | Detects |
|--------|--------|------|---------|
| JSON Format Compliance | Deterministic | `test_learning_path.py:test_learning_path_json_format` | Missing required keys |
| Path Coherence | Deterministic | `test_learning_path.py:test_learning_path_level_coherence` | Non-monotonic difficulty progression |
| Level Coverage | Deterministic | `test_learning_path.py:test_learning_path_level_coverage` | Path does not span requested level range |
| Tool Call Presence | Deterministic | `test_learning_path.py:test_learning_path_tool_calls` | `retrieve_courses` not called |
| Course Detail Utilization | Deterministic | `test_learning_path.py:test_learning_path_course_detail_utilization` | `get_course_details` not called |
| Answer Relevancy | LLM-as-Judge (DeepEval) | `test_quality_metrics.py` — 5 Learning Path cases | Response does not address learning path request |
| Faithfulness | LLM-as-Judge (DeepEval) | `test_quality_metrics.py` — 5 Learning Path cases | Courses in path not from retrieval results |

### Not adopted

| Metric | Rationale | Reconsider when |
|--------|-----------|-----------------|
| Actionability | Career Advisor uses this. Learning Path's structured JSON inherently provides actionability. | Free-form path descriptions |
| Completeness | JSON structure validation already checks coverage. | Production release |
| Course Diversity (Provider) | Courses cluster by topic, not provider. Topic relevance should take priority. | Provider-aware recommendation feature |

## 6. Career-Oriented Course Exploration

Measures whether the Career Advisor provides market-grounded career guidance
with actionable plans.

### Adopted

| Metric | Method | Test | Detects |
|--------|--------|------|---------|
| JSON Format Compliance | Deterministic | `test_career.py:test_career_json_format` | Missing required keys |
| Web Search Utilization | Deterministic | `test_web_search.py:test_career_uses_web_search` | Career advice not grounded in current market data |
| Web Search → data_source | Deterministic | `test_web_search.py:test_career_web_search_reflected_in_output` | `data_source` not set to `"web_search"` |
| Action Plan Structure | Deterministic | `test_career.py:test_career_action_plan_structure` | `action_plan` missing `month`/`action`/`milestone` fields |
| Actionability | LLM-as-Judge (GEval) | `test_quality_metrics.py:test_actionability_career` — 5 cases | Vague advice without concrete steps |
| Answer Relevancy | LLM-as-Judge (DeepEval) | `test_quality_metrics.py` — 5 Career cases | Response does not address career question |
| Faithfulness | LLM-as-Judge (DeepEval) | `test_quality_metrics.py` — 5 Career cases | Career data not grounded in web search results |

### Not adopted

| Metric | Rationale | Reconsider when |
|--------|-----------|-----------------|
| Salary Accuracy | Web search results vary per run. Faithfulness metric verifies grounding. | Stable salary data API |
| Multi-Path Comparison Quality | JSON structure ensures multiple paths are presented. Quality covered by Answer Relevancy. | User satisfaction surveys |

---

## Cross-Cutting: Web Search

Web search (`web_search` tool via OpenAI) is a critical data source for
Skill Gap Analyst and Career Advisor. Dedicated tests in `test_web_search.py`
validate:

1. **Tool invocation** — `web_search` appears in `all_tool_calls`
2. **Data reflection** — Web search data is reflected in agent output (gaps/data_source)
3. **Negative case** — Agents that should NOT use web search (Learning Path Designer) do not call it

## Cross-Cutting: Guardrails

Input/output guardrails tested in `test_guardrails.py`:

| Test Group | Cases | Detects |
|------------|-------|---------|
| Off-topic rejection | 5 | Unrelated queries not redirected |
| Prompt injection blocking | 5 | Injection attempts not blocked |
| On-topic pass-through | 5 | Legitimate queries incorrectly blocked |
| Output sanitization | 3 | PII or stack traces leaked in output |

## Cross-Cutting: System Performance

Measured via LangFuse traces (online) and `response.latency_ms` (offline).

| Metric | Measures | Purpose |
|--------|----------|---------|
| E2E Latency (p50/p95/p99) | Request to response complete | User-perceived performance |
| LLM Latency | Agent LLM call time | Largest bottleneck. Model comparison |
| Tool Execution Latency | Per-tool execution time | DB performance degradation |
| Embedding Latency | OpenAI Embedding API call time | Semantic search fixed cost |
| Token Usage (input/output/total) | Tokens consumed per request | Cost calculation, prompt optimization |

---

## Ground Truth Dataset

### Creation context

No real user query logs were available for this PoC. Ground truth was created by examining the 1,000-course sample dataset and manually selecting expected course titles for each test query.

### Structure

- 38 cases total: 20 search/filter + 18 multi-agent routing
- Search cases (gt-01 to gt-20): `expected_titles` manually selected from the 1K dataset
- Routing cases (gt-21 to gt-38): `expected_agent` only, no `expected_titles` — data-independent

### Known limitation — GT is tied to 1K dataset

When the dataset was expanded from 1,000 to 6,599 courses, IR metric scores dropped significantly (Hit Rate 1.00 → 0.71, Precision@5 0.61 → 0.16). This is NOT system degradation — it is GT staleness:

| Pattern | Cases | Cause | Impact |
|---|---|---|---|
| GT data dependency | 15 cases | `expected_titles` selected from 1K. New relevant courses in 6.6K push old ones out of top-5 | Scores appear to drop but retrieval may actually be correct |
| LLM non-determinism | 5 cases | Agent didn't call `retrieve_courses` or delegated differently between runs | Unrelated to data scale |
| Routing (data-independent) | 18 cases | No `expected_titles`, only checks `expected_agent` | Agent Routing = 1.00 on 6.6K ✅ |

**Implication**: IR metrics (Precision@K, Recall@K) from the 6.6K evaluation should not be compared against 1K baselines. GT needs to be rebuilt against the full dataset for meaningful IR measurement.

## Model Comparison Strategy

When comparing models (e.g., gpt-4o vs gpt-4o-mini), the key trade-off axes are:

| Axis | Metrics |
|------|---------|
| Accuracy | Faithfulness, Answer Relevancy, Actionability |
| Search Quality | Precision@K, Recall@K, Hit Rate |
| Structure | JSON Format Compliance, Path Coherence |
| Speed | E2E Latency, LLM Latency |
| Cost | Token Usage x model pricing |

---

# Agent Evaluation Plan

## Agent Workflow Patterns

### 1. Learning Advisor (Orchestrator)

The orchestrator classifies intent using a numbered decision flow (rules 1-7 in prompt) and either handles directly or delegates via `handoff()`.

#### Tools Available
| Tool | Purpose |
|------|---------|
| `retrieve_courses` | Hybrid search (BM25 + dense + RRF) with filters |
| `get_user_profile` | Fetch user skills/goals from MongoDB |
| `update_user_profile` | Store skills/motivation/interest_areas |
| `web_search` | External knowledge (OpenAI web search) |

#### Routing Patterns (handoff to specialist)

| Input Pattern | Expected Agent | Example Query |
|---------------|---------------|---------------|
| Skill gap / missing skills / readiness | Skill Gap Analyst | "What skills am I missing for ML Engineer?" |
| Career path / job market / salary / direction | Career Advisor | "What career should I pursue in tech?" |
| Learning plan / curriculum / step-by-step path | Learning Path Designer | "Create a learning path for web development" |

#### Direct Handling Patterns (no handoff)

| Input Pattern | Expected Tool(s) | Expected Behavior |
|---------------|-------------------|-------------------|
| Greeting / small talk | None | Friendly response, no tool calls |
| Simple course search | `retrieve_courses` | Search + recommend |
| Profile update | `update_user_profile` | Store explicit user data |
| Unrelated question | None | Polite redirect or direct response |
| Ambiguous multi-intent | `retrieve_courses` (fallback) | Handle directly when unclear |

#### Filter Extraction Rules

The LLM must extract explicit constraints into `retrieve_courses` parameters:

| User Phrase | Expected Parameter |
|-------------|-------------------|
| "beginner courses" | `level="Beginner"` |
| "rating above 4.5" | `min_rating=4.5` |
| "courses from Google" | `organization="Google"` |
| "intermediate data science" | `level="Intermediate"`, `query="intermediate data science"` |

Rule: do NOT set filter parameters the user did not mention.

### 2. Skill Gap Analyst

#### Workflow
```
1. get_user_profile(user_id)     → current skills list
2. web_search(target_role)       → market-required skills (primary source)
3. retrieve_courses(skill)       → match platform courses to each gap
4. LLM: combine sources          → classify gaps as "matched" or "alternative"
5. Output: JSON with gaps[]       → priority-ranked, with courses
```

#### Output Schema (JSON)
```
{
  "target_role": string,
  "current_skills": string[],
  "gaps": [
    {
      "skill": string,
      "priority": number,
      "match_type": "matched" | "alternative",
      "reason": string,
      "note"?: string,
      "courses": [{ title, organization, level, rating }]
    }
  ],
  "summary": string
}
```

### 3. Career Advisor

#### Workflow
```
1. web_search(career question)   → job market data (salary, demand, skills, trends)
2. get_user_profile(user_id)     → personalize with existing skills/motivation
3. retrieve_courses(skill)       → match courses to career path skills
4. LLM: synthesize career guidance
5. Output: JSON with career_paths[], recommendation, data_source
```

#### Output Schema (JSON)
```
{
  "career_paths": [
    {
      "role": string,
      "overview": { demand, salary_range, growth_outlook },
      "required_skills": [{ skill, user_has: boolean }],
      "recommended_courses": [{ title, organization, level, rating, reason }],
      "action_plan": [{ month, action, milestone }]
    }
  ],
  "recommendation": string,
  "data_source": "web_search" | "general_knowledge"
}
```

### 4. Learning Path Designer

#### Workflow
```
1. get_user_profile(user_id)     → determine starting level from existing skills
2. Identify learning goal        → topic + target level from user message
3. retrieve_courses(level=X)     → search at multiple levels
4. get_course_details(title)     → check prerequisites, modules, schedule
5. Select 3-6 courses            → high rating, non-overlapping skills
6. Order by prerequisites        → fallback: level ascending
7. Output: JSON with path[], summary
```

#### Output Schema (JSON)
```
{
  "goal": string,
  "personalized": boolean,
  "skipped_levels": string[],
  "reason_for_skip": string,
  "path": [
    {
      "step": number,
      "title": string,
      "organization": string,
      "level": string,
      "rating": number,
      "duration": string,
      "skills_acquired": string[],
      "why": string,
      "prerequisite": string
    }
  ],
  "summary": {
    "total_courses": number,
    "estimated_duration": string,
    "skills_acquired": string[],
    "starting_level": string,
    "target_level": string
  }
}
```

---

## Test Categories

### 1. Routing Tests (deterministic)
Assert `response.agent` matches expected specialist for each query.

| Test Group | GT Cases | Expected Agent |
|------------|----------|----------------|
| Skill gap queries | gt-21 to gt-26 (6) | "Skill Gap Analyst" |
| Career queries | gt-27 to gt-32 (6) | "Career Advisor" |
| Learning path queries | gt-33 to gt-38 (6) | "Learning Path Designer" |
| Direct handling (TO ADD) | 3 new cases | "Learning Advisor" |
| Compound intent (TO ADD) | 3 new cases | Primary intent agent |

### 2. Tool Call Tests (deterministic)

| Agent | Expected Tools | Assert |
|-------|---------------|--------|
| Learning Advisor (direct) | `retrieve_courses` | Present for course search queries |
| Learning Advisor (greeting) | None | `tool_calls` is empty |
| Skill Gap Analyst | `get_user_profile`, `web_search`, `retrieve_courses` | All three present |
| Career Advisor | `web_search`, `get_user_profile`, `retrieve_courses` | `web_search` present |
| Learning Path Designer | `retrieve_courses`, `get_course_details` | Both present |

### 3. Filter Extraction Tests (deterministic)
Assert `response.retrieval_args` contains correct filter parameters. 6 GT cases.

### 4. Output Format Tests (deterministic)

| Agent | Required JSON Keys |
|-------|-------------------|
| Skill Gap Analyst | `target_role`, `current_skills`, `gaps[]`, `summary` |
| Career Advisor | `career_paths[]`, `recommendation`, `data_source` |
| Learning Path Designer | `goal`, `personalized`, `skipped_levels`, `path[]`, `summary` |

### 5. Quality Tests (LLM-as-Judge)

| Metric | Agents | DeepEval Metric | Threshold |
|--------|--------|-----------------|-----------|
| Answer Relevancy | All 4 | `AnswerRelevancyMetric` | 0.5 |
| Faithfulness | All 4 | `FaithfulnessMetric` | 0.5 |
| Actionability | Career Advisor | Custom `GEval` | 0.5 |

### 6. IR Metrics (deterministic)

| Metric | Method | Existing |
|--------|--------|----------|
| Hit Rate | At least one expected course in results | Yes |
| Precision@K | Fraction of top-K results that are relevant | Yes |
| Recall@K | Fraction of expected courses in top-K | Yes |
| Filter Satisfaction | All returned courses match filter constraints | Yes |

---

## Existing Coverage vs Gaps

### Already Implemented

| What | File | Coverage |
|------|------|----------|
| IR metrics (Hit Rate, Precision@K, Recall@K) | `evals/metrics.py` | 14 search GT cases |
| Filter extraction + satisfaction | `evals/metrics.py`, `evals/eval_search.py` | 6 filter GT cases |
| Tool selection (advisor level) | `evals/eval_search.py` | All GT cases |
| Agent routing accuracy | `evals/eval_search.py` | 18 routing GT cases |
| LLM-as-Judge (Answer Relevancy, Faithfulness, Contextual Relevancy) | `evals/eval_search.py` | All cases |
| Ground truth dataset | `evals/ground_truth.json` | 38 cases total |

### Gaps for Multi-Agent Evaluation

| Gap | Priority | Effort |
|-----|----------|--------|
| Negative GT cases (greeting, small talk) | P0 | Low |
| JSON format validation per agent | P0 | Medium |
| Sub-agent tool call exposure | P0 | Medium |
| Path Coherence test | P0 | Low |
| Per-agent LLM-as-Judge | P1 | Medium |
| Compound intent GT cases | P1 | Low |
| Skill Coverage metric | P1 | Medium |
| Level Coverage test | P1 | Low |
| Course Detail Utilization | P1 | Low |
| Web Search Utilization | P1 | Low |
| Actionability metric | P2 | Medium |
| Profile Utilization test | P2 | Medium |
| Agent-specific GT fields | P0 | Medium |

---

## Cost Estimate per Full Run

| Component | Cost |
|-----------|------|
| Agent API calls (~44 cases) | ~$1.00-1.50 |
| LLM-as-Judge (all metrics) | ~$0.22 |
| **Total** | **~$1.20-1.70** |

---

# Evaluation Strategy: Online vs Offline

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

| Evaluator | Target span | Evaluates |
|---|---|---|
| `skill_gap_answer_relevancy` | Skill Gap Analyst | Response relevance |
| `skill_gap_faithfulness` | Skill Gap Analyst | Grounded in context |
| `career_answer_relevancy` | Career Advisor | Response relevance |
| `career_faithfulness` | Career Advisor | Grounded in context |
| `career_actionability` | Career Advisor | Concrete steps, timelines |
| `learning_path_answer_relevancy` | Learning Path Designer | Response relevance |
| `learning_path_faithfulness` | Learning Path Designer | Grounded in context |
| `retrieval_contextual_relevancy` | retrieve_courses | Retrieved courses relevant |
| `web_search_relevancy` | web_search | Search results relevant |

### Score from Code (deterministic)

Sent from `app/scoring.py` after each request:

| Score | Source | Logic |
|---|---|---|
| `tool_selection_correct` | chat.py | `retrieve_courses` in tool_calls → 1.0, else 0.0 |

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

## Why Both?

- **Online** catches production regressions in real-time (no GT needed).
- **Offline** provides precise, reproducible metrics with GT comparison.
- **LLM-as-Judge (LangFuse)** is flexible and code-change-free.
- **Deterministic scores** are exact and free (no LLM cost).
- **DeepEval** integrates with pytest for CI/CD threshold enforcement.

---

# Offline Analysis: Data Scale Impact (1K → 6.6K)

## Summary

Expanding the course dataset from 1,000 to 6,599 courses caused significant
IR metric degradation. Root cause: data quality issues + LLM non-determinism — not Rerank.

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

## Root Cause Analysis

### 1. Data Quality in Expanded Dataset (Primary Cause)
Many added courses have missing or sparse `description` fields. They dilute
top-K results with irrelevant entries, pushing relevant courses out of top-K.

### 2. LLM Non-Determinism (Secondary Cause)
Even with the same prompt and model (gpt-4o-mini), run-to-run variation in
tool calling, agent delegation, and filter parameter extraction.

### 3. Rerank Impact (Minimal)
Slight degradation with rerank ON may be due to the reranker (fastembed all-MiniLM-L6-v2)
re-scoring differently than Qdrant's native RRF ranking, combined with LLM non-determinism.

### 4. Ground Truth Staleness
`expected_titles` were authored against the 1K dataset. With 6.6K courses,
many new relevant courses exist that are not in the expected list.

## Recommendations

1. Rebuild ground truth against the 6,599-course dataset
2. Audit data quality: identify courses with missing descriptions
3. Pin temperature=0 and verify tool_choice to reduce LLM non-determinism
4. Run multiple eval passes (3-5x) and average results
5. Consider MRR/NDCG now that reranking is implemented

---

# Embedding Space Analysis — Summary

Full analysis and visualizations: [`data/embedding-analysis/`](../../data/embedding-analysis/embedding-analysis.md)

## Key Findings

1,000 courses dense embedding (text-embedding-3-small, 1536-dim) t-SNE visualization:

| Color axis | Cluster? | Meaning |
|-----------|----------|---------|
| **Topic** | ✅ Clear | Embedding captures topic similarity |
| **Skill** | △ Weak | Data is sparse (2,195 unique), weak clusters only |
| **Level** | ❌ None | Beginner/Intermediate/Advanced mixed everywhere |
| **Organization** | ❌ None | No separation by provider |

## Design Validation

- **Semantic search** → Topic similarity (embedding's strength)
- **BM25 keyword matching** → Specific skill/tool names (embedding's weakness)
- **Payload filter** → Level, Organization, Rating (not captured by embedding)

## Future Directions

Embedding clustering (HDBSCAN / BERTopic) for automatic topic classification.
