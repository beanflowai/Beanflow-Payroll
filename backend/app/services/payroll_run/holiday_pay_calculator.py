"""
Holiday Pay Calculator

Calculates Regular Holiday Pay and Premium Holiday Pay by province.
Uses configuration-driven formulas loaded from JSON files.

Regular Holiday Pay:
- Only for Hourly employees (Salaried employees already have it included)
- Calculated based on provincial formulas from config

Premium Holiday Pay:
- For all employees who work on a statutory holiday
- Rate from config (default: 1.5x regular hourly rate)
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, NamedTuple

from app.models.holiday_pay_config import HolidayPayConfig
from app.services.payroll.holiday_pay_config_loader import (
    HolidayPayConfigLoader,
    get_config,
)
from app.services.payroll_run.constants import COMPLETED_RUN_STATUSES
from app.services.payroll_run.gross_calculator import GrossCalculator

logger = logging.getLogger(__name__)

# Work days per pay period (for Alberta formula)
WORK_DAYS_PER_PERIOD = {
    "weekly": Decimal("5"),
    "bi_weekly": Decimal("10"),
    "semi_monthly": Decimal("10.83"),  # 260 / 24
    "monthly": Decimal("21.67"),  # 260 / 12
}


class HolidayPayResult(NamedTuple):
    """Result of holiday pay calculation."""

    regular_holiday_pay: Decimal  # Hourly employee's daily pay for holidays
    premium_holiday_pay: Decimal  # 1.5x pay for hours worked on holidays
    total_holiday_pay: Decimal
    calculation_details: dict[str, Any]


class HolidayPayCalculator:
    """Calculates holiday pay by provincial rules.

    Uses configuration from backend/config/holiday_pay/ to determine:
    - Formula type and parameters
    - Eligibility rules
    - Premium rates
    """

    def __init__(
        self,
        supabase: Any,
        user_id: str,
        company_id: str,
        config_loader: HolidayPayConfigLoader | None = None,
    ):
        """Initialize holiday pay calculator.

        Args:
            supabase: Supabase client instance
            user_id: Current user ID
            company_id: Current company ID
            config_loader: Optional config loader (for testing/DI)
        """
        self.supabase = supabase
        self.user_id = user_id
        self.company_id = company_id
        self.config_loader = config_loader

    def _get_config(self, province: str, pay_date: date | None = None) -> HolidayPayConfig:
        """Get holiday pay config for a province.

        Args:
            province: Province code
            pay_date: Date for version selection

        Returns:
            HolidayPayConfig for the province
        """
        if self.config_loader:
            return self.config_loader.get_config(province)
        return get_config(province, pay_date=pay_date)

    def calculate_holiday_pay(
        self,
        employee: dict[str, Any],
        province: str,
        pay_frequency: str,
        period_start: date,
        period_end: date,
        holidays_in_period: list[dict[str, Any]],
        holiday_work_entries: list[dict[str, Any]],
        current_period_gross: Decimal,
        current_run_id: str,
        holiday_pay_exempt: bool = False,
    ) -> HolidayPayResult:
        """Calculate total holiday pay for an employee.

        This method calculates:
        1. Regular Holiday Pay: For Hourly employees only, one day's pay per holiday
        2. Premium Holiday Pay: For all employees who work on holidays (configurable rate)

        Args:
            employee: Employee data dict
            province: Province code (ON, BC, AB, etc.)
            pay_frequency: Pay frequency string (weekly, bi_weekly, etc.)
            period_start: Pay period start date
            period_end: Pay period end date
            holidays_in_period: List of statutory holidays in the period
            holiday_work_entries: List of holiday work entries from input_data
            current_period_gross: Current period gross pay (regular + overtime)
            current_run_id: Current payroll run ID (to exclude from historical queries)
            holiday_pay_exempt: If True, skip Regular Holiday Pay (HR manual override)

        Returns:
            HolidayPayResult with regular, premium, and total holiday pay
        """
        regular_holiday_pay = Decimal("0")
        premium_holiday_pay = Decimal("0")

        # Get config for this province (use period_end as pay_date for version selection)
        config = self._get_config(province, period_end)

        details: dict[str, Any] = {
            "holidays_count": len(holidays_in_period),
            "holidays": [],
            "work_entries": [],
            "is_hourly": bool(employee.get("hourly_rate")),
            "province": province,
            "holiday_pay_exempt": holiday_pay_exempt,
            "config": {
                "formula_type": config.formula_type,
                "premium_rate": str(config.premium_rate),
                "min_employment_days": config.eligibility.min_employment_days,
                "require_last_first_rule": config.eligibility.require_last_first_rule,
            },
        }

        # Skip if no holidays in period
        if not holidays_in_period:
            return HolidayPayResult(
                regular_holiday_pay=Decimal("0"),
                premium_holiday_pay=Decimal("0"),
                total_holiday_pay=Decimal("0"),
                calculation_details=details,
            )

        is_hourly = bool(employee.get("hourly_rate"))

        # Fetch timesheet entries for eligibility checks if config requires them
        # This is needed for require_last_first_rule and min_days_worked_in_period
        timesheet_entries: list[dict[str, Any]] | None = None
        if (
            config.eligibility.require_last_first_rule
            or config.eligibility.min_days_worked_in_period is not None
        ):
            # Calculate date range: 30 days before first holiday to 7 days after last holiday
            holiday_dates = []
            for h in holidays_in_period:
                try:
                    holiday_dates.append(date.fromisoformat(h.get("holiday_date", "")))
                except (ValueError, TypeError):
                    pass
            if holiday_dates:
                earliest = min(holiday_dates) - timedelta(days=30)
                latest = max(holiday_dates) + timedelta(days=7)
                timesheet_entries = self._get_timesheet_entries_for_eligibility(
                    employee["id"], earliest, latest
                )

        # Build lookup for hours worked per holiday
        hours_worked_by_date: dict[str, Decimal] = {}
        for entry in holiday_work_entries or []:
            holiday_date_str = entry.get("holidayDate", "")
            hours = Decimal(str(entry.get("hoursWorked", 0)))
            if holiday_date_str and hours > 0:
                hours_worked_by_date[holiday_date_str] = hours

        # Process each holiday
        for holiday in holidays_in_period:
            logger.debug(
                "HOLIDAY CALC DEBUG: Processing holiday %s for %s %s (province=%s)",
                holiday.get("name"),
                employee.get("first_name"),
                employee.get("last_name"),
                province,
            )
            holiday_date_str = holiday.get("holiday_date", "")
            holiday_name = holiday.get("name", "Unknown")

            try:
                holiday_date = date.fromisoformat(holiday_date_str)
            except (ValueError, TypeError):
                logger.warning("Invalid holiday date: %s", holiday_date_str)
                continue

            holiday_detail: dict[str, Any] = {
                "date": holiday_date_str,
                "name": holiday_name,
                "eligible": False,
                "regular_pay": "0",
                "premium_pay": "0",
                "hours_worked": "0",
            }

            # Check eligibility using config-driven rules
            # If HR marked as exempt, skip Regular Holiday Pay entirely
            if holiday_pay_exempt:
                is_eligible = False
                holiday_detail["eligible"] = False
                holiday_detail["exempt_by_hr"] = True
                logger.debug(
                    "Employee %s %s exempt from Regular holiday pay on %s (HR override)",
                    employee.get("first_name"),
                    employee.get("last_name"),
                    holiday_name,
                )
            else:
                is_eligible = self._is_eligible_for_holiday_pay(
                    employee, holiday_date, config, timesheet_entries
                )
                holiday_detail["eligible"] = is_eligible

            if not is_eligible and not holiday_pay_exempt:
                reason = self._get_ineligibility_reason(
                    employee, holiday_date, config, timesheet_entries
                )
                logger.debug(
                    "Employee %s %s not eligible for Regular holiday pay on %s (%s)",
                    employee.get("first_name"),
                    employee.get("last_name"),
                    holiday_name,
                    reason,
                )
                holiday_detail["ineligibility_reason"] = reason
                # Even ineligible employees can get Premium Pay if they work
            elif is_eligible and is_hourly:
                # Calculate Regular Holiday Pay (Hourly employees only, must be eligible)
                daily_pay = self._calculate_regular_holiday_pay(
                    employee=employee,
                    config=config,
                    pay_frequency=pay_frequency,
                    period_start=period_start,
                    period_end=period_end,
                    holiday_date=holiday_date,
                    current_period_gross=current_period_gross,
                    current_run_id=current_run_id,
                )
                regular_holiday_pay += daily_pay
                holiday_detail["regular_pay"] = str(daily_pay)
                holiday_detail["formula"] = config.formula_type

            # Calculate Premium Pay (if employee worked on this holiday)
            hours_worked = hours_worked_by_date.get(holiday_date_str, Decimal("0"))
            if hours_worked > 0:
                premium_pay = self._calculate_premium_pay(employee, hours_worked, config)
                premium_holiday_pay += premium_pay
                holiday_detail["hours_worked"] = str(hours_worked)
                holiday_detail["premium_pay"] = str(premium_pay)

                details["work_entries"].append({
                    "date": holiday_date_str,
                    "hours": str(hours_worked),
                    "premium": str(premium_pay),
                })

            details["holidays"].append(holiday_detail)

        total_holiday_pay = regular_holiday_pay + premium_holiday_pay

        logger.debug(
            "Holiday pay for %s %s: regular=$%.2f, premium=$%.2f, total=$%.2f",
            employee.get("first_name"),
            employee.get("last_name"),
            float(regular_holiday_pay),
            float(premium_holiday_pay),
            float(total_holiday_pay),
        )

        return HolidayPayResult(
            regular_holiday_pay=regular_holiday_pay,
            premium_holiday_pay=premium_holiday_pay,
            total_holiday_pay=total_holiday_pay,
            calculation_details=details,
        )

    def _is_eligible_for_holiday_pay(
        self,
        employee: dict[str, Any],
        holiday_date: date,
        config: HolidayPayConfig,
        timesheet_entries: list[dict[str, Any]] | None = None,
    ) -> bool:
        """Check if employee is eligible for holiday pay based on config.

        Eligibility rules are loaded from configuration:
        - min_employment_days: Minimum days of employment required
        - require_last_first_rule: Must work last shift before and first shift after holiday
        - min_days_worked_in_period: Minimum days worked in 30-day period (PE)

        Args:
            employee: Employee data dict (must contain hire_date)
            holiday_date: The date of the statutory holiday
            config: HolidayPayConfig for the province
            timesheet_entries: Optional timesheet entries for eligibility checks

        Returns:
            True if employee is eligible for holiday pay
        """
        hire_date_str = employee.get("hire_date")
        if not hire_date_str:
            # hire_date is required field; missing indicates data issue
            logger.warning(
                "Employee %s missing hire_date, marking ineligible for holiday pay",
                employee.get("id"),
            )
            return False

        try:
            hire_date = date.fromisoformat(hire_date_str)
        except (ValueError, TypeError):
            logger.warning(
                "Employee %s has invalid hire_date: %s, marking ineligible",
                employee.get("id"),
                hire_date_str,
            )
            return False

        # Check 1: minimum employment days
        days_employed = (holiday_date - hire_date).days
        min_days = config.eligibility.min_employment_days

        if days_employed < min_days:
            return False

        # Check 2: require_last_first_rule (work before and after holiday)
        if config.eligibility.require_last_first_rule and timesheet_entries is not None:
            has_work_before = self._has_work_in_range(
                timesheet_entries,
                holiday_date - timedelta(days=7),
                holiday_date - timedelta(days=1),
            )
            has_work_after = self._has_work_in_range(
                timesheet_entries,
                holiday_date + timedelta(days=1),
                holiday_date + timedelta(days=7),
            )
            if not (has_work_before and has_work_after):
                logger.debug(
                    "Employee %s failed last/first rule: before=%s, after=%s",
                    employee.get("id"),
                    has_work_before,
                    has_work_after,
                )
                return False

        # Check 3: min_days_worked_in_period (PE requires 15 days in 30-day period)
        min_days_worked = config.eligibility.min_days_worked_in_period
        if min_days_worked is not None and timesheet_entries is not None:
            days_worked = self._count_days_worked_in_period(
                timesheet_entries,
                holiday_date - timedelta(days=30),
                holiday_date,
            )
            if days_worked < min_days_worked:
                logger.debug(
                    "Employee %s failed min_days_worked check: %d < %d",
                    employee.get("id"),
                    days_worked,
                    min_days_worked,
                )
                return False

        return True

    def _get_ineligibility_reason(
        self,
        employee: dict[str, Any],
        holiday_date: date,
        config: HolidayPayConfig,
        timesheet_entries: list[dict[str, Any]] | None = None,
    ) -> str:
        """Get the reason for ineligibility.

        Args:
            employee: Employee data
            holiday_date: Holiday date
            config: HolidayPayConfig
            timesheet_entries: Optional timesheet entries for eligibility checks

        Returns:
            Reason string
        """
        hire_date_str = employee.get("hire_date")
        if not hire_date_str:
            return "missing hire date"

        try:
            hire_date = date.fromisoformat(hire_date_str)
        except (ValueError, TypeError):
            return "invalid hire date"

        days_employed = (holiday_date - hire_date).days
        min_days = config.eligibility.min_employment_days

        if days_employed < min_days:
            return f"< {min_days} days employed ({days_employed} days)"

        # Check last/first rule
        if config.eligibility.require_last_first_rule and timesheet_entries is not None:
            has_work_before = self._has_work_in_range(
                timesheet_entries,
                holiday_date - timedelta(days=7),
                holiday_date - timedelta(days=1),
            )
            has_work_after = self._has_work_in_range(
                timesheet_entries,
                holiday_date + timedelta(days=1),
                holiday_date + timedelta(days=7),
            )
            if not (has_work_before and has_work_after):
                return "did not work before/after holiday"

        # Check min_days_worked_in_period
        min_days_worked = config.eligibility.min_days_worked_in_period
        if min_days_worked is not None and timesheet_entries is not None:
            days_worked = self._count_days_worked_in_period(
                timesheet_entries,
                holiday_date - timedelta(days=30),
                holiday_date,
            )
            if days_worked < min_days_worked:
                return f"only {days_worked} days worked in 30-day period (need {min_days_worked})"

        return "unknown"

    def _has_work_in_range(
        self,
        entries: list[dict[str, Any]],
        start_date: date,
        end_date: date,
    ) -> bool:
        """Check if employee worked in date range.

        Args:
            entries: List of timesheet entries
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)

        Returns:
            True if any work entry exists with hours > 0 in range
        """
        for entry in entries:
            work_date_str = entry.get("work_date")
            if not work_date_str:
                continue
            try:
                work_date = date.fromisoformat(work_date_str)
            except (ValueError, TypeError):
                continue
            if start_date <= work_date <= end_date:
                regular = Decimal(str(entry.get("regular_hours", 0) or 0))
                overtime = Decimal(str(entry.get("overtime_hours", 0) or 0))
                if regular + overtime > 0:
                    return True
        return False

    def _count_days_worked_in_period(
        self,
        entries: list[dict[str, Any]],
        start_date: date,
        end_date: date,
    ) -> int:
        """Count unique days with work in date range.

        Args:
            entries: List of timesheet entries
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)

        Returns:
            Number of unique days with hours > 0
        """
        days_with_work: set[date] = set()
        for entry in entries:
            work_date_str = entry.get("work_date")
            if not work_date_str:
                continue
            try:
                work_date = date.fromisoformat(work_date_str)
            except (ValueError, TypeError):
                continue
            if start_date <= work_date <= end_date:
                regular = Decimal(str(entry.get("regular_hours", 0) or 0))
                overtime = Decimal(str(entry.get("overtime_hours", 0) or 0))
                if regular + overtime > 0:
                    days_with_work.add(work_date)
        return len(days_with_work)

    def _get_timesheet_entries_for_eligibility(
        self,
        employee_id: str,
        start_date: date,
        end_date: date,
    ) -> list[dict[str, Any]] | None:
        """Query timesheet_entries for eligibility checks.

        Args:
            employee_id: Employee ID
            start_date: Start of date range
            end_date: End of date range

        Returns:
            List of timesheet entries, or None if query fails.
            None triggers fallback (default eligible), [] means no work found.
        """
        try:
            result = (
                self.supabase.table("timesheet_entries")
                .select("work_date, regular_hours, overtime_hours")
                .eq("employee_id", employee_id)
                .gte("work_date", start_date.isoformat())
                .lte("work_date", end_date.isoformat())
                .execute()
            )
            return result.data if result.data is not None else []
        except Exception as e:
            logger.warning("Failed to query timesheet entries: %s", e)
            # Return None to indicate query failure - triggers fallback (default eligible)
            return None

    def _calculate_regular_holiday_pay(
        self,
        employee: dict[str, Any],
        config: HolidayPayConfig,
        pay_frequency: str,
        period_start: date,
        period_end: date,
        holiday_date: date,
        current_period_gross: Decimal,
        current_run_id: str,
    ) -> Decimal:
        """Calculate one day's pay for Hourly employees using config-driven formula.

        Formula types from config:
        - 4_week_average: (past 4 weeks wages + vacation pay) / divisor
        - 30_day_average: Average daily pay based on 30 days
        - 4_week_average_daily: Wages in 4 weeks / days worked
        - current_period_daily: Current period gross / work days in period

        Args:
            employee: Employee data dict
            config: HolidayPayConfig for the province
            pay_frequency: Pay frequency string
            period_start: Pay period start date
            period_end: Pay period end date
            holiday_date: The holiday date
            current_period_gross: Current period gross pay
            current_run_id: Current run ID to exclude from queries

        Returns:
            One day's pay as Decimal
        """
        formula_type = config.formula_type
        params = config.formula_params

        match formula_type:
            case "4_week_average":
                return self._apply_4_week_average(
                    employee_id=employee["id"],
                    holiday_date=holiday_date,
                    current_run_id=current_run_id,
                    divisor=params.divisor or 20,
                    include_vacation_pay=params.include_vacation_pay,
                    employee_fallback=employee,
                    new_employee_fallback=params.new_employee_fallback,
                )
            case "4_week_average_daily":
                return self._apply_4_week_daily(
                    employee_id=employee["id"],
                    holiday_date=holiday_date,
                    current_run_id=current_run_id,
                    employee_fallback=employee,
                    new_employee_fallback=params.new_employee_fallback,
                )
            case "current_period_daily":
                return self._apply_current_period_daily(
                    current_period_gross=current_period_gross,
                    pay_frequency=pay_frequency,
                )
            case "5_percent_28_days":
                # Saskatchewan formula: 5% of wages in past 28 days
                # New employee handling is config-driven via new_employee_fallback
                return self._apply_5_percent_28_days(
                    employee_id=employee["id"],
                    holiday_date=holiday_date,
                    current_run_id=current_run_id,
                    percentage=params.percentage or Decimal("0.05"),
                    include_vacation_pay=params.include_vacation_pay,
                    include_previous_holiday_pay=params.include_previous_holiday_pay,
                    current_period_gross=current_period_gross,
                    new_employee_fallback=params.new_employee_fallback,
                )
            case "30_day_average" | _:
                # Default to 30-day average (BC formula)
                return self._apply_30_day_average(
                    employee=employee,
                    default_daily_hours=params.default_daily_hours,
                )

    def _apply_30_day_average(
        self,
        employee: dict[str, Any],
        default_daily_hours: Decimal,
    ) -> Decimal:
        """Apply BC-style 30-day average formula.

        Formula: default_daily_hours × hourly_rate

        Args:
            employee: Employee data dict with hourly_rate
            default_daily_hours: Default daily hours (usually 8)

        Returns:
            One day's pay as Decimal
        """
        hourly_rate = GrossCalculator.calculate_hourly_rate(employee)
        daily_pay = default_daily_hours * hourly_rate

        logger.debug(
            "30-day avg formula: %.2fh × $%.2f = $%.2f",
            float(default_daily_hours),
            float(hourly_rate),
            float(daily_pay),
        )

        return daily_pay

    def _apply_current_period_daily(
        self,
        current_period_gross: Decimal,
        pay_frequency: str,
    ) -> Decimal:
        """Apply current period daily average formula.

        Formula: current_period_gross / work_days_in_period

        Args:
            current_period_gross: Gross pay for current period
            pay_frequency: Pay frequency string

        Returns:
            One day's pay as Decimal
        """
        work_days = WORK_DAYS_PER_PERIOD.get(pay_frequency, Decimal("10"))

        if work_days == 0:
            return Decimal("0")

        daily_pay = current_period_gross / work_days

        logger.debug(
            "Current period formula: $%.2f / %s days = $%.2f",
            float(current_period_gross),
            float(work_days),
            float(daily_pay),
        )

        return daily_pay

    def _apply_4_week_average(
        self,
        employee_id: str,
        holiday_date: date,
        current_run_id: str,
        divisor: int,
        include_vacation_pay: bool,
        employee_fallback: dict[str, Any],
        new_employee_fallback: str | None,
    ) -> Decimal:
        """Apply 4-week average formula (Ontario style).

        Formula: (total wages in past 4 weeks + vacation pay) / divisor

        For new employees with no historical data, behavior is config-driven:
        - "pro_rated": Use 30-day average fallback (hourly_rate × 8)
        - "ineligible": Return $0

        Args:
            employee_id: Employee ID
            holiday_date: The holiday date (for 4-week lookback)
            current_run_id: Current run ID to exclude from queries
            divisor: Divisor for the formula (usually 20)
            include_vacation_pay: Whether to include vacation pay
            employee_fallback: Employee data for fallback calculation
            new_employee_fallback: Config-driven fallback for new employees

        Returns:
            One day's pay as Decimal
        """
        total_wages, vacation_pay = self._get_4_week_earnings(
            employee_id=employee_id,
            before_date=holiday_date,
            current_run_id=current_run_id,
        )

        # Handle new employees with no historical data based on config
        if total_wages == Decimal("0"):
            if new_employee_fallback == "pro_rated":
                logger.info(
                    "4-week avg formula: No historical data for employee %s, "
                    "using 30-day avg fallback (pro_rated)",
                    employee_id,
                )
                return self._apply_30_day_average(employee_fallback, Decimal("8"))
            else:
                # "ineligible" or None: return $0
                logger.info(
                    "4-week avg formula: No historical data for employee %s, "
                    "returning $0 (ineligible fallback)",
                    employee_id,
                )
                return Decimal("0")

        # Apply formula
        if include_vacation_pay:
            daily_pay = (total_wages + vacation_pay) / Decimal(str(divisor))
        else:
            daily_pay = total_wages / Decimal(str(divisor))

        logger.debug(
            "4-week avg formula: ($%.2f + $%.2f) / %d = $%.2f",
            float(total_wages),
            float(vacation_pay) if include_vacation_pay else 0,
            divisor,
            float(daily_pay),
        )

        return daily_pay

    def _apply_4_week_daily(
        self,
        employee_id: str,
        holiday_date: date,
        current_run_id: str,
        employee_fallback: dict[str, Any],
        new_employee_fallback: str | None,
    ) -> Decimal:
        """Apply 4-week daily average formula (Alberta style).

        Formula: wages in 4 weeks / days worked in 4 weeks

        For new employees with no historical data, behavior is config-driven:
        - "pro_rated": Use 30-day average fallback (hourly_rate × 8)
        - "ineligible": Return $0

        Args:
            employee_id: Employee ID
            holiday_date: Holiday date for lookback
            current_run_id: Current run ID to exclude
            employee_fallback: Employee data for fallback
            new_employee_fallback: Config-driven fallback for new employees

        Returns:
            One day's pay as Decimal
        """
        total_wages, _ = self._get_4_week_earnings(
            employee_id=employee_id,
            before_date=holiday_date,
            current_run_id=current_run_id,
        )

        # Handle new employees with no historical data based on config
        if total_wages == Decimal("0"):
            if new_employee_fallback == "pro_rated":
                logger.info(
                    "4-week daily formula: No historical data for employee %s, "
                    "using 30-day avg fallback (pro_rated)",
                    employee_id,
                )
                return self._apply_30_day_average(employee_fallback, Decimal("8"))
            else:
                # "ineligible" or None: return $0
                logger.info(
                    "4-week daily formula: No historical data for employee %s, "
                    "returning $0 (ineligible fallback)",
                    employee_id,
                )
                return Decimal("0")

        # Estimate days worked based on records (simplified version)
        # In a full implementation, this would query actual days worked
        days_worked = Decimal("20")  # Default to 20 working days in 4 weeks

        daily_pay = total_wages / days_worked

        logger.debug(
            "4-week daily formula: $%.2f / %d days = $%.2f",
            float(total_wages),
            int(days_worked),
            float(daily_pay),
        )

        return daily_pay

    def _get_4_week_earnings(
        self,
        employee_id: str,
        before_date: date,
        current_run_id: str,
    ) -> tuple[Decimal, Decimal]:
        """Query past 4 weeks payroll records.

        Args:
            employee_id: Employee ID
            before_date: Date to look back from (typically the holiday date)
            current_run_id: Current run ID to exclude from query

        Returns:
            Tuple of (total_wages, vacation_pay)
        """
        # Calculate 4-week window (28 days before the holiday)
        start_date = before_date - timedelta(days=28)

        try:
            # Query payroll records with approved/paid runs in the 4-week window
            # Join with payroll_runs to filter by status and pay_date
            result = self.supabase.table("payroll_records").select(
                "gross_regular, gross_overtime, vacation_pay_paid, "
                "payroll_runs!inner(id, pay_date, status)"
            ).eq(
                "employee_id", employee_id
            ).neq(
                "payroll_run_id", current_run_id
            ).gte(
                "payroll_runs.pay_date", start_date.isoformat()
            ).lt(
                "payroll_runs.pay_date", before_date.isoformat()
            ).in_(
                "payroll_runs.status", COMPLETED_RUN_STATUSES
            ).execute()

            records = result.data or []

            if not records:
                return Decimal("0"), Decimal("0")

            total_wages = Decimal("0")
            vacation_pay = Decimal("0")

            for record in records:
                gross_regular = Decimal(str(record.get("gross_regular", 0)))
                gross_overtime = Decimal(str(record.get("gross_overtime", 0)))
                vac_pay = Decimal(str(record.get("vacation_pay_paid", 0)))

                total_wages += gross_regular + gross_overtime
                vacation_pay += vac_pay

            logger.debug(
                "4-week earnings for %s: wages=$%.2f, vacation=$%.2f (%d records)",
                employee_id,
                float(total_wages),
                float(vacation_pay),
                len(records),
            )

            return total_wages, vacation_pay

        except Exception as e:
            logger.error("Failed to query 4-week earnings: %s", e)
            return Decimal("0"), Decimal("0")

    def _get_28_day_earnings(
        self,
        employee_id: str,
        before_date: date,
        current_run_id: str,
    ) -> tuple[Decimal, Decimal, Decimal]:
        """Query past 28 days payroll records for Saskatchewan formula.

        Args:
            employee_id: Employee ID
            before_date: Date to look back from (typically the holiday date)
            current_run_id: Current run ID to exclude from query

        Returns:
            Tuple of (regular_wages, vacation_pay, holiday_pay)
            Note: Does NOT include overtime wages (per Saskatchewan SEA)
        """
        start_date = before_date - timedelta(days=28)

        try:
            result = self.supabase.table("payroll_records").select(
                "gross_regular, vacation_pay_paid, holiday_pay, "
                "payroll_runs!inner(id, pay_date, status)"
            ).eq(
                "employee_id", employee_id
            ).neq(
                "payroll_run_id", current_run_id
            ).gte(
                "payroll_runs.pay_date", start_date.isoformat()
            ).lt(
                "payroll_runs.pay_date", before_date.isoformat()
            ).in_(
                "payroll_runs.status", COMPLETED_RUN_STATUSES
            ).execute()

            records = result.data or []

            if not records:
                return Decimal("0"), Decimal("0"), Decimal("0")

            regular_wages = Decimal("0")
            vacation_pay = Decimal("0")
            holiday_pay = Decimal("0")

            for record in records:
                regular_wages += Decimal(str(record.get("gross_regular", 0)))
                vacation_pay += Decimal(str(record.get("vacation_pay_paid", 0)))
                holiday_pay += Decimal(str(record.get("holiday_pay", 0)))

            logger.debug(
                "28-day earnings for %s: wages=$%.2f, vacation=$%.2f, holiday=$%.2f (%d records)",
                employee_id,
                float(regular_wages),
                float(vacation_pay),
                float(holiday_pay),
                len(records),
            )

            return regular_wages, vacation_pay, holiday_pay

        except Exception as e:
            logger.error("Failed to query 28-day earnings: %s", e)
            return Decimal("0"), Decimal("0"), Decimal("0")

    def _apply_5_percent_28_days(
        self,
        employee_id: str,
        holiday_date: date,
        current_run_id: str,
        percentage: Decimal,
        include_vacation_pay: bool,
        include_previous_holiday_pay: bool,
        current_period_gross: Decimal,
        new_employee_fallback: str | None,
    ) -> Decimal:
        """Apply Saskatchewan-style 5% formula.

        Formula: percentage × (wages in past 28 days)
        Includes: regular wages, optionally vacation pay and previous holiday pay
        Excludes: overtime (per Saskatchewan Employment Act)

        For new employees with no historical data, behavior is config-driven:
        - "pro_rated": Use current period gross as base (SK, ON)
        - "ineligible": Return $0 (BC, AB, etc.)

        Reference: Saskatchewan Holiday Pay Calculator
        https://apps.saskatchewan.ca/lrws/calculator/holidaypay/

        Args:
            employee_id: Employee ID
            holiday_date: The holiday date (for 28-day lookback)
            current_run_id: Current run ID to exclude from queries
            percentage: Percentage to apply (e.g., 0.05 for 5%)
            include_vacation_pay: Whether to include vacation pay in base
            include_previous_holiday_pay: Whether to include previous holiday pay in base
            current_period_gross: Current period gross pay (for new employees)
            new_employee_fallback: Config-driven fallback for new employees

        Returns:
            Holiday pay amount as Decimal
        """
        regular_wages, vacation_pay, previous_holiday_pay = self._get_28_day_earnings(
            employee_id=employee_id,
            before_date=holiday_date,
            current_run_id=current_run_id,
        )

        # Build base amount from historical data
        base = regular_wages
        if include_vacation_pay:
            base += vacation_pay
        if include_previous_holiday_pay:
            base += previous_holiday_pay

        # Handle new employees with no historical data based on config
        if base == Decimal("0"):
            if new_employee_fallback == "pro_rated" and current_period_gross > Decimal("0"):
                base = current_period_gross
                logger.info(
                    "5%% 28-day formula: No historical data for employee %s, "
                    "using current period gross $%.2f (pro_rated fallback)",
                    employee_id,
                    float(current_period_gross),
                )
            else:
                # "ineligible" or None: return $0
                logger.info(
                    "5%% 28-day formula: No historical data for employee %s, "
                    "returning $0 (ineligible fallback)",
                    employee_id,
                )
                return Decimal("0")

        holiday_pay = base * percentage

        logger.debug(
            "5%% 28-day formula: $%.2f × %.1f%% = $%.2f "
            "(hist_wages=$%.2f, vac=$%.2f, hol=$%.2f, curr_gross=$%.2f)",
            float(base),
            float(percentage * 100),
            float(holiday_pay),
            float(regular_wages),
            float(vacation_pay),
            float(previous_holiday_pay),
            float(current_period_gross),
        )

        return holiday_pay

    def _calculate_premium_pay(
        self,
        employee: dict[str, Any],
        hours_worked: Decimal,
        config: HolidayPayConfig,
    ) -> Decimal:
        """Calculate premium pay for working on a statutory holiday.

        Formula: hours_worked × hourly_rate × premium_rate

        Args:
            employee: Employee data dict
            hours_worked: Number of hours worked on the holiday
            config: HolidayPayConfig for the province

        Returns:
            Premium pay as Decimal
        """
        hourly_rate = GrossCalculator.calculate_hourly_rate(employee)
        premium_rate = config.premium_rate
        premium_pay = hours_worked * hourly_rate * premium_rate

        logger.debug(
            "Premium pay: %.2f hours × $%.2f × %.1f = $%.2f",
            float(hours_worked),
            float(hourly_rate),
            float(premium_rate),
            float(premium_pay),
        )

        return premium_pay
