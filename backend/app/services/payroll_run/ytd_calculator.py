"""
YTD (Year-to-Date) Calculator for Payroll Run

Handles calculation of YTD totals from completed payroll runs.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.models.payroll import PayrollRecord
from app.services.payroll_run.constants import COMPLETED_RUN_STATUSES, DEFAULT_TAX_YEAR
from app.services.payroll_run.model_builders import ModelBuilder


class YtdCalculator:
    """Calculates YTD totals from completed payroll runs."""

    def __init__(self, supabase: Any, user_id: str, company_id: str):
        """Initialize YTD calculator with database context.

        Args:
            supabase: Supabase client instance
            user_id: Current user ID
            company_id: Current company ID
        """
        self.supabase = supabase
        self.user_id = user_id
        self.company_id = company_id

    def get_prior_ytd_for_employees(
        self, employee_ids: list[str], current_run_id: str, year: int = DEFAULT_TAX_YEAR
    ) -> dict[str, dict[str, Decimal]]:
        """Get prior YTD totals for employees from completed payroll runs.

        This queries all approved/paid payroll_records for each employee
        in the given year, EXCLUDING the current run, and sums their totals.
        Also includes initial_ytd_* values from employee records for transferred
        employees (those who worked at another employer earlier this year).

        Args:
            employee_ids: List of employee IDs to query
            current_run_id: The current payroll run ID to exclude
            year: The tax year (default from DEFAULT_TAX_YEAR)

        Returns:
            Dict mapping employee_id -> {
                'ytd_gross': Decimal,
                'ytd_cpp': Decimal,
                'ytd_cpp_additional': Decimal,
                'ytd_ei': Decimal,
                'ytd_federal_tax': Decimal,
                'ytd_provincial_tax': Decimal,
            }
        """
        if not employee_ids:
            return {}

        # Get initial YTD values from employee records (for transferred employees)
        # Only include values that match the current tax year
        initial_ytd = self._get_initial_ytd_for_employees(employee_ids, year)

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
        ).eq("user_id", self.user_id).eq("company_id", self.company_id).in_(
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

        # Initialize YTD dict for all employees with initial values
        ytd_data: dict[str, dict[str, Decimal]] = {}
        for emp_id in employee_ids:
            init = initial_ytd.get(emp_id, {})
            ytd_data[emp_id] = {
                "ytd_gross": Decimal("0"),
                # Include initial YTD from previous employer
                "ytd_cpp": init.get("initial_ytd_cpp", Decimal("0")),
                "ytd_cpp_additional": init.get("initial_ytd_cpp2", Decimal("0")),
                "ytd_ei": init.get("initial_ytd_ei", Decimal("0")),
                "ytd_federal_tax": Decimal("0"),
                "ytd_provincial_tax": Decimal("0"),
                "ytd_net_pay": Decimal("0"),
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

            ytd_data[emp_id]["ytd_gross"] += total_gross
            # Track CPP base and additional (CPP2) separately
            ytd_data[emp_id]["ytd_cpp"] += Decimal(str(record.get("cpp_employee", 0)))
            ytd_data[emp_id]["ytd_cpp_additional"] += Decimal(
                str(record.get("cpp_additional", 0))
            )
            ytd_data[emp_id]["ytd_ei"] += Decimal(str(record.get("ei_employee", 0)))
            ytd_data[emp_id]["ytd_federal_tax"] += Decimal(
                str(record.get("federal_tax", 0))
            )
            ytd_data[emp_id]["ytd_provincial_tax"] += Decimal(
                str(record.get("provincial_tax", 0))
            )
            ytd_data[emp_id]["ytd_net_pay"] += Decimal(
                str(record.get("net_pay", 0))
            )

        return ytd_data

    async def get_ytd_records_for_employee(
        self,
        employee_id: str,
        current_run_id: str,
        year: int,
    ) -> list[PayrollRecord]:
        """Get prior YTD payroll records for an employee.

        Args:
            employee_id: Employee ID
            current_run_id: Current run ID to exclude
            year: Tax year

        Returns:
            List of PayrollRecord models for prior completed runs
        """
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
            records.append(ModelBuilder.build_payroll_record(r))

        return records

    def _get_initial_ytd_for_employees(
        self, employee_ids: list[str], year: int = DEFAULT_TAX_YEAR
    ) -> dict[str, dict[str, Decimal]]:
        """Get initial YTD values from employee records for a specific tax year.

        These values represent CPP/EI contributions made at a previous employer
        this year, for employees who transferred mid-year.

        IMPORTANT: Only returns values where initial_ytd_year matches the requested
        year. This prevents stale values from previous years being incorrectly
        applied to current year calculations.

        Args:
            employee_ids: List of employee IDs to query
            year: The tax year to filter by (only include values for this year)

        Returns:
            Dict mapping employee_id -> {
                'initial_ytd_cpp': Decimal,
                'initial_ytd_cpp2': Decimal,
                'initial_ytd_ei': Decimal,
            }
        """
        if not employee_ids:
            return {}

        result = self.supabase.table("employees").select(
            "id, initial_ytd_cpp, initial_ytd_cpp2, initial_ytd_ei, initial_ytd_year"
        ).eq("user_id", self.user_id).eq("company_id", self.company_id).in_(
            "id", employee_ids
        ).execute()

        initial_data: dict[str, dict[str, Decimal]] = {}
        for emp in result.data or []:
            # Only include initial YTD values if they match the requested tax year
            ytd_year = emp.get("initial_ytd_year")
            if ytd_year is not None and ytd_year == year:
                initial_data[emp["id"]] = {
                    "initial_ytd_cpp": Decimal(str(emp.get("initial_ytd_cpp") or 0)),
                    "initial_ytd_cpp2": Decimal(str(emp.get("initial_ytd_cpp2") or 0)),
                    "initial_ytd_ei": Decimal(str(emp.get("initial_ytd_ei") or 0)),
                }
            # If ytd_year is None or doesn't match, return zeros (no prior employment for this year)

        return initial_data
