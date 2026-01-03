"""
Tests for Holiday Pay Formula Calculations.

Tests:
- BC 30-day average formula
- Ontario 4-week average formula
- Current period daily formula
"""

from datetime import date
from decimal import Decimal

from app.services.payroll_run.holiday_pay_calculator import WORK_DAYS_PER_PERIOD
from tests.payroll.conftest import make_bc_config


class TestBCFormula:
    """Tests for BC holiday pay formula: default_daily_hours × hourly_rate."""

    def test_bc_hourly_employee(self, holiday_calculator, hourly_employee):
        """BC formula should calculate 8h × hourly_rate."""
        config = make_bc_config()
        daily_pay = holiday_calculator._apply_30_day_average(
            hourly_employee, config.formula_params.default_daily_hours
        )

        # 8h × $25/hr = $200
        assert daily_pay == Decimal("200")

    def test_bc_salaried_employee(self, holiday_calculator, salaried_employee):
        """BC formula should derive hourly rate from salary for calculation."""
        config = make_bc_config()
        daily_pay = holiday_calculator._apply_30_day_average(
            salaried_employee, config.formula_params.default_daily_hours
        )

        # 8h × ($60000/2080) = 8 × $28.846... ≈ $230.77
        expected = Decimal("8") * (Decimal("60000") / Decimal("2080"))
        assert daily_pay == expected


class TestCurrentPeriodFormula:
    """Tests for current period daily formula."""

    def test_bi_weekly(self, holiday_calculator):
        """Current period formula for bi-weekly pay period."""
        current_gross = Decimal("2000")
        pay_frequency = "bi_weekly"

        daily_pay = holiday_calculator._apply_current_period_daily(current_gross, pay_frequency)

        # $2000 / 10 work days = $200
        assert daily_pay == Decimal("200")

    def test_weekly(self, holiday_calculator):
        """Current period formula for weekly pay period."""
        current_gross = Decimal("1000")
        pay_frequency = "weekly"

        daily_pay = holiday_calculator._apply_current_period_daily(current_gross, pay_frequency)

        # $1000 / 5 work days = $200
        assert daily_pay == Decimal("200")

    def test_monthly(self, holiday_calculator):
        """Current period formula for monthly pay period."""
        current_gross = Decimal("4000")
        pay_frequency = "monthly"

        daily_pay = holiday_calculator._apply_current_period_daily(current_gross, pay_frequency)

        # $4000 / 21.67 work days ≈ $184.59
        expected = current_gross / WORK_DAYS_PER_PERIOD["monthly"]
        assert daily_pay == expected


class TestOntarioFormula:
    """Tests for Ontario formula: (past 4 weeks wages + vacation) / 20."""

    def test_ontario_with_history(self, holiday_calculator, mock_supabase):
        """Ontario formula with historical payroll data."""
        # Mock historical data query
        mock_supabase.table.return_value.select.return_value.eq.return_value.neq.return_value.gte.return_value.lt.return_value.in_.return_value.execute.return_value.data = [
            {"gross_regular": 1000, "gross_overtime": 200, "vacation_pay_paid": 50},
            {"gross_regular": 1000, "gross_overtime": 150, "vacation_pay_paid": 50},
        ]

        employee = {"id": "emp-001", "hourly_rate": 25.00}

        daily_pay = holiday_calculator._apply_4_week_average(
            employee_id="emp-001",
            holiday_date=date(2025, 7, 1),
            current_run_id="run-001",
            divisor=20,
            include_vacation_pay=True,
            employee_fallback=employee,
            new_employee_fallback="pro_rated",
        )

        # total_wages = (1000+200) + (1000+150) = 2350
        # vacation_pay = 50 + 50 = 100
        # (2350 + 100) / 20 = $122.50
        expected = (Decimal("2350") + Decimal("100")) / Decimal("20")
        assert daily_pay == expected

    def test_ontario_no_history_fallback(self, holiday_calculator, mock_supabase):
        """Ontario formula should fall back to 30-day avg when no history."""
        # Mock empty historical data
        mock_supabase.table.return_value.select.return_value.eq.return_value.neq.return_value.gte.return_value.lt.return_value.in_.return_value.execute.return_value.data = []

        employee = {"id": "emp-001", "hourly_rate": 25.00}

        daily_pay = holiday_calculator._apply_4_week_average(
            employee_id="emp-001",
            holiday_date=date(2025, 7, 1),
            current_run_id="run-001",
            divisor=20,
            include_vacation_pay=True,
            employee_fallback=employee,
            new_employee_fallback="pro_rated",
        )

        # Falls back to 30-day avg: 8h × $25 = $200
        assert daily_pay == Decimal("200")
