"""
Sick Leave Service

Implements sick leave calculation and balance tracking for Canadian payroll.
Supports both provincial (BC: 5 paid days) and federal (10 paid days) jurisdictions.

Key Features:
- Province-specific sick leave rules
- Part-time employee support (NO pro-rating - full entitlement)
- Average day's pay calculation (BC: 30-day, Federal: 20-day)
- Balance tracking and year-end carryover (Federal only)

References:
- BC: https://www2.gov.bc.ca/gov/content/employment-business/employment-standards-advice/paid-sick-leave
- Federal: https://www.canada.ca/en/employment-social-development/programs/laws-regulations/labour/interpretations-policies/medical-leave-pay.html
- docs/08_holidays_vacation.md Task 8.7
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal, NamedTuple

logger = logging.getLogger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class SickLeaveConfig:
    """Province-level sick leave configuration."""

    province_code: str
    paid_days_per_year: int
    unpaid_days_per_year: int
    waiting_period_days: int
    allows_carryover: bool
    max_carryover_days: int
    accrual_method: Literal["immediate", "monthly"]
    initial_days_after_qualifying: int = 0  # For monthly accrual (Federal: 3)
    days_per_month_after_initial: int = 0  # For monthly accrual (Federal: 1)


@dataclass
class SickLeaveBalance:
    """Employee's sick leave balance for a year."""

    employee_id: str
    year: int
    paid_days_entitled: Decimal
    unpaid_days_entitled: Decimal
    paid_days_used: Decimal
    unpaid_days_used: Decimal
    carried_over_days: Decimal
    is_eligible: bool
    eligibility_date: date | None = None
    accrued_days_ytd: Decimal = Decimal("0")

    @property
    def paid_days_remaining(self) -> Decimal:
        """Paid sick days remaining for the year."""
        return self.paid_days_entitled + self.carried_over_days - self.paid_days_used

    @property
    def unpaid_days_remaining(self) -> Decimal:
        """Unpaid sick days remaining for the year."""
        return self.unpaid_days_entitled - self.unpaid_days_used


class SickPayResult(NamedTuple):
    """Result of sick pay calculation."""

    eligible: bool
    days_used: Decimal
    paid_days: Decimal
    unpaid_days: Decimal
    amount: Decimal  # Total sick pay amount
    average_day_pay: Decimal
    balance_after: Decimal
    reason: str | None = None


class AverageDayPayResult(NamedTuple):
    """Result of average day's pay calculation."""

    amount: Decimal
    calculation_method: str
    wages_included: Decimal
    days_counted: int




# =============================================================================
# SICK LEAVE SERVICE
# =============================================================================


class SickLeaveService:
    """
    Service for sick leave calculations and balance management.

    Handles:
    - Eligibility checking based on waiting period
    - Average day's pay calculation (province-specific)
    - Balance tracking and updates
    - Year-end carryover processing
    """

    def __init__(
        self,
        configs: dict[str, SickLeaveConfig] | None = None,
        year: int = 2025,
        pay_date: date | None = None,
    ):
        """
        Initialize sick leave service.

        Args:
            configs: Province-specific sick leave configurations.
                    If None, loads from JSON config files.
            year: Configuration year (default: 2025)
            pay_date: Date to determine which edition to use
        """
        if configs is not None:
            self.configs = configs
        else:
            from app.services.payroll.sick_leave_config_loader import get_all_configs

            self.configs = get_all_configs(year, pay_date)

    def _round(self, value: Decimal) -> Decimal:
        """Round to 2 decimal places."""
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def get_config(self, province_code: str) -> SickLeaveConfig | None:
        """Get sick leave configuration for a province."""
        return self.configs.get(province_code)

    def check_eligibility(
        self, hire_date: date, province_code: str, reference_date: date
    ) -> tuple[bool, date | None]:
        """
        Check if employee is eligible for sick leave.

        Args:
            hire_date: Employee's hire date
            province_code: Province of employment
            reference_date: Date to check eligibility for

        Returns:
            Tuple of (is_eligible, eligibility_date)
        """
        config = self.get_config(province_code)
        if not config:
            return False, None

        # No waiting period = immediately eligible
        if config.waiting_period_days == 0:
            return True, hire_date

        # Calculate eligibility date
        eligibility_date = hire_date + timedelta(days=config.waiting_period_days)
        is_eligible = reference_date >= eligibility_date

        return is_eligible, eligibility_date

    def calculate_bc_average_day_pay(
        self, wages_past_30_days: Decimal, days_worked_past_30_days: int
    ) -> AverageDayPayResult:
        """
        Calculate average day's pay for BC sick leave.

        BC Employment Standards Act formula:
        - Total wages in past 30 calendar days
        - Divided by number of days actually worked
        - EXCLUDES overtime pay
        - INCLUDES vacation pay paid/payable in that period

        Args:
            wages_past_30_days: Total wages (excluding overtime) in past 30 calendar days
            days_worked_past_30_days: Number of days actually worked in past 30 days

        Returns:
            AverageDayPayResult with calculated amount
        """
        if days_worked_past_30_days <= 0:
            return AverageDayPayResult(
                amount=Decimal("0"),
                calculation_method="bc_30_day_avg",
                wages_included=wages_past_30_days,
                days_counted=0,
            )

        average = self._round(wages_past_30_days / Decimal(str(days_worked_past_30_days)))

        return AverageDayPayResult(
            amount=average,
            calculation_method="bc_30_day_avg",
            wages_included=wages_past_30_days,
            days_counted=days_worked_past_30_days,
        )

    def calculate_federal_average_day_pay(
        self, earnings_past_20_days: Decimal, days_count: int = 20
    ) -> AverageDayPayResult:
        """
        Calculate average day's pay for Federal sick leave.

        Canada Labour Standards Regulations Section 17:
        - Average of daily earnings (excluding overtime)
        - For the 20 days worked immediately before the leave

        Args:
            earnings_past_20_days: Total earnings (excluding overtime) for last 20 days worked
            days_count: Number of days included (default 20)

        Returns:
            AverageDayPayResult with calculated amount
        """
        if days_count <= 0:
            return AverageDayPayResult(
                amount=Decimal("0"),
                calculation_method="federal_20_day_avg",
                wages_included=earnings_past_20_days,
                days_counted=0,
            )

        average = self._round(earnings_past_20_days / Decimal(str(days_count)))

        return AverageDayPayResult(
            amount=average,
            calculation_method="federal_20_day_avg",
            wages_included=earnings_past_20_days,
            days_counted=days_count,
        )

    def calculate_federal_accrued_days(
        self,
        hire_date: date,
        reference_date: date,
        sick_days_used_ytd: Decimal = Decimal("0"),
        carried_over_days: Decimal = Decimal("0"),
    ) -> Decimal:
        """
        Calculate accrued sick days for Federal jurisdiction.

        Federal accrual method:
        - 3 days after 30-day qualifying period
        - +1 day at start of each subsequent month
        - Maximum 10 days per year
        - Carryover max 10 days total

        Args:
            hire_date: Employee's hire date
            reference_date: Date to calculate accrual for
            sick_days_used_ytd: Sick days already used this year
            carried_over_days: Days carried over from previous year

        Returns:
            Number of sick days currently available
        """
        # Check if past qualifying period (30 days)
        qualifying_date = hire_date + timedelta(days=30)
        if reference_date < qualifying_date:
            return Decimal("0")

        # Initial 3 days after qualifying period
        accrued = Decimal("3")

        # Calculate months elapsed since qualifying
        days_since_qualifying = (reference_date - qualifying_date).days
        months_since_qualifying = days_since_qualifying // 30

        # Add 1 day per month after qualifying (up to max 10 total per year)
        accrued = min(accrued + Decimal(str(months_since_qualifying)), Decimal("10"))

        # Add carryover (but max 10 total at any time)
        total_available = min(accrued + carried_over_days, Decimal("10"))

        # Subtract used days
        remaining = max(Decimal("0"), total_available - sick_days_used_ytd)

        return remaining

    def calculate_sick_pay(
        self,
        province_code: str,
        sick_hours_taken: Decimal,
        average_day_pay: Decimal,
        balance: SickLeaveBalance,
        hours_per_day: Decimal = Decimal("8"),
    ) -> SickPayResult:
        """
        Calculate sick pay for an employee.

        Args:
            province_code: Province of employment
            sick_hours_taken: Hours of sick leave taken
            average_day_pay: Pre-calculated average day's pay
            balance: Employee's current sick leave balance
            hours_per_day: Hours in a standard work day (default 8)

        Returns:
            SickPayResult with payment details
        """
        config = self.get_config(province_code)

        if not config:
            return SickPayResult(
                eligible=False,
                days_used=Decimal("0"),
                paid_days=Decimal("0"),
                unpaid_days=Decimal("0"),
                amount=Decimal("0"),
                average_day_pay=Decimal("0"),
                balance_after=Decimal("0"),
                reason=f"No sick leave configuration for province: {province_code}",
            )

        if not balance.is_eligible:
            return SickPayResult(
                eligible=False,
                days_used=Decimal("0"),
                paid_days=Decimal("0"),
                unpaid_days=Decimal("0"),
                amount=Decimal("0"),
                average_day_pay=Decimal("0"),
                balance_after=Decimal("0"),
                reason="Employee not yet eligible (waiting period not met)",
            )

        # Convert hours to days
        sick_days = self._round(sick_hours_taken / hours_per_day)

        # Determine paid vs unpaid days
        paid_days_available = balance.paid_days_remaining

        if sick_days <= paid_days_available:
            paid_days = sick_days
            unpaid_days = Decimal("0")
        else:
            paid_days = paid_days_available
            unpaid_days = sick_days - paid_days_available

        # Calculate payment
        sick_pay = self._round(average_day_pay * paid_days)

        # Calculate balance after
        balance_after = paid_days_available - paid_days

        return SickPayResult(
            eligible=True,
            days_used=sick_days,
            paid_days=paid_days,
            unpaid_days=unpaid_days,
            amount=sick_pay,
            average_day_pay=average_day_pay,
            balance_after=balance_after,
        )

    def calculate_year_end_carryover(
        self, province_code: str, paid_days_remaining: Decimal
    ) -> Decimal:
        """
        Calculate sick leave carryover for year-end.

        Args:
            province_code: Province of employment
            paid_days_remaining: Paid days remaining at year end

        Returns:
            Days to carry over to next year
        """
        config = self.get_config(province_code)

        if not config or not config.allows_carryover:
            return Decimal("0")

        # Carryover up to max allowed
        return min(paid_days_remaining, Decimal(str(config.max_carryover_days)))

    def create_new_year_balance(
        self,
        employee_id: str,
        year: int,
        province_code: str,
        hire_date: date,
        carried_over_days: Decimal = Decimal("0"),
    ) -> SickLeaveBalance:
        """
        Create a new year's sick leave balance for an employee.

        Args:
            employee_id: Employee ID
            year: Year to create balance for
            province_code: Province of employment
            hire_date: Employee's hire date
            carried_over_days: Days carried over from previous year

        Returns:
            New SickLeaveBalance for the year
        """
        config = self.get_config(province_code)

        if not config:
            # Province with no sick leave
            return SickLeaveBalance(
                employee_id=employee_id,
                year=year,
                paid_days_entitled=Decimal("0"),
                unpaid_days_entitled=Decimal("0"),
                paid_days_used=Decimal("0"),
                unpaid_days_used=Decimal("0"),
                carried_over_days=Decimal("0"),
                is_eligible=False,
            )

        # Check eligibility
        reference_date = date(year, 1, 1)
        is_eligible, eligibility_date = self.check_eligibility(
            hire_date, province_code, reference_date
        )

        # Determine entitlement
        paid_entitled = Decimal(str(config.paid_days_per_year))
        unpaid_entitled = Decimal(str(config.unpaid_days_per_year))

        # For Federal with carryover, limit total to max
        if config.allows_carryover:
            # Carryover is already limited in calculate_year_end_carryover
            pass

        return SickLeaveBalance(
            employee_id=employee_id,
            year=year,
            paid_days_entitled=paid_entitled,
            unpaid_days_entitled=unpaid_entitled,
            paid_days_used=Decimal("0"),
            unpaid_days_used=Decimal("0"),
            carried_over_days=carried_over_days,
            is_eligible=is_eligible,
            eligibility_date=eligibility_date,
        )
