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
| Observability | LangFuse, Arize Phoenix |

See `docs/decisions/tech-stack.md` for selection rationale.

---

## Requirements Checklist

### Requirement 1 (Basic)

- [x] Basic RAG for course discovery
- [x] Intent-based semantic search
- [ ] Simple recommendation agent
- [x] Skill gap identification
- [x] Difficulty level filtering
- [ ] Learning objective validation guardrails
- [ ] Basic course sequencing
- [x] Metadata filtering (organization, rating, difficulty)
- [x] Expose core functionality through API endpoint

### Requirement 2 (Advanced)

- [ ] DeepEval for recommendation relevance and learning outcomes
- [ ] Rerank using learner preference models and success rate data
- [ ] LLM-as-judge for course quality and prerequisite validation
- [ ] Token optimization for personalized learning path generation
- [ ] Performance testing: real-time recommendations at scale
- [ ] Content appropriateness and prerequisite guardrails
- [x] Build a simple front-end interface

### Hybrid Course Retrieval

- [ ] Hybrid search combining vector embeddings and keyword retrieval
- [x] Dynamic filtering by difficulty level, rating, organization, and skill category
- [ ] Cross-encoder reranking for improved course recommendation quality

### Learning Path Intelligence

- [x] Automated generation of structured multi-course learning paths
- [ ] Identification of prerequisite courses for advanced topics
- [ ] Skill graph mapping between courses and learning outcomes

### Multi-Agent Learning Recommendation System

- [ ] Course Retrieval Agent - retrieves relevant courses from the catalog
- [ ] Skill Gap Analysis Agent - identifies missing prerequisite skills
- [ ] Learning Path Planning Agent - generates structured course sequences
- [ ] Career Alignment Agent - maps courses to potential career tracks
- [ ] Learning Advisor Agent - summarizes recommendations for students

### Additional Learning Intelligence

- [ ] Learning analytics integration showing popular courses and completion trends
- [x] Personalized course recommendations based on learner preferences
- [ ] Adaptive difficulty adjustment based on learner progress
- [ ] Agent handoff between different learning domains and specializations
- [ ] Agent-to-Agent (A2A) communication for collaborative filtering and peer recommendations

### Key Capabilities

- [ ] Multimodal query understanding (text, voice, uploaded descriptions)
- [x] Semantic course retrieval (conceptual matching, not keyword-only)
- [x] Relevance assistance (explain why courses are recommended)
- [ ] Prerequisite awareness
- [x] Skill gap identification with foundational course suggestions
- [x] Learning path recommendations (introductory to advanced)
- [x] Career-oriented course exploration

### Deliverables

- [ ] Architecture diagram (JPEG or PDF)
- [ ] Design document (embedding model, chunking strategy, hybrid retrieval, agent orchestration, learning path generation)
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
