# ADR-003: Qdrant as Vector Database

## Status
Accepted

## Context
Phase 3 (Semantic Search) requires vector similarity search for product embeddings. The checklist requires the ability to swap Vector DB providers without rewriting the core API.

## Decision
Use **Qdrant** as the primary vector database, accessed through an abstract `VectorStore` adapter (`src/shared/vector_store.py`).

## Alternatives Considered

| Option | Local Docker | RAM | Hybrid Search | SDK Quality | Learning Value |
|---|---|---|---|---|---|
| ChromaDB | Easy (256MB) | Low | Limited | Good | High |
| **Qdrant** | **Easy (512MB-1GB)** | **Low** | **Full** | **Best (Pydantic)** | **High** |
| Weaviate | Easy (1-2GB) | Medium | Full | Good | High |
| Pinecone | No (cloud only) | N/A | Yes | Good | Low |
| Milvus | Heavy (4-8GB) | High | Full | Complex | Medium |

## Consequences
- **Positive**: Lightweight Docker container, runs comfortably on Windows dev machine
- **Positive**: Python SDK is Pydantic-based — consistent with our FastAPI tech stack
- **Positive**: Full hybrid search (sparse + dense vectors) for Phase 3
- **Positive**: Adapter pattern enables swapping to ChromaDB/Milvus without API changes
- **Negative**: Smaller community than ChromaDB for RAG tutorials (but growing fast)
