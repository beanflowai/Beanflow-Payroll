"""
API tests for authentication endpoints.

Tests:
- GET /api/v1/auth/me (get current user info)
- POST /api/v1/auth/logout (logout)
"""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestGetCurrentUserInfo:
    """Tests for GET /api/v1/auth/me endpoint."""

    def test_get_current_user_info_success(self, client: TestClient):
        """Successfully get current user information."""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "data" in data
        assert "success" in data
        assert data["success"] is True

        user_data = data["data"]
        assert "id" in user_data
        assert "email" in user_data


class TestLogout:
    """Tests for POST /api/v1/auth/logout endpoint."""

    def test_logout_success(self, client: TestClient):
        """Successfully logout (client-side logout with server logging)."""
        response = client.post("/api/v1/auth/logout")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "data" in data
        assert "success" in data
        assert data["success"] is True
        assert data["data"]["message"] == "Logged out successfully"
