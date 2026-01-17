"""
Payroll Result Persister

Persists payroll calculation results to database.
Extracted from run_operations.py for better modularity.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Protocol

logger = logging.getLogger(__name__)


class PayrollResult(Protocol):
    """Protocol for payroll calculation results."""

    employee_id: str
    gross_regular: Decimal
    gross_overtime: Decimal
    holiday_pay: Decimal
    holiday_premium_pay: Decimal
    vacation_pay: Decimal
    other_earnings: Decimal
    bonus_earnings: Decimal
    cpp_base: Decimal
    cpp_additional: Decimal
    cpp_total: Decimal
    cpp_employer: Decimal
    ei_employee: Decimal
    ei_employer: Decimal
    federal_tax: Decimal
    provincial_tax: Decimal
    federal_tax_on_income: Decimal
    provincial_tax_on_income: Decimal
    federal_tax_on_bonus: Decimal
    provincial_tax_on_bonus: Decimal
    other_deductions: Decimal
    net_pay: Decimal
    total_gross: Decimal
    new_ytd_gross: Decimal
    new_ytd_cpp: Decimal
    new_ytd_ei: Decimal
    new_ytd_federal_tax: Decimal
    new_ytd_provincial_tax: Decimal


class PayrollResultPersister:
    """Persists payroll calculation results to database."""

    def __init__(self, supabase: Any):
        """Initialize result persister.

        Args:
            supabase: Supabase client instance
        """
        self.supabase = supabase

    def persist_results(
        self,
        results: list[Any],
        record_map: dict[str, dict[str, Any]],
        prior_ytd_data: dict[str, dict[str, Any]],
    ) -> None:
        """Persist all calculation results to database.

        Args:
            results: List of PayrollResult objects
            record_map: Map of employee_id to record data with metadata
            prior_ytd_data: Map of employee_id to prior YTD data
        """
        for result in results:
            record = record_map[result.employee_id]
            self._update_single_record(result, record, prior_ytd_data)

    def _update_single_record(
        self,
        result: Any,
        record: dict[str, Any],
        prior_ytd_data: dict[str, dict[str, Any]],
    ) -> None:
        """Update a single payroll record with calculation results.

        Args:
            result: PayrollResult object
            record: Record data with metadata
            prior_ytd_data: Map of employee_id to prior YTD data
        """
        input_data = record.get("input_data") or {}
        employee = record["employees"]
        emp_prior_ytd = prior_ytd_data.get(result.employee_id, {})

        # Calculate vacation accrued
        vacation_accrued = self._calculate_vacation_accrued(employee, result)

        # Get metadata from record_map
        vacation_hours_taken = record.get("_vacation_hours_taken", Decimal("0"))
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
            "bonus_earnings": float(result.bonus_earnings),
            "cpp_employee": float(result.cpp_base),
            "cpp_additional": float(result.cpp_additional),
            "ei_employee": float(result.ei_employee),
            "federal_tax": float(result.federal_tax),
            "provincial_tax": float(result.provincial_tax),
            "federal_tax_on_income": float(result.federal_tax_on_income),
            "provincial_tax_on_income": float(result.provincial_tax_on_income),
            "federal_tax_on_bonus": float(result.federal_tax_on_bonus),
            "provincial_tax_on_bonus": float(result.provincial_tax_on_bonus),
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

    def _calculate_vacation_accrued(
        self, employee: dict[str, Any], result: Any
    ) -> Decimal:
        """Calculate vacation accrued for an employee.

        Args:
            employee: Employee data
            result: PayrollResult object

        Returns:
            Vacation accrued amount
        """
        vacation_config = employee.get("vacation_config") or {}
        payout_method = vacation_config.get("payout_method", "accrual")

        if payout_method != "accrual":
            return Decimal("0")

        rate_val = vacation_config.get("vacation_rate")
        vacation_rate = Decimal(str(rate_val)) if rate_val is not None else Decimal("0.04")
        base_earnings = (
            result.gross_regular + result.gross_overtime +
            result.holiday_pay + result.other_earnings
        )
        return base_earnings * vacation_rate

    def update_run_totals(self, run_id: str, results: list[Any]) -> None:
        """Calculate and update payroll run totals.

        Args:
            run_id: Payroll run ID
            results: List of PayrollResult objects
        """
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
        }).eq("id", run_id).execute()

        logger.info(
            "Updated run %s totals: gross=%.2f, net=%.2f, employees=%d",
            run_id, total_gross, total_net_pay, len(results)
        )
