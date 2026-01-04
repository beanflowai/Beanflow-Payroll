"""Tests for authentication service."""

from unittest.mock import MagicMock, patch

import pytest

from app.models.auth import UserResponse
from app.services.auth_service import AuthService, auth_service


class TestAuthServiceVerifyToken:
    """Tests for AuthService.verify_token method."""

    def test_verify_token_calls_verify_supabase_jwt(self):
        """Test that verify_token delegates to verify_supabase_jwt."""
        with patch(
            "app.services.auth_service.verify_supabase_jwt"
        ) as mock_verify:
            mock_verify.return_value = {"sub": "user-123", "email": "test@example.com"}

            result = AuthService.verify_token("fake-token")

            mock_verify.assert_called_once_with("fake-token")
            assert result == {"sub": "user-123", "email": "test@example.com"}

    def test_verify_token_returns_none_for_invalid_token(self):
        """Test that verify_token returns None for invalid tokens."""
        with patch(
            "app.services.auth_service.verify_supabase_jwt"
        ) as mock_verify:
            mock_verify.return_value = None

            result = AuthService.verify_token("invalid-token")

            assert result is None


class TestAuthServiceGetUserFromPayload:
    """Tests for AuthService.get_user_from_payload method."""

    def test_basic_payload_extraction(self):
        """Test extracting user info from basic JWT payload."""
        payload = {
            "sub": "user-123",
            "email": "test@example.com",
        }

        result = AuthService.get_user_from_payload(payload)

        assert isinstance(result, UserResponse)
        assert result.id == "user-123"
        assert result.email == "test@example.com"
        assert result.full_name is None
        assert result.avatar_url is None

    def test_payload_with_user_metadata(self):
        """Test extracting user info with user_metadata."""
        payload = {
            "sub": "user-456",
            "email": "john@example.com",
            "user_metadata": {
                "full_name": "John Doe",
                "avatar_url": "https://example.com/avatar.png",
            },
        }

        result = AuthService.get_user_from_payload(payload)

        assert result.id == "user-456"
        assert result.email == "john@example.com"
        assert result.full_name == "John Doe"
        assert result.avatar_url == "https://example.com/avatar.png"

    def test_payload_with_alternative_metadata_keys(self):
        """Test extracting user info with alternative metadata keys (name, picture)."""
        payload = {
            "sub": "user-789",
            "email": "jane@example.com",
            "user_metadata": {
                "name": "Jane Smith",
                "picture": "https://example.com/jane.png",
            },
        }

        result = AuthService.get_user_from_payload(payload)

        assert result.full_name == "Jane Smith"
        assert result.avatar_url == "https://example.com/jane.png"

    def test_empty_payload(self):
        """Test extracting user info from empty payload."""
        payload = {}

        result = AuthService.get_user_from_payload(payload)

        assert result.id == ""
        assert result.email is None
        assert result.full_name is None
        assert result.avatar_url is None


class TestAuthServiceGetUserById:
    """Tests for AuthService.get_user_by_id method."""

    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self):
        """Test successfully getting user by ID."""
        mock_user = MagicMock()
        mock_user.id = "user-123"
        mock_user.email = "test@example.com"
        mock_user.user_metadata = {
            "full_name": "Test User",
            "avatar_url": "https://example.com/avatar.png",
        }
        mock_user.created_at = "2025-01-01T00:00:00"
        mock_user.last_sign_in_at = "2025-01-15T12:00:00"

        mock_response = MagicMock()
        mock_response.user = mock_user

        mock_client = MagicMock()
        mock_client.auth.admin.get_user_by_id.return_value = mock_response

        with patch(
            "app.services.auth_service.get_supabase_client",
            return_value=mock_client,
        ):
            result = await AuthService.get_user_by_id("user-123")

            assert result is not None
            assert result.id == "user-123"
            assert result.email == "test@example.com"
            assert result.full_name == "Test User"

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self):
        """Test getting user by ID when user doesn't exist."""
        mock_response = MagicMock()
        mock_response.user = None

        mock_client = MagicMock()
        mock_client.auth.admin.get_user_by_id.return_value = mock_response

        with patch(
            "app.services.auth_service.get_supabase_client",
            return_value=mock_client,
        ):
            result = await AuthService.get_user_by_id("nonexistent-user")

            assert result is None

    @pytest.mark.asyncio
    async def test_get_user_by_id_error_handling(self):
        """Test error handling when getting user fails."""
        mock_client = MagicMock()
        mock_client.auth.admin.get_user_by_id.side_effect = Exception("API Error")

        with patch(
            "app.services.auth_service.get_supabase_client",
            return_value=mock_client,
        ):
            result = await AuthService.get_user_by_id("user-123")

            assert result is None

    @pytest.mark.asyncio
    async def test_get_user_by_id_with_alternative_metadata_keys(self):
        """Test getting user with alternative metadata keys."""
        mock_user = MagicMock()
        mock_user.id = "user-456"
        mock_user.email = "alt@example.com"
        mock_user.user_metadata = {
            "name": "Alt User",
            "picture": "https://example.com/alt.png",
        }
        mock_user.created_at = None
        mock_user.last_sign_in_at = None

        mock_response = MagicMock()
        mock_response.user = mock_user

        mock_client = MagicMock()
        mock_client.auth.admin.get_user_by_id.return_value = mock_response

        with patch(
            "app.services.auth_service.get_supabase_client",
            return_value=mock_client,
        ):
            result = await AuthService.get_user_by_id("user-456")

            assert result is not None
            assert result.full_name == "Alt User"
            assert result.avatar_url == "https://example.com/alt.png"

    @pytest.mark.asyncio
    async def test_get_user_by_id_empty_metadata(self):
        """Test getting user with empty/None metadata."""
        mock_user = MagicMock()
        mock_user.id = "user-789"
        mock_user.email = "empty@example.com"
        mock_user.user_metadata = None
        mock_user.created_at = None
        mock_user.last_sign_in_at = None

        mock_response = MagicMock()
        mock_response.user = mock_user

        mock_client = MagicMock()
        mock_client.auth.admin.get_user_by_id.return_value = mock_response

        with patch(
            "app.services.auth_service.get_supabase_client",
            return_value=mock_client,
        ):
            result = await AuthService.get_user_by_id("user-789")

            assert result is not None
            assert result.full_name is None
            assert result.avatar_url is None


class TestAuthServiceSingleton:
    """Tests for auth_service singleton."""

    def test_singleton_is_auth_service_instance(self):
        """Test that auth_service is an AuthService instance."""
        assert isinstance(auth_service, AuthService)
