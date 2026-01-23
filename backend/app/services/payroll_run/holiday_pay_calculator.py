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

from dateutil.relativedelta import relativedelta

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
            # Use configurable window days from config, with sensible defaults
            # eligibility_lookback_days: how far back to look for work history
            # last_first_window_days: how far forward to look after holiday
            lookback_days = config.formula_params.eligibility_lookback_days or 30
            forward_days = config.formula_params.last_first_window_days or 14

            # Calculate date range based on config
            holiday_dates = []
            for h in holidays_in_period:
                try:
                    holiday_dates.append(date.fromisoformat(h.get("holiday_date", "")))
                except (ValueError, TypeError):
                    pass
            if holiday_dates:
                earliest = min(holiday_dates) - timedelta(days=lookback_days)
                latest = max(holiday_dates) + timedelta(days=forward_days)
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

            # Check if holiday falls on a regular work day (for Alberta "5 of 9" rule)
            is_regular_work_day = False
            checked_5_of_9_rule = False  # Track if we actually checked the rule
            if config.eligibility.require_last_first_rule and province == "AB":
                # Alberta uses "5 of 9" rule to determine regular work days
                hire_date = None
                try:
                    hire_date = date.fromisoformat(employee.get("hire_date")) if employee.get("hire_date") else None
                except (ValueError, TypeError):
                    hire_date = None
                is_regular_work_day = self._is_regular_work_day_5_of_9(
                    employee["id"], holiday_date, hire_date, config=config
                )
                checked_5_of_9_rule = True

            # Store is_regular_work_day in details for transparency
            holiday_detail["is_regular_work_day"] = is_regular_work_day

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
                # For Alberta: Check if holiday is on a regular work day using "5 of 9" rule
                # Non-regular day (regardless of worked or not) = $0 regular holiday pay
                hours_worked = hours_worked_by_date.get(holiday_date_str, Decimal("0"))

                # NL Special Rule (NL Labour Standards Act s.17):
                # - Full shift worked (>= normal hours): 2x wages ONLY (no regular holiday pay)
                # - Partial shift worked (< normal hours): regular wages + full day's holiday pay
                # NL s.17(2) uses "normal working day" which is employee-specific
                nl_full_shift_worked = False
                expected_daily_hours = self._get_normal_daily_hours(
                    employee, config, holiday_date
                )
                if province == "NL" and hours_worked >= expected_daily_hours:
                    # NL full shift: Skip regular holiday pay (will get 2x premium below)
                    nl_full_shift_worked = True
                    daily_pay = Decimal("0")
                    logger.debug(
                        "NL s.17(a): Full shift (%s hrs) worked on %s - giving 2x wages only, no regular holiday pay",
                        hours_worked, holiday_name,
                    )
                elif checked_5_of_9_rule and not is_regular_work_day:
                    # Alberta rule: Non-regular day = no regular pay (premium only if worked)
                    daily_pay = Decimal("0")
                    logger.debug(
                        "Holiday %s is NOT a regular work day (5 of 9 rule): $0 regular pay (premium only if worked)",
                        holiday_name,
                    )
                else:
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
                if nl_full_shift_worked:
                    holiday_detail["nl_rule"] = "s.17(a) full shift - 2x wages only"

            # Calculate Premium Pay (if employee worked on this holiday)
            hours_worked = hours_worked_by_date.get(holiday_date_str, Decimal("0"))
            if hours_worked > 0:
                # NL Partial Shift Rule (NL Labour Standards Act s.17(2)):
                # If worked < normal daily hours, give regular wages (1.0x) + holiday pay
                # NOT 2x premium - the 2x only applies for full shift
                # NL s.17(2) uses "normal working day" which is employee-specific
                expected_daily_hours = self._get_normal_daily_hours(
                    employee, config, holiday_date
                )
                if province == "NL" and hours_worked < expected_daily_hours:
                    # NL partial shift: use 1.0x rate instead of premium_rate (2.0x)
                    hourly_rate = GrossCalculator.calculate_hourly_rate(employee)
                    premium_pay = hours_worked * hourly_rate * Decimal("1.0")
                    holiday_detail["nl_rule"] = "s.17(2) partial shift - regular wages + holiday pay"
                    logger.debug(
                        "NL s.17(2): Partial shift (%s hrs < %s) on %s - "
                        "giving regular wages ($%.2f) + holiday pay",
                        hours_worked, expected_daily_hours, holiday_name,
                        float(premium_pay),
                    )
                else:
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
        min_days = config.eligibility.min_employment_days

        if config.eligibility.count_work_days:
            # Alberta-style: count actual work days in the eligibility period
            # Use relativedelta for accurate calendar month calculation (not period_months * 30)
            period_months = config.eligibility.eligibility_period_months or 12
            period_start = holiday_date - relativedelta(months=period_months)
            work_days = self._count_work_days_for_eligibility(
                employee.get("id"), period_start, holiday_date
            )
            if work_days < min_days:
                logger.debug(
                    "Employee %s failed work days eligibility: %d < %d (in %d months)",
                    employee.get("id"), work_days, min_days, period_months
                )
                return False
        else:
            # Standard calendar days since hire
            days_employed = (holiday_date - hire_date).days
            if days_employed < min_days:
                return False

        # Check 2: require_last_first_rule (work before and after holiday)
        #
        # Improved implementation: Finds actual "last scheduled day before" and
        # "first scheduled day after" by searching work history.
        #
        # Per Alberta Employment Standards Code s.23(2)(a): Employee must work
        # on their last scheduled shift before and first scheduled shift after
        # the holiday, without employer consent for absence.
        # Reference: https://www.alberta.ca/alberta-general-holidays
        if config.eligibility.require_last_first_rule:
            # Get configurable search window from config (default: 28 days)
            max_search_days = config.formula_params.last_first_window_days or 28
            # Use strict mode (fail-closed) for provinces with strict requirements
            # Strict provinces: AB, PE, NT, NU, YT (require actual work on last/first day)
            strict_mode = True  # Default to strict for compliance

            if timesheet_entries is not None:
                # Use passed timesheet entries (for testing or when data is already loaded)
                worked_before, worked_after = self._check_last_first_rule_from_entries(
                    timesheet_entries, holiday_date, strict_mode=strict_mode
                )
            else:
                # Query database for timesheet data
                worked_before, worked_after, _, _ = (
                    self._check_last_first_rule_improved(
                        employee.get("id"),
                        holiday_date,
                        max_search_days=max_search_days,
                        strict_mode=strict_mode,
                    )
                )
            if not (worked_before and worked_after):
                logger.debug(
                    "Employee %s failed last/first rule: worked_before=%s, worked_after=%s",
                    employee.get("id"),
                    worked_before,
                    worked_after,
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

        min_days = config.eligibility.min_employment_days

        # Check minimum days - use work days for Alberta, calendar days for others
        if config.eligibility.count_work_days:
            # Alberta-style: count actual work days in the eligibility period
            period_months = config.eligibility.eligibility_period_months or 12
            period_start = holiday_date - relativedelta(months=period_months)
            work_days = self._count_work_days_for_eligibility(
                employee.get("id"), period_start, holiday_date
            )
            if work_days < min_days:
                return f"< {min_days} work days in past {period_months} months ({work_days} work days)"
        else:
            # Standard calendar days since hire
            days_employed = (holiday_date - hire_date).days
            if days_employed < min_days:
                return f"< {min_days} days employed ({days_employed} days)"

        # Check last/first rule
        if config.eligibility.require_last_first_rule:
            max_search_days = config.formula_params.last_first_window_days or 28
            strict_mode = True

            if timesheet_entries is not None:
                worked_before, worked_after = self._check_last_first_rule_from_entries(
                    timesheet_entries, holiday_date, strict_mode=strict_mode
                )
            else:
                worked_before, worked_after, _, _ = (
                    self._check_last_first_rule_improved(
                        employee.get("id"),
                        holiday_date,
                        max_search_days=max_search_days,
                        strict_mode=strict_mode,
                    )
                )
            if not (worked_before and worked_after):
                return "did not work on last scheduled day before/first scheduled day after holiday"

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

        Used for BC/NS/PE "15 of 30 days" eligibility rule.

        LIMITATION: Currently only counts days with hours > 0 from timesheet
        entries. Per official rules (BC ESA, NS LSC, PEI ESA), this should
        count days "entitled to wages" which includes:
        - Days actually worked (currently counted ✓)
        - Paid vacation days (currently NOT counted)
        - Paid sick leave (currently NOT counted)
        - Other paid leave days (currently NOT counted)

        This is a conservative implementation that may undercount eligible
        days for employees with paid leave. HR can use the holiday_pay_exempt
        flag to manually override eligibility if needed.

        TODO: Enhance to also check payroll_records for days with wages paid
        but no hours worked (requires data model changes).

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

    def _get_normal_daily_hours(
        self,
        employee: dict[str, Any],
        config: HolidayPayConfig,
        holiday_date: date,
    ) -> Decimal:
        """Calculate the employee's normal daily hours.

        Per NL Labour Standards Act s.17(2): Uses "the number of hours that
        the employee would work if it were a normal working day" which is
        employee-specific, not a fixed value.

        For hourly employees: Calculate typical daily hours from recent
        timesheet history (mode of daily hours in last 4 weeks).

        For salaried employees: Use default_daily_hours from config
        (typically 8 hours, since salary employees have fixed schedules).

        Fallback: If insufficient data, use default_daily_hours.

        Args:
            employee: Employee data dict
            config: HolidayPayConfig for the province
            holiday_date: Holiday date for lookback calculation

        Returns:
            Normal daily hours as Decimal
        """
        default_hours = Decimal(str(config.formula_params.default_daily_hours or 8))

        # Salaried employees have fixed schedules - use default
        if not employee.get("hourly_rate"):
            logger.debug(
                "Normal daily hours for salaried employee %s: %.2f (default)",
                employee.get("id"),
                float(default_hours),
            )
            return default_hours

        # Hourly employees - calculate from recent timesheet history
        # Look at last 4 weeks to find typical daily hours
        start_date = holiday_date - timedelta(days=28)
        end_date = holiday_date - timedelta(days=1)

        try:
            result = self.supabase.table("timesheet_entries").select(
                "work_date, regular_hours, overtime_hours"
            ).eq(
                "employee_id", employee["id"]
            ).gte(
                "work_date", start_date.isoformat()
            ).lte(
                "work_date", end_date.isoformat()
            ).execute()

            entries = result.data or []

            if not entries:
                logger.debug(
                    "Normal daily hours for hourly employee %s: %.2f (no data, using default)",
                    employee.get("id"),
                    float(default_hours),
                )
                return default_hours

            # Calculate total hours per work day (aggregate by date)
            hours_by_date: dict[str, Decimal] = {}
            for entry in entries:
                work_date_str = entry.get("work_date", "")
                regular = Decimal(str(entry.get("regular_hours", 0) or 0))
                # Only count regular hours for "normal" day - overtime is extra
                if regular > 0:
                    if work_date_str not in hours_by_date:
                        hours_by_date[work_date_str] = Decimal("0")
                    hours_by_date[work_date_str] += regular

            if not hours_by_date:
                logger.debug(
                    "Normal daily hours for hourly employee %s: %.2f (no work days, using default)",
                    employee.get("id"),
                    float(default_hours),
                )
                return default_hours

            # Find the mode (most common daily hours) - this represents "normal"
            from collections import Counter

            # Round to nearest 0.5 to find typical shifts (7.5h, 8h, 10h, etc.)
            rounded_hours = [
                float(round(h * 2) / 2) for h in hours_by_date.values()
            ]
            if not rounded_hours:
                return default_hours

            hour_counts = Counter(rounded_hours)
            most_common_hours = hour_counts.most_common(1)[0][0]
            normal_hours = Decimal(str(most_common_hours))

            logger.debug(
                "Normal daily hours for hourly employee %s: %.2f (from %d work days, mode of %s)",
                employee.get("id"),
                float(normal_hours),
                len(hours_by_date),
                [f"{h:.1f}h" for h in sorted(set(rounded_hours))],
            )

            return normal_hours

        except Exception as e:
            logger.warning(
                "Failed to calculate normal daily hours for employee %s: %s, using default",
                employee.get("id"),
                e,
            )
            return default_hours

    def _count_work_days_for_eligibility(
        self,
        employee_id: str,
        start_date: date,
        end_date: date,
    ) -> int:
        """Count unique days with work in date range for eligibility check.

        This queries the database directly (unlike _count_days_worked_in_period
        which uses pre-fetched entries). Used for Alberta-style work day eligibility.

        Args:
            employee_id: Employee ID
            start_date: Start of date range (inclusive)
            end_date: End of date range (exclusive, typically the holiday date)

        Returns:
            Number of unique days with hours > 0 in the period
        """
        try:
            result = self.supabase.table("timesheet_entries").select(
                "work_date, regular_hours, overtime_hours"
            ).eq(
                "employee_id", employee_id
            ).gte(
                "work_date", start_date.isoformat()
            ).lt(
                "work_date", end_date.isoformat()
            ).execute()

            entries = result.data or []

            days_with_work: set[str] = set()
            for entry in entries:
                work_date = entry.get("work_date")
                if not work_date:
                    continue
                regular = Decimal(str(entry.get("regular_hours", 0) or 0))
                overtime = Decimal(str(entry.get("overtime_hours", 0) or 0))
                if regular + overtime > 0:
                    days_with_work.add(work_date)

            work_days_count = len(days_with_work)
            logger.debug(
                "Work days eligibility check: employee=%s, period=%s to %s, work_days=%d",
                employee_id, start_date, end_date, work_days_count
            )
            return work_days_count

        except Exception as e:
            logger.warning(
                "Failed to count work days for employee %s: %s", employee_id, e
            )
            # Conservative: return 0 (ineligible) on error
            return 0

    def _find_nearest_work_day(
        self,
        employee_id: str,
        holiday_date: date,
        direction: str,  # "before" or "after"
        max_days: int = 28,
    ) -> date | None:
        """Find the nearest scheduled work day before or after holiday.

        This implements Alberta's "last scheduled day before" and "first scheduled
        day after" rule by searching for the first day with actual work history.

        Args:
            employee_id: Employee ID
            holiday_date: The holiday date
            direction: "before" to search backward, "after" to search forward
            max_days: Maximum days to search (default 28 days / 4 weeks)

        Returns:
            The nearest work day date, or None if not found
        """
        if direction == "before":
            start_date = holiday_date - timedelta(days=max_days)
            end_date = holiday_date - timedelta(days=1)
        else:  # after
            start_date = holiday_date + timedelta(days=1)
            end_date = holiday_date + timedelta(days=max_days)

        try:
            result = (
                self.supabase.table("timesheet_entries")
                .select("work_date, regular_hours, overtime_hours")
                .eq("employee_id", employee_id)
                .gte("work_date", start_date.isoformat())
                .lte("work_date", end_date.isoformat())
                .order("work_date", desc=(direction == "before"))
                .limit(1)
                .execute()
            )

            if result.data and len(result.data) > 0:
                entry = result.data[0]
                regular = Decimal(str(entry.get("regular_hours", 0) or 0))
                overtime = Decimal(str(entry.get("overtime_hours", 0) or 0))
                if regular + overtime > 0:
                    work_date_str = entry.get("work_date")
                    if work_date_str:
                        return date.fromisoformat(work_date_str)

            return None
        except Exception as e:
            logger.warning("Failed to find nearest work day: %s", e)
            return None

    def _check_last_first_rule_from_entries(
        self,
        timesheet_entries: list[dict[str, Any]],
        holiday_date: date,
        strict_mode: bool = True,
    ) -> tuple[bool, bool]:
        """Check last/first rule using passed timesheet entries.

        Per Alberta/Ontario/PEI Employment Standards:
        - Employee must work on their LAST scheduled day before the holiday
        - Employee must work on their FIRST scheduled day after the holiday

        This method finds the actual last/first scheduled work days from timesheet
        history and verifies attendance on those specific days.

        LIMITATIONS (due to timesheet-only data model):
        This implementation determines "scheduled day" by looking for days with
        hours > 0 in timesheet history. It CANNOT handle:

        1. Scheduled but absent with good reason (sick leave with valid excuse)
           - Many provinces (AB, ON, NS, etc.) have "good reason" exceptions
           - Employee would show no hours but should still be eligible

        2. Permitted absence (employer consented to absence)
           - Employee explicitly asked for and got permission to miss

        3. Employer told not to report
           - Employee was available but employer had no work

        4. Paid leave with no hours logged
           - Vacation, bereavement, etc. may not have timesheet entries

        WORKAROUND: HR can use the `holiday_pay_exempt` flag to manually override
        eligibility for employees who fall into these categories.

        TODO: Consider adding a `scheduled_shifts` data model or an `excused_absence`
        flag to timesheet entries to handle these cases systematically.

        Args:
            timesheet_entries: List of timesheet entry dictionaries
            holiday_date: The holiday date
            strict_mode: If True, no data = ineligible (fail-closed).
                        If False, no data = eligible (fail-open, legacy behavior)

        Returns:
            Tuple of (worked_on_last_scheduled_day, worked_on_first_scheduled_day)
        """
        # Collect all work dates with hours > 0
        work_dates_before: list[date] = []
        work_dates_after: list[date] = []

        for entry in timesheet_entries:
            work_date_str = entry.get("work_date")
            if not work_date_str:
                continue

            try:
                work_date = date.fromisoformat(work_date_str)
            except (ValueError, TypeError):
                continue

            regular = Decimal(str(entry.get("regular_hours", 0) or 0))
            overtime = Decimal(str(entry.get("overtime_hours", 0) or 0))

            if regular + overtime > 0:
                if work_date < holiday_date:
                    work_dates_before.append(work_date)
                elif work_date > holiday_date:
                    work_dates_after.append(work_date)

        # Find last scheduled day before holiday (most recent work date before holiday)
        last_scheduled_before = max(work_dates_before) if work_dates_before else None
        # Find first scheduled day after holiday (earliest work date after holiday)
        first_scheduled_after = min(work_dates_after) if work_dates_after else None

        # If no work history found, apply strict_mode logic
        if last_scheduled_before is None and first_scheduled_after is None:
            if strict_mode:
                logger.debug(
                    "Last/first rule (from entries): No work history found for holiday %s, "
                    "returning ineligible (strict_mode=True)",
                    holiday_date,
                )
                return False, False
            else:
                logger.debug(
                    "Last/first rule (from entries): No work history found for holiday %s, "
                    "returning eligible (strict_mode=False, legacy fallback)",
                    holiday_date,
                )
                return True, True

        # Check if employee worked on the specific last/first scheduled days
        # Since we built the lists from work entries with hours > 0, if the date
        # exists in our list, the employee worked that day
        worked_before = last_scheduled_before is not None
        worked_after = first_scheduled_after is not None

        logger.debug(
            "Last/first rule (from entries): holiday=%s, last_scheduled=%s (worked=%s), "
            "first_scheduled=%s (worked=%s)",
            holiday_date, last_scheduled_before, worked_before,
            first_scheduled_after, worked_after,
        )

        return worked_before, worked_after

    def _check_last_first_rule_improved(
        self,
        employee_id: str,
        holiday_date: date,
        max_search_days: int = 28,
        strict_mode: bool = True,
    ) -> tuple[bool, bool, date | None, date | None]:
        """Check last/first rule using actual scheduled work days.

        Per Alberta Employment Standards:
        - Employee must work on "last scheduled day before" holiday
        - Employee must work on "first scheduled day after" holiday

        This finds the actual nearest scheduled work days by looking at work history.

        LIMITATIONS: Same as _check_last_first_rule_from_entries - cannot handle
        excused absences, permitted absences, or paid leave without hours.
        See that method's docstring for details and workarounds.

        Args:
            employee_id: Employee ID
            holiday_date: The holiday date
            max_search_days: Maximum days to search before/after holiday (configurable)
            strict_mode: If True, no data = ineligible (fail-closed).
                        If False, no data = eligible (fail-open)

        Returns:
            Tuple of (worked_before, worked_after, last_scheduled_day, first_scheduled_day)
            - worked_before: True if employee worked on last scheduled day before
            - worked_after: True if employee worked on first scheduled day after
            - last_scheduled_day: The last scheduled work day before holiday (or None)
            - first_scheduled_day: The first scheduled work day after holiday (or None)
        """
        # Find nearest scheduled work days with configurable search window
        last_scheduled_day = self._find_nearest_work_day(
            employee_id, holiday_date, direction="before", max_days=max_search_days
        )
        first_scheduled_day = self._find_nearest_work_day(
            employee_id, holiday_date, direction="after", max_days=max_search_days
        )

        # If NO scheduled days found at all, employee has no work history
        # Apply strict_mode to determine behavior
        if last_scheduled_day is None and first_scheduled_day is None:
            if strict_mode:
                logger.debug(
                    "No scheduled work days found for employee %s within %d days, "
                    "returning ineligible (strict_mode=True)",
                    employee_id, max_search_days,
                )
                return False, False, None, None
            else:
                logger.debug(
                    "No scheduled work days found for employee %s within %d days, "
                    "returning eligible (strict_mode=False, legacy fallback)",
                    employee_id, max_search_days,
                )
                return True, True, None, None

        # Default behavior based on strict_mode when partial data
        worked_before = not strict_mode  # False if strict, True if lenient
        worked_after = not strict_mode

        # Check if employee worked on last scheduled day before
        if last_scheduled_day is not None:
            try:
                result = (
                    self.supabase.table("timesheet_entries")
                    .select("regular_hours, overtime_hours")
                    .eq("employee_id", employee_id)
                    .eq("work_date", last_scheduled_day.isoformat())
                    .execute()
                )

                if result.data and len(result.data) > 0:
                    entry = result.data[0]
                    regular = Decimal(str(entry.get("regular_hours", 0) or 0))
                    overtime = Decimal(str(entry.get("overtime_hours", 0) or 0))
                    worked_before = (regular + overtime) > 0
                else:
                    worked_before = False
            except Exception as e:
                logger.warning("Failed to check work on last scheduled day: %s", e)
                # On error, apply strict_mode behavior
                worked_before = not strict_mode

        # Check if employee worked on first scheduled day after
        if first_scheduled_day is not None:
            try:
                result = (
                    self.supabase.table("timesheet_entries")
                    .select("regular_hours, overtime_hours")
                    .eq("employee_id", employee_id)
                    .eq("work_date", first_scheduled_day.isoformat())
                    .execute()
                )

                if result.data and len(result.data) > 0:
                    entry = result.data[0]
                    regular = Decimal(str(entry.get("regular_hours", 0) or 0))
                    overtime = Decimal(str(entry.get("overtime_hours", 0) or 0))
                    worked_after = (regular + overtime) > 0
                else:
                    worked_after = False
            except Exception as e:
                logger.warning("Failed to check work on first scheduled day: %s", e)
                # On error, apply strict_mode behavior
                worked_after = not strict_mode

        logger.debug(
            "Last/first rule check: last_scheduled=%s (worked=%s), first_scheduled=%s (worked=%s), "
            "strict_mode=%s",
            last_scheduled_day,
            worked_before,
            first_scheduled_day,
            worked_after,
            strict_mode,
        )

        return worked_before, worked_after, last_scheduled_day, first_scheduled_day

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

    def _is_regular_work_day_5_of_9(
        self,
        employee_id: str,
        holiday_date: date,
        hire_date: date | None,
        config: HolidayPayConfig | None = None,
    ) -> bool:
        """Check if holiday falls on a regular work day using Alberta's "5 of 9" rule.

        Official rule: In the last N weeks before the holiday, if the employee
        has worked M times on the same day of week, it's a regular work day.

        Default values (configurable via formula_params):
        - weeks_before (alberta_5_of_9_weeks): 9
        - threshold (alberta_5_of_9_threshold): 5

        Reference: Alberta Employment Standards Tool Kit - Module 6: General Holidays
        https://open.alberta.ca/dataset/06084a7e-dcfb-4aaa-b142-259f91370c76/resource/

        Args:
            employee_id: Employee ID
            holiday_date: The holiday date
            hire_date: Employee's hire date (for new employee handling)
            config: Optional HolidayPayConfig for configurable parameters

        Returns:
            True if holiday is on a regular work day, False otherwise
        """
        # Get the day of week for the holiday (0=Monday, 6=Sunday)
        holiday_dow = holiday_date.weekday()

        # Use configurable parameters from config, with defaults for Alberta
        weeks_before = 9  # Default Alberta value
        base_threshold = 5  # Default Alberta value

        if config and config.formula_params:
            weeks_before = config.formula_params.alberta_5_of_9_weeks or 9
            base_threshold = config.formula_params.alberta_5_of_9_threshold or 5

        # Calculate N-week window
        # Start: Sunday of the week, N weeks before holiday
        # End: Day before holiday
        start_of_week = holiday_date - timedelta(days=holiday_date.weekday() + 1)  # Sunday
        start_date = start_of_week - timedelta(weeks=weeks_before)
        end_date = holiday_date - timedelta(days=1)

        # Adjust threshold for new employees (hired < N weeks ago)
        threshold = base_threshold
        if hire_date and hire_date > start_date:
            days_employed = (holiday_date - hire_date).days
            weeks_employed = max(0, days_employed // 7)
            if weeks_employed < weeks_before:
                # Pro-rated threshold for new employees
                threshold = max(1, int(weeks_employed * base_threshold / weeks_before))
                start_date = hire_date  # Only count from hire date

        # Query timesheet_entries for the N-week period
        try:
            result = self.supabase.table("timesheet_entries").select(
                "work_date, regular_hours, overtime_hours"
            ).eq("employee_id", employee_id).gte(
                "work_date", start_date.isoformat()
            ).lte("work_date", end_date.isoformat()).execute()

            # Count matching weekdays with hours > 0
            count = 0
            for entry in result.data or []:
                work_date = date.fromisoformat(entry["work_date"])
                if work_date.weekday() == holiday_dow:
                    regular = Decimal(str(entry.get("regular_hours", 0)))
                    overtime = Decimal(str(entry.get("overtime_hours", 0)))
                    if regular + overtime > 0:
                        count += 1

            is_regular = count >= threshold

            logger.debug(
                "5 of 9 rule: employee=%s, holiday=%s (%s), window=%s to %s, "
                "count=%d, threshold=%d (base=%d), weeks=%d, is_regular=%s",
                employee_id, holiday_date, holiday_date.strftime("%A"),
                start_date, end_date, count, threshold, base_threshold,
                weeks_before, is_regular
            )

            return is_regular
        except Exception as e:
            logger.warning("Failed to check 5 of 9 rule for employee %s: %s", employee_id, e)
            # Conservative: assume regular for eligibility on error
            return True

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
        - 4_week_average: (past 4 weeks wages + vacation pay) / divisor (ON, Federal, QC)
        - 30_day_average: Average daily pay based on 30 days (BC, NS, PE, NB, YT, NU)
        - 4_week_average_daily: Wages in 4 weeks / days worked (AB)
        - current_period_daily: Current period gross / work days in period
        - 5_percent_28_days: 5% of wages in past 28 days (SK, MB)
        - 3_week_average_nl: hourly_rate × (hours in 3 weeks / 15) (NL)
        - irregular_hours: percentage × wages in lookback weeks (YT irregular-hours employees)
        - commission: 1/divisor of wages in lookback weeks (QC/Federal commission employees)

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
                    include_overtime=params.include_overtime,
                    employee_fallback=employee,
                    new_employee_fallback=params.new_employee_fallback,
                )
            case "4_week_average_daily":
                return self._apply_4_week_daily(
                    employee_id=employee["id"],
                    holiday_date=holiday_date,
                    current_run_id=current_run_id,
                    include_overtime=params.include_overtime,
                    employee_fallback=employee,
                    new_employee_fallback=params.new_employee_fallback,
                )
            case "current_period_daily":
                return self._apply_current_period_daily(
                    current_period_gross=current_period_gross,
                    pay_frequency=pay_frequency,
                )
            case "5_percent_28_days":
                # Saskatchewan/Manitoba formula: 5% of wages in past N days
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
                    lookback_days=params.lookback_days or 28,
                )
            case "30_day_average":
                # BC/NS/PE/NB/YT/NU style: wages in 30 days / days worked
                return self._apply_30_day_average(
                    employee_id=employee["id"],
                    employee=employee,
                    holiday_date=holiday_date,
                    method=params.method or "total_wages_div_days",
                    include_overtime=params.include_overtime,
                    default_daily_hours=params.default_daily_hours,
                    new_employee_fallback=params.new_employee_fallback,
                    lookback_days=params.lookback_days or 30,
                )
            case "3_week_average_nl":
                # Newfoundland formula: hourly_rate × (hours in 3 weeks / 15)
                return self._apply_3_week_average_nl(
                    employee_id=employee["id"],
                    employee=employee,
                    holiday_date=holiday_date,
                    lookback_weeks=params.lookback_weeks_nl or 3,
                    divisor=params.nl_divisor or 15,
                    include_overtime=params.include_overtime,
                )
            case "irregular_hours":
                # Yukon irregular-hours employees: percentage × wages in lookback weeks
                # Reference: Yukon Employment Standards Act
                return self._apply_irregular_hours(
                    employee_id=employee["id"],
                    employee=employee,
                    holiday_date=holiday_date,
                    current_run_id=current_run_id,
                    percentage=params.irregular_hours_percentage or Decimal("0.10"),
                    lookback_weeks=params.irregular_hours_lookback_weeks or 2,
                    include_overtime=params.include_overtime,
                )
            case "commission":
                # Quebec/Federal commission employees: 1/divisor of wages in lookback weeks
                # Reference: Quebec Labour Standards Act, Canada Labour Code
                return self._apply_commission(
                    employee_id=employee["id"],
                    holiday_date=holiday_date,
                    current_run_id=current_run_id,
                    divisor=params.commission_divisor or 60,
                    lookback_weeks=params.commission_lookback_weeks or 12,
                )
            case _:
                # Unknown formula type - log error and use hourly fallback
                logger.error(
                    "Unknown formula_type '%s' for province %s, using hourly rate fallback",
                    formula_type,
                    config.province_code,
                )
                hourly_rate = GrossCalculator.calculate_hourly_rate(employee)
                return params.default_daily_hours * hourly_rate

    def _apply_30_day_average(
        self,
        employee_id: str,
        employee: dict[str, Any],
        holiday_date: date,
        method: str,
        include_overtime: bool,
        default_daily_hours: Decimal,
        new_employee_fallback: str | None,
        lookback_days: int = 30,
    ) -> Decimal:
        """Apply BC-style 30-day average formula.

        Official formula: total wages in 30 days / days with wages (or days worked)

        Methods:
        - "total_wages_div_days": Total wages / number of unique days with pay
        - "wages_div_days_worked": Wages / unique days actually worked (from timesheet)
        - "hours_times_rate": (hours in period / divisor) × hourly_rate

        Args:
            employee_id: Employee ID
            employee: Employee data dict with hourly_rate
            holiday_date: The holiday date for lookback
            method: Calculation method from config
            include_overtime: Whether to include overtime in wages
            default_daily_hours: Fallback daily hours for new employees
            new_employee_fallback: How to handle new employees ("pro_rated" or "ineligible")
            lookback_days: Number of days to look back (default: 30)

        Returns:
            One day's pay as Decimal
        """
        # Query past N days of timesheet data (configurable lookback)
        start_date = holiday_date - timedelta(days=lookback_days)
        end_date = holiday_date - timedelta(days=1)

        try:
            result = self.supabase.table("timesheet_entries").select(
                "work_date, regular_hours, overtime_hours"
            ).eq(
                "employee_id", employee_id
            ).gte(
                "work_date", start_date.isoformat()
            ).lte(
                "work_date", end_date.isoformat()
            ).execute()

            entries = result.data or []

            if not entries:
                # No timesheet data - handle based on fallback config
                if new_employee_fallback == "pro_rated":
                    # Use hourly rate × default daily hours as fallback
                    hourly_rate = GrossCalculator.calculate_hourly_rate(employee)
                    daily_pay = default_daily_hours * hourly_rate
                    logger.info(
                        "30-day avg: No data for employee %s, using pro_rated fallback: $%.2f",
                        employee_id, float(daily_pay)
                    )
                    return daily_pay
                else:
                    # "ineligible" - return $0
                    logger.info(
                        "30-day avg: No data for employee %s, returning $0 (ineligible)",
                        employee_id
                    )
                    return Decimal("0")

            # Calculate wages and days from timesheet entries
            # Use set to deduplicate days (multiple entries per day should count as 1 day)
            hourly_rate = GrossCalculator.calculate_hourly_rate(employee)
            total_hours = Decimal("0")
            days_with_work: set[str] = set()  # Track unique dates with work
            hours_by_date: dict[str, Decimal] = {}  # Track hours per date for accurate calculation

            for entry in entries:
                work_date_str = entry.get("work_date", "")
                regular = Decimal(str(entry.get("regular_hours", 0) or 0))
                overtime = Decimal(str(entry.get("overtime_hours", 0) or 0))

                if include_overtime:
                    entry_hours = regular + overtime
                else:
                    entry_hours = regular

                total_hours += entry_hours

                # Track unique days with work (deduplicated)
                if regular > 0 or overtime > 0:
                    days_with_work.add(work_date_str)
                    # Aggregate hours by date
                    if work_date_str not in hours_by_date:
                        hours_by_date[work_date_str] = Decimal("0")
                    hours_by_date[work_date_str] += entry_hours

            days_worked = len(days_with_work)

            if days_worked == 0:
                logger.warning(
                    "30-day avg: Employee %s has timesheet entries but 0 days with hours, returning $0",
                    employee_id
                )
                return Decimal("0")

            # Apply the calculation method
            if method == "hours_times_rate":
                # BC-style: (hours in period / days_worked) × hourly_rate
                # This gives average daily hours × hourly rate
                avg_daily_hours = total_hours / Decimal(str(days_worked))
                daily_pay = avg_daily_hours * hourly_rate
            elif method == "wages_div_days_worked":
                # Simple: total wages / days actually worked
                total_wages = total_hours * hourly_rate
                daily_pay = total_wages / Decimal(str(days_worked))
            else:
                # Default: "total_wages_div_days" - total wages / days with pay
                # This is the most common interpretation
                total_wages = total_hours * hourly_rate
                daily_pay = total_wages / Decimal(str(days_worked))

            logger.debug(
                "30-day avg formula: employee=%s, method=%s, total_hours=%.2f, "
                "days_worked=%d (deduplicated), daily_pay=$%.2f, include_overtime=%s",
                employee_id, method, float(total_hours), days_worked,
                float(daily_pay), include_overtime
            )

            return daily_pay

        except Exception as e:
            logger.error(
                "Failed to calculate 30-day average for employee %s: %s",
                employee_id, e
            )
            # Conservative fallback: use hourly rate × default hours
            hourly_rate = GrossCalculator.calculate_hourly_rate(employee)
            return default_daily_hours * hourly_rate

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

    def _apply_3_week_average_nl(
        self,
        employee_id: str,
        employee: dict[str, Any],
        holiday_date: date,
        lookback_weeks: int,
        divisor: int,
        include_overtime: bool,
    ) -> Decimal:
        """Apply Newfoundland 3-week average formula.

        Official formula: hourly_rate × (hours in 3 weeks / 15)

        The divisor of 15 represents the expected work days in a 3-week period
        (5 days × 3 weeks = 15 days).

        Args:
            employee_id: Employee ID
            employee: Employee data dict with hourly_rate
            holiday_date: The holiday date for lookback
            lookback_weeks: Number of weeks to look back (default: 3)
            divisor: The divisor for averaging (default: 15)
            include_overtime: Whether to include overtime hours

        Returns:
            One day's pay as Decimal
        """
        # Calculate lookback period
        start_date = holiday_date - timedelta(weeks=lookback_weeks)
        end_date = holiday_date - timedelta(days=1)

        try:
            result = self.supabase.table("timesheet_entries").select(
                "work_date, regular_hours, overtime_hours"
            ).eq(
                "employee_id", employee_id
            ).gte(
                "work_date", start_date.isoformat()
            ).lte(
                "work_date", end_date.isoformat()
            ).execute()

            entries = result.data or []

            if not entries:
                logger.info(
                    "NL 3-week avg: No data for employee %s, returning $0",
                    employee_id
                )
                return Decimal("0")

            # Sum up all hours in the period
            total_hours = Decimal("0")
            for entry in entries:
                regular = Decimal(str(entry.get("regular_hours", 0) or 0))
                overtime = Decimal(str(entry.get("overtime_hours", 0) or 0))

                if include_overtime:
                    total_hours += regular + overtime
                else:
                    total_hours += regular

            # Calculate: hourly_rate × (hours / divisor)
            hourly_rate = GrossCalculator.calculate_hourly_rate(employee)
            daily_pay = hourly_rate * (total_hours / Decimal(str(divisor)))

            logger.debug(
                "NL 3-week avg formula: employee=%s, total_hours=%.2f, divisor=%d, "
                "hourly_rate=$%.2f, daily_pay=$%.2f",
                employee_id, float(total_hours), divisor,
                float(hourly_rate), float(daily_pay)
            )

            return daily_pay

        except Exception as e:
            logger.error(
                "Failed to calculate NL 3-week average for employee %s: %s",
                employee_id, e
            )
            return Decimal("0")

    def _apply_irregular_hours(
        self,
        employee_id: str,
        employee: dict[str, Any],
        holiday_date: date,
        current_run_id: str,
        percentage: Decimal,
        lookback_weeks: int,
        include_overtime: bool,
    ) -> Decimal:
        """Apply Yukon irregular-hours formula.

        For employees with irregular hours (no fixed schedule), holiday pay is
        calculated as a percentage of wages earned in a recent period.

        Formula: percentage × total wages in lookback_weeks
        Example: Yukon = 10% × wages in past 2 weeks

        Reference: Yukon Employment Standards Act

        Args:
            employee_id: Employee ID
            employee: Employee data dict with hourly_rate
            holiday_date: The holiday date for lookback
            current_run_id: Current run ID to exclude from queries
            percentage: Percentage of wages (e.g., 0.10 for 10%)
            lookback_weeks: Number of weeks to look back (default: 2)
            include_overtime: Whether to include overtime wages

        Returns:
            Holiday pay amount as Decimal
        """
        # Calculate lookback period
        start_date = holiday_date - timedelta(weeks=lookback_weeks)
        end_date = holiday_date - timedelta(days=1)

        try:
            # Query payroll records for wages in the lookback period
            result = self.supabase.table("payroll_records").select(
                "gross_regular, gross_overtime, "
                "payroll_runs!inner(id, pay_date, status)"
            ).eq(
                "employee_id", employee_id
            ).neq(
                "payroll_run_id", current_run_id
            ).gte(
                "payroll_runs.pay_date", start_date.isoformat()
            ).lt(
                "payroll_runs.pay_date", end_date.isoformat()
            ).in_(
                "payroll_runs.status", COMPLETED_RUN_STATUSES
            ).execute()

            records = result.data or []

            if not records:
                # No historical data - try timesheet-based calculation
                hourly_rate = GrossCalculator.calculate_hourly_rate(employee)
                wages_from_timesheet = self._get_wages_from_timesheet(
                    employee_id, start_date, end_date, hourly_rate, include_overtime
                )
                if wages_from_timesheet > Decimal("0"):
                    holiday_pay = wages_from_timesheet * percentage
                    logger.info(
                        "Irregular hours formula (from timesheet): employee=%s, "
                        "wages=$%.2f × %.1f%% = $%.2f",
                        employee_id, float(wages_from_timesheet),
                        float(percentage * 100), float(holiday_pay)
                    )
                    return holiday_pay

                logger.info(
                    "Irregular hours formula: No data for employee %s, returning $0",
                    employee_id
                )
                return Decimal("0")

            # Calculate total wages from payroll records
            total_wages = Decimal("0")
            for record in records:
                gross_regular = Decimal(str(record.get("gross_regular", 0)))
                gross_overtime = Decimal(str(record.get("gross_overtime", 0)))

                if include_overtime:
                    total_wages += gross_regular + gross_overtime
                else:
                    total_wages += gross_regular

            holiday_pay = total_wages * percentage

            logger.debug(
                "Irregular hours formula: employee=%s, wages=$%.2f × %.1f%% = $%.2f, "
                "lookback_weeks=%d, include_overtime=%s",
                employee_id, float(total_wages), float(percentage * 100),
                float(holiday_pay), lookback_weeks, include_overtime
            )

            return holiday_pay

        except Exception as e:
            logger.error(
                "Failed to calculate irregular hours holiday pay for employee %s: %s",
                employee_id, e
            )
            return Decimal("0")

    def _apply_commission(
        self,
        employee_id: str,
        holiday_date: date,
        current_run_id: str,
        divisor: int,
        lookback_weeks: int,
    ) -> Decimal:
        """Apply commission employee formula.

        For commission-based employees (Quebec/Federal), holiday pay is
        calculated as a fraction of wages earned over a longer period.

        Formula: total wages in lookback_weeks / divisor
        Example: Federal/QC = wages in 12 weeks / 60 (i.e., 1/60 of 12 weeks)

        Reference:
        - Canada Labour Code Part III s.196-202
        - Quebec Labour Standards Act

        Args:
            employee_id: Employee ID
            holiday_date: The holiday date for lookback
            current_run_id: Current run ID to exclude from queries
            divisor: The divisor (e.g., 60 for 1/60)
            lookback_weeks: Number of weeks to look back (e.g., 12)

        Returns:
            Holiday pay amount as Decimal
        """
        # Calculate lookback period
        start_date = holiday_date - timedelta(weeks=lookback_weeks)
        end_date = holiday_date - timedelta(days=1)

        try:
            # Query payroll records for wages in the lookback period
            # For commission employees, we typically include all wages
            result = self.supabase.table("payroll_records").select(
                "gross_regular, gross_overtime, commission_pay, "
                "payroll_runs!inner(id, pay_date, status)"
            ).eq(
                "employee_id", employee_id
            ).neq(
                "payroll_run_id", current_run_id
            ).gte(
                "payroll_runs.pay_date", start_date.isoformat()
            ).lt(
                "payroll_runs.pay_date", end_date.isoformat()
            ).in_(
                "payroll_runs.status", COMPLETED_RUN_STATUSES
            ).execute()

            records = result.data or []

            if not records:
                logger.info(
                    "Commission formula: No data for employee %s, returning $0",
                    employee_id
                )
                return Decimal("0")

            # Calculate total wages (excluding overtime per Canada Labour Code s.196
            # and Quebec Labour Standards Act - commission formula explicitly
            # excludes overtime pay from the wage calculation)
            total_wages = Decimal("0")
            for record in records:
                gross_regular = Decimal(str(record.get("gross_regular", 0)))
                commission = Decimal(str(record.get("commission_pay", 0) or 0))

                # Per CLC s.196(2): "wages, excluding overtime pay"
                total_wages += gross_regular + commission

            holiday_pay = total_wages / Decimal(str(divisor))

            logger.debug(
                "Commission formula: employee=%s, wages=$%.2f / %d = $%.2f, "
                "lookback_weeks=%d",
                employee_id, float(total_wages), divisor,
                float(holiday_pay), lookback_weeks
            )

            return holiday_pay

        except Exception as e:
            logger.error(
                "Failed to calculate commission holiday pay for employee %s: %s",
                employee_id, e
            )
            return Decimal("0")

    def _get_wages_from_timesheet(
        self,
        employee_id: str,
        start_date: date,
        end_date: date,
        hourly_rate: Decimal,
        include_overtime: bool,
        overtime_multiplier: Decimal = Decimal("1.5"),
    ) -> Decimal:
        """Calculate wages from timesheet entries for a period.

        Helper method used when payroll records are not available.

        Args:
            employee_id: Employee ID
            start_date: Start of period
            end_date: End of period
            hourly_rate: Employee's hourly rate
            include_overtime: Whether to include overtime wages
            overtime_multiplier: Overtime pay multiplier (default 1.5x)

        Returns:
            Total wages as Decimal
        """
        try:
            result = self.supabase.table("timesheet_entries").select(
                "regular_hours, overtime_hours"
            ).eq(
                "employee_id", employee_id
            ).gte(
                "work_date", start_date.isoformat()
            ).lte(
                "work_date", end_date.isoformat()
            ).execute()

            total_regular_hours = Decimal("0")
            total_overtime_hours = Decimal("0")
            for entry in result.data or []:
                regular = Decimal(str(entry.get("regular_hours", 0) or 0))
                overtime = Decimal(str(entry.get("overtime_hours", 0) or 0))

                total_regular_hours += regular
                if include_overtime:
                    total_overtime_hours += overtime

            # Calculate wages: regular hours at base rate, overtime at multiplied rate
            regular_wages = total_regular_hours * hourly_rate
            overtime_wages = total_overtime_hours * hourly_rate * overtime_multiplier

            return regular_wages + overtime_wages

        except Exception as e:
            logger.warning(
                "Failed to get wages from timesheet for employee %s: %s",
                employee_id, e
            )
            return Decimal("0")

    def _apply_4_week_average(
        self,
        employee_id: str,
        holiday_date: date,
        current_run_id: str,
        divisor: int,
        include_vacation_pay: bool,
        include_overtime: bool,
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
            include_overtime: Whether to include overtime in wages
            employee_fallback: Employee data for fallback calculation
            new_employee_fallback: Config-driven fallback for new employees

        Returns:
            One day's pay as Decimal
        """
        total_wages, vacation_pay = self._get_4_week_earnings(
            employee_id=employee_id,
            before_date=holiday_date,
            current_run_id=current_run_id,
            include_overtime=include_overtime,
        )

        # Handle new employees with no historical data based on config
        if total_wages == Decimal("0"):
            if new_employee_fallback == "pro_rated":
                logger.info(
                    "4-week avg formula: No historical data for employee %s, "
                    "using hourly rate fallback (pro_rated)",
                    employee_id,
                )
                hourly_rate = GrossCalculator.calculate_hourly_rate(employee_fallback)
                return Decimal("8") * hourly_rate
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

    def _get_days_worked_in_4_weeks(
        self, employee_id: str, holiday_date: date
    ) -> int:
        """Query timesheet_entries to get actual days worked in 4-week period.

        Args:
            employee_id: Employee ID
            holiday_date: Holiday date (calculation period ends day before)

        Returns:
            Number of unique days with work hours > 0 in the 4-week period
        """
        # 4-week window: 28 days before holiday, ending day before holiday
        start_date = holiday_date - timedelta(days=28)
        end_date = holiday_date - timedelta(days=1)

        try:
            result = self.supabase.table("timesheet_entries").select(
                "work_date, regular_hours, overtime_hours"
            ).eq("employee_id", employee_id).gte(
                "work_date", start_date.isoformat()
            ).lte("work_date", end_date.isoformat()).execute()

            days_worked: set[date] = set()
            for entry in result.data or []:
                work_date = date.fromisoformat(entry["work_date"])
                regular = Decimal(str(entry.get("regular_hours", 0)))
                overtime = Decimal(str(entry.get("overtime_hours", 0)))
                if regular + overtime > 0:
                    days_worked.add(work_date)

            count = len(days_worked)
            logger.debug(
                "Days worked in 4-week period for %s: %d days (%s to %s)",
                employee_id, count, start_date, end_date,
            )
            return count
        except Exception as e:
            logger.warning("Failed to query days worked for employee %s: %s", employee_id, e)
            return 20  # Fallback to default on error

    def _apply_4_week_daily(
        self,
        employee_id: str,
        holiday_date: date,
        current_run_id: str,
        include_overtime: bool,
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
            include_overtime: Whether to include overtime in wages
            employee_fallback: Employee data for fallback
            new_employee_fallback: Config-driven fallback for new employees

        Returns:
            One day's pay as Decimal
        """
        # Get hourly rate from employee data
        hourly_rate = GrossCalculator.calculate_hourly_rate(employee_fallback)

        # Calculate wages from timesheet_entries (not payroll_records)
        # This ensures consistency: both numerator and denominator come from timesheet data
        total_wages = self._get_4_week_earnings_from_timesheet(
            employee_id=employee_id,
            holiday_date=holiday_date,
            hourly_rate=hourly_rate,
            include_overtime=include_overtime,
        )

        # Handle no timesheet data based on config
        if total_wages == Decimal("0"):
            if new_employee_fallback == "pro_rated":
                logger.info(
                    "4-week daily formula: No timesheet data for employee %s, "
                    "using hourly rate fallback (pro_rated)",
                    employee_id,
                )
                return Decimal("8") * hourly_rate  # hourly_rate already calculated above
            else:
                # "ineligible" or None: return $0
                logger.info(
                    "4-week daily formula: No timesheet data for employee %s, "
                    "returning $0 (ineligible fallback)",
                    employee_id,
                )
                return Decimal("0")

        # Get actual days worked from timesheet_entries
        days_worked_int = self._get_days_worked_in_4_weeks(employee_id, holiday_date)

        # Fallback to 20 days if no timesheet entries found
        if days_worked_int == 0:
            days_worked_int = 20

        days_worked = Decimal(str(days_worked_int))

        daily_pay = total_wages / days_worked

        logger.info(
            "4-week daily formula FINAL: employee_id=%s, holiday_date=%s, total_wages=$%.2f, days_worked=%d, daily_pay=$%.2f",
            employee_id, holiday_date, float(total_wages), days_worked_int, float(daily_pay)
        )
        logger.debug(
            "4-week daily formula: $%.2f / %d days = $%.2f",
            float(total_wages),
            days_worked_int,
            float(daily_pay),
        )

        return daily_pay

    def _get_4_week_earnings(
        self,
        employee_id: str,
        before_date: date,
        current_run_id: str,
        include_overtime: bool = False,
    ) -> tuple[Decimal, Decimal]:
        """Query past 4 weeks payroll records.

        Args:
            employee_id: Employee ID
            before_date: Date to look back from (typically the holiday date)
            current_run_id: Current run ID to exclude from query
            include_overtime: Whether to include overtime in total wages (default: False)

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

            # DEBUG: Log query details for troubleshooting holiday pay calculation
            logger.info(
                "4-week earnings query for %s: start_date=%s, before_date=%s, current_run_id=%s, "
                "records_found=%d, COMPLETED_STATUSES=%s, include_overtime=%s",
                employee_id, start_date, before_date, current_run_id,
                len(records), COMPLETED_RUN_STATUSES, include_overtime
            )

            if not records:
                return Decimal("0"), Decimal("0")

            total_wages = Decimal("0")
            vacation_pay = Decimal("0")

            for record in records:
                gross_regular = Decimal(str(record.get("gross_regular", 0)))
                gross_overtime = Decimal(str(record.get("gross_overtime", 0)))
                vac_pay = Decimal(str(record.get("vacation_pay_paid", 0)))

                if include_overtime:
                    total_wages += gross_regular + gross_overtime
                else:
                    total_wages += gross_regular
                vacation_pay += vac_pay

            logger.debug(
                "4-week earnings for %s: wages=$%.2f (overtime %s), vacation=$%.2f (%d records)",
                employee_id,
                float(total_wages),
                "included" if include_overtime else "excluded",
                float(vacation_pay),
                len(records),
            )

            return total_wages, vacation_pay

        except Exception as e:
            logger.error("Failed to query 4-week earnings: %s", e)
            return Decimal("0"), Decimal("0")

    def _get_4_week_earnings_from_timesheet(
        self,
        employee_id: str,
        holiday_date: date,
        hourly_rate: Decimal,
        include_overtime: bool = False,
    ) -> Decimal:
        """Calculate wages earned from timesheet_entries for 4-week period.

        This method is used for Alberta's "4_week_average_daily" formula.
        It calculates "wages earned" (based on hours worked) rather than
        "wages paid" (from payroll_records), which is important for:
        - New employees with incomplete payroll history
        - Correct calculation of average daily wage

        Formula: sum(regular_hours [+ overtime_hours if included]) × hourly_rate

        Args:
            employee_id: Employee ID
            holiday_date: Holiday date (calculation period ends day before)
            hourly_rate: Employee's hourly rate for wage calculation
            include_overtime: Whether to include overtime hours (default: False)

        Returns:
            Total wages earned in the 4-week period as Decimal
        """
        # 4-week window: 28 days before holiday, ending day before holiday
        start_date = holiday_date - timedelta(days=28)
        end_date = holiday_date - timedelta(days=1)

        try:
            result = self.supabase.table("timesheet_entries").select(
                "regular_hours, overtime_hours"
            ).eq(
                "employee_id", employee_id
            ).gte(
                "work_date", start_date.isoformat()
            ).lte(
                "work_date", end_date.isoformat()
            ).execute()

            total_hours = Decimal("0")
            for entry in result.data or []:
                regular = Decimal(str(entry.get("regular_hours", 0) or 0))
                overtime = Decimal(str(entry.get("overtime_hours", 0) or 0))
                if include_overtime:
                    total_hours += regular + overtime
                else:
                    total_hours += regular

            total_wages = total_hours * hourly_rate

            logger.info(
                "4-week earnings from timesheet for %s: period=%s to %s, total_hours=%.2f, "
                "hourly_rate=$%.2f, total_wages=$%.2f, overtime %s",
                employee_id, start_date, end_date, float(total_hours),
                float(hourly_rate), float(total_wages),
                "included" if include_overtime else "excluded"
            )

            return total_wages

        except Exception as e:
            logger.error("Failed to query 4-week earnings from timesheet for employee %s: %s", employee_id, e)
            return Decimal("0")

    def _get_28_day_earnings(
        self,
        employee_id: str,
        before_date: date,
        current_run_id: str,
        lookback_days: int = 28,
    ) -> tuple[Decimal, Decimal, Decimal]:
        """Query past N days payroll records for Saskatchewan/Manitoba formula.

        Args:
            employee_id: Employee ID
            before_date: Date to look back from (typically the holiday date)
            current_run_id: Current run ID to exclude from query
            lookback_days: Number of days to look back (default: 28 for SK/MB)

        Returns:
            Tuple of (regular_wages, vacation_pay, holiday_pay)
            Note: Does NOT include overtime wages (per Saskatchewan SEA)
        """
        start_date = before_date - timedelta(days=lookback_days)

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
        lookback_days: int = 28,
    ) -> Decimal:
        """Apply Saskatchewan-style 5% formula.

        Formula: percentage × (wages in past N days)
        Includes: regular wages, optionally vacation pay and previous holiday pay
        Excludes: overtime (per Saskatchewan Employment Act)

        For new employees with no historical data, behavior is config-driven:
        - "pro_rated": Use current period gross as base (SK, ON)
        - "ineligible": Return $0 (BC, AB, etc.)

        Reference: Saskatchewan Holiday Pay Calculator
        https://apps.saskatchewan.ca/lrws/calculator/holidaypay/

        Args:
            employee_id: Employee ID
            holiday_date: The holiday date (for lookback)
            current_run_id: Current run ID to exclude from queries
            percentage: Percentage to apply (e.g., 0.05 for 5%)
            include_vacation_pay: Whether to include vacation pay in base
            include_previous_holiday_pay: Whether to include previous holiday pay in base
            current_period_gross: Current period gross pay (for new employees)
            new_employee_fallback: Config-driven fallback for new employees
            lookback_days: Number of days to look back (default: 28 for SK/MB)

        Returns:
            Holiday pay amount as Decimal
        """
        regular_wages, vacation_pay, previous_holiday_pay = self._get_28_day_earnings(
            employee_id=employee_id,
            before_date=holiday_date,
            current_run_id=current_run_id,
            lookback_days=lookback_days,
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

        Basic formula: hours_worked × hourly_rate × premium_rate

        For provinces with tiered rates (e.g., BC requires 2x after 12 hours),
        the calculation splits hours across tiers:
        - First N hours at base premium_rate
        - Hours beyond threshold at higher tier rate

        Example BC (12-hour threshold):
        - 10 hours worked: 10 × rate × 1.5 = $150 (if rate=$10)
        - 14 hours worked: 12 × rate × 1.5 + 2 × rate × 2.0 = $220

        Args:
            employee: Employee data dict
            hours_worked: Number of hours worked on the holiday
            config: HolidayPayConfig for the province

        Returns:
            Premium pay as Decimal
        """
        hourly_rate = GrossCalculator.calculate_hourly_rate(employee)

        # If no tiered rates, use simple flat calculation
        if not config.premium_rate_tiers:
            premium_rate = config.premium_rate
            premium_pay = hours_worked * hourly_rate * premium_rate

            logger.debug(
                "Premium pay (flat rate): %.2f hours × $%.2f × %.2f = $%.2f",
                float(hours_worked),
                float(hourly_rate),
                float(premium_rate),
                float(premium_pay),
            )

            return premium_pay

        # Tiered calculation: apply different rates based on hour thresholds
        # Sort tiers by threshold (ascending) to process from lowest to highest
        sorted_tiers = sorted(
            config.premium_rate_tiers,
            key=lambda t: t.hours_threshold
        )

        premium_pay = Decimal("0")
        remaining_hours = hours_worked
        previous_threshold = Decimal("0")
        tier_details: list[str] = []

        # First, apply base premium rate up to the first tier threshold
        first_tier_threshold = sorted_tiers[0].hours_threshold if sorted_tiers else hours_worked

        if remaining_hours > Decimal("0"):
            # Hours below first tier threshold get base rate
            base_hours = min(remaining_hours, first_tier_threshold)
            if base_hours > Decimal("0"):
                base_pay = base_hours * hourly_rate * config.premium_rate
                premium_pay += base_pay
                remaining_hours -= base_hours
                tier_details.append(
                    f"{float(base_hours):.2f}h × ${float(hourly_rate):.2f} × {float(config.premium_rate):.2f}"
                )
            previous_threshold = first_tier_threshold

        # Apply each tier's rate to hours in that tier's range
        for i, tier in enumerate(sorted_tiers):
            if remaining_hours <= Decimal("0"):
                break

            # Determine hours in this tier
            # Next threshold is the next tier's threshold, or infinity for the last tier
            if i + 1 < len(sorted_tiers):
                next_threshold = sorted_tiers[i + 1].hours_threshold
                tier_hours = min(remaining_hours, next_threshold - tier.hours_threshold)
            else:
                # Last tier: all remaining hours
                tier_hours = remaining_hours

            if tier_hours > Decimal("0"):
                tier_pay = tier_hours * hourly_rate * tier.rate
                premium_pay += tier_pay
                remaining_hours -= tier_hours
                tier_details.append(
                    f"{float(tier_hours):.2f}h × ${float(hourly_rate):.2f} × {float(tier.rate):.2f}"
                )

        logger.debug(
            "Premium pay (tiered): %.2f hours total, breakdown: [%s] = $%.2f",
            float(hours_worked),
            " + ".join(tier_details),
            float(premium_pay),
        )

        return premium_pay
