"""
test_auth.py
Auth Service API tests: register + login
"""


class TestRegister:
    def test_success(self, auth_client):
        resp = auth_client.post("/auth/register", json={
            "email": "test@example.com",
            "password": "securepass123",
            "name": "Test User",
        })
        assert resp.status_code == 201
        assert "user_id" in resp.json()

    def test_duplicate_email(self, auth_client):
        payload = {
            "email": "dup@example.com",
            "password": "securepass123",
            "name": "Dup",
        }
        auth_client.post("/auth/register", json=payload)
        resp = auth_client.post("/auth/register", json=payload)
        assert resp.status_code == 400
        assert "already registered" in resp.json()["detail"]

    def test_short_password_rejected(self, auth_client):
        resp = auth_client.post("/auth/register", json={
            "email": "short@example.com",
            "password": "abc",
            "name": "Short",
        })
        assert resp.status_code == 422  # Pydantic validation


class TestLogin:
    def _register(self, client, email="login@example.com"):
        client.post("/auth/register", json={
            "email": email,
            "password": "securepass123",
            "name": "Login User",
        })

    def test_success(self, auth_client):
        self._register(auth_client)
        resp = auth_client.post("/auth/login", json={
            "email": "login@example.com",
            "password": "securepass123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_wrong_password(self, auth_client):
        self._register(auth_client)
        resp = auth_client.post("/auth/login", json={
            "email": "login@example.com",
            "password": "wrongpassword",
        })
        assert resp.status_code == 401

    def test_nonexistent_email(self, auth_client):
        resp = auth_client.post("/auth/login", json={
            "email": "noone@example.com",
            "password": "anypassword",
        })
        assert resp.status_code == 401
