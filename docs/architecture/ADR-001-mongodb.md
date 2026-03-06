# ADR-001: MongoDB as Primary Database

## Status
Accepted

## Context
The platform stores users, products, carts, orders, and inventory data. We need a database that handles:
- Flexible product schemas (fashion items have varying attributes)
- Nested documents (cart items, order line items)
- Fast reads for product catalog
- Simple setup for local development

## Decision
Use **MongoDB 7** as the primary data store.

## Alternatives Considered

| Option | Pros | Cons |
|---|---|---|
| PostgreSQL | Strong consistency, ACID, mature | Rigid schema, harder for nested docs |
| MongoDB | Flexible schema, document model fits e-commerce, easy Docker setup | Eventual consistency, no JOINs |
| DynamoDB | Serverless, auto-scaling | AWS lock-in, complex local dev |

## Consequences
- **Positive**: Document model naturally fits cart/order structures. No ORM needed with pymongo
- **Positive**: Single `docker compose up` with official mongo:7 image
- **Negative**: No foreign key constraints — referential integrity must be enforced in application code
- **Negative**: Cross-collection transactions are more complex than SQL JOINs
