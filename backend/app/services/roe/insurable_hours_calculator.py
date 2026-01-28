"""Insurable Hours Calculator for ROE (Record of Employment).

Calculates insurable hours for EI purposes as required by the CRA.

For salaried employees:
    Uses standard_hours_per_week to calculate hours based on the pay period.

For hourly employees:
    Sums actual hours worked from payroll records.

Reference:
    - Service Canada ROE guidelines
    - EI Act regulations on insurable hours
"""

from datetime import date
from decimal import Decimal

from app.models.payroll import Employee, PayrollRecord


class InsurableHoursCalculator:
    """Calculator for ROE insurable hours.

    Insurable hours are required on the ROE form for EI eligibility determination.
    The calculation method differs based on compensation type:

    - Salaried: Use contractual hours (standard_hours_per_week)
    - Hourly: Use actual hours worked from payroll records
    """

    @staticmethod
    def calculate_for_period(
        employee: Employee,
        period_start: date,
        period_end: date,
        payroll_records: list[PayrollRecord] | None = None,
    ) -> Decimal:
        """Calculate insurable hours for a specific period.

        Args:
            employee: Employee model with compensation details
            period_start: Start date of the ROE period
            period_end: End date of the ROE period
            payroll_records: Payroll records for the period (required for hourly)

        Returns:
            Total insurable hours for the period as Decimal

        Note:
            For salaried employees, this calculates based on weeks in the period.
            For hourly employees, this sums actual hours from payroll records.
        """
        if InsurableHoursCalculator._is_salaried(employee):
            return InsurableHoursCalculator._calculate_salaried_hours(
                employee, period_start, period_end
            )
        else:
            return InsurableHoursCalculator._calculate_hourly_hours(
                payroll_records or []
            )

    @staticmethod
    def _is_salaried(employee: Employee) -> bool:
        """Check if employee is salaried (has annual salary, no hourly rate)."""
        return (
            employee.annual_salary is not None
            and employee.annual_salary > 0
            and (employee.hourly_rate is None or employee.hourly_rate == 0)
        )

    @staticmethod
    def _calculate_salaried_hours(
        employee: Employee,
        period_start: date,
        period_end: date,
    ) -> Decimal:
        """Calculate insurable hours for salaried employee.

        Uses standard_hours_per_week to calculate based on weeks in the period.

        Args:
            employee: Salaried employee
            period_start: Period start date
            period_end: Period end date

        Returns:
            Insurable hours based on contractual weekly hours
        """
        # Calculate weeks in the period (inclusive of both dates)
        days_in_period = (period_end - period_start).days + 1
        weeks_in_period = Decimal(str(days_in_period)) / Decimal("7")

        # Use standard hours per week (default 40 if not set)
        weekly_hours = employee.standard_hours_per_week or Decimal("40")

        return (weekly_hours * weeks_in_period).quantize(Decimal("0.01"))

    @staticmethod
    def _calculate_hourly_hours(
        payroll_records: list[PayrollRecord],
    ) -> Decimal:
        """Calculate insurable hours for hourly employee.

        Sums actual regular and overtime hours from payroll records.

        Args:
            payroll_records: List of payroll records for the period

        Returns:
            Total hours worked from payroll records
        """
        total_hours = Decimal("0")

        for record in payroll_records:
            # Add regular hours
            if record.regular_hours_worked:
                total_hours += record.regular_hours_worked

            # Add overtime hours
            if record.overtime_hours_worked:
                total_hours += record.overtime_hours_worked

        return total_hours.quantize(Decimal("0.01"))


def calculate_insurable_hours(
    employee: Employee,
    period_start: date,
    period_end: date,
    payroll_records: list[PayrollRecord] | None = None,
) -> Decimal:
    """Convenience function to calculate insurable hours.

    This is a wrapper around InsurableHoursCalculator.calculate_for_period()
    for simpler API usage.

    Args:
        employee: Employee model
        period_start: Start date of ROE period
        period_end: End date of ROE period
        payroll_records: Payroll records (required for hourly employees)

    Returns:
        Insurable hours for the period

    Example:
        >>> # For a salaried employee with 40h/week over 4 weeks
        >>> hours = calculate_insurable_hours(
        ...     employee=salaried_emp,
        ...     period_start=date(2026, 1, 1),
        ...     period_end=date(2026, 1, 28),
        ... )
        >>> hours
        Decimal('160.00')

        >>> # For an hourly employee with actual hours
        >>> hours = calculate_insurable_hours(
        ...     employee=hourly_emp,
        ...     period_start=date(2026, 1, 1),
        ...     period_end=date(2026, 1, 28),
        ...     payroll_records=records,
        ... )
    """
    return InsurableHoursCalculator.calculate_for_period(
        employee, period_start, period_end, payroll_records
    )
