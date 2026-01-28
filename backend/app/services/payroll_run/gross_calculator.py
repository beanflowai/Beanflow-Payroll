"""
Gross Pay Calculator for Payroll Run

Handles calculation of regular and overtime gross pay for employees.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.services.payroll_run.constants import PERIODS_PER_YEAR


class GrossCalculator:
    """Calculates gross regular and overtime pay for employees."""

    @staticmethod
    def calculate_hourly_rate(employee: dict[str, Any]) -> Decimal:
        """Calculate employee's hourly rate for vacation pay calculation.

        For salaried employees: annual_salary / (standard_hours_per_week × 52)
        For hourly employees: use their hourly_rate directly

        Args:
            employee: Employee data dict with annual_salary or hourly_rate
                     and optional standard_hours_per_week (defaults to 40)

        Returns:
            Hourly rate as Decimal
        """
        hourly_rate = employee.get("hourly_rate")
        annual_salary = employee.get("annual_salary")

        if hourly_rate:
            return Decimal(str(hourly_rate))
        elif annual_salary:
            # Use employee's actual standard hours per week (default 40 if NULL or missing)
            std_hours = employee.get("standard_hours_per_week")
            weekly_hours = Decimal(str(std_hours)) if std_hours is not None else Decimal("40")
            if weekly_hours < 1:
                weekly_hours = Decimal("40")  # Fallback to 40 if invalid
            annual_hours = weekly_hours * Decimal("52")
            return Decimal(str(annual_salary)) / annual_hours
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

            # Use employee's actual standard hours per week (default 40 if NULL, minimum 1 to prevent division by zero)
            std_hours = employee.get("standard_hours_per_week")
            weekly_hours = Decimal(str(std_hours)) if std_hours is not None else Decimal("40")
            if weekly_hours < 1:
                weekly_hours = Decimal("40")  # Fallback to 40 if invalid
            annual_hours = weekly_hours * Decimal("52")
            implied_hourly = Decimal(str(annual_salary)) / annual_hours

            # Calculate standard hours for this pay period based on employee's weekly hours
            if pay_frequency == "weekly":
                standard_hours = weekly_hours
            elif pay_frequency == "bi_weekly":
                standard_hours = weekly_hours * 2
            elif pay_frequency == "semi_monthly":
                standard_hours = weekly_hours * Decimal("52") / Decimal("24")
            elif pay_frequency == "monthly":
                standard_hours = weekly_hours * Decimal("52") / Decimal("12")
            else:
                standard_hours = weekly_hours * 2  # default to bi-weekly

            if overrides.get("regularPay") is not None:
                # Manual override takes precedence
                gross_regular = Decimal(str(overrides["regularPay"]))
            elif input_data.get("regularHours") is not None:
                # Hours-based proration for salaried employees
                worked_hours = Decimal(str(input_data["regularHours"]))
                if worked_hours < standard_hours:
                    # Prorated: worked_hours × implied_hourly_rate
                    gross_regular = worked_hours * implied_hourly
                else:
                    # Full period (or more): use standard calculation
                    gross_regular = Decimal(str(annual_salary)) / Decimal(str(periods))
            else:
                # Default: standard period calculation
                gross_regular = Decimal(str(annual_salary)) / Decimal(str(periods))

            # Salaried overtime (using implied hourly rate)
            overtime_hours = Decimal(str(input_data.get("overtimeHours", 0)))
            if overtime_hours > 0:
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
