"""
test_recommend.py
Tests for the semantic search recommendation feature (M3).

Tests cover:
  - ParsedQuery structured output model validation
  - _search_products_structured with mocked embedding + vector store
  - _search_products_impl text formatting
  - POST /products/recommend endpoint (mocked agents)
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from src.product.agents import (
    ParsedQuery,
    _search_products_structured,
    _search_products_impl,
)


# ---------------------------------------------------------------------------
# ParsedQuery model tests
# ---------------------------------------------------------------------------
class TestParsedQuery:
    def test_full_query(self):
        pq = ParsedQuery(
            semantic_query="赤いドレス",
            price_max=5000,
            category="ドレス",
        )
        assert pq.semantic_query == "赤いドレス"
        assert pq.price_max == 5000
        assert pq.price_min is None
        assert pq.sort_by_price is None
        assert pq.category == "ドレス"

    def test_minimal_query(self):
        pq = ParsedQuery(semantic_query="shoes")
        assert pq.semantic_query == "shoes"
        assert pq.price_min is None
        assert pq.price_max is None

    def test_sort_by_price(self):
        pq = ParsedQuery(semantic_query="Tシャツ", sort_by_price="asc")
        assert pq.sort_by_price == "asc"

    def test_price_range(self):
        pq = ParsedQuery(semantic_query="jacket", price_min=3000, price_max=8000)
        assert pq.price_min == 3000
        assert pq.price_max == 8000


# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------
FAKE_RESULTS = [
    {
        "id": "prod-1",
        "score": 0.95,
        "payload": {
            "product_id": "prod-1",
            "name": "Red Dress",
            "category": "ドレス",
            "price": 4500,
            "available_stock": 10,
            "description": "Beautiful red dress",
            "image_url": "/static/images/red-dress.jpg",
        },
    },
    {
        "id": "prod-2",
        "score": 0.85,
        "payload": {
            "product_id": "prod-2",
            "name": "Blue Dress",
            "category": "ドレス",
            "price": 6000,
            "available_stock": 5,
            "description": "Elegant blue dress",
            "image_url": "/static/images/blue-dress.jpg",
        },
    },
]


# ---------------------------------------------------------------------------
# _search_products_structured tests (returns list[dict])
# ---------------------------------------------------------------------------
class TestSearchProductsStructured:
    """Test _search_products_structured with mocked embedding + vector store."""

    @pytest.fixture(autouse=True)
    def mock_deps(self):
        fake_vector = [0.1] * 1536
        mock_store = MagicMock()
        mock_store.search.return_value = list(FAKE_RESULTS)

        with (
            patch("src.product.agents.get_embedding", return_value=fake_vector),
            patch("src.product.agents.get_vector_store", return_value=mock_store),
        ):
            self.mock_store = mock_store
            yield

    def test_returns_list_of_dicts(self):
        products = _search_products_structured("赤いドレス")
        assert isinstance(products, list)
        assert len(products) == 2

    def test_product_fields(self):
        products = _search_products_structured("赤いドレス")
        p = products[0]
        assert p["product_id"] == "prod-1"
        assert p["name"] == "Red Dress"
        assert p["category"] == "ドレス"
        assert p["price"] == 4500
        assert p["image_url"] == "/static/images/red-dress.jpg"
        assert p["similarity_score"] == 0.95
        assert p["available_stock"] == 10

    def test_with_price_filter(self):
        _search_products_structured("ドレス", price_max=5000)
        call_kwargs = self.mock_store.search.call_args.kwargs
        assert call_kwargs["filters"] == {"price_max": 5000}

    def test_with_price_range(self):
        _search_products_structured("ドレス", price_min=3000, price_max=8000)
        call_kwargs = self.mock_store.search.call_args.kwargs
        assert call_kwargs["filters"] == {"price_min": 3000, "price_max": 8000}

    def test_sort_asc(self):
        products = _search_products_structured("ドレス", sort_by_price="asc")
        assert products[0]["price"] <= products[1]["price"]

    def test_sort_desc(self):
        products = _search_products_structured("ドレス", sort_by_price="desc")
        assert products[0]["price"] >= products[1]["price"]

    def test_no_results(self):
        self.mock_store.search.return_value = []
        products = _search_products_structured("nonexistent")
        assert products == []

    def test_with_category(self):
        _search_products_structured("ドレス", category="ドレス")
        call_kwargs = self.mock_store.search.call_args.kwargs
        assert call_kwargs["filters"]["category"] == "ドレス"

    def test_no_filters_when_none(self):
        _search_products_structured("ドレス")
        call_kwargs = self.mock_store.search.call_args.kwargs
        assert call_kwargs["filters"] is None


# ---------------------------------------------------------------------------
# _search_products_impl tests (text formatting)
# ---------------------------------------------------------------------------
class TestSearchProductsImpl:
    """Test _search_products_impl text output (delegates to _search_products_structured)."""

    @pytest.fixture(autouse=True)
    def mock_deps(self):
        fake_vector = [0.1] * 1536
        mock_store = MagicMock()
        mock_store.search.return_value = list(FAKE_RESULTS)

        with (
            patch("src.product.agents.get_embedding", return_value=fake_vector),
            patch("src.product.agents.get_vector_store", return_value=mock_store),
        ):
            self.mock_store = mock_store
            yield

    def test_basic_search_text(self):
        result = _search_products_impl("赤いドレス")
        assert "Red Dress" in result
        assert "4,500" in result

    def test_no_results_text(self):
        self.mock_store.search.return_value = []
        result = _search_products_impl("nonexistent")
        assert "No products found" in result

    def test_sort_asc_text(self):
        result = _search_products_impl("ドレス", sort_by_price="asc")
        lines = result.strip().split("\n")
        assert "4,500" in lines[0]
        assert "6,000" in lines[1]

    def test_sort_desc_text(self):
        result = _search_products_impl("ドレス", sort_by_price="desc")
        lines = result.strip().split("\n")
        assert "6,000" in lines[0]
        assert "4,500" in lines[1]


# ---------------------------------------------------------------------------
# Endpoint tests (mocked agent pipeline)
# ---------------------------------------------------------------------------
class TestRecommendEndpoint:
    def test_recommend_success(self, product_client, auth_header):
        mock_return = {
            "query": "赤いドレスで5000円以下",
            "model_version": "text-embedding-3-small",
            "recommendations": "Found 2 products: Red Dress, Blue Dress",
            "products": [
                {
                    "product_id": "prod-1",
                    "name": "Red Dress",
                    "category": "ドレス",
                    "price": 4500,
                    "image_url": "/static/images/red-dress.jpg",
                    "description": "Beautiful red dress",
                    "available_stock": 10,
                    "similarity_score": 0.95,
                },
            ],
        }
        with patch("src.product.routes.recommend", new_callable=AsyncMock) as mock_rec:
            mock_rec.return_value = mock_return

            resp = product_client.post(
                "/products/recommend",
                json={"query": "赤いドレスで5000円以下"},
                headers=auth_header,
            )

            assert resp.status_code == 200
            data = resp.json()
            assert data["query"] == "赤いドレスで5000円以下"
            assert data["model_version"] == "text-embedding-3-small"
            assert "recommendations" in data
            assert len(data["products"]) == 1
            assert data["products"][0]["similarity_score"] == 0.95
            mock_rec.assert_called_once_with("赤いドレスで5000円以下")

    def test_recommend_unauthorized(self, product_client):
        resp = product_client.post(
            "/products/recommend",
            json={"query": "ドレス"},
        )
        assert resp.status_code == 401

    def test_recommend_empty_query(self, product_client, auth_header):
        resp = product_client.post(
            "/products/recommend",
            json={"query": ""},
            headers=auth_header,
        )
        assert resp.status_code == 422
