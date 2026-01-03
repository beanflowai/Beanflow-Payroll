"""
Tests for Holiday Pay Eligibility Rules.

Tests:
- Config-driven eligibility checks
- Province-specific employment day requirements
- New employee fallback behavior
- NB 90-day requirement
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.services.payroll_run.holiday_pay_calculator import HolidayPayCalculator
from tests.payroll.conftest import (
    MockConfigLoader,
    make_ab_config,
    make_bc_config,
    make_on_config,
    make_qc_config,
    make_sk_config,
)


class TestEligibilityCheck:
    """Tests for config-driven eligibility rules."""

    def test_bc_eligible_employee(self, holiday_calculator, hourly_employee):
        """BC: Employee hired >30 days ago should be eligible."""
        config = make_bc_config()
        holiday_date = date(2025, 7, 1)

        result = holiday_calculator._is_eligible_for_holiday_pay(
            hourly_employee, holiday_date, config
        )

        assert result is True

    def test_bc_ineligible_new_hire(self, holiday_calculator, new_hire_employee):
        """BC: Employee hired <30 days ago should not be eligible."""
        config = make_bc_config()
        holiday_date = date.today()

        result = holiday_calculator._is_eligible_for_holiday_pay(
            new_hire_employee, holiday_date, config
        )

        assert result is False

    def test_ontario_no_min_days_requirement(self, holiday_calculator, new_hire_employee):
        """Ontario: No minimum employment days requirement."""
        config = make_on_config()
        holiday_date = date.today()

        # Even a new hire should be eligible in Ontario (no 30-day rule)
        result = holiday_calculator._is_eligible_for_holiday_pay(
            new_hire_employee, holiday_date, config
        )

        assert result is True  # Ontario has min_employment_days = 0

    def test_exactly_30_days(self, holiday_calculator):
        """BC: Employee hired exactly 30 days ago should be eligible."""
        config = make_bc_config()
        holiday_date = date(2025, 2, 1)
        employee = {
            "id": "emp-exact",
            "hire_date": "2025-01-02",  # Exactly 30 days before Feb 1
        }

        result = holiday_calculator._is_eligible_for_holiday_pay(
            employee, holiday_date, config
        )

        assert result is True

    def test_no_hire_date(self, holiday_calculator):
        """Employee without hire_date should be assumed eligible."""
        config = make_bc_config()
        employee = {"id": "emp-no-date"}
        holiday_date = date(2025, 1, 1)

        result = holiday_calculator._is_eligible_for_holiday_pay(
            employee, holiday_date, config
        )

        assert result is True


class TestNewEmployeeFallback:
    """Tests for new_employee_fallback config behavior.

    Tests the difference between:
    - "pro_rated": Use current period gross or 30-day avg fallback
    - "ineligible": Return $0 when no historical data
    """

    @pytest.fixture
    def new_hire_sk(self):
        """New employee in Saskatchewan (no 30-day min)."""
        return {
            "id": "emp-sk-new",
            "first_name": "New",
            "last_name": "Saskatchewan",
            "hourly_rate": 20.00,
            "annual_salary": None,
            "hire_date": (date.today() - timedelta(days=10)).isoformat(),
            "province_of_employment": "SK",
        }

    @pytest.fixture
    def new_hire_ab(self):
        """New employee in Alberta (30-day min required)."""
        return {
            "id": "emp-ab-new",
            "first_name": "New",
            "last_name": "Alberta",
            "hourly_rate": 25.00,
            "annual_salary": None,
            "hire_date": (date.today() - timedelta(days=10)).isoformat(),
            "province_of_employment": "AB",
        }

    def test_sk_new_employee_pro_rated_uses_current_gross(self, mock_supabase):
        """SK: New employee with no history uses current_period_gross (pro_rated)."""
        # Setup calculator with SK config
        sk_loader = MockConfigLoader({"SK": make_sk_config()})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=sk_loader,
        )

        # Mock empty historical data
        mock_supabase.table.return_value.select.return_value.eq.return_value.neq.return_value.gte.return_value.lt.return_value.in_.return_value.execute.return_value.data = []

        new_hire = {
            "id": "emp-sk-new",
            "first_name": "New",
            "last_name": "SK",
            "hourly_rate": 20.00,
            "hire_date": (date.today() - timedelta(days=10)).isoformat(),
        }

        holiday_date = date.today()
        holidays = [{"holiday_date": holiday_date.isoformat(), "name": "Test Holiday", "province": "SK"}]

        result = calculator.calculate_holiday_pay(
            employee=new_hire,
            province="SK",
            pay_frequency="bi_weekly",
            period_start=holiday_date - timedelta(days=7),
            period_end=holiday_date + timedelta(days=7),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("1600"),  # Use this as base
            current_run_id="run-001",
        )

        # SK pro_rated: uses current_period_gross × 5% = $1600 × 0.05 = $80
        assert result.regular_holiday_pay == Decimal("80")
        assert result.premium_holiday_pay == Decimal("0")

    def test_ab_new_employee_ineligible_returns_zero(self, mock_supabase):
        """AB: New employee with no history returns $0 (ineligible fallback)."""
        # Setup calculator with AB config (ineligible fallback)
        ab_loader = MockConfigLoader({"AB": make_ab_config()})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=ab_loader,
        )

        # Mock empty historical data
        mock_supabase.table.return_value.select.return_value.eq.return_value.neq.return_value.gte.return_value.lt.return_value.in_.return_value.execute.return_value.data = []

        # Employee with >30 days employment (eligible by min_days) but no historical payroll
        eligible_no_history = {
            "id": "emp-ab-eligible",
            "first_name": "Eligible",
            "last_name": "NoHistory",
            "hourly_rate": 25.00,
            "hire_date": (date.today() - timedelta(days=45)).isoformat(),
        }

        holiday_date = date.today()
        holidays = [{"holiday_date": holiday_date.isoformat(), "name": "Test Holiday", "province": "AB"}]

        result = calculator.calculate_holiday_pay(
            employee=eligible_no_history,
            province="AB",
            pay_frequency="bi_weekly",
            period_start=holiday_date - timedelta(days=7),
            period_end=holiday_date + timedelta(days=7),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("2000"),
            current_run_id="run-001",
        )

        # AB ineligible: no historical data → $0
        assert result.regular_holiday_pay == Decimal("0")

    def test_on_new_employee_pro_rated_uses_30_day_avg(self, mock_supabase):
        """ON: New employee with no history uses 30-day avg fallback (pro_rated)."""
        # Setup calculator with ON config
        on_loader = MockConfigLoader({"ON": make_on_config()})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=on_loader,
        )

        # Mock empty historical data
        mock_supabase.table.return_value.select.return_value.eq.return_value.neq.return_value.gte.return_value.lt.return_value.in_.return_value.execute.return_value.data = []

        new_hire = {
            "id": "emp-on-new",
            "first_name": "New",
            "last_name": "Ontario",
            "hourly_rate": 22.00,
            "hire_date": (date.today() - timedelta(days=5)).isoformat(),
        }

        holiday_date = date.today()
        holidays = [{"holiday_date": holiday_date.isoformat(), "name": "Test Holiday", "province": "ON"}]

        result = calculator.calculate_holiday_pay(
            employee=new_hire,
            province="ON",
            pay_frequency="bi_weekly",
            period_start=holiday_date - timedelta(days=7),
            period_end=holiday_date + timedelta(days=7),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("1760"),
            current_run_id="run-001",
        )

        # ON pro_rated: falls back to 30-day avg: 8h × $22 = $176
        assert result.regular_holiday_pay == Decimal("176")

    def test_bc_new_hire_ineligible_by_min_days(self, mock_supabase):
        """BC: New hire <30 days is ineligible by min_employment_days."""
        bc_loader = MockConfigLoader({"BC": make_bc_config()})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=bc_loader,
        )

        new_hire = {
            "id": "emp-bc-new",
            "first_name": "New",
            "last_name": "BC",
            "hourly_rate": 20.00,
            "hire_date": (date.today() - timedelta(days=15)).isoformat(),
        }

        holiday_date = date.today()
        holidays = [{"holiday_date": holiday_date.isoformat(), "name": "Test Holiday", "province": "BC"}]

        result = calculator.calculate_holiday_pay(
            employee=new_hire,
            province="BC",
            pay_frequency="bi_weekly",
            period_start=holiday_date - timedelta(days=7),
            period_end=holiday_date + timedelta(days=7),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("1600"),
            current_run_id="run-001",
        )

        # BC: <30 days employed → ineligible (not due to fallback, but min_days)
        assert result.regular_holiday_pay == Decimal("0")
        # Check details show ineligibility
        assert result.calculation_details["holidays"][0]["eligible"] is False

    def test_qc_new_employee_eligible_no_min_days(self, mock_supabase):
        """QC: New employee is eligible (no min employment days)."""
        qc_loader = MockConfigLoader({"QC": make_qc_config()})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=qc_loader,
        )

        new_hire = {
            "id": "emp-qc-new",
            "first_name": "New",
            "last_name": "Quebec",
            "hourly_rate": 18.00,
            "hire_date": (date.today() - timedelta(days=5)).isoformat(),
        }

        holiday_date = date.today()
        holidays = [{"holiday_date": holiday_date.isoformat(), "name": "Test Holiday", "province": "QC"}]

        result = calculator.calculate_holiday_pay(
            employee=new_hire,
            province="QC",
            pay_frequency="bi_weekly",
            period_start=holiday_date - timedelta(days=7),
            period_end=holiday_date + timedelta(days=7),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("1440"),
            current_run_id="run-001",
        )

        # QC: min_employment_days=0, uses 30-day avg: 8h × $18 = $144
        assert result.regular_holiday_pay == Decimal("144")
        assert result.calculation_details["holidays"][0]["eligible"] is True


class TestNBEligibility:
    """Tests for New Brunswick's 90-day employment requirement."""

    def test_nb_employee_under_90_days_ineligible(self, mock_supabase):
        """NB: Employee with <90 days employment is not eligible."""
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
        )

        # Employee hired 60 days ago (< 90 days required)
        employee = {
            "id": "emp-nb-new",
            "first_name": "New",
            "last_name": "Brunswick",
            "hourly_rate": 20.00,
            "hire_date": (date.today() - timedelta(days=60)).isoformat(),
        }

        holiday_date = date.today()
        holidays = [{"holiday_date": holiday_date.isoformat(), "name": "Test Holiday", "province": "NB"}]

        result = calculator.calculate_holiday_pay(
            employee=employee,
            province="NB",
            pay_frequency="bi_weekly",
            period_start=holiday_date - timedelta(days=7),
            period_end=holiday_date + timedelta(days=7),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("1600"),
            current_run_id="run-001",
        )

        # NB: <90 days employed → ineligible for regular pay
        assert result.regular_holiday_pay == Decimal("0")
        assert result.calculation_details["holidays"][0]["eligible"] is False
        assert "< 90 days" in result.calculation_details["holidays"][0].get("ineligibility_reason", "")

    def test_nb_employee_over_90_days_eligible(self, mock_supabase):
        """NB: Employee with ≥90 days employment is eligible."""
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
        )

        # Employee hired 100 days ago (≥ 90 days)
        employee = {
            "id": "emp-nb-senior",
            "first_name": "Senior",
            "last_name": "Brunswick",
            "hourly_rate": 22.00,
            "hire_date": (date.today() - timedelta(days=100)).isoformat(),
        }

        holiday_date = date.today()
        holidays = [{"holiday_date": holiday_date.isoformat(), "name": "Test Holiday", "province": "NB"}]

        result = calculator.calculate_holiday_pay(
            employee=employee,
            province="NB",
            pay_frequency="bi_weekly",
            period_start=holiday_date - timedelta(days=7),
            period_end=holiday_date + timedelta(days=7),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("1760"),
            current_run_id="run-002",
        )

        # NB: ≥90 days employed → eligible
        # Uses 30_day_average: 8h × $22 = $176
        assert result.regular_holiday_pay == Decimal("176")
        assert result.calculation_details["holidays"][0]["eligible"] is True

    def test_nb_exactly_90_days_eligible(self, mock_supabase):
        """NB: Employee with exactly 90 days employment is eligible."""
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
        )

        holiday_date = date(2025, 4, 1)
        # Hired exactly 90 days before holiday
        hire_date = holiday_date - timedelta(days=90)

        employee = {
            "id": "emp-nb-exact",
            "first_name": "Exact",
            "last_name": "Ninety",
            "hourly_rate": 20.00,
            "hire_date": hire_date.isoformat(),
        }

        holidays = [{"holiday_date": holiday_date.isoformat(), "name": "Test Holiday", "province": "NB"}]

        result = calculator.calculate_holiday_pay(
            employee=employee,
            province="NB",
            pay_frequency="bi_weekly",
            period_start=holiday_date - timedelta(days=7),
            period_end=holiday_date + timedelta(days=7),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("1600"),
            current_run_id="run-003",
        )

        # NB: exactly 90 days → eligible
        assert result.regular_holiday_pay == Decimal("160")  # 8h × $20
        assert result.calculation_details["holidays"][0]["eligible"] is True
