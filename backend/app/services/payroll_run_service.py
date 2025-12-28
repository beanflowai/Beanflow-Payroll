"""
Payroll Run Service - Manages payroll run lifecycle and operations

Provides:
- Record updates in draft state
- Recalculation of payroll deductions
- Status transitions (draft -> pending_approval)
"""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.core.supabase_client import get_supabase_client
from app.models.payroll import (
    Company,
    Employee,
    GroupBenefits,
    PayFrequency,
    PayGroup,
    PayrollRecord,
    PayrollRun,
    Province,
)
from app.services.payroll import (
    EmployeePayrollInput,
    PayrollEngine,
    PaystubDataBuilder,
    PaystubGenerator,
)
from app.services.payroll.tax_tables import get_province_config

logger = logging.getLogger(__name__)

# 2025 Federal Basic Personal Amount (default claim amount)
DEFAULT_FEDERAL_CLAIM_2025 = Decimal("16129")

# Payroll run statuses that count as "completed" for YTD calculations
COMPLETED_RUN_STATUSES = ["approved", "paid"]

# Default fallback year if date parsing fails
DEFAULT_TAX_YEAR = 2025


def _extract_year_from_date(date_str: str, default: int = DEFAULT_TAX_YEAR) -> int:
    """Safely extract year from a date string (YYYY-MM-DD format).

    Args:
        date_str: Date string in YYYY-MM-DD format
        default: Default year to return if parsing fails

    Returns:
        The extracted year, or default if parsing fails
    """
    if not date_str or not isinstance(date_str, str):
        return default
    try:
        # Ensure we have at least 4 characters and they're digits
        if len(date_str) >= 4 and date_str[:4].isdigit():
            return int(date_str[:4])
        return default
    except (ValueError, TypeError):
        return default


def get_provincial_bpa(
    province_code: str,
    year: int = 2025,
    pay_date: date | None = None
) -> Decimal:
    """Get the Basic Personal Amount for a province from tax tables.

    Args:
        province_code: Two-letter province code (e.g., "ON", "SK")
        year: Tax year (default: 2025)
        pay_date: Pay date for edition selection (SK, PE have different BPA in Jan vs Jul)

    Returns:
        Provincial BPA as Decimal
    """
    try:
        config = get_province_config(province_code, year, pay_date)
        return Decimal(str(config["bpa"]))
    except Exception as e:
        logger.warning(f"Failed to get BPA for {province_code}: {e}, using fallback")
        # Fallback to ON default if lookup fails
        return Decimal("12747")


class PayrollRunService:
    """Service for payroll run operations"""

    def __init__(self, user_id: str, ledger_id: str):
        """Initialize service with user context"""
        self.user_id = user_id
        self.ledger_id = ledger_id
        self.supabase = get_supabase_client()

    def _get_prior_ytd_for_employees(
        self, employee_ids: list[str], current_run_id: str, year: int = DEFAULT_TAX_YEAR
    ) -> dict[str, dict[str, Decimal]]:
        """
        Get prior YTD totals for employees from completed payroll runs.

        This queries all approved/paid payroll_records for each employee
        in the given year, EXCLUDING the current run, and sums their totals.

        Args:
            employee_ids: List of employee IDs to query
            current_run_id: The current payroll run ID to exclude
            year: The tax year (default from DEFAULT_TAX_YEAR)

        Returns:
            Dict mapping employee_id -> {
                'ytd_gross': Decimal,
                'ytd_cpp': Decimal,
                'ytd_ei': Decimal,
                'ytd_federal_tax': Decimal,
                'ytd_provincial_tax': Decimal,
            }
        """
        if not employee_ids:
            return {}

        # Define year boundaries for efficient database filtering
        year_start = f"{year}-01-01"
        year_end = f"{year}-12-31"

        # Query all completed payroll records for these employees in the year
        # Join with payroll_runs to filter by status and year at database level
        result = self.supabase.table("payroll_records").select(
            """
            employee_id,
            gross_regular,
            gross_overtime,
            holiday_pay,
            holiday_premium_pay,
            vacation_pay_paid,
            other_earnings,
            cpp_employee,
            cpp_additional,
            ei_employee,
            federal_tax,
            provincial_tax,
            payroll_runs!inner (
                id,
                pay_date,
                status
            )
            """
        ).eq("user_id", self.user_id).eq("ledger_id", self.ledger_id).in_(
            "employee_id", employee_ids
        ).in_(
            "payroll_runs.status", COMPLETED_RUN_STATUSES
        ).gte(
            "payroll_runs.pay_date", year_start
        ).lte(
            "payroll_runs.pay_date", year_end
        ).neq(
            "payroll_run_id", current_run_id
        ).execute()

        # Initialize YTD dict for all employees
        ytd_data: dict[str, dict[str, Decimal]] = {}
        for emp_id in employee_ids:
            ytd_data[emp_id] = {
                "ytd_gross": Decimal("0"),
                "ytd_cpp": Decimal("0"),
                "ytd_ei": Decimal("0"),
                "ytd_federal_tax": Decimal("0"),
                "ytd_provincial_tax": Decimal("0"),
            }

        # Sum up prior records (year filtering already done at database level)
        for record in result.data or []:
            emp_id = record["employee_id"]
            if emp_id not in ytd_data:
                continue

            # Calculate total gross for this record
            total_gross = (
                Decimal(str(record.get("gross_regular", 0)))
                + Decimal(str(record.get("gross_overtime", 0)))
                + Decimal(str(record.get("holiday_pay", 0)))
                + Decimal(str(record.get("holiday_premium_pay", 0)))
                + Decimal(str(record.get("vacation_pay_paid", 0)))
                + Decimal(str(record.get("other_earnings", 0)))
            )

            # Sum CPP (base + additional)
            total_cpp = (
                Decimal(str(record.get("cpp_employee", 0)))
                + Decimal(str(record.get("cpp_additional", 0)))
            )

            ytd_data[emp_id]["ytd_gross"] += total_gross
            ytd_data[emp_id]["ytd_cpp"] += total_cpp
            ytd_data[emp_id]["ytd_ei"] += Decimal(str(record.get("ei_employee", 0)))
            ytd_data[emp_id]["ytd_federal_tax"] += Decimal(
                str(record.get("federal_tax", 0))
            )
            ytd_data[emp_id]["ytd_provincial_tax"] += Decimal(
                str(record.get("provincial_tax", 0))
            )

        return ytd_data

    def _calculate_benefits_deduction(
        self, group_benefits: dict[str, Any]
    ) -> Decimal:
        """Calculate total employee benefits deduction from group benefits config.

        This calculates the post-tax employee deduction amount for all enabled benefits.
        """
        if not group_benefits.get("enabled"):
            return Decimal("0")

        benefits_deduction = Decimal("0")

        # Health
        health = group_benefits.get("health") or {}
        if health.get("enabled"):
            benefits_deduction += Decimal(str(health.get("employeeDeduction", 0)))

        # Dental
        dental = group_benefits.get("dental") or {}
        if dental.get("enabled"):
            benefits_deduction += Decimal(str(dental.get("employeeDeduction", 0)))

        # Life Insurance
        life = group_benefits.get("lifeInsurance") or {}
        if life.get("enabled"):
            benefits_deduction += Decimal(str(life.get("employeeDeduction", 0)))

        # Vision
        vision = group_benefits.get("vision") or {}
        if vision.get("enabled"):
            benefits_deduction += Decimal(str(vision.get("employeeDeduction", 0)))

        # Disability
        disability = group_benefits.get("disability") or {}
        if disability.get("enabled"):
            benefits_deduction += Decimal(str(disability.get("employeeDeduction", 0)))

        return benefits_deduction

    def _calculate_taxable_benefits(
        self, group_benefits: dict[str, Any]
    ) -> Decimal:
        """Calculate taxable benefits that are pensionable but NOT insurable.

        In Canada, only employer-paid life insurance premiums have this special
        treatment (pensionable for CPP, but NOT insurable for EI).

        Other benefit types (health, dental, vision, disability) are generally
        NOT taxable in Canada. If they were taxable, they would be both
        pensionable AND insurable, but that's extremely rare.

        We only check lifeInsurance.isTaxable to avoid incorrect CPP/EI
        calculations for other benefit types.
        """
        if not group_benefits.get("enabled"):
            return Decimal("0")

        taxable_benefits = Decimal("0")

        # Only life insurance has the special "pensionable but not insurable" treatment
        # Employer-paid life insurance is ALWAYS a taxable benefit in Canada (CRA rule)
        life = group_benefits.get("lifeInsurance") or {}
        if life.get("enabled"):
            employer_contribution = Decimal(str(life.get("employerContribution", 0)))
            if employer_contribution > 0:
                taxable_benefits += employer_contribution

        return taxable_benefits

    async def get_run(self, run_id: UUID) -> dict[str, Any] | None:
        """Get a payroll run by ID

        Note: RLS policies using auth.uid() will automatically filter by user.
        The explicit user_id/ledger_id filters provide defense-in-depth.
        """
        result = self.supabase.table("payroll_runs").select("*").eq(
            "id", str(run_id)
        ).eq("user_id", self.user_id).eq("ledger_id", self.ledger_id).execute()

        if result.data and len(result.data) > 0:
            return result.data[0]
        return None

    async def get_run_records(self, run_id: UUID) -> list[dict[str, Any]]:
        """Get all records for a payroll run with employee info"""
        result = self.supabase.table("payroll_records").select(
            """
            *,
            employees!inner (
                id,
                first_name,
                last_name,
                province_of_employment,
                pay_frequency,
                annual_salary,
                hourly_rate,
                federal_claim_amount,
                provincial_claim_amount,
                is_cpp_exempt,
                is_ei_exempt,
                cpp2_exempt,
                vacation_config,
                pay_group_id,
                pay_groups (
                    id,
                    name,
                    pay_frequency,
                    employment_type,
                    group_benefits
                )
            )
            """
        ).eq("payroll_run_id", str(run_id)).eq("user_id", self.user_id).eq(
            "ledger_id", self.ledger_id
        ).execute()

        return result.data or []

    async def update_record(
        self, run_id: UUID, record_id: UUID, input_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Update a payroll record's input_data in draft state.

        Args:
            run_id: The payroll run ID
            record_id: The payroll record ID
            input_data: New input data (regularHours, overtimeHours, leaveEntries, etc.)

        Returns:
            Updated record data

        Raises:
            ValueError: If run is not in draft status
        """
        # Verify run is in draft status
        run = await self.get_run(run_id)
        if not run:
            raise ValueError("Payroll run not found")

        if run["status"] != "draft":
            raise ValueError(
                f"Cannot update record: payroll run is in '{run['status']}' status, "
                "not 'draft'"
            )

        # Get current record
        record_result = self.supabase.table("payroll_records").select("*").eq(
            "id", str(record_id)
        ).eq("payroll_run_id", str(run_id)).eq("user_id", self.user_id).execute()

        if not record_result.data or len(record_result.data) == 0:
            raise ValueError("Payroll record not found")

        current_record = record_result.data[0]

        # Merge with existing input_data
        existing_input_data = current_record.get("input_data") or {}
        merged_input_data = {**existing_input_data, **input_data}

        # Update the record
        update_result = self.supabase.table("payroll_records").update({
            "input_data": merged_input_data,
            "is_modified": True
        }).eq("id", str(record_id)).execute()

        if not update_result.data or len(update_result.data) == 0:
            raise ValueError("Failed to update payroll record")

        return update_result.data[0]

    async def recalculate_run(self, run_id: UUID) -> dict[str, Any]:
        """
        Recalculate all records in a draft payroll run.

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
        run = await self.get_run(run_id)
        if not run:
            raise ValueError("Payroll run not found")

        if run["status"] != "draft":
            raise ValueError(
                f"Cannot recalculate: payroll run is in '{run['status']}' status, "
                "not 'draft'"
            )

        # Get all records with employee info
        records = await self.get_run_records(run_id)
        if not records:
            raise ValueError("No records found for payroll run")

        # Extract year from pay_date for YTD calculations
        pay_date_str = run.get("pay_date", "")
        tax_year = _extract_year_from_date(pay_date_str)

        # Convert pay_date string to date object for tax edition selection
        # (2025: before July 1 uses 15% rate, after uses 14% rate)
        from datetime import datetime
        pay_date_obj = datetime.strptime(pay_date_str, "%Y-%m-%d").date() if pay_date_str else None

        # Get prior YTD data from completed payroll runs (excluding current run)
        employee_ids = [record["employee_id"] for record in records]
        prior_ytd_data = self._get_prior_ytd_for_employees(
            employee_ids, str(run_id), year=tax_year
        )

        # Build calculation inputs from input_data
        calculation_inputs: list[EmployeePayrollInput] = []
        record_map: dict[str, dict[str, Any]] = {}  # employee_id -> record

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

            # Calculate taxable benefits (employer contributions where isTaxable=True)
            # These are pensionable but NOT insurable for EI
            taxable_benefits_pensionable = self._calculate_taxable_benefits(group_benefits)

            # Calculate employee benefits deduction (post-tax deductions)
            # This is passed to the engine so it's included in net_pay calculation
            benefits_deduction = self._calculate_benefits_deduction(group_benefits)

            # Calculate gross pay from input_data
            gross_regular, gross_overtime = self._calculate_gross_from_input(
                employee, input_data, pay_frequency_str
            )

            # Calculate vacation pay for pay_as_you_go method
            # For accrual method, vacation is accumulated but not added to gross
            # For pay_as_you_go, vacation pay is added to each paycheck
            vacation_config = employee.get("vacation_config") or {}
            payout_method = vacation_config.get("payout_method", "accrual")
            vacation_pay_for_gross = Decimal("0")

            if payout_method == "pay_as_you_go":
                vacation_rate = Decimal(str(vacation_config.get("vacation_rate", "0.04")))
                # Vacation pay is based on regular + overtime earnings (not including vacation itself)
                base_earnings = gross_regular + gross_overtime
                vacation_pay_for_gross = base_earnings * vacation_rate

            # Calculate additional earnings from input_data
            holiday_pay = Decimal("0")
            other_earnings = Decimal("0")

            # Holiday work entries
            if input_data.get("holidayWorkEntries"):
                hourly_rate = Decimal(str(employee.get("hourly_rate") or 0))
                for hw in input_data["holidayWorkEntries"]:
                    hours = Decimal(str(hw.get("hoursWorked", 0)))
                    holiday_pay += hours * hourly_rate * Decimal("1.5")

            # Adjustments
            if input_data.get("adjustments"):
                for adj in input_data["adjustments"]:
                    amount = Decimal(str(adj.get("amount", 0)))
                    if adj.get("type") == "deduction":
                        other_earnings -= amount
                    else:
                        other_earnings += amount

            # Build calculation input
            # Determine claim amounts (use employee values or province-specific BPA)
            province_code = employee["province_of_employment"]
            federal_claim = Decimal(
                str(employee.get("federal_claim_amount"))
            ) if employee.get("federal_claim_amount") is not None else DEFAULT_FEDERAL_CLAIM_2025
            provincial_claim = Decimal(
                str(employee.get("provincial_claim_amount"))
            ) if employee.get("provincial_claim_amount") is not None else get_provincial_bpa(
                province_code, tax_year, pay_date_obj
            )

            # DEBUG: Log claim amounts for each employee
            logger.info(
                f"PAYROLL DEBUG: Employee {employee.get('first_name')} {employee.get('last_name')} "
                f"(province={province_code}): "
                f"federal_claim_amount={employee.get('federal_claim_amount')} -> {federal_claim}, "
                f"provincial_claim_amount={employee.get('provincial_claim_amount')} -> {provincial_claim}, "
                f"gross={gross_regular + gross_overtime}"
            )

            # Get prior YTD for this employee (from completed pay runs only)
            emp_prior_ytd = prior_ytd_data.get(record["employee_id"], {})

            calc_input = EmployeePayrollInput(
                employee_id=record["employee_id"],
                province=Province(employee["province_of_employment"]),
                pay_frequency=pay_frequency,
                gross_regular=gross_regular,
                gross_overtime=gross_overtime,
                holiday_pay=holiday_pay,
                # Vacation pay for pay_as_you_go method (added to gross)
                vacation_pay=vacation_pay_for_gross,
                other_earnings=other_earnings,
                federal_claim_amount=federal_claim,
                provincial_claim_amount=provincial_claim,
                is_cpp_exempt=employee.get("is_cpp_exempt", False),
                is_ei_exempt=employee.get("is_ei_exempt", False),
                cpp2_exempt=employee.get("cpp2_exempt", False),
                # Taxable benefits (employer contributions where isTaxable=True)
                taxable_benefits_pensionable=taxable_benefits_pensionable,
                # Employee benefits deduction (post-tax, included in net_pay calc)
                other_deductions=benefits_deduction,
                # Pay date for tax edition selection (2025: Jan=15%, Jul=14%)
                pay_date=pay_date_obj,
                # YTD values from PRIOR completed payroll runs (not current record)
                # This prevents double-counting when recalculating
                ytd_gross=emp_prior_ytd.get("ytd_gross", Decimal("0")),
                ytd_cpp_base=emp_prior_ytd.get("ytd_cpp", Decimal("0")),
                ytd_ei=emp_prior_ytd.get("ytd_ei", Decimal("0")),
                ytd_federal_tax=emp_prior_ytd.get("ytd_federal_tax", Decimal("0")),
                ytd_provincial_tax=emp_prior_ytd.get("ytd_provincial_tax", Decimal("0")),
            )
            calculation_inputs.append(calc_input)
            record_map[record["employee_id"]] = record

        # Calculate using PayrollEngine
        engine = PayrollEngine(year=tax_year)
        results = engine.calculate_batch(calculation_inputs)

        # Update each record with new calculation results
        for result in results:
            record = record_map[result.employee_id]
            input_data = record.get("input_data") or {}
            employee = record["employees"]

            # Calculate vacation accrued (only for accrual method, not pay-as-you-go)
            vacation_config = employee.get("vacation_config") or {}
            payout_method = vacation_config.get("payout_method", "accrual")
            if payout_method == "accrual":
                vacation_rate = Decimal(str(vacation_config.get("vacation_rate", "0.04")))
                # For accrual: calculate based on base earnings (excluding vacation_pay itself)
                base_earnings = (
                    result.gross_regular + result.gross_overtime +
                    result.holiday_pay + result.other_earnings
                )
                vacation_accrued = base_earnings * vacation_rate
            else:
                # pay_as_you_go: vacation is already included in gross via vacation_pay field
                vacation_accrued = Decimal("0")

            # other_deductions already includes benefits (passed to engine earlier)
            self.supabase.table("payroll_records").update({
                "gross_regular": float(result.gross_regular),
                "gross_overtime": float(result.gross_overtime),
                "holiday_pay": float(result.holiday_pay),
                "vacation_pay_paid": float(result.vacation_pay),
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
                "vacation_accrued": float(vacation_accrued),
                "is_modified": False,
                # Update hours from input_data
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

        # Return updated run
        return await self.get_run(run_id) or {}

    async def finalize_run(self, run_id: UUID) -> dict[str, Any]:
        """
        Finalize a draft payroll run, transitioning to pending_approval.

        1. Verifies run is in draft status
        2. Verifies no records have is_modified = True
        3. Updates status to pending_approval

        Returns:
            Updated payroll run data

        Raises:
            ValueError: If run is not in draft or has modified records
        """
        # Verify run is in draft status
        run = await self.get_run(run_id)
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

        # Update status to pending_approval
        update_result = self.supabase.table("payroll_runs").update({
            "status": "pending_approval"
        }).eq("id", str(run_id)).execute()

        if not update_result.data or len(update_result.data) == 0:
            raise ValueError("Failed to update payroll run status")

        return update_result.data[0]

    async def check_has_modified_records(self, run_id: UUID) -> bool:
        """Check if any records in the run have is_modified = True"""
        result = self.supabase.table("payroll_records").select("id").eq(
            "payroll_run_id", str(run_id)
        ).eq("is_modified", True).limit(1).execute()

        return bool(result.data and len(result.data) > 0)

    async def approve_run(
        self, run_id: UUID, approved_by: str | None = None
    ) -> dict[str, Any]:
        """
        Approve a pending_approval payroll run.

        1. Verifies run is in pending_approval status
        2. Generates paystub PDFs for all records
        3. Updates status to approved
        4. Records approval timestamp and approver

        Note: Paystub storage to DO Spaces will be implemented in Phase 3b.
        Currently, paystubs are generated but not stored.

        Args:
            run_id: The payroll run ID
            approved_by: Optional identifier of the approver

        Returns:
            Updated payroll run data with paystubs_generated count

        Raises:
            ValueError: If run is not in pending_approval status
        """
        from datetime import datetime as dt

        # Verify run is in pending_approval status
        run = await self.get_run(run_id)
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
                id,
                first_name,
                last_name,
                email,
                sin_encrypted,
                province_of_employment,
                pay_frequency,
                employment_type,
                annual_salary,
                hourly_rate,
                federal_claim_amount,
                provincial_claim_amount,
                is_cpp_exempt,
                is_ei_exempt,
                cpp2_exempt,
                hire_date,
                termination_date,
                vacation_config,
                vacation_balance,
                address_street,
                address_city,
                address_postal_code,
                occupation,
                company_id,
                pay_group_id,
                companies (
                    id,
                    company_name,
                    business_number,
                    payroll_account_number,
                    province,
                    address_street,
                    address_city,
                    address_postal_code,
                    remitter_type,
                    auto_calculate_deductions,
                    send_paystub_emails
                ),
                pay_groups (
                    id,
                    name,
                    description,
                    pay_frequency,
                    employment_type,
                    next_pay_date,
                    period_start_day,
                    leave_enabled,
                    statutory_defaults,
                    overtime_policy,
                    wcb_config,
                    group_benefits,
                    custom_deductions
                )
            )
            """
        ).eq("payroll_run_id", str(run_id)).eq(
            "user_id", self.user_id
        ).eq("ledger_id", self.ledger_id).execute()

        records = records_result.data or []
        if not records:
            raise ValueError("No records found for payroll run")

        # Build PayrollRun model from run data
        payroll_run = self._build_payroll_run_model(run)

        # Initialize services
        paystub_builder = PaystubDataBuilder()
        paystub_generator = PaystubGenerator()

        paystubs_generated = 0
        paystub_errors: list[str] = []

        for record_data in records:
            try:
                employee_data = record_data["employees"]
                company_data = employee_data.get("companies")
                pay_group_data = employee_data.get("pay_groups")

                # Build models from data
                employee = self._build_employee_model(employee_data)
                company = self._build_company_model(company_data) if company_data else None
                pay_group = self._build_pay_group_model(pay_group_data) if pay_group_data else None
                payroll_record = self._build_payroll_record_model(record_data)

                if not company:
                    logger.warning(
                        f"Skipping paystub for record {record_data['id']}: no company data"
                    )
                    paystub_errors.append(
                        f"Record {record_data['id']}: missing company data"
                    )
                    continue

                # Get prior YTD records for this employee (for YTD calculations)
                # Note: This is for accurate YTD benefits calculation
                ytd_records = await self._get_ytd_records_for_employee(
                    record_data["employee_id"],
                    str(run_id),
                    int(run["pay_date"][:4]),  # Extract year from pay_date
                )

                # Generate masked SIN (last 3 digits visible)
                # Note: SIN decryption would be needed here for real implementation
                # For now, use placeholder since we don't have the encryption key in scope
                masked_sin = "***-***-***"  # Placeholder

                # Build PaystubData
                paystub_data = paystub_builder.build(
                    record=payroll_record,
                    employee=employee,
                    payroll_run=payroll_run,
                    pay_group=pay_group,
                    company=company,
                    ytd_records=ytd_records,
                    masked_sin=masked_sin,
                )

                # Generate PDF bytes
                pdf_bytes = paystub_generator.generate_paystub_bytes(paystub_data)

                # TODO: Phase 3b - Store to DO Spaces
                # storage_key = await self._store_paystub_to_spaces(
                #     pdf_bytes, run_id, record_data["id"]
                # )

                # Update record with paystub info (storage key placeholder for now)
                self.supabase.table("payroll_records").update({
                    "paystub_generated_at": dt.now().isoformat(),
                    # "paystub_storage_key": storage_key,  # Phase 3b
                }).eq("id", record_data["id"]).execute()

                paystubs_generated += 1
                logger.info(
                    f"Generated paystub for employee {employee.first_name} {employee.last_name} "
                    f"(record {record_data['id']}), size: {len(pdf_bytes)} bytes"
                )

            except Exception as e:
                logger.error(
                    f"Failed to generate paystub for record {record_data['id']}: {e}"
                )
                paystub_errors.append(f"Record {record_data['id']}: {str(e)}")

        # Update run status to approved
        update_data: dict[str, Any] = {
            "status": "approved",
            "approved_at": dt.now().isoformat(),
        }
        if approved_by:
            update_data["approved_by"] = approved_by

        update_result = self.supabase.table("payroll_runs").update(
            update_data
        ).eq("id", str(run_id)).execute()

        if not update_result.data or len(update_result.data) == 0:
            raise ValueError("Failed to update payroll run status")

        return {
            **update_result.data[0],
            "paystubs_generated": paystubs_generated,
            "paystub_errors": paystub_errors if paystub_errors else None,
        }

    async def _get_ytd_records_for_employee(
        self,
        employee_id: str,
        current_run_id: str,
        year: int,
    ) -> list[PayrollRecord]:
        """Get prior YTD payroll records for an employee."""
        year_start = f"{year}-01-01"
        year_end = f"{year}-12-31"

        result = self.supabase.table("payroll_records").select(
            """
            *,
            payroll_runs!inner (
                id,
                pay_date,
                status
            )
            """
        ).eq("employee_id", employee_id).in_(
            "payroll_runs.status", COMPLETED_RUN_STATUSES
        ).gte(
            "payroll_runs.pay_date", year_start
        ).lte(
            "payroll_runs.pay_date", year_end
        ).neq(
            "payroll_run_id", current_run_id
        ).execute()

        records: list[PayrollRecord] = []
        for r in result.data or []:
            records.append(self._build_payroll_record_model(r))

        return records

    def _build_payroll_run_model(self, data: dict[str, Any]) -> PayrollRun:
        """Build PayrollRun model from database row."""
        from datetime import datetime as dt

        return PayrollRun(
            id=UUID(data["id"]),
            user_id=data["user_id"],
            ledger_id=data["ledger_id"],
            period_start=date.fromisoformat(data["period_start"]),
            period_end=date.fromisoformat(data["period_end"]),
            pay_date=date.fromisoformat(data["pay_date"]),
            status=data.get("status", "draft"),
            total_employees=data.get("total_employees", 0),
            total_gross=Decimal(str(data.get("total_gross", 0))),
            total_cpp_employee=Decimal(str(data.get("total_cpp_employee", 0))),
            total_cpp_employer=Decimal(str(data.get("total_cpp_employer", 0))),
            total_ei_employee=Decimal(str(data.get("total_ei_employee", 0))),
            total_ei_employer=Decimal(str(data.get("total_ei_employer", 0))),
            total_federal_tax=Decimal(str(data.get("total_federal_tax", 0))),
            total_provincial_tax=Decimal(str(data.get("total_provincial_tax", 0))),
            total_net_pay=Decimal(str(data.get("total_net_pay", 0))),
            total_employer_cost=Decimal(str(data.get("total_employer_cost", 0))),
            notes=data.get("notes"),
            approved_by=data.get("approved_by"),
            approved_at=dt.fromisoformat(data["approved_at"]) if data.get("approved_at") else None,
            created_at=dt.fromisoformat(data["created_at"]),
            updated_at=dt.fromisoformat(data["updated_at"]),
        )

    def _build_employee_model(self, data: dict[str, Any]) -> Employee:
        """Build Employee model from database row."""
        from datetime import datetime as dt
        from app.models.payroll import VacationConfig, VacationPayoutMethod

        vacation_config_data = data.get("vacation_config") or {}

        return Employee(
            id=UUID(data["id"]),
            user_id=data.get("user_id", ""),
            ledger_id=data.get("ledger_id", ""),
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data.get("email"),
            province_of_employment=Province(data["province_of_employment"]),
            pay_frequency=PayFrequency(data.get("pay_frequency", "bi_weekly")),
            employment_type=data.get("employment_type", "full_time"),
            address_street=data.get("address_street"),
            address_city=data.get("address_city"),
            address_postal_code=data.get("address_postal_code"),
            occupation=data.get("occupation"),
            annual_salary=Decimal(str(data["annual_salary"])) if data.get("annual_salary") else None,
            hourly_rate=Decimal(str(data["hourly_rate"])) if data.get("hourly_rate") else None,
            federal_claim_amount=Decimal(str(data.get("federal_claim_amount", 16129))),
            provincial_claim_amount=Decimal(str(data.get("provincial_claim_amount", 12747))),
            is_cpp_exempt=data.get("is_cpp_exempt", False),
            is_ei_exempt=data.get("is_ei_exempt", False),
            cpp2_exempt=data.get("cpp2_exempt", False),
            rrsp_per_period=Decimal(str(data.get("rrsp_per_period", 0))),
            union_dues_per_period=Decimal(str(data.get("union_dues_per_period", 0))),
            hire_date=date.fromisoformat(data["hire_date"]),
            termination_date=date.fromisoformat(data["termination_date"]) if data.get("termination_date") else None,
            vacation_config=VacationConfig(
                payout_method=VacationPayoutMethod(vacation_config_data.get("payout_method", "accrual")),
                vacation_rate=Decimal(str(vacation_config_data.get("vacation_rate", "0.04"))),
            ),
            sin_encrypted=data.get("sin_encrypted", ""),
            vacation_balance=Decimal(str(data.get("vacation_balance", 0))),
            created_at=dt.fromisoformat(data["created_at"]) if data.get("created_at") else dt.now(),
            updated_at=dt.fromisoformat(data["updated_at"]) if data.get("updated_at") else dt.now(),
        )

    def _build_company_model(self, data: dict[str, Any]) -> Company:
        """Build Company model from database row."""
        from datetime import datetime as dt
        from app.models.payroll import RemitterType

        return Company(
            id=UUID(data["id"]),
            user_id=data.get("user_id", ""),
            company_name=data["company_name"],
            business_number=data.get("business_number", "000000000"),
            payroll_account_number=data.get("payroll_account_number", "000000000RP0001"),
            province=Province(data["province"]),
            address_street=data.get("address_street"),
            address_city=data.get("address_city"),
            address_postal_code=data.get("address_postal_code"),
            remitter_type=RemitterType(data.get("remitter_type", "regular")),
            auto_calculate_deductions=data.get("auto_calculate_deductions", True),
            send_paystub_emails=data.get("send_paystub_emails", False),
            bookkeeping_ledger_id=data.get("bookkeeping_ledger_id"),
            bookkeeping_ledger_name=data.get("bookkeeping_ledger_name"),
            bookkeeping_connected_at=dt.fromisoformat(data["bookkeeping_connected_at"]) if data.get("bookkeeping_connected_at") else None,
            created_at=dt.fromisoformat(data["created_at"]) if data.get("created_at") else dt.now(),
            updated_at=dt.fromisoformat(data["updated_at"]) if data.get("updated_at") else dt.now(),
        )

    def _build_pay_group_model(self, data: dict[str, Any]) -> PayGroup:
        """Build PayGroup model from database row."""
        from datetime import datetime as dt
        from app.models.payroll import (
            BenefitConfig,
            LifeInsuranceConfig,
            OvertimePolicy,
            PeriodStartDay,
            StatutoryDefaults,
            WcbConfig,
        )

        # Parse group_benefits JSONB
        gb_data = data.get("group_benefits") or {}
        group_benefits = GroupBenefits(
            enabled=gb_data.get("enabled", False),
            health=BenefitConfig(
                enabled=gb_data.get("health", {}).get("enabled", False),
                employee_deduction=Decimal(str(gb_data.get("health", {}).get("employee_deduction", 0))),
                employer_contribution=Decimal(str(gb_data.get("health", {}).get("employer_contribution", 0))),
                is_taxable=gb_data.get("health", {}).get("is_taxable", False),
            ),
            dental=BenefitConfig(
                enabled=gb_data.get("dental", {}).get("enabled", False),
                employee_deduction=Decimal(str(gb_data.get("dental", {}).get("employee_deduction", 0))),
                employer_contribution=Decimal(str(gb_data.get("dental", {}).get("employer_contribution", 0))),
                is_taxable=gb_data.get("dental", {}).get("is_taxable", False),
            ),
            vision=BenefitConfig(
                enabled=gb_data.get("vision", {}).get("enabled", False),
                employee_deduction=Decimal(str(gb_data.get("vision", {}).get("employee_deduction", 0))),
                employer_contribution=Decimal(str(gb_data.get("vision", {}).get("employer_contribution", 0))),
                is_taxable=gb_data.get("vision", {}).get("is_taxable", False),
            ),
            life_insurance=LifeInsuranceConfig(
                enabled=gb_data.get("life_insurance", {}).get("enabled", False),
                employee_deduction=Decimal(str(gb_data.get("life_insurance", {}).get("employee_deduction", 0))),
                employer_contribution=Decimal(str(gb_data.get("life_insurance", {}).get("employer_contribution", 0))),
                is_taxable=gb_data.get("life_insurance", {}).get("is_taxable", False),
                coverage_amount=Decimal(str(gb_data.get("life_insurance", {}).get("coverage_amount", 0))),
            ),
            disability=BenefitConfig(
                enabled=gb_data.get("disability", {}).get("enabled", False),
                employee_deduction=Decimal(str(gb_data.get("disability", {}).get("employee_deduction", 0))),
                employer_contribution=Decimal(str(gb_data.get("disability", {}).get("employer_contribution", 0))),
                is_taxable=gb_data.get("disability", {}).get("is_taxable", False),
            ),
        )

        # Parse other JSONB fields
        sd_data = data.get("statutory_defaults") or {}
        statutory_defaults = StatutoryDefaults(
            cpp_exempt_by_default=sd_data.get("cpp_exempt_by_default", False),
            cpp2_exempt_by_default=sd_data.get("cpp2_exempt_by_default", False),
            ei_exempt_by_default=sd_data.get("ei_exempt_by_default", False),
        )

        op_data = data.get("overtime_policy") or {}
        overtime_policy = OvertimePolicy(
            bank_time_enabled=op_data.get("bank_time_enabled", False),
            bank_time_rate=op_data.get("bank_time_rate", 1.5),
            bank_time_expiry_months=op_data.get("bank_time_expiry_months", 3),
            require_written_agreement=op_data.get("require_written_agreement", True),
        )

        wcb_data = data.get("wcb_config") or {}
        wcb_config = WcbConfig(
            enabled=wcb_data.get("enabled", False),
            industry_class_code=wcb_data.get("industry_class_code"),
            industry_name=wcb_data.get("industry_name"),
            assessment_rate=Decimal(str(wcb_data.get("assessment_rate", 0))),
            max_assessable_earnings=Decimal(str(wcb_data["max_assessable_earnings"])) if wcb_data.get("max_assessable_earnings") else None,
        )

        return PayGroup(
            id=UUID(data["id"]),
            company_id=UUID(data["company_id"]) if data.get("company_id") else UUID("00000000-0000-0000-0000-000000000000"),
            name=data["name"],
            description=data.get("description"),
            pay_frequency=PayFrequency(data.get("pay_frequency", "bi_weekly")),
            employment_type=data.get("employment_type", "full_time"),
            next_pay_date=date.fromisoformat(data["next_pay_date"]) if data.get("next_pay_date") else date.today(),
            period_start_day=PeriodStartDay(data.get("period_start_day", "monday")),
            leave_enabled=data.get("leave_enabled", True),
            statutory_defaults=statutory_defaults,
            overtime_policy=overtime_policy,
            wcb_config=wcb_config,
            group_benefits=group_benefits,
            custom_deductions=[],  # Not needed for paystub generation
            created_at=dt.fromisoformat(data["created_at"]) if data.get("created_at") else dt.now(),
            updated_at=dt.fromisoformat(data["updated_at"]) if data.get("updated_at") else dt.now(),
        )

    def _build_payroll_record_model(self, data: dict[str, Any]) -> PayrollRecord:
        """Build PayrollRecord model from database row."""
        from datetime import datetime as dt

        return PayrollRecord(
            id=UUID(data["id"]),
            payroll_run_id=UUID(data["payroll_run_id"]),
            employee_id=UUID(data["employee_id"]),
            user_id=data.get("user_id", ""),
            ledger_id=data.get("ledger_id", ""),
            gross_regular=Decimal(str(data.get("gross_regular", 0))),
            gross_overtime=Decimal(str(data.get("gross_overtime", 0))),
            holiday_pay=Decimal(str(data.get("holiday_pay", 0))),
            holiday_premium_pay=Decimal(str(data.get("holiday_premium_pay", 0))),
            vacation_pay_paid=Decimal(str(data.get("vacation_pay_paid", 0))),
            other_earnings=Decimal(str(data.get("other_earnings", 0))),
            cpp_employee=Decimal(str(data.get("cpp_employee", 0))),
            cpp_additional=Decimal(str(data.get("cpp_additional", 0))),
            ei_employee=Decimal(str(data.get("ei_employee", 0))),
            federal_tax=Decimal(str(data.get("federal_tax", 0))),
            provincial_tax=Decimal(str(data.get("provincial_tax", 0))),
            rrsp=Decimal(str(data.get("rrsp", 0))),
            union_dues=Decimal(str(data.get("union_dues", 0))),
            garnishments=Decimal(str(data.get("garnishments", 0))),
            other_deductions=Decimal(str(data.get("other_deductions", 0))),
            cpp_employer=Decimal(str(data.get("cpp_employer", 0))),
            ei_employer=Decimal(str(data.get("ei_employer", 0))),
            total_gross=Decimal(str(data.get("total_gross", 0))),
            total_deductions=Decimal(str(data.get("total_deductions", 0))),
            net_pay=Decimal(str(data.get("net_pay", 0))),
            total_employer_cost=Decimal(str(data.get("total_employer_cost", 0))),
            ytd_gross=Decimal(str(data.get("ytd_gross", 0))),
            ytd_cpp=Decimal(str(data.get("ytd_cpp", 0))),
            ytd_ei=Decimal(str(data.get("ytd_ei", 0))),
            ytd_federal_tax=Decimal(str(data.get("ytd_federal_tax", 0))),
            ytd_provincial_tax=Decimal(str(data.get("ytd_provincial_tax", 0))),
            vacation_accrued=Decimal(str(data.get("vacation_accrued", 0))),
            vacation_hours_taken=Decimal(str(data.get("vacation_hours_taken", 0))),
            calculation_details=data.get("calculation_details"),
            paystub_storage_key=data.get("paystub_storage_key"),
            paystub_generated_at=dt.fromisoformat(data["paystub_generated_at"]) if data.get("paystub_generated_at") else None,
            created_at=dt.fromisoformat(data["created_at"]) if data.get("created_at") else dt.now(),
        )

    async def sync_employees(self, run_id: UUID) -> dict[str, Any]:
        """
        Sync new employees to a draft payroll run.

        When loading a draft payroll run, employees may have been added to pay groups
        after the run was created. This method:
        1. Finds pay groups for the run's pay_date
        2. Gets all active employees from those pay groups
        3. Creates payroll_records for any employees not in the run
        4. Updates the run's total_employees count

        Returns:
            Dict with added_count, added_employees, and updated run data

        Raises:
            ValueError: If run is not in draft status
        """
        # Verify run exists and is in draft status
        run = await self.get_run(run_id)
        if not run:
            raise ValueError("Payroll run not found")

        if run["status"] != "draft":
            # Not an error, just return empty result for non-draft runs
            return {
                "added_count": 0,
                "added_employees": [],
                "run": run,
            }

        pay_date = run["pay_date"]

        # Get pay groups with matching next_pay_date
        # Note: pay_groups table doesn't have user_id/ledger_id columns
        # RLS policy filters via company_id relationship
        pay_groups_result = self.supabase.table("pay_groups").select(
            "id, name, pay_frequency, employment_type, group_benefits"
        ).eq("next_pay_date", pay_date).execute()

        pay_groups = pay_groups_result.data or []
        if not pay_groups:
            return {
                "added_count": 0,
                "added_employees": [],
                "run": run,
            }

        pay_group_ids = [pg["id"] for pg in pay_groups]
        pay_group_map = {pg["id"]: pg for pg in pay_groups}

        # Get all active employees from these pay groups
        employees_result = self.supabase.table("employees").select(
            "id, first_name, last_name, province_of_employment, pay_group_id, "
            "annual_salary, hourly_rate, federal_claim_amount, provincial_claim_amount, "
            "is_cpp_exempt, is_ei_exempt, cpp2_exempt, vacation_config"
        ).eq("user_id", self.user_id).eq("ledger_id", self.ledger_id).in_(
            "pay_group_id", pay_group_ids
        ).is_("termination_date", "null").execute()

        all_employees = employees_result.data or []

        # Get existing employee IDs in this run
        existing_records_result = self.supabase.table("payroll_records").select(
            "employee_id"
        ).eq("payroll_run_id", str(run_id)).execute()

        existing_employee_ids = {
            r["employee_id"] for r in (existing_records_result.data or [])
        }

        # Find missing employees
        missing_employees = [
            emp for emp in all_employees if emp["id"] not in existing_employee_ids
        ]

        if not missing_employees:
            return {
                "added_count": 0,
                "added_employees": [],
                "run": run,
            }

        # Extract tax year from pay_date
        tax_year = _extract_year_from_date(pay_date)

        # Convert pay_date string to date object for tax edition selection
        from datetime import datetime
        pay_date_obj = datetime.strptime(pay_date, "%Y-%m-%d").date() if pay_date else None

        # Calculate payroll for missing employees and create records
        added_employees, results = await self._create_records_for_employees(
            run_id, missing_employees, pay_group_map, tax_year, pay_date_obj
        )

        # Calculate totals from new results and add to existing run totals
        new_gross = sum(float(r.total_gross) for r in results)
        new_cpp_employee = sum(float(r.cpp_total) for r in results)
        new_cpp_employer = sum(float(r.cpp_employer) for r in results)
        new_ei_employee = sum(float(r.ei_employee) for r in results)
        new_ei_employer = sum(float(r.ei_employer) for r in results)
        new_federal_tax = sum(float(r.federal_tax) for r in results)
        new_provincial_tax = sum(float(r.provincial_tax) for r in results)
        new_net_pay = sum(float(r.net_pay) for r in results)
        new_employer_cost = new_cpp_employer + new_ei_employer

        # Update all run totals
        self.supabase.table("payroll_runs").update({
            "total_employees": (run.get("total_employees") or 0) + len(added_employees),
            "total_gross": float(run.get("total_gross", 0)) + new_gross,
            "total_cpp_employee": float(run.get("total_cpp_employee", 0)) + new_cpp_employee,
            "total_cpp_employer": float(run.get("total_cpp_employer", 0)) + new_cpp_employer,
            "total_ei_employee": float(run.get("total_ei_employee", 0)) + new_ei_employee,
            "total_ei_employer": float(run.get("total_ei_employer", 0)) + new_ei_employer,
            "total_federal_tax": float(run.get("total_federal_tax", 0)) + new_federal_tax,
            "total_provincial_tax": float(run.get("total_provincial_tax", 0)) + new_provincial_tax,
            "total_net_pay": float(run.get("total_net_pay", 0)) + new_net_pay,
            "total_employer_cost": float(run.get("total_employer_cost", 0)) + new_employer_cost,
        }).eq("id", str(run_id)).execute()

        # Return updated run
        updated_run = await self.get_run(run_id) or run

        return {
            "added_count": len(added_employees),
            "added_employees": added_employees,
            "run": updated_run,
        }

    async def _create_records_for_employees(
        self,
        run_id: UUID,
        employees: list[dict[str, Any]],
        pay_group_map: dict[str, dict[str, Any]],
        tax_year: int = 2025,
        pay_date: date | None = None,
    ) -> tuple[list[dict[str, Any]], list[Any]]:
        """Create payroll records for a list of employees.

        Args:
            run_id: The payroll run ID
            employees: List of employee data
            pay_group_map: Mapping of pay group ID to pay group data
            tax_year: The tax year for YTD calculations (extracted from pay_date)

        Returns:
            Tuple of (added_employees list, calculation_results list)
        """
        if not employees:
            return [], []

        # Get prior YTD data for all employees from completed payroll runs
        employee_ids = [emp["id"] for emp in employees]
        prior_ytd_data = self._get_prior_ytd_for_employees(
            employee_ids, str(run_id), year=tax_year
        )

        # Build calculation inputs
        calculation_inputs: list[EmployeePayrollInput] = []
        employee_map: dict[str, dict[str, Any]] = {}

        for emp in employees:
            pay_group = pay_group_map.get(emp.get("pay_group_id", ""), {})
            pay_frequency_str = pay_group.get("pay_frequency", "bi_weekly")
            pay_frequency = PayFrequency(pay_frequency_str)

            # Extract benefits from pay group
            group_benefits = pay_group.get("group_benefits") or {}

            # Calculate taxable benefits (employer contributions where isTaxable=True)
            taxable_benefits_pensionable = self._calculate_taxable_benefits(group_benefits)

            # Calculate employee benefits deduction (post-tax deductions)
            benefits_deduction = self._calculate_benefits_deduction(group_benefits)

            # Calculate gross pay
            gross_regular, gross_overtime = self._calculate_initial_gross(
                emp, pay_frequency_str
            )

            # Calculate vacation pay for pay_as_you_go method
            vacation_config = emp.get("vacation_config") or {}
            payout_method = vacation_config.get("payout_method", "accrual")
            vacation_pay_for_gross = Decimal("0")

            if payout_method == "pay_as_you_go":
                vacation_rate = Decimal(str(vacation_config.get("vacation_rate", "0.04")))
                # Vacation pay is based on regular + overtime earnings
                base_earnings = gross_regular + gross_overtime
                vacation_pay_for_gross = base_earnings * vacation_rate

            # Use province-specific BPA as default if no employee override
            emp_province = emp["province_of_employment"]

            # Get prior YTD for this employee
            emp_prior_ytd = prior_ytd_data.get(emp["id"], {})

            calc_input = EmployeePayrollInput(
                employee_id=emp["id"],
                province=Province(emp_province),
                pay_frequency=pay_frequency,
                gross_regular=gross_regular,
                gross_overtime=gross_overtime,
                # Vacation pay for pay_as_you_go method (added to gross)
                vacation_pay=vacation_pay_for_gross,
                federal_claim_amount=Decimal(
                    str(emp.get("federal_claim_amount"))
                ) if emp.get("federal_claim_amount") is not None else DEFAULT_FEDERAL_CLAIM_2025,
                provincial_claim_amount=Decimal(
                    str(emp.get("provincial_claim_amount"))
                ) if emp.get("provincial_claim_amount") is not None else get_provincial_bpa(
                    emp_province, tax_year, pay_date
                ),
                is_cpp_exempt=emp.get("is_cpp_exempt", False),
                is_ei_exempt=emp.get("is_ei_exempt", False),
                cpp2_exempt=emp.get("cpp2_exempt", False),
                # Taxable benefits (employer contributions where isTaxable=True)
                taxable_benefits_pensionable=taxable_benefits_pensionable,
                # Employee benefits deduction (post-tax, included in net_pay calc)
                other_deductions=benefits_deduction,
                # Pay date for tax edition selection (2025: Jan=15%, Jul=14%)
                pay_date=pay_date,
                # YTD values from prior completed payroll runs
                ytd_gross=emp_prior_ytd.get("ytd_gross", Decimal("0")),
                ytd_cpp_base=emp_prior_ytd.get("ytd_cpp", Decimal("0")),
                ytd_ei=emp_prior_ytd.get("ytd_ei", Decimal("0")),
                ytd_federal_tax=emp_prior_ytd.get("ytd_federal_tax", Decimal("0")),
                ytd_provincial_tax=emp_prior_ytd.get("ytd_provincial_tax", Decimal("0")),
            )
            calculation_inputs.append(calc_input)
            employee_map[emp["id"]] = emp

        # Calculate using PayrollEngine
        engine = PayrollEngine(year=tax_year)
        results = engine.calculate_batch(calculation_inputs)

        # Create payroll records
        records_to_insert = []
        added_employees = []

        for result in results:
            emp = employee_map[result.employee_id]
            pay_group = pay_group_map.get(emp.get("pay_group_id", ""), {})

            # Build employee name snapshot
            employee_name = f"{emp['first_name']} {emp['last_name']}"

            # Calculate vacation accrued (only for accrual method, not pay-as-you-go)
            vacation_config = emp.get("vacation_config") or {}
            payout_method = vacation_config.get("payout_method", "accrual")
            if payout_method == "accrual":
                vacation_rate = Decimal(str(vacation_config.get("vacation_rate", "0.04")))
                # For accrual: calculate based on base earnings (excluding vacation_pay itself)
                base_earnings = (
                    result.gross_regular + result.gross_overtime +
                    result.holiday_pay + result.other_earnings
                )
                vacation_accrued = base_earnings * vacation_rate
            else:
                # pay_as_you_go: vacation is already included in gross via vacation_pay field
                vacation_accrued = Decimal("0")

            # other_deductions already includes benefits (passed to engine earlier)
            records_to_insert.append({
                "payroll_run_id": str(run_id),
                "employee_id": result.employee_id,
                "user_id": self.user_id,
                "ledger_id": self.ledger_id,
                # Snapshot fields
                "employee_name_snapshot": employee_name,
                "province_snapshot": emp["province_of_employment"],
                "annual_salary_snapshot": emp.get("annual_salary"),
                "pay_group_id_snapshot": emp.get("pay_group_id"),
                "pay_group_name_snapshot": pay_group.get("name"),
                # Hours (for hourly employees, defaults)
                "regular_hours_worked": None,
                "overtime_hours_worked": 0,
                "hourly_rate_snapshot": emp.get("hourly_rate"),
                # Earnings
                "gross_regular": float(result.gross_regular),
                "gross_overtime": float(result.gross_overtime),
                "holiday_pay": float(result.holiday_pay),
                "holiday_premium_pay": float(result.holiday_premium_pay),
                "vacation_pay_paid": float(result.vacation_pay),
                "other_earnings": float(result.other_earnings),
                # Deductions
                "cpp_employee": float(result.cpp_base),
                "cpp_additional": float(result.cpp_additional),
                "ei_employee": float(result.ei_employee),
                "federal_tax": float(result.federal_tax),
                "provincial_tax": float(result.provincial_tax),
                "rrsp": float(result.rrsp),
                "union_dues": float(result.union_dues),
                "garnishments": float(result.garnishments),
                "other_deductions": float(result.other_deductions),
                # Employer costs
                "cpp_employer": float(result.cpp_employer),
                "ei_employer": float(result.ei_employer),
                # YTD
                "ytd_gross": float(result.new_ytd_gross),
                "ytd_cpp": float(result.new_ytd_cpp),
                "ytd_ei": float(result.new_ytd_ei),
                "ytd_federal_tax": float(result.new_ytd_federal_tax),
                "ytd_provincial_tax": float(result.new_ytd_provincial_tax),
                "vacation_accrued": float(vacation_accrued),
                "vacation_hours_taken": 0,
                # Draft state
                "input_data": {
                    "regularHours": 0,
                    "overtimeHours": 0,
                    "leaveEntries": [],
                    "holidayWorkEntries": [],
                    "adjustments": [],
                    "overrides": {},
                },
                "is_modified": False,
            })

            added_employees.append({
                "employee_id": result.employee_id,
                "employee_name": employee_name,
            })

        # Insert all records
        if records_to_insert:
            self.supabase.table("payroll_records").insert(records_to_insert).execute()

        return added_employees, results

    def _calculate_initial_gross(
        self, employee: dict[str, Any], pay_frequency: str
    ) -> tuple[Decimal, Decimal]:
        """Calculate initial gross pay for a new employee in a payroll run."""
        annual_salary = employee.get("annual_salary")
        hourly_rate = employee.get("hourly_rate")

        if annual_salary and not hourly_rate:
            # Salaried employee
            periods_per_year = {
                "weekly": 52,
                "bi_weekly": 26,
                "semi_monthly": 24,
                "monthly": 12,
            }
            periods = periods_per_year.get(pay_frequency, 26)
            gross_regular = Decimal(str(annual_salary)) / Decimal(str(periods))
            return gross_regular, Decimal("0")
        elif hourly_rate:
            # Hourly employee - start with 0 hours, user will input
            return Decimal("0"), Decimal("0")
        else:
            return Decimal("0"), Decimal("0")

    def _calculate_gross_from_input(
        self,
        employee: dict[str, Any],
        input_data: dict[str, Any],
        pay_frequency: str,
    ) -> tuple[Decimal, Decimal]:
        """Calculate gross regular and overtime pay from input_data"""
        gross_regular = Decimal("0")
        gross_overtime = Decimal("0")

        annual_salary = employee.get("annual_salary")
        hourly_rate = employee.get("hourly_rate")

        # Check for overrides first
        overrides = input_data.get("overrides") or {}

        if annual_salary and not hourly_rate:
            # Salaried employee
            periods_per_year = {
                "weekly": 52,
                "bi_weekly": 26,
                "semi_monthly": 24,
                "monthly": 12,
            }
            periods = periods_per_year.get(pay_frequency, 26)

            if overrides.get("regularPay") is not None:
                gross_regular = Decimal(str(overrides["regularPay"]))
            else:
                gross_regular = Decimal(str(annual_salary)) / Decimal(str(periods))

            # Salaried overtime (using implied hourly rate)
            overtime_hours = Decimal(str(input_data.get("overtimeHours", 0)))
            if overtime_hours > 0:
                default_hours = {
                    "weekly": 40,
                    "bi_weekly": 80,
                    "semi_monthly": 86.67,
                    "monthly": 173.33,
                }
                hours_per_period = Decimal(str(default_hours.get(pay_frequency, 80)))
                implied_hourly = gross_regular / hours_per_period
                gross_overtime = overtime_hours * implied_hourly * Decimal("1.5")

        elif hourly_rate:
            # Hourly employee
            rate = Decimal(str(hourly_rate))
            regular_hours = Decimal(str(input_data.get("regularHours", 0)))
            overtime_hours = Decimal(str(input_data.get("overtimeHours", 0)))

            if overrides.get("regularPay") is not None:
                gross_regular = Decimal(str(overrides["regularPay"]))
            else:
                gross_regular = regular_hours * rate

            if overrides.get("overtimePay") is not None:
                gross_overtime = Decimal(str(overrides["overtimePay"]))
            else:
                gross_overtime = overtime_hours * rate * Decimal("1.5")

            # Add leave pay
            leave_entries = input_data.get("leaveEntries") or []
            for leave in leave_entries:
                leave_hours = Decimal(str(leave.get("hours", 0)))
                gross_regular += leave_hours * rate

        return gross_regular, gross_overtime


    async def create_or_get_run(self, pay_date: str) -> dict[str, Any]:
        """
        Create a new draft payroll run or get existing one for a pay date.

        This method:
        1. Checks if a payroll run already exists for this pay date
        2. If exists, returns the existing run
        3. If not, creates a new draft run with payroll records for all eligible employees

        Args:
            pay_date: The pay date in YYYY-MM-DD format

        Returns:
            Dict with 'run' (payroll run data), 'created' (bool), and 'records_count'
        """
        # Check if a run already exists for this pay date
        existing_result = self.supabase.table("payroll_runs").select("*").eq(
            "user_id", self.user_id
        ).eq("ledger_id", self.ledger_id).eq("pay_date", pay_date).execute()

        if existing_result.data and len(existing_result.data) > 0:
            return {
                "run": existing_result.data[0],
                "created": False,
                "records_count": 0,
            }

        # Get pay groups with matching next_pay_date
        pay_groups_result = self.supabase.table("pay_groups").select(
            "id, name, pay_frequency, employment_type, group_benefits"
        ).eq("next_pay_date", pay_date).execute()

        pay_groups = pay_groups_result.data or []
        if not pay_groups:
            raise ValueError(f"No pay groups found with pay date {pay_date}")

        pay_group_ids = [pg["id"] for pg in pay_groups]
        pay_group_map = {pg["id"]: pg for pg in pay_groups}

        # Get all active employees from these pay groups
        employees_result = self.supabase.table("employees").select(
            "id, first_name, last_name, province_of_employment, pay_group_id, "
            "annual_salary, hourly_rate, federal_claim_amount, provincial_claim_amount, "
            "is_cpp_exempt, is_ei_exempt, cpp2_exempt, vacation_config"
        ).eq("user_id", self.user_id).eq("ledger_id", self.ledger_id).in_(
            "pay_group_id", pay_group_ids
        ).is_("termination_date", "null").execute()

        employees = employees_result.data or []
        if not employees:
            raise ValueError("No active employees found for these pay groups")

        # Calculate period dates based on pay frequency
        from calendar import monthrange
        from datetime import datetime, timedelta

        pay_date_obj = datetime.strptime(pay_date, "%Y-%m-%d")

        # Get pay frequency from the first pay group (all should have same frequency)
        pay_frequency = pay_groups[0].get("pay_frequency", "bi_weekly")

        if pay_frequency == "monthly":
            # Monthly: full month of pay_date (e.g., pay date Nov 30 -> Nov 1-30)
            period_start = pay_date_obj.replace(day=1)
            last_day = monthrange(pay_date_obj.year, pay_date_obj.month)[1]
            period_end = pay_date_obj.replace(day=last_day)
        elif pay_frequency == "semi_monthly":
            # Semi-monthly: 1-15 or 16-end of month
            if pay_date_obj.day <= 15:
                # Pay date in first half: period is 16th to end of previous month
                prev_month = pay_date_obj.replace(day=1) - timedelta(days=1)
                period_start = prev_month.replace(day=16)
                period_end = prev_month
            else:
                # Pay date in second half: period is 1st to 15th of current month
                period_start = pay_date_obj.replace(day=1)
                period_end = pay_date_obj.replace(day=15)
        elif pay_frequency == "weekly":
            # Weekly: 7 days ending day before pay date
            period_end = pay_date_obj - timedelta(days=1)
            period_start = period_end - timedelta(days=6)
        else:
            # Bi-weekly (default): 14 days ending day before pay date
            period_end = pay_date_obj - timedelta(days=1)
            period_start = period_end - timedelta(days=13)

        # Create the payroll run
        run_insert_result = self.supabase.table("payroll_runs").insert({
            "user_id": self.user_id,
            "ledger_id": self.ledger_id,
            "period_start": period_start.strftime("%Y-%m-%d"),
            "period_end": period_end.strftime("%Y-%m-%d"),
            "pay_date": pay_date,
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

        # Extract tax year from pay_date
        tax_year = _extract_year_from_date(pay_date)

        # Create payroll records for all employees (without calculation)
        # Note: pay_date_obj is datetime, convert to date for tax edition selection
        _, results = await self._create_records_for_employees(
            UUID(run_id), employees, pay_group_map, tax_year, pay_date_obj.date()
        )

        # Update run totals from created records
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

            # Refresh run data
            run = await self.get_run(UUID(run_id)) or run

        return {
            "run": run,
            "created": True,
            "records_count": len(employees),
        }

    async def add_employee_to_run(
        self, run_id: UUID, employee_id: str
    ) -> dict[str, Any]:
        """
        Add a single employee to a draft payroll run.

        This adds the employee to the run and creates a payroll record for them.
        If the employee doesn't belong to a pay group, they'll be assigned based
        on the run's pay groups.

        Args:
            run_id: The payroll run ID
            employee_id: The employee ID to add

        Returns:
            Dict with 'record' (created payroll record) and 'employee_name'

        Raises:
            ValueError: If run is not in draft status or employee not found
        """
        # Verify run is in draft status
        run = await self.get_run(run_id)
        if not run:
            raise ValueError("Payroll run not found")

        if run["status"] != "draft":
            raise ValueError(
                f"Cannot add employee: payroll run is in '{run['status']}' status, "
                "not 'draft'"
            )

        # Check if employee already in run
        existing_record = self.supabase.table("payroll_records").select("id").eq(
            "payroll_run_id", str(run_id)
        ).eq("employee_id", employee_id).execute()

        if existing_record.data and len(existing_record.data) > 0:
            raise ValueError("Employee already exists in this payroll run")

        # Get employee data
        employee_result = self.supabase.table("employees").select(
            "id, first_name, last_name, province_of_employment, pay_group_id, "
            "annual_salary, hourly_rate, federal_claim_amount, provincial_claim_amount, "
            "is_cpp_exempt, is_ei_exempt, cpp2_exempt, vacation_config"
        ).eq("id", employee_id).eq("user_id", self.user_id).eq(
            "ledger_id", self.ledger_id
        ).single().execute()

        if not employee_result.data:
            raise ValueError("Employee not found")

        employee = employee_result.data

        # Get pay group info
        pay_group_id = employee.get("pay_group_id")
        pay_group = {}
        if pay_group_id:
            pg_result = self.supabase.table("pay_groups").select(
                "id, name, pay_frequency, employment_type, group_benefits"
            ).eq("id", pay_group_id).execute()
            if pg_result.data:
                pay_group = pg_result.data[0]

        pay_group_map = {pay_group_id: pay_group} if pay_group_id else {}

        # Extract tax year from run's pay_date
        pay_date_str = run.get("pay_date", "")
        tax_year = _extract_year_from_date(pay_date_str)

        # Convert pay_date string to date object for tax edition selection
        from datetime import datetime
        pay_date_obj = datetime.strptime(pay_date_str, "%Y-%m-%d").date() if pay_date_str else None

        # Create the payroll record
        added_employees, results = await self._create_records_for_employees(
            run_id, [employee], pay_group_map, tax_year, pay_date_obj
        )

        if not added_employees:
            raise ValueError("Failed to create payroll record for employee")

        # Update run totals
        if results:
            r = results[0]
            self.supabase.table("payroll_runs").update({
                "total_employees": (run.get("total_employees") or 0) + 1,
                "total_gross": float(run.get("total_gross", 0)) + float(r.total_gross),
                "total_cpp_employee": float(run.get("total_cpp_employee", 0)) + float(r.cpp_total),
                "total_cpp_employer": float(run.get("total_cpp_employer", 0)) + float(r.cpp_employer),
                "total_ei_employee": float(run.get("total_ei_employee", 0)) + float(r.ei_employee),
                "total_ei_employer": float(run.get("total_ei_employer", 0)) + float(r.ei_employer),
                "total_federal_tax": float(run.get("total_federal_tax", 0)) + float(r.federal_tax),
                "total_provincial_tax": float(run.get("total_provincial_tax", 0)) + float(r.provincial_tax),
                "total_net_pay": float(run.get("total_net_pay", 0)) + float(r.net_pay),
                "total_employer_cost": float(run.get("total_employer_cost", 0)) + float(r.cpp_employer) + float(r.ei_employer),
            }).eq("id", str(run_id)).execute()

        return {
            "employee_id": employee_id,
            "employee_name": f"{employee['first_name']} {employee['last_name']}",
        }

    async def remove_employee_from_run(
        self, run_id: UUID, employee_id: str
    ) -> dict[str, Any]:
        """
        Remove an employee from a draft payroll run.

        This deletes the payroll record for the employee.

        Args:
            run_id: The payroll run ID
            employee_id: The employee ID to remove

        Returns:
            Dict with 'removed' (bool) and 'employee_id'

        Raises:
            ValueError: If run is not in draft status or record not found
        """
        # Verify run is in draft status
        run = await self.get_run(run_id)
        if not run:
            raise ValueError("Payroll run not found")

        if run["status"] != "draft":
            raise ValueError(
                f"Cannot remove employee: payroll run is in '{run['status']}' status, "
                "not 'draft'"
            )

        # Get the record to remove (for updating totals)
        record_result = self.supabase.table("payroll_records").select("*").eq(
            "payroll_run_id", str(run_id)
        ).eq("employee_id", employee_id).eq("user_id", self.user_id).execute()

        if not record_result.data or len(record_result.data) == 0:
            raise ValueError("Employee not found in this payroll run")

        record = record_result.data[0]

        # Delete the record
        self.supabase.table("payroll_records").delete().eq(
            "id", record["id"]
        ).execute()

        # Clear employee's pay_group_id (unassign from pay group)
        self.supabase.table("employees").update({
            "pay_group_id": None
        }).eq("id", employee_id).eq("user_id", self.user_id).execute()

        # Update run totals (subtract the removed employee's values)
        gross = float(record.get("gross_regular", 0)) + float(record.get("gross_overtime", 0))
        cpp_employee = float(record.get("cpp_employee", 0)) + float(record.get("cpp_additional", 0))
        cpp_employer = float(record.get("cpp_employer", 0))
        ei_employee = float(record.get("ei_employee", 0))
        ei_employer = float(record.get("ei_employer", 0))
        federal_tax = float(record.get("federal_tax", 0))
        provincial_tax = float(record.get("provincial_tax", 0))
        net_pay = gross - cpp_employee - ei_employee - federal_tax - provincial_tax

        self.supabase.table("payroll_runs").update({
            "total_employees": max(0, (run.get("total_employees") or 0) - 1),
            "total_gross": max(0, float(run.get("total_gross", 0)) - gross),
            "total_cpp_employee": max(0, float(run.get("total_cpp_employee", 0)) - cpp_employee),
            "total_cpp_employer": max(0, float(run.get("total_cpp_employer", 0)) - cpp_employer),
            "total_ei_employee": max(0, float(run.get("total_ei_employee", 0)) - ei_employee),
            "total_ei_employer": max(0, float(run.get("total_ei_employer", 0)) - ei_employer),
            "total_federal_tax": max(0, float(run.get("total_federal_tax", 0)) - federal_tax),
            "total_provincial_tax": max(0, float(run.get("total_provincial_tax", 0)) - provincial_tax),
            "total_net_pay": max(0, float(run.get("total_net_pay", 0)) - net_pay),
            "total_employer_cost": max(0, float(run.get("total_employer_cost", 0)) - cpp_employer - ei_employer),
        }).eq("id", str(run_id)).execute()

        return {
            "removed": True,
            "employee_id": employee_id,
        }

    async def delete_run(self, run_id: UUID) -> dict[str, Any]:
        """
        Delete a draft payroll run.

        Only draft runs can be deleted. The associated payroll_records will be
        automatically deleted via CASCADE.

        Args:
            run_id: The payroll run ID

        Returns:
            Dict with 'deleted' (bool) and 'run_id'

        Raises:
            ValueError: If run is not in draft status
        """
        # Verify run exists and is in draft status
        run = await self.get_run(run_id)
        if not run:
            raise ValueError("Payroll run not found")

        if run["status"] != "draft":
            raise ValueError(
                f"Cannot delete: payroll run is in '{run['status']}' status. "
                "Only draft runs can be deleted."
            )

        # Delete the run (CASCADE will delete payroll_records)
        self.supabase.table("payroll_runs").delete().eq(
            "id", str(run_id)
        ).eq("user_id", self.user_id).eq("ledger_id", self.ledger_id).execute()

        return {
            "deleted": True,
            "run_id": str(run_id),
        }


    async def list_runs(
        self,
        status: str | None = None,
        exclude_statuses: list[str] | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        List payroll runs with filtering and pagination.

        Args:
            status: Optional single status to filter by
            exclude_statuses: Optional list of statuses to exclude
            limit: Maximum number of runs to return (default 20)
            offset: Number of runs to skip (default 0)

        Returns:
            Dict with 'runs' (list) and 'total' (count)
        """
        # Start building query
        query = self.supabase.table("payroll_runs").select(
            "*", count="exact"
        ).eq("user_id", self.user_id).eq("ledger_id", self.ledger_id)

        # Apply status filter
        if status:
            query = query.eq("status", status)

        # Apply exclude statuses filter
        if exclude_statuses:
            for excluded in exclude_statuses:
                query = query.neq("status", excluded)

        # Apply ordering and pagination
        query = query.order("pay_date", desc=True).range(offset, offset + limit - 1)

        result = query.execute()

        return {
            "runs": result.data or [],
            "total": result.count or 0,
        }


# Factory function for creating service instance
def get_payroll_run_service(user_id: str, ledger_id: str) -> PayrollRunService:
    """Create a PayrollRunService instance with user context"""
    return PayrollRunService(user_id, ledger_id)
