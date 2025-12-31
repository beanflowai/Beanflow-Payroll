"""
Gross Pay Calculator for Payroll Run

Handles calculation of regular and overtime gross pay for employees.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.services.payroll_run.constants import (
    DEFAULT_HOURS_PER_PERIOD,
    PERIODS_PER_YEAR,
)


class GrossCalculator:
    """Calculates gross regular and overtime pay for employees."""

    @staticmethod
    def calculate_hourly_rate(employee: dict[str, Any]) -> Decimal:
        """Calculate employee's hourly rate for vacation pay calculation.

        For salaried employees: annual_salary / 2080
        For hourly employees: use their hourly_rate directly

        Args:
            employee: Employee data dict with annual_salary or hourly_rate

        Returns:
            Hourly rate as Decimal
        """
        hourly_rate = employee.get("hourly_rate")
        annual_salary = employee.get("annual_salary")

        if hourly_rate:
            return Decimal(str(hourly_rate))
        elif annual_salary:
            # 2080 = 52 weeks × 40 hours/week (standard annual working hours)
            return Decimal(str(annual_salary)) / Decimal("2080")
        return Decimal("0")

    @staticmethod
    def calculate_initial_gross(
        employee: dict[str, Any], pay_frequency: str
    ) -> tuple[Decimal, Decimal]:
        """Calculate initial gross pay for a new employee in a payroll run.

        Args:
            employee: Employee data dict
            pay_frequency: Pay frequency string (weekly, bi_weekly, etc.)

        Returns:
            Tuple of (gross_regular, gross_overtime)
        """
        annual_salary = employee.get("annual_salary")
        hourly_rate = employee.get("hourly_rate")

        if annual_salary and not hourly_rate:
            # Salaried employee
            periods = PERIODS_PER_YEAR.get(pay_frequency, 26)
            gross_regular = Decimal(str(annual_salary)) / Decimal(str(periods))
            return gross_regular, Decimal("0")
        elif hourly_rate:
            # Hourly employee - start with 0 hours, user will input
            return Decimal("0"), Decimal("0")
        else:
            return Decimal("0"), Decimal("0")

    @staticmethod
    def calculate_gross_from_input(
        employee: dict[str, Any],
        input_data: dict[str, Any],
        pay_frequency: str,
    ) -> tuple[Decimal, Decimal]:
        """Calculate gross regular and overtime pay from input_data.

        Args:
            employee: Employee data dict
            input_data: Input data with hours, overrides, leave entries
            pay_frequency: Pay frequency string

        Returns:
            Tuple of (gross_regular, gross_overtime)
        """
        gross_regular = Decimal("0")
        gross_overtime = Decimal("0")

        annual_salary = employee.get("annual_salary")
        hourly_rate = employee.get("hourly_rate")

        # Check for overrides first
        overrides = input_data.get("overrides") or {}

        if annual_salary and not hourly_rate:
            # Salaried employee
            periods = PERIODS_PER_YEAR.get(pay_frequency, 26)

            if overrides.get("regularPay") is not None:
                gross_regular = Decimal(str(overrides["regularPay"]))
            else:
                gross_regular = Decimal(str(annual_salary)) / Decimal(str(periods))

            # Salaried overtime (using implied hourly rate)
            overtime_hours = Decimal(str(input_data.get("overtimeHours", 0)))
            if overtime_hours > 0:
                hours_per_period = DEFAULT_HOURS_PER_PERIOD.get(
                    pay_frequency, Decimal("80")
                )
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

            # Add vacation leave pay only (sick leave handled separately in run_operations)
            leave_entries = input_data.get("leaveEntries") or []
            for leave in leave_entries:
                if leave.get("type") == "vacation":
                    leave_hours = Decimal(str(leave.get("hours", 0)))
                    gross_regular += leave_hours * rate
            # Note: Sick leave is processed in run_operations.py where we have
            # access to employee.sick_balance for paid/unpaid calculation

        return gross_regular, gross_overtime
