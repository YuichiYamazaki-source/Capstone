# Data Flow: Course Retrieval Pipeline

## Overview

This document describes the logical flow when a user searches for or browses courses, covering both structured search (Phase 2) and semantic search (Phase 3).

## Structured Search (Phase 2 — Current)

```
User types search query or applies filters
  │
  ▼
Frontend (React)
  │  Debounced input → API call
  │
  ▼
Vite Proxy (/api → gateway:8000)
  │
  ▼
Gateway (FastAPI :8000)
  │  Route: /api/v1/courses or /api/v1/courses/search
  │  JWT validation (optional, for personalized results)
  │
  ▼
Course Service (FastAPI :8001)
  │  Build MongoDB query:
  │    - Text search: regex on title, description, skills
  │    - Level filter: case-insensitive exact match
  │    - Organization filter: case-insensitive partial match
  │    - Rating filter: $gte comparison
  │    - Skills filter: $in on skills_lower array
  │  Pagination: skip(offset).limit(limit)
  │
  ▼
MongoDB
  │  Uses indexes for level, organization, skills
  │  count_documents for total, find for results
  │
  ▼
Response: { courses: [...], total, limit, offset }
  │
  ▼
Frontend renders CourseCard grid (3 columns, 12 per page)
```

## Semantic Search (Phase 3 — Planned)

```
User enters natural language query
  (e.g., "I want to learn machine learning for healthcare")
  │
  ▼
Frontend → Gateway → AI Service (:8003)
  │
  ▼
AI Service: Query Understanding
  │  Extract intent, entities, constraints
  │  Agent orchestration (OpenAI Agents SDK)
  │
  ▼
Embedding: query → OpenAI text-embedding-3-small → vector
  │
  ▼
Qdrant: vector similarity search → top-K course IDs
  │  Filters: level, organization (metadata filtering)
  │
  ▼
MongoDB: Fetch full course documents by IDs
  │
  ▼
RAG: courses + user query + user profile → LLM
  │  Generate: explanations, recommendations, learning path
  │
  ▼
Response: structured recommendation with reasoning
  │
  ▼
Frontend renders personalized results with "Why recommended" reasons
```

## Graceful Degradation Chain

```
Semantic Search (Qdrant + LLM)
  │ fails?
  ▼
Vector Search Only (Qdrant, no LLM reasoning)
  │ fails?
  ▼
Keyword Search (MongoDB regex — Phase 2 behavior)
  │ fails?
  ▼
Error message to user
```
