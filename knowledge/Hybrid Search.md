# Hybrid Search — How It Works

## What Is Hybrid Search

Hybrid search combines two complementary retrieval methods:

1. **Keyword search** (sparse / BM25) — token-level relevance scoring with TF-IDF weighting
2. **Semantic search** (dense) — vector similarity via embeddings (cosine distance)

Neither method alone covers all query types well. Hybrid search runs both and merges results using score fusion.

## Why Two Methods Are Complementary

| Query Type | Keyword (BM25) | Semantic (Dense) | Example |
|---|---|---|---|
| Exact term | Strong | Weak | "Python" matches title directly |
| Conceptual intent | Weak | Strong | "transition from backend to ML" has no exact keyword |
| Synonyms | Miss | Hit | "coding" finds "programming" |
| Proper nouns | Hit | May miss | "AWS" matches exactly |
| Typos/variations | Miss | Partial | "machin lerning" may partially embed |

Keyword search is **high precision, low recall** — it finds exact matches but misses related content.
Semantic search is **high recall, low precision** — it finds related content but may return loosely related results.

Hybrid search takes the union and re-ranks, getting both precision and recall benefits.

## BM25 (Best Matching 25)

BM25 is the standard keyword ranking algorithm used in information retrieval (Elasticsearch, Solr, Qdrant, etc.).

### How It Scores

```
BM25(q, d) = Σ IDF(qi) × (TF(qi, d) × (k1 + 1)) / (TF(qi, d) + k1 × (1 - b + b × |d|/avgdl))
```

- **TF (Term Frequency)**: how often a query term appears in the document — more = higher score, with diminishing returns
- **IDF (Inverse Document Frequency)**: rare terms across the corpus get higher weight — "Python" scores higher than "course"
- **Document length normalization**: shorter documents that match get a boost over verbose ones

### Why BM25 >> Regex

| | Regex | BM25 |
|---|---|---|
| Match type | Binary (yes/no) | Scored (0 to ∞) |
| Multi-term queries | OR of individual matches | Terms weighted by IDF, multi-match boosted |
| Ranking | No relevance rank (sort by rating, etc.) | Ranked by text relevance |
| "Python programming" | Any doc with "Python" OR "programming" | Docs with BOTH terms ranked highest |
| Performance | Full collection scan | Inverted index (O(1) lookup per term) |

Regex keyword search was our original implementation. It caused low Precision@5 (~0.55) because irrelevant documents with partial word matches outranked relevant ones.

## Qdrant as Unified Hybrid Search Backend

### Why Qdrant for Both Keyword and Semantic

Qdrant natively supports **named vectors** — multiple vector representations per point:
- **Dense vectors** (e.g., OpenAI `text-embedding-3-small`) for semantic search
- **Sparse vectors** (BM25) for keyword search with IDF scoring

This eliminates the need for a separate keyword search backend (MongoDB regex).

### Key Qdrant Features Used

1. **Built-in BM25**: Qdrant v1.15+ can generate BM25 sparse vectors from raw text server-side. No external tokenizer needed.
2. **IDF Modifier**: `SparseVectorParams(modifier=Modifier.IDF)` — Qdrant calculates IDF across the collection automatically.
3. **Query API with Prefetch**: Run sparse and dense searches as sub-queries in a single API call.
4. **Server-side RRF Fusion**: `FusionQuery(fusion=Fusion.RRF)` — Qdrant merges ranked lists server-side. No custom Python merge code.
5. **Payload Filters**: Level, rating, organization constraints applied as pre-filters during both sparse and dense search.

### Architecture Comparison

**Before (v2.1):**
```
hybrid_search()
  ├── asyncio.gather (parallel, 2 network calls)
  │   ├── _keyword_search()  → MongoDB regex (no relevance score)
  │   └── _semantic_search() → Qdrant dense vectors
  ├── _rrf_merge()           → Python-side RRF
  └── Return top_k
```

**After (v3.0):**
```
hybrid_search()
  └── qdrant.query_points()  → 1 API call
        prefetch:
          ├── BM25 sparse query (keyword, IDF-scored)
          └── Dense vector query (semantic, cosine)
        fusion: RRF (server-side)
        filter: level, rating, organization
        → Return top_k
```

Benefits:
- 2 network calls → 1 (lower latency)
- Custom RRF code → server-side (less code, optimized)
- Regex (no scoring) → BM25 (relevance-ranked)
- MongoDB for search → MongoDB for CRUD only (cleaner separation)

## Score Fusion: Reciprocal Rank Fusion (RRF)

The key problem: BM25 returns relevance scores (0 to ∞), and vector search returns cosine similarity (0-1). These scores are not on the same scale and cannot be directly compared.

**RRF solves this by using rank position instead of raw scores.**

### Algorithm

For each document `d` that appears in any result list:

```
RRF_score(d) = sum over all lists L:  1 / (k + rank_L(d))
```

Where:
- `k` = smoothing constant (typically 60)
- `rank_L(d)` = position of document `d` in list `L` (1-indexed)
- If `d` is not in list `L`, it contributes 0

### Example

Query: "beginner machine learning courses"

BM25 returns: [Course_A (rank 1), Course_B (rank 2), Course_C (rank 3)]
Semantic returns: [Course_D (rank 1), Course_A (rank 2), Course_E (rank 3)]

RRF scores (k=60):
- Course_A: 1/(60+1) + 1/(60+2) = 0.01639 + 0.01613 = **0.03252** (appears in both!)
- Course_D: 0 + 1/(60+1) = **0.01639**
- Course_B: 1/(60+2) + 0 = **0.01613**
- Course_C: 1/(60+3) + 0 = **0.01587**
- Course_E: 0 + 1/(60+3) = **0.01587**

Final ranking: **Course_A > Course_D > Course_B > Course_C = Course_E**

Course_A is ranked first because it appeared in BOTH lists.

### Why k=60?

The original RRF paper (Cormack et al., 2009) found k=60 to be robust across datasets:
- Small k (e.g., 1): top positions are heavily favored
- Large k (e.g., 1000): all positions are nearly equal
- k=60: balanced — top results matter more, but lower-ranked results still contribute

## Filter Integration

Structured constraints (level, rating, organization) are applied as **Qdrant payload filters** — pre-filtering during both sparse and dense search.

Pre-filtering is more efficient than post-filtering because:
1. Qdrant applies filters at the index level (uses payload indexes)
2. Results respect the `limit` parameter (always get K results that match filters)
3. No wasted computation on filtered-out documents
