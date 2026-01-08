"""
Holiday Pay Configuration Models

Data classes for holiday pay calculation configuration.
Loaded from JSON files in backend/config/holiday_pay/
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class HolidayPayEligibility:
    """Eligibility rules for holiday pay."""

    min_employment_days: int
    require_last_first_rule: bool
    min_days_worked_in_period: int | None = None  # PE requires 15 days worked in 30-day period
    notes: str | None = None


@dataclass
class HolidayPayFormulaParams:
    """Parameters for holiday pay calculation formulas."""

    # For 4_week_average formula (Ontario)
    lookback_weeks: int | None = None
    divisor: int | None = None
    include_vacation_pay: bool = False

    # For 30_day_average formula (BC and others)
    lookback_days: int | None = None
    method: str | None = None  # "total_wages_div_days", "wages_div_days_worked", "hours_times_rate"

    # For 5_percent_28_days formula (Saskatchewan)
    percentage: Decimal | None = None  # e.g., 0.05 for 5%
    include_previous_holiday_pay: bool = False

    # Common parameters
    include_overtime: bool = False
    default_daily_hours: Decimal = field(default_factory=lambda: Decimal("8"))

    # New employee handling when no historical payroll data available
    # - "pro_rated": Use current period gross for calculation (SK, ON)
    # - "ineligible": Return $0, employee not eligible without history (BC, AB)
    # - None: Default to "ineligible" behavior
    new_employee_fallback: str | None = None


@dataclass
class HolidayPayConfig:
    """Holiday pay configuration for a province."""

    province_code: str
    # Formula types:
    # - "4_week_average": Ontario style (wages + vacation) / 20
    # - "30_day_average": BC style, average daily pay
    # - "4_week_average_daily": Alberta style, wages / days worked
    # - "current_period_daily": Current period gross / work days
    # - "5_percent_28_days": Saskatchewan style, 5% of past 28 days wages
    formula_type: str
    formula_params: HolidayPayFormulaParams
    eligibility: HolidayPayEligibility
    premium_rate: Decimal
    name: str | None = None
    notes: str | None = None
