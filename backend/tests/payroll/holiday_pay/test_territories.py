"""
Holiday Pay Tests for Canadian Territories

Tests for Northwest Territories (NT), Nunavut (NU), and Yukon (YT).

These territories follow similar rules but have unique requirements. This module provides
comprehensive tests to ensure accuracy.

References:
- NT: https://www.ece.gov.nt.ca/en/services/employment-standards/frequently-asked-questions
- NU: https://nu-lsco.ca/faq-s?tmpl=component&faqid=11
- YT: https://yukon.ca/en/employment/employment-standards/find-employee-information-statutory-holidays
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


class TestNorthwestTerritories:
    """Tests for Northwest Territories holiday pay calculations.

    NWT Rules:
    - Formula: 30_day_average (default_daily_hours × hourly_rate)
    - Min employment: 30 days within 12 months prior
    - Last/first rule: Yes (must work last shift before AND first shift after)
    - Premium rate: 1.5x
    """

    def test_nt_eligible_with_last_first_compliance(self, mock_supabase):
        """Test NT employee with last/first rule compliance gets holiday pay."""
        nt_config = HolidayPayConfig(
            province_code="NT",
            formula_type="30_day_average",
            formula_params=HolidayPayFormulaParams(
                lookback_days=30,
                method="total_wages_div_days",
                default_daily_hours=Decimal("8"),
                new_employee_fallback="ineligible",
            ),
            eligibility=HolidayPayEligibility(
                min_employment_days=30,
                require_last_first_rule=True,
            ),
            premium_rate=Decimal("1.5"),
        )

        loader = MockConfigLoader({"NT": nt_config})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=loader,
        )

        employee = {
            "id": "emp-nt-001",
            "first_name": "John",
            "last_name": "Tulo",
            "hourly_rate": 26.00,
            "hire_date": "2024-10-01",  # >30 days ago
        }

        holidays = [{"holiday_date": "2025-01-01", "name": "New Year's Day", "province": "NT"}]

        # Mock timesheet with last/first rule compliance
        timesheet_data = [
            {
                "work_date": "2024-12-31",  # Day before holiday
                "regular_hours": "8.0",
                "overtime_hours": "0",
            },
            {
                "work_date": "2025-01-02",  # Day after holiday
                "regular_hours": "8.0",
                "overtime_hours": "0",
            },
        ]

        mock_timesheet_result = MagicMock()
        mock_timesheet_result.data = timesheet_data

        def table_side_effect(table_name):
            mock_table = MagicMock()
            if table_name == "timesheet_entries":
                result = MagicMock()
                result.execute.return_value = mock_timesheet_result
                mock_table.select.return_value.eq.return_value.gte.return_value.lte.return_value = result
                mock_table.select.return_value.eq.return_value.gte.return_value.lte.return_value.order.return_value.limit.return_value.execute.return_value = mock_timesheet_result
                mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_timesheet_result
            return mock_table

        mock_supabase.table.side_effect = table_side_effect

        result = calculator.calculate_holiday_pay(
            employee=employee,
            province="NT",
            pay_frequency="bi_weekly",
            period_start=date(2024, 12, 29),
            period_end=date(2025, 1, 11),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("2080"),
            current_run_id="run-001",
        )

        # NT: 8h × $26 = $208
        assert result.regular_holiday_pay == Decimal("208")

    def test_nt_ineligible_without_last_first_compliance(self, mock_supabase):
        """Test NT employee without last/first rule compliance is ineligible."""
        nt_config = HolidayPayConfig(
            province_code="NT",
            formula_type="30_day_average",
            formula_params=HolidayPayFormulaParams(
                lookback_days=30,
                method="total_wages_div_days",
                default_daily_hours=Decimal("8"),
                new_employee_fallback="ineligible",
            ),
            eligibility=HolidayPayEligibility(
                min_employment_days=30,
                require_last_first_rule=True,
            ),
            premium_rate=Decimal("1.5"),
        )

        loader = MockConfigLoader({"NT": nt_config})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=loader,
        )

        employee = {
            "id": "emp-nt-002",
            "hourly_rate": 25.00,
            "hire_date": "2024-10-01",
        }

        holidays = [{"holiday_date": "2025-01-01", "name": "New Year's Day", "province": "NT"}]

        # Mock empty timesheet (no last/first compliance)
        mock_timesheet_result = MagicMock()
        mock_timesheet_result.data = []

        def table_side_effect(table_name):
            mock_table = MagicMock()
            if table_name == "timesheet_entries":
                result = MagicMock()
                result.execute.return_value = mock_timesheet_result
                mock_table.select.return_value.eq.return_value.gte.return_value.lte.return_value = result
                mock_table.select.return_value.eq.return_value.gte.return_value.lte.return_value.order.return_value.limit.return_value.execute.return_value = mock_timesheet_result
            return mock_table

        mock_supabase.table.side_effect = table_side_effect

        result = calculator.calculate_holiday_pay(
            employee=employee,
            province="NT",
            pay_frequency="bi_weekly",
            period_start=date(2024, 12, 29),
            period_end=date(2025, 1, 11),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("2000"),
            current_run_id="run-001",
        )

        # Should be ineligible due to no last/first compliance
        assert result.regular_holiday_pay == Decimal("0")
        assert result.calculation_details["holidays"][0]["eligible"] is False

    def test_nt_premium_pay(self, mock_supabase):
        """Test NT premium pay calculation."""
        nt_config = HolidayPayConfig(
            province_code="NT",
            formula_type="30_day_average",
            formula_params=HolidayPayFormulaParams(
                lookback_days=30,
                method="total_wages_div_days",
                default_daily_hours=Decimal("8"),
                new_employee_fallback="ineligible",
            ),
            eligibility=HolidayPayEligibility(
                min_employment_days=30,
                require_last_first_rule=True,
            ),
            premium_rate=Decimal("1.5"),
        )

        loader = MockConfigLoader({"NT": nt_config})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=loader,
        )

        employee = {
            "id": "emp-nt-premium",
            "hourly_rate": 28.00,
            "hire_date": "2024-10-01",
        }

        holidays = [{"holiday_date": "2025-01-01", "name": "New Year's Day", "province": "NT"}]
        work_entries = [{"holidayDate": "2025-01-01", "hoursWorked": 8}]

        # Mock last/first compliance
        timesheet_data = [
            {"work_date": "2024-12-31", "regular_hours": "8.0", "overtime_hours": "0"},
            {"work_date": "2025-01-02", "regular_hours": "8.0", "overtime_hours": "0"},
        ]

        mock_timesheet_result = MagicMock()
        mock_timesheet_result.data = timesheet_data

        def table_side_effect(table_name):
            mock_table = MagicMock()
            if table_name == "timesheet_entries":
                result = MagicMock()
                result.execute.return_value = mock_timesheet_result
                mock_table.select.return_value.eq.return_value.gte.return_value.lte.return_value = result
                mock_table.select.return_value.eq.return_value.gte.return_value.lte.return_value.order.return_value.limit.return_value.execute.return_value = mock_timesheet_result
                mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_timesheet_result
            return mock_table

        mock_supabase.table.side_effect = table_side_effect

        result = calculator.calculate_holiday_pay(
            employee=employee,
            province="NT",
            pay_frequency="bi_weekly",
            period_start=date(2024, 12, 29),
            period_end=date(2025, 1, 11),
            holidays_in_period=holidays,
            holiday_work_entries=work_entries,
            current_period_gross=Decimal("2240"),
            current_run_id="run-001",
        )

        # Regular: 8h × $28 = $224
        # Premium: 8h × $28 × 1.5 = $336
        assert result.regular_holiday_pay == Decimal("224")
        assert result.premium_holiday_pay == Decimal("336")


class TestNunavut:
    """Tests for Nunavut holiday pay calculations.

    Nunavut Rules:
    - Formula: 30_day_average (default_daily_hours × hourly_rate)
    - Min employment: 30 days within 12 months prior
    - Last/first rule: Yes (must work last shift before AND first shift after)
    - Premium rate: 1.5x
    """

    def test_nu_eligible_employee(self, mock_supabase):
        """Test NU employee with 30+ days employment and last/first compliance."""
        nu_config = HolidayPayConfig(
            province_code="NU",
            formula_type="30_day_average",
            formula_params=HolidayPayFormulaParams(
                lookback_days=30,
                method="total_wages_div_days",
                default_daily_hours=Decimal("8"),
                new_employee_fallback="ineligible",
            ),
            eligibility=HolidayPayEligibility(
                min_employment_days=30,
                require_last_first_rule=True,
            ),
            premium_rate=Decimal("1.5"),
        )

        loader = MockConfigLoader({"NU": nu_config})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=loader,
        )

        employee = {
            "id": "emp-nu-001",
            "first_name": "Aputi",
            "last_name": "Kullualik",
            "hourly_rate": 27.00,
            "hire_date": "2024-10-01",
        }

        holidays = [{"holiday_date": "2025-01-01", "name": "New Year's Day", "province": "NU"}]

        # Mock last/first compliance
        timesheet_data = [
            {"work_date": "2024-12-31", "regular_hours": "8.0", "overtime_hours": "0"},
            {"work_date": "2025-01-02", "regular_hours": "8.0", "overtime_hours": "0"},
        ]

        mock_timesheet_result = MagicMock()
        mock_timesheet_result.data = timesheet_data

        def table_side_effect(table_name):
            mock_table = MagicMock()
            if table_name == "timesheet_entries":
                result = MagicMock()
                result.execute.return_value = mock_timesheet_result
                mock_table.select.return_value.eq.return_value.gte.return_value.lte.return_value = result
                mock_table.select.return_value.eq.return_value.gte.return_value.lte.return_value.order.return_value.limit.return_value.execute.return_value = mock_timesheet_result
                mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_timesheet_result
            return mock_table

        mock_supabase.table.side_effect = table_side_effect

        result = calculator.calculate_holiday_pay(
            employee=employee,
            province="NU",
            pay_frequency="bi_weekly",
            period_start=date(2024, 12, 29),
            period_end=date(2025, 1, 11),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("2160"),
            current_run_id="run-001",
        )

        # NU: 8h × $27 = $216
        assert result.regular_holiday_pay == Decimal("216")

    def test_nu_edge_case_no_work_history(self, mock_supabase):
        """Test NU employee with no work history (edge case)."""
        nu_config = HolidayPayConfig(
            province_code="NU",
            formula_type="30_day_average",
            formula_params=HolidayPayFormulaParams(
                lookback_days=30,
                method="total_wages_div_days",
                default_daily_hours=Decimal("8"),
                new_employee_fallback="ineligible",
            ),
            eligibility=HolidayPayEligibility(
                min_employment_days=30,
                require_last_first_rule=True,
            ),
            premium_rate=Decimal("1.5"),
        )

        loader = MockConfigLoader({"NU": nu_config})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=loader,
        )

        employee = {
            "id": "emp-nu-new",
            "hourly_rate": 25.00,
            "hire_date": "2024-10-01",
        }

        holidays = [{"holiday_date": "2025-01-01", "name": "New Year's Day", "province": "NU"}]

        # Mock empty timesheet (no work history)
        mock_timesheet_result = MagicMock()
        mock_timesheet_result.data = []

        def table_side_effect(table_name):
            mock_table = MagicMock()
            if table_name == "timesheet_entries":
                result = MagicMock()
                result.execute.return_value = mock_timesheet_result
                mock_table.select.return_value.eq.return_value.gte.return_value.lte.return_value = result
                mock_table.select.return_value.eq.return_value.gte.return_value.lte.return_value.order.return_value.limit.return_value.execute.return_value = mock_timesheet_result
            return mock_table

        mock_supabase.table.side_effect = table_side_effect

        result = calculator.calculate_holiday_pay(
            employee=employee,
            province="NU",
            pay_frequency="bi_weekly",
            period_start=date(2024, 12, 29),
            period_end=date(2025, 1, 11),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("2000"),
            current_run_id="run-001",
        )

        # Should be ineligible due to no last/first compliance
        assert result.regular_holiday_pay == Decimal("0")
        assert result.calculation_details["holidays"][0]["eligible"] is False


class TestYukon:
    """Tests for Yukon holiday pay calculations.

    Yukon Rules:
    - Formula: 30_day_average (default_daily_hours × hourly_rate)
    - Min employment: 30 calendar days
    - Last/first rule: Yes (unless permitted absence)
    - Premium rate: 1.5x
    - Note: May have dual formula for different industries (needs verification)
    """

    def test_yt_eligible_employee(self, mock_supabase):
        """Test YT employee with 30+ days employment gets holiday pay."""
        yt_config = HolidayPayConfig(
            province_code="YT",
            formula_type="30_day_average",
            formula_params=HolidayPayFormulaParams(
                lookback_days=30,
                method="total_wages_div_days",
                default_daily_hours=Decimal("8"),
                new_employee_fallback="ineligible",
            ),
            eligibility=HolidayPayEligibility(
                min_employment_days=30,
                require_last_first_rule=True,
            ),
            premium_rate=Decimal("1.5"),
        )

        loader = MockConfigLoader({"YT": yt_config})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=loader,
        )

        employee = {
            "id": "emp-yt-001",
            "first_name": "Michele",
            "last_name": "Stirling",
            "hourly_rate": 25.00,
            "hire_date": "2024-10-01",
        }

        holidays = [{"holiday_date": "2025-01-01", "name": "New Year's Day", "province": "YT"}]

        # Mock last/first compliance
        timesheet_data = [
            {"work_date": "2024-12-31", "regular_hours": "8.0", "overtime_hours": "0"},
            {"work_date": "2025-01-02", "regular_hours": "8.0", "overtime_hours": "0"},
        ]

        mock_timesheet_result = MagicMock()
        mock_timesheet_result.data = timesheet_data

        def table_side_effect(table_name):
            mock_table = MagicMock()
            if table_name == "timesheet_entries":
                result = MagicMock()
                result.execute.return_value = mock_timesheet_result
                mock_table.select.return_value.eq.return_value.gte.return_value.lte.return_value = result
                mock_table.select.return_value.eq.return_value.gte.return_value.lte.return_value.order.return_value.limit.return_value.execute.return_value = mock_timesheet_result
                mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_timesheet_result
            return mock_table

        mock_supabase.table.side_effect = table_side_effect

        result = calculator.calculate_holiday_pay(
            employee=employee,
            province="YT",
            pay_frequency="bi_weekly",
            period_start=date(2024, 12, 29),
            period_end=date(2025, 1, 11),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("2000"),
            current_run_id="run-001",
        )

        # YT: 8h × $25 = $200
        assert result.regular_holiday_pay == Decimal("200")

    def test_yt_premium_pay_overtime_hours(self, mock_supabase):
        """Test YT premium pay with overtime hours worked on holiday."""
        yt_config = HolidayPayConfig(
            province_code="YT",
            formula_type="30_day_average",
            formula_params=HolidayPayFormulaParams(
                lookback_days=30,
                method="total_wages_div_days",
                default_daily_hours=Decimal("8"),
                new_employee_fallback="ineligible",
            ),
            eligibility=HolidayPayEligibility(
                min_employment_days=30,
                require_last_first_rule=True,
            ),
            premium_rate=Decimal("1.5"),
        )

        loader = MockConfigLoader({"YT": yt_config})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=loader,
        )

        employee = {
            "id": "emp-yt-premium",
            "hourly_rate": 30.00,
            "hire_date": "2024-10-01",
        }

        holidays = [{"holiday_date": "2025-01-01", "name": "New Year's Day", "province": "YT"}]
        # 10 hours worked on holiday (includes 2 overtime)
        work_entries = [{"holidayDate": "2025-01-01", "hoursWorked": 10}]

        # Mock last/first compliance
        timesheet_data = [
            {"work_date": "2024-12-31", "regular_hours": "8.0", "overtime_hours": "0"},
            {"work_date": "2025-01-02", "regular_hours": "8.0", "overtime_hours": "0"},
        ]

        mock_timesheet_result = MagicMock()
        mock_timesheet_result.data = timesheet_data

        def table_side_effect(table_name):
            mock_table = MagicMock()
            if table_name == "timesheet_entries":
                result = MagicMock()
                result.execute.return_value = mock_timesheet_result
                mock_table.select.return_value.eq.return_value.gte.return_value.lte.return_value = result
                mock_table.select.return_value.eq.return_value.gte.return_value.lte.return_value.order.return_value.limit.return_value.execute.return_value = mock_timesheet_result
                mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_timesheet_result
            return mock_table

        mock_supabase.table.side_effect = table_side_effect

        result = calculator.calculate_holiday_pay(
            employee=employee,
            province="YT",
            pay_frequency="bi_weekly",
            period_start=date(2024, 12, 29),
            period_end=date(2025, 1, 11),
            holidays_in_period=holidays,
            holiday_work_entries=work_entries,
            current_period_gross=Decimal("2400"),
            current_run_id="run-001",
        )

        # Regular: 8h × $30 = $240
        # Premium: 10h × $30 × 1.5 = $450
        assert result.regular_holiday_pay == Decimal("240")
        assert result.premium_holiday_pay == Decimal("450")

    def test_yt_error_handling_database_failure(self, mock_supabase):
        """Test YT error handling when database query fails."""
        yt_config = HolidayPayConfig(
            province_code="YT",
            formula_type="30_day_average",
            formula_params=HolidayPayFormulaParams(
                lookback_days=30,
                method="total_wages_div_days",
                default_daily_hours=Decimal("8"),
                new_employee_fallback="ineligible",
            ),
            eligibility=HolidayPayEligibility(
                min_employment_days=30,
                require_last_first_rule=True,
            ),
            premium_rate=Decimal("1.5"),
        )

        loader = MockConfigLoader({"YT": yt_config})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=loader,
        )

        employee = {
            "id": "emp-yt-error",
            "hourly_rate": 25.00,
            "hire_date": "2024-10-01",
        }

        holidays = [{"holiday_date": "2025-01-01", "name": "New Year's Day", "province": "YT"}]

        # Mock database exception
        mock_supabase.table.side_effect = Exception("Database connection failed")

        result = calculator.calculate_holiday_pay(
            employee=employee,
            province="YT",
            pay_frequency="bi_weekly",
            period_start=date(2024, 12, 29),
            period_end=date(2025, 1, 11),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("2000"),
            current_run_id="run-001",
        )

        # Should return $0 on error for 30_day_average with ineligible fallback
        assert result.regular_holiday_pay == Decimal("0")
