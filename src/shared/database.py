"""
database.py
Shared MongoDB client factory used across all microservices.
"""

import os

from pymongo import MongoClient
from pymongo.database import Database

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB", "commerce")

_client: MongoClient | None = None


def get_db() -> Database:
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI, maxPoolSize=10, serverSelectionTimeoutMS=5000)
    return _client[DB_NAME]
