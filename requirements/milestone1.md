# Milestone 1 — Inventory Data Engineering with PySpark

**Marks**: 40 | **Deadline**: 2026-02-27

---

## Tasks

| # | Task | Status |
|---|------|--------|
| 1 | Connect to remote storage and load inventory dataset using PySpark | Done |
| 2 | Perform data cleansing and schema validation | Done |
| 3 | Transform dataset to structured MongoDB schema | Done |
| 4 | Load processed inventory data into MongoDB | Done |

---

## Deliverables Checklist

- [x] PySpark ingestion script — `src/pipeline/ingest.py`
- [x] Synthetic data generator — `src/pipeline/generate_data.py`
- [x] Pydantic schema validation — `src/pipeline/schema.py`
- [x] MongoDB loader — `src/pipeline/loader.py`
- [x] Schema validation documentation — `docs/data-flow/ingestion_flow.md`
- [x] Execution logs (JSON structured) — written to `logs/pipeline.log`
- [x] Automated tests — `tests/test_pipeline.py`

---

## MongoDB Schema: INVENTORY Collection

| Field | Type | Notes |
|-------|------|-------|
| inventory_id | String | Primary key, unique index |
| product_id | String | Foreign key → PRODUCTS |
| warehouse_id | String | |
| available_stock | Integer | ≥ 0 |
| reserved_stock | Integer | ≥ 0 |
| damaged_stock | Integer | ≥ 0 |
| reorder_level | Integer | ≥ 0 |
| last_updated | DateTime | UTC |
| batch_number | String | Default: "UNKNOWN" |

---

## How to Run

```bash
# 1. Start containers
docker compose up -d

# 2. Enter app container
docker exec -it fde-learning bash

# 3. Generate synthetic CSV
python -m src.pipeline.generate_data

# 4. Run full pipeline (ingest + load)
python -m src.pipeline.loader

# 5. Run tests
pytest tests/test_pipeline.py -v
```
