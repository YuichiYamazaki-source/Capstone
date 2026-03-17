# Architecture — Intelligent University Course Finder

**Tags**: #type/reference #domain/system-design #domain/orchestration #domain/rag #concept/microservices

## Status
- Phase 2: ✅ Complete (Frontend + Backend + MongoDB)
- Phase 3: 🚧 Starting (Qdrant + RAG + AI Agents)

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
│           │     MongoDB        │   │  Qdrant  │ (P3)   │
│           │     :27017         │   │  :6333   │        │
│           └────────────────────┘   └──────────┘        │
│                                                          │
│  Phase 3 additions:                                      │
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
| **Qdrant** | 6333 | Vector store for course embeddings (Phase 3) |
| **AI Service** | 8003 | LLM orchestration, RAG pipeline, 5 Agents (Phase 3) |

## Communication Flow

```
Browser → Frontend (:5173)
  → Vite Proxy (/api → gateway:8000)
    → Gateway (/api/v1/courses → course-service:8001)
    → Gateway (/api/v1/auth, /api/v1/users → user-service:8002)
    → Gateway (/api/v1/chat, /api/v1/recommend → ai-service:8003) [Phase 3]
```

## Data Flow

### Current (Phase 2)
1. Course data: JSON seed → MongoDB `courses` collection → Course Service API → Frontend
2. User data: Register → MongoDB `users` collection → JWT → Frontend localStorage

### Phase 3 (planned)
1. Embedding generation: MongoDB courses → OpenAI text-embedding-3-small → Qdrant
2. Semantic search: User query → Embedding → Qdrant vector search → Course results
3. RAG: Query + Retrieved courses → LLM → Contextual response
4. Agent pipeline: User intent → Agent orchestration → Structured recommendation

## Architecture Decisions

### AD-001: Microservices over Monolith
- **Decision**: Separate services for courses, users, and AI
- **Rationale**: Independent scaling, clear boundaries, easier Phase 3 integration (add AI Service without touching existing services)

### AD-002: Gateway Pattern
- **Decision**: Single Gateway service proxies all requests
- **Rationale**: Single CORS config, centralized routing, future auth middleware

### AD-003: MongoDB + Qdrant Dual DB
- **Decision**: Keep MongoDB for CRUD, add Qdrant for vector search
- **Rationale**: See `Tech Stack.md` for full rationale. Zero migration cost, best RAG features, Docker-native

### AD-004: Feature-based Frontend Structure
- **Decision**: `features/{name}/` directory structure
- **Rationale**: Feature addition = new folder + 1 route. Feature removal = delete folder + 1 route. Minimizes cross-feature coupling

### AD-005: Client-side Recommendation Scoring (Phase 2)
- **Decision**: `scoreMatch()` function runs in browser
- **Rationale**: Phase 2 stub. Will be replaced by AI Service in Phase 3. Avoids premature backend complexity
