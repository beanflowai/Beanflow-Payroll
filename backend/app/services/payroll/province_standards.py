"""
Province Employment Standards Service

Aggregates employment standards data from various sources:
- Vacation pay (from config files)
- Sick leave (from config files)
- Overtime rules (hardcoded - provincial legislation rarely changes)
- Statutory holidays count (hardcoded - based on provincial legislation)

Reference: docs/08_holidays_vacation.md
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import TypedDict

from app.services.payroll.sick_leave_config_loader import (
    get_config as get_sick_leave_config,
)
from app.services.payroll.vacation_pay_config_loader import (
    get_config as get_vacation_config,
)

# Valid province codes (12 provinces/territories + Federal)
VALID_PROVINCE_CODES: frozenset[str] = frozenset({
    "Federal", "AB", "BC", "MB", "NB", "NL", "NS", "NT", "NU", "ON", "PE", "QC", "SK", "YT"
})


class InvalidProvinceCodeError(ValueError):
    """Raised when an invalid province code is provided."""

    def __init__(self, province_code: str) -> None:
        self.province_code = province_code
        valid_codes = ", ".join(sorted(VALID_PROVINCE_CODES))
        super().__init__(
            f"Invalid province code: '{province_code}'. Valid codes are: {valid_codes}"
        )


class OvertimeRuleData(TypedDict):
    """Typed dict for overtime rule configuration."""

    daily_threshold: int | None
    weekly_threshold: int
    overtime_rate: float
    double_time_daily: int | None
    notes: str


# =============================================================================
# OVERTIME RULES (Provincial Employment Standards)
# =============================================================================

# Overtime thresholds by province
# daily_threshold: Hours per day before overtime kicks in (None = no daily limit)
# weekly_threshold: Hours per week before overtime kicks in
# overtime_rate: Multiplier for overtime hours (typically 1.5x)
# double_time_daily: Hours per day before double-time kicks in (None = no double-time)
# notes: Additional context

OVERTIME_RULES: dict[str, OvertimeRuleData] = {
    "Federal": {
        "daily_threshold": None,
        "weekly_threshold": 40,
        "overtime_rate": 1.5,
        "double_time_daily": None,
        "notes": "No daily overtime. Weekly overtime after 40 hours.",
    },
    "AB": {
        "daily_threshold": 8,
        "weekly_threshold": 44,
        "overtime_rate": 1.5,
        "double_time_daily": None,
        "notes": "OT after 8 hrs/day OR 44 hrs/week, whichever provides greater benefit.",
    },
    "BC": {
        "daily_threshold": 8,
        "weekly_threshold": 40,
        "overtime_rate": 1.5,
        "double_time_daily": 12,
        "notes": "OT after 8 hrs/day, double-time after 12 hrs/day. Weekly OT after 40 hrs.",
    },
    "MB": {
        "daily_threshold": None,
        "weekly_threshold": 40,
        "overtime_rate": 1.5,
        "double_time_daily": None,
        "notes": "No daily overtime. Weekly overtime after 40 hours.",
    },
    "NB": {
        "daily_threshold": None,
        "weekly_threshold": 44,
        "overtime_rate": 1.5,
        "double_time_daily": None,
        "notes": "No daily overtime. Weekly overtime after 44 hours.",
    },
    "NL": {
        "daily_threshold": None,
        "weekly_threshold": 40,
        "overtime_rate": 1.5,
        "double_time_daily": None,
        "notes": "No daily overtime. Weekly overtime after 40 hours.",
    },
    "NS": {
        "daily_threshold": None,
        "weekly_threshold": 48,
        "overtime_rate": 1.5,
        "double_time_daily": None,
        "notes": "No daily overtime. Weekly overtime after 48 hours.",
    },
    "NT": {
        "daily_threshold": 8,
        "weekly_threshold": 40,
        "overtime_rate": 1.5,
        "double_time_daily": None,
        "notes": "OT after 8 hrs/day OR 40 hrs/week.",
    },
    "NU": {
        "daily_threshold": 8,
        "weekly_threshold": 40,
        "overtime_rate": 1.5,
        "double_time_daily": None,
        "notes": "OT after 8 hrs/day OR 40 hrs/week.",
    },
    "ON": {
        "daily_threshold": None,
        "weekly_threshold": 44,
        "overtime_rate": 1.5,
        "double_time_daily": None,
        "notes": "No daily overtime. Weekly overtime after 44 hours.",
    },
    "PE": {
        "daily_threshold": None,
        "weekly_threshold": 48,
        "overtime_rate": 1.5,
        "double_time_daily": None,
        "notes": "No daily overtime. Weekly overtime after 48 hours.",
    },
    "QC": {
        "daily_threshold": None,
        "weekly_threshold": 40,
        "overtime_rate": 1.5,
        "double_time_daily": None,
        "notes": "No daily overtime. Weekly overtime after 40 hours.",
    },
    "SK": {
        "daily_threshold": None,
        "weekly_threshold": 40,
        "overtime_rate": 1.5,
        "double_time_daily": None,
        "notes": "No daily overtime. Weekly overtime after 40 hours.",
    },
    "YT": {
        "daily_threshold": 8,
        "weekly_threshold": 40,
        "overtime_rate": 1.5,
        "double_time_daily": None,
        "notes": "OT after 8 hrs/day OR 40 hrs/week.",
    },
}

# =============================================================================
# STATUTORY HOLIDAYS COUNT (Per province)
# =============================================================================

# Number of statutory/general holidays per province (2025)
# This is configuration data that changes very rarely
STATUTORY_HOLIDAYS_COUNT: dict[str, int] = {
    "Federal": 9,  # New Year, Good Friday, Victoria Day, Canada Day, Labour Day, Thanksgiving, Remembrance Day, Christmas, Boxing Day
    "AB": 9,  # New Year, Family Day, Good Friday, Victoria Day, Canada Day, Labour Day, Thanksgiving, Remembrance Day, Christmas
    "BC": 11,  # New Year, Family Day, Good Friday, Victoria Day, Canada Day, BC Day, Labour Day, Thanksgiving, Remembrance Day, Christmas, Boxing Day (Truth & Reconciliation optional)
    "MB": 8,  # New Year, Louis Riel Day, Good Friday, Victoria Day, Canada Day, Labour Day, Thanksgiving, Christmas
    "NB": 8,  # New Year, Family Day, Good Friday, Victoria Day, Canada Day, NB Day, Labour Day, Christmas
    "NL": 6,  # New Year, Good Friday, Victoria Day (observed), Memorial Day, Labour Day, Christmas
    "NS": 6,  # New Year, Heritage Day, Good Friday, Canada Day, Labour Day, Christmas
    "NT": 10,  # New Year, Good Friday, Victoria Day, National Indigenous Peoples Day, Canada Day, Civic Holiday, Labour Day, Thanksgiving, Remembrance Day, Christmas
    "NU": 9,  # New Year, Good Friday, Victoria Day, Canada Day, Nunavut Day, Civic Holiday, Labour Day, Thanksgiving, Christmas
    "ON": 9,  # New Year, Family Day, Good Friday, Victoria Day, Canada Day, Civic Holiday, Labour Day, Thanksgiving, Christmas
    "PE": 8,  # New Year, Islander Day, Good Friday, Victoria Day, Canada Day, Civic Holiday, Labour Day, Christmas
    "QC": 8,  # New Year, Good Friday/Easter Monday, Fête nationale, Canada Day, Labour Day, Thanksgiving, Christmas (Victoria Day not statutory)
    "SK": 10,  # New Year, Family Day, Good Friday, Victoria Day, Canada Day, Saskatchewan Day, Labour Day, Thanksgiving, Remembrance Day, Christmas
    "YT": 10,  # New Year, Heritage Day, Good Friday, Victoria Day, Canada Day, Discovery Day, Labour Day, Thanksgiving, Remembrance Day, Christmas
}


# =============================================================================
# PROVINCE STANDARDS AGGREGATION
# =============================================================================


@dataclass
class OvertimeRules:
    """Overtime rules for a province."""

    daily_threshold: int | None
    weekly_threshold: int
    overtime_rate: float
    double_time_daily: int | None
    notes: str


@dataclass
class VacationStandards:
    """Vacation standards summary."""

    minimum_weeks: int
    minimum_rate: float
    rate_display: str
    upgrade_years: int | None
    upgrade_weeks: int | None
    notes: str | None


@dataclass
class SickLeaveStandards:
    """Sick leave standards summary."""

    paid_days: int
    unpaid_days: int
    waiting_period_days: int
    notes: str | None


@dataclass
class ProvinceStandards:
    """Aggregated employment standards for a province."""

    province_code: str
    province_name: str
    vacation: VacationStandards
    sick_leave: SickLeaveStandards
    overtime: OvertimeRules
    statutory_holidays_count: int


def get_province_standards(
    province_code: str, year: int = 2025, pay_date: date | None = None
) -> ProvinceStandards:
    """
    Get aggregated employment standards for a province.

    Args:
        province_code: Province code (e.g., 'ON', 'BC', 'Federal')
        year: Configuration year
        pay_date: Date for edition selection

    Returns:
        ProvinceStandards with vacation, sick leave, overtime, and holiday info

    Raises:
        InvalidProvinceCodeError: If province_code is not a valid Canadian province/territory
    """
    # Validate province code
    if province_code not in VALID_PROVINCE_CODES:
        raise InvalidProvinceCodeError(province_code)

    # Get vacation config
    vacation_config = get_vacation_config(province_code, year)
    first_tier = vacation_config.tiers[0] if vacation_config.tiers else None
    upgrade_tier = vacation_config.tiers[1] if len(vacation_config.tiers) > 1 else None

    vacation = VacationStandards(
        minimum_weeks=first_tier.vacation_weeks if first_tier else 2,
        minimum_rate=float(first_tier.vacation_rate) if first_tier else 0.04,
        rate_display=f"{float(first_tier.vacation_rate) * 100:.2f}%"
        if first_tier
        else "4.00%",
        upgrade_years=upgrade_tier.min_years_of_service if upgrade_tier else None,
        upgrade_weeks=upgrade_tier.vacation_weeks if upgrade_tier else None,
        notes=vacation_config.notes,
    )

    # Get sick leave config
    sick_config = get_sick_leave_config(province_code, year, pay_date)
    if sick_config:
        sick_leave = SickLeaveStandards(
            paid_days=sick_config.paid_days_per_year,
            unpaid_days=sick_config.unpaid_days_per_year,
            waiting_period_days=sick_config.waiting_period_days,
            notes=None,
        )
    else:
        sick_leave = SickLeaveStandards(
            paid_days=0,
            unpaid_days=0,
            waiting_period_days=0,
            notes="No statutory sick leave",
        )

    # Get overtime rules
    ot_data = OVERTIME_RULES.get(province_code, OVERTIME_RULES["Federal"])
    overtime = OvertimeRules(
        daily_threshold=ot_data["daily_threshold"],
        weekly_threshold=ot_data["weekly_threshold"],
        overtime_rate=ot_data["overtime_rate"],
        double_time_daily=ot_data.get("double_time_daily"),
        notes=ot_data["notes"],
    )

    # Get holiday count
    holiday_count = STATUTORY_HOLIDAYS_COUNT.get(
        province_code, STATUTORY_HOLIDAYS_COUNT["Federal"]
    )

    # Get province name from vacation config
    province_name = vacation_config.name

    return ProvinceStandards(
        province_code=province_code,
        province_name=province_name,
        vacation=vacation,
        sick_leave=sick_leave,
        overtime=overtime,
        statutory_holidays_count=holiday_count,
    )
