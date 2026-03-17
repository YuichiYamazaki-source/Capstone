"""Generate dense + BM25 sparse vectors for courses and store in Qdrant.

Usage:
    python scripts/generate_embeddings.py [--batch-size N] [--concurrency N]

Creates a Qdrant collection with two named vectors:
  - "dense": OpenAI text-embedding-3-small (semantic search)
  - "bm25":  Qdrant built-in BM25 sparse vectors (keyword search)

Qdrant's Query API performs server-side RRF fusion of both at search time.

Requires: OPENAI_API_KEY, MONGO_URI, QDRANT_HOST in environment or local/.env
"""

import argparse
import asyncio
import logging
import sys
import uuid

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pymongo import MongoClient
from qdrant_client import QdrantClient, models

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("embeddings")

# Defaults
MONGO_URI = "mongodb://localhost:27017"
MONGO_DB = "course_finder"
COLLECTION = "courses"
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
QDRANT_COLLECTION = "courses"
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536


def build_dense_text(doc: dict) -> str:
    """Build text for dense embedding (semantic understanding).

    Title + description capture conceptual meaning.
    """
    parts = []
    if doc.get("title"):
        parts.append(doc["title"])
    if doc.get("description"):
        parts.append(doc["description"])
    return " | ".join(parts)


def build_bm25_text(doc: dict) -> str:
    """Build text for BM25 sparse vector (keyword matching).

    Title + skills provide exact-term matching surface.
    Description is included for broader keyword coverage.
    """
    parts = []
    if doc.get("title"):
        parts.append(doc["title"])
    if doc.get("description"):
        parts.append(doc["description"])
    skills = doc.get("skills", [])
    if skills:
        parts.append(" ".join(skills))
    return " ".join(parts)


async def generate_dense_embeddings(
    texts: list[str],
    client: AsyncOpenAI,
    batch_size: int = 50,
    concurrency: int = 5,
) -> list[list[float]]:
    """Generate dense embeddings in parallel batches using AsyncOpenAI.

    Uses asyncio.Semaphore to limit concurrent API calls.

    Args:
        texts: List of text strings to embed.
        client: AsyncOpenAI client instance.
        batch_size: Number of texts per API call.
        concurrency: Maximum concurrent API calls.

    Returns:
        List of embedding vectors (one per input text).
    """
    semaphore = asyncio.Semaphore(concurrency)
    results: dict[int, list[list[float]]] = {}

    async def embed_batch(batch_idx: int, batch: list[str]):
        async with semaphore:
            logger.info(
                "Dense embedding batch %d (size: %d)",
                batch_idx,
                len(batch),
            )
            response = await client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=batch,
            )
            embeddings = [item.embedding for item in response.data]
            results[batch_idx] = embeddings
            logger.info(
                "Batch %d done (tokens: %d)",
                batch_idx,
                response.usage.total_tokens,
            )

    # Create tasks for all batches
    tasks = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        batch_idx = i // batch_size
        tasks.append(embed_batch(batch_idx, batch))

    # Run all batches with concurrency control
    await asyncio.gather(*tasks)

    # Reassemble in order
    all_embeddings = []
    for idx in range(len(tasks)):
        all_embeddings.extend(results[idx])

    return all_embeddings


async def async_main(args):
    """Async entry point for embedding generation."""
    load_dotenv(args.env_file)

    # --- MongoDB: load courses ---
    mongo_client = MongoClient(args.mongo_uri)
    db = mongo_client[args.mongo_db]
    courses = list(db[COLLECTION].find({}))
    logger.info("Loaded %d courses from MongoDB", len(courses))

    if not courses:
        logger.warning("No courses found. Run ingest_courses.py first.")
        return

    # --- Build texts ---
    valid_courses = []
    dense_texts = []
    bm25_texts = []
    for course in courses:
        dt = build_dense_text(course)
        bt = build_bm25_text(course)
        if dt.strip():
            valid_courses.append(course)
            dense_texts.append(dt)
            bm25_texts.append(bt)

    logger.info("Valid courses: %d", len(valid_courses))

    # --- Generate dense embeddings via OpenAI (parallel) ---
    openai_client = AsyncOpenAI()
    dense_embeddings = await generate_dense_embeddings(
        dense_texts,
        openai_client,
        batch_size=args.batch_size,
        concurrency=args.concurrency,
    )
    logger.info("Dense embeddings generated: %d", len(dense_embeddings))

    # --- Create Qdrant collection with dense + BM25 sparse ---
    qdrant = QdrantClient(host=args.qdrant_host, port=args.qdrant_port)

    existing = [c.name for c in qdrant.get_collections().collections]
    if QDRANT_COLLECTION in existing:
        qdrant.delete_collection(QDRANT_COLLECTION)
        logger.info("Deleted existing collection '%s'", QDRANT_COLLECTION)

    qdrant.create_collection(
        collection_name=QDRANT_COLLECTION,
        vectors_config={
            "dense": models.VectorParams(
                size=EMBEDDING_DIM,
                distance=models.Distance.COSINE,
            ),
        },
        sparse_vectors_config={
            "bm25": models.SparseVectorParams(
                modifier=models.Modifier.IDF,
            ),
        },
    )
    logger.info(
        "Created collection '%s' (dense: %d-dim cosine, bm25: sparse IDF)",
        QDRANT_COLLECTION,
        EMBEDDING_DIM,
    )

    # --- Build and upsert points ---
    batch_size = 50
    for i in range(0, len(valid_courses), batch_size):
        batch_courses = valid_courses[i : i + batch_size]
        batch_dense = dense_embeddings[i : i + batch_size]
        batch_bm25 = bm25_texts[i : i + batch_size]

        points = []
        for course, dense_vec, bm25_text in zip(
            batch_courses,
            batch_dense,
            batch_bm25,
            strict=True,
        ):
            point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, str(course["_id"])))
            points.append(
                models.PointStruct(
                    id=point_id,
                    vector={
                        "dense": dense_vec,
                        "bm25": models.Document(
                            text=bm25_text,
                            model="Qdrant/bm25",
                        ),
                    },
                    payload={
                        "mongo_id": str(course["_id"]),
                        "title": course.get("title", ""),
                        "organization": course.get("organization", ""),
                        "level": course.get("level", ""),
                        "rating": course.get("rating"),
                        "skills": course.get("skills", []),
                        "url": course.get("url"),
                    },
                ),
            )

        qdrant.upsert(collection_name=QDRANT_COLLECTION, points=points)
        logger.info("Upserted batch %d-%d", i, i + len(points))

    # --- Verify ---
    info = qdrant.get_collection(QDRANT_COLLECTION)
    logger.info(
        "Done: %d points in '%s' (status: %s)",
        info.points_count,
        QDRANT_COLLECTION,
        info.status,
    )

    mongo_client.close()


def main():
    """CLI entry point for generating course embeddings."""
    parser = argparse.ArgumentParser(
        description="Generate course embeddings (dense + BM25) and store in Qdrant",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Embedding batch size (default: 50)",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=5,
        help="Max concurrent embedding API calls (default: 5)",
    )
    parser.add_argument("--mongo-uri", default=MONGO_URI)
    parser.add_argument("--mongo-db", default=MONGO_DB)
    parser.add_argument("--qdrant-host", default=QDRANT_HOST)
    parser.add_argument("--qdrant-port", type=int, default=QDRANT_PORT)
    parser.add_argument("--env-file", default="local/.env")
    args = parser.parse_args()

    asyncio.run(async_main(args))


if __name__ == "__main__":
    main()
