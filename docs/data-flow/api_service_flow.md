# API Service Flow

## Overview

This document describes the data flow across the 4 microservices
(Auth, Product, Cart, Order) through the nginx API Gateway.

## Request Flow Diagram

```mermaid
sequenceDiagram
    participant C as Client
    participant GW as API Gateway (nginx)
    participant A as Auth Service
    participant P as Product Service
    participant CA as Cart Service
    participant O as Order Service
    participant DB as MongoDB

    Note over C,DB: 1. Authentication
    C->>GW: POST /auth/register {email, password, name}
    GW->>A: proxy
    A->>DB: users.insert_one()
    A-->>C: 201 {user_id}

    C->>GW: POST /auth/login {email, password}
    GW->>A: proxy
    A->>DB: users.find_one()
    A-->>C: 200 {access_token}

    Note over C,DB: 2. Browse Products
    C->>GW: GET /products/ [Bearer token]
    GW->>P: proxy
    P->>DB: products.find({available_stock > 0})
    P-->>C: 200 [products]

    Note over C,DB: 3. Add to Cart
    C->>GW: POST /cart/items {product_id, quantity} [Bearer token]
    GW->>CA: proxy
    CA->>DB: products.find_one() — stock check
    CA->>DB: carts.update_one() — upsert
    CA-->>C: 201 "Item added"

    Note over C,DB: 4. Place Order
    C->>GW: POST /orders/ [Bearer token]
    GW->>O: proxy
    O->>DB: carts.find_one() — get cart
    O->>DB: products.find_one() — validate stock (per item)
    O->>DB: orders.insert_one() — create order
    O->>DB: products.update_one($inc) — decrement stock (per item)
    O->>DB: carts.delete_one() — clear cart
    O-->>C: 201 {order_id, total, status}
```

## Service Responsibilities

| Service | Reads from | Writes to | Key logic |
|---------|-----------|-----------|-----------|
| Auth | users | users | bcrypt hash, JWT issue |
| Product | products | products | Stock filter (`available_stock > 0`) |
| Cart | products, carts | carts | Stock validation, quantity increment |
| Order | carts, products, orders | products, orders, carts | Stock re-validation, stock decrement, cart clear |

## Data Coupling

All services share a single MongoDB instance (MVP architecture).
Data consistency is maintained through:

1. **Stock validation at cart-add time** — prevents adding out-of-stock items
2. **Stock re-validation at order time** — catches race conditions between cart and order
3. **Atomic stock decrement** — uses MongoDB `$inc` operator (atomic per document)

## Gateway Routing

```
/auth/*      → auth:8001
/products/*  → product:8002
/cart/*      → cart:8003
/orders/*    → order:8004
```

CORS headers are set at the gateway level.
Each service handles its own JWT verification via `Depends(verify_token)`.
