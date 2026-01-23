"""
Holiday Pay Tests for Atlantic Provinces

Tests for Nova Scotia (NS), Prince Edward Island (PE), New Brunswick (NB), and Newfoundland (NL).

These provinces have unique rules and varying test coverage. This module provides
comprehensive tests to ensure accuracy.

References:
- NS: https://nslegislature.ca/sites/default/files/legc/bills/statutes/labour%20standards%20code.pdf
- PE: https://www.princeedwardisland.ca/en/information/workforce-advanced-learning-and-population/paid-holidays
- NB: https://www2.gnb.ca/content/gnb/en/departments/post-secondary_education_training_and_labour/employment_standards/content/employment_standards.html
- NL: https://www.gov.nl.ca/cec/
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


class TestNovaScotia:
    """Tests for Nova Scotia holiday pay calculations.

    Nova Scotia Rules:
    - Formula: 30_day_average (default_daily_hours × hourly_rate)
    - Min employment: 30 days
    - Last/first rule: No
    - Premium rate: 1.5x
    - Special: Remembrance Day requires actual work (needs verification)
    """

    def test_ns_eligible_employee_single_holiday(self, mock_supabase):
        """Test NS employee with 30+ days employment gets holiday pay."""
        # NS Config
        ns_config = HolidayPayConfig(
            province_code="NS",
            formula_type="30_day_average",
            formula_params=HolidayPayFormulaParams(
                lookback_days=30,
                method="total_wages_div_days",
                default_daily_hours=Decimal("8"),
                new_employee_fallback="ineligible",
            ),
            eligibility=HolidayPayEligibility(
                min_employment_days=30,
                require_last_first_rule=False,
            ),
            premium_rate=Decimal("1.5"),
        )

        loader = MockConfigLoader({"NS": ns_config})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=loader,
        )

        employee = {
            "id": "emp-ns-001",
            "first_name": "Jane",
            "last_name": "Doe",
            "hourly_rate": 22.00,
            "hire_date": "2024-11-01",  # 60 days ago
        }

        holidays = [{"holiday_date": "2025-01-01", "name": "New Year's Day", "province": "NS"}]

        # Mock timesheet entries for 30-day lookback (employee worked 8h/day)
        timesheet_data = []
        for i in range(20):  # 20 work days in 30 calendar days
            work_date = date(2024, 12, 2) + timedelta(days=i + (i // 5) * 2)  # Skip weekends
            if work_date < date(2025, 1, 1):
                timesheet_data.append({
                    "work_date": work_date.isoformat(),
                    "regular_hours": "8.0",
                    "overtime_hours": "0",
                })

        mock_timesheet_result = MagicMock()
        mock_timesheet_result.data = timesheet_data

        def table_side_effect(table_name):
            mock_table = MagicMock()
            if table_name == "timesheet_entries":
                result = MagicMock()
                result.execute.return_value = mock_timesheet_result
                mock_table.select.return_value.eq.return_value.gte.return_value.lte.return_value = result
            return mock_table

        mock_supabase.table.side_effect = table_side_effect

        result = calculator.calculate_holiday_pay(
            employee=employee,
            province="NS",
            pay_frequency="bi_weekly",
            period_start=date(2024, 12, 29),
            period_end=date(2025, 1, 11),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("1760"),
            current_run_id="run-001",
        )

        # NS: 30-day average formula: (20 days × 8h × $22) / 20 days = $176/day
        assert result.regular_holiday_pay == Decimal("176")
        assert result.premium_holiday_pay == Decimal("0")

    def test_ns_new_hire_ineligible(self, mock_supabase):
        """Test NS employee with <30 days employment is ineligible."""
        ns_config = HolidayPayConfig(
            province_code="NS",
            formula_type="30_day_average",
            formula_params=HolidayPayFormulaParams(
                lookback_days=30,
                method="total_wages_div_days",
                default_daily_hours=Decimal("8"),
                new_employee_fallback="ineligible",
            ),
            eligibility=HolidayPayEligibility(
                min_employment_days=30,
                require_last_first_rule=False,
            ),
            premium_rate=Decimal("1.5"),
        )

        loader = MockConfigLoader({"NS": ns_config})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=loader,
        )

        # Hired only 20 days ago
        hire_date = (date.today() - timedelta(days=20)).isoformat()
        employee = {
            "id": "emp-ns-new",
            "hourly_rate": 20.00,
            "hire_date": hire_date,
        }

        holidays = [{"holiday_date": date.today().isoformat(), "name": "Test Holiday", "province": "NS"}]

        result = calculator.calculate_holiday_pay(
            employee=employee,
            province="NS",
            pay_frequency="bi_weekly",
            period_start=date.today() - timedelta(days=7),
            period_end=date.today() + timedelta(days=7),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("1600"),
            current_run_id="run-001",
        )

        # Should be ineligible due to <30 days employment
        assert result.regular_holiday_pay == Decimal("0")
        assert result.calculation_details["holidays"][0]["eligible"] is False

    def test_ns_premium_pay(self, mock_supabase):
        """Test NS premium pay for working on holiday."""
        ns_config = HolidayPayConfig(
            province_code="NS",
            formula_type="30_day_average",
            formula_params=HolidayPayFormulaParams(
                lookback_days=30,
                method="total_wages_div_days",
                default_daily_hours=Decimal("8"),
                new_employee_fallback="ineligible",
            ),
            eligibility=HolidayPayEligibility(
                min_employment_days=30,
                require_last_first_rule=False,
            ),
            premium_rate=Decimal("1.5"),
        )

        loader = MockConfigLoader({"NS": ns_config})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=loader,
        )

        employee = {
            "id": "emp-ns-premium",
            "hourly_rate": 20.00,
            "hire_date": "2024-11-01",
        }

        holidays = [{"holiday_date": "2025-01-01", "name": "New Year's Day", "province": "NS"}]
        work_entries = [{"holidayDate": "2025-01-01", "hoursWorked": 8}]

        # Mock timesheet entries for 30-day lookback (employee worked 8h/day)
        timesheet_data = []
        for i in range(20):  # 20 work days in 30 calendar days
            work_date = date(2024, 12, 2) + timedelta(days=i + (i // 5) * 2)  # Skip weekends
            if work_date < date(2025, 1, 1):
                timesheet_data.append({
                    "work_date": work_date.isoformat(),
                    "regular_hours": "8.0",
                    "overtime_hours": "0",
                })

        mock_timesheet_result = MagicMock()
        mock_timesheet_result.data = timesheet_data

        def table_side_effect(table_name):
            mock_table = MagicMock()
            if table_name == "timesheet_entries":
                result = MagicMock()
                result.execute.return_value = mock_timesheet_result
                mock_table.select.return_value.eq.return_value.gte.return_value.lte.return_value = result
            return mock_table

        mock_supabase.table.side_effect = table_side_effect

        result = calculator.calculate_holiday_pay(
            employee=employee,
            province="NS",
            pay_frequency="bi_weekly",
            period_start=date(2024, 12, 29),
            period_end=date(2025, 1, 11),
            holidays_in_period=holidays,
            holiday_work_entries=work_entries,
            current_period_gross=Decimal("1600"),
            current_run_id="run-001",
        )

        # Regular: 8h × $20 = $160
        # Premium: 8h × $20 × 1.5 = $240
        assert result.regular_holiday_pay == Decimal("160")
        assert result.premium_holiday_pay == Decimal("240")
        assert result.total_holiday_pay == Decimal("400")


class TestPrinceEdwardIsland:
    """Tests for Prince Edward Island holiday pay calculations.

    Prince Edward Island Rules:
    - Formula: 30_day_average (default_daily_hours × hourly_rate)
    - Min employment: 30 days
    - Days worked: Must earn wages on 15 of 30 days in period
    - Last/first rule: Yes
    - Premium rate: 1.5x
    """

    def test_pe_eligible_with_15_days_worked(self, mock_supabase):
        """Test PE employee with 15 days worked in 30-day period is eligible."""
        pe_config = HolidayPayConfig(
            province_code="PE",
            formula_type="30_day_average",
            formula_params=HolidayPayFormulaParams(
                lookback_days=30,
                method="total_wages_div_days",
                default_daily_hours=Decimal("8"),
                new_employee_fallback="ineligible",
            ),
            eligibility=HolidayPayEligibility(
                min_employment_days=30,
                min_days_worked_in_period=15,
                require_last_first_rule=True,
            ),
            premium_rate=Decimal("1.5"),
        )

        loader = MockConfigLoader({"PE": pe_config})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=loader,
        )

        employee = {
            "id": "emp-pe-001",
            "first_name": "Sarah",
            "last_name": "MacDonald",
            "hourly_rate": 21.50,
            "hire_date": "2024-11-01",
        }

        holidays = [{"holiday_date": "2025-01-01", "name": "New Year's Day", "province": "PE"}]

        # Mock timesheet with 15 days worked in 30-day period + last/first compliance
        timesheet_data = []
        # 15 days worked in 30-day period before holiday
        for i in range(15):
            work_date = date(2024, 12, 2) + timedelta(days=i * 2)
            timesheet_data.append({
                "work_date": work_date.isoformat(),
                "regular_hours": "8.0",
                "overtime_hours": "0",
            })
        # Last/first rule compliance
        timesheet_data.append({
            "work_date": "2024-12-31",  # Day before holiday
            "regular_hours": "8.0",
            "overtime_hours": "0",
        })
        timesheet_data.append({
            "work_date": "2025-01-02",  # Day after holiday
            "regular_hours": "8.0",
            "overtime_hours": "0",
        })

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
            province="PE",
            pay_frequency="bi_weekly",
            period_start=date(2024, 12, 29),
            period_end=date(2025, 1, 11),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("1720"),
            current_run_id="run-001",
        )

        # PE: 8h × $21.50 = $172
        assert result.regular_holiday_pay == Decimal("172")

    def test_pe_ineligible_less_than_15_days_worked(self, mock_supabase):
        """Test PE employee with <15 days worked is ineligible."""
        pe_config = HolidayPayConfig(
            province_code="PE",
            formula_type="30_day_average",
            formula_params=HolidayPayFormulaParams(
                lookback_days=30,
                method="total_wages_div_days",
                default_daily_hours=Decimal("8"),
                new_employee_fallback="ineligible",
            ),
            eligibility=HolidayPayEligibility(
                min_employment_days=30,
                min_days_worked_in_period=15,
                require_last_first_rule=True,
            ),
            premium_rate=Decimal("1.5"),
        )

        loader = MockConfigLoader({"PE": pe_config})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=loader,
        )

        employee = {
            "id": "emp-pe-010",
            "hourly_rate": 20.00,
            "hire_date": "2024-11-01",
        }

        holidays = [{"holiday_date": "2025-01-01", "name": "New Year's Day", "province": "PE"}]

        # Mock timesheet with only 10 days worked
        timesheet_data = []
        for i in range(10):
            work_date = date(2024, 12, 2) + timedelta(days=i * 2)
            timesheet_data.append({
                "work_date": work_date.isoformat(),
                "regular_hours": "8.0",
                "overtime_hours": "0",
            })

        mock_timesheet_result = MagicMock()
        mock_timesheet_result.data = timesheet_data

        def table_side_effect(table_name):
            mock_table = MagicMock()
            if table_name == "timesheet_entries":
                result = MagicMock()
                result.execute.return_value = mock_timesheet_result
                mock_table.select.return_value.eq.return_value.gte.return_value.lte.return_value = result
            return mock_table

        mock_supabase.table.side_effect = table_side_effect

        result = calculator.calculate_holiday_pay(
            employee=employee,
            province="PE",
            pay_frequency="bi_weekly",
            period_start=date(2024, 12, 29),
            period_end=date(2025, 1, 11),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("1600"),
            current_run_id="run-001",
        )

        # Should be ineligible due to <15 days worked
        assert result.regular_holiday_pay == Decimal("0")
        assert result.calculation_details["holidays"][0]["eligible"] is False


class TestNewBrunswick:
    """Tests for New Brunswick holiday pay calculations.

    New Brunswick Rules:
    - Formula: 30_day_average (default_daily_hours × hourly_rate)
    - Min employment: 90 days
    - Last/first rule: No
    - Premium rate: 1.5x
    """

    def test_nb_eligible_after_90_days(self, mock_supabase):
        """Test NB employee with 90+ days employment gets holiday pay."""
        nb_config = HolidayPayConfig(
            province_code="NB",
            formula_type="30_day_average",
            formula_params=HolidayPayFormulaParams(
                lookback_days=30,
                method="total_wages_div_days",
                default_daily_hours=Decimal("8"),
                new_employee_fallback="ineligible",
            ),
            eligibility=HolidayPayEligibility(
                min_employment_days=90,
                require_last_first_rule=False,
            ),
            premium_rate=Decimal("1.5"),
        )

        loader = MockConfigLoader({"NB": nb_config})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=loader,
        )

        employee = {
            "id": "emp-nb-001",
            "first_name": "Jean",
            "last_name": "LeBlanc",
            "hourly_rate": 23.00,
            "hire_date": "2024-08-01",  # >90 days ago
        }

        holidays = [{"holiday_date": "2025-01-01", "name": "New Year's Day", "province": "NB"}]

        # Mock timesheet entries for 30-day lookback (employee worked 8h/day)
        timesheet_data = []
        for i in range(20):  # 20 work days in 30 calendar days
            work_date = date(2024, 12, 2) + timedelta(days=i + (i // 5) * 2)  # Skip weekends
            if work_date < date(2025, 1, 1):
                timesheet_data.append({
                    "work_date": work_date.isoformat(),
                    "regular_hours": "8.0",
                    "overtime_hours": "0",
                })

        mock_timesheet_result = MagicMock()
        mock_timesheet_result.data = timesheet_data

        def table_side_effect(table_name):
            mock_table = MagicMock()
            if table_name == "timesheet_entries":
                result = MagicMock()
                result.execute.return_value = mock_timesheet_result
                mock_table.select.return_value.eq.return_value.gte.return_value.lte.return_value = result
            return mock_table

        mock_supabase.table.side_effect = table_side_effect

        result = calculator.calculate_holiday_pay(
            employee=employee,
            province="NB",
            pay_frequency="bi_weekly",
            period_start=date(2024, 12, 29),
            period_end=date(2025, 1, 11),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("1840"),
            current_run_id="run-001",
        )

        # NB: 8h × $23 = $184
        assert result.regular_holiday_pay == Decimal("184")

    def test_nb_ineligible_under_90_days(self, mock_supabase):
        """Test NB employee with <90 days employment is ineligible."""
        nb_config = HolidayPayConfig(
            province_code="NB",
            formula_type="30_day_average",
            formula_params=HolidayPayFormulaParams(
                lookback_days=30,
                method="total_wages_div_days",
                default_daily_hours=Decimal("8"),
                new_employee_fallback="ineligible",
            ),
            eligibility=HolidayPayEligibility(
                min_employment_days=90,
                require_last_first_rule=False,
            ),
            premium_rate=Decimal("1.5"),
        )

        loader = MockConfigLoader({"NB": nb_config})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=loader,
        )

        # Hired 60 days ago (<90 required)
        hire_date = (date.today() - timedelta(days=60)).isoformat()
        employee = {
            "id": "emp-nb-new",
            "hourly_rate": 20.00,
            "hire_date": hire_date,
        }

        holidays = [{"holiday_date": date.today().isoformat(), "name": "Test Holiday", "province": "NB"}]

        result = calculator.calculate_holiday_pay(
            employee=employee,
            province="NB",
            pay_frequency="bi_weekly",
            period_start=date.today() - timedelta(days=7),
            period_end=date.today() + timedelta(days=7),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("1600"),
            current_run_id="run-001",
        )

        # Should be ineligible due to <90 days employment
        assert result.regular_holiday_pay == Decimal("0")
        assert result.calculation_details["holidays"][0]["eligible"] is False

    def test_nb_premium_pay(self, mock_supabase):
        """Test NB premium pay calculation."""
        nb_config = HolidayPayConfig(
            province_code="NB",
            formula_type="30_day_average",
            formula_params=HolidayPayFormulaParams(
                lookback_days=30,
                method="total_wages_div_days",
                default_daily_hours=Decimal("8"),
                new_employee_fallback="ineligible",
            ),
            eligibility=HolidayPayEligibility(
                min_employment_days=90,
                require_last_first_rule=False,
            ),
            premium_rate=Decimal("1.5"),
        )

        loader = MockConfigLoader({"NB": nb_config})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=loader,
        )

        employee = {
            "id": "emp-nb-premium",
            "hourly_rate": 18.50,
            "hire_date": "2024-08-01",
        }

        holidays = [{"holiday_date": "2025-01-01", "name": "New Year's Day", "province": "NB"}]
        work_entries = [{"holidayDate": "2025-01-01", "hoursWorked": 6}]

        # Mock timesheet entries for 30-day lookback (employee worked 8h/day)
        timesheet_data = []
        for i in range(20):  # 20 work days in 30 calendar days
            work_date = date(2024, 12, 2) + timedelta(days=i + (i // 5) * 2)  # Skip weekends
            if work_date < date(2025, 1, 1):
                timesheet_data.append({
                    "work_date": work_date.isoformat(),
                    "regular_hours": "8.0",
                    "overtime_hours": "0",
                })

        mock_timesheet_result = MagicMock()
        mock_timesheet_result.data = timesheet_data

        def table_side_effect(table_name):
            mock_table = MagicMock()
            if table_name == "timesheet_entries":
                result = MagicMock()
                result.execute.return_value = mock_timesheet_result
                mock_table.select.return_value.eq.return_value.gte.return_value.lte.return_value = result
            return mock_table

        mock_supabase.table.side_effect = table_side_effect

        result = calculator.calculate_holiday_pay(
            employee=employee,
            province="NB",
            pay_frequency="bi_weekly",
            period_start=date(2024, 12, 29),
            period_end=date(2025, 1, 11),
            holidays_in_period=holidays,
            holiday_work_entries=work_entries,
            current_period_gross=Decimal("1480"),
            current_run_id="run-001",
        )

        # Regular: 8h × $18.50 = $148
        # Premium: 6h × $18.50 × 1.5 = $166.50
        assert result.regular_holiday_pay == Decimal("148")
        assert result.premium_holiday_pay == Decimal("166.50")


class TestNewfoundlandAndLabrador:
    """Tests for Newfoundland and Labrador holiday pay calculations.

    Newfoundland and Labrador Rules:
    - Formula: 30_day_average (default_daily_hours × hourly_rate)
    - Min employment: 30 days
    - Last/first rule: No
    - Premium rate: 1.5x
    """

    def test_nl_eligible_employee(self, mock_supabase):
        """Test NL employee with 30+ days employment gets holiday pay."""
        nl_config = HolidayPayConfig(
            province_code="NL",
            formula_type="30_day_average",
            formula_params=HolidayPayFormulaParams(
                lookback_days=30,
                method="total_wages_div_days",
                default_daily_hours=Decimal("8"),
                new_employee_fallback="ineligible",
            ),
            eligibility=HolidayPayEligibility(
                min_employment_days=30,
                require_last_first_rule=False,
            ),
            premium_rate=Decimal("1.5"),
        )

        loader = MockConfigLoader({"NL": nl_config})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=loader,
        )

        employee = {
            "id": "emp-nl-001",
            "first_name": "Patrick",
            "last_name": "O'Brien",
            "hourly_rate": 24.00,
            "hire_date": "2024-10-01",  # >30 days ago
        }

        holidays = [{"holiday_date": "2025-01-01", "name": "New Year's Day", "province": "NL"}]

        # Mock timesheet entries for 30-day lookback (employee worked 8h/day)
        timesheet_data = []
        for i in range(20):  # 20 work days in 30 calendar days
            work_date = date(2024, 12, 2) + timedelta(days=i + (i // 5) * 2)  # Skip weekends
            if work_date < date(2025, 1, 1):
                timesheet_data.append({
                    "work_date": work_date.isoformat(),
                    "regular_hours": "8.0",
                    "overtime_hours": "0",
                })

        mock_timesheet_result = MagicMock()
        mock_timesheet_result.data = timesheet_data

        def table_side_effect(table_name):
            mock_table = MagicMock()
            if table_name == "timesheet_entries":
                result = MagicMock()
                result.execute.return_value = mock_timesheet_result
                mock_table.select.return_value.eq.return_value.gte.return_value.lte.return_value = result
            return mock_table

        mock_supabase.table.side_effect = table_side_effect

        result = calculator.calculate_holiday_pay(
            employee=employee,
            province="NL",
            pay_frequency="weekly",
            period_start=date(2024, 12, 30),
            period_end=date(2025, 1, 5),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("1920"),
            current_run_id="run-001",
        )

        # NL: 8h × $24 = $192
        assert result.regular_holiday_pay == Decimal("192")

    def test_nl_partial_shift_gets_regular_wages_plus_holiday_pay(self, mock_supabase):
        """Test NL partial shift: regular wages (1x) + full day's holiday pay.

        Per NL Labour Standards Act s.17(2):
        If employee works fewer hours than normal, they receive:
        - Normal wages for hours worked (NOT 2x)
        - PLUS full day's holiday pay
        """
        nl_config = HolidayPayConfig(
            province_code="NL",
            formula_type="30_day_average",
            formula_params=HolidayPayFormulaParams(
                lookback_days=30,
                method="total_wages_div_days",
                default_daily_hours=Decimal("8"),
                new_employee_fallback="ineligible",
            ),
            eligibility=HolidayPayEligibility(
                min_employment_days=30,
                require_last_first_rule=False,
            ),
            premium_rate=Decimal("2.0"),  # NL uses 2.0x for full shifts
        )

        loader = MockConfigLoader({"NL": nl_config})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=loader,
        )

        employee = {
            "id": "emp-nl-premium",
            "hourly_rate": 22.00,
            "hire_date": "2024-10-01",
        }

        holidays = [{"holiday_date": "2025-01-01", "name": "New Year's Day", "province": "NL"}]
        work_entries = [{"holidayDate": "2025-01-01", "hoursWorked": 7.5}]  # Partial shift

        # Mock timesheet entries for 30-day lookback (employee worked 8h/day)
        timesheet_data = []
        for i in range(20):  # 20 work days in 30 calendar days
            work_date = date(2024, 12, 2) + timedelta(days=i + (i // 5) * 2)  # Skip weekends
            if work_date < date(2025, 1, 1):
                timesheet_data.append({
                    "work_date": work_date.isoformat(),
                    "regular_hours": "8.0",
                    "overtime_hours": "0",
                })

        mock_timesheet_result = MagicMock()
        mock_timesheet_result.data = timesheet_data

        def table_side_effect(table_name):
            mock_table = MagicMock()
            if table_name == "timesheet_entries":
                result = MagicMock()
                result.execute.return_value = mock_timesheet_result
                mock_table.select.return_value.eq.return_value.gte.return_value.lte.return_value = result
            return mock_table

        mock_supabase.table.side_effect = table_side_effect

        result = calculator.calculate_holiday_pay(
            employee=employee,
            province="NL",
            pay_frequency="weekly",
            period_start=date(2024, 12, 30),
            period_end=date(2025, 1, 5),
            holidays_in_period=holidays,
            holiday_work_entries=work_entries,
            current_period_gross=Decimal("1760"),
            current_run_id="run-001",
        )

        # NL s.17(2) partial shift rule:
        # Regular: full day's holiday pay = 8h × $22 = $176
        # Premium: regular wages (1.0x, not 2x) = 7.5h × $22 × 1.0 = $165
        assert result.regular_holiday_pay == Decimal("176")
        assert result.premium_holiday_pay == Decimal("165")

    def test_nl_full_shift_gets_double_wages_only(self, mock_supabase):
        """Test NL full shift: 2x wages ONLY, no regular holiday pay.

        Per NL Labour Standards Act s.17(a):
        When employee works full shift on holiday, they receive
        "twice the wages properly earned" - not regular pay + 2x.
        """
        nl_config = HolidayPayConfig(
            province_code="NL",
            formula_type="30_day_average",
            formula_params=HolidayPayFormulaParams(
                lookback_days=30,
                method="total_wages_div_days",
                default_daily_hours=Decimal("8"),
                new_employee_fallback="ineligible",
            ),
            eligibility=HolidayPayEligibility(
                min_employment_days=30,
                require_last_first_rule=False,
            ),
            premium_rate=Decimal("2.0"),
        )

        loader = MockConfigLoader({"NL": nl_config})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=loader,
        )

        employee = {
            "id": "emp-nl-full",
            "hourly_rate": 22.00,
            "hire_date": "2024-10-01",
        }

        holidays = [{"holiday_date": "2025-01-01", "name": "New Year's Day", "province": "NL"}]
        work_entries = [{"holidayDate": "2025-01-01", "hoursWorked": 8.0}]  # Full shift

        # Mock timesheet entries for 30-day lookback
        timesheet_data = []
        for i in range(20):
            work_date = date(2024, 12, 2) + timedelta(days=i + (i // 5) * 2)
            if work_date < date(2025, 1, 1):
                timesheet_data.append({
                    "work_date": work_date.isoformat(),
                    "regular_hours": "8.0",
                    "overtime_hours": "0",
                })

        mock_timesheet_result = MagicMock()
        mock_timesheet_result.data = timesheet_data

        def table_side_effect(table_name):
            mock_table = MagicMock()
            if table_name == "timesheet_entries":
                result = MagicMock()
                result.execute.return_value = mock_timesheet_result
                mock_table.select.return_value.eq.return_value.gte.return_value.lte.return_value = result
            return mock_table

        mock_supabase.table.side_effect = table_side_effect

        result = calculator.calculate_holiday_pay(
            employee=employee,
            province="NL",
            pay_frequency="weekly",
            period_start=date(2024, 12, 30),
            period_end=date(2025, 1, 5),
            holidays_in_period=holidays,
            holiday_work_entries=work_entries,
            current_period_gross=Decimal("1760"),
            current_run_id="run-001",
        )

        # NL s.17(a) full shift rule:
        # Regular: $0 (skipped - employee gets 2x wages only)
        # Premium: 2x wages = 8h × $22 × 2.0 = $352
        assert result.regular_holiday_pay == Decimal("0")
        assert result.premium_holiday_pay == Decimal("352")
