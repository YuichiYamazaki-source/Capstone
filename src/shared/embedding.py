"""
embedding.py
OpenAI embedding client for semantic search.
Model: text-embedding-3-small (1536 dimensions)

Singleton pattern: OpenAI client is lazily initialized on first call.
Requires OPENAI_API_KEY environment variable.

Used by:
  - src/product/index.py  → get_embeddings() for batch indexing
  - src/product/agents.py → get_embedding() for query-time search
"""

import os

from openai import OpenAI

MODEL = "text-embedding-3-small"
VECTOR_SIZE = 1536

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


def get_embedding(text: str) -> list[float]:
    """Generate embedding for a single text."""
    resp = _get_client().embeddings.create(input=[text], model=MODEL)
    return resp.data[0].embedding


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for multiple texts (batch)."""
    resp = _get_client().embeddings.create(input=texts, model=MODEL)
    return [item.embedding for item in resp.data]
