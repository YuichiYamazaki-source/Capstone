# Technical Decisions & ADRs

Tech Stack is in `architecture/system-design.md`.

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

### Observability: LangFuse (Phoenix evaluated and removed)

**Evaluated**: Arize Phoenix (local OTEL tracing)

Phoenix was initially adopted alongside LangFuse for local trace visualization. After evaluation:
- Phoenix v13.x removed the `px.Inferences` embedding visualization API (available in v4.x, but requires Python <3.13 and fragile dependency pins)
- All Phoenix capabilities (tracing, latency, cost) were already covered by LangFuse cloud
- Phoenix added Docker container overhead with no unique value

**Decision**: LangFuse only. Covers tracing, cost tracking, prompt versioning (v1 registered), and evaluation dataset management. Embedding space visualization handled by standalone UMAP/t-SNE script (`scripts/visualize_embeddings.py`).

### Caching: Deferred

Redis or similar caching layer is not needed at this stage. Will be evaluated during PoB (Proof of Business) phase when actual user load patterns and latency requirements are known.

### Key Trade-offs Documented

1. **Single DB (PG+pgvector) vs Dual DB (MongoDB+Qdrant)**: Chose dual DB. The added operational complexity (data sync between MongoDB and Qdrant) is minimal because course data is near-static (batch import, not frequent writes). The RAG feature advantage of Qdrant outweighs the simplicity benefit of a single DB.

2. **SQL strictness vs NoSQL flexibility**: Chose NoSQL. The project's data model is semi-structured (variable-length skill arrays, potential multimodal fields). Pydantic validation at the API layer provides equivalent data integrity guarantees without the migration overhead of SQL schema changes.

3. **Cloud vs Local**: Chose local Docker-first development. No cloud account constraints, full offline capability. Cloud migration path is clear (Cosmos DB + Qdrant Cloud) when needed.

---

## ADR: Hybrid Search for Course Retrieval

**Status**: Accepted (2026-03-16)

### Context

v2.0 had 3 separate search tools (keyword / semantic / filter) with LLM-based tool selection. Evaluation revealed the LLM chose the wrong tool 1/3 times (Precision@5: 0.27, latency: 15.4s). The tool selection decision is deterministic by nature — LLM reasoning adds no value here.

### Decision

Replace 3 tools + LLM selection with a single `retrieve_courses` tool: keyword + semantic search in parallel, merged via RRF.

```
Before: Advisor (LLM #1) → Retrieval Agent (LLM #2) → one search method
After:  Advisor (LLM #1) → retrieve_courses (rule-based) → keyword ∥ semantic → RRF merge
```

| Axis | Before | After |
|---|---|---|
| LLM calls | 2 | 1 |
| Tool selection risk | High (LLM error) | None (deterministic) |
| Latency | ~15s | ~7-9s |

### Alternatives Rejected

- **Better prompting** — Tool selection is inherently non-deterministic. Structural problem, not prompt-level.
- **Weighted score normalization** — BM25 and cosine score distributions differ. RRF uses rank position only, avoiding scale mismatch.
- **Cross-encoder reranking** — Deferred. Can be layered on top of RRF later.

---

## ADR: Deferred Features

Features listed in Requirement 2 (Advanced) that were intentionally **not implemented** in the current PoC, with rationale for each decision.

### Multi-Modal Query (voice, uploaded docs)

**Decision**: Defer — Ground truth datasets for voice and document inputs are difficult to prepare. Text-based query evaluation must be established first before extending to other modalities.

### Token Optimization

**Decision**: Not required — The system already uses **gpt-4o-mini** as the default model. Explicit token reduction techniques would add complexity with marginal cost savings. **Local models** (fastembed) for embedding and reranking avoid LLM token costs entirely for those operations.

### Learning Analytics (popular courses, completion trends)

**Decision**: Defer — Requires accumulated user interaction data. In the current PoC stage, there is insufficient user data to derive meaningful trends.

### Adaptive Difficulty Adjustment

**Decision**: Defer — Requires course completion tracking history per user. The current approach uses **profile-based filtering** as a practical alternative.

### Agent-to-Agent (A2A) Communication

**Decision**: Not needed — The multi-agent system runs within a single AI service process using **OpenAI Agents SDK handoff**. A2A protocol becomes relevant when agents are deployed as separate microservices.

### Skill Graph Mapping

**Decision**: Defer — The Coursera dataset does **not include prerequisite fields**. The Learning Path agent already provides **level-ordered sequencing** as a practical alternative.

---

## Open Questions

### Web Search result caching
- **Context**: Missing data in CSV (Skills=[], Level, Satisfaction Rate) can be supplemented via Web Search at runtime
- **Options**:
  1. Read-only: Use Web Search results only for the current response, do not update CSV
  2. Write-back: Update CSV with Web Search results to avoid repeated lookups
- **Leaning**: Start with read-only; add caching layer later if needed
- **Status**: Pending

## Deferred to PoB (Proof of Business)

The following optimizations require real user traffic data and are not meaningful at PoC stage:

- **Compress** — Response/context compression for token reduction
- **Routing** — Intelligent request routing (model selection per query complexity)
- **Query caching** — Repeated query deduplication and cache layer (Redis etc.)
