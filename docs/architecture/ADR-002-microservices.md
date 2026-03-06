# ADR-002: Microservices Architecture from Day 1

## Status
Accepted

## Context
The platform has 4 distinct business domains: Auth, Product, Cart, Order. The Senior Engineering Checklist requires "Modular Microservices. Clean separation of DB, AI, and API layers."

## Decision
Deploy each service as a **separate Docker container** from the start, with an nginx API Gateway for routing.

## Alternatives Considered

| Option | Pros | Cons |
|---|---|---|
| Monolith first, split later | Simpler initial setup | Migration pain, tight coupling risk |
| Microservices from day 1 | Clean boundaries, independent scaling, matches checklist | More Docker config, network complexity |
| Serverless functions | Zero ops | Cold starts, vendor lock-in |

## Consequences
- **Positive**: Each service can be developed, tested, and deployed independently
- **Positive**: Clear ownership boundaries per domain
- **Positive**: Agile-friendly — can add/modify services without touching others
- **Negative**: Docker Compose configuration is more complex than a single container
- **Negative**: Shared DB coupling still exists (MVP trade-off — will address in future phases)
