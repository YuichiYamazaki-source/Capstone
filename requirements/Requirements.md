# Requirements — Intelligent University Course Finder

**Tags**: #type/reference #domain/rag #domain/agent #domain/evaluation #domain/llmops

## Overview
AI-powered multimodal course discovery and recommendation system that helps students explore university course offerings using natural and flexible inputs.

## Key Capabilities
- Multimodal Query Understanding (text, voice, uploaded docs)
- Semantic Course Retrieval
- Relevance Assistance
- Prerequisite Awareness
- Skill Gap Identification
- Learning Path Recommendations
- Career-Oriented Course Exploration

## Requirement 1 (Basic)
- Basic RAG for course discovery
- Intent-based semantic search
- Simple recommendation agent
- Skill gap identification
- Difficulty level filtering
- Learning objective validation guardrails
- Basic course sequencing
- Metadata filtering (organization, rating, difficulty)
- **Expose via API endpoint**

## Requirement 2 (Advanced)
- DeepEval for recommendation relevance and learning outcomes
- Rerank using learner preference models and success rate data
- LLM-as-judge for course quality and prerequisite validation
- Token optimization for personalized learning path generation
- Performance testing: real-time recommendations at scale
- Content appropriateness and prerequisite guardrails
- **Simple front-end interface**

### Hybrid Course Retrieval
- Hybrid search combining vector embeddings and keyword retrieval
- Dynamic filtering by difficulty level, rating, organization, skill category
- Cross-encoder reranking

### Learning Path Intelligence
- Automated generation of structured multi-course learning paths
- Identification of prerequisite courses
- Skill graph mapping between courses and learning outcomes

### Multi-Agent Learning Recommendation System
- Course Retrieval Agent
- Skill Gap Analysis Agent
- Learning Path Planning Agent
- Career Alignment Agent
- Learning Advisor Agent

### Additional Learning Intelligence
- Learning analytics (popular courses, completion trends)
- Personalized recommendations based on learner preferences
- Adaptive difficulty adjustment
- Agent handoff between learning domains
- Agent-to-Agent (A2A) communication

## Deliverables
1. Architecture Diagram (JPEG/PDF)
2. Design Document (trade-offs, decisions)
3. Full Executable Code (Microservice) + README
4. Panel Presentation (10 min: 8 demo + 2 Q&A)

## Dataset
- **Coursera Course Dataset** (CSV/JSON)
- Fields: course_name, description, skills, difficulty_level, rating, organization
- Sources: Kaggle, HuggingFace, GitHub

---

## Evaluation Checklist (from Checklist.pdf)

### 1. Filesystem & Documentation
- [ ] Clear folder structure: `/requirements`, `/docs/architecture`, `/docs/data-flow`, `/src` (services/), `/tests`, `README.md`
- [ ] Stakeholder PPT: Briefing deck summarizing EDA, Design, Decisions, and Evaluation
- [ ] README consistency: Code and structure actually follow the README

### 2. Architecture & Design Integrity
- [ ] Architecture vs Data Flow distinction: Architecture = components/services/caches. Data Flow = logical movement (retrieval sequence). Do not confuse the two.
- [ ] Production Scale Deployment:
  - [ ] Architecture discusses API Gateways, Load Balancers, and Kubernetes (K8s)
  - [ ] Clear distinction between PoC vs Production
- [ ] Observability & MLOps: Architecture explicitly includes monitoring, logging, and ML lifecycle layers
- [ ] Design Decisions:
  - [ ] ADRs with Pros/Cons for major choices (e.g., DECISIONS.md)
  - [ ] Trade-offs explicitly highlighted (e.g., Accuracy vs Performance)
  - [ ] Decoupling: Can swap Vector DB without rewriting core API

### 3. Implementation & Code Quality
- [ ] Production Grade Code:
  - [ ] Zero `print()` statements — 100% structured logging (JSON preferred)
  - [ ] Clean code: No hardcoded secrets, no monolithic "God" files
  - [ ] Microservices reflected in code boundaries/packages
  - [ ] Connection pooling for DB and downstream services
  - [ ] Input validation via Pydantic schemas
- [ ] Containerization: Working Dockerfile + docker-compose.yml for one-command startup
- [ ] Resource Management:
  - [ ] Memory-efficient processing (streaming/generators)
  - [ ] Cold start optimization: Models and indices loaded at startup, not on first request
- [ ] Error handling: Missing files, empty data, API timeouts handled gracefully

### 4. Testing & Validation (Accuracy)
- [ ] API Testing: Automated tests for both Loading (Ingestion) and Retrieving (Search)
- [ ] Performance Measurement: Monitoring latency (p99) and throughput for retrieval
- [ ] Accuracy Validation:
  - [ ] Defined methodology (LLM-as-Judge or custom rubrics)
  - [ ] Ground Truth Dataset provided and documented
  - [ ] Metrics Summary: Latency + Accuracy results documented
- [ ] ML Resiliency:
  - [ ] Local Fallback: Working code for local model (Flan-T5/Transformers) if OpenAI times out
  - [ ] Graceful Degradation: System returns keyword-only results if vector indexing fails

### 5. SME Evaluation Rubric

| Dimension | "No" | "Borderline" | "Yes" |
|-----------|------|-------------|-------|
| Correctness | Bugs in core flow | Functional but brittle | Robust, handles edge cases |
| Architecture | Monolithic / spaghetti | Layered but tightly coupled | Modular microservices, clean separation |
| Design Decisions | Ad-hoc, no reasoning | Popular tech, can't explain trade-offs | ADRs with cost/latency/complexity justification |
| Performance | High-latency LLM for every task | Basic in-memory caching | Optimized pipelines, SLMs, parallel ingestion |
| Testing | Manual only | Basic unit tests | Unit + Integration + Load tests |
| Evaluation | None | Script-based logs | LLM-as-Judge or IR metrics (NDCG/MAP) |
| Scalability | Global state, no pooling | Vertical only | Cloud-ready, stateless, connection pooled |
| Reliability | No error handling | Basic try/except | Retry logic, local fallbacks, circuit breakers |
| Maintainability | Hardcoded keys | Clean but undocumented | Self-documenting, Dockerized |
| Observation | print() statements | Basic log output | Structured logs + health checks |

### 6. Final Benchmarking (SME "Yes" Grade)
- [ ] Core Flow: Robust, handles sad path edge cases
- [ ] Architecture: Clear DB/AI/API layer separation
- [ ] Design Decisions: ADRs with cost/latency/complexity justification
- [ ] Performance: Parallelized ingestion, SLM for high-frequency tasks
- [ ] Testing: Unit + Integration + Load test suite
- [ ] Evaluation: Automated rubrics (LLM-as-Judge) or IR metrics
- [ ] Scalability: Stateless, horizontally scalable, connection pooled
- [ ] Reliability: Retry logic, local model fallbacks, circuit breakers
- [ ] Maintainability: Self-documenting, logically grouped, fully Dockerized
- [ ] Observation: Production-ready structured logs + health check endpoints
