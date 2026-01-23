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
    """Tests for BC holiday pay formula: wages in 30 days / days worked."""

    def test_bc_hourly_employee(self, holiday_calculator, hourly_employee, mock_supabase):
        """BC formula with timesheet data should calculate wages / days worked."""
        # Mock timesheet entries: 10 days worked, 8 hours each day
        mock_supabase.table.return_value.select.return_value.eq.return_value.gte.return_value.lte.return_value.execute.return_value.data = [
            {"work_date": "2025-06-15", "regular_hours": 8, "overtime_hours": 0},
            {"work_date": "2025-06-16", "regular_hours": 8, "overtime_hours": 0},
            {"work_date": "2025-06-17", "regular_hours": 8, "overtime_hours": 0},
            {"work_date": "2025-06-18", "regular_hours": 8, "overtime_hours": 0},
            {"work_date": "2025-06-19", "regular_hours": 8, "overtime_hours": 0},
            {"work_date": "2025-06-22", "regular_hours": 8, "overtime_hours": 0},
            {"work_date": "2025-06-23", "regular_hours": 8, "overtime_hours": 0},
            {"work_date": "2025-06-24", "regular_hours": 8, "overtime_hours": 0},
            {"work_date": "2025-06-25", "regular_hours": 8, "overtime_hours": 0},
            {"work_date": "2025-06-26", "regular_hours": 8, "overtime_hours": 0},
        ]
        config = make_bc_config()
        daily_pay = holiday_calculator._apply_30_day_average(
            employee_id=hourly_employee["id"],
            employee=hourly_employee,
            holiday_date=date(2025, 7, 1),
            method=config.formula_params.method or "total_wages_div_days",
            include_overtime=config.formula_params.include_overtime,
            default_daily_hours=config.formula_params.default_daily_hours,
            new_employee_fallback=config.formula_params.new_employee_fallback,
        )

        # 10 days × 8h × $25/hr = $2000, divided by 10 days = $200/day
        assert daily_pay == Decimal("200")

    def test_bc_salaried_employee(self, holiday_calculator, salaried_employee, mock_supabase):
        """BC formula should derive hourly rate from salary for calculation."""
        # Mock timesheet entries: 10 days worked
        mock_supabase.table.return_value.select.return_value.eq.return_value.gte.return_value.lte.return_value.execute.return_value.data = [
            {"work_date": f"2025-06-{15+i}", "regular_hours": 8, "overtime_hours": 0}
            for i in range(10)
        ]
        config = make_bc_config()
        daily_pay = holiday_calculator._apply_30_day_average(
            employee_id=salaried_employee["id"],
            employee=salaried_employee,
            holiday_date=date(2025, 7, 1),
            method=config.formula_params.method or "total_wages_div_days",
            include_overtime=config.formula_params.include_overtime,
            default_daily_hours=config.formula_params.default_daily_hours,
            new_employee_fallback=config.formula_params.new_employee_fallback,
        )

        # 10 days × 8h × ($60000/2080) = 10 days, wage = 80h × hourly_rate
        # daily_pay = (80h × hourly_rate) / 10 = 8h × hourly_rate
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
        """Ontario formula with historical payroll data (overtime excluded)."""
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
            include_overtime=False,  # Ontario excludes overtime
            employee_fallback=employee,
            new_employee_fallback="pro_rated",
        )

        # total_wages = 1000 + 1000 = 2000 (overtime excluded!)
        # vacation_pay = 50 + 50 = 100
        # (2000 + 100) / 20 = $105.00
        expected = (Decimal("2000") + Decimal("100")) / Decimal("20")
        assert daily_pay == expected

    def test_ontario_no_history_fallback(self, holiday_calculator, mock_supabase):
        """Ontario formula should fall back to hourly rate when no history."""
        # Mock empty historical data
        mock_supabase.table.return_value.select.return_value.eq.return_value.neq.return_value.gte.return_value.lt.return_value.in_.return_value.execute.return_value.data = []

        employee = {"id": "emp-001", "hourly_rate": 25.00}

        daily_pay = holiday_calculator._apply_4_week_average(
            employee_id="emp-001",
            holiday_date=date(2025, 7, 1),
            current_run_id="run-001",
            divisor=20,
            include_vacation_pay=True,
            include_overtime=False,
            employee_fallback=employee,
            new_employee_fallback="pro_rated",
        )

        # Falls back to hourly rate: 8h × $25 = $200
        assert daily_pay == Decimal("200")
