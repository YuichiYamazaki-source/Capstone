# Data Flow: Course Ingestion Pipeline

## Overview

This document describes the logical flow of course data from raw CSV to searchable state in both MongoDB (structured queries) and Qdrant (semantic search).

## Phase 2: CSV → MongoDB

```
coursera_course_2024.csv (6,645 courses)
  │
  ▼
scripts/ingest_courses.py
  │  --sample 100 (default) or --all
  │  Field mapping: CSV columns → MongoDB fields
  │  Type conversion: rating (str→float), skills (str→list)
  │  Placeholder detection: "Rating not found" → null
  │  Adds skills_lower[] for case-insensitive filtering
  │
  ▼
MongoDB (course_finder.courses)
  │  Indexes: title, level, organization, skills
  │
  ▼
Course Service (FastAPI + Motor async driver)
  │  GET /courses — list with filters
  │  GET /courses/search?q= — regex search
  │  GET /courses/{id} — by ObjectId
  │  GET /filters/options — distinct values
  │
  ▼
Gateway (:8000) → Frontend (:5173)
```

## Phase 3: MongoDB → Qdrant (Planned)

```
MongoDB (course_finder.courses)
  │
  ▼
Embedding Service
  │  Primary: OpenAI text-embedding-3-small (1536 dims)
  │  Fallback: sentence-transformers/all-MiniLM-L6-v2 (384 dims)
  │  Input: title + description + skills (concatenated)
  │
  ▼
Qdrant (course_vectors collection)
  │  Payload: course_id (reference back to MongoDB)
  │  Index: HNSW (default)
  │
  ▼
AI Service (:8003)
  │  Semantic search: query → embed → Qdrant → top-K courses
  │  RAG: top-K + query → LLM → contextual response
```

## Error Handling

| Failure Point | PoC Behavior | Production Behavior |
|---------------|-------------|-------------------|
| CSV parse error | Skip row, log warning | Skip row, alert on error rate threshold |
| MongoDB connection failure | Service won't start (lifespan) | Retry with backoff, health check fails |
| Embedding API timeout | Fall back to local MiniLM model | Circuit breaker → local model → log |
| Qdrant unavailable | Degrade to keyword search (MongoDB regex) | Circuit breaker → keyword fallback → alert |
