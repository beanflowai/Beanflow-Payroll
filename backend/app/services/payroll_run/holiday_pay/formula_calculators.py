"""Holiday Pay Formula Calculators.

Implements various provincial formulas for calculating regular holiday pay.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from app.services.payroll_run.constants import COMPLETED_RUN_STATUSES
from app.services.payroll_run.gross_calculator import GrossCalculator
from app.services.payroll_run.holiday_pay.earnings_fetcher import EarningsFetcher
from app.services.payroll_run.holiday_pay.work_day_tracker import WorkDayTracker

logger = logging.getLogger(__name__)

# Work days per pay period (for Alberta formula)
WORK_DAYS_PER_PERIOD = {
    "weekly": Decimal("5"),
    "bi_weekly": Decimal("10"),
    "semi_monthly": Decimal("10.83"),
    "monthly": Decimal("21.67"),
}


class FormulaCalculators:
    """Calculates regular holiday pay using provincial formulas.

    Supports multiple formula types:
    - 4_week_average: (past 4 weeks wages + vacation pay) / divisor (ON, Federal, QC)
    - 30_day_average: Average daily pay based on 30 days (BC, NS, PE, NB, YT, NU)
    - 4_week_average_daily: Wages in 4 weeks / days worked (AB)
    - current_period_daily: Current period gross / work days in period
    - 5_percent_28_days: 5% of wages in past 28 days (SK, MB)
    - 3_week_average_nl: hourly_rate x (hours in 3 weeks / 15) (NL)
    - irregular_hours: percentage x wages in lookback weeks (YT irregular)
    - commission: 1/divisor of wages in lookback weeks (QC/Federal commission)
    """

    def __init__(
        self,
        supabase: Any,
        earnings_fetcher: EarningsFetcher,
        work_day_tracker: WorkDayTracker,
    ):
        """Initialize formula calculators.

        Args:
            supabase: Supabase client instance
            earnings_fetcher: EarningsFetcher instance for historical earnings
            work_day_tracker: WorkDayTracker instance for work day queries
        """
        self.supabase = supabase
        self.earnings_fetcher = earnings_fetcher
        self.work_day_tracker = work_day_tracker

    def apply_30_day_average(
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

        Official formula: total wages in 30 days / days with wages

        Methods:
        - "total_wages_div_days": Total wages / number of unique days with pay
        - "wages_div_days_worked": Wages / unique days actually worked
        - "hours_times_rate": (hours in period / divisor) x hourly_rate

        Args:
            employee_id: Employee ID
            employee: Employee data dict with hourly_rate
            holiday_date: The holiday date for lookback
            method: Calculation method from config
            include_overtime: Whether to include overtime in wages
            default_daily_hours: Fallback daily hours for new employees
            new_employee_fallback: How to handle new employees
            lookback_days: Number of days to look back (default: 30)

        Returns:
            One day's pay as Decimal
        """
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
                if new_employee_fallback == "pro_rated":
                    hourly_rate = GrossCalculator.calculate_hourly_rate(employee)
                    daily_pay = default_daily_hours * hourly_rate
                    logger.info(
                        "30-day avg: No data for %s, using pro_rated fallback: $%.2f",
                        employee_id, float(daily_pay)
                    )
                    return daily_pay
                else:
                    logger.info(
                        "30-day avg: No data for %s, returning $0", employee_id
                    )
                    return Decimal("0")

            hourly_rate = GrossCalculator.calculate_hourly_rate(employee)
            total_hours = Decimal("0")
            days_with_work: set[str] = set()

            for entry in entries:
                work_date_str = entry.get("work_date", "")
                regular = Decimal(str(entry.get("regular_hours", 0) or 0))
                overtime = Decimal(str(entry.get("overtime_hours", 0) or 0))

                if include_overtime:
                    entry_hours = regular + overtime
                else:
                    entry_hours = regular

                total_hours += entry_hours

                if regular > 0 or overtime > 0:
                    days_with_work.add(work_date_str)

            days_worked = len(days_with_work)

            if days_worked == 0:
                logger.warning(
                    "30-day avg: Employee %s has 0 days with hours", employee_id
                )
                return Decimal("0")

            if method == "hours_times_rate":
                avg_daily_hours = total_hours / Decimal(str(days_worked))
                daily_pay = avg_daily_hours * hourly_rate
            else:
                total_wages = total_hours * hourly_rate
                daily_pay = total_wages / Decimal(str(days_worked))

            logger.debug(
                "30-day avg: employee=%s, method=%s, daily_pay=$%.2f",
                employee_id, method, float(daily_pay)
            )

            return daily_pay

        except Exception as e:
            logger.error("Failed to calculate 30-day average: %s", e)
            hourly_rate = GrossCalculator.calculate_hourly_rate(employee)
            return default_daily_hours * hourly_rate

    def apply_current_period_daily(
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
            "Current period: $%.2f / %s days = $%.2f",
            float(current_period_gross), float(work_days), float(daily_pay),
        )

        return daily_pay

    def apply_3_week_average_nl(
        self,
        employee_id: str,
        employee: dict[str, Any],
        holiday_date: date,
        lookback_weeks: int,
        divisor: int,
        include_overtime: bool,
    ) -> Decimal:
        """Apply Newfoundland 3-week average formula.

        Official formula: hourly_rate x (hours in 3 weeks / 15)

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
                logger.info("NL 3-week avg: No data for %s", employee_id)
                return Decimal("0")

            total_hours = Decimal("0")
            for entry in entries:
                regular = Decimal(str(entry.get("regular_hours", 0) or 0))
                overtime = Decimal(str(entry.get("overtime_hours", 0) or 0))

                if include_overtime:
                    total_hours += regular + overtime
                else:
                    total_hours += regular

            hourly_rate = GrossCalculator.calculate_hourly_rate(employee)
            daily_pay = hourly_rate * (total_hours / Decimal(str(divisor)))

            logger.debug(
                "NL 3-week avg: employee=%s, hours=%.2f, daily_pay=$%.2f",
                employee_id, float(total_hours), float(daily_pay)
            )

            return daily_pay

        except Exception as e:
            logger.error("Failed to calculate NL 3-week average: %s", e)
            return Decimal("0")

    def apply_irregular_hours(
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

        Formula: percentage x total wages in lookback_weeks

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
        start_date = holiday_date - timedelta(weeks=lookback_weeks)
        end_date = holiday_date - timedelta(days=1)

        try:
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
                # Try timesheet-based calculation
                hourly_rate = GrossCalculator.calculate_hourly_rate(employee)
                wages_from_timesheet = self.earnings_fetcher.get_wages_from_timesheet(
                    employee_id, start_date, end_date, hourly_rate, include_overtime
                )
                if wages_from_timesheet > Decimal("0"):
                    holiday_pay = wages_from_timesheet * percentage
                    logger.info(
                        "Irregular hours (timesheet): %s, wages=$%.2f x %.1f%% = $%.2f",
                        employee_id, float(wages_from_timesheet),
                        float(percentage * 100), float(holiday_pay)
                    )
                    return holiday_pay

                logger.info("Irregular hours: No data for %s", employee_id)
                return Decimal("0")

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
                "Irregular hours: %s, wages=$%.2f x %.1f%% = $%.2f",
                employee_id, float(total_wages), float(percentage * 100), float(holiday_pay)
            )

            return holiday_pay

        except Exception as e:
            logger.error("Failed to calculate irregular hours: %s", e)
            return Decimal("0")

    def apply_commission(
        self,
        employee_id: str,
        holiday_date: date,
        current_run_id: str,
        divisor: int,
        lookback_weeks: int,
    ) -> Decimal:
        """Apply commission employee formula.

        Formula: total wages in lookback_weeks / divisor

        Args:
            employee_id: Employee ID
            holiday_date: The holiday date for lookback
            current_run_id: Current run ID to exclude from queries
            divisor: The divisor (e.g., 60 for 1/60)
            lookback_weeks: Number of weeks to look back (e.g., 12)

        Returns:
            Holiday pay amount as Decimal
        """
        start_date = holiday_date - timedelta(weeks=lookback_weeks)
        end_date = holiday_date - timedelta(days=1)

        try:
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
                logger.info("Commission: No data for %s", employee_id)
                return Decimal("0")

            total_wages = Decimal("0")
            for record in records:
                gross_regular = Decimal(str(record.get("gross_regular", 0)))
                commission = Decimal(str(record.get("commission_pay", 0) or 0))
                total_wages += gross_regular + commission

            holiday_pay = total_wages / Decimal(str(divisor))

            logger.debug(
                "Commission: %s, wages=$%.2f / %d = $%.2f",
                employee_id, float(total_wages), divisor, float(holiday_pay)
            )

            return holiday_pay

        except Exception as e:
            logger.error("Failed to calculate commission: %s", e)
            return Decimal("0")

    def apply_4_week_average(
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
        total_wages, vacation_pay = self.earnings_fetcher.get_4_week_earnings(
            employee_id=employee_id,
            before_date=holiday_date,
            current_run_id=current_run_id,
            include_overtime=include_overtime,
        )

        if total_wages == Decimal("0"):
            if new_employee_fallback == "pro_rated":
                logger.info("4-week avg: No data for %s, using pro_rated", employee_id)
                hourly_rate = GrossCalculator.calculate_hourly_rate(employee_fallback)
                return Decimal("8") * hourly_rate
            else:
                logger.info("4-week avg: No data for %s, returning $0", employee_id)
                return Decimal("0")

        if include_vacation_pay:
            daily_pay = (total_wages + vacation_pay) / Decimal(str(divisor))
        else:
            daily_pay = total_wages / Decimal(str(divisor))

        logger.debug(
            "4-week avg: ($%.2f + $%.2f) / %d = $%.2f",
            float(total_wages),
            float(vacation_pay) if include_vacation_pay else 0,
            divisor,
            float(daily_pay),
        )

        return daily_pay

    def apply_4_week_daily(
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
        hourly_rate = GrossCalculator.calculate_hourly_rate(employee_fallback)

        total_wages = self.earnings_fetcher.get_4_week_earnings_from_timesheet(
            employee_id=employee_id,
            holiday_date=holiday_date,
            hourly_rate=hourly_rate,
            include_overtime=include_overtime,
        )

        if total_wages == Decimal("0"):
            if new_employee_fallback == "pro_rated":
                logger.info("4-week daily: No data for %s, using pro_rated", employee_id)
                return Decimal("8") * hourly_rate
            else:
                logger.info("4-week daily: No data for %s, returning $0", employee_id)
                return Decimal("0")

        days_worked_int = self.work_day_tracker.get_days_worked_in_4_weeks(
            employee_id, holiday_date
        )

        if days_worked_int == 0:
            days_worked_int = 20

        days_worked = Decimal(str(days_worked_int))
        daily_pay = total_wages / days_worked

        logger.info(
            "4-week daily: %s, wages=$%.2f / %d days = $%.2f",
            employee_id, float(total_wages), days_worked_int, float(daily_pay)
        )

        return daily_pay

    def apply_5_percent_28_days(
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

        Formula: percentage x (wages in past N days)

        Args:
            employee_id: Employee ID
            holiday_date: The holiday date (for lookback)
            current_run_id: Current run ID to exclude from queries
            percentage: Percentage to apply (e.g., 0.05 for 5%)
            include_vacation_pay: Whether to include vacation pay in base
            include_previous_holiday_pay: Whether to include previous holiday pay
            current_period_gross: Current period gross pay (for new employees)
            new_employee_fallback: Config-driven fallback for new employees
            lookback_days: Number of days to look back (default: 28)

        Returns:
            Holiday pay amount as Decimal
        """
        regular_wages, vacation_pay, previous_holiday_pay = (
            self.earnings_fetcher.get_28_day_earnings(
                employee_id=employee_id,
                before_date=holiday_date,
                current_run_id=current_run_id,
                lookback_days=lookback_days,
            )
        )

        base = regular_wages
        if include_vacation_pay:
            base += vacation_pay
        if include_previous_holiday_pay:
            base += previous_holiday_pay

        if base == Decimal("0"):
            if new_employee_fallback == "pro_rated" and current_period_gross > Decimal("0"):
                base = current_period_gross
                logger.info(
                    "5%% 28-day: No data for %s, using current gross $%.2f",
                    employee_id, float(current_period_gross),
                )
            else:
                logger.info("5%% 28-day: No data for %s, returning $0", employee_id)
                return Decimal("0")

        holiday_pay = base * percentage

        logger.debug(
            "5%% 28-day: $%.2f x %.1f%% = $%.2f",
            float(base), float(percentage * 100), float(holiday_pay),
        )

        return holiday_pay
