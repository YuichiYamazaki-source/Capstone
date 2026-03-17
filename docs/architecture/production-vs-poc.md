# Production vs PoC Architecture

## Overview

This document clarifies the boundary between the current Proof of Concept (PoC) and a production-ready deployment. The PoC demonstrates full functionality on a single machine using Docker Compose. Production deployment addresses scalability, reliability, and operational concerns.

## Architecture Comparison

| Layer | PoC (Current) | Production |
|-------|--------------|------------|
| **Deployment** | Docker Compose (localhost) | Azure App Service / AWS ECS Fargate / Cloud Run |
| **Database** | Single MongoDB container | Azure Cosmos DB (MongoDB API) / Atlas |
| **Vector DB** | Single Qdrant container | Qdrant Cloud / managed instance |
| **API Gateway** | FastAPI self-routing | Cloud API Gateway + Rate Limiting + WAF |
| **Auth** | JWT with dev secret key | OAuth2/OIDC + Azure Key Vault / AWS Secrets Manager |
| **Observability** | Health endpoints + structured logs | Prometheus + Grafana + OpenTelemetry tracing |
| **LLM Ops** | Local logging / LangFuse OSS | LangFuse Cloud / Datadog LLM Monitoring |
| **Caching** | None | Redis (Azure Cache / ElastiCache) |
| **Resilience** | Local fallback model (MiniLM-L6-v2) | Circuit breaker + retry + fallback + dead letter queue |
| **Scaling** | Single instance per service | Horizontal autoscale (PaaS-managed) |
| **CI/CD** | Manual docker compose up | GitHub Actions → Container Registry → PaaS deploy |
| **Testing** | Unit + Integration + small Load test | + Chaos engineering + A/B testing + canary deploy |

## Deployment Strategy Decision

### Why NOT Kubernetes?

For a university course finder (~6,000 courses, limited concurrent users), Kubernetes is overengineered:
- High operational overhead (cluster management, YAML complexity)
- Cost disproportionate to traffic volume
- University use case does not require sub-second autoscaling

### Why PaaS (App Service / Cloud Run)?

- **Low management overhead**: No cluster ops, automatic OS patching
- **Natural migration path**: Docker Compose → container image → PaaS deploy
- **Cost-efficient**: Pay-per-use or low-tier plans sufficient for university scale
- **Managed DB integration**: Cosmos DB, managed Qdrant available as add-ons
- **Sufficient scaling**: Handles hundreds of concurrent users without K8s complexity

### Migration Path

```
PoC (Docker Compose)
  → Containerize each service (already done)
    → Push images to Container Registry (ACR/ECR/GCR)
      → Deploy to App Service / Cloud Run / ECS Fargate
        → Connect to managed MongoDB (Cosmos DB) + managed Qdrant
          → Add API Gateway + CDN + monitoring
```

## What PoC Proves

1. **Functional completeness**: All features work end-to-end (search, filter, auth, RAG, recommendations)
2. **Microservice boundaries**: Services are independently deployable containers
3. **Data pipeline**: CSV → MongoDB → Qdrant embedding pipeline is validated
4. **AI quality**: RAG retrieval accuracy and recommendation relevance are measured
5. **API contract**: Frontend ↔ Gateway ↔ Services interface is stable

## What Production Adds

1. **Operational reliability**: Health monitoring, alerting, log aggregation
2. **Security hardening**: Secret management, HTTPS termination, input sanitization
3. **Performance**: Connection pooling, caching, CDN for static assets
4. **Observability**: Distributed tracing across services, LLM cost/latency dashboards
5. **Data management**: Backup strategies, data retention policies
