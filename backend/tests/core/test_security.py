"""
Tests for security module.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from cryptography.fernet import Fernet

from app.core.security import (
    SecurityManager,
    decrypt_sin,
    encrypt_sin,
    mask_sin,
    verify_supabase_jwt,
)


class TestSecurityManager:
    """Tests for SecurityManager class."""

    def setup_method(self):
        """Reset SecurityManager state before each test."""
        SecurityManager._fernet = None

    def test_get_fernet_returns_none_when_no_key(self):
        """Test that get_fernet returns None when encryption key is not configured."""
        with patch("app.core.security.get_config") as mock_config:
            mock_config.return_value = MagicMock(encryption_key=None)

            result = SecurityManager.get_fernet()

            assert result is None

    def test_get_fernet_initializes_with_valid_key(self):
        """Test that get_fernet initializes Fernet with valid encryption key."""
        # Generate a valid Fernet key
        valid_key = Fernet.generate_key().decode()

        with patch("app.core.security.get_config") as mock_config:
            mock_config.return_value = MagicMock(encryption_key=valid_key)

            result = SecurityManager.get_fernet()

            assert result is not None
            assert isinstance(result, Fernet)

    def test_get_fernet_caches_instance(self):
        """Test that get_fernet caches the Fernet instance."""
        valid_key = Fernet.generate_key().decode()

        with patch("app.core.security.get_config") as mock_config:
            mock_config.return_value = MagicMock(encryption_key=valid_key)

            first = SecurityManager.get_fernet()
            second = SecurityManager.get_fernet()

            assert first is second

    def test_get_fernet_handles_invalid_key(self):
        """Test that get_fernet handles invalid encryption key gracefully."""
        with patch("app.core.security.get_config") as mock_config:
            mock_config.return_value = MagicMock(encryption_key="invalid-key")

            result = SecurityManager.get_fernet()

            assert result is None

    def test_verify_supabase_jwt_valid_token(self):
        """Test that verify_supabase_jwt returns payload for valid token."""
        test_payload = {"sub": "user-123", "email": "test@example.com"}

        with patch("app.core.security.get_config") as mock_config, \
             patch("app.core.security.jwt.decode") as mock_decode:
            mock_config.return_value = MagicMock(supabase_jwt_secret="test-secret")
            mock_decode.return_value = test_payload

            result = SecurityManager.verify_supabase_jwt("valid-token")

            assert result == test_payload
            mock_decode.assert_called_once_with(
                "valid-token",
                "test-secret",
                algorithms=["HS256"],
                audience="authenticated",
            )

    def test_verify_supabase_jwt_invalid_token(self):
        """Test that verify_supabase_jwt returns None for invalid token."""
        from jose import JWTError

        with patch("app.core.security.get_config") as mock_config, \
             patch("app.core.security.jwt.decode") as mock_decode:
            mock_config.return_value = MagicMock(supabase_jwt_secret="test-secret")
            mock_decode.side_effect = JWTError("Invalid token")

            result = SecurityManager.verify_supabase_jwt("invalid-token")

            assert result is None

    def test_encrypt_returns_none_when_no_fernet(self):
        """Test that encrypt returns None when Fernet is not initialized."""
        with patch.object(SecurityManager, "get_fernet", return_value=None):
            result = SecurityManager.encrypt("test-data")

            assert result is None

    def test_encrypt_returns_encrypted_string(self):
        """Test that encrypt returns encrypted string."""
        mock_fernet = MagicMock()
        mock_fernet.encrypt.return_value = b"encrypted-data"

        with patch.object(SecurityManager, "get_fernet", return_value=mock_fernet):
            result = SecurityManager.encrypt("test-data")

            assert result == "encrypted-data"
            mock_fernet.encrypt.assert_called_once_with(b"test-data")

    def test_encrypt_handles_exception(self):
        """Test that encrypt handles encryption exceptions."""
        mock_fernet = MagicMock()
        mock_fernet.encrypt.side_effect = Exception("Encryption failed")

        with patch.object(SecurityManager, "get_fernet", return_value=mock_fernet):
            result = SecurityManager.encrypt("test-data")

            assert result is None

    def test_decrypt_returns_none_when_no_fernet(self):
        """Test that decrypt returns None when Fernet is not initialized."""
        with patch.object(SecurityManager, "get_fernet", return_value=None):
            result = SecurityManager.decrypt("encrypted-data")

            assert result is None

    def test_decrypt_returns_decrypted_string(self):
        """Test that decrypt returns decrypted string."""
        mock_fernet = MagicMock()
        mock_fernet.decrypt.return_value = b"decrypted-data"

        with patch.object(SecurityManager, "get_fernet", return_value=mock_fernet):
            result = SecurityManager.decrypt("encrypted-data")

            assert result == "decrypted-data"
            mock_fernet.decrypt.assert_called_once_with(b"encrypted-data")

    def test_decrypt_handles_exception(self):
        """Test that decrypt handles decryption exceptions."""
        mock_fernet = MagicMock()
        mock_fernet.decrypt.side_effect = Exception("Decryption failed")

        with patch.object(SecurityManager, "get_fernet", return_value=mock_fernet):
            result = SecurityManager.decrypt("encrypted-data")

            assert result is None


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_verify_supabase_jwt_calls_security_manager(self):
        """Test that verify_supabase_jwt convenience function calls SecurityManager."""
        with patch.object(SecurityManager, "verify_supabase_jwt") as mock_verify:
            mock_verify.return_value = {"sub": "user-123"}

            result = verify_supabase_jwt("token")

            mock_verify.assert_called_once_with("token")
            assert result == {"sub": "user-123"}

    def test_encrypt_sin_calls_security_manager(self):
        """Test that encrypt_sin convenience function calls SecurityManager."""
        with patch.object(SecurityManager, "encrypt") as mock_encrypt:
            mock_encrypt.return_value = "encrypted-sin"

            result = encrypt_sin("123456789")

            mock_encrypt.assert_called_once_with("123456789")
            assert result == "encrypted-sin"

    def test_decrypt_sin_returns_decrypted_value(self):
        """Test that decrypt_sin returns decrypted SIN."""
        with patch.object(SecurityManager, "decrypt") as mock_decrypt:
            mock_decrypt.return_value = "123456789"

            result = decrypt_sin("encrypted-sin")

            assert result == "123456789"

    def test_decrypt_sin_fallback_to_plain_text_in_debug(self):
        """Test that decrypt_sin falls back to plain text SIN in debug mode."""
        with patch.object(SecurityManager, "decrypt") as mock_decrypt, \
             patch("app.core.security.get_config") as mock_config:
            mock_decrypt.return_value = None
            mock_config.return_value = MagicMock(debug=True)

            result = decrypt_sin("123456789")

            assert result == "123456789"

    def test_decrypt_sin_handles_formatted_sin_in_debug(self):
        """Test that decrypt_sin handles formatted SIN in debug mode."""
        with patch.object(SecurityManager, "decrypt") as mock_decrypt, \
             patch("app.core.security.get_config") as mock_config:
            mock_decrypt.return_value = None
            mock_config.return_value = MagicMock(debug=True)

            result = decrypt_sin("123-456-789")

            assert result == "123456789"

    def test_decrypt_sin_returns_none_for_invalid_sin_in_debug(self):
        """Test that decrypt_sin returns None for invalid SIN format in debug mode."""
        with patch.object(SecurityManager, "decrypt") as mock_decrypt, \
             patch("app.core.security.get_config") as mock_config:
            mock_decrypt.return_value = None
            mock_config.return_value = MagicMock(debug=True)

            # Too short
            result = decrypt_sin("12345")
            assert result is None

            # Not digits
            result = decrypt_sin("12345678A")
            assert result is None

    def test_decrypt_sin_returns_none_for_plain_text_when_not_debug(self):
        """Test that decrypt_sin returns None for plain text SIN when not in debug mode."""
        with patch.object(SecurityManager, "decrypt") as mock_decrypt, \
             patch("app.core.security.get_config") as mock_config:
            mock_decrypt.return_value = None
            mock_config.return_value = MagicMock(debug=False)

            result = decrypt_sin("123456789")

            assert result is None


class TestMaskSin:
    """Tests for mask_sin function."""

    def test_masks_full_sin(self):
        """Test that mask_sin masks a full SIN correctly."""
        result = mask_sin("123456789")

        assert result == "***-***-789"

    def test_masks_formatted_sin(self):
        """Test that mask_sin masks a formatted SIN correctly."""
        result = mask_sin("123-456-789")

        assert result == "***-***-789"

    def test_handles_short_sin(self):
        """Test that mask_sin handles SIN shorter than 3 characters."""
        result = mask_sin("12")

        assert result == "***-***-***"

    def test_handles_empty_string(self):
        """Test that mask_sin handles empty string."""
        result = mask_sin("")

        assert result == "***-***-***"

    def test_masks_with_exactly_three_chars(self):
        """Test that mask_sin works with exactly 3 characters."""
        result = mask_sin("789")

        assert result == "***-***-789"
