"""
schema.py
Pydantic model for INVENTORY collection.
Validates each row before MongoDB insertion.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class InventoryRecord(BaseModel):
    inventory_id: str = Field(..., min_length=1)
    product_id: str = Field(..., min_length=1)
    warehouse_id: str = Field(..., min_length=1)
    available_stock: int = Field(..., ge=0)
    reserved_stock: int = Field(..., ge=0)
    damaged_stock: int = Field(..., ge=0)
    reorder_level: int = Field(..., ge=0)
    last_updated: datetime
    batch_number: str = Field(default="UNKNOWN")

    @field_validator("available_stock", "reserved_stock", "damaged_stock", "reorder_level", mode="before")
    @classmethod
    def coerce_non_negative_int(cls, v):
        """Cast to int and clamp negatives to 0."""
        try:
            val = int(float(str(v)))
            return max(val, 0)
        except (ValueError, TypeError):
            raise ValueError(f"Cannot convert '{v}' to a non-negative integer")

    @field_validator("batch_number", mode="before")
    @classmethod
    def default_batch_number(cls, v):
        if not v or str(v).strip() == "":
            return "UNKNOWN"
        return str(v).strip()

    @field_validator("last_updated", mode="before")
    @classmethod
    def parse_last_updated(cls, v):
        if isinstance(v, datetime):
            return v
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(str(v), fmt)
            except ValueError:
                continue
        raise ValueError(f"Cannot parse date: '{v}'")

    @model_validator(mode="after")
    def check_ids_not_empty(self):
        if not self.inventory_id.strip():
            raise ValueError("inventory_id must not be empty")
        if not self.product_id.strip():
            raise ValueError("product_id must not be empty")
        return self

    def to_mongo_doc(self) -> dict:
        """Return a dict suitable for MongoDB insertion."""
        return {
            "inventory_id": self.inventory_id,
            "product_id": self.product_id,
            "warehouse_id": self.warehouse_id,
            "available_stock": self.available_stock,
            "reserved_stock": self.reserved_stock,
            "damaged_stock": self.damaged_stock,
            "reorder_level": self.reorder_level,
            "last_updated": self.last_updated,
            "batch_number": self.batch_number,
        }
