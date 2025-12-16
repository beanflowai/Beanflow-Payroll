"""Tests for health check endpoint"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client"""
    from app.main import app

    return TestClient(app)


def test_health_check(client: TestClient):
    """Test health check endpoint returns healthy status"""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "healthy"
    assert "version" in data["data"]
