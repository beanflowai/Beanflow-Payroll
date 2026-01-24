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
    make_bc_15_30_config,
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
        """Ontario: No minimum employment days requirement (but still needs last/first rule)."""
        config = make_on_config()
        holiday_date = date.today()

        # Provide timesheet entries that satisfy the last/first rule
        # (work before and after holiday) - this is what Ontario requires
        timesheet_entries = [
            {"work_date": (holiday_date - timedelta(days=1)).isoformat(), "regular_hours": 8, "overtime_hours": 0},
            {"work_date": (holiday_date + timedelta(days=1)).isoformat(), "regular_hours": 8, "overtime_hours": 0},
        ]

        # Even a new hire should be eligible in Ontario (no 30-day rule)
        # as long as they satisfy the last/first rule
        result = holiday_calculator._is_eligible_for_holiday_pay(
            new_hire_employee, holiday_date, config, timesheet_entries
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
        from tests.payroll.conftest import setup_empty_timesheet_mock
        setup_empty_timesheet_mock(mock_supabase)

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
        from tests.payroll.conftest import setup_nb_timesheet_mock

        holiday_date = date.today()
        setup_nb_timesheet_mock(mock_supabase, holiday_date)

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
        # Uses 30_day_average: 10 days × 8h × $22 = $1760 / 10 = $176
        assert result.regular_holiday_pay == Decimal("176")
        assert result.calculation_details["holidays"][0]["eligible"] is True

    def test_nb_exactly_90_days_eligible(self, mock_supabase):
        """NB: Employee with exactly 90 days employment is eligible."""
        from tests.payroll.conftest import setup_nb_timesheet_mock

        holiday_date = date(2025, 4, 1)
        setup_nb_timesheet_mock(mock_supabase, holiday_date)

        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
        )

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

    def test_on_ineligible_when_no_timesheet_data(self, holiday_calculator):
        """ON: Without timesheet data, fail-closed (ineligible) for compliance.

        When require_last_first_rule=True but no timesheet data exists to verify,
        the employee is marked ineligible. This is stricter than the old behavior
        but more compliant with provincial requirements that mandate verification
        of work on last/first scheduled days.
        """
        config = make_on_config()
        holiday_date = date(2025, 12, 25)

        employee = {
            "id": "emp-on-no-ts",
            "hire_date": "2024-01-01",
        }

        # No timesheet entries provided - strict mode means ineligible
        result = holiday_calculator._is_eligible_for_holiday_pay(
            employee, holiday_date, config, None
        )

        assert result is False

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

    def test_pe_ineligible_when_no_timesheet_data(self, holiday_calculator):
        """PE: Without timesheet data, fail-closed (ineligible) for compliance.

        PEI requires both the last/first rule and min_days_worked_in_period.
        Without timesheet data to verify these requirements, the employee
        is marked ineligible (strict mode for compliance).
        """
        config = make_pe_config()
        holiday_date = date(2025, 7, 1)

        employee = {
            "id": "emp-pe-no-ts",
            "hire_date": "2025-05-01",
        }

        result = holiday_calculator._is_eligible_for_holiday_pay(
            employee, holiday_date, config, None
        )

        assert result is False

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

        # Check for key terms in the reason message
        assert "last scheduled day" in reason.lower() or "first scheduled day" in reason.lower()

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


class TestBCSalariedEligibility:
    """Tests for BC salaried employee 15/30 eligibility check.

    BC requires employees to have worked or earned wages on 15 of the 30 days
    before a holiday. For salaried employees without timesheet entries, this
    is calculated as:
    - Business days (Mon-Fri) in the 30-day period
    - Minus: sick leave days
    - Minus: vacation days
    - Minus: statutory holidays on business days
    """

    def test_bc_salaried_eligible_with_calculated_work_days(self, mock_supabase):
        """BC salaried employee with 15+ calculated work days is eligible.

        A 30-day period contains ~22 business days. Without any leave,
        the salaried employee should have 22 calculated work days > 15.
        """
        from app.services.payroll_run.holiday_pay_calculator import HolidayPayCalculator

        # Mock empty sick leave, vacation, and stat holiday queries
        def mock_table(table_name):
            mock = MagicMock()
            empty_result = MagicMock()
            empty_result.data = []

            if table_name == "sick_leave_usage_history":
                # No sick leave days
                mock.select.return_value.eq.return_value.eq.return_value.gte.return_value.lte.return_value.execute.return_value = empty_result
            elif table_name == "payroll_records":
                # No vacation hours taken
                mock.select.return_value.eq.return_value.gte.return_value.lt.return_value.execute.return_value = empty_result
            elif table_name == "statutory_holidays":
                # No stat holidays in period
                mock.select.return_value.eq.return_value.eq.return_value.gte.return_value.lt.return_value.execute.return_value = empty_result
            elif table_name == "timesheet_entries":
                # Empty timesheet (salaried employees don't have timesheet entries)
                mock.select.return_value.eq.return_value.gte.return_value.lte.return_value.execute.return_value = empty_result
            else:
                # Default empty for any other table
                mock.select.return_value.eq.return_value.neq.return_value.gte.return_value.lt.return_value.in_.return_value.execute.return_value = empty_result

            return mock

        mock_supabase.table.side_effect = mock_table

        bc_loader = MockConfigLoader({"BC": make_bc_15_30_config()})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=bc_loader,
        )

        holiday_date = date(2025, 7, 1)  # Tuesday

        # Salaried employee with >30 days employment (hired 60 days before holiday)
        salaried_employee = {
            "id": "emp-bc-salaried",
            "first_name": "Salaried",
            "last_name": "BC",
            "hourly_rate": None,
            "annual_salary": 60000.00,
            "compensation_type": "salary",  # Key: marks as salaried
            "hire_date": (holiday_date - timedelta(days=60)).isoformat(),
        }
        config = make_bc_15_30_config()

        # Test eligibility directly
        result = calculator._is_eligible_for_holiday_pay(
            salaried_employee, holiday_date, config, timesheet_entries=None
        )

        # 30-day period has ~22 business days, no leave = 22 work days > 15
        assert result is True

    def test_bc_salaried_eligible_with_vacation(self, mock_supabase):
        """BC salaried employee with vacation is still ELIGIBLE.

        CORRECTED TEST per BC ESA:
        Vacation days are "days entitled to wages" and should NOT be subtracted
        from the 15/30 eligibility count. The employee receives vacation pay
        during vacation, so these days count toward the 15-day requirement.

        Previous (incorrect) expectation:
            22 business days - 10 vacation days = 12 days < 15 → ineligible

        Corrected expectation:
            22 business days (vacation days are "entitled to wages") >= 15 → ELIGIBLE
        """
        from app.services.payroll_run.holiday_pay_calculator import HolidayPayCalculator

        holiday_date = date(2025, 7, 1)

        # Mock queries - vacation hours no longer affect eligibility
        def mock_table(table_name):
            mock = MagicMock()
            empty_result = MagicMock()
            empty_result.data = []

            if table_name == "sick_leave_usage_history":
                # No sick leave days (paid or unpaid)
                mock.select.return_value.eq.return_value.eq.return_value.gte.return_value.lt.return_value.execute.return_value = empty_result
            elif table_name == "payroll_records":
                # 80 hours vacation taken (10 days worth) - but this no longer affects eligibility
                vacation_result = MagicMock()
                vacation_result.data = [{"vacation_hours_taken": 80, "payroll_runs": {"pay_date": "2025-06-15"}}]
                mock.select.return_value.eq.return_value.gte.return_value.lt.return_value.execute.return_value = vacation_result
            elif table_name == "statutory_holidays":
                # No stat holidays in period
                mock.select.return_value.eq.return_value.eq.return_value.gte.return_value.lt.return_value.execute.return_value = empty_result
            elif table_name == "timesheet_entries":
                # Empty timesheet (salaried employees)
                mock.select.return_value.eq.return_value.gte.return_value.lte.return_value.execute.return_value = empty_result
            else:
                mock.select.return_value.eq.return_value.neq.return_value.gte.return_value.lt.return_value.in_.return_value.execute.return_value = empty_result

            return mock

        mock_supabase.table.side_effect = mock_table

        bc_loader = MockConfigLoader({"BC": make_bc_15_30_config()})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=bc_loader,
        )

        # Salaried employee hired 60 days before holiday
        salaried_employee = {
            "id": "emp-bc-salaried-vacation",
            "first_name": "Vacation",
            "last_name": "Taker",
            "hourly_rate": None,
            "annual_salary": 60000.00,
            "compensation_type": "salary",
            "hire_date": (holiday_date - timedelta(days=60)).isoformat(),
        }

        config = make_bc_15_30_config()

        result = calculator._is_eligible_for_holiday_pay(
            salaried_employee, holiday_date, config, timesheet_entries=None
        )

        # CORRECTED: Vacation days are "entitled to wages" per BC ESA
        # 22 business days >= 15 → ELIGIBLE (vacation doesn't reduce count)
        assert result is True

    def test_bc_salaried_ineligible_with_unpaid_sick_leave(self, mock_supabase):
        """BC salaried employee with excessive UNPAID sick leave is ineligible.

        Per BC ESA, only UNPAID sick leave days should reduce the eligibility count.
        If employee has many unpaid sick days, they may fall below 15 days.

        22 business days - 10 unpaid sick days = 12 days < 15 → ineligible
        """
        from app.services.payroll_run.holiday_pay_calculator import HolidayPayCalculator

        holiday_date = date(2025, 7, 1)

        # Mock queries to return 10 unpaid sick leave days
        def mock_table(table_name):
            mock = MagicMock()
            empty_result = MagicMock()
            empty_result.data = []

            if table_name == "sick_leave_usage_history":
                # Check if querying for is_paid=False (unpaid) or is_paid=True (paid)
                # We need to return different results based on is_paid filter
                def mock_eq_chain(*args, **kwargs):
                    result_mock = MagicMock()
                    # If this is the is_paid=False query, return 10 unpaid days
                    if args == ("is_paid", False):
                        unpaid_result = MagicMock()
                        unpaid_result.data = [
                            {"usage_date": (holiday_date - timedelta(days=i)).isoformat()}
                            for i in range(1, 11)  # 10 unpaid sick days
                        ]
                        result_mock.gte.return_value.lt.return_value.execute.return_value = unpaid_result
                    else:
                        # For is_paid=True query, return empty (no paid sick leave)
                        result_mock.gte.return_value.lt.return_value.execute.return_value = empty_result
                        result_mock.gte.return_value.lte.return_value.execute.return_value = empty_result
                    return result_mock

                mock.select.return_value.eq.return_value.eq.side_effect = mock_eq_chain
            elif table_name == "payroll_records":
                mock.select.return_value.eq.return_value.gte.return_value.lt.return_value.execute.return_value = empty_result
            elif table_name == "statutory_holidays":
                mock.select.return_value.eq.return_value.eq.return_value.gte.return_value.lt.return_value.execute.return_value = empty_result
            elif table_name == "timesheet_entries":
                mock.select.return_value.eq.return_value.gte.return_value.lte.return_value.execute.return_value = empty_result
            else:
                mock.select.return_value.eq.return_value.neq.return_value.gte.return_value.lt.return_value.in_.return_value.execute.return_value = empty_result

            return mock

        mock_supabase.table.side_effect = mock_table

        bc_loader = MockConfigLoader({"BC": make_bc_15_30_config()})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=bc_loader,
        )

        salaried_employee = {
            "id": "emp-bc-salaried-unpaid-sick",
            "first_name": "Unpaid",
            "last_name": "Sick",
            "hourly_rate": None,
            "annual_salary": 60000.00,
            "compensation_type": "salary",
            "hire_date": (holiday_date - timedelta(days=60)).isoformat(),
        }

        config = make_bc_15_30_config()

        result = calculator._is_eligible_for_holiday_pay(
            salaried_employee, holiday_date, config, timesheet_entries=None
        )

        # 22 business days - 10 unpaid sick days = 12 days < 15 → ineligible
        assert result is False

    def test_bc_salaried_ineligibility_reason_with_unpaid_sick(self, mock_supabase):
        """BC salaried employee gets correct ineligibility reason for unpaid sick leave."""
        from app.services.payroll_run.holiday_pay_calculator import HolidayPayCalculator

        holiday_date = date(2025, 7, 1)

        # Mock to return excessive unpaid sick leave
        def mock_table(table_name):
            mock = MagicMock()
            empty_result = MagicMock()
            empty_result.data = []

            if table_name == "sick_leave_usage_history":
                def mock_eq_chain(*args, **kwargs):
                    result_mock = MagicMock()
                    if args == ("is_paid", False):
                        unpaid_result = MagicMock()
                        unpaid_result.data = [
                            {"usage_date": (holiday_date - timedelta(days=i)).isoformat()}
                            for i in range(1, 11)  # 10 unpaid sick days
                        ]
                        result_mock.gte.return_value.lt.return_value.execute.return_value = unpaid_result
                    else:
                        result_mock.gte.return_value.lt.return_value.execute.return_value = empty_result
                        result_mock.gte.return_value.lte.return_value.execute.return_value = empty_result
                    return result_mock

                mock.select.return_value.eq.return_value.eq.side_effect = mock_eq_chain
            elif table_name == "payroll_records":
                mock.select.return_value.eq.return_value.gte.return_value.lt.return_value.execute.return_value = empty_result
            elif table_name == "statutory_holidays":
                mock.select.return_value.eq.return_value.eq.return_value.gte.return_value.lt.return_value.execute.return_value = empty_result
            elif table_name == "timesheet_entries":
                mock.select.return_value.eq.return_value.gte.return_value.lte.return_value.execute.return_value = empty_result
            else:
                mock.select.return_value.eq.return_value.neq.return_value.gte.return_value.lt.return_value.in_.return_value.execute.return_value = empty_result

            return mock

        mock_supabase.table.side_effect = mock_table

        bc_loader = MockConfigLoader({"BC": make_bc_15_30_config()})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=bc_loader,
        )

        salaried_employee = {
            "id": "emp-bc-salaried-reason",
            "first_name": "Reason",
            "last_name": "Check",
            "hourly_rate": None,
            "annual_salary": 60000.00,
            "compensation_type": "salary",
            "hire_date": (holiday_date - timedelta(days=60)).isoformat(),
        }

        config = make_bc_15_30_config()

        reason = calculator._get_ineligibility_reason(
            salaried_employee, holiday_date, config, timesheet_entries=None
        )

        # Should mention days worked and the requirement
        assert "days worked" in reason
        assert "need 15" in reason

    def test_bc_hourly_still_uses_timesheet(self, mock_supabase):
        """BC hourly employee still uses timesheet entries for 15/30 check."""
        from app.services.payroll_run.holiday_pay_calculator import HolidayPayCalculator

        # Mock empty DB queries
        def mock_table(table_name):
            mock = MagicMock()
            empty_result = MagicMock()
            empty_result.data = []
            mock.select.return_value.eq.return_value.gte.return_value.lte.return_value.execute.return_value = empty_result
            mock.select.return_value.eq.return_value.neq.return_value.gte.return_value.lt.return_value.in_.return_value.execute.return_value = empty_result
            return mock

        mock_supabase.table.side_effect = mock_table

        bc_loader = MockConfigLoader({"BC": make_bc_15_30_config()})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=bc_loader,
        )

        holiday_date = date(2025, 7, 1)

        # Hourly employee hired 60 days before holiday
        hourly_employee = {
            "id": "emp-bc-hourly",
            "first_name": "Hourly",
            "last_name": "Worker",
            "hourly_rate": 25.00,
            "annual_salary": None,
            "compensation_type": "hourly",  # Hourly employee
            "hire_date": (holiday_date - timedelta(days=60)).isoformat(),
        }

        config = make_bc_15_30_config()

        # Provide 15 days of timesheet entries
        timesheet_entries = [
            {"work_date": (holiday_date - timedelta(days=i)).isoformat(), "regular_hours": 8, "overtime_hours": 0}
            for i in range(1, 16)  # 15 days
        ]

        result = calculator._is_eligible_for_holiday_pay(
            hourly_employee, holiday_date, config, timesheet_entries=timesheet_entries
        )

        # Hourly employee with 15 days from timesheet = eligible
        assert result is True

    def test_bc_hourly_ineligible_without_enough_timesheet_days(self, mock_supabase):
        """BC hourly employee without 15 timesheet days is ineligible."""
        from app.services.payroll_run.holiday_pay_calculator import HolidayPayCalculator

        # Mock empty DB queries
        def mock_table(table_name):
            mock = MagicMock()
            empty_result = MagicMock()
            empty_result.data = []
            mock.select.return_value.eq.return_value.gte.return_value.lte.return_value.execute.return_value = empty_result
            mock.select.return_value.eq.return_value.neq.return_value.gte.return_value.lt.return_value.in_.return_value.execute.return_value = empty_result
            return mock

        mock_supabase.table.side_effect = mock_table

        bc_loader = MockConfigLoader({"BC": make_bc_15_30_config()})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=bc_loader,
        )

        holiday_date = date(2025, 7, 1)

        # Hourly employee hired 60 days before holiday
        hourly_employee = {
            "id": "emp-bc-hourly-few",
            "first_name": "Few",
            "last_name": "Days",
            "hourly_rate": 25.00,
            "annual_salary": None,
            "compensation_type": "hourly",
            "hire_date": (holiday_date - timedelta(days=60)).isoformat(),
        }

        config = make_bc_15_30_config()

        # Only 10 days of timesheet entries (less than 15 required)
        timesheet_entries = [
            {"work_date": (holiday_date - timedelta(days=i)).isoformat(), "regular_hours": 8, "overtime_hours": 0}
            for i in range(1, 11)  # Only 10 days
        ]

        result = calculator._is_eligible_for_holiday_pay(
            hourly_employee, holiday_date, config, timesheet_entries=timesheet_entries
        )

        # Hourly employee with only 10 days < 15 = ineligible
        assert result is False

    def test_bc_salaried_eligible_with_paid_sick_leave(self, mock_supabase):
        """BC salaried employee with PAID sick leave is still ELIGIBLE.

        Per BC ESA, paid sick leave days are "days entitled to wages" and should
        NOT reduce the 15/30 eligibility count. Only UNPAID sick leave reduces it.
        """
        from app.services.payroll_run.holiday_pay_calculator import HolidayPayCalculator

        holiday_date = date(2025, 7, 1)

        # Mock queries - paid sick leave should not affect eligibility
        def mock_table(table_name):
            mock = MagicMock()
            empty_result = MagicMock()
            empty_result.data = []

            if table_name == "sick_leave_usage_history":
                def mock_eq_chain(*args, **kwargs):
                    result_mock = MagicMock()
                    if args == ("is_paid", False):
                        # No unpaid sick leave
                        result_mock.gte.return_value.lt.return_value.execute.return_value = empty_result
                    else:
                        # 5 PAID sick leave days - should NOT reduce count
                        paid_result = MagicMock()
                        paid_result.data = [
                            {"usage_date": (holiday_date - timedelta(days=i)).isoformat()}
                            for i in range(1, 6)  # 5 paid sick days
                        ]
                        result_mock.gte.return_value.lt.return_value.execute.return_value = paid_result
                        result_mock.gte.return_value.lte.return_value.execute.return_value = paid_result
                    return result_mock

                mock.select.return_value.eq.return_value.eq.side_effect = mock_eq_chain
            elif table_name == "payroll_records":
                mock.select.return_value.eq.return_value.gte.return_value.lt.return_value.execute.return_value = empty_result
            elif table_name == "statutory_holidays":
                mock.select.return_value.eq.return_value.eq.return_value.gte.return_value.lt.return_value.execute.return_value = empty_result
            elif table_name == "timesheet_entries":
                mock.select.return_value.eq.return_value.gte.return_value.lte.return_value.execute.return_value = empty_result
            else:
                mock.select.return_value.eq.return_value.neq.return_value.gte.return_value.lt.return_value.in_.return_value.execute.return_value = empty_result

            return mock

        mock_supabase.table.side_effect = mock_table

        bc_loader = MockConfigLoader({"BC": make_bc_15_30_config()})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=bc_loader,
        )

        salaried_employee = {
            "id": "emp-bc-salaried-paid-sick",
            "first_name": "Paid",
            "last_name": "Sick",
            "hourly_rate": None,
            "annual_salary": 60000.00,
            "compensation_type": "salary",
            "hire_date": (holiday_date - timedelta(days=60)).isoformat(),
        }

        config = make_bc_15_30_config()

        result = calculator._is_eligible_for_holiday_pay(
            salaried_employee, holiday_date, config, timesheet_entries=None
        )

        # Paid sick leave days are "entitled to wages" - should still be eligible
        # 22 business days (paid sick doesn't reduce) >= 15 → ELIGIBLE
        assert result is True

    def test_bc_salaried_eligible_with_combined_paid_leave(self, mock_supabase):
        """BC salaried employee with vacation + paid sick + stat holidays is ELIGIBLE.

        Comprehensive test: All forms of paid leave count as "days entitled to wages"
        per BC ESA. Only unpaid leave should reduce the count.

        Scenario:
        - 22 business days in 30-day period
        - 5 vacation days (paid) → should NOT reduce count
        - 3 paid sick days → should NOT reduce count
        - 1 stat holiday → should NOT reduce count
        - 0 unpaid sick days → nothing to subtract

        Result: 22 days >= 15 → ELIGIBLE
        """
        from app.services.payroll_run.holiday_pay_calculator import HolidayPayCalculator

        holiday_date = date(2025, 7, 1)

        # Mock queries with various paid leave types
        def mock_table(table_name):
            mock = MagicMock()
            empty_result = MagicMock()
            empty_result.data = []

            if table_name == "sick_leave_usage_history":
                def mock_eq_chain(*args, **kwargs):
                    result_mock = MagicMock()
                    if args == ("is_paid", False):
                        # No unpaid sick leave
                        result_mock.gte.return_value.lt.return_value.execute.return_value = empty_result
                    else:
                        # 3 paid sick days
                        paid_result = MagicMock()
                        paid_result.data = [
                            {"usage_date": (holiday_date - timedelta(days=i)).isoformat()}
                            for i in range(1, 4)
                        ]
                        result_mock.gte.return_value.lt.return_value.execute.return_value = paid_result
                        result_mock.gte.return_value.lte.return_value.execute.return_value = paid_result
                    return result_mock

                mock.select.return_value.eq.return_value.eq.side_effect = mock_eq_chain
            elif table_name == "payroll_records":
                # 40 hours vacation (5 days)
                vacation_result = MagicMock()
                vacation_result.data = [{"vacation_hours_taken": 40, "payroll_runs": {"pay_date": "2025-06-15"}}]
                mock.select.return_value.eq.return_value.gte.return_value.lt.return_value.execute.return_value = vacation_result
            elif table_name == "statutory_holidays":
                # 1 stat holiday
                stat_result = MagicMock()
                stat_result.data = [{"holiday_date": "2025-06-16"}]  # A Monday
                mock.select.return_value.eq.return_value.eq.return_value.gte.return_value.lt.return_value.execute.return_value = stat_result
            elif table_name == "timesheet_entries":
                mock.select.return_value.eq.return_value.gte.return_value.lte.return_value.execute.return_value = empty_result
            else:
                mock.select.return_value.eq.return_value.neq.return_value.gte.return_value.lt.return_value.in_.return_value.execute.return_value = empty_result

            return mock

        mock_supabase.table.side_effect = mock_table

        bc_loader = MockConfigLoader({"BC": make_bc_15_30_config()})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=bc_loader,
        )

        salaried_employee = {
            "id": "emp-bc-combined-paid",
            "first_name": "Combined",
            "last_name": "Paid",
            "hourly_rate": None,
            "annual_salary": 60000.00,
            "compensation_type": "salary",
            "hire_date": (holiday_date - timedelta(days=60)).isoformat(),
        }

        config = make_bc_15_30_config()

        result = calculator._is_eligible_for_holiday_pay(
            salaried_employee, holiday_date, config, timesheet_entries=None
        )

        # All paid leave = "entitled to wages" → 22 business days >= 15 → ELIGIBLE
        assert result is True

