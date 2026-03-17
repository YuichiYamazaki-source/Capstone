import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import settings

logger = logging.getLogger("ai-service.clients.mongodb")

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def connect_db() -> None:
    """Initialize the MongoDB connection and verify access."""
    global _client, _db
    _client = AsyncIOMotorClient(
        settings.mongo_uri,
        serverSelectionTimeoutMS=5000,
        socketTimeoutMS=10000,
        connectTimeoutMS=5000,
    )
    _db = _client[settings.mongo_db]
    count = await _db.courses.count_documents({})
    logger.info(
        "MongoDB connected",
        extra={"database": settings.mongo_db, "courses_count": count},
    )


async def close_db() -> None:
    """Close the MongoDB connection and release resources."""
    global _client, _db
    if _client is not None:
        _client.close()
        _client = None
        _db = None
        logger.info("MongoDB connection closed")


def get_db() -> AsyncIOMotorDatabase:
    """Return the active MongoDB database instance.

    Returns:
        The AsyncIOMotorDatabase instance.

    Raises:
        RuntimeError: If connect_db() has not been called.
    """
    if _db is None:
        raise RuntimeError("MongoDB not connected. Call connect_db() first.")
    return _db
