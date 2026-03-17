# Tests

## Structure

```
tests/
├── api/          # API endpoint tests (ingestion + retrieval)
├── integration/  # End-to-end integration tests
└── load/         # Load/performance tests (locust)
```

## Status

Test suite implementation is planned for Phase 3.

### Planned Coverage

| Category | Scope | Tool |
|----------|-------|------|
| API Tests | Course CRUD, Auth, Search | pytest + httpx |
| Integration | Full request flow through Gateway | pytest + docker |
| Load | Throughput and latency under concurrency | locust |
| Evaluation | RAG accuracy, recommendation quality | Custom + LLM-as-Judge |
