# Learnings & Insights

## Pipeline Architecture (`generate_data.py` / `ingest.py`)

### What the pipeline does
- `generate_data.py` generates a synthetic inventory CSV with intentionally dirty rows to simulate real-world data quality issues
- `ingest.py` reads that CSV, cleanses it, validates each row with Pydantic, and returns MongoDB-ready documents

### Why cleansing and validation are both needed
- `_cleanse()` (PySpark): Handles bulk data transformation — casting types, clamping negatives, dropping invalid rows. Fast and efficient for large-scale data.
- `_validate()` (Pydantic): Checks the structure of each individual row after cleansing. Acts as a final quality gate.
- They serve different purposes: cleansing **fixes or removes** bad data; validation **confirms** the result is correct.

### Why `RAW_SCHEMA` has all `nullable=True`
- The raw schema is intentionally permissive because it represents the **ingestion layer** — data should be accepted as-is first.
- Null enforcement happens explicitly in `_cleanse()` via `REQUIRED_COLS`, not at the schema level.
- Setting `nullable=False` in Spark schema can cause silent row drops or errors at read time, making debugging harder.

---

## ETL vs ELT

### ETL (Extract → Transform → Load) — Traditional
- Data is cleaned and transformed **before** loading into the database
- Common in older, smaller-scale systems

### ELT (Extract → Load → Transform) — Modern
- Raw data is loaded first, then transformed **inside** the Data Warehouse or Data Lake
- Preferred in modern data engineering because:
  - Warehouses and lakes are powerful enough to handle transformation internally
  - Raw data is preserved for reprocessing if needed
  - Over-validating at ingestion risks losing data permanently

---

## Medallion Architecture (Bronze / Silver / Gold)

A common pattern in Data Lakes (e.g., Databricks, Delta Lake):

```
Bronze layer  — Raw data, loose validation, stored as-is
      ↓
Silver layer  — Cleansed, typed, validated data
      ↓
Gold layer    — Business-ready, aggregated data
```

### Connection to this project
- `RAW_SCHEMA` with `nullable=True` = **Bronze layer thinking** — accept everything first
- `_cleanse()` = promotion to **Silver layer** — fix and filter
- `_validate()` (Pydantic) = final gate before writing to MongoDB (**Gold layer**)

---

## PySpark Key Concepts

### DAG and Lazy Evaluation
- PySpark builds a DAG (Directed Acyclic Graph) of transformations but does NOT execute them immediately
- Transformations like `filter()` and `withColumn()` are **lazy** — they just add to the DAG
- Execution only happens when an **Action** is called (e.g., `count()`, `collect()`, `show()`)
- Calling `count()` mid-pipeline for logging is wasteful — it triggers the entire DAG unnecessarily

### `withColumn` vs `filter`

| | What it does |
|---|---|
| `withColumn(col, expr)` | **Transforms a column** — row count stays the same |
| `filter(condition)` | **Removes rows** — column values stay the same |

### `F` alias (`pyspark.sql.functions`)
```python
from pyspark.sql import functions as F
```
- `pyspark.sql.functions` is imported as `F` by convention to keep code concise
- `F.col()`, `F.trim()`, `F.greatest()` etc. are all PySpark built-in column functions

### `cast()` function
- Converts a column's data type (e.g., String → Integer)
- **Key behavior**: if conversion fails, it returns `null` instead of raising an error
- This is intentionally exploited in the pipeline:
  ```
  Step 2: cast() — unparseable values become null
  Step 3: filter(isNotNull()) — null rows are dropped
  ```
- Example:
  ```
  "100" → 100    ✅
  "N/A" → null   ❌ (then dropped by filter)
  ```

---

## `_validate()` and `schema.py`

### What `_validate()` does
- Calls `df.collect()` — this is an **Action**, triggering the full DAG execution
- Converts each Spark row to a Python dict with `row.asDict()`
- Passes each dict to `InventoryRecord(**raw)` for Pydantic validation
- Returns two lists: `valid_docs` (MongoDB-ready) and `invalid_rows` (logged but not inserted)

### `InventoryRecord` — Pydantic schema in `schema.py`

Field rules:
| Field | Rule |
|---|---|
| `inventory_id` / `product_id` / `warehouse_id` | Required, `min_length=1` |
| stock columns (4 fields) | Required, `ge=0` (non-negative int) |
| `last_updated` | Required, datetime type |
| `batch_number` | Optional, defaults to `"UNKNOWN"` |

Custom validators:
- **`coerce_non_negative_int`**: casts to int, clamps negatives to 0, raises error if unparseable
- **`default_batch_number`**: returns `"UNKNOWN"` if empty or whitespace
- **`parse_last_updated`**: tries multiple date formats; raises error if all fail
- **`check_ids_not_empty`** (model_validator): runs after all fields are set — catches whitespace-only IDs that pass `min_length=1`

### Why `_cleanse()` and `InventoryRecord` overlap
Both handle negatives, batch_number defaults, and date parsing. This is an **intentional double safety net**:
- `_cleanse()` handles bulk data efficiently with PySpark before `collect()`
- `InventoryRecord` catches anything that slips through, row by row

---

## MongoDB / loader.py

### Connection Pooling
- Reuses a fixed set of connections instead of opening/closing one per operation
- `MongoClient(maxPoolSize=10)` keeps up to 10 connections ready in the pool
- Without pooling: connect → write → disconnect (repeated every time = slow)
- With pooling: borrow from pool → write → return to pool (fast)

### PySpark is NOT directly connected to MongoDB
```
PySpark (_cleanse) → collect() → Python list → pymongo (loader.py) → MongoDB
```
- Connection pooling is a **pymongo feature**, not PySpark
- PySpark's job ends at `collect()` — after that, pymongo takes over

### bulk_write
- Inserts documents in batches of 500 (`BATCH_SIZE = 500`) for memory efficiency
- Uses `ordered=False` so one failure doesn't stop the rest of the batch
- Duplicate `inventory_id` entries are caught by a unique index and counted as `failed`

---

## Phase 0: Scaffold & Docker Architecture

### Why per-service Dockerfiles over a monolithic image
- The original monolithic Dockerfile installed Java + Node.js + build-essential — ~2GB of unnecessary deps per service
- Each microservice only needs `python:3.12-slim` (~150MB) + its pip dependencies
- Independent builds mean one service change doesn't rebuild everything
- Health checks can be service-specific (`/health` per container)

### PYTHONPATH trick for shared modules in containers
- All services import `from src.shared.database import get_db`
- In Docker, we copy `src/shared/` into each container and set `PYTHONPATH=/app`
- This means imports resolve as `src.shared.database` from `/app/src/shared/database.py`
- No code changes needed — same imports work locally and in containers

### Docker Compose networking
- Services communicate by container name (e.g., `auth:8001`, `mongo:27017`)
- The `depends_on` with `condition: service_healthy` prevents race conditions on startup
- `context: .` with `dockerfile: src/auth/Dockerfile` lets COPY use project-root-relative paths

### API Gateway (nginx) as reverse proxy
- Routes `/auth/*` to auth:8001, `/products/*` to product:8002, etc.
- Handles CORS at the gateway level (single point of configuration)
- No authentication enforcement at gateway level — each service handles its own JWT verification
- Duplicate location blocks (with/without trailing slash) prevent 301 redirects that lose POST bodies

### Vector DB Adapter Pattern
- Abstract `VectorStore` class in `src/shared/vector_store.py`
- Concrete `QdrantStore` implementation (stub in Phase 0, real in Phase 3)
- Factory function `get_vector_store()` switches backend via `VECTOR_STORE_BACKEND` env var
- Satisfies checklist requirement: "Can you swap your Vector DB without rewriting the core API?"

### Connection pooling (from database.py)
- `MongoClient(maxPoolSize=10)` reuses connections across requests
- The singleton pattern (`_client: MongoClient | None`) ensures one pool per process
- Each container gets its own pool (separate processes, separate connection pools)

---

## Milestone 2: API Testing Strategy

### mongomock + monkeypatch パターン
- `mongomock` はpymongoのインメモリ互換実装。`find`, `insert_one`, `$inc`, `$push`, `$pull` 等の主要操作をサポート
- テスト時に本番DBへ接続不要 → Docker不要で高速（26テスト 3.8秒）
- `monkeypatch.setattr("src.auth.routes.get_db", lambda: db)` で各モジュールの `get_db` を差替え
- **なぜモジュール毎にpatchするのか**: Pythonの `from X import Y` は関数オブジェクトへの参照コピー。`src.shared.database.get_db` だけpatchしても、既にimport済みの `src.auth.routes.get_db` は元の参照のまま。だから全importモジュールをpatchする必要がある

### conftest.py のfixture連鎖設計
```
test関数 → product_client(mock_db) → mock_db(monkeypatch)
```
- `product_client` が `mock_db` に依存することで、テスト側が明示的に `mock_db` を要求しなくてもDBが自動的にモック化される
- テストがDB直接操作（シードデータ挿入）したい場合は `mock_db` もfixture引数に追加。pytestはスコープ内でfixtureをキャッシュするので同一インスタンスが渡される

### FastAPI HTTPBearer の認証レスポンス
- `HTTPBearer()` はAuthorizationヘッダー無しで **401 Unauthorized** を返す（403ではない）
- FastAPIの旧バージョンでは403だったが、現バージョンはHTTP仕様に準拠して401
- テスト作成時にこの差に注意

### JWT InsecureKeyLengthWarning
- テスト環境のデフォルト `JWT_SECRET_KEY="changeme-in-production"` は22バイト
- PyJWTはSHA256用に最低32バイトを推奨 → 警告が出る
- 本番では十分な長さのキーを使えば解消。テストでは無視して問題なし

### E2Eテスト vs 単体テスト — 何が違うのか
- **単体テスト**: `mock_db.products.insert_one(...)` でDBにシードデータを直接入れ、1エンドポイントだけ叩く。テスト対象は「そのエンドポイントの振る舞い」
- **E2Eテスト**: APIだけを通じてデータを作成する。Register→LoginでJWT取得→そのJWTでProduct作成→CartにそのproductIdを追加→Order確定。テスト対象は「サービス間のデータフロー全体」
- 4つの `TestClient` が同じ `mock_db` インスタンスを共有 → 本番の「複数コンテナがMongoDB共有」アーキテクチャを再現
- E2Eで在庫チェックのレースコンディションも模擬: カート内数量を直接DB更新で在庫超過させ、注文時の検証ロジックが機能するか確認

### シードデータの冪等性パターン
- `find_one({"product_id": ...})` で存在チェック → 既存ならスキップ、なければ挿入
- 何度実行しても安全（冪等）。CI/CDや開発環境リセット時に便利
- デモユーザーもシードに含めることで、`docker compose up` → `seed` → すぐにAPIテスト可能

### Mermaid sequenceDiagram でサービスフロー文書化
- `sequenceDiagram` は横軸にアクター（Client, Gateway, 各Service, DB）、縦軸に時系列でリクエスト/レスポンスを表現
- APIのデータフローを可視化するのに最適。コードレビューやオンボーディング資料として使える
- `Note over C,DB:` でフェーズ（認証、商品閲覧、カート、注文）を区切ると読みやすい

---

## Milestone 3: Semantic Search（Multi-Agent + Hybrid Search）

### OpenAI Agents SDK の基本構造
- `pip install openai-agents` でインストール。`from agents import Agent, Runner, function_tool`
- **Agent**: `name`, `instructions`, `tools`, `model`, `output_type` を持つ。LLMの振る舞いを定義
- **Runner.run(agent, input)**: async実行。`RunResult.final_output` で結果を取得
- **@function_tool**: Python関数をAgentが呼べるツールに変換。docstringが自動的にtool descriptionになる
- **output_type**: `Agent(output_type=PydanticModel)` を指定すると、LLMがstructured outputを返す。plain textではなくPydanticモデルのインスタンスが `final_output` に入る

### @function_tool のテスタビリティ問題と解決策
- `@function_tool` で装飾された関数は `FunctionTool` オブジェクトになる
- 内部の `on_invoke_tool` は `(ctx: ToolContext, input: str)` シグネチャに変換されるため、直接呼び出しが困難
- **解決策**: ビジネスロジックを `_search_products_impl()` に分離し、`@function_tool` はそれを呼ぶだけのラッパーにする
- テストでは `_search_products_impl()` を直接呼び出し、embedding/vector storeをmockする

### Hybrid Search の実装パターン
- **Hybrid Search** = semantic vector search + structured payload filter を組み合わせた検索
- Qdrantの `query_points()` に `query_filter` を渡すことで、サーバー側で同時実行される
- フィルタ構築: `filters` dictを受け取り、`FieldCondition` + `Range`/`MatchValue` に変換
- `VectorStore` ABC の `search()` に `filters: dict | None` 引数を追加（Phase 0のスタブから拡張）

### Embedding の設計判断
- **対象フィールド**: `f"{name}. {category}. {description}"` — 意味的なフィールドのみ
- **price/stock**: embedding対象外。Qdrant payload に格納してフィルタ/ソート用に使う
- **理由**: embeddingはセマンティック類似度を捉える。数値の大小比較は embedding の得意領域ではない。「5000円」と「4999円」はembedding空間で近いとは限らない
- **バッチ処理**: indexing時は `get_embeddings(texts: list)` でまとめてAPI呼び出し（1件ずつ呼ぶより効率的）

### 価格クエリの3パターン処理
| パターン | 処理方法 | 実装状態 |
|---|---|---|
| 明示的価格（「5000円以下」）| Query Parserで数値抽出 → Qdrant Range filter | MVP実装済み |
| 曖昧な価格意図（「安いもの」）| sort_by_price: "asc"（Qdrant検索後にクライアントサイドソート）| MVP実装済み |
| 他通貨（「50ドル」）| MVPではJPYのみ対応 | Future Work |

### Query Parser Agent のプロンプト設計
- `output_type=ParsedQuery` を使うことで、LLMに特定のJSON構造を強制できる
- instructionsにルールと具体例を記載すると精度が上がる
- `semantic_query` から価格情報を除去するルールが重要（「赤いドレスで5000円以下」→ semantic_query="赤いドレス"）
- model は `gpt-4o-mini` で十分（構造化パースはシンプルなタスク）

### Index スクリプトの設計（Option B）
- 3つの選択肢を検討: A) seed.pyに組込み、B) 独立スクリプト、C) API呼び出し時
- **Option B を採用**: `python -m src.product.index` で独立実行
- **理由**: seedとindexは責務が異なる（DB初期化 vs ベクトルDB同期）。独立させることで再indexが容易
- `ensure_collection()` + `upsert()` で冪等実行可能（何度実行しても安全）

### Qdrant のポイントID制約
- Qdrant は unsigned integer か UUID のみをポイントIDとして受け付ける（文字列不可）
- `product_id` が `"p-001"` のような文字列の場合、`uuid.uuid5(namespace, product_id)` で決定論的UUIDに変換
- 同じproduct_idは常に同じUUIDにマッピングされるため、upsertの冪等性が保たれる

### recommend レスポンスの構造化（仕様準拠）
- 仕様書Section 5: レスポンスに query, model_version, top 5 products, image URLs, similarity score を含める要件
- 元の実装は Search Agent の自然言語テキストのみ返していた
- 解決: `_search_products_structured()` で構造化dict（product_id, name, price, similarity_score等）を返す関数を追加
- `recommend()` が `_search_products_structured()`（構造化データ） + Search Agent（NLテキスト）の両方を返す
- 2層構造: `_search_products_structured()` → `_search_products_impl()` はテキストフォーマットのラッパー

---

## Frontend: Vite + React in Docker

### Vite dev server を Docker + nginx で配信するパターン
- Vite dev server はデフォルトで `localhost` にバインド → Docker内からアクセス不可
- `server.host: '0.0.0.0'` を設定することでコンテナ外（nginx）からアクセス可能に
- nginx の `location /` catch-all で frontend:5173 にプロキシ → `http://localhost` でアクセス

### Vite HMR（Hot Module Replacement）と WebSocket
- Vite は WebSocket (`ws://`) を使ってブラウザにファイル変更を通知する
- nginx を経由する場合、WebSocket ヘッダーが必要:
  ```
  proxy_set_header Upgrade $http_upgrade;
  proxy_set_header Connection "upgrade";
  proxy_http_version 1.1;
  ```
- これがないとHMRが無言で失敗し、ファイル変更がブラウザに反映されない

### volume mount でホットリロード
- `docker-compose.yml` で `./src/frontend/src:/app/src` をマウント
- ホスト側でソースを編集すると、コンテナ内のViteが検知してHMRで即時反映
- `node_modules/` はマウントしない（コンテナ内の `npm install` 結果を使う）

### API呼び出しの同一オリジン戦略
- `API_BASE = ''`（空文字）で全APIリクエストが同一オリジン経由
- nginx が `/auth/*`, `/products/*`, `/cart/*` を各バックエンドサービスにプロキシ
- CORS問題が発生しない（全て同じ `http://localhost:80` から配信）

### 認証状態管理（Router不使用パターン）
- 2〜4画面程度なら React Router を入れず、`useState` による条件分岐で十分
- `token` state が null → LoginForm、あり → Navbar + ページコンポーネント
- ページ切替も `page` state（'products' | 'search' | 'cart'）で管理
- 401レスポンス時に `clearToken()` + state リセットで自動ログアウト

### ローカルにNode.js未インストールでも開発可能
- Docker コンテナ内で `npm install` + `vite` を実行
- ソースファイルは volume mount でホストと共有
- `package-lock.json` はコンテナ内で生成される（ホスト側にはない）
