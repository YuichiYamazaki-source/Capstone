"""
test_e2e.py
End-to-end integration test: Auth → Product → Cart → Order

Unlike the unit tests (test_auth.py etc.) that test one endpoint at a time,
this test walks through the entire user journey in a single flow to verify
that data propagates correctly across services through the shared MongoDB.

Architecture note:
  In production, each service runs in its own container but shares MongoDB.
  Here we replicate that by using 4 separate TestClient instances (one per
  FastAPI app) all pointing at the same mongomock database via conftest.py.
"""


class TestPurchaseFlow:
    """Full user journey: register → login → create product → add to cart → place order."""

    def test_full_purchase_flow(
        self, auth_client, product_client, cart_client, order_client, mock_db
    ):
        # ── Step 1: Register ──
        resp = auth_client.post("/auth/register", json={
            "email": "e2e@example.com",
            "password": "securepass123",
            "name": "E2E User",
        })
        assert resp.status_code == 201
        user_id = resp.json()["user_id"]

        # ── Step 2: Login → get JWT ──
        resp = auth_client.post("/auth/login", json={
            "email": "e2e@example.com",
            "password": "securepass123",
        })
        assert resp.status_code == 200
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # ── Step 3: Create product ──
        resp = product_client.post("/products/", json={
            "name": "E2E Sneaker",
            "description": "Limited edition test sneaker",
            "category": "footwear",
            "price": 120.0,
            "available_stock": 5,
        }, headers=headers)
        assert resp.status_code == 201
        product_id = resp.json()["product_id"]

        # ── Step 4: Verify product is listed ──
        resp = product_client.get("/products/", headers=headers)
        assert resp.status_code == 200
        assert any(p["product_id"] == product_id for p in resp.json())

        # ── Step 5: Add to cart ──
        resp = cart_client.post("/cart/items", json={
            "product_id": product_id,
            "quantity": 2,
        }, headers=headers)
        assert resp.status_code == 201

        # ── Step 6: Verify cart contents ──
        resp = cart_client.get("/cart/", headers=headers)
        assert resp.status_code == 200
        cart = resp.json()
        assert len(cart["items"]) == 1
        assert cart["items"][0]["product_id"] == product_id
        assert cart["items"][0]["quantity"] == 2

        # ── Step 7: Place order ──
        resp = order_client.post("/orders/", headers=headers)
        assert resp.status_code == 201
        order = resp.json()
        assert order["status"] == "confirmed"
        assert order["payment_status"] == "paid"
        assert order["total"] == 240.0  # 120.0 * 2

        # ── Step 8: Verify side effects ──
        # Stock should have decremented: 5 - 2 = 3
        product = mock_db.products.find_one({"product_id": product_id})
        assert product["available_stock"] == 3

        # Cart should be empty
        cart_doc = mock_db.carts.find_one({"user_id": user_id})
        assert cart_doc is None

        # Order should appear in order list
        resp = order_client.get("/orders/", headers=headers)
        assert resp.status_code == 200
        orders = resp.json()
        assert len(orders) == 1
        assert orders[0]["total"] == 240.0


class TestPurchaseFlowEdgeCases:
    """Edge cases in the purchase flow."""

    def test_cannot_order_more_than_stock(
        self, auth_client, product_client, cart_client, order_client, mock_db
    ):
        # Register + login
        auth_client.post("/auth/register", json={
            "email": "edge@example.com",
            "password": "securepass123",
            "name": "Edge User",
        })
        resp = auth_client.post("/auth/login", json={
            "email": "edge@example.com",
            "password": "securepass123",
        })
        headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}

        # Create product with only 1 in stock
        resp = product_client.post("/products/", json={
            "name": "Rare Item",
            "description": "Very limited",
            "category": "collectible",
            "price": 500.0,
            "available_stock": 1,
        }, headers=headers)
        product_id = resp.json()["product_id"]

        # Add 1 to cart (within stock) — succeeds
        resp = cart_client.post("/cart/items", json={
            "product_id": product_id,
            "quantity": 1,
        }, headers=headers)
        assert resp.status_code == 201

        # Manually update cart quantity to exceed stock (simulating race condition)
        mock_db.carts.update_one(
            {"items.product_id": product_id},
            {"$set": {"items.$.quantity": 3}},
        )

        # Order should fail — stock check at order time catches this
        resp = order_client.post("/orders/", headers=headers)
        assert resp.status_code == 400
        assert "Insufficient stock" in resp.json()["detail"]

        # Stock should remain unchanged
        product = mock_db.products.find_one({"product_id": product_id})
        assert product["available_stock"] == 1
