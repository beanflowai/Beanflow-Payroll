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
    # Alberta-style: count actual work days instead of calendar days for eligibility
    # If True, min_employment_days means "min work days in eligibility_period_months"
    count_work_days: bool = False
    eligibility_period_months: int = 12  # Period to look back for work days (default: 12 months)
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

    # Configurable time periods (in days)
    lookback_period_days: int | None = None  # e.g., 28 for 4-week lookback
    eligibility_lookback_days: int | None = None  # For eligibility checks (e.g., 30 days before/after)
    last_first_window_days: int | None = None  # For last/first rule search window

    # Alberta-specific "5 of 9" rule parameters
    alberta_5_of_9_weeks: int | None = None  # Number of weeks to check (default: 9)
    alberta_5_of_9_threshold: int | None = None  # Days worked threshold (default: 5)

    # Manitoba construction industry special percentage
    construction_percentage: Decimal | None = None  # e.g., 0.04 for 4%

    # Alberta incentive pay percentage (4.2%)
    incentive_pay_percentage: Decimal | None = None  # e.g., 0.042 for 4.2%

    # Quebec commission employee formula (1/60 of 12 weeks)
    commission_divisor: int | None = None  # e.g., 60 for 1/60
    commission_lookback_weeks: int | None = None  # e.g., 12 weeks

    # Yukon irregular hours formula (10% of 2 weeks)
    irregular_hours_percentage: Decimal | None = None  # e.g., 0.10 for 10%
    irregular_hours_lookback_weeks: int | None = None  # e.g., 2 weeks

    # Newfoundland 3-week lookback (hours / 15)
    lookback_weeks_nl: int | None = None  # e.g., 3 weeks for NL
    nl_divisor: int | None = None  # e.g., 15 for NL formula


@dataclass
class PremiumRateTier:
    """A tier for premium pay rates based on hours worked."""

    hours_threshold: Decimal  # Hours worked threshold (e.g., 12 for BC)
    rate: Decimal  # Premium rate for hours above this threshold (e.g., 2.0 for 2x)


@dataclass
class HolidayPayConfig:
    """Holiday pay configuration for a province."""

    province_code: str
    # Formula types:
    # - "4_week_average": Ontario/Federal/QC/NT style (wages + vacation) / 20
    # - "30_day_average": BC/NS/PE/NB/YT style, average daily pay
    # - "4_week_average_daily": Alberta style, wages / days worked
    # - "current_period_daily": Current period gross / work days
    # - "5_percent_28_days": Saskatchewan/Manitoba style, 5% of past 28 days wages
    # - "3_week_average_nl": Newfoundland style, hourly_rate × (hours in 3 weeks / 15)
    # - "irregular_hours": Yukon irregular-hours employees, percentage × wages
    # - "commission": Quebec/Federal commission employees, wages / divisor
    formula_type: str
    formula_params: HolidayPayFormulaParams
    eligibility: HolidayPayEligibility
    premium_rate: Decimal  # Default premium rate (e.g., 1.5 for 1.5x)
    # Optional tiered premium rates for extended hours (e.g., BC requires 2x after 12 hours)
    premium_rate_tiers: list[PremiumRateTier] | None = None
    name: str | None = None
    notes: str | None = None
