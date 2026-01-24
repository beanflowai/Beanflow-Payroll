"""Holiday Pay Eligibility Checking.

Provides methods to check employee eligibility for holiday pay based on
provincial rules (employment duration, last/first rule, etc.).
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from dateutil.relativedelta import relativedelta

from app.models.holiday_pay_config import HolidayPayConfig
from app.services.payroll_run.holiday_pay.work_day_tracker import WorkDayTracker

logger = logging.getLogger(__name__)


class EligibilityChecker:
    """Checks employee eligibility for holiday pay.

    Provides methods to:
    - Check overall eligibility based on config rules
    - Get ineligibility reasons for reporting
    - Check last/first rule (work before and after holiday)
    """

    def __init__(self, supabase: Any, work_day_tracker: WorkDayTracker):
        """Initialize eligibility checker.

        Args:
            supabase: Supabase client instance
            work_day_tracker: WorkDayTracker instance for work day queries
        """
        self.supabase = supabase
        self.work_day_tracker = work_day_tracker

    def is_eligible_for_holiday_pay(
        self,
        employee: dict[str, Any],
        holiday_date: date,
        config: HolidayPayConfig,
        timesheet_entries: list[dict[str, Any]] | None = None,
    ) -> bool:
        """Check if employee is eligible for holiday pay based on config.

        Eligibility rules are loaded from configuration:
        - min_employment_days: Minimum days of employment required
        - require_last_first_rule: Must work last shift before and first shift after
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
            logger.warning(
                "Employee %s missing hire_date, marking ineligible",
                employee.get("id"),
            )
            return False

        try:
            hire_date = date.fromisoformat(hire_date_str)
        except (ValueError, TypeError):
            logger.warning(
                "Employee %s has invalid hire_date: %s",
                employee.get("id"),
                hire_date_str,
            )
            return False

        min_days = config.eligibility.min_employment_days

        if config.eligibility.count_work_days:
            # Alberta-style: count actual work days in the eligibility period
            period_months = config.eligibility.eligibility_period_months or 12
            period_start = holiday_date - relativedelta(months=period_months)
            work_days = self.work_day_tracker.count_work_days_for_eligibility(
                employee.get("id"), period_start, holiday_date
            )
            if work_days < min_days:
                logger.debug(
                    "Employee %s failed work days eligibility: %d < %d",
                    employee.get("id"), work_days, min_days
                )
                return False
        else:
            # Standard calendar days since hire
            days_employed = (holiday_date - hire_date).days
            if days_employed < min_days:
                return False

        # Check last/first rule
        if config.eligibility.require_last_first_rule:
            max_search_days = config.formula_params.last_first_window_days or 28
            strict_mode = True

            if timesheet_entries is not None:
                worked_before, worked_after = self.check_last_first_rule_from_entries(
                    timesheet_entries, holiday_date, strict_mode=strict_mode
                )
            else:
                worked_before, worked_after, _, _ = (
                    self.check_last_first_rule_improved(
                        employee.get("id"),
                        holiday_date,
                        max_search_days=max_search_days,
                        strict_mode=strict_mode,
                    )
                )
            if not (worked_before and worked_after):
                logger.debug(
                    "Employee %s failed last/first rule: before=%s, after=%s",
                    employee.get("id"),
                    worked_before,
                    worked_after,
                )
                return False

        # Check min_days_worked_in_period (PE requires 15 days in 30-day period)
        min_days_worked = config.eligibility.min_days_worked_in_period
        if min_days_worked is not None and timesheet_entries is not None:
            days_worked = self.work_day_tracker.count_days_worked_in_period(
                timesheet_entries,
                holiday_date - timedelta(days=30),
                holiday_date,
                employee_id=employee.get("id"),
            )
            if days_worked < min_days_worked:
                logger.debug(
                    "Employee %s failed min_days_worked: %d < %d",
                    employee.get("id"),
                    days_worked,
                    min_days_worked,
                )
                return False

        return True

    def get_ineligibility_reason(
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
            timesheet_entries: Optional timesheet entries

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

        if config.eligibility.count_work_days:
            period_months = config.eligibility.eligibility_period_months or 12
            period_start = holiday_date - relativedelta(months=period_months)
            work_days = self.work_day_tracker.count_work_days_for_eligibility(
                employee.get("id"), period_start, holiday_date
            )
            if work_days < min_days:
                return f"< {min_days} work days in past {period_months} months ({work_days} work days)"
        else:
            days_employed = (holiday_date - hire_date).days
            if days_employed < min_days:
                return f"< {min_days} days employed ({days_employed} days)"

        if config.eligibility.require_last_first_rule:
            max_search_days = config.formula_params.last_first_window_days or 28
            strict_mode = True

            if timesheet_entries is not None:
                worked_before, worked_after = self.check_last_first_rule_from_entries(
                    timesheet_entries, holiday_date, strict_mode=strict_mode
                )
            else:
                worked_before, worked_after, _, _ = (
                    self.check_last_first_rule_improved(
                        employee.get("id"),
                        holiday_date,
                        max_search_days=max_search_days,
                        strict_mode=strict_mode,
                    )
                )
            if not (worked_before and worked_after):
                return "did not work on last scheduled day before/first scheduled day after holiday"

        min_days_worked = config.eligibility.min_days_worked_in_period
        if min_days_worked is not None and timesheet_entries is not None:
            days_worked = self.work_day_tracker.count_days_worked_in_period(
                timesheet_entries,
                holiday_date - timedelta(days=30),
                holiday_date,
                employee_id=employee.get("id"),
            )
            if days_worked < min_days_worked:
                return f"only {days_worked} days worked in 30-day period (need {min_days_worked})"

        return "unknown"

    def check_last_first_rule_from_entries(
        self,
        timesheet_entries: list[dict[str, Any]],
        holiday_date: date,
        strict_mode: bool = True,
    ) -> tuple[bool, bool]:
        """Check last/first rule using passed timesheet entries.

        Per Alberta/Ontario/PEI Employment Standards:
        - Employee must work on their LAST scheduled day before the holiday
        - Employee must work on their FIRST scheduled day after the holiday

        Args:
            timesheet_entries: List of timesheet entry dictionaries
            holiday_date: The holiday date
            strict_mode: If True, no data = ineligible (fail-closed)

        Returns:
            Tuple of (worked_on_last_scheduled_day, worked_on_first_scheduled_day)
        """
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

        last_scheduled_before = max(work_dates_before) if work_dates_before else None
        first_scheduled_after = min(work_dates_after) if work_dates_after else None

        if last_scheduled_before is None and first_scheduled_after is None:
            if strict_mode:
                logger.debug(
                    "Last/first rule: No work history for holiday %s, ineligible",
                    holiday_date,
                )
                return False, False
            else:
                return True, True

        worked_before = last_scheduled_before is not None
        worked_after = first_scheduled_after is not None

        logger.debug(
            "Last/first rule: holiday=%s, last=%s, first=%s",
            holiday_date, last_scheduled_before, first_scheduled_after,
        )

        return worked_before, worked_after

    def check_last_first_rule_improved(
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

        Args:
            employee_id: Employee ID
            holiday_date: The holiday date
            max_search_days: Maximum days to search before/after holiday
            strict_mode: If True, no data = ineligible

        Returns:
            Tuple of (worked_before, worked_after, last_scheduled_day, first_scheduled_day)
        """
        last_scheduled_day = self.work_day_tracker.find_nearest_work_day(
            employee_id, holiday_date, direction="before", max_days=max_search_days
        )
        first_scheduled_day = self.work_day_tracker.find_nearest_work_day(
            employee_id, holiday_date, direction="after", max_days=max_search_days
        )

        if last_scheduled_day is None and first_scheduled_day is None:
            if strict_mode:
                logger.debug(
                    "No scheduled work days for %s within %d days, ineligible",
                    employee_id, max_search_days,
                )
                return False, False, None, None
            else:
                return True, True, None, None

        worked_before = not strict_mode
        worked_after = not strict_mode

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
                logger.warning("Failed to check last scheduled day: %s", e)
                worked_before = not strict_mode

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
                logger.warning("Failed to check first scheduled day: %s", e)
                worked_after = not strict_mode

        logger.debug(
            "Last/first rule: last=%s (worked=%s), first=%s (worked=%s)",
            last_scheduled_day, worked_before, first_scheduled_day, worked_after,
        )

        return worked_before, worked_after, last_scheduled_day, first_scheduled_day
