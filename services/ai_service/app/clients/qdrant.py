import logging

from qdrant_client import QdrantClient

from app.config import settings

logger = logging.getLogger("ai-service.clients.qdrant")

_client: QdrantClient | None = None


def get_qdrant_client() -> QdrantClient:
    """Return the Qdrant client, initializing it on first call.

    Returns:
        The singleton QdrantClient instance.
    """
    global _client
    if _client is None:
        _client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            timeout=10,
            prefer_grpc=True,
        )
        logger.info(
            "Qdrant client initialized",
            extra={
                "host": settings.qdrant_host,
                "port": settings.qdrant_port,
            },
        )
    return _client


def close_qdrant_client() -> None:
    """Close the Qdrant client connection and release resources."""
    global _client
    if _client is not None:
        _client.close()
        _client = None
        logger.info("Qdrant client closed")
