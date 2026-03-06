# ADR-004: nginx as API Gateway

## Status
Accepted

## Context
With 4 microservices on separate ports, clients need a single entry point. The checklist asks: "Does the architecture discuss API Gateways?"

## Decision
Use **nginx:alpine** as a reverse proxy / API Gateway, routing by URL path prefix.

## Routing Table

| Path | Upstream |
|---|---|
| `/auth/*` | auth:8001 |
| `/products/*` | product:8002 |
| `/cart/*` | cart:8003 |
| `/orders/*` | order:8004 |
| `/health` | Gateway self-check |

## Alternatives Considered

| Option | Pros | Cons |
|---|---|---|
| **nginx** | Proven, lightweight, zero custom code | No built-in auth, rate limiting needs config |
| Traefik | Auto-discovery, Docker-native labels | More complex config for simple routing |
| Kong | Plugin ecosystem (auth, rate-limit) | Heavy, overkill for MVP |
| Custom FastAPI gateway | Full control, Python | Maintenance burden, reinventing the wheel |

## Consequences
- **Positive**: CORS handled at one point (gateway level)
- **Positive**: Clients use a single port (80) instead of remembering 4 service ports
- **Positive**: Easy to add rate limiting, SSL termination later
- **Negative**: No authentication enforcement at gateway level (each service does its own JWT check)
- **Negative**: Static config — adding a new service requires updating nginx.conf
