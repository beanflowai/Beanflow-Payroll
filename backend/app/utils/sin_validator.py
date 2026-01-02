"""
SIN (Social Insurance Number) Validation Utilities

Provides Luhn algorithm validation and formatting functions
for Canadian Social Insurance Numbers.
"""

from __future__ import annotations


def validate_sin_luhn(sin: str) -> bool:
    """
    Validate a Canadian SIN using the Luhn algorithm.

    The SIN is a 9-digit number where the check digit (last digit)
    is calculated using the Luhn algorithm (mod 10).

    Algorithm:
    1. Starting from the rightmost digit, double every second digit
    2. If doubling results in a number > 9, subtract 9
    3. Sum all the digits
    4. If the sum is divisible by 10, the SIN is valid

    Args:
        sin: 9-digit SIN string (digits only, no dashes)

    Returns:
        True if SIN is valid, False otherwise

    Examples:
        >>> validate_sin_luhn("046454286")
        True
        >>> validate_sin_luhn("123456789")
        False
    """
    # Remove any formatting (spaces, dashes)
    cleaned = "".join(c for c in sin if c.isdigit())

    # SIN must be exactly 9 digits
    if len(cleaned) != 9:
        return False

    # SIN cannot start with 0 (except special cases) or 8
    # Valid starting digits: 1-7, 9
    first_digit = cleaned[0]
    if first_digit == "8":
        return False

    # Apply Luhn algorithm
    total = 0
    for i, digit in enumerate(cleaned):
        d = int(digit)

        # Double every second digit (starting from the second position)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9

        total += d

    return total % 10 == 0


def format_sin_display(sin: str) -> str:
    """
    Format a SIN with dashes for display (XXX-XXX-XXX).

    Args:
        sin: 9-digit SIN string (may or may not have formatting)

    Returns:
        Formatted SIN with dashes

    Examples:
        >>> format_sin_display("046454286")
        '046-454-286'
        >>> format_sin_display("046-454-286")
        '046-454-286'
    """
    # Remove any existing formatting
    cleaned = "".join(c for c in sin if c.isdigit())

    if len(cleaned) != 9:
        return sin  # Return as-is if invalid length

    return f"{cleaned[:3]}-{cleaned[3:6]}-{cleaned[6:]}"


def mask_sin_display(sin: str) -> str:
    """
    Mask a SIN for display, showing only last 3 digits.

    Args:
        sin: 9-digit SIN string

    Returns:
        Masked SIN in format "***-***-XXX"

    Examples:
        >>> mask_sin_display("046454286")
        '***-***-286'
    """
    # Remove any formatting
    cleaned = "".join(c for c in sin if c.isdigit())

    if len(cleaned) >= 3:
        return f"***-***-{cleaned[-3:]}"
    return "***-***-***"


def normalize_sin(sin: str) -> str | None:
    """
    Normalize a SIN to 9 digits only.

    Removes dashes, spaces, and validates basic format.

    Args:
        sin: SIN string with possible formatting

    Returns:
        9-digit SIN string or None if invalid format

    Examples:
        >>> normalize_sin("046-454-286")
        '046454286'
        >>> normalize_sin("046 454 286")
        '046454286'
        >>> normalize_sin("12345")
        None
    """
    # Remove any formatting
    cleaned = "".join(c for c in sin if c.isdigit())

    if len(cleaned) != 9:
        return None

    return cleaned


def validate_sin_format(sin: str) -> tuple[bool, str | None]:
    """
    Validate SIN format and Luhn check, returning error message if invalid.

    Args:
        sin: SIN string to validate

    Returns:
        Tuple of (is_valid, error_message)
        error_message is None if valid

    Examples:
        >>> validate_sin_format("046454286")
        (True, None)
        >>> validate_sin_format("123456789")
        (False, "Invalid SIN: failed Luhn check")
        >>> validate_sin_format("12345")
        (False, "Invalid SIN: must be 9 digits")
    """
    normalized = normalize_sin(sin)

    if normalized is None:
        return False, "Invalid SIN: must be 9 digits"

    if not validate_sin_luhn(normalized):
        return False, "Invalid SIN: failed Luhn check"

    return True, None
