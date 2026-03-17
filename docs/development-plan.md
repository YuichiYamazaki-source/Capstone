# Development Plan — Intelligent University Course Finder

**Tags**: #type/reference #domain/planning

---

## Phase 1: UI Mock ✅

- Build HTML mockups using MUI CDN to design screen layouts
- Cross-reference with Requirements.md to confirm necessary features
- Iterate on design with preview feedback

**Goal**: Finalize screen specifications and feature list

---

## Phase 2: Full-Stack MVP ✅

- Set up FastAPI microservices (Gateway, Course Service, User Service)
- MongoDB integration (courses + users)
- React + Vite + MUI frontend with all pages
- JWT authentication flow
- CSV data ingestion pipeline (100 sample courses)
- Frontend-Backend integration via Vite proxy

**Goal**: Working full-stack application with real data

---

## Phase 3: AI Functional — "Make it work" 🚧

Build the AI pipeline end-to-end with sample courses. The goal is functional correctness, not optimization.

| # | Task | Status | Details |
|---|------|--------|---------|
| 3-1 | Structured logging | ✅ | JSON structured logging across all services |
| 3-2 | Qdrant setup | ✅ | Docker Compose + hybrid search (dense + sparse vectors) |
| 3-3 | Embedding pipeline | ✅ | 1,000 courses (stratified sample) → OpenAI text-embedding-3-small → Qdrant |
| 3-4 | AI Service | ✅ | Microservice with tools-based architecture (not MCP — tools via OpenAI Agents SDK) |
| 3-5 | Agents | 🚧 | Single Agent (Learning Advisor) + Course Retrieval tool done. Remaining: Skill Gap, Learning Path, Career agents |
| 3-6 | RAG pipeline | ✅ | Hybrid search (BM25 sparse + dense + RRF fusion), level normalization, filter extraction |
| 3-7 | Explore chat | ✅ | Chat API → Learning Advisor Agent → hybrid search → response |

**Goal**: RAG + Agents working end-to-end with sample courses
**Exit criteria**: User can chat, get semantic search results, and receive AI-powered recommendations

---

## Phase 4: Measurable — "Make it right" 🚧

Instrument, measure, and improve. This phase focuses on evaluation metrics, accuracy improvement, and observability. Includes both offline and online validation.

| # | Task | Status | Details |
|---|------|--------|---------|
| 4-1 | Observability setup | ✅ | LangFuse v4 (traces + scores) + Arize Phoenix (OTEL + cost). Tracing strategy finalized. |
| 4-2 | Full data ingestion | ⬜ | 6,645 courses: cleansing, embedding, Qdrant indexing (currently 1,000 sample) |
| 4-3 | Ground truth dataset | ✅ | 20 test cases: keyword/semantic, filter-only, mixed. Curated from indexed data. |
| 4-4 | Offline evaluation | ✅ | IR metrics (Hit Rate, Precision@5, Recall@5) + Filter metrics + DeepEval LLM-as-Judge (Answer Relevancy, Faithfulness, Contextual Relevancy) |
| 4-5 | Online evaluation | 🚧 | Latency p50/p95/p99 captured. LangFuse score graph fixed. Throughput testing pending. |
| 4-6 | Accuracy improvement | ⬜ | Reranker tuning, prompt optimization, embedding strategy refinement |
| 4-7 | Performance optimization | ⬜ | Parallel ingestion, connection pooling, cold start optimization |

### Tracing Strategy (to be finalized in 4-1)

| Tool | Role | Scope |
|------|------|-------|
| **OpenAI Agents SDK Tracing** | Agent internal step visibility | Tool call sequence, LLM call count per agent, handoff tracking |
| **LangFuse** | Cross-cutting LLM observability | Cost per query, latency trends, prompt versioning, A/B comparison |
| **Arize Phoenix** | Retrieval quality monitoring | Embedding drift detection, retrieval relevance dashboards, dataset analysis |

Synergy: Agent SDK traces feed into LangFuse for cost/latency aggregation. Arize Phoenix monitors the vector search layer independently. Together they cover the full pipeline: query → embedding → retrieval → agent reasoning → response.

**Goal**: Quantified accuracy and performance baselines with improvement evidence
**Exit criteria**: Documented metrics (Latency + Accuracy), improvement trajectory visible in dashboards

---

## Phase 5: Resilient — "Make it safe"

Harden the system for reliability and safety. Define thresholds for CI/CD pipeline gates.

| # | Task | Details |
|---|------|---------|
| 5-1 | Local fallback | MiniLM-L6-v2 embedding when OpenAI is unavailable |
| 5-2 | Graceful degradation | Vector DB down → keyword search fallback chain |
| 5-3 | Error handling | Circuit breaker, retry with backoff, timeout handling |
| 5-4 | Guardrails | Content appropriateness, prerequisite validation, input sanitization |
| 5-5 | Test suite | Unit + Integration + Load tests (pytest + locust) |
| 5-6 | CI/CD thresholds | Define quality gates: min accuracy, max latency, guardrail pass rate |
| 5-7 | Safety evaluation | Guardrail metrics evaluation, edge case stress testing |

**Goal**: System degrades gracefully under failure; safety metrics meet defined thresholds
**Exit criteria**: All checklist §3-§4 items checked, CI/CD pipeline with quality gates defined

---

## Phase 6: Deliverable — "Ship it"

Final documentation, presentation, and deployment readiness.

| # | Task | Details |
|---|------|---------|
| 6-1 | Architecture diagram | JPEG/PDF export for submission |
| 6-2 | Stakeholder PPT | Briefing deck: EDA, Design, Decisions, Evaluation results |
| 6-3 | README finalization | Ensure code/structure matches README |
| 6-4 | Documentation review | All docs/ updated, checklist items verified |
| 6-5 | Panel presentation | 8 min demo + 2 min Q&A preparation |

**Goal**: All deliverables complete and submission-ready
**Exit criteria**: Checklist fully satisfied, presentation rehearsed

---

## Phase Summary

```
Phase 1  ✅  UI Mock
Phase 2  ✅  Full-Stack MVP
Phase 3  🚧  AI Functional    — "Make it work"    (機能性)      ← 3-5 remaining agents
Phase 4  🚧  Measurable       — "Make it right"   (評価・精度向上) ← 4-2, 4-6, 4-7 remaining
Phase 5  ⬜  Resilient        — "Make it safe"    (安全性・耐障害性)
Phase 6  ⬜  Deliverable      — "Ship it"         (提出・発表)
```
