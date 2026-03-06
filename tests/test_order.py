"""
test_order.py
Order Service API tests: create order, list orders
"""


def _seed_cart_and_product(db, user_id="test-user-id", stock=10, quantity=2):
    """Pre-populate a product and a cart for order tests."""
    db.products.insert_one({
        "product_id": "p1",
        "name": "Test Shoe",
        "price": 50.0,
        "available_stock": stock,
    })
    db.carts.insert_one({
        "user_id": user_id,
        "items": [{"product_id": "p1", "name": "Test Shoe", "price": 50.0, "quantity": quantity}],
    })


class TestCreateOrder:
    def test_success(self, order_client, auth_header, mock_db):
        _seed_cart_and_product(mock_db, quantity=2, stock=10)

        resp = order_client.post("/orders/", headers=auth_header)
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "confirmed"
        assert data["payment_status"] == "paid"
        assert data["total"] == 100.0  # 50.0 * 2

        # Stock should be decremented
        product = mock_db.products.find_one({"product_id": "p1"})
        assert product["available_stock"] == 8

        # Cart should be cleared
        cart = mock_db.carts.find_one({"user_id": "test-user-id"})
        assert cart is None

    def test_empty_cart(self, order_client, auth_header):
        resp = order_client.post("/orders/", headers=auth_header)
        assert resp.status_code == 400
        assert "empty" in resp.json()["detail"].lower()

    def test_insufficient_stock(self, order_client, auth_header, mock_db):
        _seed_cart_and_product(mock_db, stock=1, quantity=5)

        resp = order_client.post("/orders/", headers=auth_header)
        assert resp.status_code == 400
        assert "Insufficient stock" in resp.json()["detail"]

    def test_product_removed_after_cart(self, order_client, auth_header, mock_db):
        """Product deleted between cart add and order — should fail."""
        mock_db.carts.insert_one({
            "user_id": "test-user-id",
            "items": [{"product_id": "ghost", "name": "Ghost", "price": 10, "quantity": 1}],
        })
        resp = order_client.post("/orders/", headers=auth_header)
        assert resp.status_code == 400
        assert "not found" in resp.json()["detail"]


class TestListOrders:
    def test_empty(self, order_client, auth_header):
        resp = order_client.get("/orders/", headers=auth_header)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_user_orders(self, order_client, auth_header, mock_db):
        mock_db.orders.insert_one({
            "user_id": "test-user-id",
            "items": [{"product_id": "p1", "name": "Shoe", "price": 50.0, "quantity": 1}],
            "total": 50.0,
            "status": "confirmed",
            "payment_status": "paid",
        })
        resp = order_client.get("/orders/", headers=auth_header)
        assert resp.status_code == 200
        orders = resp.json()
        assert len(orders) == 1
        assert orders[0]["total"] == 50.0
