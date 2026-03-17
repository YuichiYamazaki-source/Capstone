# Discussion Log

Open questions and design decisions raised during development.

## Resolved

### 2026-03-16: Document DB Selection — MongoDB vs PostgreSQL
- **Context**: Phase 3 requires Vector DB. Should we also reconsider the document DB?
- **Evaluated**: PostgreSQL (SQL), MongoDB (current NoSQL), DynamoDB, Firestore, CouchDB
- **Decision**: Keep MongoDB
- **Rationale**:
  - Schema flexibility critical for multimodal extension (Nice-to-Have requirement)
  - Pydantic validation at API layer provides equivalent strictness to SQL constraints
  - Zero migration cost (already in use and working)
  - Limited relational needs (user ↔ course) do not justify PostgreSQL migration
  - Cloud migration: Cosmos DB (MongoDB API) is available
- **Full rationale**: See `Tech Stack.md` > Selection Rationale > Document DB

### 2026-03-16: Vector DB Selection — Qdrant
- **Context**: Need vector search for Phase 3 RAG pipeline
- **Evaluated**: pgvector (PostgreSQL), MongoDB Atlas Vector Search, Qdrant, Milvus, ChromaDB
- **Decision**: Qdrant
- **Rationale**:
  - Best RAG feature set (hybrid search, multi-vector, re-ranking)
  - Lightweight Docker container, fully functional locally
  - Atlas rejected (cloud-only, no local Docker support)
  - Milvus rejected (overspec for 6,000 courses)
  - pgvector rejected (lacks advanced RAG features, would require PG migration)
- **Full rationale**: See `Tech Stack.md` > Selection Rationale > Vector DB

### 2026-03-16: Embedding Model Selection
- **Context**: Need embedding model for course description vectors
- **Decision**: OpenAI text-embedding-3-small (primary) + sentence-transformers/all-MiniLM-L6-v2 (failover)
- **Rationale**:
  - Small model sufficient for test/prototype phase (cost: $0.02/1M tokens)
  - Commercial deployment would require cost-performance benchmarking
  - HuggingFace failover for API outage / offline development / cost optimization

### 2026-03-16: Caching Strategy
- **Context**: Should we add Redis for caching?
- **Decision**: Deferred to PoB phase
- **Rationale**: No user load data yet. Premature optimization. Will evaluate when actual usage patterns are known.

## Open

### Web Search result caching
- **Context**: Missing data in CSV (Skills=[], Level, Satisfaction Rate) can be supplemented via Web Search at runtime
- **Options**:
  1. Read-only: Use Web Search results only for the current response, do not update CSV
  2. Write-back: Update CSV with Web Search results to avoid repeated lookups
- **Leaning**: Start with read-only; add caching layer later if needed
- **Status**: Pending
