"""
Employee Management for Payroll Run

Handles employee-related operations within payroll runs:
- sync_employees
- add_employee_to_run
- remove_employee_from_run
- create_records_for_employees
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.models.payroll import PayFrequency, Province
from app.services.payroll import EmployeePayrollInput, PayrollEngine
from app.services.payroll_run.benefits_calculator import BenefitsCalculator
from app.services.payroll_run.constants import (
    extract_year_from_date,
    get_federal_bpa,
    get_provincial_bpa,
)
from app.services.payroll_run.gross_calculator import GrossCalculator
from app.services.payroll_run.ytd_calculator import YtdCalculator


class EmployeeManagement:
    """Manages employees within payroll runs."""

    def __init__(
        self,
        supabase: Any,
        user_id: str,
        company_id: str,
        ytd_calculator: YtdCalculator,
        get_run_func: Any,
    ):
        """Initialize employee management.

        Args:
            supabase: Supabase client instance
            user_id: Current user ID
            company_id: Current company ID
            ytd_calculator: YTD calculator instance
            get_run_func: Function to get a payroll run by ID
        """
        self.supabase = supabase
        self.user_id = user_id
        self.company_id = company_id
        self.ytd_calculator = ytd_calculator
        self._get_run = get_run_func

    async def sync_employees(self, run_id: UUID) -> dict[str, Any]:
        """Sync new employees to a draft payroll run.

        When loading a draft payroll run, employees may have been added to pay groups
        after the run was created. This method finds and adds any missing employees.

        Returns:
            Dict with added_count, added_employees, and updated run data

        Raises:
            ValueError: If run is not in draft status
        """
        run = await self._get_run(run_id)
        if not run:
            raise ValueError("Payroll run not found")

        if run["status"] != "draft":
            return {
                "added_count": 0,
                "added_employees": [],
                "run": run,
            }

        period_end = run["period_end"]

        # Get pay groups with matching next_period_end
        pay_groups_result = self.supabase.table("pay_groups").select(
            "id, name, pay_frequency, employment_type, group_benefits"
        ).eq("next_period_end", period_end).execute()

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
            "annual_salary, hourly_rate, federal_additional_claims, provincial_additional_claims, "
            "is_cpp_exempt, is_ei_exempt, cpp2_exempt, vacation_config"
        ).eq("user_id", self.user_id).eq("company_id", self.company_id).in_(
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

        pay_date = run["pay_date"]
        tax_year = extract_year_from_date(pay_date)
        pay_date_obj = datetime.strptime(pay_date, "%Y-%m-%d").date() if pay_date else None

        added_employees, results = await self.create_records_for_employees(
            run_id, missing_employees, pay_group_map, tax_year, pay_date_obj
        )

        # Calculate totals from new results
        new_gross = sum(float(r.total_gross) for r in results)
        new_cpp_employee = sum(float(r.cpp_total) for r in results)
        new_cpp_employer = sum(float(r.cpp_employer) for r in results)
        new_ei_employee = sum(float(r.ei_employee) for r in results)
        new_ei_employer = sum(float(r.ei_employer) for r in results)
        new_federal_tax = sum(float(r.federal_tax) for r in results)
        new_provincial_tax = sum(float(r.provincial_tax) for r in results)
        new_net_pay = sum(float(r.net_pay) for r in results)
        new_employer_cost = new_cpp_employer + new_ei_employer

        # Update run totals
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

        updated_run = await self._get_run(run_id) or run

        return {
            "added_count": len(added_employees),
            "added_employees": added_employees,
            "run": updated_run,
        }

    async def add_employee_to_run(
        self, run_id: UUID, employee_id: str
    ) -> dict[str, Any]:
        """Add a single employee to a draft payroll run.

        Returns:
            Dict with 'employee_id' and 'employee_name'

        Raises:
            ValueError: If run is not in draft status or employee not found
        """
        run = await self._get_run(run_id)
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
            "annual_salary, hourly_rate, federal_additional_claims, provincial_additional_claims, "
            "is_cpp_exempt, is_ei_exempt, cpp2_exempt, vacation_config"
        ).eq("id", employee_id).eq("user_id", self.user_id).eq(
            "company_id", self.company_id
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

        pay_date_str = run.get("pay_date", "")
        tax_year = extract_year_from_date(pay_date_str)
        pay_date_obj = datetime.strptime(pay_date_str, "%Y-%m-%d").date() if pay_date_str else None

        added_employees, results = await self.create_records_for_employees(
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
        """Remove an employee from a draft payroll run.

        Returns:
            Dict with 'removed' (bool) and 'employee_id'

        Raises:
            ValueError: If run is not in draft status or record not found
        """
        run = await self._get_run(run_id)
        if not run:
            raise ValueError("Payroll run not found")

        if run["status"] != "draft":
            raise ValueError(
                f"Cannot remove employee: payroll run is in '{run['status']}' status, "
                "not 'draft'"
            )

        # Get the record to remove
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

        # Clear employee's pay_group_id
        self.supabase.table("employees").update({
            "pay_group_id": None
        }).eq("id", employee_id).eq("user_id", self.user_id).execute()

        # Update run totals
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

    async def create_records_for_employees(
        self,
        run_id: UUID,
        employees: list[dict[str, Any]],
        pay_group_map: dict[str, dict[str, Any]],
        tax_year: int = 2025,
        pay_date: date | None = None,
    ) -> tuple[list[dict[str, Any]], list[Any]]:
        """Create payroll records for a list of employees.

        Returns:
            Tuple of (added_employees list, calculation_results list)
        """
        if not employees:
            return [], []

        # Get prior YTD data
        employee_ids = [emp["id"] for emp in employees]
        prior_ytd_data = self.ytd_calculator.get_prior_ytd_for_employees(
            employee_ids, str(run_id), year=tax_year
        )

        # Build calculation inputs
        calculation_inputs: list[EmployeePayrollInput] = []
        employee_map: dict[str, dict[str, Any]] = {}

        for emp in employees:
            pay_group = pay_group_map.get(emp.get("pay_group_id", ""), {})
            pay_frequency_str = pay_group.get("pay_frequency", "bi_weekly")
            pay_frequency = PayFrequency(pay_frequency_str)

            group_benefits = pay_group.get("group_benefits") or {}
            taxable_benefits_pensionable = BenefitsCalculator.calculate_taxable_benefits(group_benefits)
            benefits_deduction = BenefitsCalculator.calculate_benefits_deduction(group_benefits)

            gross_regular, gross_overtime = GrossCalculator.calculate_initial_gross(
                emp, pay_frequency_str
            )

            # Calculate vacation pay for pay_as_you_go
            vacation_config = emp.get("vacation_config") or {}
            payout_method = vacation_config.get("payout_method", "accrual")
            vacation_pay_for_gross = Decimal("0")

            if payout_method == "pay_as_you_go":
                # Use vacation_rate from DB; default 0.04 only if missing (not if "0")
                rate_val = vacation_config.get("vacation_rate")
                vacation_rate = Decimal(str(rate_val)) if rate_val is not None else Decimal("0.04")
                base_earnings = gross_regular + gross_overtime
                vacation_pay_for_gross = base_earnings * vacation_rate

            # Calculate claim amounts
            emp_province = emp["province_of_employment"]

            federal_additional = Decimal(str(emp.get("federal_additional_claims", 0)))
            federal_bpa = get_federal_bpa(tax_year, pay_date)
            federal_claim = federal_bpa + federal_additional

            provincial_additional = Decimal(str(emp.get("provincial_additional_claims", 0)))
            provincial_bpa = get_provincial_bpa(emp_province, tax_year, pay_date)
            provincial_claim = provincial_bpa + provincial_additional

            emp_prior_ytd = prior_ytd_data.get(emp["id"], {})

            calc_input = EmployeePayrollInput(
                employee_id=emp["id"],
                province=Province(emp_province),
                pay_frequency=pay_frequency,
                gross_regular=gross_regular,
                gross_overtime=gross_overtime,
                vacation_pay=vacation_pay_for_gross,
                federal_claim_amount=federal_claim,
                provincial_claim_amount=provincial_claim,
                is_cpp_exempt=emp.get("is_cpp_exempt", False),
                is_ei_exempt=emp.get("is_ei_exempt", False),
                cpp2_exempt=emp.get("cpp2_exempt", False),
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
            employee_name = f"{emp['first_name']} {emp['last_name']}"
            emp_prior_ytd = prior_ytd_data.get(result.employee_id, {})

            # Calculate vacation accrued
            vacation_config = emp.get("vacation_config") or {}
            payout_method = vacation_config.get("payout_method", "accrual")
            if payout_method == "accrual":
                # Use vacation_rate from DB; default 0.04 only if missing (not if "0")
                rate_val = vacation_config.get("vacation_rate")
                vacation_rate = Decimal(str(rate_val)) if rate_val is not None else Decimal("0.04")
                base_earnings = (
                    result.gross_regular + result.gross_overtime +
                    result.holiday_pay + result.other_earnings
                )
                vacation_accrued = base_earnings * vacation_rate
            else:
                vacation_accrued = Decimal("0")

            records_to_insert.append({
                "payroll_run_id": str(run_id),
                "employee_id": result.employee_id,
                "user_id": self.user_id,
                "company_id": self.company_id,
                "employee_name_snapshot": employee_name,
                "province_snapshot": emp["province_of_employment"],
                "annual_salary_snapshot": emp.get("annual_salary"),
                "pay_group_id_snapshot": emp.get("pay_group_id"),
                "pay_group_name_snapshot": pay_group.get("name"),
                "regular_hours_worked": None,
                "overtime_hours_worked": 0,
                "hourly_rate_snapshot": emp.get("hourly_rate"),
                "gross_regular": float(result.gross_regular),
                "gross_overtime": float(result.gross_overtime),
                "holiday_pay": float(result.holiday_pay),
                "holiday_premium_pay": float(result.holiday_premium_pay),
                "vacation_pay_paid": float(result.vacation_pay),
                "other_earnings": float(result.other_earnings),
                "cpp_employee": float(result.cpp_base),
                "cpp_additional": float(result.cpp_additional),
                "ei_employee": float(result.ei_employee),
                "federal_tax": float(result.federal_tax),
                "provincial_tax": float(result.provincial_tax),
                "rrsp": float(result.rrsp),
                "union_dues": float(result.union_dues),
                "garnishments": float(result.garnishments),
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
                "vacation_hours_taken": 0,
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
