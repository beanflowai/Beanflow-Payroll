"""
Tests for API dependencies module.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.api.deps import (
    extract_bearer_token,
    get_current_user,
    get_optional_user,
)
from app.models.auth import UserResponse


class TestExtractBearerToken:
    """Tests for extract_bearer_token function."""

    def test_returns_none_for_none_header(self):
        """Test that extract_bearer_token returns None for None header."""
        result = extract_bearer_token(None)

        assert result is None

    def test_returns_none_for_empty_header(self):
        """Test that extract_bearer_token returns None for empty header."""
        result = extract_bearer_token("")

        assert result is None

    def test_returns_token_for_valid_bearer_header(self):
        """Test that extract_bearer_token returns token for valid Bearer header."""
        result = extract_bearer_token("Bearer valid-token-123")

        assert result == "valid-token-123"

    def test_is_case_insensitive(self):
        """Test that extract_bearer_token is case insensitive for 'Bearer'."""
        result = extract_bearer_token("bearer valid-token-123")

        assert result == "valid-token-123"

        result = extract_bearer_token("BEARER valid-token-123")

        assert result == "valid-token-123"

    def test_returns_none_for_invalid_format(self):
        """Test that extract_bearer_token returns None for invalid format."""
        # Only token, no Bearer prefix
        result = extract_bearer_token("valid-token-123")

        assert result is None

        # Too many parts
        result = extract_bearer_token("Bearer token extra")

        assert result is None

    def test_returns_none_for_non_bearer_auth(self):
        """Test that extract_bearer_token returns None for non-Bearer auth."""
        result = extract_bearer_token("Basic dXNlcjpwYXNz")

        assert result is None


class TestGetCurrentUser:
    """Tests for get_current_user function."""

    @pytest.mark.asyncio
    async def test_raises_401_when_no_authorization(self):
        """Test that get_current_user raises 401 when no authorization header."""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(None)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Authentication required"

    @pytest.mark.asyncio
    async def test_raises_401_when_invalid_authorization_format(self):
        """Test that get_current_user raises 401 for invalid authorization format."""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user("InvalidFormat")

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Authentication required"

    @pytest.mark.asyncio
    async def test_raises_401_when_jwt_verification_fails(self):
        """Test that get_current_user raises 401 when JWT verification fails."""
        with patch("app.api.deps.verify_supabase_jwt") as mock_verify:
            mock_verify.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user("Bearer invalid-token")

            assert exc_info.value.status_code == 401
            assert exc_info.value.detail == "Invalid or expired token"

    @pytest.mark.asyncio
    async def test_raises_401_when_no_sub_in_payload(self):
        """Test that get_current_user raises 401 when payload has no sub."""
        with patch("app.api.deps.verify_supabase_jwt") as mock_verify:
            mock_verify.return_value = {"email": "test@example.com"}

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user("Bearer valid-token")

            assert exc_info.value.status_code == 401
            assert exc_info.value.detail == "Invalid token payload"

    @pytest.mark.asyncio
    async def test_returns_user_response_for_valid_token(self):
        """Test that get_current_user returns UserResponse for valid token."""
        payload = {
            "sub": "user-123",
            "email": "test@example.com",
            "user_metadata": {
                "full_name": "Test User",
                "avatar_url": "https://example.com/avatar.jpg",
            },
        }

        with patch("app.api.deps.verify_supabase_jwt") as mock_verify, \
             patch("app.api.deps.SupabaseClient") as mock_client:
            mock_verify.return_value = payload

            result = await get_current_user("Bearer valid-token")

            assert isinstance(result, UserResponse)
            assert result.id == "user-123"
            assert result.email == "test@example.com"
            assert result.full_name == "Test User"
            assert result.avatar_url == "https://example.com/avatar.jpg"
            mock_client.set_user_token.assert_called_once_with("valid-token")

    @pytest.mark.asyncio
    async def test_uses_name_fallback_for_full_name(self):
        """Test that get_current_user uses 'name' as fallback for full_name."""
        payload = {
            "sub": "user-123",
            "email": "test@example.com",
            "user_metadata": {
                "name": "Test User Name",
            },
        }

        with patch("app.api.deps.verify_supabase_jwt") as mock_verify, \
             patch("app.api.deps.SupabaseClient"):
            mock_verify.return_value = payload

            result = await get_current_user("Bearer valid-token")

            assert result.full_name == "Test User Name"

    @pytest.mark.asyncio
    async def test_uses_picture_fallback_for_avatar_url(self):
        """Test that get_current_user uses 'picture' as fallback for avatar_url."""
        payload = {
            "sub": "user-123",
            "email": "test@example.com",
            "user_metadata": {
                "picture": "https://example.com/picture.jpg",
            },
        }

        with patch("app.api.deps.verify_supabase_jwt") as mock_verify, \
             patch("app.api.deps.SupabaseClient"):
            mock_verify.return_value = payload

            result = await get_current_user("Bearer valid-token")

            assert result.avatar_url == "https://example.com/picture.jpg"

    @pytest.mark.asyncio
    async def test_handles_empty_user_metadata(self):
        """Test that get_current_user handles empty user_metadata."""
        payload = {
            "sub": "user-123",
            "email": "test@example.com",
        }

        with patch("app.api.deps.verify_supabase_jwt") as mock_verify, \
             patch("app.api.deps.SupabaseClient"):
            mock_verify.return_value = payload

            result = await get_current_user("Bearer valid-token")

            assert result.id == "user-123"
            assert result.full_name is None
            assert result.avatar_url is None


class TestGetOptionalUser:
    """Tests for get_optional_user function."""

    @pytest.mark.asyncio
    async def test_returns_none_when_no_authorization(self):
        """Test that get_optional_user returns None when no authorization header."""
        result = await get_optional_user(None)

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_user_when_authenticated(self):
        """Test that get_optional_user returns user when authenticated."""
        payload = {
            "sub": "user-123",
            "email": "test@example.com",
            "user_metadata": {},
        }

        with patch("app.api.deps.verify_supabase_jwt") as mock_verify, \
             patch("app.api.deps.SupabaseClient"):
            mock_verify.return_value = payload

            result = await get_optional_user("Bearer valid-token")

            assert result is not None
            assert result.id == "user-123"

    @pytest.mark.asyncio
    async def test_returns_none_when_authentication_fails(self):
        """Test that get_optional_user returns None when authentication fails."""
        with patch("app.api.deps.verify_supabase_jwt") as mock_verify:
            mock_verify.return_value = None

            result = await get_optional_user("Bearer invalid-token")

            assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_for_invalid_format(self):
        """Test that get_optional_user returns None for invalid auth format."""
        # This will fail in extract_bearer_token, so get_current_user raises HTTPException
        with patch("app.api.deps.verify_supabase_jwt") as mock_verify:
            mock_verify.return_value = None

            result = await get_optional_user("InvalidFormat")

            assert result is None
