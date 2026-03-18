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
│  └──────────────┘ ── 5 Agents                           │
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
| **AI Service** | 8003 | LLM orchestration, RAG pipeline, 5 Agents |

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
| System Overview | [diagrams/system-overview.drawio](diagrams/system-overview.drawio) | Layered pipeline from input to response |
| Query Processing Flow | [diagrams/query-processing-flow.drawio](diagrams/query-processing-flow.drawio) | Step-by-step complex query handling |
| Version Evolution | [diagrams/version-evolution.drawio](diagrams/version-evolution.drawio) | Component decisions + version mapping |

## Pipeline Overview

```
User Input (text)
   │
   ▼
┌──────────────────────────────────────────────────────┐
│  Query Understanding Layer                           │
│  ┌─────────┐  ┌──────────┐  ┌────────┐  ┌────────┐ │
│  │Normalize│→ │ Entity   │→ │Intent  │→ │Decompose│ │
│  │(rules)  │  │Extract   │  │Classify│  │(LLM)   │ │
│  │<5ms     │  │(LLM)     │  │(LLM)   │  │~300ms  │ │
│  │$0       │  │~200ms    │  │~100ms  │  │skip if │ │
│  └─────────┘  └──────────┘  └────────┘  │simple  │ │
│                                          └────────┘ │
└──────────────────────────────────────────────────────┘
   │
   ▼
┌──────────────────────────────────────────────────────┐
│  Orchestration Layer                                 │
│  Execution Planner (DAG) → Agent Dispatcher          │
│  → Result Merger                                     │
└──────────────────────────────────────────────────────┘
   │
   ▼
┌──────────────────────────────────────────────────────┐
│  Agent Layer (OpenAI Agents SDK)                     │
│  ┌─────────┐ ┌─────────┐ ┌──────────┐ ┌──────────┐│
│  │Retrieval│ │Skill Gap│ │Learn Path│ │Career    ││
│  │Agent    │ │Agent    │ │Agent     │ │Alignment ││
│  └─────────┘ └─────────┘ └──────────┘ └──────────┘│
│                    ↓ all outputs merge ↓            │
│              ┌──────────────────────┐               │
│              │ Learning Advisor     │               │
│              │ (final synthesizer)  │               │
│              └──────────────────────┘               │
└──────────────────────────────────────────────────────┘
   │                         │
   ▼                         ▼
┌─────────────────┐  ┌───────────────────────────────┐
│ Tool Layer      │  │ Response Layer                 │
│ search_semantic │  │ Context Assembly → LLM Gen     │
│ search_keyword  │  │ → Guardrails → Output          │
│ filter_courses  │  └───────────────────────────────┘
│ get_course_detail│
│ get_user_profile│
│ rerank          │
└─────────────────┘
   │
   ▼
┌──────────────────────────────────────────────────────┐
│ Retrieval Layer                                      │
│ Embed → Vector Search (Qdrant) ─┐                   │
│                                  ├→ RRF Fusion       │
│ Keyword Search (MongoDB) ───────┘   → Rerank        │
└──────────────────────────────────────────────────────┘
   │
   ▼
┌──────────────────────────────────────────────────────┐
│ Data Layer                                           │
│ Qdrant │ MongoDB │ OpenAI API                        │
└──────────────────────────────────────────────────────┘
```

## Query Understanding Layer

### Step 1: Input Normalizer (rule-based)
Whitespace/encoding normalization, language detection (en/ja). Latency <5ms, cost $0.

### Step 2: Entity Extractor (LLM structured output)
Extracts structured fields from free-form text using GPT-4o-mini with JSON mode:

```json
{
  "skills_mentioned": ["Transformer", "AI-RAN", "LLM"],
  "career_goal": "AI Engineer at Google",
  "experience": "AI-RAN research (university)",
  "desired_focus": "LLM research and development",
  "constraints": { "timeline": "6 months" },
  "difficulty_pref": null,
  "ambiguity_score": 0.2
}
```

Latency ~200ms, cost ~$0.0003/req.

### Step 3: Intent Classifier (multi-label)
Outputs confidence scores for all intents simultaneously (not mutually exclusive):

| Intent | Threshold | Triggers Agent |
|--------|-----------|----------------|
| `course_search` | ≥ 0.5 | Course Retrieval |
| `skill_gap_analysis` | ≥ 0.5 | Skill Gap Analysis |
| `learning_path` | ≥ 0.5 | Learning Path Planning |
| `career_guidance` | ≥ 0.5 | Career Alignment |
| `clarification_needed` | ≥ 0.7 | → Ask follow-up question |

Latency ~100ms (LLM), cost ~$0.0002.

### Step 4: Query Decomposer (LLM, conditional)
Activated only when multiple intents detected or ambiguity is moderate (0.3-0.7).
**Skipped** for simple queries (single intent ≥ 0.5, ambiguity < 0.3) — saves ~300ms for ~60-70% of queries.

---

## Orchestration Layer

### Execution Planner
Converts sub-tasks into a DAG with dependency tracking. **Rule-based**, not LLM.

```
Complex query example:
  CAA ──┐
        ├──→ RA ──→ LPPA ──→ LA
  SGA ──┘

  CAA ∥ SGA (parallel)  →  RA  →  LPPA  →  LA (always last)
```

### Agent Dispatcher
Executes the DAG, passing context between agents. Parallel execution via asyncio.

### Result Merger
Aggregates outputs from all agents, deduplicates courses, formats for the Learning Advisor.

---

## Agent Layer

### Agent × Tool Matrix

| Tool | Retrieval | Skill Gap | Learning Path | Career | Advisor |
|------|:---------:|:---------:|:-------------:|:------:|:-------:|
| `search_semantic` | ✅ | ✅ | ✅ | ✅ | — |
| `search_keyword` | ✅ | — | — | — | — |
| `filter_courses` | ✅ | — | — | — | — |
| `get_course_detail` | ✅ | — | ✅ | — | — |
| `get_user_profile` | — | ✅ | — | ✅ | — |
| `rerank` | ✅ | — | — | — | — |

### Agent Descriptions

- **Course Retrieval Agent**: Semantic + keyword search, filtering, hybrid score fusion.
- **Skill Gap Analysis Agent**: Compares user profile skills against required skills for a goal. Outputs missing skill list.
- **Learning Path Planning Agent**: Orders courses by prerequisite dependencies, difficulty progression, and skill coverage.
- **Career Alignment Agent**: Maps career goals to required skill sets using domain knowledge.
- **Learning Advisor Agent**: No tools. Synthesizes merged outputs into final natural language response.

---

## Component Specs

| Component | Implementation | Latency | Cost |
|-----------|---------------|---------|------|
| Input Normalizer | Rule-based | <5ms | $0 |
| Entity Extractor | GPT-4o-mini | ~200ms | ~$0.0003 |
| Intent Classifier | GPT-4o-mini | ~100ms | ~$0.0002 |
| Query Decomposer | GPT-4o-mini (skip if simple) | ~300ms | ~$0.0005 |
| Retrieval | Hybrid (Vector+Keyword) + RRF + Rerank | ~100ms | ~$0.00002 |
| Agent Reasoning | GPT-4o-mini | ~500-800ms | ~$0.005/agent |
| Response Gen | GPT-4o-mini | ~400ms | ~$0.003 |
| Guardrails | Rule-based | <5ms | $0 |

## Per-Query Cost & Latency Estimates

| Query Type | Example | Latency | Cost | Agents Used |
|------------|---------|:-------:|:----:|:-----------:|
| **Simple** | "machine learning courses" | ~1.0s | ~$0.004 | RA → LA |
| **Moderate** | "I want to become a data scientist" | ~2.0s | ~$0.012 | SGA → RA → LPPA → LA |
| **Complex** | "Google AI Engineer, 6 months, LLM R&D..." | ~2.9s | ~$0.020 | CAA ∥ SGA → RA → LPPA → LA |
| **Ambiguous** | "何から学習したらいいかわからない" | ~0.4s | ~$0.001 | None (clarifying Q) |
