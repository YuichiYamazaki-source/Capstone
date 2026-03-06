"""
test_product.py
Product Service API tests: create, list, get
"""

SAMPLE_PRODUCT = {
    "name": "Test Shoe",
    "description": "A comfortable test shoe",
    "category": "footwear",
    "price": 99.99,
    "available_stock": 10,
}


class TestCreateProduct:
    def test_success(self, product_client, auth_header):
        resp = product_client.post("/products/", json=SAMPLE_PRODUCT, headers=auth_header)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Test Shoe"
        assert "product_id" in data

    def test_unauthorized(self, product_client):
        resp = product_client.post("/products/", json=SAMPLE_PRODUCT)
        assert resp.status_code == 401


class TestListProducts:
    def test_returns_in_stock_only(self, product_client, auth_header, mock_db):
        mock_db.products.insert_many([
            {
                "product_id": "p1", "name": "In Stock", "description": "d",
                "category": "c", "price": 10, "available_stock": 5, "image_url": "",
            },
            {
                "product_id": "p2", "name": "Out of Stock", "description": "d",
                "category": "c", "price": 10, "available_stock": 0, "image_url": "",
            },
        ])
        resp = product_client.get("/products/", headers=auth_header)
        assert resp.status_code == 200
        products = resp.json()
        assert len(products) == 1
        assert products[0]["name"] == "In Stock"

    def test_empty_catalogue(self, product_client, auth_header):
        resp = product_client.get("/products/", headers=auth_header)
        assert resp.status_code == 200
        assert resp.json() == []


class TestGetProduct:
    def test_success(self, product_client, auth_header, mock_db):
        mock_db.products.insert_one({
            "product_id": "p1", "name": "Shoe", "description": "d",
            "category": "c", "price": 50, "available_stock": 3, "image_url": "",
        })
        resp = product_client.get("/products/p1", headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Shoe"

    def test_not_found(self, product_client, auth_header):
        resp = product_client.get("/products/nonexistent", headers=auth_header)
        assert resp.status_code == 404
