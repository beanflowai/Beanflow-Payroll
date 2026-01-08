"""
Payroll Input Preparation

Prepares employee payroll inputs for calculation engine.
Extracted from run_operations.py for better modularity.
"""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from typing import Any

from app.models.payroll import PayFrequency, Province
from app.services.payroll import EmployeePayrollInput
from app.services.payroll_run.benefits_calculator import BenefitsCalculator
from app.services.payroll_run.constants import get_federal_bpa, get_provincial_bpa
from app.services.payroll_run.gross_calculator import GrossCalculator
from app.services.payroll_run.holiday_pay_calculator import HolidayPayCalculator
from app.services.payroll_run.ytd_calculator import YtdCalculator

logger = logging.getLogger(__name__)


class PayrollInputPreparer:
    """Prepares employee payroll inputs for calculation."""

    def __init__(
        self,
        supabase: Any,
        user_id: str,
        company_id: str,
        ytd_calculator: YtdCalculator,
        holiday_calculator: HolidayPayCalculator,
    ):
        """Initialize input preparer.

        Args:
            supabase: Supabase client instance
            user_id: Current user ID
            company_id: Current company ID
            ytd_calculator: YTD calculator instance
            holiday_calculator: Holiday pay calculator instance
        """
        self.supabase = supabase
        self.user_id = user_id
        self.company_id = company_id
        self.ytd_calculator = ytd_calculator
        self.holiday_calculator = holiday_calculator

    async def prepare_all_inputs(
        self,
        run: dict[str, Any],
        records: list[dict[str, Any]],
        run_id: str,
        tax_year: int,
        pay_date: date | None,
        period_start: date | None,
        period_end: date | None,
    ) -> tuple[list[EmployeePayrollInput], dict[str, dict[str, Any]]]:
        """Prepare calculation inputs for all employees.

        Args:
            run: Payroll run data
            records: List of payroll records with employee info
            run_id: Payroll run ID
            tax_year: Tax year for calculations
            pay_date: Pay date for tax edition selection
            period_start: Period start date
            period_end: Period end date

        Returns:
            Tuple of (calculation_inputs, record_map with metadata)
        """
        # Query statutory holidays in the pay period
        holidays_in_period = await self._get_holidays_in_period(period_start, period_end)

        # Get prior YTD data for all employees
        employee_ids = [record["employee_id"] for record in records]
        prior_ytd_data = self.ytd_calculator.get_prior_ytd_for_employees(
            employee_ids, run_id, year=tax_year
        )

        calculation_inputs: list[EmployeePayrollInput] = []
        record_map: dict[str, dict[str, Any]] = {}

        for record in records:
            calc_input, record_metadata = await self._prepare_single_input(
                record=record,
                run=run,
                run_id=run_id,
                tax_year=tax_year,
                pay_date=pay_date,
                period_start=period_start,
                period_end=period_end,
                holidays_in_period=holidays_in_period,
                prior_ytd_data=prior_ytd_data,
            )
            calculation_inputs.append(calc_input)
            record_map[record["employee_id"]] = record_metadata

        return calculation_inputs, record_map

    async def _get_holidays_in_period(
        self, period_start: date | None, period_end: date | None
    ) -> list[dict[str, Any]]:
        """Query statutory holidays in the pay period."""
        if not period_start or not period_end:
            return []

        holidays_result = self.supabase.table("statutory_holidays").select(
            "holiday_date, name, province"
        ).gte(
            "holiday_date", period_start.strftime("%Y-%m-%d")
        ).lte(
            "holiday_date", period_end.strftime("%Y-%m-%d")
        ).eq(
            "is_statutory", True
        ).execute()

        return holidays_result.data or []

    async def _prepare_single_input(
        self,
        record: dict[str, Any],
        run: dict[str, Any],
        run_id: str,
        tax_year: int,
        pay_date: date | None,
        period_start: date | None,
        period_end: date | None,
        holidays_in_period: list[dict[str, Any]],
        prior_ytd_data: dict[str, dict[str, Any]],
    ) -> tuple[EmployeePayrollInput, dict[str, Any]]:
        """Prepare calculation input for a single employee.

        Returns:
            Tuple of (EmployeePayrollInput, record with metadata)
        """
        employee = record["employees"]
        input_data = record.get("input_data") or {}

        # Determine pay frequency
        pay_group = employee.get("pay_groups") or {}
        pay_frequency_str = pay_group.get("pay_frequency") or employee.get(
            "pay_frequency", "bi_weekly"
        )
        pay_frequency = PayFrequency(pay_frequency_str)

        # Calculate taxable benefits and deductions
        group_benefits = pay_group.get("group_benefits") or {}
        taxable_benefits_pensionable = BenefitsCalculator.calculate_taxable_benefits(group_benefits)
        benefits_deduction = BenefitsCalculator.calculate_benefits_deduction(group_benefits)

        # Calculate gross pay
        gross_regular, gross_overtime = GrossCalculator.calculate_gross_from_input(
            employee, input_data, pay_frequency_str
        )

        # Calculate vacation pay
        vacation_pay, vacation_hours_taken = self._calculate_vacation_pay(
            employee, input_data, gross_regular, gross_overtime
        )

        # Calculate sick leave
        (
            sick_hours_taken,
            paid_sick_hours,
            unpaid_sick_hours,
            sick_pay,
            gross_regular,
        ) = self._calculate_sick_leave(employee, input_data, gross_regular)

        # Calculate holiday pay
        holiday_pay, holiday_premium_pay = await self._calculate_holiday_pay(
            employee=employee,
            input_data=input_data,
            pay_frequency_str=pay_frequency_str,
            period_start=period_start,
            period_end=period_end,
            holidays_in_period=holidays_in_period,
            gross_regular=gross_regular,
            gross_overtime=gross_overtime,
            run_id=run_id,
        )

        # Calculate other earnings from adjustments
        other_earnings = self._calculate_other_earnings(input_data)

        # Calculate tax claims
        province_code = employee["province_of_employment"]
        federal_claim, provincial_claim = self._calculate_tax_claims(
            employee, province_code, tax_year, pay_date, gross_regular, gross_overtime
        )

        # Get prior YTD for this employee
        emp_prior_ytd = prior_ytd_data.get(record["employee_id"], {})

        calc_input = EmployeePayrollInput(
            employee_id=record["employee_id"],
            province=Province(province_code),
            pay_frequency=pay_frequency,
            gross_regular=gross_regular,
            gross_overtime=gross_overtime,
            holiday_pay=holiday_pay,
            holiday_premium_pay=holiday_premium_pay,
            vacation_pay=vacation_pay,
            other_earnings=other_earnings,
            federal_claim_amount=federal_claim,
            provincial_claim_amount=provincial_claim,
            is_cpp_exempt=employee.get("is_cpp_exempt", False),
            is_ei_exempt=employee.get("is_ei_exempt", False),
            cpp2_exempt=employee.get("cpp2_exempt", False),
            taxable_benefits_pensionable=taxable_benefits_pensionable,
            other_deductions=benefits_deduction,
            pay_date=pay_date,
            ytd_gross=emp_prior_ytd.get("ytd_gross", Decimal("0")),
            ytd_cpp_base=emp_prior_ytd.get("ytd_cpp", Decimal("0")),
            ytd_cpp_additional=emp_prior_ytd.get("ytd_cpp_additional", Decimal("0")),
            ytd_ei=emp_prior_ytd.get("ytd_ei", Decimal("0")),
            ytd_federal_tax=emp_prior_ytd.get("ytd_federal_tax", Decimal("0")),
            ytd_provincial_tax=emp_prior_ytd.get("ytd_provincial_tax", Decimal("0")),
        )

        # Build record metadata for later use
        record_metadata = {
            **record,
            "_vacation_hours_taken": vacation_hours_taken,
            "_sick_hours_taken": sick_hours_taken,
            "_paid_sick_hours": paid_sick_hours,
            "_unpaid_sick_hours": unpaid_sick_hours,
            "_sick_pay": sick_pay,
        }

        return calc_input, record_metadata

    def _calculate_vacation_pay(
        self,
        employee: dict[str, Any],
        input_data: dict[str, Any],
        gross_regular: Decimal,
        gross_overtime: Decimal,
    ) -> tuple[Decimal, Decimal]:
        """Calculate vacation pay based on payout method.

        Returns:
            Tuple of (vacation_pay, vacation_hours_taken)
        """
        vacation_config = employee.get("vacation_config") or {}
        payout_method = vacation_config.get("payout_method", "accrual")
        vacation_pay = Decimal("0")
        vacation_hours_taken = Decimal("0")

        if payout_method == "pay_as_you_go":
            rate_val = vacation_config.get("vacation_rate")
            vacation_rate = Decimal(str(rate_val)) if rate_val is not None else Decimal("0.04")
            base_earnings = gross_regular + gross_overtime
            vacation_pay = base_earnings * vacation_rate
        elif payout_method == "accrual":
            leave_entries = input_data.get("leaveEntries") or []
            for leave in leave_entries:
                if leave.get("type") == "vacation":
                    vacation_hours_taken += Decimal(str(leave.get("hours", 0)))

            if vacation_hours_taken > 0:
                hourly_rate = GrossCalculator.calculate_hourly_rate(employee)
                vacation_pay = vacation_hours_taken * hourly_rate

        return vacation_pay, vacation_hours_taken

    def _calculate_sick_leave(
        self,
        employee: dict[str, Any],
        input_data: dict[str, Any],
        gross_regular: Decimal,
    ) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal]:
        """Calculate sick leave pay and adjustments.

        Returns:
            Tuple of (sick_hours_taken, paid_sick_hours, unpaid_sick_hours, sick_pay, adjusted_gross_regular)
        """
        sick_hours_taken = Decimal("0")
        paid_sick_hours = Decimal("0")
        unpaid_sick_hours = Decimal("0")
        sick_pay = Decimal("0")

        leave_entries = input_data.get("leaveEntries") or []
        for leave in leave_entries:
            if leave.get("type") == "sick":
                sick_hours_taken += Decimal(str(leave.get("hours", 0)))

        if sick_hours_taken > 0:
            # sick_balance is stored in days, convert to hours (8 hours/day)
            sick_balance_days = Decimal(str(employee.get("sick_balance", 0)))
            sick_balance_hours = sick_balance_days * Decimal("8")
            paid_sick_hours = min(sick_hours_taken, sick_balance_hours)
            unpaid_sick_hours = max(Decimal("0"), sick_hours_taken - sick_balance_hours)

            hourly_rate = GrossCalculator.calculate_hourly_rate(employee)
            sick_pay = paid_sick_hours * hourly_rate

            # For salaried employees: deduct unpaid sick hours
            if employee.get("annual_salary") and not employee.get("hourly_rate"):
                unpaid_sick_deduction = unpaid_sick_hours * hourly_rate
                gross_regular -= unpaid_sick_deduction
                logger.debug(
                    "SICK LEAVE: Employee %s %s (salaried) - "
                    "sick_hours=%s, balance_days=%s, balance_hours=%s, paid=%s, unpaid=%s, "
                    "hourly_rate=%s, deduction=%s, new_gross=%s",
                    employee.get('first_name'), employee.get('last_name'),
                    sick_hours_taken, sick_balance_days, sick_balance_hours,
                    paid_sick_hours, unpaid_sick_hours,
                    hourly_rate, unpaid_sick_deduction, gross_regular
                )
            # For hourly employees: add only paid sick hours
            elif employee.get("hourly_rate"):
                gross_regular += sick_pay
                logger.debug(
                    "SICK LEAVE: Employee %s %s (hourly) - "
                    "sick_hours=%s, balance_days=%s, balance_hours=%s, paid=%s, unpaid=%s, sick_pay=%s",
                    employee.get('first_name'), employee.get('last_name'),
                    sick_hours_taken, sick_balance_days, sick_balance_hours,
                    paid_sick_hours, unpaid_sick_hours, sick_pay
                )

        return sick_hours_taken, paid_sick_hours, unpaid_sick_hours, sick_pay, gross_regular

    async def _calculate_holiday_pay(
        self,
        employee: dict[str, Any],
        input_data: dict[str, Any],
        pay_frequency_str: str,
        period_start: date | None,
        period_end: date | None,
        holidays_in_period: list[dict[str, Any]],
        gross_regular: Decimal,
        gross_overtime: Decimal,
        run_id: str,
    ) -> tuple[Decimal, Decimal]:
        """Calculate holiday pay using HolidayPayCalculator.

        Returns:
            Tuple of (holiday_pay, holiday_premium_pay)
        """
        holiday_pay = Decimal("0")
        holiday_premium_pay = Decimal("0")

        if not period_start or not period_end:
            return holiday_pay, holiday_premium_pay

        province_code = employee["province_of_employment"]

        # Filter holidays for this employee's province
        employee_holidays = [
            h for h in holidays_in_period
            if h.get("province") == province_code
        ]

        # Debug logging to track holidays count
        logger.debug(
            "HOLIDAY DEBUG: Employee %s %s (province=%s): "
            "total_holidays_in_period=%d, employee_holidays=%d",
            employee.get("first_name"),
            employee.get("last_name"),
            province_code,
            len(holidays_in_period),
            len(employee_holidays),
        )

        holiday_result = self.holiday_calculator.calculate_holiday_pay(
            employee=employee,
            province=province_code,
            pay_frequency=pay_frequency_str,
            period_start=period_start,
            period_end=period_end,
            holidays_in_period=employee_holidays,
            holiday_work_entries=input_data.get("holidayWorkEntries") or [],
            current_period_gross=gross_regular + gross_overtime,
            current_run_id=run_id,
            holiday_pay_exempt=input_data.get("holidayPayExempt", False),
        )

        return holiday_result.regular_holiday_pay, holiday_result.premium_holiday_pay

    def _calculate_other_earnings(self, input_data: dict[str, Any]) -> Decimal:
        """Calculate other earnings from adjustments."""
        other_earnings = Decimal("0")

        if input_data.get("adjustments"):
            for adj in input_data["adjustments"]:
                amount = Decimal(str(adj.get("amount", 0)))
                if adj.get("type") == "deduction":
                    other_earnings -= amount
                else:
                    other_earnings += amount

        return other_earnings

    def _calculate_tax_claims(
        self,
        employee: dict[str, Any],
        province_code: str,
        tax_year: int,
        pay_date: date | None,
        gross_regular: Decimal,
        gross_overtime: Decimal,
    ) -> tuple[Decimal, Decimal]:
        """Calculate federal and provincial tax claims.

        Returns:
            Tuple of (federal_claim, provincial_claim)
        """
        federal_additional = Decimal(str(employee.get("federal_additional_claims", 0)))
        federal_bpa = get_federal_bpa(tax_year, pay_date)
        federal_claim = federal_bpa + federal_additional

        provincial_additional = Decimal(str(employee.get("provincial_additional_claims", 0)))
        provincial_bpa = get_provincial_bpa(province_code, tax_year, pay_date)
        provincial_claim = provincial_bpa + provincial_additional

        logger.debug(
            "PAYROLL DEBUG: Employee %s %s (province=%s): "
            "federal_bpa=%s, additional=%s -> %s, "
            "provincial_bpa=%s, additional=%s -> %s, gross=%s",
            employee.get('first_name'), employee.get('last_name'), province_code,
            federal_bpa, federal_additional, federal_claim,
            provincial_bpa, provincial_additional, provincial_claim,
            gross_regular + gross_overtime
        )

        return federal_claim, provincial_claim
