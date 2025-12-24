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

logger = logging.getLogger(__name__)


class PayrollRunService:
    """Service for payroll run operations"""

    def __init__(self, user_id: str, ledger_id: str):
        """Initialize service with user context"""
        self.user_id = user_id
        self.ledger_id = ledger_id
        self.supabase = get_supabase_client()

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
                pay_group_id,
                pay_groups (
                    id,
                    name,
                    pay_frequency,
                    employment_type
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
            calc_input = EmployeePayrollInput(
                employee_id=record["employee_id"],
                province=Province(employee["province_of_employment"]),
                pay_frequency=pay_frequency,
                gross_regular=gross_regular,
                gross_overtime=gross_overtime,
                holiday_pay=holiday_pay,
                other_earnings=other_earnings,
                federal_claim_amount=Decimal(
                    str(employee.get("federal_claim_amount", "16129"))
                ),
                provincial_claim_amount=Decimal(
                    str(employee.get("provincial_claim_amount", "12747"))
                ),
                is_cpp_exempt=employee.get("is_cpp_exempt", False),
                is_ei_exempt=employee.get("is_ei_exempt", False),
                cpp2_exempt=employee.get("cpp2_exempt", False),
                # YTD values from current record
                ytd_gross=Decimal(str(record.get("ytd_gross", 0))),
                ytd_cpp_base=Decimal(str(record.get("ytd_cpp", 0))),
                ytd_ei=Decimal(str(record.get("ytd_ei", 0))),
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
                "cpp_employer": float(result.cpp_employer),
                "ei_employer": float(result.ei_employer),
                "ytd_gross": float(result.new_ytd_gross),
                "ytd_cpp": float(result.new_ytd_cpp),
                "ytd_ei": float(result.new_ytd_ei),
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


# Factory function for creating service instance
def get_payroll_run_service(user_id: str, ledger_id: str) -> PayrollRunService:
    """Create a PayrollRunService instance with user context"""
    return PayrollRunService(user_id, ledger_id)
