# Offline Evaluation Results — 2026-03-17

## Test Environment
- Model: gpt-4o-mini (OPENAI_MODEL override)
- Infrastructure: Docker Compose (MongoDB + Qdrant + Gateway + AI Service)
- Response caching: enabled (conftest.py `_response_cache`)

## Results by File

| # | Test File | Tests | Passed | Failed | Time | Notes |
|---|-----------|-------|--------|--------|------|-------|
| 01 | test_routing.py | 4 | 4 | 0 | 69s | All agents routed correctly |
| 02 | test_direct_handling.py | 5 | 5 | 0 | 10s | Greeting, off-topic, course search |
| 03 | test_e2e_handoff.py | 3 | 3 | 0 | 65s | Full pipeline validated |
| 04 | test_skill_gap.py | 3 | 2 | 1 | 38s | `courses` key missing in gap entry |
| 05 | test_career.py | 4 | 4 | 0 | 106s | JSON + web_search + action plan |
| 06 | test_learning_path.py | 5 | 5 | 0 | 49s | JSON + level coherence + tool calls |
| 07 | test_web_search.py | 5 | 5 | 0 | 90s | web_search usage per agent verified |
| 08 | test_guardrails.py | 22 | 22 | 0 | 120s | Off-topic, injection, on-topic, PII, sanitization |
| 09 | test_quality_metrics.py | 35 | 34 | 1 | 932s | Answer Relevancy career_4 = 0.45 < 0.50 |

## Grand Total (initial run)
- **86 tests, 84 passed, 2 failed**
- **Total time: ~1,479s (~25 min)**

## Failures (initial run) → Fixed

### 1. test_skill_gap_json_format (test_skill_gap.py)
- **Error**: `Gap entry missing keys: {'courses'}`
- **Root cause**: Skill Gap Analyst omitted `courses` array in gap entries
- **Fix**: Added rule "Every gap entry MUST include a courses array" to prompt
- **Re-run**: PASSED (29s)

### 2. test_answer_relevancy_career[career_4] (test_quality_metrics.py)
- **Error**: Answer Relevancy 0.45 < 0.50
- **Query**: "How much do machine learning engineers earn and what do they do?"
- **Root cause**: Agent responded with course recommendations instead of directly addressing earnings/responsibilities
- **Fix**: Added rule to prioritize overview (salary, demand) for salary/role queries
- **Re-run**: PASSED (366s)

## Final Result After Fixes
- **86 tests, 86 passed, 0 failed**

## Quality Metrics Summary (DeepEval, gpt-4o-mini judge)

| Metric | Skill Gap (5) | Career (5) | Learning Path (5) |
|--------|--------------|------------|-------------------|
| Answer Relevancy | 5/5 PASS | 4/5 PASS | 5/5 PASS |
| Faithfulness | 5/5 PASS | 5/5 PASS | 5/5 PASS |
| Actionability | — | 5/5 PASS | — |

## Performance Notes
- Response caching reduced unique API calls from ~58 to ~25
- Before optimization: estimated 35-45 min → After: ~25 min
- Guardrail off-topic/injection tests are fast (no agent call): 10 tests in ~15s
- Quality metrics (15 agent calls + 35 DeepEval judges) is the bottleneck: 932s
