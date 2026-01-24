"""
Tier 1 Major Provinces Holiday Pay Validation Tests

Tests holiday pay calculations for major provinces by calling ACTUAL IMPLEMENTATION:
- SK: Saskatchewan (5% of 28-day wages)
- ON: Ontario (4-week average / 20)
- BC: British Columbia (30-day average)
- AB: Alberta (4-week daily average)

Uses fixture data verified against official provincial calculators.

IMPORTANT: These tests call the actual calculator methods, NOT re-implementing formulas.
For pure math formula tests, see test_formula_pure.py.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.models.holiday_pay_config import (
    HolidayPayConfig,
    HolidayPayEligibility,
    HolidayPayFormulaParams,
)
from app.services.payroll_run.holiday_pay import HolidayPayCalculator

from .conftest import (
    VARIANCE_TOLERANCE,
    build_employee_data,
    build_historical_earnings,
    get_case_by_id,
    get_cases_by_province,
    validate_component,
)
from tests.payroll.conftest import make_sk_config, make_on_config, make_ab_config


# =============================================================================
# Test Fixtures for Integration Tests
# =============================================================================


def setup_sk_payroll_mock(mock_supabase, case_input: dict) -> None:
    """Set up mock for Saskatchewan 5% formula.

    The 5% formula uses payroll_records for historical earnings.
    """
    wages = Decimal(str(case_input.get("wages_past_28_days", "0")))
    vacation_pay = Decimal(str(case_input.get("vacation_pay_past_28_days", "0")))
    holiday_pay = Decimal(str(case_input.get("holiday_pay_past_28_days", "0")))

    # Mock payroll_records query for 28-day earnings
    payroll_data = [{
        "gross_regular": float(wages),
        "vacation_pay_paid": float(vacation_pay),
        "holiday_pay": float(holiday_pay),
        "payroll_runs": {"id": "run-prev", "pay_date": "2024-12-15", "status": "completed"},
    }] if wages > 0 else []

    mock_result = MagicMock()
    mock_result.data = payroll_data
    mock_supabase.table.return_value.select.return_value.eq.return_value.neq.return_value.gte.return_value.lt.return_value.in_.return_value.execute.return_value = mock_result

    # Also set up empty timesheet mock (SK uses payroll_records, not timesheet)
    empty_result = MagicMock()
    empty_result.data = []
    mock_supabase.table.return_value.select.return_value.eq.return_value.gte.return_value.lte.return_value.execute.return_value = empty_result


def setup_on_payroll_mock(mock_supabase, case_input: dict) -> None:
    """Set up mock for Ontario 4-week average formula.

    ON formula: (wages + vacation_pay) / 20
    """
    wages = Decimal(str(case_input.get("wages_past_4_weeks", "0")))
    vacation_pay = Decimal(str(case_input.get("vacation_pay_past_4_weeks", "0")))

    payroll_data = [{
        "gross_regular": float(wages),
        "gross_overtime": 0,
        "vacation_pay_paid": float(vacation_pay),
        "payroll_runs": {"id": "run-prev", "pay_date": "2024-12-20", "status": "completed"},
    }] if wages > 0 else []

    mock_result = MagicMock()
    mock_result.data = payroll_data
    mock_supabase.table.return_value.select.return_value.eq.return_value.neq.return_value.gte.return_value.lt.return_value.in_.return_value.execute.return_value = mock_result

    # Empty timesheet for fallback
    empty_result = MagicMock()
    empty_result.data = []
    mock_supabase.table.return_value.select.return_value.eq.return_value.gte.return_value.lte.return_value.execute.return_value = empty_result


def setup_ab_timesheet_mock(mock_supabase, case_input: dict, holiday_date: date) -> None:
    """Set up mock for Alberta 4-week daily formula.

    AB formula: wages / days_worked
    Uses timesheet data for days worked count.
    """
    wages = Decimal(str(case_input.get("wages_past_4_weeks", "0")))
    days_worked = int(case_input.get("days_worked_past_4_weeks", 0))
    hourly_rate = Decimal(str(case_input.get("hourly_rate", "0")))

    if days_worked > 0 and hourly_rate > 0:
        # Calculate hours per day from wages: wages / hourly_rate / days
        hours_per_day = wages / hourly_rate / days_worked
        timesheet_data = [
            {"work_date": (holiday_date - timedelta(days=i+1)).isoformat(),
             "regular_hours": float(hours_per_day), "overtime_hours": 0}
            for i in range(days_worked)
        ]
    else:
        timesheet_data = []

    mock_result = MagicMock()
    mock_result.data = timesheet_data
    mock_supabase.table.return_value.select.return_value.eq.return_value.gte.return_value.lte.return_value.execute.return_value = mock_result

    # Also mock payroll_records as empty (AB uses timesheet)
    empty_result = MagicMock()
    empty_result.data = []
    mock_supabase.table.return_value.select.return_value.eq.return_value.neq.return_value.gte.return_value.lt.return_value.in_.return_value.execute.return_value = empty_result


class MockConfigLoader:
    """Mock config loader that returns config for any province."""

    def __init__(self):
        self.configs = {
            "SK": make_sk_config(),
            "ON": make_on_config(),
            "AB": make_ab_config(),
        }

    def get_config(self, province_code: str) -> HolidayPayConfig:
        if province_code not in self.configs:
            return self._make_generic_config(province_code)
        return self.configs[province_code]

    def _make_generic_config(self, province_code: str) -> HolidayPayConfig:
        """Create a generic 30-day config for unmapped provinces."""
        return HolidayPayConfig(
            province_code=province_code,
            formula_type="30_day_average",
            formula_params=HolidayPayFormulaParams(
                lookback_days=30,
                method="total_wages_div_days",
                default_daily_hours=Decimal("8"),
                new_employee_fallback="pro_rated",
            ),
            eligibility=HolidayPayEligibility(
                min_employment_days=30,
                require_last_first_rule=False,
            ),
            premium_rate=Decimal("1.5"),
        )


# =============================================================================
# Saskatchewan Tests (5% of 28-day wages)
# =============================================================================


class TestSaskatchewanHolidayPay:
    """Integration tests for Saskatchewan 5% formula.

    IMPORTANT: These tests call the actual calculator._apply_5_percent_28_days()
    method, NOT re-implementing the formula in test code.
    """

    TIER = 1
    PROVINCE = "SK"

    @pytest.fixture
    def mock_supabase(self):
        """Create a fresh mock Supabase client for each test."""
        return MagicMock()

    @pytest.fixture
    def sk_calculator(self, mock_supabase):
        """Create calculator with SK config."""
        return HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test_user",
            company_id="test_company",
            config_loader=MockConfigLoader(),
        )

    def test_sk_full_time_standard(self, mock_supabase, sk_calculator):
        """Test SK full-time employee - calls actual implementation.

        Verified case: SK_FULL_TIME_BIWEEKLY
        Formula: $2,800 × 5% = $140.00
        """
        case = get_case_by_id(1, "SK_FULL_TIME_BIWEEKLY")
        if case is None:
            pytest.skip("Case SK_FULL_TIME_BIWEEKLY not found")

        setup_sk_payroll_mock(mock_supabase, case.input)

        # Call actual implementation method
        result = sk_calculator.formula_calculators.apply_5_percent_28_days(
            employee_id=f"test_{case.id.lower()}",
            holiday_date=date.fromisoformat(case.input["holiday_date"]),
            current_run_id="run-001",
            percentage=Decimal("0.05"),
            include_vacation_pay=True,
            include_previous_holiday_pay=True,
            current_period_gross=Decimal("0"),
            new_employee_fallback="pro_rated",
        )

        expected = Decimal(case.expected["regular_holiday_pay"])
        validation = validate_component("SK Holiday Pay", result, expected, VARIANCE_TOLERANCE)

        print(f"\n--- {case.id} Validation ---")
        print(f"  {validation.message}")
        assert validation.passed, f"Failed: {validation.message}"

    def test_sk_part_time_low_hours(self, mock_supabase, sk_calculator):
        """Test SK part-time with minimal hours - calls actual implementation.

        Verified case: SK_PART_TIME_LOW_HOURS
        Formula: $60 × 5% = $3.00
        """
        case = get_case_by_id(1, "SK_PART_TIME_LOW_HOURS")
        if case is None:
            pytest.skip("Case SK_PART_TIME_LOW_HOURS not found")

        setup_sk_payroll_mock(mock_supabase, case.input)

        result = sk_calculator.formula_calculators.apply_5_percent_28_days(
            employee_id=f"test_{case.id.lower()}",
            holiday_date=date.fromisoformat(case.input["holiday_date"]),
            current_run_id="run-001",
            percentage=Decimal("0.05"),
            include_vacation_pay=True,
            include_previous_holiday_pay=True,
            current_period_gross=Decimal("0"),
            new_employee_fallback="pro_rated",
        )

        expected = Decimal(case.expected["regular_holiday_pay"])
        validation = validate_component("SK Holiday Pay (Low Hours)", result, expected, VARIANCE_TOLERANCE)

        print(f"\n--- {case.id} Validation ---")
        print(f"  {validation.message}")
        assert validation.passed, f"Failed: {validation.message}"

    def test_sk_with_vacation_pay(self, mock_supabase, sk_calculator):
        """Test SK calculation including vacation pay - calls actual implementation.

        Verified case: SK_WITH_VACATION_PAY
        Formula: ($2,000 + $80) × 5% = $104.00
        """
        case = get_case_by_id(1, "SK_WITH_VACATION_PAY")
        if case is None:
            pytest.skip("Case SK_WITH_VACATION_PAY not found")

        setup_sk_payroll_mock(mock_supabase, case.input)

        result = sk_calculator.formula_calculators.apply_5_percent_28_days(
            employee_id=f"test_{case.id.lower()}",
            holiday_date=date.fromisoformat(case.input["holiday_date"]),
            current_run_id="run-001",
            percentage=Decimal("0.05"),
            include_vacation_pay=True,
            include_previous_holiday_pay=True,
            current_period_gross=Decimal("0"),
            new_employee_fallback="pro_rated",
        )

        expected = Decimal(case.expected["regular_holiday_pay"])
        validation = validate_component("SK Holiday Pay (With Vacation)", result, expected, VARIANCE_TOLERANCE)

        print(f"\n--- {case.id} Validation ---")
        print(f"  {validation.message}")
        assert validation.passed, f"Failed: {validation.message}"

    def test_sk_new_employee(self, mock_supabase, sk_calculator):
        """Test SK new employee - calls actual implementation.

        Verified case: SK_NEW_EMPLOYEE
        Formula: $720 × 5% = $36.00
        """
        case = get_case_by_id(1, "SK_NEW_EMPLOYEE")
        if case is None:
            pytest.skip("Case SK_NEW_EMPLOYEE not found")

        setup_sk_payroll_mock(mock_supabase, case.input)

        result = sk_calculator.formula_calculators.apply_5_percent_28_days(
            employee_id=f"test_{case.id.lower()}",
            holiday_date=date.fromisoformat(case.input["holiday_date"]),
            current_run_id="run-001",
            percentage=Decimal("0.05"),
            include_vacation_pay=True,
            include_previous_holiday_pay=True,
            current_period_gross=Decimal("0"),
            new_employee_fallback="pro_rated",
        )

        expected = Decimal(case.expected["regular_holiday_pay"])
        validation = validate_component("SK Holiday Pay (New Employee)", result, expected, VARIANCE_TOLERANCE)

        print(f"\n--- {case.id} Validation ---")
        print(f"  {validation.message}")
        assert validation.passed, f"Failed: {validation.message}"

    def test_sk_with_previous_holiday_pay(self, mock_supabase, sk_calculator):
        """Test SK calculation including previous holiday pay - calls actual implementation.

        Verified case: SK_WITH_PREVIOUS_HOLIDAY_PAY
        Formula: ($2,400 + $96 + $120) × 5% = $130.80
        """
        case = get_case_by_id(1, "SK_WITH_PREVIOUS_HOLIDAY_PAY")
        if case is None:
            pytest.skip("Case SK_WITH_PREVIOUS_HOLIDAY_PAY not found")

        setup_sk_payroll_mock(mock_supabase, case.input)

        result = sk_calculator.formula_calculators.apply_5_percent_28_days(
            employee_id=f"test_{case.id.lower()}",
            holiday_date=date.fromisoformat(case.input["holiday_date"]),
            current_run_id="run-001",
            percentage=Decimal("0.05"),
            include_vacation_pay=True,
            include_previous_holiday_pay=True,
            current_period_gross=Decimal("0"),
            new_employee_fallback="pro_rated",
        )

        expected = Decimal(case.expected["regular_holiday_pay"])
        validation = validate_component("SK Holiday Pay (With Previous Holiday)", result, expected, VARIANCE_TOLERANCE)

        print(f"\n--- {case.id} Validation ---")
        print(f"  {validation.message}")
        assert validation.passed, f"Failed: {validation.message}"


# =============================================================================
# Ontario Tests (4-week average / 20)
# =============================================================================


class TestOntarioHolidayPay:
    """Integration tests for Ontario 4-week average formula.

    IMPORTANT: These tests call the actual calculator._apply_4_week_average()
    method, NOT re-implementing the formula in test code.
    """

    TIER = 1
    PROVINCE = "ON"

    @pytest.fixture
    def mock_supabase(self):
        """Create a fresh mock Supabase client for each test."""
        return MagicMock()

    @pytest.fixture
    def on_calculator(self, mock_supabase):
        """Create calculator with ON config."""
        return HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test_user",
            company_id="test_company",
            config_loader=MockConfigLoader(),
        )

    def test_on_standard_4week(self, mock_supabase, on_calculator):
        """Test ON standard 4-week calculation - calls actual implementation.

        Verified case: ON_STANDARD_4WEEK
        Formula: ($2,000 + $80) / 20 = $104.00
        """
        case = get_case_by_id(1, "ON_STANDARD_4WEEK")
        if case is None:
            pytest.skip("Case ON_STANDARD_4WEEK not found")

        setup_on_payroll_mock(mock_supabase, case.input)

        employee = build_employee_data(case)

        result = on_calculator.formula_calculators.apply_4_week_average(
            employee_id=f"test_{case.id.lower()}",
            holiday_date=date.fromisoformat(case.input["holiday_date"]),
            current_run_id="run-001",
            divisor=20,
            include_vacation_pay=True,
            include_overtime=False,
            employee_fallback=employee,
            new_employee_fallback="pro_rated",
        )

        expected = Decimal(case.expected["regular_holiday_pay"])
        validation = validate_component("ON Holiday Pay", result, expected, VARIANCE_TOLERANCE)

        print(f"\n--- {case.id} Validation ---")
        print(f"  {validation.message}")
        assert validation.passed, f"Failed: {validation.message}"

    def test_on_with_high_vacation(self, mock_supabase, on_calculator):
        """Test ON with significant vacation pay - calls actual implementation.

        Verified case: ON_WITH_HIGH_VACATION
        Formula: ($4,800 + $288) / 20 = $254.40
        """
        case = get_case_by_id(1, "ON_WITH_HIGH_VACATION")
        if case is None:
            pytest.skip("Case ON_WITH_HIGH_VACATION not found")

        setup_on_payroll_mock(mock_supabase, case.input)

        employee = build_employee_data(case)

        result = on_calculator.formula_calculators.apply_4_week_average(
            employee_id=f"test_{case.id.lower()}",
            holiday_date=date.fromisoformat(case.input["holiday_date"]),
            current_run_id="run-001",
            divisor=20,
            include_vacation_pay=True,
            include_overtime=False,
            employee_fallback=employee,
            new_employee_fallback="pro_rated",
        )

        expected = Decimal(case.expected["regular_holiday_pay"])
        validation = validate_component("ON Holiday Pay (High Vacation)", result, expected, VARIANCE_TOLERANCE)

        print(f"\n--- {case.id} Validation ---")
        print(f"  {validation.message}")
        assert validation.passed, f"Failed: {validation.message}"

    def test_on_new_employee_fallback(self, mock_supabase, on_calculator):
        """Test ON new employee fallback - calls actual implementation.

        Verified case: ON_NEW_EMPLOYEE
        Fallback: 8h × $20.00 = $160.00 (pro_rated)
        """
        case = get_case_by_id(1, "ON_NEW_EMPLOYEE")
        if case is None:
            pytest.skip("Case ON_NEW_EMPLOYEE not found")

        # Set up empty payroll data to trigger fallback
        mock_result = MagicMock()
        mock_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.neq.return_value.gte.return_value.lt.return_value.in_.return_value.execute.return_value = mock_result

        employee = build_employee_data(case)
        employee["hourly_rate"] = float(case.input["hourly_rate"])

        result = on_calculator.formula_calculators.apply_4_week_average(
            employee_id=f"test_{case.id.lower()}",
            holiday_date=date.fromisoformat(case.input["holiday_date"]),
            current_run_id="run-001",
            divisor=20,
            include_vacation_pay=True,
            include_overtime=False,
            employee_fallback=employee,
            new_employee_fallback="pro_rated",
        )

        expected = Decimal(case.expected["regular_holiday_pay"])
        validation = validate_component("ON Holiday Pay (New Employee)", result, expected, VARIANCE_TOLERANCE)

        print(f"\n--- {case.id} Validation ---")
        print(f"  {validation.message}")
        assert validation.passed, f"Failed: {validation.message}"


# =============================================================================
# Alberta Tests (4-week daily average)
# =============================================================================


class TestAlbertaHolidayPay:
    """Integration tests for Alberta 4-week daily formula.

    IMPORTANT: These tests call the actual calculator._apply_4_week_daily()
    method, NOT re-implementing the formula in test code.
    """

    TIER = 1
    PROVINCE = "AB"

    @pytest.fixture
    def mock_supabase(self):
        """Create a fresh mock Supabase client for each test."""
        return MagicMock()

    @pytest.fixture
    def ab_calculator(self, mock_supabase):
        """Create calculator with AB config."""
        return HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test_user",
            company_id="test_company",
            config_loader=MockConfigLoader(),
        )

    def test_ab_4week_daily(self, mock_supabase, ab_calculator):
        """Test AB 4-week daily average - calls actual implementation.

        Verified case: AB_4WEEK_DAILY
        Formula: $4,480 / 20 days = $224.00
        """
        case = get_case_by_id(1, "AB_4WEEK_DAILY")
        if case is None:
            pytest.skip("Case AB_4WEEK_DAILY not found")

        holiday_date = date.fromisoformat(case.input["holiday_date"])
        setup_ab_timesheet_mock(mock_supabase, case.input, holiday_date)

        employee = build_employee_data(case)
        employee["hourly_rate"] = float(case.input["hourly_rate"])

        result = ab_calculator.formula_calculators.apply_4_week_daily(
            employee_id=f"test_{case.id.lower()}",
            holiday_date=holiday_date,
            current_run_id="run-001",
            include_overtime=False,
            employee_fallback=employee,
            new_employee_fallback="ineligible",
        )

        expected = Decimal(case.expected["regular_holiday_pay"])
        validation = validate_component("AB Holiday Pay", result, expected, VARIANCE_TOLERANCE)

        print(f"\n--- {case.id} Validation ---")
        print(f"  {validation.message}")
        assert validation.passed, f"Failed: {validation.message}"

    def test_ab_part_time(self, mock_supabase, ab_calculator):
        """Test AB part-time (3 days/week) - calls actual implementation.

        Verified case: AB_PART_TIME
        Formula: $2,112 / 12 days = $176.00
        """
        case = get_case_by_id(1, "AB_PART_TIME")
        if case is None:
            pytest.skip("Case AB_PART_TIME not found")

        holiday_date = date.fromisoformat(case.input["holiday_date"])
        setup_ab_timesheet_mock(mock_supabase, case.input, holiday_date)

        employee = build_employee_data(case)
        employee["hourly_rate"] = float(case.input["hourly_rate"])

        result = ab_calculator.formula_calculators.apply_4_week_daily(
            employee_id=f"test_{case.id.lower()}",
            holiday_date=holiday_date,
            current_run_id="run-001",
            include_overtime=False,
            employee_fallback=employee,
            new_employee_fallback="ineligible",
        )

        expected = Decimal(case.expected["regular_holiday_pay"])
        validation = validate_component("AB Holiday Pay (Part Time)", result, expected, VARIANCE_TOLERANCE)

        print(f"\n--- {case.id} Validation ---")
        print(f"  {validation.message}")
        assert validation.passed, f"Failed: {validation.message}"

    def test_ab_new_employee_ineligible(self, mock_supabase, ab_calculator):
        """Test AB new employee returns $0 (ineligible) - calls actual implementation.

        Verified case: AB_NEW_EMPLOYEE_INELIGIBLE
        Result: $0.00 (< 30 days employed)
        """
        case = get_case_by_id(1, "AB_NEW_EMPLOYEE_INELIGIBLE")
        if case is None:
            pytest.skip("Case AB_NEW_EMPLOYEE_INELIGIBLE not found")

        holiday_date = date.fromisoformat(case.input["holiday_date"])

        # Set up empty timesheet (new employee)
        mock_result = MagicMock()
        mock_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.gte.return_value.lte.return_value.execute.return_value = mock_result

        employee = build_employee_data(case)
        employee["hourly_rate"] = float(case.input["hourly_rate"])

        result = ab_calculator.formula_calculators.apply_4_week_daily(
            employee_id=f"test_{case.id.lower()}",
            holiday_date=holiday_date,
            current_run_id="run-001",
            include_overtime=False,
            employee_fallback=employee,
            new_employee_fallback="ineligible",  # Returns $0 for new employees
        )

        expected = Decimal(case.expected["regular_holiday_pay"])
        validation = validate_component("AB Holiday Pay (Ineligible)", result, expected, VARIANCE_TOLERANCE)

        print(f"\n--- {case.id} Validation ---")
        print(f"  {validation.message}")
        assert validation.passed, f"Failed: {validation.message}"


# =============================================================================
# Configuration Validation Tests
# =============================================================================


class TestProvinceConfigValidation:
    """Test that province configurations are correctly loaded.

    These are valid configuration tests that verify the config loader
    returns correct parameters for each province.
    """

    def test_sk_config_has_correct_formula_type(self):
        """Verify SK uses 5_percent_28_days formula."""
        from app.services.payroll.holiday_pay_config_loader import get_config

        config = get_config("SK")
        assert config.formula_type == "5_percent_28_days", (
            f"SK should use 5_percent_28_days, got {config.formula_type}"
        )

    def test_sk_config_has_correct_percentage(self):
        """Verify SK uses 5% (0.05) percentage."""
        from app.services.payroll.holiday_pay_config_loader import get_config

        config = get_config("SK")
        assert config.formula_params.percentage == Decimal("0.05"), (
            f"SK should use 0.05 percentage, got {config.formula_params.percentage}"
        )

    def test_sk_config_includes_vacation_pay(self):
        """Verify SK includes vacation pay in base."""
        from app.services.payroll.holiday_pay_config_loader import get_config

        config = get_config("SK")
        assert config.formula_params.include_vacation_pay is True, (
            "SK should include vacation pay"
        )

    def test_sk_config_includes_previous_holiday_pay(self):
        """Verify SK includes previous holiday pay in base."""
        from app.services.payroll.holiday_pay_config_loader import get_config

        config = get_config("SK")
        assert config.formula_params.include_previous_holiday_pay is True, (
            "SK should include previous holiday pay"
        )

    def test_sk_config_no_minimum_employment(self):
        """Verify SK has no minimum employment period."""
        from app.services.payroll.holiday_pay_config_loader import get_config

        config = get_config("SK")
        assert config.eligibility.min_employment_days == 0, (
            f"SK should have 0 minimum employment days, got {config.eligibility.min_employment_days}"
        )

    def test_on_config_has_4_week_average(self):
        """Verify ON uses 4_week_average formula."""
        from app.services.payroll.holiday_pay_config_loader import get_config

        config = get_config("ON")
        assert config.formula_type == "4_week_average", (
            f"ON should use 4_week_average, got {config.formula_type}"
        )

    def test_on_config_has_divisor_20(self):
        """Verify ON uses divisor of 20."""
        from app.services.payroll.holiday_pay_config_loader import get_config

        config = get_config("ON")
        assert config.formula_params.divisor == 20, (
            f"ON should use divisor 20, got {config.formula_params.divisor}"
        )

    def test_ab_config_has_4_week_daily(self):
        """Verify AB uses 4_week_average_daily formula."""
        from app.services.payroll.holiday_pay_config_loader import get_config

        config = get_config("AB")
        assert config.formula_type == "4_week_average_daily", (
            f"AB should use 4_week_average_daily, got {config.formula_type}"
        )

    def test_ab_config_has_30_day_minimum(self):
        """Verify AB requires 30 days of employment."""
        from app.services.payroll.holiday_pay_config_loader import get_config

        config = get_config("AB")
        assert config.eligibility.min_employment_days == 30, (
            f"AB should require 30 days, got {config.eligibility.min_employment_days}"
        )
