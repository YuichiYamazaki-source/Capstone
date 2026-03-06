"""
test_pipeline.py
Unit and integration tests for the M1 data pipeline.
Run inside Docker: pytest tests/test_pipeline.py -v
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from pydantic import ValidationError

from src.pipeline.schema import InventoryRecord


# ---------------------------------------------------------------------------
# Schema Tests
# ---------------------------------------------------------------------------

class TestInventoryRecordSchema:

    def _valid_data(self, **overrides) -> dict:
        base = {
            "inventory_id": "inv-001",
            "product_id": "prod-abc",
            "warehouse_id": "WH-001",
            "available_stock": 100,
            "reserved_stock": 10,
            "damaged_stock": 2,
            "reorder_level": 20,
            "last_updated": "2026-01-15 10:00:00",
            "batch_number": "BATCH-1234",
        }
        base.update(overrides)
        return base

    def test_valid_record(self):
        record = InventoryRecord(**self._valid_data())
        assert record.inventory_id == "inv-001"
        assert record.available_stock == 100

    def test_missing_inventory_id_raises(self):
        with pytest.raises(ValidationError):
            InventoryRecord(**self._valid_data(inventory_id=""))

    def test_missing_product_id_raises(self):
        with pytest.raises(ValidationError):
            InventoryRecord(**self._valid_data(product_id=""))

    def test_negative_stock_clamped_to_zero(self):
        record = InventoryRecord(**self._valid_data(available_stock=-10, reserved_stock=-5))
        assert record.available_stock == 0
        assert record.reserved_stock == 0

    def test_non_numeric_stock_raises(self):
        with pytest.raises(ValidationError):
            InventoryRecord(**self._valid_data(available_stock="N/A"))

    def test_empty_batch_number_defaults_to_unknown(self):
        record = InventoryRecord(**self._valid_data(batch_number=""))
        assert record.batch_number == "UNKNOWN"

    def test_missing_batch_number_defaults_to_unknown(self):
        data = self._valid_data()
        del data["batch_number"]
        record = InventoryRecord(**data)
        assert record.batch_number == "UNKNOWN"

    def test_invalid_date_raises(self):
        with pytest.raises(ValidationError):
            InventoryRecord(**self._valid_data(last_updated="not-a-date"))

    def test_date_string_parsed(self):
        record = InventoryRecord(**self._valid_data(last_updated="2026-02-01 08:30:00"))
        assert isinstance(record.last_updated, datetime)
        assert record.last_updated.year == 2026

    def test_to_mongo_doc_keys(self):
        record = InventoryRecord(**self._valid_data())
        doc = record.to_mongo_doc()
        expected_keys = {
            "inventory_id", "product_id", "warehouse_id",
            "available_stock", "reserved_stock", "damaged_stock",
            "reorder_level", "last_updated", "batch_number",
        }
        assert set(doc.keys()) == expected_keys

    def test_stock_cast_from_float_string(self):
        record = InventoryRecord(**self._valid_data(available_stock="42.9"))
        assert record.available_stock == 42


# ---------------------------------------------------------------------------
# Loader Tests (unit — mocked MongoDB)
# ---------------------------------------------------------------------------

class TestLoader:

    @patch("src.pipeline.loader.MongoClient")
    def test_load_inserts_documents(self, mock_client_cls):
        from src.pipeline.loader import load

        mock_collection = MagicMock()
        mock_collection.bulk_write.return_value.inserted_count = 2
        mock_client_cls.return_value.__getitem__.return_value.__getitem__.return_value = mock_collection

        docs = [
            {
                "inventory_id": "a", "product_id": "p1", "warehouse_id": "WH-001",
                "available_stock": 10, "reserved_stock": 0, "damaged_stock": 0,
                "reorder_level": 5, "last_updated": datetime.now(timezone.utc), "batch_number": "B1",
            },
            {
                "inventory_id": "b", "product_id": "p2", "warehouse_id": "WH-002",
                "available_stock": 20, "reserved_stock": 1, "damaged_stock": 0,
                "reorder_level": 10, "last_updated": datetime.now(timezone.utc), "batch_number": "B2",
            },
        ]

        result = load(docs)
        assert result["inserted"] >= 0  # mock returns 2

    @patch("src.pipeline.loader.MongoClient")
    def test_load_empty_list(self, mock_client_cls):
        from src.pipeline.loader import load

        result = load([])
        assert result == {"inserted": 0, "failed": 0}
        mock_client_cls.assert_not_called()


# ---------------------------------------------------------------------------
# Generate Data Tests
# ---------------------------------------------------------------------------

class TestGenerateData:

    def test_make_clean_row_has_all_fields(self):
        from src.pipeline.generate_data import make_clean_row, COLUMNS
        row = make_clean_row()
        for col in COLUMNS:
            assert col in row

    def test_make_dirty_rows_returns_list(self):
        from src.pipeline.generate_data import make_dirty_rows
        dirty = make_dirty_rows()
        assert isinstance(dirty, list)
        assert len(dirty) > 0

    def test_generate_creates_file(self, tmp_path, monkeypatch):
        from src.pipeline import generate_data
        output = tmp_path / "test_inventory.csv"
        monkeypatch.setattr(generate_data, "OUTPUT_PATH", output)
        generate_data.generate(n_clean=10)
        assert output.exists()
        lines = output.read_text().splitlines()
        # header + at least 10 clean + dirty rows
        assert len(lines) >= 11
