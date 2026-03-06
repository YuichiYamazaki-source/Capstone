"""
index.py
Index all products from MongoDB into Qdrant for semantic search.

Pipeline:
  1. Fetch all products from MongoDB (products collection)
  2. Build embedding text: f"{name}. {category}. {description}"
     - Only semantic fields; price/stock go in Qdrant payload for filtering
  3. Call OpenAI text-embedding-3-small API (batched, BATCH_SIZE=50)
  4. Upsert into Qdrant with payload (price, category, stock, etc.)

Usage:
    python -m src.product.index          (from project root, needs .env)
    PYTHONPATH=/app python -m src.product.index  (inside Docker)

Design decision (ADR):
  - Option B chosen: Separate index script (not embedded in seed or API).
  - Re-runnable: calling ensure_collection() + upsert() is idempotent.
"""

from dotenv import load_dotenv

load_dotenv()

from src.shared.database import get_db
from src.shared.embedding import get_embeddings, VECTOR_SIZE
from src.shared.logging import setup_logger
from src.shared.vector_store import get_vector_store

logger = setup_logger("indexer")

COLLECTION = "products"
BATCH_SIZE = 50


def build_text(product: dict) -> str:
    """Build embedding text from product fields."""
    return f"{product['name']}. {product['category']}. {product['description']}"


def index_products():
    """Fetch all products from MongoDB and upsert into Qdrant."""
    db = get_db()
    store = get_vector_store()

    # Ensure collection exists
    store.ensure_collection(COLLECTION, VECTOR_SIZE)

    products = list(db.products.find({}, {"_id": 0}))
    if not products:
        logger.warning("no products found in MongoDB")
        return

    logger.info("indexing %d products", len(products))

    # Process in batches
    for i in range(0, len(products), BATCH_SIZE):
        batch = products[i : i + BATCH_SIZE]
        texts = [build_text(p) for p in batch]
        embeddings = get_embeddings(texts)

        ids = [p["product_id"] for p in batch]
        payloads = [
            {
                "product_id": p["product_id"],
                "name": p["name"],
                "category": p["category"],
                "price": p["price"],
                "available_stock": p["available_stock"],
                "description": p["description"],
                "image_url": p.get("image_url", ""),
            }
            for p in batch
        ]

        count = store.upsert(COLLECTION, ids, embeddings, payloads)
        logger.info("batch %d-%d: upserted %d points", i, i + len(batch), count)

    logger.info("indexing complete: %d products", len(products))


if __name__ == "__main__":
    index_products()
