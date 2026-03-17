# Agent Evaluation Plan

## Overview

- **Architecture**: Star topology — Learning Advisor (orchestrator) routes to 3 specialists via `handoff()`
- **Framework**: Pytest + DeepEval (Pytest plugin) + custom IR metrics (`evals/metrics.py`)
- **Principle**: Deterministic tests first, LLM-as-Judge only where necessary
- **Model for judge**: gpt-4o-mini (cost control, per project convention)
- **Entry point**: `POST /api/v1/chat` returns `ChatResponse` with `agent`, `tool_calls`, `retrieval_tool_calls`, `retrieval_args`, `courses`, `reply`

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

#### Metrics & Test Approach

| Metric | Test Type | What to Assert | Existing Coverage |
|--------|-----------|---------------|-------------------|
| Routing Accuracy | Deterministic | `response.agent` == expected agent | Yes: `run_agent_routing_eval()` with 18 GT cases (gt-21 to gt-38) |
| Direct Handling Accuracy | Deterministic | `response.agent` == "Learning Advisor" for greetings/simple search | No: need negative GT cases |
| Filter Extraction Accuracy | Deterministic | `response.retrieval_args` matches `expected_filters` | Yes: `run_filter_eval()` with ~6 GT cases |
| Tool Call Efficiency | Deterministic | No `retrieve_courses` on greetings; `retrieve_courses` present for course queries | Partial: `run_tool_selection_eval()` checks retrieve_courses presence |
| Answer Relevancy (direct only) | LLM-as-Judge | DeepEval AnswerRelevancy >= 0.5 | Yes: `run_deepeval()` for course search cases |
| E2E Latency | Deterministic | `response.latency_ms` < threshold (LangFuse traces) | Yes: latency stats in eval_search.py |

---

### 2. Skill Gap Analyst

#### Workflow Steps

```
1. get_user_profile(user_id)     → current skills list
2. web_search(target_role)       → market-required skills (primary source)
3. retrieve_courses(skill)       → match platform courses to each gap
4. LLM: combine sources          → classify gaps as "matched" or "alternative"
5. Output: JSON with gaps[]       → priority-ranked, with courses
```

#### Tool Call Sequence

| Step | Tool | Purpose | Required? |
|------|------|---------|-----------|
| 1 | `get_user_profile` | Get current skills | Yes (if user_id provided) |
| 2 | `web_search` | Research target role requirements | Yes |
| 3 | `retrieve_courses` | Find courses for gap skills | Yes (1+ calls) |

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
      "note"?: string,          // only for "alternative" match_type
      "courses": [{ title, organization, level, rating }]
    }
  ],
  "summary": string
}
```

#### Key Decision Points

- **No profile available**: Output `current_skills: []` and present ALL required skills as self-assessment checklist (do NOT ask user to list skills)
- **Skill name normalization**: LLM treats "Python" / "python3" / "Python Programming" as equivalent
- **match_type classification**: `matched` = exact course exists; `alternative` = related course with honest disclosure

#### Testable Behaviors

1. Tool call presence: `get_user_profile`, `web_search`, `retrieve_courses` all called
2. Output contains valid JSON with required keys (`target_role`, `current_skills`, `gaps`, `summary`)
3. Each gap has `skill`, `priority`, `match_type`, `courses`
4. `match_type` is one of `"matched"` or `"alternative"`
5. Priorities are sequential integers starting from 1
6. When user profile has skills, `current_skills` reflects profile data

#### Metrics & Test Approach

| Metric | Test Type | What to Assert | Existing Coverage |
|--------|-----------|---------------|-------------------|
| Routing Accuracy | Deterministic | `response.agent` == "Skill Gap Analyst" | Yes: 6 GT cases (gt-21 to gt-26) |
| Answer Relevancy | LLM-as-Judge | Response addresses the skill gap question | No: DeepEval currently only runs on course search cases |
| Faithfulness | LLM-as-Judge | No hallucinated skills or courses | No: needs agent-specific test cases |
| Skill Coverage | Deterministic | GT `expected_skills` subset present in response gaps[].skill | No: GT cases lack `expected_skills` field |
| Profile Utilization | Deterministic | When profile exists, `current_skills` in output matches profile | No: requires test user with known profile |
| JSON Format Compliance | Deterministic | Parse JSON from response, validate required keys | No: new test needed |

---

### 3. Career Advisor

#### Workflow Steps

```
1. web_search(career question)   → job market data (salary, demand, skills, trends)
2. get_user_profile(user_id)     → personalize with existing skills/motivation
3. retrieve_courses(skill)       → match courses to career path skills
4. LLM: synthesize career guidance
5. Output: JSON with career_paths[], recommendation, data_source
```

#### Tool Call Sequence

| Step | Tool | Purpose | Required? |
|------|------|---------|-----------|
| 1 | `web_search` | Current market data | Yes |
| 2 | `get_user_profile` | Personalization | Yes (if user_id provided) |
| 3 | `retrieve_courses` | Course recommendations | Yes (1+ calls) |

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

#### Key Decision Points

- **web_search failure**: Fallback to `data_source: "general_knowledge"` with explicit disclaimer
- **Differentiation from Skill Gap**: Career = "Where should I go?" / Skill Gap = "What am I missing?"
- **Multi-path comparison**: Multiple entries in `career_paths[]` when user asks about alternatives

#### Testable Behaviors

1. Tool calls: `web_search` called; `retrieve_courses` called
2. Output contains valid JSON with `career_paths`, `recommendation`, `data_source`
3. Each career path has `action_plan` with timeline (months)
4. `data_source` reflects whether web_search succeeded
5. When comparing careers, multiple entries in `career_paths[]`

#### Metrics & Test Approach

| Metric | Test Type | What to Assert | Existing Coverage |
|--------|-----------|---------------|-------------------|
| Routing Accuracy | Deterministic | `response.agent` == "Career Advisor" | Yes: 6 GT cases (gt-27 to gt-32) |
| Answer Relevancy | LLM-as-Judge | Response addresses career question | No |
| Faithfulness | LLM-as-Judge | Career data grounded in web_search results | No |
| Actionability | LLM-as-Judge | Contains concrete action plan with timeline | No: new custom metric |
| Web Search Utilization | Deterministic | `web_search` in `tool_calls` AND `data_source` field present | No: new test needed |
| JSON Format Compliance | Deterministic | Parse JSON, validate required keys | No: new test needed |

---

### 4. Learning Path Designer

#### Workflow Steps

```
1. get_user_profile(user_id)     → determine starting level from existing skills
2. Identify learning goal        → topic + target level from user message
3. retrieve_courses(level=X)     → search at multiple levels (Beginner, Intermediate, Advanced)
4. get_course_details(title)     → check prerequisites, modules, schedule for top candidates
5. Select 3-6 courses            → high rating, non-overlapping skills, provider diversity
6. Order by prerequisites        → fallback: level ascending, review count descending
7. Output: JSON with path[], summary, personalization info
```

#### Tool Call Sequence

| Step | Tool | Purpose | Required? |
|------|------|---------|-----------|
| 1 | `get_user_profile` | Starting level determination | Yes (if user_id provided) |
| 2 | `retrieve_courses` | Multi-level course search | Yes (2-3 calls at different levels) |
| 3 | `get_course_details` | Prerequisite/module check | Yes (for recommended courses) |

**Unique tool**: `get_course_details` is exclusive to Learning Path Designer (not available to other agents).

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

#### Key Decision Points

- **Level skipping**: If user profile shows beginner skills, skip Beginner level (`skipped_levels`, `reason_for_skip`)
- **No profile**: Set `personalized: false`, `skipped_levels: []`, start from Beginner
- **Course selection**: High rating + non-overlapping skills + provider diversity
- **Path length**: 3-6 courses (not overwhelming)

#### Testable Behaviors

1. Multiple `retrieve_courses` calls with different `level` parameters
2. `get_course_details` called for recommended courses
3. `path[]` ordered: levels never go backwards (Beginner < Intermediate < Advanced)
4. 3-6 courses in path
5. When user profile has relevant skills, `personalized: true` and `skipped_levels` non-empty
6. No profile: `personalized: false`, starts from Beginner

#### Metrics & Test Approach

| Metric | Test Type | What to Assert | Existing Coverage |
|--------|-----------|---------------|-------------------|
| Routing Accuracy | Deterministic | `response.agent` == "Learning Path Designer" | Yes: 6 GT cases (gt-33 to gt-38) |
| Answer Relevancy | LLM-as-Judge | Response addresses learning path request | No |
| Faithfulness | LLM-as-Judge | Courses in path exist in DB | No |
| Path Coherence | Deterministic | Levels in path[] are non-decreasing | No: new test needed |
| Level Coverage | Deterministic | Path spans from starting_level to target_level | No: new test needed |
| Course Detail Utilization | Deterministic | `get_course_details` appears in tool_calls | No: new test needed |
| JSON Format Compliance | Deterministic | Parse JSON, validate required keys | No: new test needed |

---

## Test Categories

### 1. Routing Tests (deterministic, no API cost beyond agent call)

Assert `response.agent` matches expected specialist for each query.

| Test Group | GT Cases | Expected Agent |
|------------|----------|----------------|
| Skill gap queries | gt-21 to gt-26 (6) | "Skill Gap Analyst" |
| Career queries | gt-27 to gt-32 (6) | "Career Advisor" |
| Learning path queries | gt-33 to gt-38 (6) | "Learning Path Designer" |
| Direct handling (TO ADD) | 3 new cases | "Learning Advisor" |
| Compound intent (TO ADD) | 3 new cases | Primary intent agent |

**Existing**: `run_agent_routing_eval()` in `evals/eval_search.py` covers this. 18 GT cases exist.

**Gap**: No negative cases (greeting, small talk) or compound intent cases.

### 2. Tool Call Tests (deterministic)

Assert expected tools were called by checking `response.tool_calls`.

| Agent | Expected Tools | Assert |
|-------|---------------|--------|
| Learning Advisor (direct) | `retrieve_courses` | Present for course search queries |
| Learning Advisor (greeting) | None | `tool_calls` is empty |
| Skill Gap Analyst | `get_user_profile`, `web_search`, `retrieve_courses` | All three present |
| Career Advisor | `web_search`, `get_user_profile`, `retrieve_courses` | `web_search` present |
| Learning Path Designer | `retrieve_courses`, `get_course_details` | Both present; multiple `retrieve_courses` calls |

**Existing**: `run_tool_selection_eval()` only checks `retrieve_courses` at advisor level.

**Gap**: No per-agent tool call validation for specialist agents. The current `tool_calls` field in `ChatResponse` captures outer (Learning Advisor) tool calls. Sub-agent tool calls are not currently exposed in the API response.

**Implementation note**: Sub-agent tool calls must be extracted from `result.raw_responses` or added to context vars (similar to `retrieval_tool_calls`). This is a code change prerequisite.

### 3. Filter Extraction Tests (deterministic)

Assert `response.retrieval_args` contains correct filter parameters.

**Existing**: `run_filter_eval()` with `filter_param_accuracy()` covers this for 6 GT cases (gt-03, gt-07, gt-09, gt-15, gt-20, and level-only cases).

**Gap**: No filter extraction tests for specialist agents (they also call `retrieve_courses` with filters).

### 4. Output Format Tests (deterministic)

Assert JSON structure in `response.reply` for specialist agents.

| Agent | Required JSON Keys |
|-------|-------------------|
| Skill Gap Analyst | `target_role`, `current_skills`, `gaps[]` (each with `skill`, `priority`, `match_type`, `courses`), `summary` |
| Career Advisor | `career_paths[]` (each with `role`, `overview`, `required_skills`, `recommended_courses`, `action_plan`), `recommendation`, `data_source` |
| Learning Path Designer | `goal`, `personalized`, `skipped_levels`, `path[]` (each with `step`, `title`, `level`, `rating`), `summary` |

**Existing**: None. This is entirely new.

**Implementation**: Parse `response.reply` with regex to extract JSON code block, then `json.loads()` and validate keys.

### 5. Quality Tests (LLM-as-Judge, API cost)

| Metric | Agents | DeepEval Metric | Threshold |
|--------|--------|-----------------|-----------|
| Answer Relevancy | All 4 | `AnswerRelevancyMetric` | 0.5 |
| Faithfulness | All 4 | `FaithfulnessMetric` | 0.5 |
| Actionability | Career Advisor | Custom `GEval` or `LLMJudgeMetric` | 0.5 |

**Existing**: `run_deepeval()` runs AnswerRelevancy, Faithfulness, ContextualRelevancy on course search cases only.

**Gap**: No LLM-as-Judge evaluation for specialist agent outputs. Need new test cases with `retrieval_context` from sub-agent tool results.

**Actionability metric** (Career Advisor only): Custom LLM-as-Judge prompt:
> "Does the response contain a concrete action plan with specific steps, timeline (months), and measurable milestones? Score 0-1."

### 6. IR Metrics (deterministic)

| Metric | Method | Existing |
|--------|--------|----------|
| Hit Rate | At least one expected course in results | Yes: `hit_rate()` |
| Precision@K | Fraction of top-K results that are relevant | Yes: `precision_at_k()` |
| Recall@K | Fraction of expected courses in top-K | Yes: `recall_at_k()` |
| Filter Satisfaction | All returned courses match filter constraints | Yes: `filter_satisfaction()` |

**Existing**: Fully implemented in `evals/metrics.py` for course search cases (gt-01 to gt-20).

**Gap**: Specialist agents also call `retrieve_courses`, but their results are embedded in the JSON response, not exposed as `response.courses`. IR metrics for specialist agents would require parsing courses from the JSON output.

---

## Existing Coverage vs Gaps

### Already Implemented (in `evals/`)

| What | File | Coverage |
|------|------|----------|
| IR metrics (Hit Rate, Precision@K, Recall@K) | `evals/metrics.py` | 14 search GT cases |
| Filter extraction + satisfaction | `evals/metrics.py`, `evals/eval_search.py` | 6 filter GT cases |
| Tool selection (advisor level) | `evals/eval_search.py` | All GT cases |
| Agent routing accuracy | `evals/eval_search.py` | 18 routing GT cases |
| LLM-as-Judge (Answer Relevancy, Faithfulness, Contextual Relevancy) | `evals/eval_search.py` | All cases (course search focus) |
| Latency stats (p50/p95/p99) | `evals/eval_search.py` | All cases |
| Ground truth dataset | `evals/ground_truth.json` | 38 cases total |

### Gaps for Multi-Agent Evaluation

| Gap | Priority | Effort | Description |
|-----|----------|--------|-------------|
| **Negative GT cases** | P0 | Low | Add 3 cases: greeting, small talk, unrelated → expected_agent: "Learning Advisor", expected tool_calls: [] |
| **Compound intent GT cases** | P1 | Low | Add 3 cases with mixed intents → expected primary agent |
| **JSON format validation** | P0 | Medium | New test: parse specialist JSON output, validate required keys per agent schema |
| **Sub-agent tool call exposure** | P0 | Medium | Code change: capture sub-agent tool_calls in context vars (similar to retrieval_tool_calls) |
| **Per-agent LLM-as-Judge** | P1 | Medium | Extend DeepEval to run on specialist agent responses with agent-specific context |
| **Skill Coverage metric** | P1 | Medium | Add `expected_skills` to GT cases (gt-21 to gt-26), compare with response gaps[].skill |
| **Profile Utilization test** | P2 | Medium | Create test user in DB, verify `current_skills` matches profile |
| **Path Coherence test** | P0 | Low | Parse Learning Path JSON, assert levels are non-decreasing |
| **Level Coverage test** | P1 | Low | Assert path spans from starting_level to target_level in summary |
| **Course Detail Utilization** | P1 | Low | Assert `get_course_details` in tool_calls for Learning Path cases |
| **Actionability metric** | P2 | Medium | Custom LLM-as-Judge for Career Advisor action plans |
| **Web Search Utilization** | P1 | Low | Assert `web_search` in tool_calls for Career/Skill Gap cases |
| **Agent-specific GT fields** | P0 | Medium | Add `expected_skills`, `expected_json_keys`, `expected_tools` per agent in ground_truth.json |

---

## Ground Truth Expansion Needed

### New GT Cases to Add

```json
// Negative cases (direct handling)
{ "id": "gt-39", "query": "Hello!", "expected_agent": "Learning Advisor", "expected_tools": [] }
{ "id": "gt-40", "query": "What's the weather like today?", "expected_agent": "Learning Advisor", "expected_tools": [] }
{ "id": "gt-41", "query": "Tell me a joke", "expected_agent": "Learning Advisor", "expected_tools": [] }

// Compound intent cases
{ "id": "gt-42", "query": "Find Python courses and analyze my skill gaps for ML Engineer", "expected_agent": "Skill Gap Analyst" }
{ "id": "gt-43", "query": "I want to learn data science. What career options exist and create a study plan", "expected_agent": "Learning Path Designer" }
{ "id": "gt-44", "query": "Show me beginner AI courses and tell me about AI career paths", "expected_agent": "Career Advisor" }
```

### Existing GT Cases: Fields to Add

For gt-21 to gt-26 (Skill Gap):
- `expected_skills`: e.g., `["TensorFlow", "PyTorch", "MLOps", "Deep Learning"]` for ML Engineer
- `expected_json_keys`: `["target_role", "current_skills", "gaps", "summary"]`

For gt-27 to gt-32 (Career):
- `expected_json_keys`: `["career_paths", "recommendation", "data_source"]`
- `expected_tools`: `["web_search", "retrieve_courses"]`

For gt-33 to gt-38 (Learning Path):
- `expected_json_keys`: `["goal", "personalized", "path", "summary"]`
- `expected_tools`: `["retrieve_courses", "get_course_details"]`

---

## Cost Estimate

### Deterministic Tests (no LLM judge cost)

Each test case requires one agent call through the API:
- **Agent call cost**: ~$0.01-0.03 per case (gpt-4o-mini, ~1000-3000 tokens)
- **Specialist agents with web_search**: ~$0.02-0.05 per case (additional web search sub-agent call)

| Test Category | Cases | Agent Cost | Judge Cost | Total |
|---------------|-------|------------|------------|-------|
| Routing (existing 18) | 18 | ~$0.54 | $0 | ~$0.54 |
| Routing (new 6) | 6 | ~$0.12 | $0 | ~$0.12 |
| Filter extraction | 6 | (shared with routing) | $0 | $0 |
| JSON format validation | 18 | (shared with routing) | $0 | $0 |
| Tool call validation | 18 | (shared with routing) | $0 | $0 |
| Path coherence | 6 | (shared with routing) | $0 | $0 |
| IR metrics (course search) | 14 | ~$0.28 | $0 | ~$0.28 |

### LLM-as-Judge Tests

- **Judge cost**: ~$0.002-0.005 per metric per case (gpt-4o-mini)
- DeepEval internally makes multiple judge calls per metric

| Test Category | Cases | Metrics | Est. Judge Cost |
|---------------|-------|---------|-----------------|
| Answer Relevancy (all agents) | 38 | 1 | ~$0.10 |
| Faithfulness (all agents) | 38 | 1 | ~$0.10 |
| Actionability (Career only) | 6 | 1 | ~$0.02 |

### Total Estimated Cost per Full Run

| Component | Cost |
|-----------|------|
| Agent API calls (~44 cases) | ~$1.00-1.50 |
| LLM-as-Judge (all metrics) | ~$0.22 |
| **Total** | **~$1.20-1.70** |

For `--hit-rate-only` mode (deterministic only): ~$1.00-1.50 (agent calls only, no judge).

---

## Recommended Implementation Order

### Phase 1: Deterministic Foundation (no new API cost patterns)

1. **Add negative + compound GT cases** (gt-39 to gt-44) to `ground_truth.json`
   - Immediate: extends existing `run_agent_routing_eval()` coverage
   - Effort: ~30 min

2. **Add JSON format validation test**
   - New function: `run_json_format_eval()` in `eval_search.py`
   - Parse JSON from specialist agent replies, validate required keys per agent
   - Effort: ~1 hour

3. **Add Path Coherence test**
   - New function: `run_path_coherence_eval()` — parse Learning Path JSON, check level ordering
   - Effort: ~30 min

4. **Add Web Search Utilization test**
   - Check `web_search` in `tool_calls` for Skill Gap and Career cases
   - Effort: ~30 min

### Phase 2: Observability Prerequisite (code change)

5. **Expose sub-agent tool calls in API response**
   - Extend `context.py` with `_sub_agent_tool_calls` ContextVar
   - Capture tool calls from specialist agents in `run_agent()`
   - Add `sub_agent_tool_calls` to `ChatResponse`
   - Effort: ~2 hours
   - Prerequisite for: per-agent tool call validation, course detail utilization test

### Phase 3: Agent-Specific GT Enrichment

6. **Add `expected_skills` to Skill Gap GT cases**
   - Research realistic expected skills per target role
   - Implement `skill_coverage()` metric in `evals/metrics.py`
   - Effort: ~1 hour

7. **Add `expected_json_keys` and `expected_tools` to all specialist GT cases**
   - Effort: ~30 min

### Phase 4: LLM-as-Judge Extension

8. **Extend DeepEval to specialist agents**
   - Run AnswerRelevancy + Faithfulness on specialist outputs
   - Context: use the agent's JSON response as `actual_output`
   - Effort: ~1 hour

9. **Implement Actionability metric for Career Advisor**
   - Custom `GEval` metric with criteria: concrete steps, timeline, milestones
   - Effort: ~1 hour

### Phase 5: Profile-Dependent Tests

10. **Create test user fixture and Profile Utilization tests**
    - Seed MongoDB with known test user (skills, motivation)
    - Run Skill Gap + Learning Path with `user_id`, verify personalization
    - Effort: ~2 hours

---

## Architecture Note: Sub-Agent Tool Call Visibility

Currently, `ChatResponse.tool_calls` only captures Learning Advisor-level tool calls (from `result.raw_responses`). When a handoff occurs, the specialist agent's tool calls are not exposed.

The `retrieval_tool_calls` field captures `retrieve_courses` → `hybrid_search` calls via ContextVar, but other tool calls (`web_search`, `get_user_profile`, `get_course_details`) in specialist agents are invisible.

**Recommendation** (Phase 2, item 5): Add a `_sub_agent_tool_calls` ContextVar that each tool function appends to. This enables deterministic validation of specialist agent behavior without parsing natural language responses.
