# Agent Review and Agreed Metrics

Reviewed 2026-03-17. All 4 agents reviewed sequentially with user approval at each step.

## Architecture Overview

```
User → Learning Advisor (orchestrator)
           ├── direct: greeting, course search, profile update
           ├── handoff → Skill Gap Analyst
           ├── handoff → Career Advisor
           └── handoff → Learning Path Designer
```

Star topology — sub-agents have no handoffs to each other (prevents loops).

---

## 1. Skill Gap Analyst

### What it does
Identifies gaps between user's current skills and target role requirements, recommends courses to fill gaps.

### Flow
1. `get_user_profile` — current skills
2. `web_search` — authoritative required skill list for target role (primary source)
3. `retrieve_courses` — match platform courses to required skills
4. LLM combines both sources → classify each gap as `matched` or `alternative`
5. JSON output with priority-ranked gaps

### Key Design Decisions
- **web_search is primary source** for skill requirements (not limited to DB contents)
- **match_type classification**: `matched` (exact course exists) vs `alternative` (no exact match, suggest related course with honest disclosure)
- **Skill name normalization**: LLM treats Python/python3/Python Programming as same skill
- **No-profile fallback**: Output all required skills as self-assessment checklist (don't ask user to list skills)

### Agreed Metrics
| Metric | Description |
|--------|-------------|
| Routing Accuracy | Correct handoff from Learning Advisor |
| Answer Relevancy | DeepEval — response addresses the user's question |
| Faithfulness | DeepEval — no hallucinated skills or courses |
| Skill Coverage | GT `expected_skills` vs skills in response |
| Profile Utilization | When profile exists, `current_skills` in output matches profile |
| JSON Format Compliance | Output contains valid JSON with required keys |

---

## 2. Career Advisor

### What it does
Researches career paths, job market data, and recommends courses aligned with career goals.

### Flow
1. `web_search` — job market data (salary, demand, required skills, trends)
2. `get_user_profile` — personalize based on existing skills/motivation
3. `retrieve_courses` — match courses to career path skills
4. JSON output with career_paths[], action_plan[], recommendation

### Key Design Decisions
- **web_search driven**: Career advice must be grounded in current market data
- **Fallback**: If web_search fails, use general knowledge with `data_source: "general_knowledge"` flag
- **Differentiation from Skill Gap**: Career = "Where should I go?" / Skill Gap = "What am I missing?"
- **JSON output** with `career_paths[]` supporting multi-path comparison

### Agreed Metrics
| Metric | Description |
|--------|-------------|
| Routing Accuracy | Correct handoff from Learning Advisor |
| Answer Relevancy | DeepEval |
| Faithfulness | DeepEval |
| Actionability | LLM-as-Judge — contains concrete action plan with timeline |
| Web Search Utilization | web_search called and data_source reflects result |

### Future TODO
- **Web search caching/efficiency**: Skill Gap and Career Advisor often search similar queries. Consider MongoDB cache or compressed storage for cross-agent sharing.

---

## 3. Learning Path Designer

### What it does
Builds structured, progressive learning plans (3-6 courses) personalized to user's current level.

### Flow
1. `get_user_profile` — determine starting level based on existing skills
2. Identify learning goal from user message
3. `retrieve_courses` at multiple levels (skip levels user already has)
4. `get_course_details` for top candidates (prerequisites, modules)
5. Select 3-6 courses, order by prerequisites
6. JSON output with path[], summary, personalization info

### Key Design Decisions
- **get_user_profile added** (was initially excluded) — essential for personalization (skip beginner if user knows basics)
- **Prerequisite fallback**: If unclear, default to level ascending → review count descending
- **Course selection criteria**: High rating, non-overlapping skills, provider diversity
- **JSON output** with `personalized`, `skipped_levels`, `reason_for_skip`

### Agreed Metrics
| Metric | Description |
|--------|-------------|
| Routing Accuracy | Correct handoff from Learning Advisor |
| Answer Relevancy | DeepEval |
| Faithfulness | DeepEval |
| Path Coherence | Courses ordered Beginner→Intermediate→Advanced (no backwards jumps) |
| Level Coverage | Path spans from user's current level to target level |
| Course Detail Utilization | get_course_details called for recommended courses |
| JSON Format Compliance | Valid JSON with required keys |

---

## 4. Learning Advisor (Orchestrator)

### What it does
Entry point for all user requests. Determines intent and either handles directly or delegates to specialist agent.

### Flow
```
User Request → Intent Classification (if-then decision flow)
  1. Greeting/small talk → direct response
  2. Simple course search → retrieve_courses → direct response
  3. Profile update → update_user_profile → direct response
  4. Skill gap question → handoff → Skill Gap Analyst
  5. Career question → handoff → Career Advisor
  6. Learning path request → handoff → Learning Path Designer
  7. Multiple intents → primary intent's specialist / if unclear → direct
```

### Key Design Decisions
- **Star topology**: No sub-agent-to-sub-agent handoffs (loop prevention)
- **If-then decision flow**: Numbered priority-based routing instead of vague examples
- **"When in doubt, handle directly"**: Conservative — bad handoff is worse than direct handling
- **web_search on orchestrator**: Light general questions handled without handoff
- **ContextVar reset at run_agent() start**: Request isolation for async safety

### Proposed Metrics (to be validated after usage)
| Metric | Description |
|--------|-------------|
| Routing Accuracy | Correct agent handles the request (existing 18 GT cases) |
| Direct Handling Accuracy | No handoff for greeting/simple search (negative cases) |
| Filter Extraction Accuracy | `retrieval_args` matches GT `expected_filters` (existing 20 cases) |
| End-to-End Latency | Total time, split by handoff vs direct (LangFuse trace) |
| Answer Relevancy | DeepEval — for direct-handling cases only |
| Tool Call Efficiency | No unnecessary tool calls (e.g., no retrieve_courses on greeting) |

### GT Cases to Add
- Negative cases (3): greeting, small talk, unrelated question → expected_agent: "Learning Advisor"
- Compound intent cases (3): e.g., "Find Python courses and also analyze my skill gaps" → primary intent agent

---

## Cross-Agent Improvements Completed

| Improvement | Status | Files Changed |
|-------------|--------|---------------|
| P0: Timeout settings (MongoDB 5s, Qdrant 10s, OpenAI 60s) | Done | clients/*.py |
| P0: Input validation (Pydantic, 1-2000 chars, ObjectId) | Done | routers/chat.py |
| P1: ContextVar migration (async safety) | Done | agent/context.py |
| P1: web_search retry (2 retries, exponential backoff) | Done | tools/web_search.py |
| P1: Handoff decision flow (if-then rules) | Done | learning_advisor.py |
| P2: Skill Gap no-profile fallback | Done | skill_gap.py |
| P2: Learning Path prerequisite fallback | Done | learning_path.py |
| Unified error format `[ERROR]` prefix | Done | all tools |
| JSON output for all specialist agents | Done | skill_gap.py, career.py, learning_path.py |
| Learning Path personalization (added get_user_profile) | Done | learning_path.py |

## Remaining TODO
- Evaluation framework: Implement agent-specific GT fields and metrics in eval code
- Web search caching: Cross-agent sharing (MongoDB cache or compression)
- GT expansion: Negative cases, compound intents, agent-specific expected fields
- Phase 4-6: Full data ingestion, tests/CI/CD/safety, docs/presentation
