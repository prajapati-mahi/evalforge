import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "ok")

def test_login_demo_user():
    response = client.post("/api/v1/auth/login", json={
        "email": "demo@evalforge.dev",
        "password": "evalforge123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "demo@evalforge.dev"

def test_login_invalid_password():
    response = client.post("/api/v1/auth/login", json={
        "email": "demo@evalforge.dev",
        "password": "wrongpassword"
    })
    assert response.status_code == 401
