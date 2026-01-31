"""
Holiday Pay Tests for Federal Jurisdiction

Tests for federally regulated employees under the Canada Labour Code.

Reference:
- Canada Labour Code Part III s.196-202
- https://laws-lois.justice.gc.ca/eng/acts/L-2/page-1.html

Federal Rules:
- Formula: 4_week_average for general employees (1/20 of wages in 4 weeks before holiday week)
- Formula: Commission employees use 1/60th for 12 weeks (needs verification)
- Min employment: None (all federally regulated employees qualify)
- Last/first rule: No
- Premium rate: 1.5x
"""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

from app.models.holiday_pay_config import (
    HolidayPayConfig,
    HolidayPayEligibility,
    HolidayPayFormulaParams,
)
from app.services.payroll_run.holiday_pay_calculator import HolidayPayCalculator
from tests.payroll.conftest import MockConfigLoader


class TestFederalGeneralEmployees:
    """Tests for federally regulated general employees.

    Formula: (wages in 4 weeks) / 20
    - Does NOT include vacation pay
    - Does NOT include overtime
    """

    def test_federal_eligible_no_minimum_employment(self, mock_supabase):
        """Test federal employees are eligible regardless of employment length."""
        federal_config = HolidayPayConfig(
            province_code="Federal",
            formula_type="4_week_average",
            formula_params=HolidayPayFormulaParams(
                lookback_weeks=4,
                divisor=20,
                include_vacation_pay=False,
                include_overtime=False,
                new_employee_fallback="pro_rated",
            ),
            eligibility=HolidayPayEligibility(
                min_employment_days=0,
                require_last_first_rule=False,
            ),
            premium_rate=Decimal("1.5"),
        )

        loader = MockConfigLoader({"Federal": federal_config})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=loader,
        )

        # Even recently hired employee (10 days)
        hire_date = (date.today() - timedelta(days=10)).isoformat()
        employee = {
            "id": "emp-fed-001",
            "first_name": "Alex",
            "last_name": "Chen",
            "hourly_rate": 28.00,
            "hire_date": hire_date,
        }

        holidays = [{"holiday_date": date.today().isoformat(), "name": "Test Holiday", "province": "Federal"}]

        result = calculator.calculate_holiday_pay(
            employee=employee,
            province="Federal",
            pay_frequency="bi_weekly",
            period_start=date.today() - timedelta(days=7),
            period_end=date.today() + timedelta(days=7),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("2240"),
            current_run_id="run-001",
        )

        # Federal: 8h × $28 = $224 (pro_rated fallback for new employee)
        assert result.regular_holiday_pay == Decimal("224")

    def test_federal_4_week_average_without_vacation(self, mock_supabase):
        """Test federal formula excludes vacation pay."""
        federal_config = HolidayPayConfig(
            province_code="Federal",
            formula_type="4_week_average",
            formula_params=HolidayPayFormulaParams(
                lookback_weeks=4,
                divisor=20,
                include_vacation_pay=False,
                include_overtime=False,
                new_employee_fallback="pro_rated",
            ),
            eligibility=HolidayPayEligibility(
                min_employment_days=0,
                require_last_first_rule=False,
            ),
            premium_rate=Decimal("1.5"),
        )

        loader = MockConfigLoader({"Federal": federal_config})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=loader,
        )

        employee = {
            "id": "emp-fed-002",
            "hourly_rate": 30.00,
            "hire_date": "2024-01-01",
        }

        holidays = [{"holiday_date": "2025-01-01", "name": "New Year's Day", "province": "Federal"}]

        # Mock historical data: $2000 regular + $200 vacation (vacation should NOT be included)
        mock_data = MagicMock()
        mock_data.data = [
            {"gross_regular": "1000.00", "gross_overtime": "0", "vacation_pay_paid": "100.00"},
            {"gross_regular": "1000.00", "gross_overtime": "0", "vacation_pay_paid": "100.00"},
        ]

        def table_side_effect(table_name):
            mock_table = MagicMock()
            if table_name == "payroll_records":
                result = MagicMock()
                result.execute.return_value = mock_data
                mock_table.select.return_value.eq.return_value.neq.return_value.gte.return_value.lt.return_value.in_.return_value = result
            return mock_table

        mock_supabase.table.side_effect = table_side_effect

        result = calculator.calculate_holiday_pay(
            employee=employee,
            province="Federal",
            pay_frequency="bi_weekly",
            period_start=date(2024, 12, 29),
            period_end=date(2025, 1, 11),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("2400"),
            current_run_id="run-001",
        )

        # Federal: ($2000) / 20 = $100 (vacation NOT included)
        assert result.regular_holiday_pay == Decimal("100")

    def test_federal_premium_pay(self, mock_supabase):
        """Test federal premium pay for working on holiday."""
        federal_config = HolidayPayConfig(
            province_code="Federal",
            formula_type="4_week_average",
            formula_params=HolidayPayFormulaParams(
                lookback_weeks=4,
                divisor=20,
                include_vacation_pay=False,
                include_overtime=False,
                new_employee_fallback="pro_rated",
            ),
            eligibility=HolidayPayEligibility(
                min_employment_days=0,
                require_last_first_rule=False,
            ),
            premium_rate=Decimal("1.5"),
        )

        loader = MockConfigLoader({"Federal": federal_config})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=loader,
        )

        employee = {
            "id": "emp-fed-premium",
            "hourly_rate": 32.00,
            "hire_date": "2024-01-01",
        }

        holidays = [{"holiday_date": "2025-01-01", "name": "New Year's Day", "province": "Federal"}]
        work_entries = [{"holidayDate": "2025-01-01", "hoursWorked": 8}]

        result = calculator.calculate_holiday_pay(
            employee=employee,
            province="Federal",
            pay_frequency="bi_weekly",
            period_start=date(2024, 12, 29),
            period_end=date(2025, 1, 11),
            holidays_in_period=holidays,
            holiday_work_entries=work_entries,
            current_period_gross=Decimal("2560"),
            current_run_id="run-001",
        )

        # Regular: 8h × $32 = $256
        # Premium: 8h × $32 × 1.5 = $384
        assert result.regular_holiday_pay == Decimal("256")
        assert result.premium_holiday_pay == Decimal("384")


class TestFederalCommissionEmployees:
    """Tests for federally regulated commission employees.

    Commission Formula: 1/60th of wages in 12 weeks before holiday week

    NOTE: This formula needs verification and implementation. Currently using
    the general 4_week_average formula.

    TODO: Implement commission-specific formula when verified
    """

    def test_commission_formula_placeholder(self, mock_supabase):
        """Placeholder test for commission employee formula.

        The Canada Labour Code specifies that commission employees should
        receive 1/60th of wages earned in the 12 weeks before the holiday week.

        This needs:
        1. Verification of the exact formula
        2. Implementation in holiday_pay_calculator.py
        3. Configuration support for commission employee type

        Reference: Canada Labour Code Part III s.196-202
        """
        # This is a placeholder to document the need for this feature
        federal_config = HolidayPayConfig(
            province_code="Federal",
            formula_type="4_week_average",
            formula_params=HolidayPayFormulaParams(
                lookback_weeks=4,
                divisor=20,
                include_vacation_pay=False,
                include_overtime=False,
                new_employee_fallback="pro_rated",
            ),
            eligibility=HolidayPayEligibility(
                min_employment_days=0,
                require_last_first_rule=False,
            ),
            premium_rate=Decimal("1.5"),
        )

        loader = MockConfigLoader({"Federal": federal_config})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=loader,
        )

        employee = {
            "id": "emp-fed-commission",
            "hourly_rate": 0,  # Commission employee
            "hire_date": "2024-01-01",
        }

        holidays = [{"holiday_date": "2025-01-01", "name": "New Year's Day", "province": "Federal"}]

        result = calculator.calculate_holiday_pay(
            employee=employee,
            province="Federal",
            pay_frequency="bi_weekly",
            period_start=date(2024, 12, 29),
            period_end=date(2025, 1, 11),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("0"),
            current_run_id="run-001",
        )

        # Currently returns $0 since no hourly rate and no historical data
        # TODO: Implement commission formula: (wages in 12 weeks) / 60
        assert result.regular_holiday_pay == Decimal("0")


class TestFederalEdgeCases:
    """Tests for federal jurisdiction edge cases."""

    def test_federal_no_historical_data_pro_rated(self, mock_supabase):
        """Test federal new employee with pro_rated fallback."""
        federal_config = HolidayPayConfig(
            province_code="Federal",
            formula_type="4_week_average",
            formula_params=HolidayPayFormulaParams(
                lookback_weeks=4,
                divisor=20,
                include_vacation_pay=False,
                include_overtime=False,
                new_employee_fallback="pro_rated",
            ),
            eligibility=HolidayPayEligibility(
                min_employment_days=0,
                require_last_first_rule=False,
            ),
            premium_rate=Decimal("1.5"),
        )

        loader = MockConfigLoader({"Federal": federal_config})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=loader,
        )

        employee = {
            "id": "emp-fed-new",
            "hourly_rate": 35.00,
            "hire_date": "2024-12-01",  # Recently hired
        }

        holidays = [{"holiday_date": "2025-01-01", "name": "New Year's Day", "province": "Federal"}]

        # Mock empty historical data
        mock_data = MagicMock()
        mock_data.data = []

        def table_side_effect(table_name):
            mock_table = MagicMock()
            if table_name == "payroll_records":
                result = MagicMock()
                result.execute.return_value = mock_data
                mock_table.select.return_value.eq.return_value.neq.return_value.gte.return_value.lt.return_value.in_.return_value = result
            return mock_table

        mock_supabase.table.side_effect = table_side_effect

        result = calculator.calculate_holiday_pay(
            employee=employee,
            province="Federal",
            pay_frequency="bi_weekly",
            period_start=date(2024, 12, 29),
            period_end=date(2025, 1, 11),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("2800"),
            current_run_id="run-001",
        )

        # Pro_rated fallback: 8h × $35 = $280
        assert result.regular_holiday_pay == Decimal("280")

    def test_federal_multiple_holidays_in_period(self, mock_supabase):
        """Test federal calculation with multiple holidays in same period."""
        federal_config = HolidayPayConfig(
            province_code="Federal",
            formula_type="4_week_average",
            formula_params=HolidayPayFormulaParams(
                lookback_weeks=4,
                divisor=20,
                include_vacation_pay=False,
                include_overtime=False,
                new_employee_fallback="pro_rated",
            ),
            eligibility=HolidayPayEligibility(
                min_employment_days=0,
                require_last_first_rule=False,
            ),
            premium_rate=Decimal("1.5"),
        )

        loader = MockConfigLoader({"Federal": federal_config})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=loader,
        )

        employee = {
            "id": "emp-fed-multi",
            "hourly_rate": 25.00,
            "hire_date": "2024-01-01",
        }

        holidays = [
            {"holiday_date": "2025-12-25", "name": "Christmas Day", "province": "Federal"},
            {"holiday_date": "2025-12-26", "name": "Boxing Day", "province": "Federal"},
        ]

        result = calculator.calculate_holiday_pay(
            employee=employee,
            province="Federal",
            pay_frequency="bi_weekly",
            period_start=date(2025, 12, 20),
            period_end=date(2026, 1, 2),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("2000"),
            current_run_id="run-001",
        )

        # 2 holidays: 8h × $25 × 2 = $400
        assert result.regular_holiday_pay == Decimal("400")
