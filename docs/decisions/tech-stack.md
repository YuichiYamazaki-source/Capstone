# Tech Stack — Intelligent University Course Finder

**Tags**: #type/reference #domain/system-design #concept/microservices

## Confirmed

| Component | Choice | Notes |
|-----------|--------|-------|
| LLM Orchestration | OpenAI Agents SDK | Agent SDK-based architecture |
| Evaluation | DeepEval | Required by Requirement 2 |
| Observability | LangFuse, Arize Phoenix | Tracing & monitoring |
| Backend | Python + FastAPI | API layer (microservices: Gateway, Course Service, User Service) |
| Frontend | React + JavaScript + Vite + MUI | Udemy-style UI, feature-based directory structure |
| Dataset | Coursera Course Dataset | CSV/JSON, 6,645 courses |
| Document DB | MongoDB | CRUD for courses, users, chat history |
| Vector DB | Qdrant | Semantic search & RAG |
| Embedding Model | OpenAI text-embedding-3-small | Primary. 1536 dimensions, $0.02/1M tokens |
| Embedding Fallback | HuggingFace all-MiniLM-L6-v2 | Failover. 384 dimensions, free, local inference |
| Design System | Material UI (MUI) | Consistent component library |

## Not Yet Decided

| Component | Candidates | Notes |
|-----------|-----------|-------|
| Reranker | Cross-encoder (TBD) | Required by Requirement 2 |
| Deployment | Local / Cloud | Cloud account availability unknown |

---

## Selection Rationale

### Document DB: MongoDB

**Evaluated alternatives**: PostgreSQL, DynamoDB, Firestore, CouchDB

| Criteria | MongoDB | PostgreSQL | Others |
|----------|---------|-----------|--------|
| Schema flexibility | Natively schemaless — fields added without migration | ALTER TABLE + Alembic migration | Varies |
| Array data (skills) | Native array type, first-class query support | JSONB or normalized join table | Varies |
| Multimodal extension | New field types (image refs, audio) added without schema change | Requires migration | Varies |
| Validation | Pydantic models at API layer (equivalent strictness to SQL constraints) | DB-level constraints (NOT NULL, CHECK, FK) | Varies |
| Referential integrity | Application-level (acceptable: course data is static, relations are limited) | DB-level FK constraints | Varies |
| Cloud migration | Cosmos DB (MongoDB API), MongoDB Atlas | RDS, Aurora, Cloud SQL | Vendor-specific |
| Migration cost | Zero (already in use) | Full rewrite of data layer | High |

**Decision**: MongoDB. Schema flexibility is critical for multimodal extension and iterative development. Pydantic provides equivalent validation to SQL constraints. The limited relational needs (user ↔ course favorites/history) do not justify the migration cost to PostgreSQL.

### Vector DB: Qdrant

**Evaluated alternatives**: pgvector (PostgreSQL), MongoDB Atlas Vector Search, Milvus, ChromaDB

| Criteria | Qdrant | pgvector | Atlas Vector Search | Milvus | ChromaDB |
|----------|--------|----------|-------------------|--------|----------|
| Hybrid search (sparse+dense) | Native | Not supported | Not supported | Supported | Not supported |
| Multi-vector (named vectors) | Native | Manual table design | Not supported | Supported | Not supported |
| Re-ranking support | Fusion API | Manual | Manual | Supported | Not supported |
| Metadata filtering + vector | Payload filters | SQL WHERE + ORDER BY | Aggregation pipeline | Attribute filtering | Where clause |
| Docker deployment | Single lightweight container | Part of PG | Cloud only (no local) | Heavy (etcd + MinIO + Milvus) | Embedded (no container needed) |
| Local development | Fully functional | Fully functional | Not possible | Functional but heavy | Fully functional |
| Scale fit (6,000 courses) | Optimal | Optimal | Optimal | Overspec (designed for billions) | Optimal but fragile at scale |
| Cloud migration | Qdrant Cloud (any region) | Managed PG services | Already cloud | Zilliz Cloud | Not production-ready |
| RAG feature depth | Excellent | Basic | Basic | Excellent | Basic |

**Decision**: Qdrant. This project prioritizes RAG capabilities (hybrid search, multi-vector, re-ranking). Qdrant provides the deepest RAG feature set while remaining lightweight for Docker-based local development. pgvector was the strongest alternative (single DB simplicity) but lacks advanced RAG features that would require custom implementation. Atlas was rejected due to cloud-only constraint. Milvus was rejected as overspec.

### Embedding Model: OpenAI text-embedding-3-small

**Primary**: OpenAI `text-embedding-3-small`
- 1536 dimensions
- $0.02 per 1M tokens
- High quality for English text
- Consistent with OpenAI Agents SDK ecosystem

**Failover**: HuggingFace `all-MiniLM-L6-v2`
- 384 dimensions
- Free, local inference (no API dependency)
- Well-established, widely benchmarked
- Use case: API outage, cost optimization, offline development

**Note**: For production/commercial use, model selection should be revisited with cost-performance benchmarking across embedding dimensions, latency, and retrieval quality.

### Caching: Deferred

Redis or similar caching layer is not needed at this stage. Will be evaluated during PoB (Proof of Business) phase when actual user load patterns and latency requirements are known.

### Key Trade-offs Documented

1. **Single DB (PG+pgvector) vs Dual DB (MongoDB+Qdrant)**: Chose dual DB. The added operational complexity (data sync between MongoDB and Qdrant) is minimal because course data is near-static (batch import, not frequent writes). The RAG feature advantage of Qdrant outweighs the simplicity benefit of a single DB.

2. **SQL strictness vs NoSQL flexibility**: Chose NoSQL. The project's data model is semi-structured (variable-length skill arrays, potential multimodal fields). Pydantic validation at the API layer provides equivalent data integrity guarantees without the migration overhead of SQL schema changes.

3. **Cloud vs Local**: Chose local Docker-first development. No cloud account constraints, full offline capability. Cloud migration path is clear (Cosmos DB + Qdrant Cloud) when needed.
