"""
Payroll Run Constants and Utility Functions

Contains:
- Module-level constants for payroll run operations
- Date extraction and calculation utilities
- BPA (Basic Personal Amount) lookup functions
"""

from __future__ import annotations

import logging
from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal

from app.services.payroll.tax_tables import get_federal_config, get_province_config

logger = logging.getLogger(__name__)

# Fallback Federal BPA when tax table lookup fails
DEFAULT_FEDERAL_BPA_FALLBACK = Decimal("16129")

# Payroll run statuses that count as "completed" for YTD calculations
COMPLETED_RUN_STATUSES = ["approved", "paid"]

# Default fallback year if date parsing fails
DEFAULT_TAX_YEAR = 2025

# Pay periods per year by frequency
PERIODS_PER_YEAR = {
    "weekly": 52,
    "bi_weekly": 26,
    "semi_monthly": 24,
    "monthly": 12,
}

# Default hours per pay period
DEFAULT_HOURS_PER_PERIOD = {
    "weekly": Decimal("40"),
    "bi_weekly": Decimal("80"),
    "semi_monthly": Decimal("86.67"),
    "monthly": Decimal("173.33"),
}


def extract_year_from_date(date_str: str, default: int = DEFAULT_TAX_YEAR) -> int:
    """Safely extract year from a date string (YYYY-MM-DD format).

    Args:
        date_str: Date string in YYYY-MM-DD format
        default: Default year to return if parsing fails

    Returns:
        The extracted year, or default if parsing fails
    """
    if not date_str or not isinstance(date_str, str):
        return default
    try:
        # Ensure we have at least 4 characters and they're digits
        if len(date_str) >= 4 and date_str[:4].isdigit():
            return int(date_str[:4])
        return default
    except (ValueError, TypeError):
        return default


def get_federal_bpa(
    year: int = 2025,
    pay_date: date | None = None
) -> Decimal:
    """Get the Federal Basic Personal Amount from tax tables.

    Args:
        year: Tax year (default: 2025)
        pay_date: Pay date for edition selection (Jan vs Jul edition)

    Returns:
        Federal BPA as Decimal
    """
    try:
        config = get_federal_config(year, pay_date)
        return Decimal(str(config["bpaf"]))
    except Exception as e:
        logger.warning("Failed to get federal BPA: %s, using fallback", e)
        return DEFAULT_FEDERAL_BPA_FALLBACK


def get_provincial_bpa(
    province_code: str,
    year: int = 2025,
    pay_date: date | None = None
) -> Decimal:
    """Get the Basic Personal Amount for a province from tax tables.

    Args:
        province_code: Two-letter province code (e.g., "ON", "SK")
        year: Tax year (default: 2025)
        pay_date: Pay date for edition selection (SK, PE have different BPA in Jan vs Jul)

    Returns:
        Provincial BPA as Decimal
    """
    try:
        config = get_province_config(province_code, year, pay_date)
        return Decimal(str(config["bpa"]))
    except Exception as e:
        logger.warning("Failed to get BPA for %s: %s, using fallback", province_code, e)
        # Fallback to ON default if lookup fails
        return Decimal("12747")


# Maximum days after period end to pay employees (by province)
# Saskatchewan: must pay within 6 days of period end
PAY_DATE_DELAY_DAYS = {
    "SK": 6,
    "ON": 7,  # Ontario
    "BC": 8,  # British Columbia
    "AB": 10,  # Alberta
    "MB": 10,  # Manitoba
    "QC": 16,  # Quebec (can be longer based on contract)
    "NB": 5,  # New Brunswick
    "NS": 5,  # Nova Scotia
    "PE": 7,  # Prince Edward Island
    "NL": 7,  # Newfoundland and Labrador
    "NT": 10,  # Northwest Territories
    "NU": 10,  # Nunavut
    "YT": 10,  # Yukon
}
DEFAULT_PAY_DATE_DELAY = 7  # Default to 7 days if province not specified


def calculate_pay_date(period_end: date, province: str = "SK") -> date:
    """Calculate pay date based on period end and province regulations.

    Saskatchewan law requires paying employees within 6 days of pay period end.
    Other provinces have different requirements.

    Args:
        period_end: The pay period end date
        province: Two-letter province code (default: "SK")

    Returns:
        The calculated pay date
    """
    delay_days = PAY_DATE_DELAY_DAYS.get(province, DEFAULT_PAY_DATE_DELAY)
    return period_end + timedelta(days=delay_days)


def calculate_next_period_end(current_period_end: date, pay_frequency: str) -> date:
    """Calculate the next period end date based on pay frequency.

    Args:
        current_period_end: The current pay period end date
        pay_frequency: One of 'weekly', 'bi_weekly', 'semi_monthly', 'monthly'

    Returns:
        The next period end date
    """
    if pay_frequency == "weekly":
        return current_period_end + timedelta(days=7)
    elif pay_frequency == "bi_weekly":
        return current_period_end + timedelta(days=14)
    elif pay_frequency == "semi_monthly":
        # Period ends are either 15th or last day of month
        if current_period_end.day <= 15:
            # Current is 15th, next is end of month
            last_day = monthrange(current_period_end.year, current_period_end.month)[1]
            return current_period_end.replace(day=last_day)
        else:
            # Current is end of month, next is 15th of next month
            if current_period_end.month == 12:
                return date(current_period_end.year + 1, 1, 15)
            else:
                return date(current_period_end.year, current_period_end.month + 1, 15)
    elif pay_frequency == "monthly":
        # Check if current period end is the last day of its month
        current_month_last_day = monthrange(
            current_period_end.year, current_period_end.month
        )[1]
        is_last_day_of_month = current_period_end.day == current_month_last_day

        # Calculate next month
        if current_period_end.month == 12:
            next_month = date(current_period_end.year + 1, 1, 1)
        else:
            next_month = date(current_period_end.year, current_period_end.month + 1, 1)
        next_month_last_day = monthrange(next_month.year, next_month.month)[1]

        if is_last_day_of_month:
            # If period ends on last day of month, always use last day
            return next_month.replace(day=next_month_last_day)
        else:
            # Use same day, or last day if month is shorter
            return next_month.replace(day=min(current_period_end.day, next_month_last_day))
    else:
        # Default to bi-weekly
        return current_period_end + timedelta(days=14)


# Legacy function - kept for backward compatibility
def calculate_next_pay_date(current_pay_date: date, pay_frequency: str) -> date:
    """Calculate the next pay date based on pay frequency.

    Args:
        current_pay_date: The current/just-completed pay date
        pay_frequency: One of 'weekly', 'bi_weekly', 'semi_monthly', 'monthly'

    Returns:
        The next scheduled pay date
    """
    if pay_frequency == "weekly":
        return current_pay_date + timedelta(days=7)
    elif pay_frequency == "bi_weekly":
        return current_pay_date + timedelta(days=14)
    elif pay_frequency == "semi_monthly":
        # If current is around 15th, next is end of month
        # If current is around end of month, next is 15th of next month
        if current_pay_date.day <= 15:
            # Move to end of current month
            last_day = monthrange(current_pay_date.year, current_pay_date.month)[1]
            return current_pay_date.replace(day=last_day)
        else:
            # Move to 15th of next month
            if current_pay_date.month == 12:
                return date(current_pay_date.year + 1, 1, 15)
            else:
                return date(current_pay_date.year, current_pay_date.month + 1, 15)
    elif pay_frequency == "monthly":
        # Check if current pay date is the last day of its month
        current_month_last_day = monthrange(
            current_pay_date.year, current_pay_date.month
        )[1]
        is_last_day_of_month = current_pay_date.day == current_month_last_day

        # Calculate next month
        if current_pay_date.month == 12:
            next_month = date(current_pay_date.year + 1, 1, 1)
        else:
            next_month = date(current_pay_date.year, current_pay_date.month + 1, 1)
        next_month_last_day = monthrange(next_month.year, next_month.month)[1]

        if is_last_day_of_month:
            # If paid on last day of month, always use last day
            # e.g., Jan 31 -> Feb 28 -> Mar 31
            return next_month.replace(day=next_month_last_day)
        else:
            # Use same day, or last day if month is shorter
            return next_month.replace(day=min(current_pay_date.day, next_month_last_day))
    else:
        # Default to bi-weekly
        return current_pay_date + timedelta(days=14)
