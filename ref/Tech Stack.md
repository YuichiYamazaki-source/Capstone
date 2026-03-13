# Tech Stack — Intelligent University Course Finder

**Tags**: #type/reference #domain/system-design #concept/microservices

## Confirmed
| Component | Choice | Notes |
|-----------|--------|-------|
| LLM Orchestration | OpenAI Agents SDK | Agent SDK-based architecture |
| Evaluation | DeepEval | Required by Requirement 2 |
| Observability | LangFuse, Arize Phoenix | Tracing & monitoring |
| Backend | Python + FastAPI | API layer |
| Frontend | React + JavaScript + Vite | Requirement 2 UI |
| Dataset | Coursera Course Dataset | CSV/JSON |

## Not Yet Decided
| Component | Candidates | Notes |
|-----------|-----------|-------|
| Vector DB | ChromaDB / Qdrant / Weaviate | TBD |
| Embedding Model | TBD | For course descriptions |
| Reranker | TBD | Cross-encoder for Requirement 2 |
| Deployment | Local / Cloud | Cloud account availability unknown |
