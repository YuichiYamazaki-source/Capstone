"""
conftest.py
Shared fixtures for API tests.

Strategy:
  - mongomock provides an in-memory MongoDB drop-in replacement
  - monkeypatch swaps get_db() in every module that imports it
  - Each TestClient fixture depends on mock_db so patching is guaranteed
  - auth_header fixture generates a valid JWT for protected endpoints
"""

import mongomock
import pytest
from fastapi.testclient import TestClient

from src.shared.jwt import create_token

# Every module that does `from src.shared.database import get_db`
_DB_MODULES = [
    "src.shared.database",
    "src.auth.routes",
    "src.product.routes",
    "src.cart.routes",
    "src.order.routes",
]


@pytest.fixture()
def mock_db(monkeypatch):
    """In-memory MongoDB via mongomock, patched into all service modules."""
    client = mongomock.MongoClient()
    db = client["test_commerce"]

    for mod in _DB_MODULES:
        monkeypatch.setattr(f"{mod}.get_db", lambda: db)

    yield db
    client.close()


# --------------- TestClient fixtures ---------------


@pytest.fixture()
def auth_client(mock_db):
    from src.auth.main import app
    return TestClient(app)


@pytest.fixture()
def product_client(mock_db):
    from src.product.main import app
    return TestClient(app)


@pytest.fixture()
def cart_client(mock_db):
    from src.cart.main import app
    return TestClient(app)


@pytest.fixture()
def order_client(mock_db):
    from src.order.main import app
    return TestClient(app)


# --------------- Auth helpers ---------------


@pytest.fixture()
def auth_header():
    """Valid JWT header for user_id='test-user-id'."""
    token = create_token("test-user-id")
    return {"Authorization": f"Bearer {token}"}
