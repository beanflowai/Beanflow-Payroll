"""
Tests for Supabase client singleton and authentication helpers.

Tests for client initialization, token management, and admin client access.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from supabase import Client

from app.core.supabase_client import (
    SupabaseClient,
    get_supabase_admin_client,
    get_supabase_client,
)


class TestSupabaseClient:
    """Tests for SupabaseClient singleton."""

    def test_get_client_returns_singleton(self):
        """Test get_client returns the same instance."""
        # Reset singleton
        SupabaseClient._instance = None

        with patch("app.core.supabase_client.get_config") as mock_config:
            mock_cfg = MagicMock()
            mock_cfg.supabase_url = "https://test.supabase.co"
            mock_cfg.supabase_key = "test-key"
            mock_config.return_value = mock_cfg

            with patch("app.core.supabase_client.create_client") as mock_create:
                mock_client = MagicMock(spec=Client)
                mock_create.return_value = mock_client

                client1 = SupabaseClient.get_client()
                client2 = SupabaseClient.get_client()

                assert client1 is client2
                mock_create.assert_called_once()

    def test_get_admin_client_with_service_key(self):
        """Test get_admin_client creates admin instance when service key is configured."""
        # Reset singleton
        SupabaseClient._admin_instance = None

        with patch("app.core.supabase_client.get_config") as mock_config:
            mock_cfg = MagicMock()
            mock_cfg.supabase_url = "https://test.supabase.co"
            mock_cfg.supabase_service_role_key = "service-role-key"
            mock_config.return_value = mock_cfg

            with patch("app.core.supabase_client.create_client") as mock_create:
                mock_client = MagicMock(spec=Client)
                mock_create.return_value = mock_client

                admin_client = SupabaseClient.get_admin_client()

                assert admin_client is not None
                mock_create.assert_called_once_with(
                    "https://test.supabase.co",
                    "service-role-key",
                )

    def test_get_admin_client_without_service_key(self):
        """Test get_admin_client returns None when service key is not configured."""
        # Reset singleton
        SupabaseClient._admin_instance = None

        with patch("app.core.supabase_client.get_config") as mock_config:
            mock_cfg = MagicMock()
            mock_cfg.supabase_service_role_key = None
            mock_config.return_value = mock_cfg

            admin_client = SupabaseClient.get_admin_client()

            assert admin_client is None

    def test_set_and_get_user_token(self):
        """Test setting and getting user token."""
        test_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test"

        SupabaseClient.set_user_token(test_token)
        retrieved = SupabaseClient.get_user_token()

        assert retrieved == test_token

    def test_get_authenticated_client_with_token(self):
        """Test get_authenticated_client creates new client when token exists."""
        # Reset singleton
        SupabaseClient._instance = None

        test_token = "test-jwt-token"
        SupabaseClient.set_user_token(test_token)

        with patch("app.core.supabase_client.get_config") as mock_config, \
             patch("app.core.supabase_client.create_client") as mock_create:

            mock_cfg = MagicMock()
            mock_cfg.supabase_url = "https://test.supabase.co"
            mock_cfg.supabase_key = "test-key"
            mock_config.return_value = mock_cfg

            mock_client = MagicMock(spec=Client)
            mock_auth = MagicMock()
            mock_client.postgrest = mock_auth
            mock_create.return_value = mock_client

            auth_client = SupabaseClient.get_authenticated_client()

            assert auth_client is not None
            mock_auth.auth.assert_called_once_with(test_token)

    def test_get_authenticated_client_without_token(self):
        """Test get_authenticated_client falls back to base client when no token."""
        # Reset singleton
        SupabaseClient._instance = None
        SupabaseClient.set_user_token(None)

        with patch("app.core.supabase_client.get_config") as mock_config, \
             patch("app.core.supabase_client.create_client") as mock_create:

            mock_cfg = MagicMock()
            mock_cfg.supabase_url = "https://test.supabase.co"
            mock_cfg.supabase_key = "test-key"
            mock_config.return_value = mock_cfg

            mock_client = MagicMock(spec=Client)
            mock_create.return_value = mock_client

            auth_client = SupabaseClient.get_authenticated_client()

            assert auth_client is not None

    def test_set_user_context_deprecated(self):
        """Test set_user_context (deprecated method)."""
        # Reset singleton
        SupabaseClient._instance = None

        with patch("app.core.supabase_client.get_config") as mock_config, \
             patch("app.core.supabase_client.create_client") as mock_create:

            mock_cfg = MagicMock()
            mock_cfg.supabase_url = "https://test.supabase.co"
            mock_cfg.supabase_key = "test-key"
            mock_config.return_value = mock_cfg

            mock_client = MagicMock(spec=Client)
            mock_rpc = MagicMock()
            mock_rpc.execute.return_value = MagicMock()
            mock_client.rpc.return_value = mock_rpc
            mock_create.return_value = mock_client

            SupabaseClient.set_user_context("user-123")

            mock_client.rpc.assert_called_once_with(
                "set_config",
                {"setting": "app.current_user_id", "value": "user-123", "is_local": True},
            )

    def test_set_user_context_handles_error(self):
        """Test set_user_context handles exceptions gracefully."""
        # Reset singleton
        SupabaseClient._instance = None

        with patch("app.core.supabase_client.get_config") as mock_config, \
             patch("app.core.supabase_client.create_client") as mock_create:

            mock_cfg = MagicMock()
            mock_cfg.supabase_url = "https://test.supabase.co"
            mock_cfg.supabase_key = "test-key"
            mock_config.return_value = mock_cfg

            mock_client = MagicMock(spec=Client)
            mock_client.rpc.side_effect = Exception("RPC error")
            mock_create.return_value = mock_client

            # Should not raise
            SupabaseClient.set_user_context("user-123")

    def test_check_connection_success(self):
        """Test check_connection returns True when connection works."""
        # Reset singleton
        SupabaseClient._instance = None

        with patch("app.core.supabase_client.get_config") as mock_config, \
             patch("app.core.supabase_client.create_client") as mock_create:

            mock_cfg = MagicMock()
            mock_cfg.supabase_url = "https://test.supabase.co"
            mock_cfg.supabase_key = "test-key"
            mock_config.return_value = mock_cfg

            mock_client = MagicMock(spec=Client)
            mock_table = MagicMock()
            mock_select = MagicMock()
            mock_limit = MagicMock()
            mock_execute = MagicMock()

            mock_client.table.return_value = mock_table
            mock_table.select.return_value = mock_select
            mock_select.limit.return_value = mock_limit
            mock_limit.execute.return_value = mock_execute
            mock_create.return_value = mock_client

            result = SupabaseClient.check_connection()

            assert result is True

    def test_check_connection_handles_error(self):
        """Test check_connection returns True even when table doesn't exist."""
        # Reset singleton
        SupabaseClient._instance = None

        with patch("app.core.supabase_client.get_config") as mock_config, \
             patch("app.core.supabase_client.create_client") as mock_create:

            mock_cfg = MagicMock()
            mock_cfg.supabase_url = "https://test.supabase.co"
            mock_cfg.supabase_key = "test-key"
            mock_config.return_value = mock_cfg

            mock_client = MagicMock(spec=Client)
            mock_client.table.side_effect = Exception("Table doesn't exist")
            mock_create.return_value = mock_client

            result = SupabaseClient.check_connection()

            assert result is True


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_get_supabase_client(self):
        """Test get_supabase_client convenience function."""
        # Reset singleton and token
        SupabaseClient._instance = None
        SupabaseClient.set_user_token(None)

        with patch("app.core.supabase_client.get_config") as mock_config, \
             patch("app.core.supabase_client.create_client") as mock_create:

            mock_cfg = MagicMock()
            mock_cfg.supabase_url = "https://test.supabase.co"
            mock_cfg.supabase_key = "test-key"
            mock_config.return_value = mock_cfg

            mock_client = MagicMock(spec=Client)
            mock_create.return_value = mock_client

            client = get_supabase_client()

            assert client is not None

    def test_get_supabase_admin_client_convenience(self):
        """Test get_supabase_admin_client convenience function."""
        # Reset singleton
        SupabaseClient._admin_instance = None

        with patch("app.core.supabase_client.get_config") as mock_config:
            mock_cfg = MagicMock()
            mock_cfg.supabase_service_role_key = None
            mock_config.return_value = mock_cfg

            admin_client = get_supabase_admin_client()

            assert admin_client is None
