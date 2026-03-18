# Architecture — Intelligent University Course Finder

## Tech Stack

| Component | Choice | Notes |
|-----------|--------|-------|
| LLM Orchestration | OpenAI Agents SDK | Agent SDK-based architecture |
| Evaluation | DeepEval | Required by Requirement 2 |
| Observability | LangFuse | Tracing, cost tracking, prompt versioning |
| Backend | Python + FastAPI | API layer (microservices: Gateway, Course Service, User Service) |
| Frontend | React + JavaScript + Vite + MUI | Udemy-style UI, feature-based directory structure |
| Dataset | Coursera Course Dataset | CSV/JSON, 6,645 courses |
| Document DB | MongoDB | CRUD for courses, users, chat history |
| Vector DB | Qdrant | Semantic search & RAG |
| Embedding (Primary) | OpenAI text-embedding-3-small | 1536 dimensions, $0.02/1M tokens |
| Embedding (Fallback) | HuggingFace all-MiniLM-L6-v2 | 384 dimensions, free, local inference |
| Design System | Material UI (MUI) | Consistent component library |

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Compose                        │
│                                                          │
│  ┌──────────┐    ┌──────────┐                           │
│  │ Frontend │───▶│ Gateway  │ :8000                     │
│  │ (React)  │    │ (FastAPI)│                            │
│  │ :5173    │    └────┬─────┘                            │
│  └──────────┘         │                                  │
│                  ┌────┴────┐                              │
│                  │         │                              │
│           ┌──────▼──┐ ┌───▼────────┐                    │
│           │ Course  │ │   User     │                     │
│           │ Service │ │  Service   │                     │
│           │ :8001   │ │  :8002     │                     │
│           └────┬────┘ └─────┬──────┘                    │
│                │            │                            │
│           ┌────▼────────────▼──┐   ┌──────────┐        │
│           │     MongoDB        │   │  Qdrant  │        │
│           │     :27017         │   │  :6333   │        │
│           └────────────────────┘   └──────────┘        │
│                                                          │
│  ┌──────────────┐                                       │
│  │  AI Service  │ ── OpenAI Agents SDK                  │
│  │  :8003       │ ── RAG Pipeline                       │
│  └──────────────┘ ── 4 LLMs + 5 Tools                    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Service Responsibilities

| Service | Port | Responsibility |
|---------|------|----------------|
| **Frontend** | 5173 | React + Vite + MUI. Udemy-style UI. Vite proxy forwards `/api` → Gateway |
| **Gateway** | 8000 | API routing, CORS, JWT validation pass-through |
| **Course Service** | 8001 | Course CRUD, search, filter options. MongoDB `courses` collection |
| **User Service** | 8002 | Auth (register/login), profile CRUD. MongoDB `users` collection |
| **MongoDB** | 27017 | Document store for courses and users |
| **Qdrant** | 6333 | Vector store for course embeddings |
| **AI Service** | 8003 | LLM orchestration, RAG pipeline, 4 LLMs + 5 Tools |

## Communication Flow

```
Browser → Frontend (:5173)
  → Vite Proxy (/api → gateway:8000)
    → Gateway (/api/v1/courses → course-service:8001)
    → Gateway (/api/v1/auth, /api/v1/users → user-service:8002)
    → Gateway (/api/v1/chat, /api/v1/recommend → ai-service:8003)
```

## Data Flow

1. Course data: CSV → `ingest_courses.py` → MongoDB → Course Service API → Frontend
2. User data: Register → MongoDB `users` collection → JWT → Frontend localStorage
3. Embedding: MongoDB courses → OpenAI text-embedding-3-small → Qdrant
4. Semantic search: User query → Embedding → Qdrant vector search → Course results
5. RAG: Query + Retrieved courses → LLM → Contextual response
6. Agent pipeline: User intent → Agent orchestration → Structured recommendation

## Architecture Decisions

### AD-001: Microservices over Monolith
- **Decision**: Separate services for courses, users, and AI
- **Rationale**: Independent scaling, clear boundaries, AI Service added without touching existing services

### AD-002: Gateway Pattern
- **Decision**: Single Gateway service proxies all requests
- **Rationale**: Single CORS config, centralized routing, future auth middleware

### AD-003: MongoDB + Qdrant Dual DB
- **Decision**: Keep MongoDB for CRUD, add Qdrant for vector search
- **Rationale**: Zero migration cost, best RAG features (hybrid search, multi-vector, re-ranking), Docker-native

### AD-004: Feature-based Frontend Structure
- **Decision**: `features/{name}/` directory structure
- **Rationale**: Feature addition = new folder + 1 route. Minimizes cross-feature coupling

---

# Agent Architecture

## Diagrams

| Diagram | File | Description |
|---------|------|-------------|
| System Overview | [diagrams/system-overview.drawio](diagrams/system-overview.drawio) | Full system map with all components |
| Agent Overview | [diagrams/agent-overview.drawio](diagrams/agent-overview.drawio) | Requirements → Implementation mapping |
| RAG Indexing | [diagrams/rag-indexing.drawio](diagrams/rag-indexing.drawio) | CSV → MongoDB → Qdrant pipeline |
| RAG Query | [diagrams/rag-query.drawio](diagrams/rag-query.drawio) | Query-time retrieval pipeline |
| Container View | [diagrams/system-containers.drawio](diagrams/system-containers.drawio) | Docker / local host boundary |

## Requirements → Implementation Mapping

The requirements define 5 agents. The implementation uses **4 LLMs + 5 shared tools**:

| Requirements Agent | Implementation | Form | Rationale |
|---|---|---|---|
| Learning Advisor Agent | **Learning Advisor** | LLM (Router) | Routes to sub-agents via handoff |
| Course Retrieval Agent | **retrieve_courses + get_course_details** | Tool | Search execution, not reasoning → no LLM needed |
| Skill Gap Analysis Agent | **Skill Gap Analyst** | LLM (Sub-Agent) | Requires reasoning about user skills vs goals |
| Learning Path Planning Agent | **Learning Path Designer** | LLM (Sub-Agent) | Requires reasoning about course ordering |
| Career Alignment Agent | **Career Advisor** | LLM (Sub-Agent) | Requires reasoning about career paths |

**Key design decision**: Course Retrieval was converted from Agent to Tool because:
- Course retrieval is "search execution" not "reasoning" — no LLM judgment needed
- All 4 LLMs share the same tools, avoiding unnecessary agent handoff overhead
- Hybrid Search (BM25 + Dense + RRF) handles the retrieval logic entirely

## Pipeline Overview

```
User Message
   │
   ▼
┌──────────────────────────────────────────────────────┐
│  Input Guardrails                                    │
│  Injection detection · Topic relevance · PII redaction│
└──────────────────────────────────────────────────────┘
   │
   ▼
┌──────────────────────────────────────────────────────┐
│  OpenAI Agents SDK (Runner.run)                      │
│                                                      │
│  Learning Advisor (Router, gpt-4o)                   │
│     │ handoff                                        │
│     ├── Skill Gap Analyst (gpt-4o)                   │
│     ├── Career Advisor (gpt-4o)                      │
│     └── Learning Path Designer (gpt-4o, temp=0.3)    │
│                                                      │
│  @function_tool (shared by all LLMs):                │
│     retrieve_courses · get_course_details            │
│     get_user_profile · update_user_profile           │
│     web_search                                       │
└──────────────────────────────────────────────────────┘
   │
   ▼
┌──────────────────────────────────────────────────────┐
│  Output Guardrails                                   │
│  PII redaction · Stack trace removal                 │
└──────────────────────────────────────────────────────┘
   │
   ▼
  Response to User
```

## How It Works

1. **User sends a message** via chat UI
2. **Input Guardrails** check for injection, off-topic, PII
3. **Learning Advisor** (Router) receives the message and decides:
   - Answer directly (simple questions)
   - Handoff to a sub-agent (specialized tasks)
4. **Sub-agent** executes using its assigned tools, then returns control to Learning Advisor
5. **Learning Advisor** synthesizes the final response
6. **Output Guardrails** redact any PII or stack traces
7. **Response** returned to user

The LLM itself handles intent classification, entity extraction, and query construction
— no separate classifier/decomposer pipeline. This is simpler and leverages the LLM's
native ability to understand user intent from conversation context.

---

## LLM × Tool Matrix

| Tool | Learning Advisor | Skill Gap Analyst | Career Advisor | Learning Path Designer |
|------|:----------------:|:-----------------:|:--------------:|:---------------------:|
| `retrieve_courses` | ✅ | ✅ | ✅ | ✅ |
| `get_course_details` | — | — | — | ✅ |
| `get_user_profile` | ✅ | ✅ | ✅ | ✅ |
| `update_user_profile` | ✅ | — | — | — |
| `web_search` | ✅ | ✅ | ✅ | — |

## LLM Descriptions

- **Learning Advisor** (Router): Orchestrator. Handles general queries directly, delegates specialized tasks via handoff. Has all tools except `get_course_details`.
- **Skill Gap Analyst** (Sub-Agent): Compares user's current skills against target role requirements. Identifies gaps and recommends courses to fill them.
- **Learning Path Designer** (Sub-Agent): Designs structured multi-step learning paths with prerequisite ordering. Uses `get_course_details` for detailed course info. `temp=0.3` for more deterministic outputs.
- **Career Advisor** (Sub-Agent): Provides career path guidance, researches job market requirements, recommends courses aligned with career goals.

---

## Retrieval Pipeline (inside retrieve_courses)

See [RAG Query diagram](diagrams/rag-query.drawio) for the visual flow.

1. **Extract Filter + Query**: LLM extracts search text + structured filters (level, min_rating, organization, skill)
2. **Embedding**: OpenAI text-embedding-3-small (1,536 dims)
3. **Hybrid Search** (single Qdrant API call):
   - Prefetch: Dense (HNSW cosine, weight 1.5, limit 30)
   - Prefetch: BM25 (Qdrant built-in tokenizer + IDF, weight 1.2, limit 30)
   - Payload Filter applied to both prefetches
   - RRF Fusion: weights [BM25=1.2, Dense=1.5]
4. **Cross-Encoder Rerank** (optional): all-MiniLM-L6-v2, local CPU — see [Reranker Analysis](../data-flow.md#reranker-analysis)
5. **Fallback chain**: Hybrid → BM25-only → MongoDB text search

## Graceful Degradation

| Failure | Fallback | Mechanism |
|---------|----------|-----------|
| OpenAI embedding timeout | BM25-only search (Qdrant) | Circuit breaker (3 failures → 30s recovery) |
| Qdrant unavailable | MongoDB $text search | Circuit breaker + exception handler |
| OpenAI LLM timeout | Error message to user | httpx timeout (180s for chat) |
