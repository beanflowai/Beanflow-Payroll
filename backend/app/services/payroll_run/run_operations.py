"""
Payroll Run Operations

Core lifecycle operations for payroll runs:
- create_or_get_run
- recalculate_run
- finalize_run
- approve_run
- send_paystubs
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, cast
from uuid import UUID

import httpx

from app.models.payroll import PayFrequency, Province
from app.services.payroll import (
    EmployeePayrollInput,
    PayrollEngine,
    PaystubDataBuilder,
    PaystubGenerator,
)
from app.services.payroll.paystub_storage import (
    PaystubStorage,
    PaystubStorageConfigError,
)
from app.services.payroll_run.benefits_calculator import BenefitsCalculator
from app.services.payroll_run.constants import (
    calculate_next_period_end,
    calculate_pay_date,
    extract_year_from_date,
    get_federal_bpa,
    get_provincial_bpa,
)
from app.services.payroll_run.gross_calculator import GrossCalculator
from app.services.payroll_run.holiday_pay_calculator import HolidayPayCalculator
from app.services.payroll_run.model_builders import ModelBuilder
from app.services.payroll_run.ytd_calculator import YtdCalculator

logger = logging.getLogger(__name__)


class PayrollRunOperations:
    """Core payroll run lifecycle operations."""

    def __init__(
        self,
        supabase: Any,
        user_id: str,
        company_id: str,
        ytd_calculator: YtdCalculator,
        get_run_func: Any,
        get_run_records_func: Any,
        create_records_func: Any,
    ):
        """Initialize payroll run operations.

        Args:
            supabase: Supabase client instance
            user_id: Current user ID
            company_id: Current company ID
            ytd_calculator: YTD calculator instance
            get_run_func: Function to get a payroll run by ID
            get_run_records_func: Function to get run records with employee info
            create_records_func: Function to create records for employees
        """
        self.supabase = supabase
        self.user_id = user_id
        self.company_id = company_id
        self.ytd_calculator = ytd_calculator
        self.holiday_calculator = HolidayPayCalculator(supabase, user_id, company_id)
        self._get_run = get_run_func
        self._get_run_records = get_run_records_func
        self._create_records_for_employees = create_records_func

    async def recalculate_run(self, run_id: UUID) -> dict[str, Any]:
        """Recalculate all records in a draft payroll run.

        1. Reads input_data from all payroll_records
        2. Calls PayrollEngine.calculate_batch()
        3. Updates payroll_records with new CPP/EI/Tax values
        4. Updates payroll_runs summary totals
        5. Clears is_modified flags

        Returns:
            Updated payroll run data

        Raises:
            ValueError: If run is not in draft status
        """
        # Verify run is in draft status
        run = await self._get_run(run_id)
        if not run:
            raise ValueError("Payroll run not found")

        if run["status"] != "draft":
            raise ValueError(
                f"Cannot recalculate: payroll run is in '{run['status']}' status, "
                "not 'draft'"
            )

        # Get all records with employee info
        records = await self._get_run_records(run_id)
        if not records:
            raise ValueError("No records found for payroll run")

        # Extract year from pay_date for YTD calculations
        pay_date_str = run.get("pay_date", "")
        tax_year = extract_year_from_date(pay_date_str)

        # Convert pay_date string to date object for tax edition selection
        pay_date_obj = datetime.strptime(pay_date_str, "%Y-%m-%d").date() if pay_date_str else None

        # Parse period dates for holiday pay calculation
        period_start_str = run.get("period_start", "")
        period_end_str = run.get("period_end", "")
        period_start_obj = datetime.strptime(period_start_str, "%Y-%m-%d").date() if period_start_str else None
        period_end_obj = datetime.strptime(period_end_str, "%Y-%m-%d").date() if period_end_str else None

        # Query statutory holidays in the pay period (for all provinces)
        holidays_in_period: list[dict[str, Any]] = []
        if period_start_obj and period_end_obj:
            holidays_result = self.supabase.table("statutory_holidays").select(
                "holiday_date, name, province"
            ).gte(
                "holiday_date", period_start_str
            ).lte(
                "holiday_date", period_end_str
            ).eq(
                "is_statutory", True
            ).execute()
            holidays_in_period = holidays_result.data or []

        # Get prior YTD data from completed payroll runs (excluding current run)
        employee_ids = [record["employee_id"] for record in records]
        prior_ytd_data = self.ytd_calculator.get_prior_ytd_for_employees(
            employee_ids, str(run_id), year=tax_year
        )

        # Build calculation inputs from input_data
        calculation_inputs: list[EmployeePayrollInput] = []
        record_map: dict[str, dict[str, Any]] = {}

        for record in records:
            employee = record["employees"]
            input_data = record.get("input_data") or {}

            # Determine pay frequency
            pay_group = employee.get("pay_groups") or {}
            pay_frequency_str = pay_group.get("pay_frequency") or employee.get(
                "pay_frequency", "bi_weekly"
            )
            pay_frequency = PayFrequency(pay_frequency_str)

            # Extract benefits from pay group
            group_benefits = pay_group.get("group_benefits") or {}

            # Calculate taxable benefits and employee deductions
            taxable_benefits_pensionable = BenefitsCalculator.calculate_taxable_benefits(group_benefits)
            benefits_deduction = BenefitsCalculator.calculate_benefits_deduction(group_benefits)

            # Calculate gross pay from input_data
            gross_regular, gross_overtime = GrossCalculator.calculate_gross_from_input(
                employee, input_data, pay_frequency_str
            )

            # Calculate vacation pay for pay_as_you_go method
            vacation_config = employee.get("vacation_config") or {}
            payout_method = vacation_config.get("payout_method", "accrual")
            vacation_pay_for_gross = Decimal("0")
            vacation_hours_taken = Decimal("0")

            if payout_method == "pay_as_you_go":
                vacation_rate = Decimal(str(vacation_config.get("vacation_rate", "0.04")))
                base_earnings = gross_regular + gross_overtime
                vacation_pay_for_gross = base_earnings * vacation_rate
            elif payout_method == "accrual":
                # For accrual method: extract vacation hours from leaveEntries
                leave_entries = input_data.get("leaveEntries") or []
                for leave in leave_entries:
                    if leave.get("type") == "vacation":
                        vacation_hours_taken += Decimal(str(leave.get("hours", 0)))

                # Calculate vacation pay from hours taken
                if vacation_hours_taken > 0:
                    hourly_rate = GrossCalculator.calculate_hourly_rate(employee)
                    vacation_pay_for_gross = vacation_hours_taken * hourly_rate

            # =========================================================================
            # Sick Leave Processing
            # - Extract sick hours from leaveEntries
            # - Calculate paid vs unpaid based on employee.sick_balance
            # - Salaried: deduct unpaid hours from gross_regular
            # - Hourly: add paid hours to gross_regular
            # =========================================================================
            sick_hours_taken = Decimal("0")
            paid_sick_hours = Decimal("0")
            unpaid_sick_hours = Decimal("0")
            sick_pay = Decimal("0")
            unpaid_sick_deduction = Decimal("0")

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

                # For salaried employees: base salary already includes all hours,
                # so we deduct unpaid sick hours
                if employee.get("annual_salary") and not employee.get("hourly_rate"):
                    unpaid_sick_deduction = unpaid_sick_hours * hourly_rate
                    gross_regular -= unpaid_sick_deduction
                    logger.info(
                        "SICK LEAVE: Employee %s %s (salaried) - "
                        "sick_hours=%s, balance_days=%s, balance_hours=%s, paid=%s, unpaid=%s, "
                        "hourly_rate=%s, deduction=%s, new_gross=%s",
                        employee.get('first_name'), employee.get('last_name'),
                        sick_hours_taken, sick_balance_days, sick_balance_hours,
                        paid_sick_hours, unpaid_sick_hours,
                        hourly_rate, unpaid_sick_deduction, gross_regular
                    )
                # For hourly employees: add only paid sick hours (gross_calculator
                # already excludes sick leave from automatic addition)
                elif employee.get("hourly_rate"):
                    gross_regular += sick_pay
                    logger.info(
                        "SICK LEAVE: Employee %s %s (hourly) - "
                        "sick_hours=%s, balance_days=%s, balance_hours=%s, paid=%s, unpaid=%s, sick_pay=%s",
                        employee.get('first_name'), employee.get('last_name'),
                        sick_hours_taken, sick_balance_days, sick_balance_hours,
                        paid_sick_hours, unpaid_sick_hours, sick_pay
                    )

            # Calculate additional earnings from input_data
            holiday_pay = Decimal("0")
            holiday_premium_pay = Decimal("0")
            other_earnings = Decimal("0")

            # Holiday pay calculation (Regular + Premium) using HolidayPayCalculator
            province_code = employee["province_of_employment"]
            if period_start_obj and period_end_obj:
                # Filter holidays for this employee's province
                employee_holidays = [
                    h for h in holidays_in_period
                    if h.get("province") == province_code
                ]

                holiday_result = self.holiday_calculator.calculate_holiday_pay(
                    employee=employee,
                    province=province_code,
                    pay_frequency=pay_frequency_str,
                    period_start=period_start_obj,
                    period_end=period_end_obj,
                    holidays_in_period=employee_holidays,
                    holiday_work_entries=input_data.get("holidayWorkEntries") or [],
                    current_period_gross=gross_regular + gross_overtime,
                    current_run_id=str(run_id),
                )
                holiday_pay = holiday_result.regular_holiday_pay
                holiday_premium_pay = holiday_result.premium_holiday_pay

            # Adjustments
            if input_data.get("adjustments"):
                for adj in input_data["adjustments"]:
                    amount = Decimal(str(adj.get("amount", 0)))
                    if adj.get("type") == "deduction":
                        other_earnings -= amount
                    else:
                        other_earnings += amount

            # Calculate claim amounts (province_code already defined in holiday section)
            federal_additional = Decimal(str(employee.get("federal_additional_claims", 0)))
            federal_bpa = get_federal_bpa(tax_year, pay_date_obj)
            federal_claim = federal_bpa + federal_additional

            provincial_additional = Decimal(str(employee.get("provincial_additional_claims", 0)))
            provincial_bpa = get_provincial_bpa(province_code, tax_year, pay_date_obj)
            provincial_claim = provincial_bpa + provincial_additional

            logger.info(
                "PAYROLL DEBUG: Employee %s %s (province=%s): "
                "federal_bpa=%s, additional=%s -> %s, "
                "provincial_bpa=%s, additional=%s -> %s, gross=%s",
                employee.get('first_name'), employee.get('last_name'), province_code,
                federal_bpa, federal_additional, federal_claim,
                provincial_bpa, provincial_additional, provincial_claim,
                gross_regular + gross_overtime
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
                vacation_pay=vacation_pay_for_gross,
                other_earnings=other_earnings,
                federal_claim_amount=federal_claim,
                provincial_claim_amount=provincial_claim,
                is_cpp_exempt=employee.get("is_cpp_exempt", False),
                is_ei_exempt=employee.get("is_ei_exempt", False),
                cpp2_exempt=employee.get("cpp2_exempt", False),
                taxable_benefits_pensionable=taxable_benefits_pensionable,
                other_deductions=benefits_deduction,
                pay_date=pay_date_obj,
                ytd_gross=emp_prior_ytd.get("ytd_gross", Decimal("0")),
                ytd_cpp_base=emp_prior_ytd.get("ytd_cpp", Decimal("0")),
                ytd_cpp_additional=emp_prior_ytd.get("ytd_cpp_additional", Decimal("0")),
                ytd_ei=emp_prior_ytd.get("ytd_ei", Decimal("0")),
                ytd_federal_tax=emp_prior_ytd.get("ytd_federal_tax", Decimal("0")),
                ytd_provincial_tax=emp_prior_ytd.get("ytd_provincial_tax", Decimal("0")),
            )
            calculation_inputs.append(calc_input)
            record_map[record["employee_id"]] = {
                **record,
                "_vacation_hours_taken": vacation_hours_taken,
                "_sick_hours_taken": sick_hours_taken,
                "_paid_sick_hours": paid_sick_hours,
                "_unpaid_sick_hours": unpaid_sick_hours,
                "_sick_pay": sick_pay,
            }

        # Calculate using PayrollEngine
        engine = PayrollEngine(year=tax_year)
        results = engine.calculate_batch(calculation_inputs)

        # Update each record with new calculation results
        for result in results:
            record = record_map[result.employee_id]
            input_data = record.get("input_data") or {}
            employee = record["employees"]
            emp_prior_ytd = prior_ytd_data.get(result.employee_id, {})

            # Calculate vacation accrued
            vacation_config = employee.get("vacation_config") or {}
            payout_method = vacation_config.get("payout_method", "accrual")
            if payout_method == "accrual":
                vacation_rate = Decimal(str(vacation_config.get("vacation_rate", "0.04")))
                base_earnings = (
                    result.gross_regular + result.gross_overtime +
                    result.holiday_pay + result.other_earnings
                )
                vacation_accrued = base_earnings * vacation_rate
            else:
                vacation_accrued = Decimal("0")

            # Get vacation hours taken from record_map
            vacation_hours_taken = record.get("_vacation_hours_taken", Decimal("0"))

            # Get sick leave data from record_map
            sick_hours_taken = record.get("_sick_hours_taken", Decimal("0"))
            sick_pay = record.get("_sick_pay", Decimal("0"))

            self.supabase.table("payroll_records").update({
                "gross_regular": float(result.gross_regular),
                "gross_overtime": float(result.gross_overtime),
                "holiday_pay": float(result.holiday_pay),
                "holiday_premium_pay": float(result.holiday_premium_pay),
                "vacation_pay_paid": float(result.vacation_pay),
                "vacation_hours_taken": float(vacation_hours_taken),
                "sick_hours_taken": float(sick_hours_taken),
                "sick_pay_paid": float(sick_pay),
                "other_earnings": float(result.other_earnings),
                "cpp_employee": float(result.cpp_base),
                "cpp_additional": float(result.cpp_additional),
                "ei_employee": float(result.ei_employee),
                "federal_tax": float(result.federal_tax),
                "provincial_tax": float(result.provincial_tax),
                "other_deductions": float(result.other_deductions),
                "cpp_employer": float(result.cpp_employer),
                "ei_employer": float(result.ei_employer),
                "ytd_gross": float(result.new_ytd_gross),
                "ytd_cpp": float(result.new_ytd_cpp),
                "ytd_ei": float(result.new_ytd_ei),
                "ytd_federal_tax": float(result.new_ytd_federal_tax),
                "ytd_provincial_tax": float(result.new_ytd_provincial_tax),
                "ytd_net_pay": float(
                    emp_prior_ytd.get("ytd_net_pay", Decimal("0")) + result.net_pay
                ),
                "vacation_accrued": float(vacation_accrued),
                "is_modified": False,
                "regular_hours_worked": input_data.get("regularHours"),
                "overtime_hours_worked": input_data.get("overtimeHours", 0),
            }).eq("id", record["id"]).execute()

        # Calculate and update run totals
        total_gross = sum(float(r.total_gross) for r in results)
        total_cpp_employee = sum(float(r.cpp_total) for r in results)
        total_cpp_employer = sum(float(r.cpp_employer) for r in results)
        total_ei_employee = sum(float(r.ei_employee) for r in results)
        total_ei_employer = sum(float(r.ei_employer) for r in results)
        total_federal_tax = sum(float(r.federal_tax) for r in results)
        total_provincial_tax = sum(float(r.provincial_tax) for r in results)
        total_net_pay = sum(float(r.net_pay) for r in results)
        total_employer_cost = total_cpp_employer + total_ei_employer

        self.supabase.table("payroll_runs").update({
            "total_employees": len(results),
            "total_gross": total_gross,
            "total_cpp_employee": total_cpp_employee,
            "total_cpp_employer": total_cpp_employer,
            "total_ei_employee": total_ei_employee,
            "total_ei_employer": total_ei_employer,
            "total_federal_tax": total_federal_tax,
            "total_provincial_tax": total_provincial_tax,
            "total_net_pay": total_net_pay,
            "total_employer_cost": total_employer_cost,
        }).eq("id", str(run_id)).execute()

        return await self._get_run(run_id) or {}

    async def finalize_run(self, run_id: UUID) -> dict[str, Any]:
        """Finalize a draft payroll run, transitioning to pending_approval.

        Returns:
            Updated payroll run data

        Raises:
            ValueError: If run is not in draft or has modified records
        """
        run = await self._get_run(run_id)
        if not run:
            raise ValueError("Payroll run not found")

        if run["status"] != "draft":
            raise ValueError(
                f"Cannot finalize: payroll run is in '{run['status']}' status, "
                "not 'draft'"
            )

        # Check for modified records
        modified_result = self.supabase.table("payroll_records").select(
            "id"
        ).eq("payroll_run_id", str(run_id)).eq("is_modified", True).execute()

        if modified_result.data and len(modified_result.data) > 0:
            raise ValueError(
                f"Cannot finalize: {len(modified_result.data)} record(s) have unsaved "
                "changes. Please recalculate before finalizing."
            )

        update_result = self.supabase.table("payroll_runs").update({
            "status": "pending_approval"
        }).eq("id", str(run_id)).execute()

        if not update_result.data or len(update_result.data) == 0:
            raise ValueError("Failed to update payroll run status")

        return cast(dict[str, Any], update_result.data[0])

    async def approve_run(
        self, run_id: UUID, approved_by: str | None = None
    ) -> dict[str, Any]:
        """Approve a pending_approval payroll run.

        Generates paystub PDFs, stores them, and updates status to approved.

        Returns:
            Updated payroll run data with paystubs_generated count

        Raises:
            ValueError: If run is not in pending_approval status
        """
        run = await self._get_run(run_id)
        if not run:
            raise ValueError("Payroll run not found")

        if run["status"] != "pending_approval":
            raise ValueError(
                f"Cannot approve: payroll run is in '{run['status']}' status, "
                "not 'pending_approval'"
            )

        # Get all records with employee, pay group, and company info
        records_result = self.supabase.table("payroll_records").select(
            """
            *,
            employees!inner (
                id, first_name, last_name, email, sin_encrypted,
                province_of_employment, pay_frequency, employment_type,
                annual_salary, hourly_rate, federal_additional_claims,
                provincial_additional_claims, is_cpp_exempt, is_ei_exempt,
                cpp2_exempt, hire_date, termination_date, vacation_config,
                vacation_balance, address_street, address_city,
                address_postal_code, occupation, company_id, pay_group_id,
                companies (
                    id, company_name, business_number, payroll_account_number,
                    province, address_street, address_city, address_postal_code,
                    remitter_type, auto_calculate_deductions, send_paystub_emails,
                    logo_url
                ),
                pay_groups (
                    id, name, description, pay_frequency, employment_type,
                    next_period_end, period_start_day, leave_enabled,
                    statutory_defaults, overtime_policy, wcb_config, group_benefits
                )
            )
            """
        ).eq("payroll_run_id", str(run_id)).eq(
            "user_id", self.user_id
        ).eq("company_id", self.company_id).execute()

        records = records_result.data or []
        if not records:
            raise ValueError("No records found for payroll run")

        # Validate vacation balances for accrual method employees
        balance_errors = self._validate_vacation_balances(records)
        if balance_errors:
            error_msg = "Cannot approve: insufficient vacation balance. "
            error_msg += "; ".join(balance_errors[:5])
            if len(balance_errors) > 5:
                error_msg += f" ... and {len(balance_errors) - 5} more"
            raise ValueError(error_msg)

        # Build PayrollRun model
        payroll_run = ModelBuilder.build_payroll_run(run)

        # Pre-download company logo asynchronously (only once for all employees)
        logo_bytes: bytes | None = None
        first_company_data = records[0]["employees"].get("companies") if records else None
        if first_company_data:
            logo_url = first_company_data.get("logo_url")
            if logo_url:
                try:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.get(logo_url)
                        response.raise_for_status()
                        logo_bytes = response.content
                        logger.info("Downloaded company logo from %s (%d bytes)", logo_url, len(logo_bytes))
                except Exception as e:
                    logger.warning("Failed to download company logo from %s: %s", logo_url, e)

        # Initialize services
        paystub_builder = PaystubDataBuilder()
        paystub_generator = PaystubGenerator()

        try:
            paystub_storage = PaystubStorage()
        except PaystubStorageConfigError as e:
            raise ValueError(
                f"Paystub storage is not configured. Cannot approve payroll run. "
                f"Please configure DO Spaces environment variables. Error: {e}"
            ) from e

        paystubs_generated = 0
        paystub_errors: list[str] = []

        for record_data in records:
            try:
                employee_data = record_data["employees"]
                company_data = employee_data.get("companies")
                pay_group_data = employee_data.get("pay_groups")

                employee = ModelBuilder.build_employee(employee_data)
                company = ModelBuilder.build_company(company_data) if company_data else None
                pay_group = ModelBuilder.build_pay_group(pay_group_data) if pay_group_data else None
                payroll_record = ModelBuilder.build_payroll_record(record_data)

                if not company:
                    logger.warning(
                        f"Skipping paystub for record {record_data['id']}: no company data"
                    )
                    paystub_errors.append(f"Record {record_data['id']}: missing company data")
                    continue

                # Get prior YTD records
                ytd_records = await self.ytd_calculator.get_ytd_records_for_employee(
                    record_data["employee_id"],
                    str(run_id),
                    int(run["pay_date"][:4]),
                )

                masked_sin = "***-***-***"

                paystub_data = paystub_builder.build(
                    record=payroll_record,
                    employee=employee,
                    payroll_run=payroll_run,
                    pay_group=pay_group,
                    company=company,
                    ytd_records=ytd_records,
                    masked_sin=masked_sin,
                    logo_bytes=logo_bytes,
                )

                pdf_bytes = paystub_generator.generate_paystub_bytes(paystub_data)

                pay_date = date.fromisoformat(run["pay_date"])
                storage_key = await paystub_storage.save_paystub(
                    pdf_bytes=pdf_bytes,
                    company_name=company.company_name,
                    employee_id=record_data["employee_id"],
                    pay_date=pay_date,
                    record_id=record_data["id"],
                )

                self.supabase.table("payroll_records").update({
                    "paystub_generated_at": datetime.now().isoformat(),
                    "paystub_storage_key": storage_key,
                }).eq("id", record_data["id"]).execute()

                paystubs_generated += 1
                logger.info(
                    "Generated paystub for employee %s %s (record %s), size: %d bytes",
                    employee.first_name, employee.last_name, record_data['id'], len(pdf_bytes)
                )

            except Exception as e:
                logger.error("Failed to generate paystub for record %s: %s", record_data['id'], e)
                paystub_errors.append(f"Record {record_data['id']}: {str(e)}")

        if paystub_errors:
            error_summary = f"Failed to generate {len(paystub_errors)} paystub(s). "
            error_summary += "Cannot approve payroll run until all paystubs are generated. "
            error_summary += f"Errors: {'; '.join(paystub_errors[:5])}"
            if len(paystub_errors) > 5:
                error_summary += f" ... and {len(paystub_errors) - 5} more"
            raise ValueError(error_summary)

        # Update vacation balance for accrual method employees (+accrued -paid)
        await self._update_vacation_balances(records)

        update_data: dict[str, Any] = {
            "status": "approved",
            "approved_at": datetime.now().isoformat(),
        }
        if approved_by:
            update_data["approved_by"] = approved_by

        update_result = self.supabase.table("payroll_runs").update(
            update_data
        ).eq("id", str(run_id)).execute()

        if not update_result.data or len(update_result.data) == 0:
            raise ValueError("Failed to update payroll run status")

        # Update next_period_end for all affected pay groups
        pay_group_updates: dict[str, str] = {}
        for record_data in records:
            pay_group_data = record_data["employees"].get("pay_groups")
            if pay_group_data:
                pg_id = pay_group_data["id"]
                if pg_id not in pay_group_updates:
                    pay_group_updates[pg_id] = pay_group_data.get("pay_frequency", "bi_weekly")

        current_period_end = datetime.strptime(run["period_end"], "%Y-%m-%d").date()
        for pg_id, pay_frequency in pay_group_updates.items():
            next_period_end = calculate_next_period_end(current_period_end, pay_frequency)
            self.supabase.table("pay_groups").update({
                "next_period_end": next_period_end.strftime("%Y-%m-%d")
            }).eq("id", pg_id).execute()
            logger.info("Updated pay_group %s next_period_end to %s", pg_id, next_period_end)

        return {
            **update_result.data[0],
            "paystubs_generated": paystubs_generated,
        }

    async def send_paystubs(self, run_id: UUID) -> dict[str, Any]:
        """Send paystub emails to all employees.

        Returns:
            Dict with 'sent' count and optional 'errors' list

        Raises:
            ValueError: If run is not in approved status
        """
        run = await self._get_run(run_id)
        if not run:
            raise ValueError("Payroll run not found")

        if run["status"] != "approved":
            raise ValueError(
                f"Cannot send paystubs: payroll run is in '{run['status']}' status, "
                "not 'approved'"
            )

        records_result = self.supabase.table("payroll_records").select(
            """
            id, employee_id, paystub_storage_key,
            employees!inner (id, first_name, last_name, email)
            """
        ).eq("payroll_run_id", str(run_id)).eq(
            "user_id", self.user_id
        ).eq("company_id", self.company_id).execute()

        records = records_result.data or []
        if not records:
            raise ValueError("No records found for payroll run")

        sent_count = 0
        sent_record_ids: list[str] = []
        send_errors: list[str] = []

        for record in records:
            try:
                storage_key = record.get("paystub_storage_key")
                if not storage_key:
                    send_errors.append(f"Record {record['id']}: paystub not generated")
                    continue

                employee = record.get("employees", {})
                email = employee.get("email")
                if not email:
                    send_errors.append(f"Record {record['id']}: employee has no email")
                    continue

                # TODO: Integrate actual email service
                logger.info(
                    f"Would send paystub to {email} for employee "
                    f"{employee.get('first_name')} {employee.get('last_name')}"
                )

                self.supabase.table("payroll_records").update({
                    "paystub_sent_at": datetime.now().isoformat(),
                }).eq("id", record["id"]).execute()

                sent_count += 1
                sent_record_ids.append(record["id"])

            except Exception as e:
                logger.error("Failed to send paystub for record %s: %s", record['id'], e)
                send_errors.append(f"Record {record['id']}: {str(e)}")

        return {
            "sent": sent_count,
            "sent_record_ids": sent_record_ids,
            "errors": send_errors if send_errors else None,
        }

    async def create_or_get_run(self, pay_date: str) -> dict[str, Any]:
        """Create a new draft payroll run or get existing one for a pay date.

        DEPRECATED: Use create_or_get_run_by_period_end() instead.
        This method converts pay_date to period_end (pay_date - 6 days for SK)
        and delegates to the new method.

        Returns:
            Dict with 'run', 'created' bool, and 'records_count'
        """
        # Convert pay_date to period_end (assuming SK: pay_date = period_end + 6)
        pay_date_obj = datetime.strptime(pay_date, "%Y-%m-%d").date()
        period_end = pay_date_obj - timedelta(days=6)
        return await self.create_or_get_run_by_period_end(period_end.strftime("%Y-%m-%d"))

    async def create_or_get_run_by_period_end(self, period_end: str) -> dict[str, Any]:
        """Create a new draft payroll run or get existing one for a period end.

        This is the new entry point that uses period_end as the primary identifier.
        Pay date is auto-calculated based on province regulations.

        Returns:
            Dict with 'run', 'created' bool, and 'records_count'
        """
        # Check if run already exists for this period_end
        existing_result = self.supabase.table("payroll_runs").select("*").eq(
            "user_id", self.user_id
        ).eq("company_id", self.company_id).eq("period_end", period_end).execute()

        if existing_result.data and len(existing_result.data) > 0:
            return {
                "run": existing_result.data[0],
                "created": False,
                "records_count": 0,
            }

        # Get pay groups with matching next_period_end
        pay_groups_result = self.supabase.table("pay_groups").select(
            "id, name, pay_frequency, employment_type, group_benefits"
        ).eq("next_period_end", period_end).execute()

        pay_groups = pay_groups_result.data or []
        if not pay_groups:
            raise ValueError(f"No pay groups found with period end {period_end}")

        pay_group_ids = [pg["id"] for pg in pay_groups]
        pay_group_map = {pg["id"]: pg for pg in pay_groups}

        # Get all active employees
        employees_result = self.supabase.table("employees").select(
            "id, first_name, last_name, province_of_employment, pay_group_id, "
            "annual_salary, hourly_rate, federal_additional_claims, provincial_additional_claims, "
            "is_cpp_exempt, is_ei_exempt, cpp2_exempt, vacation_config"
        ).eq("user_id", self.user_id).eq("company_id", self.company_id).in_(
            "pay_group_id", pay_group_ids
        ).is_("termination_date", "null").execute()

        employees = employees_result.data or []
        if not employees:
            raise ValueError("No active employees found for these pay groups")

        # Parse period_end and calculate dates
        period_end_obj = datetime.strptime(period_end, "%Y-%m-%d").date()
        pay_frequency = pay_groups[0].get("pay_frequency", "bi_weekly")

        # Calculate period_start based on frequency
        if pay_frequency == "monthly":
            period_start = period_end_obj.replace(day=1)
        elif pay_frequency == "semi_monthly":
            if period_end_obj.day <= 15:
                period_start = period_end_obj.replace(day=1)
            else:
                period_start = period_end_obj.replace(day=16)
        elif pay_frequency == "weekly":
            period_start = period_end_obj - timedelta(days=6)
        else:  # bi_weekly
            period_start = period_end_obj - timedelta(days=13)

        # Calculate pay_date from period_end (default: +6 days for SK)
        pay_date_obj = calculate_pay_date(period_end_obj, "SK")

        # Create the payroll run
        run_insert_result = self.supabase.table("payroll_runs").insert({
            "user_id": self.user_id,
            "company_id": self.company_id,
            "period_start": period_start.strftime("%Y-%m-%d"),
            "period_end": period_end,
            "pay_date": pay_date_obj.strftime("%Y-%m-%d"),
            "status": "draft",
            "total_employees": len(employees),
            "total_gross": 0,
            "total_cpp_employee": 0,
            "total_cpp_employer": 0,
            "total_ei_employee": 0,
            "total_ei_employer": 0,
            "total_federal_tax": 0,
            "total_provincial_tax": 0,
            "total_net_pay": 0,
            "total_employer_cost": 0,
        }).execute()

        if not run_insert_result.data or len(run_insert_result.data) == 0:
            raise ValueError("Failed to create payroll run")

        run = run_insert_result.data[0]
        run_id = run["id"]

        tax_year = extract_year_from_date(period_end)

        _, results = await self._create_records_for_employees(
            UUID(run_id), employees, pay_group_map, tax_year, pay_date_obj
        )

        if results:
            total_gross = sum(float(r.total_gross) for r in results)
            total_cpp_employee = sum(float(r.cpp_total) for r in results)
            total_cpp_employer = sum(float(r.cpp_employer) for r in results)
            total_ei_employee = sum(float(r.ei_employee) for r in results)
            total_ei_employer = sum(float(r.ei_employer) for r in results)
            total_federal_tax = sum(float(r.federal_tax) for r in results)
            total_provincial_tax = sum(float(r.provincial_tax) for r in results)
            total_net_pay = sum(float(r.net_pay) for r in results)
            total_employer_cost = total_cpp_employer + total_ei_employer

            self.supabase.table("payroll_runs").update({
                "total_gross": total_gross,
                "total_cpp_employee": total_cpp_employee,
                "total_cpp_employer": total_cpp_employer,
                "total_ei_employee": total_ei_employee,
                "total_ei_employer": total_ei_employer,
                "total_federal_tax": total_federal_tax,
                "total_provincial_tax": total_provincial_tax,
                "total_net_pay": total_net_pay,
                "total_employer_cost": total_employer_cost,
            }).eq("id", run_id).execute()

            run = await self._get_run(UUID(run_id)) or run

        return {
            "run": run,
            "created": True,
            "records_count": len(employees),
        }

    async def _update_vacation_balances(self, records: list[dict[str, Any]]) -> None:
        """Update employee vacation_balance: +accrued -paid.

        Only processes employees with payout_method = "accrual".
        Called during payroll run approval.

        Args:
            records: List of payroll records with employee data
        """
        for record in records:
            employee_data = record.get("employees", {})
            vacation_config = employee_data.get("vacation_config") or {}

            # Only process accrual method employees
            if vacation_config.get("payout_method") != "accrual":
                continue

            vacation_accrued = Decimal(str(record.get("vacation_accrued", 0)))
            vacation_pay_paid = Decimal(str(record.get("vacation_pay_paid", 0)))

            # Skip if no changes
            if vacation_accrued == 0 and vacation_pay_paid == 0:
                continue

            current_balance = Decimal(str(employee_data.get("vacation_balance", 0)))
            new_balance = max(current_balance + vacation_accrued - vacation_pay_paid, Decimal("0"))

            self.supabase.table("employees").update({
                "vacation_balance": float(new_balance)
            }).eq("id", employee_data["id"]).execute()

            logger.info(
                "Updated vacation balance for employee %s %s: $%.2f -> $%.2f (accrued: $%.2f, paid: $%.2f)",
                employee_data.get("first_name"),
                employee_data.get("last_name"),
                float(current_balance),
                float(new_balance),
                float(vacation_accrued),
                float(vacation_pay_paid),
            )

    def _validate_vacation_balances(self, records: list[dict[str, Any]]) -> list[str]:
        """Validate vacation balances are sufficient for all employees.

        Returns:
            List of error messages for employees with insufficient balance
        """
        errors: list[str] = []

        for record in records:
            employee_data = record.get("employees", {})
            vacation_config = employee_data.get("vacation_config") or {}

            # Only validate accrual method employees
            if vacation_config.get("payout_method") != "accrual":
                continue

            vacation_pay_paid = Decimal(str(record.get("vacation_pay_paid", 0)))
            if vacation_pay_paid <= 0:
                continue

            current_balance = Decimal(str(employee_data.get("vacation_balance", 0)))
            if vacation_pay_paid > current_balance:
                name = f"{employee_data.get('first_name')} {employee_data.get('last_name')}"
                errors.append(
                    f"{name}: balance ${current_balance:.2f}, requested ${vacation_pay_paid:.2f}"
                )

        return errors
