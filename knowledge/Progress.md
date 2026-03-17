# Progress — Capstone Milestones

**Tags**: #type/knowledge #type/capstone

## Milestone Tracker

| Date | Milestone | Status | Notes |
|------|-----------|--------|-------|
| 2026-03-13 | Project kickoff | ✅ | Repo created, branch strategy decided |
| 2026-03-13 | Tech stack (partial) | ✅ | Agent SDK, FastAPI, React+Vite confirmed |
| 2026-03-13 | Requirements analysis | ✅ | Requirements.md created from PDF |
| 2026-03-13 | Dataset analysis | ✅ | 6,645 courses analyzed, biases documented |
| 2026-03-13 | UI Design | ✅ | Personas, UX flow, page specs documented |
| 2026-03-14 | Phase 1: HTML mockup | ✅ | MUI CDN mock for layout validation |
| 2026-03-15 | Phase 2: Backend MVP | ✅ | Gateway + Course Service + User Service + MongoDB in Docker |
| 2026-03-15 | Phase 2: Frontend | ✅ | React + Vite + MUI, all pages implemented |
| 2026-03-15 | Frontend-Backend integration | ✅ | JWT auth, course API, profile API connected |
| 2026-03-16 | Browse page redesign | ✅ | 3-column grid cards, trending topics, filter search |
| 2026-03-16 | Personal Analysis page | ✅ | Domain coverage, career alignment, skill gaps, recommended paths |
| 2026-03-16 | Learning Path merged into Analysis | ✅ | Single unified analysis page |
| 2026-03-16 | DB selection | ✅ | MongoDB + Qdrant (rationale in Tech Stack.md) |
| 2026-03-16 | Embedding model selection | ✅ | OpenAI small (primary) + MiniLM-L6-v2 (fallback) |
| 2026-03-16 | Documentation overhaul | ✅ | CLAUDE.md reference guide, Tech Stack rationale, Architecture update |
| 2026-03-16 | MongoDB migration | ✅ | Course Service: in-memory JSON → Motor async MongoDB. 100 courses ingested |
| 2026-03-16 | Directory restructure | ✅ | Checklist-compliant: docs/, requirements/, tests/ added. ref/ preserved |
| 2026-03-16 | Production vs PoC doc | ✅ | docs/architecture/production-vs-poc.md created |
| | **Phase 3: AI Functional** | | **"Make it work"** |
| 2026-03-16 | 3-1 Structured logging | ✅ | JSON structured logging across all services |
| 2026-03-16 | 3-2 Qdrant setup | ✅ | Docker Compose + hybrid search (dense + sparse) |
| 2026-03-16 | 3-3 Embedding pipeline | ✅ | 1,000 courses (stratified sample) → OpenAI embed → Qdrant |
| 2026-03-16 | 3-4 AI Service + MCP | ✅ | AI Service microservice with tools-based architecture |
| 2026-03-17 | 3-5 Agents | ✅ | Multi-Agent: Learning Advisor (orchestrator) + Skill Gap Analyst + Career Advisor + Learning Path Designer. Handoff-based routing verified. |
| 2026-03-16 | 3-6 RAG pipeline | ✅ | Hybrid search (BM25 sparse + dense + RRF fusion) + level normalization |
| 2026-03-16 | 3-7 Explore chat | ✅ | Chat API connected to Learning Advisor Agent |
| | **Phase 4: Measurable** | | **"Make it right"** |
| 2026-03-17 | 4-1 Observability | ✅ | LangFuse v4 (traces + scores + cost tracking + prompt versioning). Phoenix evaluated and removed (no unique value over LangFuse). |
| | 4-2 Full data ingestion | ⬜ | 6,645 courses embedding + indexing (currently 1,000 sample) |
| 2026-03-16 | 4-3 Ground truth dataset | ✅ | 20 test cases: keyword/semantic + filter-only + mixed. Stratified from indexed data. |
| 2026-03-17 | 4-4 Offline evaluation | ✅ | DeepEval (Answer Relevancy, Faithfulness, Actionability) + IR metrics (Hit Rate, Precision@5, Recall@5) + Filter metrics + Agent Routing Accuracy. 38 GT cases (20 search + 18 multi-agent). 65+ pytest tests. |
| 2026-03-17 | 4-5 Online evaluation | ✅ | Latency p50/p95/p99 captured. LangFuse score graph fixed. LLM-as-a-Judge available via LangFuse GUI. |
| | 4-6 Accuracy improvement | ⬜ | Reranker, prompt tuning, embedding refinement |
| | 4-7 Performance optimization | ⬜ | Parallel ingestion, connection pooling |
| | **Phase 5: Resilient** | | **"Make it safe"** |
| | 5-1 Local fallback | ⬜ | MiniLM-L6-v2 embedding fallback |
| 2026-03-17 | 5-2 Graceful degradation | ✅ | Qdrant down → MongoDB text search fallback |
| 2026-03-17 | 5-3 Error handling | 🚧 | Retry + backoff in embedding/web_search, [ERROR] convention. Circuit breaker pending. |
| 2026-03-17 | 5-4 Guardrails | ✅ | Input: sanitize + injection detection (9 patterns) + topic relevance + PII redaction. Output: PII + system info + credential masking. |
| 2026-03-17 | 5-5 Test suite | ✅ | 65+ tests (10 files): routing, direct handling, e2e handoff, web search, career, skill gap, learning path, guardrails (22), quality metrics (15). |
| | 5-6 CI/CD thresholds | ⬜ | Quality gates: accuracy, latency, guardrail pass rate |
| 2026-03-17 | 5-7 Safety evaluation | ✅ | 22 guardrail tests: off-topic (5), injection (5), on-topic (5), PII (4), output sanitize (3). |
| | **Phase 6: Deliverable** | | **"Ship it"** |
| | 6-1 Architecture diagram | ⬜ | JPEG/PDF for submission |
| | 6-2 Stakeholder PPT | ⬜ | EDA, Design, Decisions, Evaluation |
| | 6-3 Final documentation | ⬜ | README + docs/ finalization |
| | 6-4 Panel presentation | ⬜ | 8 min demo + 2 min Q&A |
