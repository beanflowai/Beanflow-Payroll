"""
Vacation Pay Configuration Loader

Loads vacation pay configurations from JSON files with year/edition versioning.
Each province has different minimum vacation entitlements based on years of service.

Configuration files are located at:
    backend/config/vacation_pay/{year}/provinces_{edition}.json

Key insight: Saskatchewan (SK) has the highest minimum at 5.77% (3 weeks) from day one,
while most other provinces start at 4% (2 weeks).

Reference: docs/references/vacation_pay/
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from typing import Any, cast

logger = logging.getLogger(__name__)

# Base path for vacation pay configuration files
CONFIG_BASE_PATH = Path(__file__).parent.parent.parent.parent / "config" / "vacation_pay"


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass(frozen=True)
class VacationTier:
    """A vacation pay tier based on years of service."""

    min_years_of_service: int
    vacation_weeks: int
    vacation_rate: Decimal
    notes: str | None = None


@dataclass(frozen=True)
class ProvinceVacationConfig:
    """Vacation pay configuration for a province."""

    province_code: str
    name: str
    tiers: tuple[VacationTier, ...]
    notes: str | None = None

    def get_tier_for_years(self, years_of_service: int) -> VacationTier:
        """
        Get the applicable vacation tier for given years of service.

        Args:
            years_of_service: Number of complete years of service

        Returns:
            The applicable VacationTier (highest tier where years >= min_years)
        """
        applicable_tier = self.tiers[0]  # Default to first tier
        for tier in self.tiers:
            if years_of_service >= tier.min_years_of_service:
                applicable_tier = tier
            else:
                break
        return applicable_tier

    def get_minimum_rate(self, years_of_service: int) -> Decimal:
        """
        Get the minimum vacation pay rate for given years of service.

        Args:
            years_of_service: Number of complete years of service

        Returns:
            Minimum vacation rate as Decimal (e.g., 0.04 for 4%)
        """
        return self.get_tier_for_years(years_of_service).vacation_rate

    def get_minimum_weeks(self, years_of_service: int) -> int:
        """
        Get the minimum vacation weeks for given years of service.

        Args:
            years_of_service: Number of complete years of service

        Returns:
            Minimum vacation weeks entitled
        """
        return self.get_tier_for_years(years_of_service).vacation_weeks


# Default BC configuration for fallback
DEFAULT_CONFIG = ProvinceVacationConfig(
    province_code="BC",
    name="British Columbia (Default)",
    tiers=(
        VacationTier(
            min_years_of_service=0,
            vacation_weeks=2,
            vacation_rate=Decimal("0.04"),
            notes="2 weeks minimum",
        ),
        VacationTier(
            min_years_of_service=5,
            vacation_weeks=3,
            vacation_rate=Decimal("0.06"),
            notes="3 weeks after 5 years",
        ),
    ),
    notes="Default BC configuration fallback",
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
        return cast(dict[str, Any], json.load(f))


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
        Edition name (e.g., "jan", "jul")
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
        edition: Edition name (e.g., "jan", "jul")

    Returns:
        Dictionary with configuration data
    """
    file_path = CONFIG_BASE_PATH / str(year) / f"provinces_{edition}.json"

    if not file_path.exists():
        logger.warning(f"Config file not found: {file_path}")
        return {"provinces": {}}

    return _load_json_file(str(file_path))


def _dict_to_config(province_data: dict[str, Any]) -> ProvinceVacationConfig:
    """
    Convert a dictionary to ProvinceVacationConfig dataclass.

    Args:
        province_data: Dictionary with province configuration

    Returns:
        ProvinceVacationConfig instance
    """
    tiers_list = []
    for tier_data in province_data.get("tiers", []):
        tiers_list.append(
            VacationTier(
                min_years_of_service=tier_data["min_years_of_service"],
                vacation_weeks=tier_data["vacation_weeks"],
                vacation_rate=Decimal(str(tier_data["vacation_rate"])),
                notes=tier_data.get("notes"),
            )
        )

    # Sort tiers by min_years_of_service
    tiers_list.sort(key=lambda t: t.min_years_of_service)

    return ProvinceVacationConfig(
        province_code=province_data["province_code"],
        name=province_data["name"],
        tiers=tuple(tiers_list),
        notes=province_data.get("notes"),
    )


# =============================================================================
# PUBLIC API - JSON-BASED CONFIGURATION
# =============================================================================


def get_config(
    province_code: str, year: int = 2025, pay_date: date | None = None
) -> ProvinceVacationConfig:
    """
    Get vacation pay configuration for a province.

    Args:
        province_code: Province code (e.g., 'BC', 'ON', 'Federal')
        year: Configuration year (default: 2025)
        pay_date: Date to determine which edition to use (default: today)

    Returns:
        ProvinceVacationConfig (returns DEFAULT_CONFIG if province not found)
    """
    edition = _get_edition_for_date(year, pay_date)
    config_data = _load_provinces_config(year, edition)
    province_data = config_data.get("provinces", {}).get(province_code)

    if province_data:
        return _dict_to_config(province_data)

    # Fall back to default config for unknown provinces
    logger.info(f"No config found for province {province_code}, using default")
    return DEFAULT_CONFIG


def get_all_configs(
    year: int = 2025, pay_date: date | None = None
) -> dict[str, ProvinceVacationConfig]:
    """
    Get all vacation pay configurations for a year.

    Args:
        year: Configuration year (default: 2025)
        pay_date: Date to determine which edition to use (default: today)

    Returns:
        Dictionary mapping province codes to ProvinceVacationConfig
    """
    edition = _get_edition_for_date(year, pay_date)
    config_data = _load_provinces_config(year, edition)

    result: dict[str, ProvinceVacationConfig] = {}
    for province_code, province_data in config_data.get("provinces", {}).items():
        result[province_code] = _dict_to_config(province_data)

    return result


def get_minimum_rate(
    province_code: str,
    years_of_service: int,
    year: int = 2025,
    pay_date: date | None = None,
) -> Decimal:
    """
    Get the minimum vacation pay rate for a province and years of service.

    This is the main function used during payroll calculation to determine
    the statutory minimum vacation rate an employee is entitled to.

    Args:
        province_code: Province code (e.g., 'BC', 'ON', 'Federal', 'SK')
        years_of_service: Number of complete years of service
        year: Configuration year (default: 2025)
        pay_date: Date to determine which edition to use (default: today)

    Returns:
        Minimum vacation rate as Decimal (e.g., Decimal("0.04") for 4%)

    Example:
        >>> get_minimum_rate("SK", 0)  # Saskatchewan, new employee
        Decimal('0.0577')  # 5.77% (3 weeks)
        >>> get_minimum_rate("SK", 10)  # Saskatchewan, 10+ years
        Decimal('0.0769')  # 7.69% (4 weeks)
        >>> get_minimum_rate("ON", 0)  # Ontario, new employee
        Decimal('0.04')  # 4% (2 weeks)
    """
    config = get_config(province_code, year, pay_date)
    return config.get_minimum_rate(years_of_service)


def get_config_metadata(year: int = 2025, pay_date: date | None = None) -> dict[str, Any]:
    """
    Get metadata about the vacation pay configuration.

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
        "notes": config_data.get("notes"),
    }


def clear_cache() -> None:
    """Clear the LRU cache for JSON file loading."""
    _load_json_file.cache_clear()


# =============================================================================
# LOADER CLASS (for dependency injection)
# =============================================================================


class VacationPayConfigLoader:
    """
    Vacation Pay Configuration Loader.

    Provides a class-based interface for loading vacation pay configurations.
    Useful for dependency injection in calculators and services.

    Example:
        loader = VacationPayConfigLoader(year=2025)

        # Get minimum rate for SK employee with 5 years of service
        rate = loader.get_minimum_rate("SK", 5)  # Returns Decimal("0.0577")

        # Get effective rate considering employee override
        effective = loader.get_effective_rate("SK", 5, override=Decimal("0.08"))
        # Returns Decimal("0.08") since 8% > 5.77% minimum
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

    def get_config(self, province_code: str) -> ProvinceVacationConfig:
        """
        Get vacation pay configuration for a province.

        Args:
            province_code: Province code (e.g., 'BC', 'ON', 'Federal')

        Returns:
            ProvinceVacationConfig (returns DEFAULT_CONFIG if not found)
        """
        config = self._configs.get(province_code)
        if config:
            return config

        # Fall back to default config for unknown provinces
        logger.info(f"No config found for province {province_code}, using default")
        return DEFAULT_CONFIG

    def get_all_configs(self) -> dict[str, ProvinceVacationConfig]:
        """Get all vacation pay configurations."""
        return self._configs

    def get_minimum_rate(self, province_code: str, years_of_service: int) -> Decimal:
        """
        Get minimum vacation pay rate for a province and years of service.

        Args:
            province_code: Province code
            years_of_service: Number of complete years of service

        Returns:
            Minimum vacation rate as Decimal
        """
        config = self.get_config(province_code)
        return config.get_minimum_rate(years_of_service)

    def get_effective_rate(
        self,
        province_code: str,
        years_of_service: int,
        override: Decimal | None = None,
    ) -> Decimal:
        """
        Get effective vacation pay rate, considering any override.

        If an override is provided, it must be >= the provincial minimum.
        If override is None, returns the provincial minimum.

        Args:
            province_code: Province code
            years_of_service: Number of complete years of service
            override: Optional override rate from employer

        Returns:
            Effective vacation rate as Decimal

        Raises:
            ValueError: If override is below provincial minimum
        """
        min_rate = self.get_minimum_rate(province_code, years_of_service)

        if override is None:
            return min_rate

        if override < min_rate:
            raise ValueError(
                f"Override rate {override} is below provincial minimum {min_rate} "
                f"for {province_code} with {years_of_service} years of service"
            )

        return override

    def clear_cache(self) -> None:
        """Clear the configuration cache and reload."""
        clear_cache()
        self._configs = get_all_configs(self.year, self.pay_date)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def calculate_years_of_service(hire_date: date, reference_date: date | None = None) -> int:
    """
    Calculate complete years of service from hire date.

    Args:
        hire_date: Employee's hire date
        reference_date: Date to calculate from (default: today)

    Returns:
        Number of complete years of service
    """
    if reference_date is None:
        reference_date = date.today()

    years = reference_date.year - hire_date.year

    # Adjust if anniversary hasn't occurred yet this year
    if (reference_date.month, reference_date.day) < (hire_date.month, hire_date.day):
        years -= 1

    return max(0, years)
