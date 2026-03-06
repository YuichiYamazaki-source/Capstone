# AI Commerce Platform – Project Overview

## Dates of Milestone project

> Milestone 1 - 27 Feb

> Milestone 2 - 4 Mar

>  Milestone 3 - 7 Mar
 
> Milestone 4 - 11 Mar

## Background

A project to modernize a fashion e-commerce company's system into
an AI-ready microservices architecture.

## Quick Start

```bash
# 1. Build and start all services
docker compose up --build -d

# 2. Seed demo data (products + demo user)
docker compose exec product python -m src.product.seed

# 3. Index products into Qdrant (for semantic search)
docker compose exec product python -m src.product.index

# 4. Open in browser
#    http://localhost
#    Login: demo@example.com / demo1234

# Run tests (no Docker required)
pytest tests/ -v
```

Services available at:
- **Frontend**: http://localhost (port 80, via nginx gateway)
- Gateway: http://localhost (port 80)
- Auth: http://localhost:8001
- Product: http://localhost:8002
- Cart: http://localhost:8003
- Order: http://localhost:8004
- MongoDB: localhost:27017
- Qdrant: http://localhost:6333
- Frontend (dev): http://localhost:5173

## Architecture Diagram

- Full system diagram: [`docs/architecture/system_architecture.mermaid`](docs/architecture/system_architecture.mermaid)
- MVP deployment: [`docs/architecture/mvp_architecture.md`](docs/architecture/mvp_architecture.md)
- Design decisions: [`FDE Capstone Lens.md`](FDE%20Capstone%20Lens.md) (ADR index)

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

---

## Implementation Roadmap

### Phase 1: Backend — Microservices

#### Step 1: 環境構築

- [x] `docker-compose.yml` で7コンテナ構成（MongoDB, Qdrant, 4サービス, nginx gateway）
- [x] 各サービスのディレクトリ構成を作成（`src/auth/`, `src/product/`, `src/cart/`, `src/order/`）
- [x] サービス別Dockerfile + 共有モジュール（logging, vector_store adapter）
- [x] ヘルスチェックエンドポイント（全サービス `/health`）
- [x] ADR（MongoDB, Microservices, Qdrant, API Gateway）

#### Step 2: Auth Service

- [x] ユーザー登録エンドポイント（`POST /auth/register`）
- [x] ログインエンドポイント（`POST /auth/login`）→ JWTトークン発行
- [x] JWT検証ミドルウェア（他サービス共通で使えるように）

#### Step 3: Product Service

- [x] 商品一覧取得（`GET /products`）
- [x] 商品詳細取得（`GET /products/{id}`）
- [x] 在庫確認ロジック（在庫なし商品は一覧から除外）

#### Step 4: Cart Service

- [x] カートにアイテム追加（`POST /cart/items`）— 在庫チェックを含む
- [x] カートからアイテム削除（`DELETE /cart/items/{id}`）
- [x] カート内容取得（`GET /cart`）

#### Step 5: Order Service

- [x] 注文確定エンドポイント（`POST /orders`）
- [x] モック決済処理
- [x] 注文完了時に在庫を自動減算

#### Step 6: バックエンド統合テスト

- [x] 各サービスのユニットテスト（`tests/`）
- [x] Auth → Product → Cart → Order の一連のE2Eフロー確認

---

### Phase 2: Frontend

#### Step 7: フロントエンド環境構築

- [x] Vite + React + JavaScript プロジェクト（`src/frontend/`）
- [x] API Gatewayへのリクエスト設定（同一オリジン経由、Bearer token認証）
- [x] Docker コンテナ化（node:20-alpine + Vite dev server）
- [x] nginx catch-all ルーティング（WebSocket HMR対応）

#### Step 8: 認証画面

- [x] ログインページ（JWTをlocalStorageに保存）
- [ ] 新規登録ページ

#### Step 9: 商品・カート・注文画面

- [x] 商品一覧ページ（在庫あり商品のみ表示、カート追加ボタン）
- [x] AI検索ページ（自然言語入力 → 商品カード + similarity score + LLMサマリー）
- [x] カートページ（追加・削除・合計金額表示）
- [ ] 商品詳細ページ
- [ ] 注文確認 → 注文完了ページ

#### Step 10: フロントエンド統合確認

- [x] バックエンドと繋いで一連のユーザーフロー動作確認（ログイン→商品一覧→AI検索→カート）

---

### Phase 3: Semantic Search

**設計決定:** Hybrid Search（semantic vector search + Qdrant payload filter）。Query Parser（LLM）でユーザー入力を「意味検索部分」と「構造化フィルタ」に分離するマルチエージェント構成。

#### Step 11: Embedding & Index 基盤

- [x] `src/shared/embedding.py` — OpenAI `text-embedding-3-small` クライアント
- [x] `src/product/index.py` — MongoDB products → embedding → Qdrant upsert（独立スクリプト）
- [x] Embedding対象: `f"{name}. {category}. {description}"`（意味フィールドのみ）
- [x] price/stock は Qdrant payload に格納（filter/sort用）

#### Step 12: Hybrid Search エンドポイント

- [x] Query Parser（LLM structured output）— semantic_query + filters 分離
- [x] `POST /products/recommend` — vector search + payload filter の統合
- [x] 明示的な価格クエリ（「5000円以下」）→ Qdrant Range filter
- [x] 曖昧な価格意図（「安い」）→ sort_by_price: asc
- [ ] 検索履歴をMongoDBに保存

#### Step 13: 検索UI統合

- [x] フロントエンドにAI検索ページを追加
- [x] Semantic Search APIと接続、商品カード（名前・価格・スコア・在庫）表示
- [x] recommend レスポンスを仕様準拠に構造化（query, model_version, products, recommendations）

#### Step 14: LLM Ops

- [ ] Embedding モデルバージョンをModel Registryで管理

#### Future Work（M3以降）

- [ ] 曖昧な価格意図の高度化（価格分布ベース動的閾値）
- [ ] 多通貨対応（為替API or LLM換算）
- [ ] Embedding model フォールバック（OpenAI障害時の代替）

---

## 🔗 Graph Links - Capstone × Lecture Connections
- 🗺️ MOC: [[MOC]]
- RAG / Semantic Search → [[Lecture/day22-Context Engineering/Context Engineering & RAG]]
- Vector DB / System Design → [[Lecture/day23-SemanticSearch/System Architecture & Semantic Search]]
- LLM Orchestration / Eval → [[Lecture/day24-FDE skills & LLM Orchestration/LLM Orchestration]]
- LangChain / LangGraph → [[Lecture/day25-LangChain/LLM Orchestration with LangChain]]
- Agentic AI → [[Lecture/day26-Agentic AI & RAG/Agentic AI & RAG]]
- MCP / Agent Protocols → [[Lecture/day27-Agent Protocols & Advanced Use Cases/Agent Protocols & Advanced Use Cases]]
- Security / Guardrails → [[Lecture/day28-Securing LLMs & Guardrails/Securing LLMs & Guardrails]]
- Architecture詳細 → [[Archtecture]]
- FDE Lens → [[Captone/FDE Capstone Lens]]

---

## 📋 Files & Notes Index

| File | Description |
|---|---|
| [[Captone/README]] | This file — project overview & architecture |
| [[Captone/FDE Capstone Lens]] | Architecture Decision Records (ADR) |
| `system_architecture.mermaid` | Full system diagram |
| `docker-compose.yml` | Local dev environment |
| `src/` | Service source code |
| `tests/` | Test suites |
| `docs/` | Additional documentation |

---

## 🔗 Graph Links — Folder Connections

- 🗺️ MOC → [[MOC]]
- Practice implementations → [[materials/README]]
- Lecture notes → [[Lecture/README]]

### Concept → Lecture cross-reference

| Capstone Component | Key Concept | Lecture |
|---|---|---|
| Semantic Search Service | Embedding, VectorDB, Hybrid Search | [[Lecture/day23-SemanticSearch/System Architecture & Semantic Search]] |
| Auth / Product / Cart / Order Service | Microservices, NoSQL | [[Lecture/day23-SemanticSearch/System Architecture & Semantic Search]] |
| LLM Ops / Embedding Generation | RAG Pipeline, Chunking | [[Lecture/day22-Context Engineering/Context Engineering & RAG]] |
| Multi-Agent Architecture | Multi-Agent, Handoff | [[Lecture/day26-Agentic AI & RAG/Agentic AI & RAG]], [[Lecture/day27-Agent Protocols & Advanced Use Cases/Agent Protocols & Advanced Use Cases]] |
| Eval / Quality Gate | LLM-as-Judge, Evals | [[Lecture/day24-FDE skills & LLM Orchestration/LLM Orchestration]] |
| Guardrails | Input/Output Guardrail | [[Lecture/day28-Securing LLMs & Guardrails/Securing LLMs & Guardrails]] |
| Data Pipeline | PySpark, ETL | [[materials/Pyspark/Pyspark]] |

### Concept → Practice cross-reference

| Capstone Component | Practice Note |
|---|---|
| Auth Service | [[materials/Authentication_JavaScript/Authentication_JavaScript]] |
| Product / Cart / Order Service | [[materials/MongoDB_FastAPI/MongoDB_FastAPI]] |
| Frontend | [[materials/React_assessment/React_Assessment]] |
| Testing | [[materials/Pytest_JEST/Pytest_JEST]] |
| Data Pipeline | [[materials/Pyspark/Pyspark]] |
| Multi-Agent / LLM Ops | [[materials/Orchestrated LLM Application/Task5_Orchestrated_LLM]] |
| MCP Integration | [[materials/day28-activity/Day28_MCP_Activity]] |

---

## 🏷️ Tags

`#type/index` `#type/capstone` `#folder/capstone`
