# AI Commerce Platform – Project Overview

## Background

A project to modernize a fashion e-commerce company's system into
an AI-ready microservices architecture.

## Architecture Diagram

See `system_architecture.mermaid`.

---

## Features

### Data Pipeline

| Component | Description |
| --- | --- |
| Remote Storage | Stores inventory data (CSV etc.). Ingested via batch processing. |
| Distributed Processing Engine | Cleanses and transforms inventory data, then loads it into the NoSQL DB. |

### API Gateway

| Component | Description |
| --- | --- |
| API Gateway | Receives external requests and routes them to each microservice. |

### Microservices

| Service | Description |
| --- | --- |
| Auth Service | Handles user registration and login, issues JWT tokens, and controls access to other services. |
| Product Service | Provides product listings and details, and checks stock availability. |
| Cart Service | Manages adding and removing items from the cart, with stock validation on each addition. |
| Order Service | Confirms orders and processes mock payments. Automatically deducts stock upon order completion. |
| Semantic Search Service | Converts text into embeddings and searches for related products using cosine similarity. |

### Data Store

| Component | Description |
| --- | --- |
| NoSQL DB | Main database storing users, products, inventory, carts, orders, and search history. |
| Vector DB | Stores embedding vectors for products and search queries, used for similarity search. |

### LLM Ops

| Component | Description |
| --- | --- |
| Embedding Generation | Vectorizes product descriptions and search queries using an LLM provider. |
| Model Registry | Manages embedding model versions to ensure traceability during redeployment. |

### Monitoring

| Component | Description |
| --- | --- |
| Monitoring & Logs | Collects metrics and logs from all services to visualize system health. |

### CI/CD

| Component | Description |
| --- | --- |
| CI/CD Pipeline | Runs automated tests on code changes and automatically deploys each service. |

---

## End-to-End User Flow

```text
1. User logs in → JWT token issued
2. Browse product listings (in-stock items only)
3. Search for products using semantic search
4. Add desired products to cart (stock check performed)
5. Review cart → Confirm order
6. Mock payment processed → Order complete
7. Stock count automatically decremented
```
