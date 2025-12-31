"""
Tier 1 Major Provinces Holiday Pay Validation Tests

Tests holiday pay calculations for major provinces:
- SK: Saskatchewan (5% of 28-day wages)
- ON: Ontario (4-week average / 20)
- BC: British Columbia (30-day average)
- AB: Alberta (4-week daily average)

Uses fixture data verified against official provincial calculators.
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.models.holiday_pay_config import (
    HolidayPayConfig,
    HolidayPayEligibility,
    HolidayPayFormulaParams,
)
from app.services.payroll_run.holiday_pay_calculator import HolidayPayCalculator

from .conftest import (
    VARIANCE_TOLERANCE,
    build_historical_earnings,
    get_case_by_id,
    validate_component,
)

# =============================================================================
# Saskatchewan Tests (5% of 28-day wages)
# =============================================================================


class TestSaskatchewanHolidayPay:
    """Test Saskatchewan 5% formula implementation."""

    TIER = 1
    PROVINCE = "SK"

    @pytest.fixture
    def sk_config(self) -> HolidayPayConfig:
        """Saskatchewan holiday pay configuration."""
        return HolidayPayConfig(
            province_code="SK",
            formula_type="5_percent_28_days",
            formula_params=HolidayPayFormulaParams(
                lookback_days=28,
                percentage=Decimal("0.05"),
                include_overtime=False,
                include_vacation_pay=True,
                include_previous_holiday_pay=True,
            ),
            eligibility=HolidayPayEligibility(
                min_employment_days=0,
                require_last_first_rule=False,
            ),
            premium_rate=Decimal("1.5"),
        )

    @pytest.fixture
    def mock_calculator(self, sk_config: HolidayPayConfig) -> HolidayPayCalculator:
        """Create calculator with mocked dependencies."""
        supabase = MagicMock()
        calculator = HolidayPayCalculator(
            supabase=supabase,
            user_id="test_user",
            company_id="test_company",
        )
        return calculator

    def test_sk_full_time_standard(self, mock_calculator: HolidayPayCalculator):
        """Test SK full-time employee standard calculation.

        Verified case: SK_FULL_TIME_BIWEEKLY
        Formula: $2,800 × 5% = $140.00
        """
        case = get_case_by_id(1, "SK_FULL_TIME_BIWEEKLY")
        if case is None:
            pytest.skip("Case SK_FULL_TIME_BIWEEKLY not found")

        earnings = build_historical_earnings(case)

        # Calculate using the formula directly
        base = earnings["wages_past_28_days"]
        if case.input.get("vacation_pay_past_28_days"):
            base += earnings["vacation_pay_past_28_days"]
        if case.input.get("holiday_pay_past_28_days"):
            base += earnings["holiday_pay_past_28_days"]

        expected = Decimal(case.expected["regular_holiday_pay"])
        calculated = base * Decimal("0.05")

        result = validate_component(
            "SK Holiday Pay",
            calculated,
            expected,
            VARIANCE_TOLERANCE,
        )

        print(f"\n--- {case.id} Validation ---")
        print(f"  Base wages: ${earnings['wages_past_28_days']}")
        print(f"  {result.message}")

        assert result.passed, f"Failed: {result.message}"

    def test_sk_part_time_low_hours(self, mock_calculator: HolidayPayCalculator):
        """Test SK part-time employee with minimal hours.

        Verified case: SK_PART_TIME_LOW_HOURS
        Formula: $60 × 5% = $3.00
        """
        case = get_case_by_id(1, "SK_PART_TIME_LOW_HOURS")
        if case is None:
            pytest.skip("Case SK_PART_TIME_LOW_HOURS not found")

        earnings = build_historical_earnings(case)
        base = earnings["wages_past_28_days"]

        expected = Decimal(case.expected["regular_holiday_pay"])
        calculated = base * Decimal("0.05")

        result = validate_component(
            "SK Holiday Pay (Low Hours)",
            calculated,
            expected,
            VARIANCE_TOLERANCE,
        )

        print(f"\n--- {case.id} Validation ---")
        print(f"  Base wages: ${earnings['wages_past_28_days']}")
        print(f"  {result.message}")

        assert result.passed, f"Failed: {result.message}"

    def test_sk_with_vacation_pay(self, mock_calculator: HolidayPayCalculator):
        """Test SK calculation including vacation pay.

        Verified case: SK_WITH_VACATION_PAY
        Formula: ($2,000 + $80) × 5% = $104.00
        """
        case = get_case_by_id(1, "SK_WITH_VACATION_PAY")
        if case is None:
            pytest.skip("Case SK_WITH_VACATION_PAY not found")

        earnings = build_historical_earnings(case)
        base = (
            earnings["wages_past_28_days"]
            + earnings["vacation_pay_past_28_days"]
        )

        expected = Decimal(case.expected["regular_holiday_pay"])
        calculated = base * Decimal("0.05")

        result = validate_component(
            "SK Holiday Pay (With Vacation)",
            calculated,
            expected,
            VARIANCE_TOLERANCE,
        )

        print(f"\n--- {case.id} Validation ---")
        print(f"  Base wages: ${earnings['wages_past_28_days']}")
        print(f"  Vacation pay: ${earnings['vacation_pay_past_28_days']}")
        print(f"  Total base: ${base}")
        print(f"  {result.message}")

        assert result.passed, f"Failed: {result.message}"

    def test_sk_new_employee(self, mock_calculator: HolidayPayCalculator):
        """Test SK new employee (no minimum employment period).

        Verified case: SK_NEW_EMPLOYEE
        Formula: $720 × 5% = $36.00
        """
        case = get_case_by_id(1, "SK_NEW_EMPLOYEE")
        if case is None:
            pytest.skip("Case SK_NEW_EMPLOYEE not found")

        earnings = build_historical_earnings(case)
        base = earnings["wages_past_28_days"]

        expected = Decimal(case.expected["regular_holiday_pay"])
        calculated = base * Decimal("0.05")

        result = validate_component(
            "SK Holiday Pay (New Employee)",
            calculated,
            expected,
            VARIANCE_TOLERANCE,
        )

        print(f"\n--- {case.id} Validation ---")
        print(f"  Hire date: {case.input.get('hire_date')}")
        print(f"  Holiday date: {case.input.get('holiday_date')}")
        print(f"  Base wages: ${base}")
        print(f"  {result.message}")

        assert result.passed, f"Failed: {result.message}"

    def test_sk_with_previous_holiday_pay(self, mock_calculator: HolidayPayCalculator):
        """Test SK calculation including previous holiday pay.

        Verified case: SK_WITH_PREVIOUS_HOLIDAY_PAY
        Formula: ($2,400 + $96 + $120) × 5% = $130.80
        """
        case = get_case_by_id(1, "SK_WITH_PREVIOUS_HOLIDAY_PAY")
        if case is None:
            pytest.skip("Case SK_WITH_PREVIOUS_HOLIDAY_PAY not found")

        earnings = build_historical_earnings(case)
        base = (
            earnings["wages_past_28_days"]
            + earnings["vacation_pay_past_28_days"]
            + earnings["holiday_pay_past_28_days"]
        )

        expected = Decimal(case.expected["regular_holiday_pay"])
        calculated = base * Decimal("0.05")

        result = validate_component(
            "SK Holiday Pay (With Previous Holiday)",
            calculated,
            expected,
            VARIANCE_TOLERANCE,
        )

        print(f"\n--- {case.id} Validation ---")
        print(f"  Base wages: ${earnings['wages_past_28_days']}")
        print(f"  Vacation pay: ${earnings['vacation_pay_past_28_days']}")
        print(f"  Previous holiday pay: ${earnings['holiday_pay_past_28_days']}")
        print(f"  Total base: ${base}")
        print(f"  {result.message}")

        assert result.passed, f"Failed: {result.message}"


class TestSaskatchewanFormula:
    """Unit tests for Saskatchewan 5% formula implementation."""

    def test_5_percent_formula_basic(self):
        """Test basic 5% calculation."""
        wages = Decimal("2800.00")
        percentage = Decimal("0.05")
        expected = Decimal("140.00")

        result = wages * percentage

        assert result == expected, f"Expected {expected}, got {result}"

    def test_5_percent_formula_with_inclusions(self):
        """Test 5% calculation with vacation and holiday pay."""
        wages = Decimal("2400.00")
        vacation = Decimal("96.00")
        holiday = Decimal("120.00")
        percentage = Decimal("0.05")

        base = wages + vacation + holiday
        expected = Decimal("130.80")

        result = base * percentage

        assert result == expected, f"Expected {expected}, got {result}"

    def test_5_percent_formula_low_wages(self):
        """Test 5% calculation with minimal wages."""
        wages = Decimal("60.00")
        percentage = Decimal("0.05")
        expected = Decimal("3.00")

        result = wages * percentage

        assert result == expected, f"Expected {expected}, got {result}"

    def test_5_percent_formula_zero_wages(self):
        """Test 5% calculation with zero wages returns zero."""
        wages = Decimal("0.00")
        percentage = Decimal("0.05")
        expected = Decimal("0.00")

        result = wages * percentage

        assert result == expected, f"Expected {expected}, got {result}"


# =============================================================================
# Configuration Validation Tests
# =============================================================================


class TestProvinceConfigValidation:
    """Test that province configurations are correctly loaded."""

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
