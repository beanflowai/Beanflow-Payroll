"""Work Day Tracking for Holiday Pay.

Provides methods to track and count work days for holiday pay calculations.
"""

from __future__ import annotations

import logging
from collections import Counter
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from app.models.holiday_pay_config import HolidayPayConfig

logger = logging.getLogger(__name__)


class WorkDayTracker:
    """Tracks work days for holiday pay eligibility and calculations.

    Provides methods to:
    - Check if employee worked in a date range
    - Count days worked in a period
    - Calculate normal daily hours
    - Find nearest work days (for last/first rule)
    - Check Alberta's "5 of 9" rule for regular work days
    """

    def __init__(self, supabase: Any):
        """Initialize work day tracker.

        Args:
            supabase: Supabase client instance
        """
        self.supabase = supabase

    def has_work_in_range(
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

    def count_days_worked_in_period(
        self,
        entries: list[dict[str, Any]],
        start_date: date,
        end_date: date,
        employee_id: str | None = None,
    ) -> int:
        """Count unique days entitled to wages in date range.

        Used for BC/NS/PE "15 of 30 days" eligibility rule.

        Per official rules (BC ESA, NS LSC, PEI ESA), this counts days
        "entitled to wages" which includes:
        - Days actually worked (from timesheet entries)
        - Paid sick leave days (from sick_leave_usage_history)

        Note: Paid vacation days are not yet tracked at the day level,
        so they are not included in this count.

        Args:
            entries: List of timesheet entries
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            employee_id: Optional employee ID to query paid leave days

        Returns:
            Number of unique days entitled to wages
        """
        days_with_wages: set[date] = set()

        # Count days with work hours from timesheet
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
                    days_with_wages.add(work_date)

        # Count paid sick leave days
        if employee_id:
            paid_leave_days = self._get_paid_leave_days(employee_id, start_date, end_date)
            days_with_wages.update(paid_leave_days)

        return len(days_with_wages)

    def _get_paid_leave_days(
        self,
        employee_id: str,
        start_date: date,
        end_date: date,
    ) -> set[date]:
        """Get dates of paid leave (sick leave) for an employee.

        Queries sick_leave_usage_history for paid sick leave days.

        Args:
            employee_id: Employee ID
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)

        Returns:
            Set of dates with paid leave
        """
        paid_leave_dates: set[date] = set()

        try:
            result = self.supabase.table("sick_leave_usage_history").select(
                "usage_date"
            ).eq(
                "employee_id", employee_id
            ).eq(
                "is_paid", True
            ).gte(
                "usage_date", start_date.isoformat()
            ).lte(
                "usage_date", end_date.isoformat()
            ).execute()

            for record in result.data or []:
                usage_date_str = record.get("usage_date")
                if usage_date_str:
                    try:
                        paid_leave_dates.add(date.fromisoformat(usage_date_str))
                    except (ValueError, TypeError):
                        continue

            if paid_leave_dates:
                logger.debug(
                    "Found %d paid sick leave days for employee %s in range %s to %s",
                    len(paid_leave_dates), employee_id, start_date, end_date
                )

        except Exception as e:
            logger.warning("Failed to query paid leave days for %s: %s", employee_id, e)

        return paid_leave_dates

    def get_normal_daily_hours(
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

        For salaried employees: Use default_daily_hours from config.

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
                    "Normal daily hours for hourly employee %s: %.2f (no data)",
                    employee.get("id"),
                    float(default_hours),
                )
                return default_hours

            # Calculate total hours per work day (aggregate by date)
            hours_by_date: dict[str, Decimal] = {}
            for entry in entries:
                work_date_str = entry.get("work_date", "")
                regular = Decimal(str(entry.get("regular_hours", 0) or 0))
                # Only count regular hours for "normal" day
                if regular > 0:
                    if work_date_str not in hours_by_date:
                        hours_by_date[work_date_str] = Decimal("0")
                    hours_by_date[work_date_str] += regular

            if not hours_by_date:
                return default_hours

            # Find the mode (most common daily hours)
            rounded_hours = [
                float(round(h * 2) / 2) for h in hours_by_date.values()
            ]
            if not rounded_hours:
                return default_hours

            hour_counts = Counter(rounded_hours)
            most_common_hours = hour_counts.most_common(1)[0][0]
            normal_hours = Decimal(str(most_common_hours))

            logger.debug(
                "Normal daily hours for hourly employee %s: %.2f (from %d work days)",
                employee.get("id"),
                float(normal_hours),
                len(hours_by_date),
            )

            return normal_hours

        except Exception as e:
            logger.warning(
                "Failed to calculate normal daily hours for employee %s: %s",
                employee.get("id"),
                e,
            )
            return default_hours

    def count_work_days_for_eligibility(
        self,
        employee_id: str,
        start_date: date,
        end_date: date,
    ) -> int:
        """Count unique days with work in date range for eligibility check.

        Queries the database directly. Used for Alberta-style work day eligibility.

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
                "Work days eligibility: employee=%s, period=%s to %s, work_days=%d",
                employee_id, start_date, end_date, work_days_count
            )
            return work_days_count

        except Exception as e:
            logger.warning(
                "Failed to count work days for employee %s: %s", employee_id, e
            )
            return 0

    def find_nearest_work_day(
        self,
        employee_id: str,
        holiday_date: date,
        direction: str,
        max_days: int = 28,
    ) -> date | None:
        """Find the nearest scheduled work day before or after holiday.

        Implements Alberta's "last scheduled day before" and "first scheduled
        day after" rule by searching for the first day with actual work history.

        Args:
            employee_id: Employee ID
            holiday_date: The holiday date
            direction: "before" to search backward, "after" to search forward
            max_days: Maximum days to search (default 28 days)

        Returns:
            The nearest work day date, or None if not found
        """
        if direction == "before":
            start_date = holiday_date - timedelta(days=max_days)
            end_date = holiday_date - timedelta(days=1)
        else:
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

    def get_timesheet_entries_for_eligibility(
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
            return None

    def get_days_worked_in_4_weeks(
        self, employee_id: str, holiday_date: date
    ) -> int:
        """Query timesheet_entries to get actual days worked in 4-week period.

        Args:
            employee_id: Employee ID
            holiday_date: Holiday date (calculation period ends day before)

        Returns:
            Number of unique days with work hours > 0 in the 4-week period
        """
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
                "Days worked in 4-week period for %s: %d days",
                employee_id, count,
            )
            return count
        except Exception as e:
            logger.warning("Failed to query days worked: %s", e)
            return 20

    def is_regular_work_day_5_of_9(
        self,
        employee_id: str,
        holiday_date: date,
        hire_date: date | None,
        config: HolidayPayConfig | None = None,
    ) -> bool:
        """Check if holiday falls on a regular work day using Alberta's "5 of 9" rule.

        In the last N weeks before the holiday, if the employee has worked M times
        on the same day of week, it's a regular work day.

        Default values (configurable via formula_params):
        - weeks_before (alberta_5_of_9_weeks): 9
        - threshold (alberta_5_of_9_threshold): 5

        Args:
            employee_id: Employee ID
            holiday_date: The holiday date
            hire_date: Employee's hire date (for new employee handling)
            config: Optional HolidayPayConfig for configurable parameters

        Returns:
            True if holiday is on a regular work day, False otherwise
        """
        holiday_dow = holiday_date.weekday()

        weeks_before = 9
        base_threshold = 5

        if config and config.formula_params:
            weeks_before = config.formula_params.alberta_5_of_9_weeks or 9
            base_threshold = config.formula_params.alberta_5_of_9_threshold or 5

        start_of_week = holiday_date - timedelta(days=(holiday_date.weekday() + 1) % 7)
        start_date = start_of_week - timedelta(weeks=weeks_before)
        end_date = holiday_date - timedelta(days=1)

        threshold = base_threshold
        if hire_date and hire_date > start_date:
            days_employed = (holiday_date - hire_date).days
            weeks_employed = max(0, days_employed // 7)
            if weeks_employed < weeks_before:
                threshold = max(1, int(weeks_employed * base_threshold / weeks_before))
                start_date = hire_date

        try:
            result = self.supabase.table("timesheet_entries").select(
                "work_date, regular_hours, overtime_hours"
            ).eq("employee_id", employee_id).gte(
                "work_date", start_date.isoformat()
            ).lte("work_date", end_date.isoformat()).execute()

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
                "5 of 9 rule: employee=%s, holiday=%s (%s), count=%d, threshold=%d, is_regular=%s",
                employee_id, holiday_date, holiday_date.strftime("%A"),
                count, threshold, is_regular
            )

            return is_regular
        except Exception as e:
            # Fail-open: assume it IS a regular work day if query fails
            # This prevents penalizing employees due to system errors
            logger.warning(
                "Failed to check 5 of 9 rule for employee %s: %s. "
                "Assuming regular work day (fail-open).",
                employee_id, e
            )
            return True
