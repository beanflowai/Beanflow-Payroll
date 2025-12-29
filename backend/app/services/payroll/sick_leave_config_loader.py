"""
Sick Leave Configuration Loader

Loads sick leave configurations from JSON files with year/edition versioning.
Supports mid-year changes (e.g., Ontario June 2025 long-term sick leave).

Configuration files are located at:
    backend/config/sick_leave/{year}/provinces_{edition}.json

Reference: docs/08_holidays_vacation.md Task 8.7
"""

from __future__ import annotations

import json
import logging
from datetime import date
from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from typing import Any

from supabase import Client

from app.services.payroll.sick_leave_service import (
    SickLeaveBalance,
    SickLeaveConfig,
)

logger = logging.getLogger(__name__)

# Base path for sick leave configuration files
CONFIG_BASE_PATH = Path(__file__).parent.parent.parent.parent / "config" / "sick_leave"


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
        Edition name (e.g., "jan", "jun")
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
        edition: Edition name (e.g., "jan", "jun")

    Returns:
        Dictionary with configuration data
    """
    file_path = CONFIG_BASE_PATH / str(year) / f"provinces_{edition}.json"

    if not file_path.exists():
        logger.warning(f"Config file not found: {file_path}")
        return {"provinces": {}}

    return _load_json_file(str(file_path))


def _dict_to_config(province_data: dict[str, Any]) -> SickLeaveConfig:
    """
    Convert a dictionary to SickLeaveConfig dataclass.

    Args:
        province_data: Dictionary with province configuration

    Returns:
        SickLeaveConfig instance
    """
    return SickLeaveConfig(
        province_code=province_data["province_code"],
        paid_days_per_year=province_data["paid_days_per_year"],
        unpaid_days_per_year=province_data["unpaid_days_per_year"],
        waiting_period_days=province_data["waiting_period_days"],
        allows_carryover=province_data["allows_carryover"],
        max_carryover_days=province_data["max_carryover_days"],
        accrual_method=province_data["accrual_method"],
        initial_days_after_qualifying=province_data.get(
            "initial_days_after_qualifying", 0
        ),
        days_per_month_after_initial=province_data.get(
            "days_per_month_after_initial", 0
        ),
    )


# =============================================================================
# PUBLIC API - JSON-BASED CONFIGURATION
# =============================================================================


def get_config(
    province_code: str, year: int = 2025, pay_date: date | None = None
) -> SickLeaveConfig | None:
    """
    Get sick leave configuration for a province.

    Args:
        province_code: Province code (e.g., 'BC', 'ON', 'Federal')
        year: Configuration year (default: 2025)
        pay_date: Date to determine which edition to use (default: today)

    Returns:
        SickLeaveConfig or None if not found
    """
    edition = _get_edition_for_date(year, pay_date)
    config_data = _load_provinces_config(year, edition)
    province_data = config_data.get("provinces", {}).get(province_code)

    if province_data:
        return _dict_to_config(province_data)

    return None


def get_all_configs(
    year: int = 2025, pay_date: date | None = None
) -> dict[str, SickLeaveConfig]:
    """
    Get all sick leave configurations for a year.

    Args:
        year: Configuration year (default: 2025)
        pay_date: Date to determine which edition to use (default: today)

    Returns:
        Dictionary mapping province codes to SickLeaveConfig
    """
    edition = _get_edition_for_date(year, pay_date)
    config_data = _load_provinces_config(year, edition)

    result: dict[str, SickLeaveConfig] = {}
    for province_code, province_data in config_data.get("provinces", {}).items():
        result[province_code] = _dict_to_config(province_data)

    return result


def get_provinces_with_paid_sick_leave(
    year: int = 2025, pay_date: date | None = None
) -> list[str]:
    """Get list of provinces that have statutory paid sick leave."""
    configs = get_all_configs(year, pay_date)
    return [
        code for code, config in configs.items() if config.paid_days_per_year > 0
    ]


def get_provinces_with_sick_leave_carryover(
    year: int = 2025, pay_date: date | None = None
) -> list[str]:
    """Get list of provinces/jurisdictions that allow sick leave carryover."""
    configs = get_all_configs(year, pay_date)
    return [code for code, config in configs.items() if config.allows_carryover]


def get_config_metadata(year: int = 2025, pay_date: date | None = None) -> dict[str, Any]:
    """
    Get metadata about the sick leave configuration.

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
# DATABASE LOADER CLASS (for employee balance operations)
# =============================================================================


class SickLeaveConfigLoader:
    """
    Loads sick leave configurations and manages employee balances.

    Configuration loading now uses JSON files instead of database.
    Employee balance operations still use Supabase.
    """

    def __init__(self, supabase_client: Client, year: int = 2025, pay_date: date | None = None):
        """
        Initialize config loader.

        Args:
            supabase_client: Supabase client for database access
            year: Configuration year
            pay_date: Date to determine which edition to use
        """
        self.client = supabase_client
        self.year = year
        self.pay_date = pay_date
        self._configs = get_all_configs(year, pay_date)

    def get_config(self, province_code: str) -> SickLeaveConfig | None:
        """
        Get sick leave configuration for a province.

        Args:
            province_code: Province code (e.g., 'BC', 'ON', 'Federal')

        Returns:
            SickLeaveConfig or None if not found
        """
        return self._configs.get(province_code)

    def get_all_configs(self) -> dict[str, SickLeaveConfig]:
        """Get all sick leave configurations."""
        return self._configs

    def clear_cache(self) -> None:
        """Clear the configuration cache and reload."""
        clear_cache()
        self._configs = get_all_configs(self.year, self.pay_date)

    # =========================================================================
    # Employee Balance Operations
    # =========================================================================

    async def get_employee_balance(
        self, employee_id: str, year: int
    ) -> SickLeaveBalance | None:
        """
        Get employee's sick leave balance for a year.

        Args:
            employee_id: Employee UUID
            year: Year to get balance for

        Returns:
            SickLeaveBalance or None if not found
        """
        try:
            response = (
                self.client.table("employee_sick_leave_balances")
                .select("*")
                .eq("employee_id", employee_id)
                .eq("year", year)
                .single()
                .execute()
            )

            if not response.data:
                return None

            row = response.data
            return SickLeaveBalance(
                employee_id=row["employee_id"],
                year=row["year"],
                paid_days_entitled=Decimal(str(row["paid_days_entitled"])),
                unpaid_days_entitled=Decimal(str(row["unpaid_days_entitled"])),
                paid_days_used=Decimal(str(row["paid_days_used"])),
                unpaid_days_used=Decimal(str(row["unpaid_days_used"])),
                carried_over_days=Decimal(str(row["carried_over_days"])),
                is_eligible=row["is_eligible"],
                eligibility_date=(
                    date.fromisoformat(row["eligibility_date"])
                    if row.get("eligibility_date")
                    else None
                ),
                accrued_days_ytd=Decimal(str(row.get("accrued_days_ytd", "0"))),
            )

        except Exception as e:
            logger.error(f"Failed to get employee balance: {e}")
            return None

    async def create_employee_balance(
        self, balance: SickLeaveBalance
    ) -> SickLeaveBalance | None:
        """
        Create a new sick leave balance record for an employee.

        Args:
            balance: SickLeaveBalance to create

        Returns:
            Created SickLeaveBalance or None on failure
        """
        try:
            data = {
                "employee_id": balance.employee_id,
                "year": balance.year,
                "paid_days_entitled": float(balance.paid_days_entitled),
                "unpaid_days_entitled": float(balance.unpaid_days_entitled),
                "paid_days_used": float(balance.paid_days_used),
                "unpaid_days_used": float(balance.unpaid_days_used),
                "carried_over_days": float(balance.carried_over_days),
                "is_eligible": balance.is_eligible,
                "eligibility_date": (
                    balance.eligibility_date.isoformat()
                    if balance.eligibility_date
                    else None
                ),
                "accrued_days_ytd": float(balance.accrued_days_ytd),
            }

            response = (
                self.client.table("employee_sick_leave_balances")
                .insert(data)
                .execute()
            )

            if response.data:
                return balance
            return None

        except Exception as e:
            logger.error(f"Failed to create employee balance: {e}")
            return None

    async def update_employee_balance(
        self,
        employee_id: str,
        year: int,
        paid_days_used_delta: Decimal = Decimal("0"),
        unpaid_days_used_delta: Decimal = Decimal("0"),
    ) -> bool:
        """
        Update employee's sick leave usage.

        Args:
            employee_id: Employee UUID
            year: Year to update
            paid_days_used_delta: Days to add to paid_days_used
            unpaid_days_used_delta: Days to add to unpaid_days_used

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current balance
            current = await self.get_employee_balance(employee_id, year)
            if not current:
                logger.error(f"No balance found for employee {employee_id} year {year}")
                return False

            # Calculate new values
            new_paid_used = current.paid_days_used + paid_days_used_delta
            new_unpaid_used = current.unpaid_days_used + unpaid_days_used_delta

            # Update
            response = (
                self.client.table("employee_sick_leave_balances")
                .update(
                    {
                        "paid_days_used": float(new_paid_used),
                        "unpaid_days_used": float(new_unpaid_used),
                    }
                )
                .eq("employee_id", employee_id)
                .eq("year", year)
                .execute()
            )

            return bool(response.data)

        except Exception as e:
            logger.error(f"Failed to update employee balance: {e}")
            return False

    async def record_sick_leave_usage(
        self,
        employee_id: str,
        balance_id: str,
        payroll_record_id: str | None,
        usage_date: date,
        hours_taken: Decimal,
        days_taken: Decimal,
        is_paid: bool,
        average_day_pay: Decimal,
        sick_pay_amount: Decimal,
        calculation_method: str,
        notes: str | None = None,
    ) -> bool:
        """
        Record sick leave usage in history table.

        Args:
            employee_id: Employee UUID
            balance_id: Balance record UUID
            payroll_record_id: Optional payroll record UUID
            usage_date: Date of sick leave
            hours_taken: Hours taken
            days_taken: Days taken (hours / 8)
            is_paid: Whether this is paid sick leave
            average_day_pay: Calculated average day's pay
            sick_pay_amount: Total sick pay amount
            calculation_method: Method used (bc_30_day_avg, federal_20_day_avg)
            notes: Optional notes

        Returns:
            True if successful, False otherwise
        """
        try:
            data: dict[str, Any] = {
                "employee_id": employee_id,
                "balance_id": balance_id,
                "usage_date": usage_date.isoformat(),
                "hours_taken": float(hours_taken),
                "days_taken": float(days_taken),
                "is_paid": is_paid,
                "average_day_pay": float(average_day_pay),
                "sick_pay_amount": float(sick_pay_amount),
                "calculation_method": calculation_method,
            }

            if payroll_record_id:
                data["payroll_record_id"] = payroll_record_id

            if notes:
                data["notes"] = notes

            response = (
                self.client.table("sick_leave_usage_history").insert(data).execute()
            )

            return bool(response.data)

        except Exception as e:
            logger.error(f"Failed to record sick leave usage: {e}")
            return False
