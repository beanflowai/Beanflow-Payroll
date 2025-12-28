"""
Canadian Payroll Tax Tables Module

Loads tax configuration from JSON files and provides calculation utilities.
Data source: CRA T4127 (121st Edition, July 2025)

Supports all provinces/territories except Quebec.
"""

from __future__ import annotations

import json
import logging
from datetime import date
from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Base path for tax table configuration files
CONFIG_BASE_PATH = Path(__file__).parent.parent.parent.parent / "config" / "tax_tables"

# Supported provinces (Quebec excluded - requires separate system)
SUPPORTED_PROVINCES = frozenset([
    "AB", "BC", "MB", "NB", "NL", "NS", "NT", "NU", "ON", "PE", "SK", "YT"
])


class TaxConfigError(Exception):
    """Raised when tax configuration is invalid or missing."""
    pass


# =============================================================================
# JSON Loading Functions
# =============================================================================

@lru_cache(maxsize=4)
def _load_json_file(file_path: str) -> dict[str, Any]:
    """Load and cache a JSON configuration file."""
    path = Path(file_path)
    if not path.exists():
        raise TaxConfigError(f"Tax configuration file not found: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise TaxConfigError(f"Invalid JSON in {path}: {e}")


def _get_config_path(year: int, filename: str) -> Path:
    """Get the path to a configuration file for a given year."""
    return CONFIG_BASE_PATH / str(year) / filename


def _get_july_cutoff(year: int) -> date:
    """Get July 1st cutoff date for a given year (mid-year rate change)."""
    return date(year, 7, 1)


def _get_federal_config_with_edition(year: int, edition: str) -> dict[str, Any]:
    """
    Load federal config, auto-detecting versioned vs single file.

    Priority:
    1. federal_{edition}.json (versioned file)
    2. federal.json (single file fallback)
    """
    # Try versioned file first
    versioned_path = _get_config_path(year, f"federal_{edition}.json")
    if versioned_path.exists():
        return _load_json_file(str(versioned_path))

    # Fallback to single file
    single_path = _get_config_path(year, "federal.json")
    if single_path.exists():
        return _load_json_file(str(single_path))

    raise TaxConfigError(f"No federal config found for year {year}")


def get_federal_config(year: int = 2025, pay_date: date | None = None) -> dict[str, Any]:
    """
    Get federal tax configuration for a given year and pay date.

    Automatically detects whether versioned files (federal_jan.json, federal_jul.json)
    exist for the year. If they do, selects edition based on pay_date:
    - Before July 1: January edition
    - July 1 onwards: July edition (default)

    If only federal.json exists, uses that regardless of pay_date.

    Args:
        year: Tax year (default: 2025)
        pay_date: Pay period date for edition selection (default: uses July edition)

    Returns:
        Dict with federal tax configuration for the appropriate edition
    """
    # Determine edition based on pay date
    if pay_date is not None and pay_date < _get_july_cutoff(year):
        edition = "jan"
    else:
        edition = "jul"

    return _get_federal_config_with_edition(year, edition)


@lru_cache(maxsize=1)
def get_cpp_config(year: int = 2025) -> dict[str, Any]:
    """
    Get CPP configuration for a given year.

    Returns dict with keys: ympe, yampe, basic_exemption, base_rate, etc.
    """
    data = _load_json_file(str(_get_config_path(year, "cpp_ei.json")))
    return data["cpp"]


@lru_cache(maxsize=1)
def get_ei_config(year: int = 2025) -> dict[str, Any]:
    """
    Get EI configuration for a given year.

    Returns dict with keys: mie, employee_rate, employer_rate_multiplier, etc.
    """
    data = _load_json_file(str(_get_config_path(year, "cpp_ei.json")))
    return data["ei"]


@lru_cache(maxsize=8)
def _get_provinces_config_with_edition(year: int, edition: str) -> dict[str, dict[str, Any]]:
    """
    Load provinces config, auto-detecting versioned vs single file.

    Priority:
    1. provinces_{edition}.json (versioned file)
    2. provinces.json (single file fallback)
    """
    # Try versioned file first
    versioned_path = _get_config_path(year, f"provinces_{edition}.json")
    if versioned_path.exists():
        data = _load_json_file(str(versioned_path))
        return data["provinces"]

    # Fallback to single file
    single_path = _get_config_path(year, "provinces.json")
    if single_path.exists():
        data = _load_json_file(str(single_path))
        return data["provinces"]

    raise TaxConfigError(f"No provinces config found for year {year}")


def get_province_config(
    province_code: str,
    year: int = 2025,
    pay_date: date | None = None
) -> dict[str, Any]:
    """
    Get tax configuration for a specific province.

    Automatically detects whether versioned files (provinces_jan.json, provinces_jul.json)
    exist for the year. If they do, selects edition based on pay_date:
    - Before July 1: January edition
    - July 1 onwards: July edition (default)

    If only provinces.json exists, uses that regardless of pay_date.

    Args:
        province_code: Two-letter province code (e.g., "ON", "BC")
        year: Tax year (default: 2025)
        pay_date: Pay period date for edition selection (default: uses July edition)

    Returns:
        Dict with province tax configuration

    Raises:
        TaxConfigError: If province is not supported
    """
    province_code = province_code.upper()

    if province_code not in SUPPORTED_PROVINCES:
        raise TaxConfigError(
            f"Province '{province_code}' not supported. "
            f"Supported: {sorted(SUPPORTED_PROVINCES)}"
        )

    # Determine edition based on pay date
    if pay_date is not None and pay_date < _get_july_cutoff(year):
        edition = "jan"
    else:
        edition = "jul"

    provinces = _get_provinces_config_with_edition(year, edition)

    if province_code not in provinces:
        raise TaxConfigError(f"Province '{province_code}' not found in {year} configuration")

    return provinces[province_code]


def get_all_provinces(year: int = 2025) -> list[str]:
    """Get list of all supported province codes."""
    return sorted(SUPPORTED_PROVINCES)


# =============================================================================
# Tax Bracket Lookup
# =============================================================================

def find_tax_bracket(
    annual_income: Decimal | float,
    brackets: list[dict[str, Any]]
) -> tuple[Decimal, Decimal]:
    """
    Find the applicable tax rate and constant for a given income.

    Args:
        annual_income: Annual taxable income
        brackets: List of bracket dicts with threshold, rate, constant

    Returns:
        Tuple of (rate, constant) as Decimals

    Example:
        >>> rate, constant = find_tax_bracket(Decimal("75000"), federal_brackets)
        >>> # For income in 2nd federal bracket:
        >>> # rate = 0.205, constant = 3155.63
    """
    income = Decimal(str(annual_income))

    # Brackets should be in ascending order by threshold
    applicable_rate = Decimal("0")
    applicable_constant = Decimal("0")

    for bracket in brackets:
        threshold = Decimal(str(bracket["threshold"]))
        if income >= threshold:
            applicable_rate = Decimal(str(bracket["rate"]))
            applicable_constant = Decimal(str(bracket["constant"]))
        else:
            break

    return (applicable_rate, applicable_constant)


# =============================================================================
# Dynamic BPA Calculations
# =============================================================================

def calculate_dynamic_bpa(
    province_code: str,
    annual_income: Decimal | float,
    net_income: Decimal | float | None = None,
    year: int = 2025,
    pay_date: date | None = None
) -> Decimal:
    """
    Calculate Basic Personal Amount for provinces with dynamic BPA.

    Some provinces have BPA that varies based on income:
    - Manitoba (MB): BPA reduces as income increases above $200,000
    - Nova Scotia (NS): BPA increases for income $25,000-$75,000
    - Yukon (YT): Follows federal BPA

    Args:
        province_code: Two-letter province code
        annual_income: Annual taxable income (for NS, YT)
        net_income: Net income (for MB calculation)
        year: Tax year
        pay_date: Pay period date for edition selection

    Returns:
        Calculated BPA as Decimal
    """
    province_code = province_code.upper()
    config = get_province_config(province_code, year, pay_date)

    if not config.get("bpa_is_dynamic", False):
        return Decimal(str(config["bpa"]))

    dynamic_type = config.get("dynamic_bpa_type", "")
    dynamic_config = config.get("dynamic_bpa_config", {})

    if dynamic_type == "income_based_reduction":
        # Manitoba: BPA reduces from base to 0 as income goes from 200k to 400k
        return _calculate_bpa_manitoba(
            net_income or annual_income,
            dynamic_config
        )

    elif dynamic_type == "income_based_increase":
        # Nova Scotia: BPA increases from base as income goes from 25k to 75k
        return _calculate_bpa_nova_scotia(
            annual_income,
            dynamic_config
        )

    elif dynamic_type == "follows_federal":
        # Yukon: Same as federal BPA (also varies by edition)
        federal = get_federal_config(year, pay_date)
        return Decimal(str(federal["bpaf"]))

    # Fallback to static BPA
    return Decimal(str(config["bpa"]))


def _calculate_bpa_manitoba(
    net_income: Decimal | float,
    config: dict[str, Any]
) -> Decimal:
    """
    Calculate Manitoba Basic Personal Amount.

    Formula from T4127:
    - NI <= 200,000: BPAMB = 15,591
    - 200,000 < NI < 400,000: BPAMB = 15,591 - (NI - 200,000) × (15,591/200,000)
    - NI >= 400,000: BPAMB = 0
    """
    ni = Decimal(str(net_income))
    base_bpa = Decimal(str(config.get("base_bpa", "15591")))
    reduction_start = Decimal(str(config.get("reduction_start", "200000")))
    reduction_end = Decimal(str(config.get("reduction_end", "400000")))
    min_bpa = Decimal(str(config.get("min_bpa", "0")))

    if ni <= reduction_start:
        return base_bpa

    if ni >= reduction_end:
        return min_bpa

    # Linear reduction
    reduction_range = reduction_end - reduction_start
    reduction_factor = base_bpa / reduction_range
    reduction_amount = (ni - reduction_start) * reduction_factor

    result = base_bpa - reduction_amount
    return max(result, min_bpa)


def _calculate_bpa_nova_scotia(
    annual_income: Decimal | float,
    config: dict[str, Any]
) -> Decimal:
    """
    Calculate Nova Scotia Basic Personal Amount.

    Formula from T4127:
    - A <= 25,000: BPANS = 11,744
    - 25,000 < A < 75,000: BPANS = 11,744 + [(A - 25,000) × 6%]
    - A >= 75,000: BPANS = 14,744
    """
    income = Decimal(str(annual_income))
    base_bpa = Decimal(str(config.get("base_bpa", "11744")))
    increase_start = Decimal(str(config.get("increase_start", "25000")))
    increase_end = Decimal(str(config.get("increase_end", "75000")))
    increase_rate = Decimal(str(config.get("increase_rate", "0.06")))
    max_bpa = Decimal(str(config.get("max_bpa", "14744")))

    if income <= increase_start:
        return base_bpa

    if income >= increase_end:
        return max_bpa

    # Linear increase
    increase_amount = (income - increase_start) * increase_rate
    result = base_bpa + increase_amount

    return min(result, max_bpa)


# =============================================================================
# Validation
# =============================================================================


def _has_versioned_federal_config(year: int) -> bool:
    """Check if versioned federal config files exist for the year."""
    jan_path = _get_config_path(year, "federal_jan.json")
    jul_path = _get_config_path(year, "federal_jul.json")
    return jan_path.exists() and jul_path.exists()


def _has_versioned_provinces_config(year: int) -> bool:
    """Check if versioned provinces config files exist for the year."""
    jan_path = _get_config_path(year, "provinces_jan.json")
    jul_path = _get_config_path(year, "provinces_jul.json")
    return jan_path.exists() and jul_path.exists()


def validate_tax_tables(year: int = 2025) -> list[str]:
    """
    Validate all tax configuration files.

    Automatically detects whether versioned files exist for the year.
    If versioned files exist, validates both Jan and Jul editions.
    Otherwise, validates single file.

    Returns:
        List of validation errors (empty if valid)
    """
    errors: list[str] = []

    # Validate federal config(s)
    # Auto-detect if versioned files exist
    federal_editions: list[tuple[str, date | None]]
    if _has_versioned_federal_config(year):
        federal_editions = [
            ("federal_jan", date(year, 1, 1)),
            ("federal_jul", date(year, 7, 1)),
        ]
    else:
        federal_editions = [("federal", None)]

    for edition_name, pay_date in federal_editions:
        try:
            federal = get_federal_config(year, pay_date)
            if len(federal.get("brackets", [])) != 5:
                errors.append(f"{edition_name}: should have 5 brackets, got {len(federal.get('brackets', []))}")
            if "bpaf" not in federal:
                errors.append(f"{edition_name}: missing 'bpaf' (Basic Personal Amount)")
        except TaxConfigError as e:
            errors.append(f"{edition_name} config error: {e}")

    # Validate CPP/EI config
    try:
        cpp = get_cpp_config(year)
        if "ympe" not in cpp:
            errors.append("CPP missing 'ympe' (Year's Maximum Pensionable Earnings)")
        ei = get_ei_config(year)
        if "mie" not in ei:
            errors.append("EI missing 'mie' (Maximum Insurable Earnings)")
    except TaxConfigError as e:
        errors.append(f"CPP/EI config error: {e}")

    # Validate each province
    # Auto-detect if versioned files exist
    province_editions: list[tuple[str, date | None]]
    if _has_versioned_provinces_config(year):
        province_editions = [
            ("provinces_jan", date(year, 1, 1)),
            ("provinces_jul", date(year, 7, 1)),
        ]
    else:
        province_editions = [("provinces", None)]

    for edition_name, pay_date in province_editions:
        for province_code in SUPPORTED_PROVINCES:
            try:
                config = get_province_config(province_code, year, pay_date)

                # Check required fields
                if "brackets" not in config:
                    errors.append(f"{edition_name}/{province_code}: missing 'brackets'")
                elif not config["brackets"]:
                    errors.append(f"{edition_name}/{province_code}: empty brackets list")
                else:
                    # Verify brackets are in ascending order
                    thresholds = [b["threshold"] for b in config["brackets"]]
                    if thresholds != sorted(thresholds):
                        errors.append(f"{edition_name}/{province_code}: brackets not in ascending order")

                    # First bracket should start at 0
                    if thresholds[0] != 0:
                        errors.append(f"{edition_name}/{province_code}: first bracket must start at 0")

                if "bpa" not in config:
                    errors.append(f"{edition_name}/{province_code}: missing 'bpa' (Basic Personal Amount)")

            except TaxConfigError as e:
                errors.append(f"{edition_name}/{province_code}: {e}")

    if errors:
        logger.warning(f"Tax table validation found {len(errors)} error(s)")
        for error in errors:
            logger.warning(f"  - {error}")
    else:
        logger.info(f"Tax tables for {year} validated successfully")

    return errors


# =============================================================================
# Module Initialization
# =============================================================================

def _init_module() -> None:
    """Initialize module and validate configuration on import."""
    try:
        errors = validate_tax_tables(2025)
        if errors:
            logger.warning(
                f"Tax table validation warnings: {len(errors)} issue(s) found. "
                "Run validate_tax_tables() for details."
            )
    except Exception as e:
        logger.error(f"Failed to validate tax tables on startup: {e}")


# Run validation on import (optional - can be disabled for performance)
# Uncomment the line below to enable startup validation:
# _init_module()
