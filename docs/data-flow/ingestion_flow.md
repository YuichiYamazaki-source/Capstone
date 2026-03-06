# Data Flow: Inventory Ingestion Pipeline (Milestone 1)

## Overview

This document describes the logical data movement from the source (remote storage)
through PySpark processing into MongoDB.

---

## Flow Diagram

```
[Remote Storage]
   inventory_raw.csv
   (local: /app/data/  |  future: Azure Blob wasbs://)
         │
         │  spark.read.csv()
         ▼
[PySpark: Raw DataFrame]
   - Schema enforced (all columns as StringType initially)
   - Row count logged
         │
         │  _cleanse()
         ▼
[PySpark: Cleansed DataFrame]
   1. Drop rows: inventory_id / product_id / warehouse_id null or empty
   2. Cast: available_stock, reserved_stock, damaged_stock, reorder_level → IntegerType
   3. Drop rows: cast failed (non-numeric stock values)
   4. Clamp: negative integers → 0
   5. Parse: last_updated → TimestampType (bad dates dropped)
   6. Fill:  batch_number empty → "UNKNOWN"
         │
         │  df.collect() → row-by-row Pydantic validation
         ▼
[Pydantic: InventoryRecord]
   - Type coercion + constraint checks
   - Invalid rows logged as WARNING, excluded
         │
         │  bulk_write() in batches of 500
         ▼
[MongoDB: commerce.inventory]
   - Unique index on inventory_id (prevents duplicates on re-run)
   - Insert count & error count logged
         │
         ▼
[logs/pipeline.log]
   - JSON structured log at each stage
```

---

## Error Handling

| Error type | Behaviour |
|------------|-----------|
| Missing required field (inventory_id / product_id) | Row dropped at PySpark filter stage |
| Non-numeric stock value | Cast to null → row dropped |
| Bad date format | `to_timestamp` returns null → row dropped |
| Pydantic ValidationError | Row logged as WARNING, excluded from load |
| MongoDB BulkWriteError (duplicate key) | Logged as WARNING, remaining batch continues |
| MongoDB connection failure | Exception propagated, pipeline exits with error |

---

## Future: Azure Blob Storage

To switch from local CSV to Azure Blob:

1. Install `azure-storage-blob` (uncomment in `requirements.txt`)
2. Add env vars: `AZURE_STORAGE_CONNECTION_STRING`, `AZURE_BLOB_CONTAINER`, `AZURE_BLOB_NAME`
3. In `ingest.py`, replace `_read_csv()` with:

```python
from azure.storage.blob import BlobServiceClient
import tempfile

def _download_from_blob(path: str) -> str:
    conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    container = os.getenv("AZURE_BLOB_CONTAINER")
    blob_name = os.getenv("AZURE_BLOB_NAME")
    client = BlobServiceClient.from_connection_string(conn_str)
    blob = client.get_blob_client(container=container, blob=blob_name)
    tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
    tmp.write(blob.download_blob().readall())
    tmp.close()
    return tmp.name
```

All downstream stages (cleanse, validate, load) remain unchanged.
