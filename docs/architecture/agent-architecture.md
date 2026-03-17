# Agent Architecture Design

## Diagrams

All architecture diagrams are in draw.io format for visual editing:

| Diagram | File | Description |
|---------|------|-------------|
| System Overview | [diagrams/system-overview.drawio](diagrams/system-overview.drawio) | Layered pipeline from input to response |
| Query Processing Flow | [diagrams/query-processing-flow.drawio](diagrams/query-processing-flow.drawio) | Step-by-step complex query handling |
| Version Evolution | [diagrams/version-evolution.drawio](diagrams/version-evolution.drawio) | Component decisions (LLM/ML/rule) + V1→V2→V3 + Phase mapping |

> Open `.drawio` files with [draw.io Desktop](https://www.drawio.com/) or VS Code draw.io extension.

---

## Architecture Principles

1. **Multi-label intent, not pattern matching** — Complex queries trigger multiple agents simultaneously. A single query can be career_guidance + skill_gap + learning_path at once.
2. **Query decomposition for complex inputs** — The system breaks multi-intent queries into sub-tasks with dependency awareness (DAG), enabling parallel execution where possible.
3. **Simple query shortcut** — When only one intent is detected with high confidence (≥0.5) and low ambiguity (<0.3), the decomposition step is skipped entirely, saving ~300ms.
4. **Ambiguity detection** — Vague queries like "何から学習したらいいかわからない" are caught early and trigger a clarifying question instead of wasting agent calls.
5. **LLM-first, optimize later** — V1 uses LLM for everything that needs semantic understanding. V2 replaces high-frequency, low-complexity components with SLM/ML. V3 adds fallback chains.
6. **Multi-modal ready** — The Input Normalizer abstracts input source (text/voice/doc), so adding modalities doesn't change downstream pipeline.

---

## Pipeline Overview

```
User Input (text / voice* / doc*)
   │
   ▼
┌──────────────────────────────────────────────────────┐
│  Query Understanding Layer                           │
│  ┌─────────┐  ┌──────────┐  ┌────────┐  ┌────────┐ │
│  │Normalize│→ │ Entity   │→ │Intent  │→ │Decompose│ │
│  │(rules)  │  │Extract   │  │Classify│  │(LLM)   │ │
│  │<5ms     │  │(LLM)     │  │(LLM)   │  │~300ms  │ │
│  │$0       │  │~200ms    │  │~100ms  │  │skip if │ │
│  └─────────┘  └──────────┘  └────────┘  │simple  │ │
│                                          └────────┘ │
└──────────────────────────────────────────────────────┘
   │
   ▼
┌──────────────────────────────────────────────────────┐
│  Orchestration Layer                                 │
│  Execution Planner (DAG) → Agent Dispatcher          │
│  → Result Merger                                     │
└──────────────────────────────────────────────────────┘
   │
   ▼
┌──────────────────────────────────────────────────────┐
│  Agent Layer (OpenAI Agents SDK)                     │
│  ┌─────────┐ ┌─────────┐ ┌──────────┐ ┌──────────┐│
│  │Retrieval│ │Skill Gap│ │Learn Path│ │Career    ││
│  │Agent    │ │Agent    │ │Agent     │ │Alignment ││
│  └─────────┘ └─────────┘ └──────────┘ └──────────┘│
│                    ↓ all outputs merge ↓            │
│              ┌──────────────────────┐               │
│              │ Learning Advisor     │               │
│              │ (final synthesizer)  │               │
│              └──────────────────────┘               │
└──────────────────────────────────────────────────────┘
   │                         │
   ▼                         ▼
┌─────────────────┐  ┌───────────────────────────────┐
│ Tool Layer (MCP)│  │ Response Layer                 │
│ search_semantic │  │ Context Assembly → LLM Gen     │
│ search_keyword  │  │ → Guardrails → Output          │
│ filter_courses  │  └───────────────────────────────┘
│ get_course_detail│
│ get_user_profile│
│ rerank (V2)     │
└─────────────────┘
   │
   ▼
┌──────────────────────────────────────────────────────┐
│ Retrieval Layer                                      │
│ Embed → Vector Search (Qdrant) ─┐                   │
│                                  ├→ RRF Fusion       │
│ Keyword Search (MongoDB) ───────┘   → Rerank (V2)   │
└──────────────────────────────────────────────────────┘
   │
   ▼
┌──────────────────────────────────────────────────────┐
│ Data Layer                                           │
│ Qdrant │ MongoDB │ OpenAI API │ Local Fallback (V3)  │
└──────────────────────────────────────────────────────┘
```

---

## Query Understanding Layer

### Step 1: Input Normalizer (rule-based)

- Whitespace and encoding normalization
- Language detection (en/ja)
- Multi-modal to text conversion (STT, OCR — future)
- **Latency**: <5ms | **Cost**: $0 | **Phase**: 3

### Step 2: Entity Extractor (LLM structured output)

Extracts structured fields from free-form text using GPT-4o-mini with JSON mode:

```json
{
  "skills_mentioned": ["Transformer", "AI-RAN", "LLM"],
  "career_goal": "AI Engineer at Google",
  "experience": "AI-RAN research (university)",
  "desired_focus": "LLM research and development",
  "constraints": { "timeline": "6 months" },
  "difficulty_pref": null,
  "ambiguity_score": 0.2
}
```

**Why LLM?** Free-form text → structured JSON requires semantic understanding. NER/regex can't handle "AI-RAN research" → experience category.

- **Latency**: ~200ms | **Cost**: ~$0.0003/req | **Phase**: 3
- **V2 optimization**: Cache frequent patterns for instant hits

### Step 3: Intent Classifier (multi-label)

Outputs confidence scores for all intents simultaneously (not mutually exclusive):

| Intent | Threshold | Triggers Agent |
|--------|-----------|----------------|
| `course_search` | ≥ 0.5 | Course Retrieval |
| `skill_gap_analysis` | ≥ 0.5 | Skill Gap Analysis |
| `learning_path` | ≥ 0.5 | Learning Path Planning |
| `career_guidance` | ≥ 0.5 | Career Alignment |
| `clarification_needed` | ≥ 0.7 | → Ask follow-up question |

- **Latency**: V1 ~100ms (LLM) → V2 ~5ms (fine-tuned SLM) | **Cost**: V1 ~$0.0002 → V2 $0
- **Key insight**: For the example query "Google AI Engineer + 6 months + LLM", this returns career=0.9, skill_gap=0.8, learning_path=0.7, course_search=0.6 — all four agents activated.

### Step 4: Query Decomposer (LLM, conditional)

Activated only when multiple intents detected or ambiguity is moderate (0.3-0.7). Breaks down the query into ordered sub-tasks with agent assignments.

**Skipped** for simple queries (single intent ≥ 0.5, ambiguity < 0.3) — saves ~300ms and 1 LLM call for ~60-70% of queries.

- **Latency**: ~300ms | **Cost**: ~$0.0005/req | **Phase**: 3

---

## Orchestration Layer

### Execution Planner

Converts sub-tasks into a DAG (Directed Acyclic Graph) with dependency tracking:

```
Complex query example:
  CAA ──┐
        ├──→ RA ──→ LPPA ──→ LA
  SGA ──┘

  CAA ∥ SGA (parallel, no data dependency)
  RA depends on both outputs
  LPPA depends on RA output
  LA always runs last
```

**Rule-based**, not LLM — the decomposer already identified dependencies. The planner just builds the execution order.

### Agent Dispatcher

Executes the DAG, passing context between agents. Supports parallel execution (e.g., CAA and SGA run concurrently via asyncio).

### Result Merger

Aggregates outputs from all agents, deduplicates courses, and formats for the Learning Advisor.

---

## Agent Layer

### Agent × Tool Matrix

| Tool | Retrieval | Skill Gap | Learning Path | Career | Advisor |
|------|:---------:|:---------:|:-------------:|:------:|:-------:|
| `search_semantic` | ✅ | ✅ | ✅ | ✅ | — |
| `search_keyword` | ✅ | — | — | — | — |
| `filter_courses` | ✅ | — | — | — | — |
| `get_course_detail` | ✅ | — | ✅ | — | — |
| `get_user_profile` | — | ✅ | — | ✅ | — |
| `rerank` (V2) | ✅ | — | — | — | — |

### Agent Descriptions

- **Course Retrieval Agent**: Primary data fetcher. Semantic + keyword search, filtering, hybrid score fusion.
- **Skill Gap Analysis Agent**: Compares user profile skills against required skills for a goal. Outputs missing skill list.
- **Learning Path Planning Agent**: Orders courses by prerequisite dependencies, difficulty progression, and skill coverage. Respects time constraints.
- **Career Alignment Agent**: Maps career goals to required skill sets. Uses domain knowledge to identify what skills matter for specific roles.
- **Learning Advisor Agent**: No tools. Receives merged outputs from all agents and generates the final natural language response with reasoning.

---

## Component Decision Matrix

| Component | V1 (Phase 3) | V2 (Phase 4) | V3 (Phase 5) |
|-----------|:------------:|:------------:|:------------:|
| **Input Normalizer** | Rule-based<br><5ms, $0 | + Multi-modal (STT, OCR)<br>+200ms | Same |
| **Entity Extractor** | LLM (GPT-4o-mini)<br>~200ms, ~$0.0003 | + Response cache<br>Hit: <5ms | Same |
| **Intent Classifier** | LLM (GPT-4o-mini)<br>~100ms, ~$0.0002 | Fine-tuned SLM<br>~5ms, $0 | + Fallback chain<br>SLM→LLM→rules |
| **Query Decomposer** | LLM (GPT-4o-mini)<br>~300ms, skip if simple | + Learned patterns<br>template for known types | Same |
| **Retrieval** | Hybrid (Vector+Keyword)<br>RRF, ~100ms | + Cross-encoder rerank<br>+50ms, $0 (local) | + Fallback chain<br>Qdrant→keyword→cached |
| **Agent Reasoning** | LLM (GPT-4o)<br>~500-800ms, ~$0.005/agent | + Prompt optimization<br>token reduction | + Local fallback<br>Flan-T5 |
| **Response Gen** | LLM (GPT-4o)<br>~400ms, ~$0.003 | + Streaming (SSE)<br>TTFB ~200ms | + Guardrail validation |
| **Guardrails** | Rule-based<br><5ms, $0 | + Heuristic checks | + LLM-as-Judge<br>CI/CD gates |

---

## Per-Query Cost & Latency Estimates

| Query Type | Example | V1 Latency | V1 Cost | Agents Used |
|------------|---------|:----------:|:-------:|:-----------:|
| **Simple** | "machine learning courses" | ~1.0s | ~$0.004 | RA → LA |
| **Moderate** | "I want to become a data scientist" | ~2.0s | ~$0.012 | SGA → RA → LPPA → LA |
| **Complex** | "Google AI Engineer, 6 months, LLM R&D..." | ~2.9s | ~$0.020 | CAA ∥ SGA → RA → LPPA → LA |
| **Ambiguous** | "何から学習したらいいかわからない" | ~0.4s | ~$0.001 | None (clarifying Q) |

---

## Phase Mapping

### Phase 3 — Make it work (V1)

All LLM-based, functional correctness over performance:

- Query Understanding pipeline (Normalize → Entity → Intent → Decompose)
- 5 Agents with OpenAI Agents SDK
- MCP Tool layer (5 tools)
- Hybrid retrieval (vector + keyword + RRF)
- Rule-based guardrails (input validation only)
- Basic DAG execution planner
- End-to-end chat flow

**Exit criteria**: User can chat, get semantic search results, and receive AI-powered recommendations.

### Phase 4 — Make it right (V2)

Measure, evaluate, optimize:

- LangFuse + Arize Phoenix observability
- Cross-encoder reranker (local model)
- Intent classifier → SLM distillation
- Prompt optimization (fewer tokens)
- Response streaming (SSE)
- DeepEval offline evaluation (NDCG, MAP, MRR)
- Ground truth dataset curation
- Full data ingestion (6,645 courses)

**Exit criteria**: Quantified accuracy/latency metrics with documented improvement trajectory.

### Phase 5 — Make it safe (V3)

Harden for reliability:

- Local embedding fallback (MiniLM-L6-v2)
- Local LLM fallback (Flan-T5)
- Retrieval fallback chain (Qdrant → keyword → cached)
- Intent classifier fallback chain (SLM → LLM → rules)
- Circuit breaker + retry with backoff
- LLM-as-Judge guardrails
- CI/CD quality gates
- Load testing (Locust)

**Exit criteria**: System degrades gracefully under any component failure.
