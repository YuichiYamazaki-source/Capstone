"""
vector_store.py
Abstract Vector DB adapter. Defaults to Qdrant.
Swappable via VECTOR_STORE_BACKEND environment variable.

Checklist requirement: "Can you swap your Vector DB without rewriting the core API?"
→ Yes. Implement a new subclass of VectorStore and add it to get_vector_store().
"""
import os
import uuid
from abc import ABC, abstractmethod

# Namespace UUID for deterministic product_id → UUID5 conversion.
# Qdrant requires point IDs to be unsigned integers or UUIDs.
_NAMESPACE = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")


class VectorStore(ABC):
    """Interface for vector similarity search backends."""

    @abstractmethod
    def upsert(
        self,
        collection: str,
        ids: list[str],
        vectors: list[list[float]],
        payloads: list[dict] | None = None,
    ) -> int:
        ...

    @abstractmethod
    def search(
        self,
        collection: str,
        query_vector: list[float],
        limit: int = 10,
        filters: dict | None = None,
    ) -> list[dict]:
        ...

    @abstractmethod
    def ensure_collection(self, collection: str, vector_size: int) -> None:
        ...


class QdrantStore(VectorStore):
    """Qdrant implementation using qdrant-client.

    Supports Hybrid Search via the `filters` parameter in search():
      - price_min/price_max → Qdrant Range filter on "price" payload field
      - category → Qdrant MatchValue filter on "category" payload field
      - Vector similarity (cosine) + payload filters run server-side in Qdrant

    Imports are deferred (inside methods) to avoid ImportError when
    qdrant-client is not installed (e.g., in auth/cart/order services).
    """

    def __init__(self):
        from qdrant_client import QdrantClient

        self.host = os.getenv("QDRANT_HOST", "localhost")
        self.port = int(os.getenv("QDRANT_PORT", "6333"))
        self.client = QdrantClient(host=self.host, port=self.port)

    def ensure_collection(self, collection: str, vector_size: int) -> None:
        from qdrant_client.models import Distance, VectorParams

        collections = [c.name for c in self.client.get_collections().collections]
        if collection not in collections:
            self.client.create_collection(
                collection_name=collection,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )

    def upsert(self, collection, ids, vectors, payloads=None):
        from qdrant_client.models import PointStruct

        points = [
            PointStruct(
                id=str(uuid.uuid5(_NAMESPACE, idx)),
                vector=vec,
                payload=payloads[i] if payloads else {},
            )
            for i, (idx, vec) in enumerate(zip(ids, vectors))
        ]
        self.client.upsert(collection_name=collection, points=points)
        return len(points)

    def search(self, collection, query_vector, limit=10, filters=None):
        from qdrant_client.models import Filter, FieldCondition, Range

        qdrant_filter = None
        if filters:
            conditions = []
            if filters.get("price_min") is not None:
                conditions.append(
                    FieldCondition(key="price", range=Range(gte=filters["price_min"]))
                )
            if filters.get("price_max") is not None:
                conditions.append(
                    FieldCondition(key="price", range=Range(lte=filters["price_max"]))
                )
            if filters.get("category"):
                from qdrant_client.models import MatchValue

                conditions.append(
                    FieldCondition(key="category", match=MatchValue(value=filters["category"]))
                )
            if conditions:
                qdrant_filter = Filter(must=conditions)

        results = self.client.query_points(
            collection_name=collection,
            query=query_vector,
            limit=limit,
            query_filter=qdrant_filter,
            with_payload=True,
        )
        return [
            {"id": hit.id, "score": hit.score, "payload": hit.payload}
            for hit in results.points
        ]


def get_vector_store() -> VectorStore:
    """Factory: returns the configured vector store backend."""
    backend = os.getenv("VECTOR_STORE_BACKEND", "qdrant")
    if backend == "qdrant":
        return QdrantStore()
    raise ValueError(f"Unknown vector store backend: {backend}")
