# Data Flow — Course Dataset & Pipeline

Source: `data/coursera_course_2024.csv`
Analysis notebook: `data/explore.ipynb`

---

## 1. Dataset Overview

- **Rows**: 6,645 courses
- **Columns**: 14
- **Key fields**: title, enrolled, rating, num_reviews, Instructor, Organization, Skills, Description, Modules/Courses, Level, Schedule, URL, Satisfaction Rate

---

## 2. Data Quality

### Effective missing values (NaN + placeholder strings)

| Field | Missing | % |
|---|---|---|
| Satisfaction Rate | 4,447 | 66.9% |
| Skills (empty `[]`) | 1,954 | 29.4% |
| Schedule | 1,888 | 28.4% |
| enrolled (`"Enrollment number not found"`) | 1,758 | 26.5% |
| rating (`"Rating not found"`) | 1,436 | 21.6% |
| num_reviews | 1,392 | 20.9% |
| Level | 778 | 11.7% |

### Data type issues

- `enrolled`, `rating`, `Satisfaction Rate` are stored as strings, not numeric.
- `Skills` is a string representation of a Python list (e.g. `"['Data Analysis', 'SQL']"`).
- `Unnamed: 0` is an artifact index column.

---

## 3. Level Distribution

| Level | Count | % |
|---|---|---|
| Beginner | 3,591 | 54.0% |
| Intermediate | 2,024 | 30.5% |
| Unknown (NaN) | 778 | 11.7% |
| Advanced | 252 | 3.8% |

**Bias**: The dataset is heavily skewed toward Beginner (54%). Advanced courses are only 3.8%.

---

## 4. Rating Distribution (valid only, n=5,209)

| Stat | Value |
|---|---|
| Mean | 4.62 |
| Std | 0.25 |
| Min | 3.0 |
| Median | 4.7 |
| Max | 5.0 |

Ratings are concentrated in 4.5-5.0 range. Very few courses below 4.0.

---

## 5. Organizations

- **298 unique organizations**
- Top 20 orgs account for 3,093 courses (46.5%)
- Remaining 278 orgs account for 3,552 courses (53.5%)
- Moderate concentration: not dominated by a single provider

---

## 6. Course Type

| Type | Count |
|---|---|
| Single courses (modules) | 5,612 |
| Specializations (series) | 1,023 |

- Unknown-level courses are **all** single courses (778/778).
- Specializations tend to have more Beginner-level courses.

---

## 7. Skills Analysis

- **70 unique skill labels** (after deduplication)
- 29.4% of courses have no skills listed
- Top skills: Data Analysis (313), Python Programming (220), Machine Learning (200), Data Visualization (173), Communication (149)

### Skills by Domain (mentions, filtered >=4 occurrences)

| Domain | Mentions | % |
|---|---|---|
| Data & Analytics | 2,394 | 18.6% |
| Programming & Dev | 1,938 | 15.0% |
| Business & Management | 1,607 | 12.5% |
| AI & ML | 1,182 | 9.2% |
| Cloud & Infra | 1,029 | 8.0% |
| Arts & Humanities | 976 | 7.6% |
| Marketing & Communication | 812 | 6.3% |
| Personal & Career Dev | 682 | 5.3% |
| Health & Life Sciences | 589 | 4.6% |
| Science & Engineering | 532 | 4.1% |
| Finance & Accounting | 366 | 2.8% |
| Cybersecurity | 322 | 2.5% |

**Bias**: Data/Programming/Business dominate. Health, Science, Finance are underrepresented.

---

## 8. Level Distribution by Domain

### Counts

| Domain | Beginner | Intermediate | Advanced | Unknown |
|---|---|---|---|---|
| No Skills | 956 | 483 | 69 | 446 |
| Data & Analytics | 334 | 241 | 23 | 53 |
| Programming & Dev | 255 | 180 | 29 | 25 |
| Business & Management | 252 | 100 | 17 | 61 |
| Cloud & Infra | 167 | 138 | 19 | 4 |
| Arts & Humanities | 178 | 60 | 1 | 45 |
| AI & ML | 114 | 142 | 15 | 9 |
| Marketing & Communication | 173 | 29 | 2 | 21 |
| Health & Life Sciences | 138 | 59 | 3 | 17 |
| Personal & Career Dev | 127 | 26 | 2 | 7 |
| Science & Engineering | 71 | 60 | 7 | 11 |
| Cybersecurity | 91 | 38 | 3 | 4 |
| Finance & Accounting | 59 | 28 | 1 | 19 |

### Percentage within each domain

| Domain | Beginner | Intermediate | Advanced | Unknown |
|---|---|---|---|---|
| Marketing & Communication | 76.9% | 12.9% | 0.9% | 9.3% |
| Personal & Career Dev | 78.4% | 16.0% | 1.2% | 4.3% |
| Health & Life Sciences | 63.6% | 27.2% | 1.4% | 7.8% |
| Arts & Humanities | 62.7% | 21.1% | 0.4% | 15.8% |
| Business & Management | 58.6% | 23.3% | 4.0% | 14.2% |
| Data & Analytics | 51.3% | 37.0% | 3.5% | 8.1% |
| Programming & Dev | 52.1% | 36.8% | 5.9% | 5.1% |
| Cloud & Infra | 50.9% | 42.1% | 5.8% | 1.2% |
| AI & ML | 40.7% | 50.7% | 5.4% | 3.2% |
| Science & Engineering | 47.7% | 40.3% | 4.7% | 7.4% |
| Cybersecurity | 66.9% | 27.9% | 2.2% | 2.9% |
| Finance & Accounting | 55.1% | 26.2% | 0.9% | 17.8% |

### Key observations

- **AI & ML** is the only domain where Intermediate (50.7%) exceeds Beginner (40.7%).
- **Marketing & Communication** and **Personal & Career Dev** are overwhelmingly Beginner (77-78%).
- **Cloud & Infra** and **Programming & Dev** have the highest Advanced ratios (~6%).
- **No Skills** courses have the highest Unknown rate (22.8%), suggesting metadata quality issues.
- **Arts & Humanities** and **Finance & Accounting** also have relatively high Unknown rates (16-18%).

---

## 9. Description

- 99.8% available (6,635 / 6,645)
- Mean length: 3,198 characters
- Range: 123 - 32,804 characters
- Good candidate as primary text source for RAG/embedding

---

## 10. Satisfaction Rate

- Only 33.1% available (2,198 / 6,645)
- Range: 62% - 100%, concentrated at 95-99%
- Too sparse to use as a primary signal

---

## 11. RAG Usability Summary

| Field | Usability | Notes |
|---|---|---|
| Description | Primary text source | 99.8% available, avg 3,198 chars |
| title | High | 100%, use for display and search |
| Skills | Supplementary | 29.4% empty, useful as metadata/filter |
| Organization | Filter/metadata | 100%, 298 unique |
| Level | Filter/metadata | 88.3% available, 4 categories |
| rating | Ranking signal | 78.4% valid numeric |
| Satisfaction Rate | Low priority | 66.9% missing |
| enrolled | Low priority | 26.5% placeholder |

---

## 12. Known Biases and Limitations

1. **Level skew**: 54% Beginner, only 3.8% Advanced. Recommendations may over-represent beginner content.
2. **Domain imbalance**: Data/Programming/Business dominate. Niche domains (Finance, Cybersecurity) are underrepresented.
3. **Missing metadata**: Skills (29.4%), Level (11.7%) are partially missing. Filtering by these fields excludes a significant portion.
4. **Rating inflation**: Mean 4.62 with very small variance. Rating alone is weak for differentiating quality.
5. **Organization concentration**: Top 20 orgs = 46.5% of courses. Results may be biased toward large providers.
6. **Snapshot bias**: 2024 data only. No temporal trend available.

---

# Ingestion Pipeline

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

## Phase 3: MongoDB → Qdrant

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

---

# Retrieval Pipeline

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

## Semantic Search (Phase 3 — Implemented)

```
User enters natural language query
  (e.g., "I want to learn machine learning for healthcare")
  │
  ▼
Frontend → Gateway → AI Service (:8003)
  │
  ▼
LLM (Learning Advisor Agent)
  │  Reads user profile (skills, level, interests) from MongoDB
  │  Extracts: search text, level, min_rating, organization, skill
  │  Calls retrieve_courses @function_tool
  │
  ▼
Hybrid Search (single Qdrant Query API call)
  │
  ├─ Dense: query → OpenAI text-embedding-3-small (1,536 dims)
  │    → Qdrant HNSW cosine similarity (weight 1.5, limit 30)
  │
  ├─ BM25: query + skill + level → Qdrant built-in tokenizer + IDF
  │    (weight 1.2, limit 30)
  │
  ├─ Payload Filter: level, min_rating, organization
  │    applied to both prefetches
  │
  └─ RRF Fusion: weights [BM25=1.2, Dense=1.5]
     → Top-K results with payload
  │
  ▼
Cross-Encoder Rerank (optional, RERANK_ENABLED flag)
  │  Model: all-MiniLM-L6-v2 (384 dims, local CPU)
  │  Method: Bi-Encoder cosine similarity (not true Cross-Encoder)
  │  See "Reranker Analysis" below for evaluation notes
  │
  ▼
LLM generates contextual response with course recommendations
  │
  ▼
Frontend renders personalized results
```

## Reranker Analysis

### Current Implementation

The reranker uses `all-MiniLM-L6-v2` (384 dims) as a Bi-Encoder:
- Embeds query and each candidate document separately
- Scores by cosine similarity between the two embeddings
- Re-sorts the Hybrid Search results

This is **not a true Cross-Encoder**. A Cross-Encoder takes `(query, document)` as a single
input pair and outputs a relevance score, allowing the model's attention to directly compare
both texts. The current Bi-Encoder approach embeds them independently.

### Why Reranking May Not Add Value in This Architecture

1. **LLM already optimizes the query**: The agent reads the user profile (skills, level,
   interests) and constructs a targeted search query. The Hybrid Search results are already
   personalized at query construction time.

2. **Hybrid Search is already two-stage**: BM25 (keyword precision) + Dense (semantic
   relevance) with RRF fusion provide strong ranking out of the box.

3. **Payload Filters pre-narrow results**: Level, rating, and organization filters eliminate
   irrelevant candidates before ranking even begins.

4. **Dimension mismatch risk**: The search uses OpenAI embeddings (1,536 dims) for ranking,
   then the reranker re-evaluates with MiniLM (384 dims) — a completely different embedding
   space. This can demote results that were correctly ranked by the primary model.

5. **Eval observation**: In testing, disabling the reranker sometimes produced equal or better
   results, suggesting the additional re-scoring step may be counterproductive.

### Recommendation

- Keep `RERANK_ENABLED=false` as default unless eval metrics prove otherwise
- If reranking is needed in the future, implement a true Cross-Encoder
  (e.g., `cross-encoder/ms-marco-MiniLM-L-6-v2`) instead of the current Bi-Encoder approach
- Consider the latency/Docker-image-size trade-off (torch dependency ≈ +500MB-1GB)

## Graceful Degradation Chain

```
1. Hybrid Search (BM25 + Dense + RRF via Qdrant)
   │ OpenAI embedding fails?
   ▼
2. BM25-only Search (Qdrant, weights [1.0])
   │ Qdrant unavailable?
   ▼
3. MongoDB Text Search ($text + textScore)
   │ MongoDB unavailable?
   ▼
4. Error message to user
```
