"""
Holiday Pay Configuration Loader

Loads holiday pay configurations from JSON files with year/edition versioning.
Supports mid-year policy changes (e.g., Alberta 2019-09-01 formula change).

Configuration files are located at:
    backend/config/holiday_pay/{year}/provinces_{edition}.json

Reference: docs/08_holidays_vacation.md
"""

from __future__ import annotations

import json
import logging
from datetime import date
from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.models.holiday_pay_config import (
    HolidayPayConfig,
    HolidayPayEligibility,
    HolidayPayFormulaParams,
)

logger = logging.getLogger(__name__)

# Base path for holiday pay configuration files
CONFIG_BASE_PATH = Path(__file__).parent.parent.parent.parent / "config" / "holiday_pay"

# Default BC configuration for fallback
DEFAULT_BC_CONFIG = HolidayPayConfig(
    province_code="BC",
    formula_type="30_day_average",
    formula_params=HolidayPayFormulaParams(
        lookback_days=30,
        method="total_wages_div_days",
        include_overtime=False,
        default_daily_hours=Decimal("8"),
    ),
    eligibility=HolidayPayEligibility(
        min_employment_days=30,
        require_last_first_rule=False,
    ),
    premium_rate=Decimal("1.5"),
    notes="Default BC formula fallback",
)


# =============================================================================
# JSON CONFIGURATION LOADING
# =============================================================================


@lru_cache(maxsize=8)
def _load_json_file(file_path: str) -> dict[str, Any]:
    """
    Load and parse a JSON configuration file.

    Args:
        file_path: Path to the JSON file

    Returns:
        Parsed JSON as dictionary

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is invalid JSON
    """
    with open(file_path, encoding="utf-8") as f:
        return json.load(f)


def _get_available_editions(year: int) -> list[tuple[str, date, date]]:
    """
    Get all available editions for a year with their effective date ranges.

    Args:
        year: Year to check

    Returns:
        List of (edition, effective_date, end_date) tuples, sorted by effective_date
    """
    year_path = CONFIG_BASE_PATH / str(year)
    if not year_path.exists():
        return []

    editions = []
    for file in year_path.glob("provinces_*.json"):
        edition = file.stem.replace("provinces_", "")
        try:
            data = _load_json_file(str(file))
            effective = date.fromisoformat(data["effective_date"])
            end = date.fromisoformat(data["end_date"])
            editions.append((edition, effective, end))
        except (KeyError, ValueError, json.JSONDecodeError) as e:
            logger.warning(f"Invalid config file {file}: {e}")
            continue

    return sorted(editions, key=lambda x: x[1])


def _get_edition_for_date(year: int, pay_date: date | None = None) -> str:
    """
    Determine which edition to use based on the pay date.

    Args:
        year: Configuration year
        pay_date: Date to check (defaults to today)

    Returns:
        Edition name (e.g., "jan", "sep")
    """
    if pay_date is None:
        pay_date = date.today()

    editions = _get_available_editions(year)

    if not editions:
        return "jan"  # Default to jan if no editions found

    # Find the latest edition that is effective on or before pay_date
    selected = editions[0][0]  # Default to first edition
    for edition, effective_date, end_date in editions:
        if effective_date <= pay_date:
            selected = edition
        else:
            break

    return selected


def _load_provinces_config(year: int, edition: str) -> dict[str, Any]:
    """
    Load province configurations for a specific year and edition.

    Args:
        year: Configuration year
        edition: Edition name (e.g., "jan", "sep")

    Returns:
        Dictionary with configuration data
    """
    file_path = CONFIG_BASE_PATH / str(year) / f"provinces_{edition}.json"

    if not file_path.exists():
        logger.warning(f"Config file not found: {file_path}")
        return {"provinces": {}}

    return _load_json_file(str(file_path))


def _dict_to_config(province_data: dict[str, Any]) -> HolidayPayConfig:
    """
    Convert a dictionary to HolidayPayConfig dataclass.

    Args:
        province_data: Dictionary with province configuration

    Returns:
        HolidayPayConfig instance
    """
    formula_params_dict = province_data.get("formula_params", {})
    eligibility_dict = province_data.get("eligibility", {})

    # Parse percentage if present (convert float to Decimal)
    percentage = formula_params_dict.get("percentage")
    if percentage is not None:
        percentage = Decimal(str(percentage))

    formula_params = HolidayPayFormulaParams(
        lookback_weeks=formula_params_dict.get("lookback_weeks"),
        lookback_days=formula_params_dict.get("lookback_days"),
        divisor=formula_params_dict.get("divisor"),
        method=formula_params_dict.get("method"),
        include_vacation_pay=formula_params_dict.get("include_vacation_pay", False),
        include_overtime=formula_params_dict.get("include_overtime", False),
        default_daily_hours=Decimal(str(formula_params_dict.get("default_daily_hours", 8))),
        # For Saskatchewan 5% formula
        percentage=percentage,
        include_previous_holiday_pay=formula_params_dict.get("include_previous_holiday_pay", False),
        # New employee fallback handling
        new_employee_fallback=formula_params_dict.get("new_employee_fallback"),
    )

    eligibility = HolidayPayEligibility(
        min_employment_days=eligibility_dict.get("min_employment_days", 30),
        require_last_first_rule=eligibility_dict.get("require_last_first_rule", False),
        notes=eligibility_dict.get("notes"),
    )

    return HolidayPayConfig(
        province_code=province_data["province_code"],
        formula_type=province_data["formula_type"],
        formula_params=formula_params,
        eligibility=eligibility,
        premium_rate=Decimal(str(province_data.get("premium_rate", 1.5))),
        name=province_data.get("name"),
        notes=province_data.get("notes"),
    )


# =============================================================================
# PUBLIC API - JSON-BASED CONFIGURATION
# =============================================================================


def get_config(
    province_code: str, year: int = 2025, pay_date: date | None = None
) -> HolidayPayConfig:
    """
    Get holiday pay configuration for a province.

    Args:
        province_code: Province code (e.g., 'BC', 'ON', 'Federal')
        year: Configuration year (default: 2025)
        pay_date: Date to determine which edition to use (default: today)

    Returns:
        HolidayPayConfig (returns DEFAULT_BC_CONFIG if province not found)
    """
    edition = _get_edition_for_date(year, pay_date)
    config_data = _load_provinces_config(year, edition)
    province_data = config_data.get("provinces", {}).get(province_code)

    if province_data:
        return _dict_to_config(province_data)

    # Fall back to BC config for unknown provinces
    logger.info(f"No config found for province {province_code}, using BC default")
    return DEFAULT_BC_CONFIG


def get_all_configs(
    year: int = 2025, pay_date: date | None = None
) -> dict[str, HolidayPayConfig]:
    """
    Get all holiday pay configurations for a year.

    Args:
        year: Configuration year (default: 2025)
        pay_date: Date to determine which edition to use (default: today)

    Returns:
        Dictionary mapping province codes to HolidayPayConfig
    """
    edition = _get_edition_for_date(year, pay_date)
    config_data = _load_provinces_config(year, edition)

    result: dict[str, HolidayPayConfig] = {}
    for province_code, province_data in config_data.get("provinces", {}).items():
        result[province_code] = _dict_to_config(province_data)

    return result


def get_config_metadata(year: int = 2025, pay_date: date | None = None) -> dict[str, Any]:
    """
    Get metadata about the holiday pay configuration.

    Args:
        year: Configuration year
        pay_date: Date to determine which edition to use

    Returns:
        Dictionary with metadata (year, edition, effective_date, source, etc.)
    """
    edition = _get_edition_for_date(year, pay_date)
    config_data = _load_provinces_config(year, edition)

    return {
        "year": config_data.get("year", year),
        "edition": config_data.get("edition", edition),
        "effective_date": config_data.get("effective_date"),
        "end_date": config_data.get("end_date"),
        "source": config_data.get("source"),
        "changes": config_data.get("changes", []),
    }


def clear_cache() -> None:
    """Clear the LRU cache for JSON file loading."""
    _load_json_file.cache_clear()


# =============================================================================
# LOADER CLASS (for dependency injection)
# =============================================================================


class HolidayPayConfigLoader:
    """
    Holiday Pay Configuration Loader.

    Provides a class-based interface for loading holiday pay configurations.
    Useful for dependency injection in calculators and services.
    """

    def __init__(self, year: int = 2025, pay_date: date | None = None):
        """
        Initialize config loader.

        Args:
            year: Configuration year
            pay_date: Date to determine which edition to use
        """
        self.year = year
        self.pay_date = pay_date
        self._configs = get_all_configs(year, pay_date)

    def get_config(self, province_code: str) -> HolidayPayConfig:
        """
        Get holiday pay configuration for a province.

        Args:
            province_code: Province code (e.g., 'BC', 'ON', 'Federal')

        Returns:
            HolidayPayConfig (returns DEFAULT_BC_CONFIG if not found)
        """
        config = self._configs.get(province_code)
        if config:
            return config

        # Fall back to BC config for unknown provinces
        logger.info(f"No config found for province {province_code}, using BC default")
        return DEFAULT_BC_CONFIG

    def get_all_configs(self) -> dict[str, HolidayPayConfig]:
        """Get all holiday pay configurations."""
        return self._configs

    def clear_cache(self) -> None:
        """Clear the configuration cache and reload."""
        clear_cache()
        self._configs = get_all_configs(self.year, self.pay_date)
