"""
Payroll Run Service - Manages payroll run lifecycle and operations

Provides:
- Record updates in draft state
- Recalculation of payroll deductions
- Status transitions (draft -> pending_approval)
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.core.supabase_client import get_supabase_client
from app.models.payroll import PayFrequency, Province
from app.services.payroll import EmployeePayrollInput, PayrollEngine
from app.services.payroll.tax_tables import get_province_config

logger = logging.getLogger(__name__)

# 2025 Federal Basic Personal Amount (default claim amount)
DEFAULT_FEDERAL_CLAIM_2025 = Decimal("16129")


def get_provincial_bpa(province_code: str, year: int = 2025) -> Decimal:
    """Get the Basic Personal Amount for a province from tax tables."""
    try:
        config = get_province_config(province_code, year)
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
        life = group_benefits.get("lifeInsurance") or {}
        if life.get("enabled") and life.get("isTaxable", False):
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
            ) if employee.get("provincial_claim_amount") is not None else get_provincial_bpa(province_code)

            # DEBUG: Log claim amounts for each employee
            logger.info(
                f"PAYROLL DEBUG: Employee {employee.get('first_name')} {employee.get('last_name')} "
                f"(province={province_code}): "
                f"federal_claim_amount={employee.get('federal_claim_amount')} -> {federal_claim}, "
                f"provincial_claim_amount={employee.get('provincial_claim_amount')} -> {provincial_claim}, "
                f"gross={gross_regular + gross_overtime}"
            )

            calc_input = EmployeePayrollInput(
                employee_id=record["employee_id"],
                province=Province(employee["province_of_employment"]),
                pay_frequency=pay_frequency,
                gross_regular=gross_regular,
                gross_overtime=gross_overtime,
                holiday_pay=holiday_pay,
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
                # YTD values from current record
                ytd_gross=Decimal(str(record.get("ytd_gross", 0))),
                ytd_cpp_base=Decimal(str(record.get("ytd_cpp", 0))),
                ytd_ei=Decimal(str(record.get("ytd_ei", 0))),
                ytd_federal_tax=Decimal(str(record.get("ytd_federal_tax", 0))),
                ytd_provincial_tax=Decimal(str(record.get("ytd_provincial_tax", 0))),
            )
            calculation_inputs.append(calc_input)
            record_map[record["employee_id"]] = record

        # Calculate using PayrollEngine
        engine = PayrollEngine(year=2025)
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
                vacation_accrued = result.total_gross * vacation_rate
            else:
                # pay_as_you_go: vacation is paid each period, no accrual
                vacation_accrued = Decimal("0")

            # other_deductions already includes benefits (passed to engine earlier)
            self.supabase.table("payroll_records").update({
                "gross_regular": float(result.gross_regular),
                "gross_overtime": float(result.gross_overtime),
                "holiday_pay": float(result.holiday_pay),
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

        # Calculate payroll for missing employees and create records
        added_employees, results = await self._create_records_for_employees(
            run_id, missing_employees, pay_group_map
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
    ) -> tuple[list[dict[str, Any]], list[Any]]:
        """Create payroll records for a list of employees.

        Returns:
            Tuple of (added_employees list, calculation_results list)
        """
        if not employees:
            return [], []

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

            # Use province-specific BPA as default if no employee override
            emp_province = emp["province_of_employment"]
            calc_input = EmployeePayrollInput(
                employee_id=emp["id"],
                province=Province(emp_province),
                pay_frequency=pay_frequency,
                gross_regular=gross_regular,
                gross_overtime=gross_overtime,
                federal_claim_amount=Decimal(
                    str(emp.get("federal_claim_amount"))
                ) if emp.get("federal_claim_amount") is not None else DEFAULT_FEDERAL_CLAIM_2025,
                provincial_claim_amount=Decimal(
                    str(emp.get("provincial_claim_amount"))
                ) if emp.get("provincial_claim_amount") is not None else get_provincial_bpa(emp_province),
                is_cpp_exempt=emp.get("is_cpp_exempt", False),
                is_ei_exempt=emp.get("is_ei_exempt", False),
                cpp2_exempt=emp.get("cpp2_exempt", False),
                # Taxable benefits (employer contributions where isTaxable=True)
                taxable_benefits_pensionable=taxable_benefits_pensionable,
                # Employee benefits deduction (post-tax, included in net_pay calc)
                other_deductions=benefits_deduction,
            )
            calculation_inputs.append(calc_input)
            employee_map[emp["id"]] = emp

        # Calculate using PayrollEngine
        engine = PayrollEngine(year=2025)
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
                vacation_accrued = result.total_gross * vacation_rate
            else:
                # pay_as_you_go: vacation is paid each period, no accrual
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

        # Create payroll records for all employees (without calculation)
        _, results = await self._create_records_for_employees(
            UUID(run_id), employees, pay_group_map
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

        # Create the payroll record
        added_employees, results = await self._create_records_for_employees(
            run_id, [employee], pay_group_map
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


# Factory function for creating service instance
def get_payroll_run_service(user_id: str, ledger_id: str) -> PayrollRunService:
    """Create a PayrollRunService instance with user context"""
    return PayrollRunService(user_id, ledger_id)
