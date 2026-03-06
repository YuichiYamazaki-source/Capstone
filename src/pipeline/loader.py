"""
loader.py
Loads validated inventory documents into MongoDB using connection pooling
and bulk_write for efficiency.
"""

import logging
import os

from pymongo import MongoClient, InsertOne
from pymongo.errors import BulkWriteError

logger = logging.getLogger(__name__)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB", "commerce")
COLLECTION_NAME = "inventory"
BATCH_SIZE = 500


def _get_client() -> MongoClient:
    """
    Returns a MongoClient with connection pooling.
    maxPoolSize controls concurrent connections — tuned for pipeline workload.
    """
    return MongoClient(
        MONGO_URI,
        maxPoolSize=10,
        serverSelectionTimeoutMS=5000,
    )


def load(docs: list[dict]) -> dict:
    """
    Bulk-inserts documents into MongoDB.
    Skips duplicates (inventory_id) via upsert if collection already has data.
    Returns a summary dict with inserted / failed counts.
    """
    if not docs:
        logger.warning("No documents to load.")
        return {"inserted": 0, "failed": 0}

    client = _get_client()
    try:
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]

        # Ensure unique index on inventory_id to prevent duplicates
        collection.create_index("inventory_id", unique=True, background=True)

        inserted_total = 0
        failed_total = 0

        # Process in batches for memory efficiency
        for i in range(0, len(docs), BATCH_SIZE):
            batch = docs[i : i + BATCH_SIZE]
            requests = [InsertOne(doc) for doc in batch]

            try:
                result = collection.bulk_write(requests, ordered=False)
                inserted_total += result.inserted_count
                logger.info(
                    f"Batch {i // BATCH_SIZE + 1}: inserted {result.inserted_count} documents"
                )
            except BulkWriteError as bwe:
                inserted_total += bwe.details.get("nInserted", 0)
                failed_total += len(bwe.details.get("writeErrors", []))
                logger.warning(
                    f"Batch {i // BATCH_SIZE + 1}: {bwe.details.get('nInserted', 0)} inserted, "
                    f"{len(bwe.details.get('writeErrors', []))} failed (likely duplicates)"
                )

        logger.info(f"Load complete: {inserted_total} inserted, {failed_total} failed")
        return {"inserted": inserted_total, "failed": failed_total}

    finally:
        client.close()


if __name__ == "__main__":
    logging.basicConfig(
        format='{"time": "%(asctime)s", "level": "%(levelname)s", "module": "%(module)s", "message": "%(message)s"}',
        level=logging.INFO,
    )
    from src.pipeline.ingest import run_ingestion

    docs = run_ingestion()
    result = load(docs)
    logger.info(f"Final result: {result}")
