"""
test_cart.py
Cart Service API tests: add item, get cart, remove item
"""


def _seed_product(db, product_id="p1", stock=10):
    """Insert a product into the mock DB for cart tests."""
    db.products.insert_one({
        "product_id": product_id,
        "name": "Test Shoe",
        "price": 50.0,
        "available_stock": stock,
    })


class TestAddItem:
    def test_success(self, cart_client, auth_header, mock_db):
        _seed_product(mock_db)
        resp = cart_client.post(
            "/cart/items",
            json={"product_id": "p1", "quantity": 2},
            headers=auth_header,
        )
        assert resp.status_code == 201
        assert resp.json()["message"] == "Item added to cart"

    def test_quantity_increments_on_duplicate(self, cart_client, auth_header, mock_db):
        _seed_product(mock_db)
        cart_client.post("/cart/items", json={"product_id": "p1", "quantity": 1}, headers=auth_header)
        cart_client.post("/cart/items", json={"product_id": "p1", "quantity": 3}, headers=auth_header)

        resp = cart_client.get("/cart/", headers=auth_header)
        items = resp.json()["items"]
        assert len(items) == 1
        assert items[0]["quantity"] == 4  # 1 + 3

    def test_insufficient_stock(self, cart_client, auth_header, mock_db):
        _seed_product(mock_db, stock=1)
        resp = cart_client.post(
            "/cart/items",
            json={"product_id": "p1", "quantity": 5},
            headers=auth_header,
        )
        assert resp.status_code == 400

    def test_product_not_found(self, cart_client, auth_header):
        resp = cart_client.post(
            "/cart/items",
            json={"product_id": "nonexistent", "quantity": 1},
            headers=auth_header,
        )
        assert resp.status_code == 404


class TestGetCart:
    def test_empty_cart(self, cart_client, auth_header):
        resp = cart_client.get("/cart/", headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["items"] == []

    def test_cart_with_items(self, cart_client, auth_header, mock_db):
        _seed_product(mock_db)
        cart_client.post("/cart/items", json={"product_id": "p1", "quantity": 2}, headers=auth_header)

        resp = cart_client.get("/cart/", headers=auth_header)
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 1
        assert items[0]["product_id"] == "p1"
        assert items[0]["quantity"] == 2


class TestRemoveItem:
    def test_success(self, cart_client, auth_header, mock_db):
        _seed_product(mock_db)
        cart_client.post("/cart/items", json={"product_id": "p1", "quantity": 1}, headers=auth_header)
        resp = cart_client.delete("/cart/items/p1", headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["message"] == "Item removed from cart"

    def test_cart_not_found(self, cart_client, auth_header):
        resp = cart_client.delete("/cart/items/nonexistent", headers=auth_header)
        assert resp.status_code == 404
