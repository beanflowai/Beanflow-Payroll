"""Tests for gross pay calculator."""

from decimal import Decimal

import pytest

from app.services.payroll_run.gross_calculator import GrossCalculator


class TestCalculateHourlyRate:
    """Tests for calculate_hourly_rate method."""

    def test_hourly_employee(self):
        """Test hourly rate for hourly employee."""
        employee = {"hourly_rate": 25.00}
        result = GrossCalculator.calculate_hourly_rate(employee)
        assert result == Decimal("25")

    def test_salaried_employee(self):
        """Test hourly rate calculation for salaried employee with default 40h/week."""
        employee = {"annual_salary": 52000}
        result = GrossCalculator.calculate_hourly_rate(employee)
        # 52000 / (40 * 52) = 52000 / 2080 = 25
        assert result == Decimal("25")

    def test_salaried_employee_37_5_hours_per_week(self):
        """Test hourly rate for salaried employee with 37.5h/week (common in Canada).

        Bug fix verification: Previously hardcoded 2080 hours, now uses standard_hours_per_week.
        """
        employee = {"annual_salary": 60000, "standard_hours_per_week": 37.5}
        result = GrossCalculator.calculate_hourly_rate(employee)
        # 60000 / (37.5 * 52) = 60000 / 1950 = 30.769230769...
        expected = Decimal("60000") / (Decimal("37.5") * Decimal("52"))
        assert result == expected
        # Verify it's NOT the old incorrect calculation
        incorrect_result = Decimal("60000") / Decimal("2080")  # Would be ~28.85
        assert result != incorrect_result

    def test_salaried_employee_35_hours_per_week(self):
        """Test hourly rate for salaried employee with 35h/week."""
        employee = {"annual_salary": 52000, "standard_hours_per_week": 35}
        result = GrossCalculator.calculate_hourly_rate(employee)
        # 52000 / (35 * 52) = 52000 / 1820 = 28.571428571...
        expected = Decimal("52000") / (Decimal("35") * Decimal("52"))
        assert result == expected

    def test_salaried_employee_invalid_hours_fallback(self):
        """Test that invalid standard_hours_per_week falls back to 40."""
        employee = {"annual_salary": 52000, "standard_hours_per_week": 0}
        result = GrossCalculator.calculate_hourly_rate(employee)
        # Should fall back to 40 hours/week
        expected = Decimal("52000") / Decimal("2080")
        assert result == expected

    def test_salaried_employee_negative_hours_fallback(self):
        """Test that negative standard_hours_per_week falls back to 40."""
        employee = {"annual_salary": 52000, "standard_hours_per_week": -10}
        result = GrossCalculator.calculate_hourly_rate(employee)
        # Should fall back to 40 hours/week
        expected = Decimal("52000") / Decimal("2080")
        assert result == expected

    def test_employee_with_both(self):
        """Test that hourly_rate takes precedence over annual_salary."""
        employee = {"hourly_rate": 30.00, "annual_salary": 52000}
        result = GrossCalculator.calculate_hourly_rate(employee)
        assert result == Decimal("30")

    def test_employee_with_neither(self):
        """Test employee with no pay info returns zero."""
        employee = {}
        result = GrossCalculator.calculate_hourly_rate(employee)
        assert result == Decimal("0")

    def test_decimal_precision(self):
        """Test decimal precision for salary calculation."""
        employee = {"annual_salary": 60000}
        result = GrossCalculator.calculate_hourly_rate(employee)
        # 60000 / (40 * 52) = 60000 / 2080 = 28.846153846...
        expected = Decimal("60000") / Decimal("2080")
        assert result == expected


class TestCalculateInitialGross:
    """Tests for calculate_initial_gross method."""

    def test_salaried_employee_weekly(self):
        """Test initial gross for salaried employee with weekly pay."""
        employee = {"annual_salary": 52000}
        gross_regular, gross_overtime = GrossCalculator.calculate_initial_gross(
            employee, "weekly"
        )
        # 52000 / 52 = 1000
        assert gross_regular == Decimal("1000")
        assert gross_overtime == Decimal("0")

    def test_salaried_employee_bi_weekly(self):
        """Test initial gross for salaried employee with bi-weekly pay."""
        employee = {"annual_salary": 52000}
        gross_regular, gross_overtime = GrossCalculator.calculate_initial_gross(
            employee, "bi_weekly"
        )
        # 52000 / 26 = 2000
        assert gross_regular == Decimal("2000")
        assert gross_overtime == Decimal("0")

    def test_salaried_employee_semi_monthly(self):
        """Test initial gross for salaried employee with semi-monthly pay."""
        employee = {"annual_salary": 48000}
        gross_regular, gross_overtime = GrossCalculator.calculate_initial_gross(
            employee, "semi_monthly"
        )
        # 48000 / 24 = 2000
        assert gross_regular == Decimal("2000")
        assert gross_overtime == Decimal("0")

    def test_salaried_employee_monthly(self):
        """Test initial gross for salaried employee with monthly pay."""
        employee = {"annual_salary": 60000}
        gross_regular, gross_overtime = GrossCalculator.calculate_initial_gross(
            employee, "monthly"
        )
        # 60000 / 12 = 5000
        assert gross_regular == Decimal("5000")
        assert gross_overtime == Decimal("0")

    def test_hourly_employee(self):
        """Test initial gross for hourly employee returns zero."""
        employee = {"hourly_rate": 25.00}
        gross_regular, gross_overtime = GrossCalculator.calculate_initial_gross(
            employee, "bi_weekly"
        )
        # Hourly employees start with 0 - user inputs hours
        assert gross_regular == Decimal("0")
        assert gross_overtime == Decimal("0")

    def test_employee_no_pay_info(self):
        """Test initial gross for employee with no pay info."""
        employee = {}
        gross_regular, gross_overtime = GrossCalculator.calculate_initial_gross(
            employee, "bi_weekly"
        )
        assert gross_regular == Decimal("0")
        assert gross_overtime == Decimal("0")

    def test_unknown_frequency_defaults_to_bi_weekly(self):
        """Test unknown frequency defaults to 26 periods."""
        employee = {"annual_salary": 52000}
        gross_regular, gross_overtime = GrossCalculator.calculate_initial_gross(
            employee, "unknown_frequency"
        )
        # 52000 / 26 = 2000
        assert gross_regular == Decimal("2000")
        assert gross_overtime == Decimal("0")


class TestCalculateGrossFromInput:
    """Tests for calculate_gross_from_input method."""

    def test_salaried_employee_no_input(self):
        """Test salaried employee with no input data."""
        employee = {"annual_salary": 52000}
        input_data = {}
        gross_regular, gross_overtime = GrossCalculator.calculate_gross_from_input(
            employee, input_data, "bi_weekly"
        )
        # 52000 / 26 = 2000
        assert gross_regular == Decimal("2000")
        assert gross_overtime == Decimal("0")

    def test_salaried_employee_with_regular_pay_override(self):
        """Test salaried employee with regular pay override."""
        employee = {"annual_salary": 52000}
        input_data = {"overrides": {"regularPay": 2500}}
        gross_regular, gross_overtime = GrossCalculator.calculate_gross_from_input(
            employee, input_data, "bi_weekly"
        )
        assert gross_regular == Decimal("2500")
        assert gross_overtime == Decimal("0")

    def test_salaried_employee_with_overtime(self):
        """Test salaried employee with overtime hours."""
        employee = {"annual_salary": 52000}
        input_data = {"overtimeHours": 10}
        gross_regular, gross_overtime = GrossCalculator.calculate_gross_from_input(
            employee, input_data, "bi_weekly"
        )
        # Gross regular: 52000 / 26 = 2000
        # Hourly rate: 2000 / 80 = 25
        # Overtime: 10 * 25 * 1.5 = 375
        assert gross_regular == Decimal("2000")
        assert gross_overtime == Decimal("375")

    def test_hourly_employee_with_hours(self):
        """Test hourly employee with regular hours."""
        employee = {"hourly_rate": 20.00}
        input_data = {"regularHours": 40}
        gross_regular, gross_overtime = GrossCalculator.calculate_gross_from_input(
            employee, input_data, "bi_weekly"
        )
        # 40 * 20 = 800
        assert gross_regular == Decimal("800")
        assert gross_overtime == Decimal("0")

    def test_hourly_employee_with_overtime(self):
        """Test hourly employee with overtime hours."""
        employee = {"hourly_rate": 20.00}
        input_data = {"regularHours": 80, "overtimeHours": 10}
        gross_regular, gross_overtime = GrossCalculator.calculate_gross_from_input(
            employee, input_data, "bi_weekly"
        )
        # Regular: 80 * 20 = 1600
        # Overtime: 10 * 20 * 1.5 = 300
        assert gross_regular == Decimal("1600")
        assert gross_overtime == Decimal("300")

    def test_hourly_employee_with_regular_pay_override(self):
        """Test hourly employee with regular pay override."""
        employee = {"hourly_rate": 20.00}
        input_data = {"regularHours": 80, "overrides": {"regularPay": 2000}}
        gross_regular, gross_overtime = GrossCalculator.calculate_gross_from_input(
            employee, input_data, "bi_weekly"
        )
        assert gross_regular == Decimal("2000")
        assert gross_overtime == Decimal("0")

    def test_hourly_employee_with_overtime_pay_override(self):
        """Test hourly employee with overtime pay override."""
        employee = {"hourly_rate": 20.00}
        input_data = {"overtimeHours": 10, "overrides": {"overtimePay": 500}}
        gross_regular, gross_overtime = GrossCalculator.calculate_gross_from_input(
            employee, input_data, "bi_weekly"
        )
        assert gross_regular == Decimal("0")
        assert gross_overtime == Decimal("500")

    def test_hourly_employee_with_vacation_leave(self):
        """Test hourly employee with vacation leave entries."""
        employee = {"hourly_rate": 20.00}
        input_data = {
            "regularHours": 40,
            "leaveEntries": [{"type": "vacation", "hours": 8}],
        }
        gross_regular, gross_overtime = GrossCalculator.calculate_gross_from_input(
            employee, input_data, "bi_weekly"
        )
        # Regular: 40 * 20 = 800
        # Vacation: 8 * 20 = 160
        # Total regular: 800 + 160 = 960
        assert gross_regular == Decimal("960")
        assert gross_overtime == Decimal("0")

    def test_hourly_employee_sick_leave_not_added(self):
        """Test that sick leave is NOT added to gross (handled elsewhere)."""
        employee = {"hourly_rate": 20.00}
        input_data = {
            "regularHours": 40,
            "leaveEntries": [{"type": "sick", "hours": 8}],
        }
        gross_regular, gross_overtime = GrossCalculator.calculate_gross_from_input(
            employee, input_data, "bi_weekly"
        )
        # Regular: 40 * 20 = 800
        # Sick leave NOT added here (handled in run_operations)
        assert gross_regular == Decimal("800")
        assert gross_overtime == Decimal("0")

    def test_hourly_employee_multiple_leave_entries(self):
        """Test hourly employee with multiple leave entries."""
        employee = {"hourly_rate": 25.00}
        input_data = {
            "regularHours": 32,
            "leaveEntries": [
                {"type": "vacation", "hours": 8},
                {"type": "vacation", "hours": 4},
                {"type": "sick", "hours": 8},  # Not counted
            ],
        }
        gross_regular, gross_overtime = GrossCalculator.calculate_gross_from_input(
            employee, input_data, "bi_weekly"
        )
        # Regular: 32 * 25 = 800
        # Vacation: 8 * 25 = 200
        # Vacation: 4 * 25 = 100
        # Total: 800 + 200 + 100 = 1100
        assert gross_regular == Decimal("1100")
        assert gross_overtime == Decimal("0")

    def test_employee_with_no_pay_info(self):
        """Test employee with no pay info returns zeros."""
        employee = {}
        input_data = {"regularHours": 80}
        gross_regular, gross_overtime = GrossCalculator.calculate_gross_from_input(
            employee, input_data, "bi_weekly"
        )
        assert gross_regular == Decimal("0")
        assert gross_overtime == Decimal("0")

    def test_none_overrides(self):
        """Test handling of None overrides."""
        employee = {"annual_salary": 52000}
        input_data = {"overrides": None}
        gross_regular, gross_overtime = GrossCalculator.calculate_gross_from_input(
            employee, input_data, "bi_weekly"
        )
        assert gross_regular == Decimal("2000")
        assert gross_overtime == Decimal("0")

    def test_none_leave_entries(self):
        """Test handling of None leave entries."""
        employee = {"hourly_rate": 20.00}
        input_data = {"regularHours": 40, "leaveEntries": None}
        gross_regular, gross_overtime = GrossCalculator.calculate_gross_from_input(
            employee, input_data, "bi_weekly"
        )
        assert gross_regular == Decimal("800")
        assert gross_overtime == Decimal("0")

    def test_salaried_employee_with_prorated_hours(self):
        """Test salaried employee with hours less than standard for proration."""
        employee = {"annual_salary": 52000}  # $25/hr implied rate (52000/2080)
        input_data = {"regularHours": 40}  # Half of bi-weekly standard (80 hrs)
        gross_regular, gross_overtime = GrossCalculator.calculate_gross_from_input(
            employee, input_data, "bi_weekly"
        )
        # Prorated: 40 hours × $25/hr = $1000
        assert gross_regular == Decimal("1000")
        assert gross_overtime == Decimal("0")

    def test_salaried_employee_full_standard_hours(self):
        """Test salaried employee with full standard hours (no proration)."""
        employee = {"annual_salary": 52000}
        input_data = {"regularHours": 80}  # Full bi-weekly standard
        gross_regular, gross_overtime = GrossCalculator.calculate_gross_from_input(
            employee, input_data, "bi_weekly"
        )
        # Full period: $52000 / 26 = $2000
        assert gross_regular == Decimal("2000")
        assert gross_overtime == Decimal("0")

    def test_salaried_employee_prorated_semi_monthly(self):
        """Test salaried employee proration with semi-monthly frequency."""
        employee = {"annual_salary": 62400}  # $30/hr implied rate (62400/2080)
        input_data = {"regularHours": 43.335}  # Half of semi-monthly standard (86.67)
        gross_regular, gross_overtime = GrossCalculator.calculate_gross_from_input(
            employee, input_data, "semi_monthly"
        )
        # Prorated: 43.335 hours × $30/hr = $1300.05
        expected = Decimal("43.335") * (Decimal("62400") / Decimal("2080"))
        assert gross_regular == expected
        assert gross_overtime == Decimal("0")

    def test_salaried_employee_zero_hours(self):
        """Test salaried employee with zero hours (e.g., unpaid leave entire period)."""
        employee = {"annual_salary": 52000}
        input_data = {"regularHours": 0}
        gross_regular, gross_overtime = GrossCalculator.calculate_gross_from_input(
            employee, input_data, "bi_weekly"
        )
        # Zero hours = zero pay
        assert gross_regular == Decimal("0")
        assert gross_overtime == Decimal("0")

    def test_salaried_employee_proration_override_takes_precedence(self):
        """Test that manual override takes precedence over proration."""
        employee = {"annual_salary": 52000}
        input_data = {
            "regularHours": 40,  # Would prorate to $1000
            "overrides": {"regularPay": 1500},  # Override to $1500
        }
        gross_regular, gross_overtime = GrossCalculator.calculate_gross_from_input(
            employee, input_data, "bi_weekly"
        )
        # Override should win
        assert gross_regular == Decimal("1500")
        assert gross_overtime == Decimal("0")
