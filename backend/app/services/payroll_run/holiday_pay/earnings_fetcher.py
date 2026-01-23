"""Historical Earnings Fetcher for Holiday Pay.

Provides methods to query historical payroll records and timesheet entries
for holiday pay calculations.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from app.services.payroll_run.constants import COMPLETED_RUN_STATUSES

logger = logging.getLogger(__name__)


class EarningsFetcher:
    """Fetches historical earnings for holiday pay calculations.

    Provides methods to:
    - Get earnings from payroll records (4-week, 28-day)
    - Get wages from timesheet entries
    """

    def __init__(self, supabase: Any):
        """Initialize earnings fetcher.

        Args:
            supabase: Supabase client instance
        """
        self.supabase = supabase

    def get_wages_from_timesheet(
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

            regular_wages = total_regular_hours * hourly_rate
            overtime_wages = total_overtime_hours * hourly_rate * overtime_multiplier

            return regular_wages + overtime_wages

        except Exception as e:
            logger.warning(
                "Failed to get wages from timesheet for employee %s: %s",
                employee_id, e
            )
            return Decimal("0")

    def get_4_week_earnings(
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
            include_overtime: Whether to include overtime in total wages

        Returns:
            Tuple of (total_wages, vacation_pay)
        """
        start_date = before_date - timedelta(days=28)

        try:
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

            logger.info(
                "4-week earnings query for %s: start=%s, before=%s, records=%d",
                employee_id, start_date, before_date, len(records)
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
                "4-week earnings for %s: wages=$%.2f, vacation=$%.2f",
                employee_id, float(total_wages), float(vacation_pay),
            )

            return total_wages, vacation_pay

        except Exception as e:
            logger.error("Failed to query 4-week earnings: %s", e)
            return Decimal("0"), Decimal("0")

    def get_4_week_earnings_from_timesheet(
        self,
        employee_id: str,
        holiday_date: date,
        hourly_rate: Decimal,
        include_overtime: bool = False,
    ) -> Decimal:
        """Calculate wages earned from timesheet_entries for 4-week period.

        Used for Alberta's "4_week_average_daily" formula.

        Args:
            employee_id: Employee ID
            holiday_date: Holiday date (calculation period ends day before)
            hourly_rate: Employee's hourly rate for wage calculation
            include_overtime: Whether to include overtime hours

        Returns:
            Total wages earned in the 4-week period as Decimal
        """
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
                "4-week earnings from timesheet for %s: period=%s to %s, "
                "total_hours=%.2f, wages=$%.2f",
                employee_id, start_date, end_date,
                float(total_hours), float(total_wages)
            )

            return total_wages

        except Exception as e:
            logger.error("Failed to query 4-week earnings from timesheet: %s", e)
            return Decimal("0")

    def get_28_day_earnings(
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
            lookback_days: Number of days to look back (default: 28)

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
                "28-day earnings for %s: wages=$%.2f, vacation=$%.2f, holiday=$%.2f",
                employee_id, float(regular_wages), float(vacation_pay), float(holiday_pay),
            )

            return regular_wages, vacation_pay, holiday_pay

        except Exception as e:
            logger.error("Failed to query 28-day earnings: %s", e)
            return Decimal("0"), Decimal("0"), Decimal("0")
