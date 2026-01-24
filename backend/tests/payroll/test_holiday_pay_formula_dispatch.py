"""
Tests for Holiday Pay Formula Dispatch Logic.

Verifies that the calculator correctly routes formula_type to the right method.
This is a critical integration point - if dispatch is wrong, the wrong formula runs.
"""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.models.holiday_pay_config import (
    HolidayPayConfig,
    HolidayPayEligibility,
    HolidayPayFormulaParams,
)
from app.services.payroll_run.holiday_pay.calculator import HolidayPayCalculator


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_supabase():
    """Create mock Supabase client."""
    return MagicMock()


@pytest.fixture
def calculator(mock_supabase):
    """Create HolidayPayCalculator with mocked dependencies."""
    return HolidayPayCalculator(
        supabase=mock_supabase,
        user_id="test-user",
        company_id="test-company",
    )


@pytest.fixture
def standard_employee():
    """Standard hourly employee for testing."""
    return {
        "id": "emp-001",
        "hire_date": "2024-01-01",
        "hourly_rate": 25.00,
        "compensation_type": "hourly",
        "employment_type": "regular",
    }


# Common test parameters
HOLIDAY_DATE = date(2025, 7, 1)
PERIOD_START = date(2025, 6, 16)
PERIOD_END = date(2025, 6, 30)
PAY_FREQUENCY = "bi_weekly"
CURRENT_PERIOD_GROSS = Decimal("2000.00")
CURRENT_RUN_ID = "run-001"


# =============================================================================
# Formula Dispatch Tests
# =============================================================================


class TestFormulaDispatch:
    """Verify formula_type correctly routes to the right formula method."""

    def test_dispatch_3_week_average_nl(self, calculator, standard_employee):
        """formula_type='3_week_average_nl' calls apply_3_week_average_nl."""
        config = HolidayPayConfig(
            province_code="NL",
            formula_type="3_week_average_nl",
            formula_params=HolidayPayFormulaParams(
                lookback_weeks_nl=3,
                nl_divisor=15,
                include_overtime=True,
            ),
            eligibility=HolidayPayEligibility(min_employment_days=0, require_last_first_rule=False),
            premium_rate=Decimal("1.5"),
        )

        with patch.object(
            calculator.formula_calculators,
            'apply_3_week_average_nl',
            return_value=Decimal("160.00")
        ) as mock_method:
            result = calculator._calculate_regular_holiday_pay(
                employee=standard_employee,
                config=config,
                pay_frequency=PAY_FREQUENCY,
                period_start=PERIOD_START,
                period_end=PERIOD_END,
                holiday_date=HOLIDAY_DATE,
                current_period_gross=CURRENT_PERIOD_GROSS,
                current_run_id=CURRENT_RUN_ID,
            )

            mock_method.assert_called_once()
            assert result == Decimal("160.00")

    def test_dispatch_irregular_hours(self, calculator, standard_employee):
        """formula_type='irregular_hours' calls apply_irregular_hours."""
        config = HolidayPayConfig(
            province_code="YT",
            formula_type="irregular_hours",
            formula_params=HolidayPayFormulaParams(
                irregular_hours_percentage=Decimal("0.10"),
                irregular_hours_lookback_weeks=2,
                include_overtime=True,
            ),
            eligibility=HolidayPayEligibility(min_employment_days=0, require_last_first_rule=False),
            premium_rate=Decimal("1.5"),
        )

        with patch.object(
            calculator.formula_calculators,
            'apply_irregular_hours',
            return_value=Decimal("200.00")
        ) as mock_method:
            result = calculator._calculate_regular_holiday_pay(
                employee=standard_employee,
                config=config,
                pay_frequency=PAY_FREQUENCY,
                period_start=PERIOD_START,
                period_end=PERIOD_END,
                holiday_date=HOLIDAY_DATE,
                current_period_gross=CURRENT_PERIOD_GROSS,
                current_run_id=CURRENT_RUN_ID,
            )

            mock_method.assert_called_once()
            assert result == Decimal("200.00")

    def test_dispatch_commission(self, calculator, standard_employee):
        """formula_type='commission' calls apply_commission."""
        config = HolidayPayConfig(
            province_code="Federal",
            formula_type="commission",
            formula_params=HolidayPayFormulaParams(
                commission_divisor=60,
                commission_lookback_weeks=12,
            ),
            eligibility=HolidayPayEligibility(min_employment_days=0, require_last_first_rule=False),
            premium_rate=Decimal("1.5"),
        )

        with patch.object(
            calculator.formula_calculators,
            'apply_commission',
            return_value=Decimal("133.33")
        ) as mock_method:
            result = calculator._calculate_regular_holiday_pay(
                employee=standard_employee,
                config=config,
                pay_frequency=PAY_FREQUENCY,
                period_start=PERIOD_START,
                period_end=PERIOD_END,
                holiday_date=HOLIDAY_DATE,
                current_period_gross=CURRENT_PERIOD_GROSS,
                current_run_id=CURRENT_RUN_ID,
            )

            mock_method.assert_called_once()
            assert result == Decimal("133.33")

    def test_dispatch_nt_split_hourly(self, calculator):
        """formula_type='nt_split_by_compensation' with hourly employee uses daily rate."""
        employee = {
            "id": "emp-nt-hourly",
            "hire_date": "2024-01-01",
            "hourly_rate": 30.00,
            "compensation_type": "hourly",
        }
        config = HolidayPayConfig(
            province_code="NT",
            formula_type="nt_split_by_compensation",
            formula_params=HolidayPayFormulaParams(
                include_overtime=False,
                default_daily_hours=Decimal("8"),
            ),
            eligibility=HolidayPayEligibility(min_employment_days=0, require_last_first_rule=False),
            premium_rate=Decimal("1.5"),
        )

        # Mock get_normal_daily_hours to return 8
        with patch.object(
            calculator.work_day_tracker,
            'get_normal_daily_hours',
            return_value=Decimal("8")
        ):
            result = calculator._calculate_regular_holiday_pay(
                employee=employee,
                config=config,
                pay_frequency=PAY_FREQUENCY,
                period_start=PERIOD_START,
                period_end=PERIOD_END,
                holiday_date=HOLIDAY_DATE,
                current_period_gross=CURRENT_PERIOD_GROSS,
                current_run_id=CURRENT_RUN_ID,
            )

            # $30/hr × 8 hours = $240
            assert result == Decimal("240")

    def test_dispatch_nt_split_salaried(self, calculator):
        """formula_type='nt_split_by_compensation' with salaried employee uses 4-week avg."""
        employee = {
            "id": "emp-nt-salary",
            "hire_date": "2024-01-01",
            "annual_salary": 60000.00,
            "compensation_type": "salary",
        }
        config = HolidayPayConfig(
            province_code="NT",
            formula_type="nt_split_by_compensation",
            formula_params=HolidayPayFormulaParams(
                include_overtime=False,
                default_daily_hours=Decimal("8"),
                new_employee_fallback="pro_rated",
            ),
            eligibility=HolidayPayEligibility(min_employment_days=0, require_last_first_rule=False),
            premium_rate=Decimal("1.5"),
        )

        with patch.object(
            calculator.formula_calculators,
            'apply_4_week_average_from_payroll',
            return_value=Decimal("230.77")
        ) as mock_method:
            result = calculator._calculate_regular_holiday_pay(
                employee=employee,
                config=config,
                pay_frequency=PAY_FREQUENCY,
                period_start=PERIOD_START,
                period_end=PERIOD_END,
                holiday_date=HOLIDAY_DATE,
                current_period_gross=CURRENT_PERIOD_GROSS,
                current_run_id=CURRENT_RUN_ID,
            )

            mock_method.assert_called_once()
            assert result == Decimal("230.77")

    def test_dispatch_yt_split_regular(self, calculator):
        """formula_type='yt_split_by_employment' with regular employee uses 30_day_average."""
        employee = {
            "id": "emp-yt-regular",
            "hire_date": "2024-01-01",
            "hourly_rate": 25.00,
            "employment_type": "regular",
        }
        config = HolidayPayConfig(
            province_code="YT",
            formula_type="yt_split_by_employment",
            formula_params=HolidayPayFormulaParams(
                method="total_wages_div_days",
                lookback_days=30,
                include_overtime=False,
                default_daily_hours=Decimal("8"),
            ),
            eligibility=HolidayPayEligibility(min_employment_days=0, require_last_first_rule=False),
            premium_rate=Decimal("1.5"),
        )

        with patch.object(
            calculator.formula_calculators,
            'apply_30_day_average',
            return_value=Decimal("200.00")
        ) as mock_method:
            result = calculator._calculate_regular_holiday_pay(
                employee=employee,
                config=config,
                pay_frequency=PAY_FREQUENCY,
                period_start=PERIOD_START,
                period_end=PERIOD_END,
                holiday_date=HOLIDAY_DATE,
                current_period_gross=CURRENT_PERIOD_GROSS,
                current_run_id=CURRENT_RUN_ID,
            )

            mock_method.assert_called_once()
            assert result == Decimal("200.00")

    def test_dispatch_yt_split_casual(self, calculator):
        """formula_type='yt_split_by_employment' with casual employee uses irregular_hours."""
        employee = {
            "id": "emp-yt-casual",
            "hire_date": "2024-01-01",
            "hourly_rate": 20.00,
            "employment_type": "casual",
        }
        config = HolidayPayConfig(
            province_code="YT",
            formula_type="yt_split_by_employment",
            formula_params=HolidayPayFormulaParams(
                irregular_hours_percentage=Decimal("0.10"),
                irregular_hours_lookback_weeks=2,
                include_overtime=True,
            ),
            eligibility=HolidayPayEligibility(min_employment_days=0, require_last_first_rule=False),
            premium_rate=Decimal("1.5"),
        )

        with patch.object(
            calculator.formula_calculators,
            'apply_irregular_hours',
            return_value=Decimal("150.00")
        ) as mock_method:
            result = calculator._calculate_regular_holiday_pay(
                employee=employee,
                config=config,
                pay_frequency=PAY_FREQUENCY,
                period_start=PERIOD_START,
                period_end=PERIOD_END,
                holiday_date=HOLIDAY_DATE,
                current_period_gross=CURRENT_PERIOD_GROSS,
                current_run_id=CURRENT_RUN_ID,
            )

            mock_method.assert_called_once()
            assert result == Decimal("150.00")

    def test_dispatch_unknown_formula_type_fallback(self, calculator, standard_employee):
        """Unknown formula_type uses default fallback (hourly_rate × default_hours)."""
        config = HolidayPayConfig(
            province_code="XX",
            formula_type="unknown_formula",
            formula_params=HolidayPayFormulaParams(
                default_daily_hours=Decimal("8"),
            ),
            eligibility=HolidayPayEligibility(min_employment_days=0, require_last_first_rule=False),
            premium_rate=Decimal("1.5"),
        )

        result = calculator._calculate_regular_holiday_pay(
            employee=standard_employee,
            config=config,
            pay_frequency=PAY_FREQUENCY,
            period_start=PERIOD_START,
            period_end=PERIOD_END,
            holiday_date=HOLIDAY_DATE,
            current_period_gross=CURRENT_PERIOD_GROSS,
            current_run_id=CURRENT_RUN_ID,
        )

        # Fallback: 8 hours × $25/hr = $200
        assert result == Decimal("200")
