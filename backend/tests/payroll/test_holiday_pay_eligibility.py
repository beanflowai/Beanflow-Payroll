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
from unittest.mock import MagicMock

import pytest

from app.services.payroll_run.holiday_pay_calculator import HolidayPayCalculator
from tests.payroll.conftest import (
    MockConfigLoader,
    make_ab_config,
    make_bc_config,
    make_on_config,
    make_pe_config,
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
        """Employee without hire_date should be marked ineligible."""
        config = make_bc_config()
        employee = {"id": "emp-no-date"}
        holiday_date = date(2025, 1, 1)

        result = holiday_calculator._is_eligible_for_holiday_pay(
            employee, holiday_date, config
        )

        # Employee without hire_date is ineligible
        assert result is False


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

        holiday_date = date.today()

        # Mock Supabase queries - need to handle both payroll_records AND timesheet_entries
        def mock_table(table_name):
            mock = MagicMock()
            if table_name == "timesheet_entries":
                # Return work entries before and after holiday for last_first_rule
                mock.select.return_value.eq.return_value.gte.return_value.lte.return_value.execute.return_value.data = [
                    {"work_date": (holiday_date - timedelta(days=1)).isoformat(), "regular_hours": 8, "overtime_hours": 0},
                    {"work_date": (holiday_date + timedelta(days=1)).isoformat(), "regular_hours": 8, "overtime_hours": 0},
                ]
            else:
                # Return empty historical payroll data
                mock.select.return_value.eq.return_value.neq.return_value.gte.return_value.lt.return_value.in_.return_value.execute.return_value.data = []
            return mock

        mock_supabase.table.side_effect = mock_table

        new_hire = {
            "id": "emp-on-new",
            "first_name": "New",
            "last_name": "Ontario",
            "hourly_rate": 22.00,
            "hire_date": (date.today() - timedelta(days=5)).isoformat(),
        }

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


class TestLastFirstRule:
    """Tests for require_last_first_rule eligibility check."""

    def test_on_passes_with_work_before_and_after(self, holiday_calculator):
        """ON: Employee who worked before and after holiday is eligible."""
        config = make_on_config()
        holiday_date = date(2025, 12, 25)

        employee = {
            "id": "emp-on-pass",
            "hire_date": "2024-01-01",
        }

        # Worked on Dec 24 (before) and Dec 26 (after)
        timesheet_entries = [
            {"work_date": "2025-12-24", "regular_hours": 8, "overtime_hours": 0},
            {"work_date": "2025-12-26", "regular_hours": 8, "overtime_hours": 0},
        ]

        result = holiday_calculator._is_eligible_for_holiday_pay(
            employee, holiday_date, config, timesheet_entries
        )

        assert result is True

    def test_on_fails_with_only_work_before(self, holiday_calculator):
        """ON: Employee who only worked before holiday is ineligible."""
        config = make_on_config()
        holiday_date = date(2025, 12, 25)

        employee = {
            "id": "emp-on-fail-before",
            "hire_date": "2024-01-01",
        }

        # Worked on Dec 24 (before) but not after
        timesheet_entries = [
            {"work_date": "2025-12-24", "regular_hours": 8, "overtime_hours": 0},
        ]

        result = holiday_calculator._is_eligible_for_holiday_pay(
            employee, holiday_date, config, timesheet_entries
        )

        assert result is False

    def test_on_fails_with_only_work_after(self, holiday_calculator):
        """ON: Employee who only worked after holiday is ineligible."""
        config = make_on_config()
        holiday_date = date(2025, 12, 25)

        employee = {
            "id": "emp-on-fail-after",
            "hire_date": "2024-01-01",
        }

        # Worked on Dec 26 (after) but not before
        timesheet_entries = [
            {"work_date": "2025-12-26", "regular_hours": 8, "overtime_hours": 0},
        ]

        result = holiday_calculator._is_eligible_for_holiday_pay(
            employee, holiday_date, config, timesheet_entries
        )

        assert result is False

    def test_on_eligible_when_no_timesheet_data(self, holiday_calculator):
        """ON: Without timesheet data, default to eligible (graceful fallback)."""
        config = make_on_config()
        holiday_date = date(2025, 12, 25)

        employee = {
            "id": "emp-on-no-ts",
            "hire_date": "2024-01-01",
        }

        # No timesheet entries provided
        result = holiday_calculator._is_eligible_for_holiday_pay(
            employee, holiday_date, config, None
        )

        assert result is True

    def test_bc_skips_rule_check(self, holiday_calculator):
        """BC: require_last_first_rule=False means rule is skipped."""
        config = make_bc_config()
        holiday_date = date(2025, 7, 1)

        # Employee with >30 days employment
        employee = {
            "id": "emp-bc-skip",
            "hire_date": "2025-05-01",
        }

        # Even without any work entries, should be eligible (BC doesn't require rule)
        timesheet_entries = []

        result = holiday_calculator._is_eligible_for_holiday_pay(
            employee, holiday_date, config, timesheet_entries
        )

        assert result is True


class TestMinDaysWorkedInPeriod:
    """Tests for min_days_worked_in_period eligibility check (PE)."""

    def test_pe_eligible_with_15_days(self, holiday_calculator):
        """PE: Employee with 15 days worked in 30-day period is eligible."""
        config = make_pe_config()
        holiday_date = date(2025, 7, 1)

        employee = {
            "id": "emp-pe-15",
            "hire_date": "2025-05-01",  # >30 days
        }

        # 15 days of work in past 30 days
        timesheet_entries = [
            {"work_date": (holiday_date - timedelta(days=i)).isoformat(), "regular_hours": 8, "overtime_hours": 0}
            for i in range(1, 16)  # 15 days before holiday
        ]
        # Also add work after holiday for last/first rule
        timesheet_entries.append({"work_date": "2025-07-02", "regular_hours": 8, "overtime_hours": 0})

        result = holiday_calculator._is_eligible_for_holiday_pay(
            employee, holiday_date, config, timesheet_entries
        )

        assert result is True

    def test_pe_ineligible_with_14_days(self, holiday_calculator):
        """PE: Employee with only 14 days worked in 30-day period is ineligible."""
        config = make_pe_config()
        holiday_date = date(2025, 7, 1)

        employee = {
            "id": "emp-pe-14",
            "hire_date": "2025-05-01",  # >30 days
        }

        # Only 14 days of work in past 30 days
        timesheet_entries = [
            {"work_date": (holiday_date - timedelta(days=i)).isoformat(), "regular_hours": 8, "overtime_hours": 0}
            for i in range(1, 15)  # 14 days before holiday
        ]
        # Also add work after holiday for last/first rule
        timesheet_entries.append({"work_date": "2025-07-02", "regular_hours": 8, "overtime_hours": 0})

        result = holiday_calculator._is_eligible_for_holiday_pay(
            employee, holiday_date, config, timesheet_entries
        )

        assert result is False

    def test_pe_eligible_when_no_timesheet_data(self, holiday_calculator):
        """PE: Without timesheet data, default to eligible (graceful fallback)."""
        config = make_pe_config()
        holiday_date = date(2025, 7, 1)

        employee = {
            "id": "emp-pe-no-ts",
            "hire_date": "2025-05-01",
        }

        result = holiday_calculator._is_eligible_for_holiday_pay(
            employee, holiday_date, config, None
        )

        assert result is True

    def test_on_skips_days_worked_check(self, holiday_calculator):
        """ON: min_days_worked_in_period not set, so rule is skipped."""
        config = make_on_config()
        holiday_date = date(2025, 12, 25)

        employee = {
            "id": "emp-on-skip",
            "hire_date": "2024-01-01",
        }

        # Only 5 days worked, but ON doesn't have min_days_worked_in_period
        timesheet_entries = [
            {"work_date": "2025-12-24", "regular_hours": 8, "overtime_hours": 0},
            {"work_date": "2025-12-23", "regular_hours": 8, "overtime_hours": 0},
            {"work_date": "2025-12-22", "regular_hours": 8, "overtime_hours": 0},
            {"work_date": "2025-12-21", "regular_hours": 8, "overtime_hours": 0},
            {"work_date": "2025-12-20", "regular_hours": 8, "overtime_hours": 0},
            {"work_date": "2025-12-26", "regular_hours": 8, "overtime_hours": 0},  # After holiday
        ]

        result = holiday_calculator._is_eligible_for_holiday_pay(
            employee, holiday_date, config, timesheet_entries
        )

        assert result is True


class TestIneligibilityReasons:
    """Tests for _get_ineligibility_reason with new checks."""

    def test_reason_for_last_first_rule_failure(self, holiday_calculator):
        """Returns correct reason for last/first rule failure."""
        config = make_on_config()
        holiday_date = date(2025, 12, 25)

        employee = {
            "id": "emp-on-reason",
            "hire_date": "2024-01-01",
        }

        # Only work before, not after
        timesheet_entries = [
            {"work_date": "2025-12-24", "regular_hours": 8, "overtime_hours": 0},
        ]

        reason = holiday_calculator._get_ineligibility_reason(
            employee, holiday_date, config, timesheet_entries
        )

        assert "before/after" in reason.lower()

    def test_reason_for_min_days_worked_failure(self, holiday_calculator):
        """Returns correct reason for min_days_worked_in_period failure."""
        config = make_pe_config()
        holiday_date = date(2025, 7, 1)

        employee = {
            "id": "emp-pe-reason",
            "hire_date": "2025-05-01",
        }

        # 10 days worked (less than 15 required)
        timesheet_entries = [
            {"work_date": (holiday_date - timedelta(days=i)).isoformat(), "regular_hours": 8, "overtime_hours": 0}
            for i in range(1, 11)
        ]
        # Add work after for last/first rule
        timesheet_entries.append({"work_date": "2025-07-02", "regular_hours": 8, "overtime_hours": 0})

        reason = holiday_calculator._get_ineligibility_reason(
            employee, holiday_date, config, timesheet_entries
        )

        assert "10 days worked" in reason
        assert "need 15" in reason

