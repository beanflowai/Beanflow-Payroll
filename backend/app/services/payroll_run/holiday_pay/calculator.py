"""Holiday Pay Calculator - Main Orchestrator.

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
from app.services.payroll_run.gross_calculator import GrossCalculator
from app.services.payroll_run.holiday_pay.earnings_fetcher import EarningsFetcher
from app.services.payroll_run.holiday_pay.eligibility_checker import EligibilityChecker
from app.services.payroll_run.holiday_pay.formula_calculators import FormulaCalculators
from app.services.payroll_run.holiday_pay.work_day_tracker import WorkDayTracker

logger = logging.getLogger(__name__)


class HolidayPayResult(NamedTuple):
    """Result of holiday pay calculation."""

    regular_holiday_pay: Decimal
    premium_holiday_pay: Decimal
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

        # Initialize helper components
        self.work_day_tracker = WorkDayTracker(supabase)
        self.earnings_fetcher = EarningsFetcher(supabase)
        self.eligibility_checker = EligibilityChecker(supabase, self.work_day_tracker)
        self.formula_calculators = FormulaCalculators(
            supabase, self.earnings_fetcher, self.work_day_tracker
        )

    def _get_config(self, province: str, pay_date: date | None = None) -> HolidayPayConfig:
        """Get holiday pay config for a province."""
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
        2. Premium Holiday Pay: For all employees who work on holidays

        Args:
            employee: Employee data dict
            province: Province code (ON, BC, AB, etc.)
            pay_frequency: Pay frequency string (weekly, bi_weekly, etc.)
            period_start: Pay period start date
            period_end: Pay period end date
            holidays_in_period: List of statutory holidays in the period
            holiday_work_entries: List of holiday work entries from input_data
            current_period_gross: Current period gross pay (regular + overtime)
            current_run_id: Current payroll run ID
            holiday_pay_exempt: If True, skip Regular Holiday Pay (HR override)

        Returns:
            HolidayPayResult with regular, premium, and total holiday pay
        """
        regular_holiday_pay = Decimal("0")
        premium_holiday_pay = Decimal("0")

        config = self._get_config(province, period_end)

        # Pre-compute compensation type for details
        emp_compensation_type = employee.get("compensation_type", "")

        details: dict[str, Any] = {
            "holidays_count": len(holidays_in_period),
            "holidays": [],
            "work_entries": [],
            "is_hourly": bool(employee.get("hourly_rate")),
            "compensation_type": emp_compensation_type,
            "province": province,
            "holiday_pay_exempt": holiday_pay_exempt,
            "config": {
                "formula_type": config.formula_type,
                "premium_rate": str(config.premium_rate),
                "min_employment_days": config.eligibility.min_employment_days,
                "require_last_first_rule": config.eligibility.require_last_first_rule,
            },
        }

        if not holidays_in_period:
            return HolidayPayResult(
                regular_holiday_pay=Decimal("0"),
                premium_holiday_pay=Decimal("0"),
                total_holiday_pay=Decimal("0"),
                calculation_details=details,
            )

        # Determine if employee is hourly or salaried
        # Use compensation_type as source of truth, fall back to hourly_rate check
        compensation_type = employee.get("compensation_type", "").lower()
        if compensation_type == "salary":
            # Design intent: Salaried employees' holiday pay is typically already
            # included in their annual salary, so regular holiday pay calculation
            # is skipped. However, if a salaried employee works on a holiday,
            # premium pay is still calculated.
            is_hourly = False
            logger.debug(
                "Employee %s %s is salaried (compensation_type=%s) - skipping regular holiday pay",
                employee.get("first_name"),
                employee.get("last_name"),
                compensation_type,
            )
        elif compensation_type == "hourly":
            is_hourly = True
        else:
            # Fallback: check hourly_rate field
            is_hourly = bool(employee.get("hourly_rate"))

        # Fetch timesheet entries for eligibility checks if needed
        timesheet_entries: list[dict[str, Any]] | None = None
        if (
            config.eligibility.require_last_first_rule
            or config.eligibility.min_days_worked_in_period is not None
        ):
            lookback_days = config.formula_params.eligibility_lookback_days or 30
            forward_days = config.formula_params.last_first_window_days or 28

            holiday_dates = []
            for h in holidays_in_period:
                try:
                    holiday_dates.append(date.fromisoformat(h.get("holiday_date", "")))
                except (ValueError, TypeError):
                    pass
            if holiday_dates:
                earliest = min(holiday_dates) - timedelta(days=lookback_days)
                latest = max(holiday_dates) + timedelta(days=forward_days)
                timesheet_entries = self.work_day_tracker.get_timesheet_entries_for_eligibility(
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
                "Processing holiday %s for %s %s (province=%s)",
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

            # Check "5 of 9" rule for Alberta
            is_regular_work_day = False
            checked_5_of_9_rule = False
            if config.eligibility.require_last_first_rule and province == "AB":
                hire_date = None
                try:
                    hire_date = date.fromisoformat(employee.get("hire_date")) if employee.get("hire_date") else None
                except (ValueError, TypeError):
                    hire_date = None
                is_regular_work_day = self.work_day_tracker.is_regular_work_day_5_of_9(
                    employee["id"], holiday_date, hire_date, config=config
                )
                checked_5_of_9_rule = True

            holiday_detail["is_regular_work_day"] = is_regular_work_day

            # Check eligibility
            if holiday_pay_exempt:
                is_eligible = False
                holiday_detail["eligible"] = False
                holiday_detail["exempt_by_hr"] = True
                logger.debug(
                    "Employee %s %s exempt from holiday pay (HR override)",
                    employee.get("first_name"),
                    employee.get("last_name"),
                )
            else:
                is_eligible = self.eligibility_checker.is_eligible_for_holiday_pay(
                    employee, holiday_date, config, timesheet_entries
                )
                holiday_detail["eligible"] = is_eligible

            if not is_eligible and not holiday_pay_exempt:
                reason = self.eligibility_checker.get_ineligibility_reason(
                    employee, holiday_date, config, timesheet_entries
                )
                logger.debug(
                    "Employee %s %s not eligible: %s",
                    employee.get("first_name"),
                    employee.get("last_name"),
                    reason,
                )
                holiday_detail["ineligibility_reason"] = reason
            elif is_eligible and is_hourly:
                hours_worked = hours_worked_by_date.get(holiday_date_str, Decimal("0"))

                # NL Special Rule: Full shift worked = 2x wages only
                nl_full_shift_worked = False
                expected_daily_hours = self.work_day_tracker.get_normal_daily_hours(
                    employee, config, holiday_date
                )
                if province == "NL" and hours_worked >= expected_daily_hours:
                    nl_full_shift_worked = True
                    daily_pay = Decimal("0")
                    logger.debug(
                        "NL s.17(a): Full shift on %s - 2x wages only",
                        holiday_name,
                    )
                elif checked_5_of_9_rule and not is_regular_work_day:
                    daily_pay = Decimal("0")
                    logger.debug(
                        "Holiday %s is NOT a regular work day (5 of 9): $0 regular pay",
                        holiday_name,
                    )
                else:
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

            # Calculate Premium Pay
            hours_worked = hours_worked_by_date.get(holiday_date_str, Decimal("0"))
            if hours_worked > 0:
                expected_daily_hours = self.work_day_tracker.get_normal_daily_hours(
                    employee, config, holiday_date
                )
                if province == "NL" and hours_worked < expected_daily_hours:
                    # NL partial shift: 1.0x rate
                    hourly_rate = GrossCalculator.calculate_hourly_rate(employee)
                    premium_pay = hours_worked * hourly_rate * Decimal("1.0")
                    holiday_detail["nl_rule"] = "s.17(2) partial shift - regular wages + holiday pay"
                elif not is_eligible and config.eligibility.premium_requires_eligibility:
                    # Ineligible employee working on holiday: regular rate only (1.0x)
                    # Per BC ESA and similar provincial standards, ineligible employees
                    # receive regular wages for hours worked, not premium pay.
                    # This is province-configurable via premium_requires_eligibility.
                    hourly_rate = GrossCalculator.calculate_hourly_rate(employee)
                    premium_pay = hours_worked * hourly_rate
                    holiday_detail["ineligible_premium"] = "regular rate only (1.0x)"
                    logger.debug(
                        "Ineligible employee %s %s working on %s: regular rate $%.2f "
                        "(premium_requires_eligibility=True)",
                        employee.get("first_name"),
                        employee.get("last_name"),
                        holiday_name,
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
        """Calculate one day's pay for Hourly employees using config-driven formula."""
        formula_type = config.formula_type
        params = config.formula_params

        match formula_type:
            case "4_week_average":
                return self.formula_calculators.apply_4_week_average(
                    employee_id=employee["id"],
                    holiday_date=holiday_date,
                    current_run_id=current_run_id,
                    divisor=params.divisor or 20,
                    include_vacation_pay=params.include_vacation_pay,
                    include_overtime=params.include_overtime,
                    employee_fallback=employee,
                    new_employee_fallback=params.new_employee_fallback,
                    default_daily_hours=params.default_daily_hours,
                )
            case "4_week_average_daily":
                return self.formula_calculators.apply_4_week_daily(
                    employee_id=employee["id"],
                    holiday_date=holiday_date,
                    current_run_id=current_run_id,
                    include_overtime=params.include_overtime,
                    employee_fallback=employee,
                    new_employee_fallback=params.new_employee_fallback,
                    default_daily_hours=params.default_daily_hours,
                )
            case "current_period_daily":
                return self.formula_calculators.apply_current_period_daily(
                    current_period_gross=current_period_gross,
                    pay_frequency=pay_frequency,
                )
            case "5_percent_28_days":
                return self.formula_calculators.apply_5_percent_28_days(
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
                return self.formula_calculators.apply_30_day_average(
                    employee_id=employee["id"],
                    employee=employee,
                    holiday_date=holiday_date,
                    method=params.method or "total_wages_div_days",
                    include_overtime=params.include_overtime,
                    default_daily_hours=params.default_daily_hours,
                    new_employee_fallback=params.new_employee_fallback,
                    lookback_days=params.lookback_days or 30,
                    percentage=params.percentage,
                    include_vacation_pay=params.include_vacation_pay,
                    include_previous_holiday_pay=params.include_previous_holiday_pay,
                    include_sick_pay=params.include_sick_pay,
                    current_run_id=current_run_id,
                )
            case "3_week_average_nl":
                return self.formula_calculators.apply_3_week_average_nl(
                    employee_id=employee["id"],
                    employee=employee,
                    holiday_date=holiday_date,
                    lookback_weeks=params.lookback_weeks_nl or 3,
                    divisor=params.nl_divisor or 15,
                    include_overtime=params.include_overtime,
                )
            case "irregular_hours":
                return self.formula_calculators.apply_irregular_hours(
                    employee_id=employee["id"],
                    employee=employee,
                    holiday_date=holiday_date,
                    current_run_id=current_run_id,
                    percentage=params.irregular_hours_percentage or Decimal("0.10"),
                    lookback_weeks=params.irregular_hours_lookback_weeks or 2,
                    include_overtime=params.include_overtime,
                )
            case "commission":
                return self.formula_calculators.apply_commission(
                    employee_id=employee["id"],
                    holiday_date=holiday_date,
                    current_run_id=current_run_id,
                    divisor=params.commission_divisor or 60,
                    lookback_weeks=params.commission_lookback_weeks or 12,
                )
            case "nt_split_by_compensation":
                # NWT Employment Standards Act s.17:
                # - If paid by time (hourly): pay for normal hours of work at regular rate
                # - If paid otherwise (salaried): average daily pay from 4 weeks prior
                #   based on actual days worked (not fixed divisor)
                compensation_type = employee.get("compensation_type", "").lower()
                if compensation_type == "salary":
                    # Salaried: Get wages from payroll_records (not timesheet)
                    # Salaried employees typically don't have timesheet entries,
                    # so we need to use payroll records for historical wages.
                    # Per NWT ESA s.17: "average day's pay" = wages in 4 weeks / days worked
                    return self.formula_calculators.apply_4_week_average_from_payroll(
                        employee_id=employee["id"],
                        holiday_date=holiday_date,
                        current_run_id=current_run_id,
                        include_overtime=params.include_overtime,
                        employee_fallback=employee,
                        new_employee_fallback=params.new_employee_fallback,
                        default_daily_hours=params.default_daily_hours,
                    )
                else:
                    # Hourly: Use actual normal hours of work from recent history
                    # (not just default_daily_hours which may not reflect reality)
                    hourly_rate = GrossCalculator.calculate_hourly_rate(employee)
                    normal_hours = self.work_day_tracker.get_normal_daily_hours(
                        employee, config, holiday_date
                    )
                    daily_pay = hourly_rate * normal_hours
                    logger.debug(
                        "NT hourly daily rate: employee=%s, $%.2f × %.1f normal hrs = $%.2f",
                        employee["id"],
                        float(hourly_rate),
                        float(normal_hours),
                        float(daily_pay),
                    )
                    return daily_pay
            case _:
                logger.error(
                    "Unknown formula_type '%s' for province %s",
                    formula_type,
                    config.province_code,
                )
                hourly_rate = GrossCalculator.calculate_hourly_rate(employee)
                return params.default_daily_hours * hourly_rate

    def _calculate_premium_pay(
        self,
        employee: dict[str, Any],
        hours_worked: Decimal,
        config: HolidayPayConfig,
    ) -> Decimal:
        """Calculate premium pay for working on a statutory holiday.

        Basic formula: hours_worked x hourly_rate x premium_rate

        For provinces with tiered rates, the calculation splits hours across tiers.
        """
        hourly_rate = GrossCalculator.calculate_hourly_rate(employee)

        if not config.premium_rate_tiers:
            premium_rate = config.premium_rate
            premium_pay = hours_worked * hourly_rate * premium_rate

            logger.debug(
                "Premium pay (flat): %.2f hrs x $%.2f x %.2f = $%.2f",
                float(hours_worked),
                float(hourly_rate),
                float(premium_rate),
                float(premium_pay),
            )

            return premium_pay

        # Tiered calculation
        sorted_tiers = sorted(
            config.premium_rate_tiers,
            key=lambda t: t.hours_threshold
        )

        premium_pay = Decimal("0")
        remaining_hours = hours_worked
        tier_details: list[str] = []

        first_tier_threshold = sorted_tiers[0].hours_threshold if sorted_tiers else hours_worked

        if remaining_hours > Decimal("0"):
            base_hours = min(remaining_hours, first_tier_threshold)
            if base_hours > Decimal("0"):
                base_pay = base_hours * hourly_rate * config.premium_rate
                premium_pay += base_pay
                remaining_hours -= base_hours
                tier_details.append(
                    f"{float(base_hours):.2f}h x ${float(hourly_rate):.2f} x {float(config.premium_rate):.2f}"
                )

        for i, tier in enumerate(sorted_tiers):
            if remaining_hours <= Decimal("0"):
                break

            if i + 1 < len(sorted_tiers):
                next_threshold = sorted_tiers[i + 1].hours_threshold
                tier_hours = min(remaining_hours, next_threshold - tier.hours_threshold)
            else:
                tier_hours = remaining_hours

            if tier_hours > Decimal("0"):
                tier_pay = tier_hours * hourly_rate * tier.rate
                premium_pay += tier_pay
                remaining_hours -= tier_hours
                tier_details.append(
                    f"{float(tier_hours):.2f}h x ${float(hourly_rate):.2f} x {float(tier.rate):.2f}"
                )

        logger.debug(
            "Premium pay (tiered): %.2f hrs, breakdown: [%s] = $%.2f",
            float(hours_worked),
            " + ".join(tier_details),
            float(premium_pay),
        )

        return premium_pay

    # =========================================================================
    # Backwards-Compatible Wrapper Methods
    # These delegate to the component classes for tests that call them directly
    # =========================================================================

    def _apply_30_day_average(
        self,
        employee_id: str,
        employee: dict[str, Any],
        holiday_date: date,
        method: str,
        include_overtime: bool,
        default_daily_hours: Decimal,
        new_employee_fallback: str | None = None,
        lookback_days: int = 30,
        include_vacation_pay: bool = False,
        include_previous_holiday_pay: bool = False,
        include_sick_pay: bool = False,
        current_run_id: str | None = None,
    ) -> Decimal:
        """Backwards-compatible wrapper for formula_calculators.apply_30_day_average."""
        return self.formula_calculators.apply_30_day_average(
            employee_id=employee_id,
            employee=employee,
            holiday_date=holiday_date,
            method=method,
            include_overtime=include_overtime,
            default_daily_hours=default_daily_hours,
            new_employee_fallback=new_employee_fallback,
            lookback_days=lookback_days,
            include_vacation_pay=include_vacation_pay,
            include_previous_holiday_pay=include_previous_holiday_pay,
            include_sick_pay=include_sick_pay,
            current_run_id=current_run_id,
        )

    def _apply_current_period_daily(
        self, current_period_gross: Decimal, pay_frequency: str
    ) -> Decimal:
        """Backwards-compatible wrapper for formula_calculators.apply_current_period_daily."""
        return self.formula_calculators.apply_current_period_daily(
            current_period_gross=current_period_gross,
            pay_frequency=pay_frequency,
        )

    def _apply_4_week_average(
        self,
        employee_id: str,
        holiday_date: date,
        current_run_id: str,
        divisor: int,
        include_vacation_pay: bool,
        include_overtime: bool,
        employee_fallback: dict[str, Any],
        new_employee_fallback: str | None = None,
        default_daily_hours: Decimal = Decimal("8"),
    ) -> Decimal:
        """Backwards-compatible wrapper for formula_calculators.apply_4_week_average."""
        return self.formula_calculators.apply_4_week_average(
            employee_id=employee_id,
            holiday_date=holiday_date,
            current_run_id=current_run_id,
            divisor=divisor,
            include_vacation_pay=include_vacation_pay,
            include_overtime=include_overtime,
            employee_fallback=employee_fallback,
            new_employee_fallback=new_employee_fallback,
            default_daily_hours=default_daily_hours,
        )

    def _apply_4_week_daily(
        self,
        employee_id: str,
        holiday_date: date,
        current_run_id: str,
        include_overtime: bool,
        employee_fallback: dict[str, Any],
        new_employee_fallback: str | None = None,
        default_daily_hours: Decimal = Decimal("8"),
    ) -> Decimal:
        """Backwards-compatible wrapper for formula_calculators.apply_4_week_daily."""
        return self.formula_calculators.apply_4_week_daily(
            employee_id=employee_id,
            holiday_date=holiday_date,
            current_run_id=current_run_id,
            include_overtime=include_overtime,
            employee_fallback=employee_fallback,
            new_employee_fallback=new_employee_fallback,
            default_daily_hours=default_daily_hours,
        )

    def _apply_5_percent_28_days(
        self,
        employee_id: str,
        holiday_date: date,
        current_run_id: str,
        percentage: Decimal,
        include_vacation_pay: bool,
        include_previous_holiday_pay: bool,
        current_period_gross: Decimal,
        new_employee_fallback: str | None = None,
        lookback_days: int = 28,
    ) -> Decimal:
        """Backwards-compatible wrapper for formula_calculators.apply_5_percent_28_days."""
        return self.formula_calculators.apply_5_percent_28_days(
            employee_id=employee_id,
            holiday_date=holiday_date,
            current_run_id=current_run_id,
            percentage=percentage,
            include_vacation_pay=include_vacation_pay,
            include_previous_holiday_pay=include_previous_holiday_pay,
            current_period_gross=current_period_gross,
            new_employee_fallback=new_employee_fallback,
            lookback_days=lookback_days,
        )

    def _apply_3_week_average_nl(
        self,
        employee_id: str,
        employee: dict[str, Any],
        holiday_date: date,
        lookback_weeks: int,
        divisor: int,
        include_overtime: bool,
    ) -> Decimal:
        """Backwards-compatible wrapper for formula_calculators.apply_3_week_average_nl."""
        return self.formula_calculators.apply_3_week_average_nl(
            employee_id=employee_id,
            employee=employee,
            holiday_date=holiday_date,
            lookback_weeks=lookback_weeks,
            divisor=divisor,
            include_overtime=include_overtime,
        )

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
        """Backwards-compatible wrapper for formula_calculators.apply_irregular_hours."""
        return self.formula_calculators.apply_irregular_hours(
            employee_id=employee_id,
            employee=employee,
            holiday_date=holiday_date,
            current_run_id=current_run_id,
            percentage=percentage,
            lookback_weeks=lookback_weeks,
            include_overtime=include_overtime,
        )

    def _apply_commission(
        self,
        employee_id: str,
        holiday_date: date,
        current_run_id: str,
        divisor: int,
        lookback_weeks: int,
    ) -> Decimal:
        """Backwards-compatible wrapper for formula_calculators.apply_commission."""
        return self.formula_calculators.apply_commission(
            employee_id=employee_id,
            holiday_date=holiday_date,
            current_run_id=current_run_id,
            divisor=divisor,
            lookback_weeks=lookback_weeks,
        )

    def _is_eligible_for_holiday_pay(
        self,
        employee: dict[str, Any],
        holiday_date: date,
        config: HolidayPayConfig,
        timesheet_entries: list[dict[str, Any]] | None = None,
    ) -> bool:
        """Backwards-compatible wrapper for eligibility_checker.is_eligible_for_holiday_pay."""
        return self.eligibility_checker.is_eligible_for_holiday_pay(
            employee=employee,
            holiday_date=holiday_date,
            config=config,
            timesheet_entries=timesheet_entries,
        )

    def _get_ineligibility_reason(
        self,
        employee: dict[str, Any],
        holiday_date: date,
        config: HolidayPayConfig,
        timesheet_entries: list[dict[str, Any]] | None = None,
    ) -> str:
        """Backwards-compatible wrapper for eligibility_checker.get_ineligibility_reason."""
        return self.eligibility_checker.get_ineligibility_reason(
            employee=employee,
            holiday_date=holiday_date,
            config=config,
            timesheet_entries=timesheet_entries,
        )

    def _check_last_first_rule_from_entries(
        self, timesheet_entries: list[dict[str, Any]], holiday_date: date, strict_mode: bool = True
    ) -> tuple[bool, bool]:
        """Backwards-compatible wrapper for eligibility_checker."""
        return self.eligibility_checker.check_last_first_rule_from_entries(
            timesheet_entries, holiday_date, strict_mode
        )

    def _check_last_first_rule_improved(
        self, employee_id: str, holiday_date: date, max_search_days: int = 28, strict_mode: bool = True
    ) -> tuple[bool, bool, date | None, date | None]:
        """Backwards-compatible wrapper for eligibility_checker."""
        return self.eligibility_checker.check_last_first_rule_improved(
            employee_id, holiday_date, max_search_days, strict_mode
        )

    def _is_regular_work_day_5_of_9(
        self, employee_id: str, holiday_date: date, hire_date: date | None, config: HolidayPayConfig | None = None
    ) -> bool:
        """Backwards-compatible wrapper for work_day_tracker."""
        return self.work_day_tracker.is_regular_work_day_5_of_9(
            employee_id, holiday_date, hire_date, config
        )

    def _get_days_worked_in_4_weeks(self, employee_id: str, holiday_date: date) -> int:
        """Backwards-compatible wrapper for work_day_tracker."""
        return self.work_day_tracker.get_days_worked_in_4_weeks(employee_id, holiday_date)

    def _count_days_worked_in_period(
        self,
        entries: list[dict[str, Any]],
        start_date: date,
        end_date: date,
        employee_id: str | None = None,
    ) -> int:
        """Backwards-compatible wrapper for work_day_tracker."""
        return self.work_day_tracker.count_days_worked_in_period(
            entries, start_date, end_date, employee_id=employee_id
        )

    def _get_normal_daily_hours(
        self, employee: dict[str, Any], config: HolidayPayConfig, holiday_date: date
    ) -> Decimal:
        """Backwards-compatible wrapper for work_day_tracker."""
        return self.work_day_tracker.get_normal_daily_hours(employee, config, holiday_date)

    def _get_timesheet_entries_for_eligibility(
        self, employee_id: str, start_date: date, end_date: date
    ) -> list[dict[str, Any]] | None:
        """Backwards-compatible wrapper for work_day_tracker."""
        return self.work_day_tracker.get_timesheet_entries_for_eligibility(
            employee_id, start_date, end_date
        )

    def _get_4_week_earnings(
        self, employee_id: str, before_date: date, current_run_id: str, include_overtime: bool = False
    ) -> tuple[Decimal, Decimal]:
        """Backwards-compatible wrapper for earnings_fetcher."""
        return self.earnings_fetcher.get_4_week_earnings(
            employee_id, before_date, current_run_id, include_overtime
        )

    def _get_4_week_earnings_from_timesheet(
        self, employee_id: str, holiday_date: date, hourly_rate: Decimal, include_overtime: bool = False
    ) -> Decimal:
        """Backwards-compatible wrapper for earnings_fetcher."""
        return self.earnings_fetcher.get_4_week_earnings_from_timesheet(
            employee_id, holiday_date, hourly_rate, include_overtime
        )

    def _get_28_day_earnings(
        self, employee_id: str, before_date: date, current_run_id: str, lookback_days: int = 28
    ) -> tuple[Decimal, Decimal, Decimal]:
        """Backwards-compatible wrapper for earnings_fetcher."""
        return self.earnings_fetcher.get_28_day_earnings(
            employee_id, before_date, current_run_id, lookback_days
        )

    def _count_work_days_for_eligibility(
        self, employee_id: str, start_date: date, end_date: date
    ) -> int:
        """Backwards-compatible wrapper for work_day_tracker."""
        return self.work_day_tracker.count_work_days_for_eligibility(
            employee_id, start_date, end_date
        )
