"""
Overtime Calculator Service

Calculates regular/overtime split based on province-specific rules.
This is the backend equivalent of the frontend overtimeCalculator.ts.

Rules:
- Daily threshold provinces (AB, BC, NT, NU, YT): Hours exceeding daily threshold → OT
- Weekly threshold provinces (ON, QC, etc.): Total weekly hours exceeding threshold → OT
- BC special: Hours > 12/day → double-time
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.services.payroll.province_standards import (
    OVERTIME_RULES,
    InvalidProvinceCodeError,
    VALID_PROVINCE_CODES,
)


@dataclass
class DailyHoursEntry:
    """Daily hours entry for overtime calculation."""

    date: str  # ISO date string YYYY-MM-DD
    total_hours: Decimal
    is_holiday: bool


@dataclass
class OvertimeResult:
    """Result of overtime calculation."""

    regular_hours: Decimal
    overtime_hours: Decimal
    double_time_hours: Decimal


class InvalidDateFormatError(ValueError):
    """Raised when date string is not in valid YYYY-MM-DD format."""

    def __init__(self, date_str: str):
        self.date_str = date_str
        super().__init__(f"Invalid date format: '{date_str}'. Expected YYYY-MM-DD.")


def _parse_local_date(date_str: str) -> datetime:
    """Parse an ISO date string as local date.

    Args:
        date_str: Date string in YYYY-MM-DD format

    Returns:
        datetime object

    Raises:
        InvalidDateFormatError: If date string is not valid
    """
    if not date_str or not isinstance(date_str, str):
        raise InvalidDateFormatError(str(date_str))

    parts = date_str.split("-")
    if len(parts) != 3:
        raise InvalidDateFormatError(date_str)

    try:
        year, month, day = map(int, parts)
        return datetime(year, month, day)
    except (ValueError, TypeError) as e:
        raise InvalidDateFormatError(date_str) from e


def _split_into_weeks(entries: list[DailyHoursEntry]) -> list[list[DailyHoursEntry]]:
    """
    Split entries into weeks (Monday to Sunday).

    Args:
        entries: All daily entries for the pay period

    Returns:
        List of week lists, each containing entries for Mon-Sun
    """
    if not entries:
        return []

    # Sort entries by date to ensure correct week boundaries
    sorted_entries = sorted(entries, key=lambda e: e.date)

    weeks: list[list[DailyHoursEntry]] = []
    current_week: list[DailyHoursEntry] = []

    for entry in sorted_entries:
        date = _parse_local_date(entry.date)
        day_of_week = date.weekday()  # 0=Mon, 6=Sun

        # Start new week on Monday (day_of_week == 0)
        if day_of_week == 0 and current_week:
            weeks.append(current_week)
            current_week = []

        current_week.append(entry)

    # Push the last week
    if current_week:
        weeks.append(current_week)

    return weeks


def calculate_overtime_split(
    entries: list[DailyHoursEntry],
    province: str,
) -> OvertimeResult:
    """
    Calculate regular/overtime split based on province rules.

    Logic:
    1. If dailyThreshold exists (AB/BC/NT/NU/YT): Per-day hours exceeding threshold → OT
    2. If no dailyThreshold (ON/QC/etc.): Sum weekly hours, exceeding weeklyThreshold → OT
    3. BC special: Hours > 12/day → double-time (if doubleTimeDaily is set)

    Args:
        entries: List of daily hours entries
        province: Province code (e.g., 'ON', 'BC', 'AB')

    Returns:
        OvertimeResult with regular, overtime, and double-time hours

    Raises:
        InvalidProvinceCodeError: If province code is not valid
    """
    # Validate province code
    if province not in VALID_PROVINCE_CODES:
        raise InvalidProvinceCodeError(province)

    # Get overtime rules for the province
    rules = OVERTIME_RULES.get(province, OVERTIME_RULES["Federal"])

    daily_threshold = rules.get("daily_threshold")
    weekly_threshold = Decimal(str(rules["weekly_threshold"]))
    double_time_daily = rules.get("double_time_daily")

    regular_hours = Decimal("0")
    overtime_hours = Decimal("0")
    double_time_hours = Decimal("0")

    # Group entries by week (Mon-Sun)
    weeks = _split_into_weeks(entries)

    for week_entries in weeks:
        if daily_threshold is not None:
            # Province has daily threshold (AB, BC, NT, NU, YT)
            # Calculate per-day first, then apply weekly threshold on remaining
            daily_threshold_dec = Decimal(str(daily_threshold))
            double_time_daily_dec = (
                Decimal(str(double_time_daily)) if double_time_daily else None
            )

            week_regular = Decimal("0")
            week_overtime = Decimal("0")
            week_double_time = Decimal("0")

            for entry in week_entries:
                if entry.is_holiday or entry.total_hours <= 0:
                    continue

                daily_hours = entry.total_hours

                # Check for double-time (BC: > 12 hours)
                if double_time_daily_dec and daily_hours > double_time_daily_dec:
                    week_double_time += daily_hours - double_time_daily_dec
                    week_overtime += double_time_daily_dec - daily_threshold_dec
                    week_regular += daily_threshold_dec
                elif daily_hours > daily_threshold_dec:
                    # Daily overtime
                    week_overtime += daily_hours - daily_threshold_dec
                    week_regular += daily_threshold_dec
                else:
                    week_regular += daily_hours

            # For daily threshold provinces, also check weekly threshold
            # Any regular hours exceeding weekly threshold become overtime
            if week_regular > weekly_threshold:
                weekly_overflow = week_regular - weekly_threshold
                week_overtime += weekly_overflow
                week_regular = weekly_threshold

            regular_hours += week_regular
            overtime_hours += week_overtime
            double_time_hours += week_double_time
        else:
            # Province has weekly threshold only (ON, QC, MB, NB, NL, NS, PE, SK)
            week_total = Decimal("0")

            for entry in week_entries:
                if entry.is_holiday or entry.total_hours <= 0:
                    continue
                week_total += entry.total_hours

            # Apply weekly threshold
            if week_total > weekly_threshold:
                regular_hours += weekly_threshold
                overtime_hours += week_total - weekly_threshold
            else:
                regular_hours += week_total

    # Round to 2 decimal places
    return OvertimeResult(
        regular_hours=regular_hours.quantize(Decimal("0.01")),
        overtime_hours=overtime_hours.quantize(Decimal("0.01")),
        double_time_hours=double_time_hours.quantize(Decimal("0.01")),
    )
