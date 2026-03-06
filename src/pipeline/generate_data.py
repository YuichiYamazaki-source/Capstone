"""
generate_data.py
Generates synthetic inventory CSV to simulate remote storage.
Intentionally includes dirty rows (nulls, bad types) to demonstrate cleansing.
"""

import csv
import logging
import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

logging.basicConfig(
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "module": "%(module)s", "message": "%(message)s"}',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

OUTPUT_PATH = Path("/app/data/inventory_raw.csv")

WAREHOUSES = ["WH-001", "WH-002", "WH-003", "WH-004"]

COLUMNS = [
    "inventory_id",
    "product_id",
    "warehouse_id",
    "available_stock",
    "reserved_stock",
    "damaged_stock",
    "reorder_level",
    "last_updated",
    "batch_number",
]


def random_date(days_back: int = 90) -> str:
    base = datetime.now(timezone.utc) - timedelta(days=random.randint(0, days_back))
    return base.strftime("%Y-%m-%d %H:%M:%S")


def make_clean_row() -> dict:
    return {
        "inventory_id": str(uuid.uuid4()),
        "product_id": str(uuid.uuid4()),
        "warehouse_id": random.choice(WAREHOUSES),
        "available_stock": random.randint(0, 500),
        "reserved_stock": random.randint(0, 50),
        "damaged_stock": random.randint(0, 10),
        "reorder_level": random.randint(10, 100),
        "last_updated": random_date(),
        "batch_number": f"BATCH-{random.randint(1000, 9999)}",
    }


def make_dirty_rows() -> list[dict]:
    """Returns intentionally malformed rows to test cleansing logic."""
    dirty = []

    # Missing inventory_id (should be dropped)
    row = make_clean_row()
    row["inventory_id"] = ""
    dirty.append(row)

    # Missing product_id (should be dropped)
    row = make_clean_row()
    row["product_id"] = ""
    dirty.append(row)

    # Non-numeric stock value (should be coerced / dropped)
    row = make_clean_row()
    row["available_stock"] = "N/A"
    dirty.append(row)

    # Negative stock (should be coerced to 0)
    row = make_clean_row()
    row["available_stock"] = -5
    row["reserved_stock"] = -2
    dirty.append(row)

    # Missing batch_number (optional — should be filled with default)
    row = make_clean_row()
    row["batch_number"] = ""
    dirty.append(row)

    # Malformed date (should be handled gracefully)
    row = make_clean_row()
    row["last_updated"] = "not-a-date"
    dirty.append(row)

    return dirty


def generate(n_clean: int = 200) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    rows = [make_clean_row() for _ in range(n_clean)]
    dirty = make_dirty_rows()

    # Scatter dirty rows randomly within clean rows
    for d in dirty:
        pos = random.randint(0, len(rows))
        rows.insert(pos, d)

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    total = len(rows)
    logger.info(f"Generated {total} rows ({n_clean} clean + {len(dirty)} dirty) → {OUTPUT_PATH}")


if __name__ == "__main__":
    generate()
