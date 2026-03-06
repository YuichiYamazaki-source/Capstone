"""
ingest.py
PySpark-based ingestion pipeline.

Flow:
  1. Read CSV from local path (M1) — swap for Azure Blob in future milestones
  2. Cleanse: drop critical nulls, cast types, clamp negatives
  3. Validate each row with Pydantic schema
  4. Return validated records for loading

Future Azure Blob swap:
  Replace _read_csv() with a download from azure-storage-blob,
  then pass the local temp path to spark.read.csv().
"""

import logging
import os
from pathlib import Path
from typing import Iterator

from pydantic import ValidationError
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import (
    IntegerType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

from src.pipeline.schema import InventoryRecord

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CSV_PATH = os.getenv("INVENTORY_CSV_PATH", "/app/data/inventory_raw.csv")

RAW_SCHEMA = StructType([
    StructField("inventory_id",   StringType(), nullable=True),
    StructField("product_id",     StringType(), nullable=True),
    StructField("warehouse_id",   StringType(), nullable=True),
    StructField("available_stock",StringType(), nullable=True),  # read as string → cast later
    StructField("reserved_stock", StringType(), nullable=True),
    StructField("damaged_stock",  StringType(), nullable=True),
    StructField("reorder_level",  StringType(), nullable=True),
    StructField("last_updated",   StringType(), nullable=True),
    StructField("batch_number",   StringType(), nullable=True),
])

REQUIRED_COLS = ["inventory_id", "product_id", "warehouse_id"]
INT_COLS = ["available_stock", "reserved_stock", "damaged_stock", "reorder_level"]


# ---------------------------------------------------------------------------
# Spark session factory
# ---------------------------------------------------------------------------

def _get_spark() -> SparkSession:
    return (
        SparkSession.builder
        .appName("InventoryIngestion")
        .master("local[*]")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )


# ---------------------------------------------------------------------------
# Pipeline stages
# ---------------------------------------------------------------------------

def _read_csv(spark: SparkSession, path: str) -> DataFrame:
    logger.info(f"Reading CSV from: {path}")
    df = spark.read.csv(path, header=True, schema=RAW_SCHEMA)
    return df


def _cleanse(df: DataFrame) -> DataFrame:
    """
    Cleansing steps:
    1. Drop rows where required fields are null or empty string.
    2. Cast stock columns to IntegerType (non-parseable → null → dropped).
    3. Clamp negative stock values to 0.
    4. Parse last_updated to TimestampType (bad dates → null → dropped).
    5. Fill missing batch_number with 'UNKNOWN'.
    """

    # Step 1: Drop rows with missing required fields
    for col in REQUIRED_COLS:
        df = df.filter(F.col(col).isNotNull() & (F.trim(F.col(col)) != ""))

    # Step 2: Cast stock columns — unparseable → null
    for col in INT_COLS:
        df = df.withColumn(col, F.col(col).cast(IntegerType()))

    # Step 3: Clamp negatives to 0 and drop rows where cast failed (null)
    for col in INT_COLS:
        df = df.filter(F.col(col).isNotNull())
        df = df.withColumn(col, F.greatest(F.col(col), F.lit(0)))

    # Step 4: Parse timestamp — invalid dates → null → dropped
    df = df.withColumn("last_updated", F.to_timestamp(F.col("last_updated"), "yyyy-MM-dd HH:mm:ss"))
    df = df.filter(F.col("last_updated").isNotNull())

    # Step 5: Fill missing batch_number
    df = df.withColumn(
        "batch_number",
        F.when(F.col("batch_number").isNull() | (F.trim(F.col("batch_number")) == ""), F.lit("UNKNOWN"))
        .otherwise(F.trim(F.col("batch_number")))
    )

    return df


def _validate(df: DataFrame) -> tuple[list[dict], list[dict]]:
    """
    Validate each cleansed row with Pydantic.
    Returns (valid_docs, invalid_rows).
    """
    rows = df.collect()
    valid_docs: list[dict] = []
    invalid_rows: list[dict] = []

    for row in rows:
        raw = row.asDict()
        try:
            record = InventoryRecord(**raw)
            valid_docs.append(record.to_mongo_doc())
        except ValidationError as e:
            logger.warning({"message": "Validation failed", "row": raw, "errors": e.errors()})
            invalid_rows.append(raw)

    logger.info(f"Validation complete: {len(valid_docs)} valid, {len(invalid_rows)} invalid")
    return valid_docs, invalid_rows


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_ingestion(csv_path: str = CSV_PATH) -> list[dict]:
    """
    Executes the full ingestion pipeline.
    Returns a list of validated MongoDB-ready documents.
    """
    spark = _get_spark()
    try:
        df_raw = _read_csv(spark, csv_path)
        df_clean = _cleanse(df_raw)
        valid_docs, invalid_rows = _validate(df_clean)

        if invalid_rows:
            logger.warning(f"{len(invalid_rows)} rows failed Pydantic validation and were skipped")

        return valid_docs
    finally:
        spark.stop()


if __name__ == "__main__":
    logging.basicConfig(
        format='{"time": "%(asctime)s", "level": "%(levelname)s", "module": "%(module)s", "message": "%(message)s"}',
        level=logging.INFO,
    )
    docs = run_ingestion()
    logger.info(f"Pipeline complete. {len(docs)} documents ready for MongoDB.")
