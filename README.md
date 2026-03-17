# Intelligent University Course Finder

AI-Powered Multimodal Course Discovery System

---

## Quick Start

```bash
# Start all services
docker compose up -d --build

# Frontend: http://localhost:5173
# Gateway API: http://localhost:8000
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React + JavaScript + Vite + MUI |
| Backend | Python + FastAPI (microservices) |
| Document DB | MongoDB |
| Vector DB | Qdrant |
| Embedding | OpenAI text-embedding-3-small |
| LLM Orchestration | OpenAI Agents SDK |
| Evaluation | DeepEval |
| Observability | LangFuse |

See `docs/decisions/tech-stack.md` for selection rationale.

---

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
- [ ] Rerank using learner preference models and success rate data
- [x] LLM-as-judge for course quality and prerequisite validation (DeepEval + LangFuse GUI)
- [ ] Token optimization for personalized learning path generation
- [ ] Performance testing: real-time recommendations at scale
- [x] Content appropriateness and prerequisite guardrails (input/output sanitization, PII redaction)
- [x] Build a simple front-end interface

### Hybrid Course Retrieval

- [x] Hybrid search combining vector embeddings and keyword retrieval (BM25 sparse + dense + RRF fusion)
- [x] Dynamic filtering by difficulty level, rating, organization, and skill category
- [ ] Cross-encoder reranking for improved course recommendation quality

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
