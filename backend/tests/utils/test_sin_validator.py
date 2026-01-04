"""Tests for SIN validation utilities."""

import pytest

from app.utils.sin_validator import (
    format_sin_display,
    mask_sin_display,
    normalize_sin,
    validate_sin_format,
    validate_sin_luhn,
)


class TestValidateSinLuhn:
    """Tests for the Luhn algorithm SIN validation."""

    def test_valid_sin(self):
        """Test that a valid SIN passes Luhn check."""
        # This is a known valid test SIN
        assert validate_sin_luhn("046454286") is True

    def test_invalid_sin_wrong_check_digit(self):
        """Test that an invalid check digit fails."""
        assert validate_sin_luhn("123456789") is False

    def test_sin_too_short(self):
        """Test that a SIN shorter than 9 digits fails."""
        assert validate_sin_luhn("12345678") is False
        assert validate_sin_luhn("1234567") is False
        assert validate_sin_luhn("") is False

    def test_sin_too_long(self):
        """Test that a SIN longer than 9 digits fails."""
        assert validate_sin_luhn("1234567890") is False
        assert validate_sin_luhn("12345678901") is False

    def test_sin_starting_with_8(self):
        """Test that SIN starting with 8 is invalid."""
        assert validate_sin_luhn("812345678") is False

    def test_sin_with_dashes(self):
        """Test that SIN with dashes is cleaned and validated."""
        assert validate_sin_luhn("046-454-286") is True

    def test_sin_with_spaces(self):
        """Test that SIN with spaces is cleaned and validated."""
        assert validate_sin_luhn("046 454 286") is True

    def test_luhn_double_digit_subtraction(self):
        """Test that doubling digits > 4 correctly subtracts 9."""
        # A SIN where doubling produces values > 9
        # Position 1 (index 1) has digit 9: 9*2=18, 18-9=9
        assert validate_sin_luhn("193456788") is False  # Invalid by Luhn
        # Test a valid one with high doubled values
        assert validate_sin_luhn("130692544") is True


class TestFormatSinDisplay:
    """Tests for SIN display formatting."""

    def test_format_plain_sin(self):
        """Test formatting a plain 9-digit SIN."""
        assert format_sin_display("046454286") == "046-454-286"

    def test_format_already_formatted_sin(self):
        """Test that already formatted SIN stays formatted."""
        assert format_sin_display("046-454-286") == "046-454-286"

    def test_format_sin_with_spaces(self):
        """Test formatting SIN with spaces."""
        assert format_sin_display("046 454 286") == "046-454-286"

    def test_format_invalid_length_returns_original(self):
        """Test that invalid length SIN returns original."""
        assert format_sin_display("12345") == "12345"
        assert format_sin_display("1234567890") == "1234567890"


class TestMaskSinDisplay:
    """Tests for SIN masking."""

    def test_mask_plain_sin(self):
        """Test masking a plain SIN."""
        assert mask_sin_display("046454286") == "***-***-286"

    def test_mask_formatted_sin(self):
        """Test masking a formatted SIN."""
        assert mask_sin_display("046-454-286") == "***-***-286"

    def test_mask_short_sin(self):
        """Test masking a short SIN shows last 3 digits."""
        assert mask_sin_display("123") == "***-***-123"

    def test_mask_very_short_sin(self):
        """Test masking a very short SIN returns full mask."""
        assert mask_sin_display("12") == "***-***-***"
        assert mask_sin_display("") == "***-***-***"


class TestNormalizeSin:
    """Tests for SIN normalization."""

    def test_normalize_plain_sin(self):
        """Test normalizing a plain 9-digit SIN."""
        assert normalize_sin("046454286") == "046454286"

    def test_normalize_sin_with_dashes(self):
        """Test normalizing SIN with dashes."""
        assert normalize_sin("046-454-286") == "046454286"

    def test_normalize_sin_with_spaces(self):
        """Test normalizing SIN with spaces."""
        assert normalize_sin("046 454 286") == "046454286"

    def test_normalize_invalid_length_returns_none(self):
        """Test that invalid length returns None."""
        assert normalize_sin("12345") is None
        assert normalize_sin("1234567890") is None
        assert normalize_sin("") is None


class TestValidateSinFormat:
    """Tests for complete SIN validation with error messages."""

    def test_valid_sin_returns_true(self):
        """Test that valid SIN returns (True, None)."""
        is_valid, error = validate_sin_format("046454286")
        assert is_valid is True
        assert error is None

    def test_valid_sin_with_formatting(self):
        """Test that valid formatted SIN returns (True, None)."""
        is_valid, error = validate_sin_format("046-454-286")
        assert is_valid is True
        assert error is None

    def test_invalid_length_returns_error(self):
        """Test that invalid length returns appropriate error."""
        is_valid, error = validate_sin_format("12345")
        assert is_valid is False
        assert error == "Invalid SIN: must be 9 digits"

    def test_invalid_luhn_returns_error(self):
        """Test that invalid Luhn check returns appropriate error."""
        is_valid, error = validate_sin_format("123456789")
        assert is_valid is False
        assert error == "Invalid SIN: failed Luhn check"

    def test_empty_string(self):
        """Test that empty string returns length error."""
        is_valid, error = validate_sin_format("")
        assert is_valid is False
        assert error == "Invalid SIN: must be 9 digits"
