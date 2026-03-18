# Intelligent University Course Finder

AI-powered course discovery and recommendation system that helps learners explore 6,645 Coursera courses using natural language chat, skill gap analysis, career alignment, and personalized learning path generation.

---

## Quick Start

```bash
# 1. Start all services
docker compose up -d --build

# 2. Open browser
# Frontend: http://localhost:5173
# Gateway API: http://localhost:8000
```

For full setup including data ingestion and embeddings, see [Detailed Setup](#detailed-setup) below.

---

## Detailed Setup

### Prerequisites

- Docker Desktop (Docker Compose v2)
- Python 3.11+ with miniconda (for data scripts)
- OpenAI API key
- LangFuse account (optional, for observability)

### 1. Environment Variables

Create `local/.env`:

```dotenv
OPENAI_API_KEY=sk-...

# LangFuse (optional)
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_BASE_URL=https://us.cloud.langfuse.com
```

| Variable | Required | Description |
|----------|:--------:|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key for LLM + embedding |
| `LANGFUSE_SECRET_KEY` | No | LangFuse cloud secret key |
| `LANGFUSE_PUBLIC_KEY` | No | LangFuse cloud public key |
| `LANGFUSE_BASE_URL` | No | LangFuse endpoint URL |

### 2. Start Services

```bash
docker compose up -d --build
```

This starts: Frontend (:5173), Gateway (:8000), Course Service (:8001), User Service (:8002), AI Service (:8003), MongoDB (:27017), Qdrant (:6333).

### 3. Ingest Course Data

```bash
# Full dataset (6,645 courses)
/c/Users/yuila/miniconda3/python.exe scripts/ingest_courses.py --all

# Or sampled subset (default 100)
/c/Users/yuila/miniconda3/python.exe scripts/ingest_courses.py
```

### 4. Generate Embeddings

```bash
/c/Users/yuila/miniconda3/python.exe scripts/generate_embeddings.py
```

This generates dense vectors (OpenAI text-embedding-3-small, 1,536 dims) and BM25 sparse vectors for all courses in Qdrant.

### 5. Seed Test Users (optional)

```bash
/c/Users/yuila/miniconda3/python.exe scripts/seed_users.py
```

### 6. Access the Application

- **Frontend**: http://localhost:5173
- **API docs**: http://localhost:8000/docs (Gateway Swagger)
- **Qdrant dashboard**: http://localhost:6333/dashboard

---

## Directory Structure

```
Capstone/
├── frontend/              # React + Vite + MUI
├── services/
│   ├── gateway/           # API Gateway (FastAPI, :8000)
│   ├── course_service/    # Course CRUD + search (FastAPI, :8001)
│   ├── user_service/      # Auth + profile (FastAPI, :8002)
│   └── ai_service/        # LLM agents + RAG (FastAPI, :8003)
├── scripts/               # Data ingestion, embedding, seeding
├── data/                  # CSV dataset
├── tests/                 # API, integration, load tests
├── evals/                 # DeepEval evaluation suite
├── docs/
│   ├── architecture/      # System design + diagrams
│   ├── api-design.md      # API endpoint reference
│   ├── data-flow.md       # Ingestion + retrieval pipeline
│   ├── evaluation.md      # Eval metrics + results
│   └── decisions.md       # ADRs + tech choices
├── requirements/          # Project requirements + checklist
├── docker-compose.yml
└── README.md
```

---

## Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Frontend | React + JavaScript + Vite + MUI | Feature-based directory structure |
| Backend | Python + FastAPI | 4 microservices (Gateway, Course, User, AI) |
| Document DB | MongoDB 7 | Courses + users collections |
| Vector DB | Qdrant v1.17 | Hybrid search (dense + BM25 + RRF) |
| Embedding | OpenAI text-embedding-3-small | 1,536 dims, $0.02/1M tokens |
| LLM | GPT-4o (via OpenAI Agents SDK) | 4 LLMs + 5 shared tools |
| Evaluation | DeepEval 3.8 | IR metrics + LLM-as-Judge |
| Observability | LangFuse Cloud | Tracing, cost tracking |

See [docs/decisions.md](docs/decisions.md) for selection rationale.

---

## Architecture

See [docs/architecture/system-design.md](docs/architecture/system-design.md) for full documentation.

| Diagram | File | Description |
|---------|------|-------------|
| System Overview | [system-overview.drawio](docs/architecture/diagrams/system-overview.drawio) | Full system map — agents, tools, data stores |
| Agent Overview | [agent-overview.drawio](docs/architecture/diagrams/agent-overview.drawio) | Requirements → implementation mapping |
| RAG Indexing | [rag-indexing.drawio](docs/architecture/diagrams/rag-indexing.drawio) | CSV → MongoDB → Qdrant pipeline |
| RAG Query | [rag-query.drawio](docs/architecture/diagrams/rag-query.drawio) | Query-time hybrid search flow |
| Container View | [system-containers.drawio](docs/architecture/diagrams/system-containers.drawio) | Docker / local host boundary |
| Endpoint Map | [system-endpoints.drawio](docs/architecture/diagrams/system-endpoints.drawio) | Frontend → Gateway → services |
| MongoDB Schema | [data-mongodb.drawio](docs/architecture/diagrams/data-mongodb.drawio) | Collections, schema, access patterns |
| Qdrant Schema | [data-qdrant.drawio](docs/architecture/diagrams/data-qdrant.drawio) | Vector config, payload, query API |

---

## Dataset

- **Source**: Coursera Course Dataset (2024)
- **Size**: 6,645 courses, 14 fields
- **Key fields**: title, description, skills, level, rating, organization
- **Analysis**: See [docs/data-flow.md](docs/data-flow.md) for data quality, biases, and domain distribution
- **Links**:
  - https://www.kaggle.com/datasets/azraimohamad/coursera-course-data
  - https://huggingface.co/datasets/azrai99/coursera-course-dataset

---

<!-- Part 2: FDE Capstone sections (Scope, Eval, Next Actions) to be added -->

## Requirements Checklist

### Requirement 1 (Basic)

- [x] Basic RAG for course discovery
- [x] Intent-based semantic search
- [x] Simple recommendation agent (Learning Advisor with handoff-based routing)
- [x] Skill gap identification (Skill Gap Analyst agent)
- [x] Difficulty level filtering
- [x] Learning objective validation guardrails (topic relevance + prompt injection detection)
- [x] Basic course sequencing (Learning Path Designer agent)
- [x] Metadata filtering (organization, rating, difficulty)
- [x] Expose core functionality through API endpoint

### Requirement 2 (Advanced)

- [x] DeepEval for recommendation relevance and learning outcomes (Answer Relevancy, Faithfulness, Actionability)
- [x] Rerank using learner preference models and success rate data (cross-encoder + profile-based reranking)
- [x] LLM-as-judge for course quality and prerequisite validation (DeepEval + LangFuse GUI)
- [ ] Token optimization for personalized learning path generation
- [x] Performance testing: real-time recommendations at scale (locust load tests)
- [x] Content appropriateness and prerequisite guardrails (input/output sanitization, PII redaction)
- [x] Build a simple front-end interface

### Hybrid Course Retrieval

- [x] Hybrid search combining vector embeddings and keyword retrieval (BM25 sparse + dense + RRF fusion)
- [x] Dynamic filtering by difficulty level, rating, organization, and skill category
- [x] Cross-encoder reranking for improved course recommendation quality (fastembed TextCrossEncoder)

### Learning Path Intelligence

- [x] Automated generation of structured multi-course learning paths
- [x] Identification of prerequisite courses for advanced topics (Learning Path Designer checks prerequisites/modules)
- [ ] Skill graph mapping between courses and learning outcomes

### Multi-Agent Learning Recommendation System

- [x] Course Retrieval Agent - retrieves relevant courses from the catalog (retrieve_courses tool with hybrid search)
- [x] Skill Gap Analysis Agent - identifies missing prerequisite skills (web_search + profile + course matching)
- [x] Learning Path Planning Agent - generates structured course sequences (progressive Beginner→Advanced paths)
- [x] Career Alignment Agent - maps courses to potential career tracks (web_search market data + course mapping)
- [x] Learning Advisor Agent - summarizes recommendations for students (orchestrator with handoff routing)

### Additional Learning Intelligence

- [ ] Learning analytics integration showing popular courses and completion trends
- [x] Personalized course recommendations based on learner preferences
- [ ] Adaptive difficulty adjustment based on learner progress
- [x] Agent handoff between different learning domains and specializations (Learning Advisor → specialist agents)
- [ ] Agent-to-Agent (A2A) communication for collaborative filtering and peer recommendations

### Key Capabilities

- [ ] Multimodal query understanding (text, voice, uploaded descriptions)
- [x] Semantic course retrieval (conceptual matching, not keyword-only)
- [x] Relevance assistance (explain why courses are recommended)
- [x] Prerequisite awareness (Learning Path Designer evaluates prerequisites and modules)
- [x] Skill gap identification with foundational course suggestions
- [x] Learning path recommendations (introductory to advanced)
- [x] Career-oriented course exploration

### Deliverables

- [ ] Architecture diagram (JPEG or PDF)
- [x] Design document (embedding model, chunking strategy, hybrid retrieval, agent orchestration, learning path generation — see docs/)
- [x] Full executable code (microservice) with README (setup, ingestion, example query, example recommendation)
- [ ] Panel presentation (10 minutes: 8 min demo + 2 min Q&A)

### Dataset

- Source: Coursera Course Dataset
- Format: CSV, JSON
- Key fields: course_name, description, skills, difficulty_level, rating, organization
- Links:
  - https://www.kaggle.com/datasets/azraimohamad/coursera-course-data
  - https://huggingface.co/datasets/azrai99/coursera-course-dataset
  - https://github.com/Siddharth1698/Coursera-Course-Dataset
