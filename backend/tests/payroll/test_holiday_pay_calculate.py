"""
Tests for Main Holiday Pay Calculation.

Tests:
- BC hourly single/multiple holidays
- BC salaried holiday pay
- Ontario new hire eligibility
- No holidays in period
- Calculation details
"""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

from app.models.holiday_pay_config import HolidayPayConfig, HolidayPayEligibility
from app.services.payroll_run.holiday_pay_calculator import HolidayPayCalculator
from tests.payroll.conftest import MockConfigLoader, make_on_config


class TestCalculateHolidayPay:
    """Tests for the main calculate_holiday_pay method."""

    def test_bc_hourly_single_holiday_not_worked(self, holiday_calculator, hourly_employee):
        """BC hourly employee with one holiday, not worked."""
        holidays = [{"holiday_date": "2025-07-01", "name": "Canada Day", "province": "BC"}]

        result = holiday_calculator.calculate_holiday_pay(
            employee=hourly_employee,
            province="BC",
            pay_frequency="bi_weekly",
            period_start=date(2025, 6, 28),
            period_end=date(2025, 7, 11),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("2000"),
            current_run_id="run-001",
        )

        # Regular: 8h × $25 = $200
        # Premium: $0 (not worked)
        assert result.regular_holiday_pay == Decimal("200")
        assert result.premium_holiday_pay == Decimal("0")
        assert result.total_holiday_pay == Decimal("200")

    def test_bc_hourly_single_holiday_worked(self, holiday_calculator, hourly_employee):
        """BC hourly employee with one holiday, worked 8 hours."""
        holidays = [{"holiday_date": "2025-07-01", "name": "Canada Day", "province": "BC"}]
        work_entries = [{"holidayDate": "2025-07-01", "hoursWorked": 8}]

        result = holiday_calculator.calculate_holiday_pay(
            employee=hourly_employee,
            province="BC",
            pay_frequency="bi_weekly",
            period_start=date(2025, 6, 28),
            period_end=date(2025, 7, 11),
            holidays_in_period=holidays,
            holiday_work_entries=work_entries,
            current_period_gross=Decimal("2000"),
            current_run_id="run-001",
        )

        # Regular: 8h × $25 = $200
        # Premium: 8h × $25 × 1.5 = $300
        assert result.regular_holiday_pay == Decimal("200")
        assert result.premium_holiday_pay == Decimal("300")
        assert result.total_holiday_pay == Decimal("500")

    def test_salaried_holiday_not_worked(self, holiday_calculator, salaried_employee):
        """Salaried employee: skip Regular, $0 Premium when not worked."""
        holidays = [{"holiday_date": "2025-07-01", "name": "Canada Day", "province": "BC"}]

        result = holiday_calculator.calculate_holiday_pay(
            employee=salaried_employee,
            province="BC",
            pay_frequency="bi_weekly",
            period_start=date(2025, 6, 28),
            period_end=date(2025, 7, 11),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("2307.69"),
            current_run_id="run-001",
        )

        # Regular: $0 (salaried - already included)
        # Premium: $0 (not worked)
        assert result.regular_holiday_pay == Decimal("0")
        assert result.premium_holiday_pay == Decimal("0")
        assert result.total_holiday_pay == Decimal("0")

    def test_salaried_holiday_worked(self, holiday_calculator, salaried_employee):
        """Salaried employee working on holiday gets Premium pay only."""
        holidays = [{"holiday_date": "2025-07-01", "name": "Canada Day", "province": "BC"}]
        work_entries = [{"holidayDate": "2025-07-01", "hoursWorked": 8}]

        result = holiday_calculator.calculate_holiday_pay(
            employee=salaried_employee,
            province="BC",
            pay_frequency="bi_weekly",
            period_start=date(2025, 6, 28),
            period_end=date(2025, 7, 11),
            holidays_in_period=holidays,
            holiday_work_entries=work_entries,
            current_period_gross=Decimal("2307.69"),
            current_run_id="run-001",
        )

        # Regular: $0 (salaried)
        # Premium: 8h × ($60000/2080) × 1.5
        hourly_rate = Decimal("60000") / Decimal("2080")
        expected_premium = Decimal("8") * hourly_rate * Decimal("1.5")

        assert result.regular_holiday_pay == Decimal("0")
        assert result.premium_holiday_pay == expected_premium
        assert result.total_holiday_pay == expected_premium

    def test_multiple_holidays_in_period(self, holiday_calculator, hourly_employee):
        """Multiple holidays in the same pay period."""
        holidays = [
            {"holiday_date": "2025-12-25", "name": "Christmas Day", "province": "BC"},
            {"holiday_date": "2025-12-26", "name": "Boxing Day", "province": "BC"},
        ]
        work_entries = [{"holidayDate": "2025-12-25", "hoursWorked": 4}]

        result = holiday_calculator.calculate_holiday_pay(
            employee=hourly_employee,
            province="BC",
            pay_frequency="bi_weekly",
            period_start=date(2025, 12, 20),
            period_end=date(2026, 1, 2),
            holidays_in_period=holidays,
            holiday_work_entries=work_entries,
            current_period_gross=Decimal("2000"),
            current_run_id="run-001",
        )

        # Regular: 8h × $25 × 2 holidays = $400
        # Premium: 4h × $25 × 1.5 = $150 (only Christmas worked)
        assert result.regular_holiday_pay == Decimal("400")
        assert result.premium_holiday_pay == Decimal("150")
        assert result.total_holiday_pay == Decimal("550")

    def test_bc_new_hire_ineligible(self, holiday_calculator, new_hire_employee):
        """BC: New hire <30 days gets regular rate only for hours worked on holiday.

        Per BC ESA, ineligible employees working on a statutory holiday receive
        regular wages (1.0x) for their hours, not premium pay (1.5x).
        """
        holiday_date = date.today()
        holidays = [{"holiday_date": holiday_date.isoformat(), "name": "Test Holiday", "province": "BC"}]
        work_entries = [{"holidayDate": holiday_date.isoformat(), "hoursWorked": 8}]

        result = holiday_calculator.calculate_holiday_pay(
            employee=new_hire_employee,
            province="BC",
            pay_frequency="bi_weekly",
            period_start=holiday_date - timedelta(days=7),
            period_end=holiday_date + timedelta(days=7),
            holidays_in_period=holidays,
            holiday_work_entries=work_entries,
            current_period_gross=Decimal("1600"),
            current_run_id="run-001",
        )

        # Regular: $0 (not eligible - <30 days employed in BC)
        # Premium: 8h × $20 × 1.0 = $160 (regular rate only, not 1.5x)
        assert result.regular_holiday_pay == Decimal("0")
        assert result.premium_holiday_pay == Decimal("160")
        assert result.total_holiday_pay == Decimal("160")

    def test_ontario_new_hire_eligible_with_last_first_rule(self, mock_supabase):
        """Ontario: New hire with last/first rule - eligible when work before/after holiday."""
        # Create calculator with Ontario config
        on_config_loader = MockConfigLoader({"ON": make_on_config()})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=on_config_loader,
        )

        recent_date = (date.today() - timedelta(days=10)).isoformat()
        new_hire = {
            "id": "emp-on-new",
            "first_name": "New",
            "last_name": "Ontario",
            "hourly_rate": 20.00,
            "hire_date": recent_date,
        }

        holiday_date = date.today()
        holidays = [{"holiday_date": holiday_date.isoformat(), "name": "Test Holiday", "province": "ON"}]

        # Create different mock chain for different table queries
        # Historical payroll data (paystub_earnings table)
        historical_mock = MagicMock()
        historical_mock.data = []

        # Timesheet entries for last/first rule - COMPLIES (has work before AND after)
        timesheet_mock = MagicMock()
        timesheet_mock.data = [
            {"work_date": (holiday_date - timedelta(days=2)).isoformat(), "regular_hours": 8, "overtime_hours": 0},
            {"work_date": (holiday_date + timedelta(days=2)).isoformat(), "regular_hours": 8, "overtime_hours": 0},
        ]

        def table_side_effect(table_name):
            mock_table = MagicMock()
            if table_name == "paystub_earnings":
                result = MagicMock()
                result.execute.return_value = historical_mock
                mock_table.select.return_value.eq.return_value.neq.return_value.gte.return_value.lt.return_value.in_.return_value = result
            elif table_name == "timesheet_entries":
                result = MagicMock()
                result.execute.return_value = timesheet_mock
                # Support various query chains for timesheet_entries
                # Chain 1: select().eq().gte().lte() (for _get_timesheet_entries_for_eligibility)
                mock_table.select.return_value.eq.return_value.gte.return_value.lte.return_value = result
                # Chain 2: select().eq().gte().lte().order().limit() (for _find_nearest_work_day)
                order_result = MagicMock()
                order_result.limit.return_value.execute.return_value = timesheet_mock
                mock_table.select.return_value.eq.return_value.gte.return_value.lte.return_value.order.return_value = order_result
                # Chain 3: select().eq().eq().execute() (for checking specific work date)
                # This needs a separate eq chain that also leads to execute
                mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = timesheet_mock
            return mock_table

        mock_supabase.table.side_effect = table_side_effect

        result = calculator.calculate_holiday_pay(
            employee=new_hire,
            province="ON",
            pay_frequency="bi_weekly",
            period_start=holiday_date - timedelta(days=7),
            period_end=holiday_date + timedelta(days=7),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("1600"),
            current_run_id="run-001",
        )

        # Ontario: New hire IS eligible (complies with last/first rule)
        # Regular: 8h × $20 = $160 (fallback to 30-day avg since no history)
        assert result.regular_holiday_pay == Decimal("160")
        assert result.premium_holiday_pay == Decimal("0")

    def test_ontario_new_hire_ineligible_no_last_first_rule_work(self, mock_supabase):
        """Ontario: New hire ineligible when no work before/after holiday (last/first rule)."""
        # Create calculator with Ontario config
        on_config_loader = MockConfigLoader({"ON": make_on_config()})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=on_config_loader,
        )

        recent_date = (date.today() - timedelta(days=10)).isoformat()
        new_hire = {
            "id": "emp-on-new-no-work",
            "first_name": "No",
            "last_name": "Work",
            "hourly_rate": 20.00,
            "hire_date": recent_date,
        }

        holiday_date = date.today()
        holidays = [{"holiday_date": holiday_date.isoformat(), "name": "Test Holiday", "province": "ON"}]

        # Create different mock chain for different table queries
        # Historical payroll data (paystub_earnings table)
        historical_mock = MagicMock()
        historical_mock.data = []

        # Timesheet entries for last/first rule - DOES NOT COMPLY (no work before or after)
        timesheet_mock = MagicMock()
        timesheet_mock.data = []

        def table_side_effect(table_name):
            mock_table = MagicMock()
            if table_name == "paystub_earnings":
                result = MagicMock()
                result.execute.return_value = historical_mock
                mock_table.select.return_value.eq.return_value.neq.return_value.gte.return_value.lt.return_value.in_.return_value = result
            elif table_name == "timesheet_entries":
                result = MagicMock()
                result.execute.return_value = timesheet_mock
                # Support various query chains for timesheet_entries
                # Chain 1: select().eq().gte().lte() (for _get_timesheet_entries_for_eligibility)
                mock_table.select.return_value.eq.return_value.gte.return_value.lte.return_value = result
                # Chain 2: select().eq().gte().lte().order().limit() (for _find_nearest_work_day)
                order_result = MagicMock()
                order_result.limit.return_value.execute.return_value = timesheet_mock
                mock_table.select.return_value.eq.return_value.gte.return_value.lte.return_value.order.return_value = order_result
                # Chain 3: select().eq().eq().execute() (for checking specific work date)
                # This needs a separate eq chain that also leads to execute
                mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = timesheet_mock
            return mock_table

        mock_supabase.table.side_effect = table_side_effect

        result = calculator.calculate_holiday_pay(
            employee=new_hire,
            province="ON",
            pay_frequency="bi_weekly",
            period_start=holiday_date - timedelta(days=7),
            period_end=holiday_date + timedelta(days=7),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("1600"),
            current_run_id="run-001",
        )

        # Ontario: New hire NOT eligible (fails last/first rule - no work before/after)
        assert result.regular_holiday_pay == Decimal("0")
        assert result.premium_holiday_pay == Decimal("0")
        # Verify ineligibility reason
        assert result.calculation_details["holidays"][0]["eligible"] is False
        assert result.calculation_details["holidays"][0]["ineligibility_reason"] == "did not work on last scheduled day before/first scheduled day after holiday"

    def test_no_holidays_in_period(self, holiday_calculator, hourly_employee):
        """No holidays in the pay period."""
        result = holiday_calculator.calculate_holiday_pay(
            employee=hourly_employee,
            province="BC",
            pay_frequency="bi_weekly",
            period_start=date(2025, 3, 1),
            period_end=date(2025, 3, 14),
            holidays_in_period=[],
            holiday_work_entries=[],
            current_period_gross=Decimal("2000"),
            current_run_id="run-001",
        )

        assert result.regular_holiday_pay == Decimal("0")
        assert result.premium_holiday_pay == Decimal("0")
        assert result.total_holiday_pay == Decimal("0")


class TestCalculationDetails:
    """Tests for calculation details in the result."""

    def test_invalid_holiday_date_format_skipped(self, holiday_calculator, hourly_employee):
        """Test that holidays with invalid date format are skipped (lines 175-177)."""
        holidays = [
            {"holiday_date": "invalid-date", "name": "Invalid Holiday", "province": "BC"},
            {"holiday_date": "2025-07-01", "name": "Canada Day", "province": "BC"},
        ]

        result = holiday_calculator.calculate_holiday_pay(
            employee=hourly_employee,
            province="BC",
            pay_frequency="bi_weekly",
            period_start=date(2025, 6, 28),
            period_end=date(2025, 7, 11),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("2000"),
            current_run_id="run-001",
        )

        # Should only calculate for valid holiday
        assert result.regular_holiday_pay == Decimal("200")
        assert result.total_holiday_pay == Decimal("200")

    def test_hr_exempt_employee_no_regular_pay(self, holiday_calculator, hourly_employee):
        """Test that HR-exempt employees skip Regular holiday pay (lines 191-194)."""
        holidays = [{"holiday_date": "2025-07-01", "name": "Canada Day", "province": "BC"}]

        result = holiday_calculator.calculate_holiday_pay(
            employee=hourly_employee,
            province="BC",
            pay_frequency="bi_weekly",
            period_start=date(2025, 6, 28),
            period_end=date(2025, 7, 11),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("2000"),
            current_run_id="run-001",
            holiday_pay_exempt=True,  # Pass as parameter
        )

        # No Regular pay when exempt
        assert result.regular_holiday_pay == Decimal("0")
        assert result.premium_holiday_pay == Decimal("0")

    def test_details_include_config_info(self, holiday_calculator, hourly_employee):
        """Details should include config information."""
        holidays = [{"holiday_date": "2025-07-01", "name": "Canada Day", "province": "BC"}]

        result = holiday_calculator.calculate_holiday_pay(
            employee=hourly_employee,
            province="BC",
            pay_frequency="bi_weekly",
            period_start=date(2025, 6, 28),
            period_end=date(2025, 7, 11),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("2000"),
            current_run_id="run-001",
        )

        details = result.calculation_details
        assert "config" in details
        assert details["config"]["formula_type"] == "30_day_average"
        assert details["config"]["min_employment_days"] == 30

    def test_details_include_holiday_info(self, holiday_calculator, hourly_employee):
        """Details should include information about each holiday."""
        holidays = [{"holiday_date": "2025-07-01", "name": "Canada Day", "province": "BC"}]
        work_entries = [{"holidayDate": "2025-07-01", "hoursWorked": 4}]

        result = holiday_calculator.calculate_holiday_pay(
            employee=hourly_employee,
            province="BC",
            pay_frequency="bi_weekly",
            period_start=date(2025, 6, 28),
            period_end=date(2025, 7, 11),
            holidays_in_period=holidays,
            holiday_work_entries=work_entries,
            current_period_gross=Decimal("2000"),
            current_run_id="run-001",
        )

        details = result.calculation_details
        assert details["holidays_count"] == 1
        assert details["is_hourly"] is True
        assert details["province"] == "BC"
        assert len(details["holidays"]) == 1
        assert details["holidays"][0]["name"] == "Canada Day"
        assert details["holidays"][0]["eligible"] is True
        assert len(details["work_entries"]) == 1


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_invalid_hire_date_format_treats_as_ineligible(self, holiday_calculator):
        """Test that invalid hire_date format is treated as ineligible."""
        employee = {
            "id": "emp-invalid-date",
            "first_name": "Invalid",
            "last_name": "Date",
            "hourly_rate": 25.00,
            "hire_date": "not-a-valid-date",  # Invalid format
        }
        holidays = [{"holiday_date": "2025-07-01", "name": "Canada Day", "province": "BC"}]

        result = holiday_calculator.calculate_holiday_pay(
            employee=employee,
            province="BC",
            pay_frequency="bi_weekly",
            period_start=date(2025, 6, 28),
            period_end=date(2025, 7, 11),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("2000"),
            current_run_id="run-001",
        )

        # Invalid hire_date is a data issue, should be ineligible
        assert result.regular_holiday_pay == Decimal("0")
        assert result.calculation_details["holidays"][0]["eligible"] is False
        assert result.calculation_details["holidays"][0]["ineligibility_reason"] == "invalid hire date"

    def test_missing_hire_date_treats_as_ineligible(self, holiday_calculator):
        """Test that missing hire_date is treated as ineligible."""
        employee = {
            "id": "emp-no-hire-date",
            "first_name": "No",
            "last_name": "HireDate",
            "hourly_rate": 25.00,
            "hire_date": None,  # Missing hire_date
        }
        holidays = [{"holiday_date": "2025-07-01", "name": "Canada Day", "province": "BC"}]

        result = holiday_calculator.calculate_holiday_pay(
            employee=employee,
            province="BC",
            pay_frequency="bi_weekly",
            period_start=date(2025, 6, 28),
            period_end=date(2025, 7, 11),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("2000"),
            current_run_id="run-001",
        )

        # Missing hire_date is a data issue, should be ineligible
        assert result.regular_holiday_pay == Decimal("0")
        assert result.calculation_details["holidays"][0]["eligible"] is False
        assert result.calculation_details["holidays"][0]["ineligibility_reason"] == "missing hire date"

    def test_current_period_daily_formula(self, mock_supabase):
        """Test current_period_daily formula type (line 391)."""
        from app.models.holiday_pay_config import HolidayPayFormulaParams

        # Create config with current_period_daily formula
        # Note: work_days_per_period is from WORK_DAYS_PER_PERIOD constant, not config
        config = HolidayPayConfig(
            province_code="TEST",
            formula_type="current_period_daily",
            formula_params=HolidayPayFormulaParams(),
            eligibility=HolidayPayEligibility(min_employment_days=0, require_last_first_rule=False),
            premium_rate=Decimal("1.5"),
        )
        loader = MockConfigLoader({"TEST": config})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=loader,
        )

        employee = {
            "id": "emp-current-period",
            "hourly_rate": 25.00,
            "hire_date": "2024-01-01",
        }
        holidays = [{"holiday_date": "2025-07-01", "name": "Canada Day", "province": "TEST"}]

        result = calculator.calculate_holiday_pay(
            employee=employee,
            province="TEST",
            pay_frequency="bi_weekly",  # Will use 10 days from WORK_DAYS_PER_PERIOD
            period_start=date(2025, 6, 28),
            period_end=date(2025, 7, 11),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("2000"),
            current_run_id="run-001",
        )

        # Daily pay = $2000 / 10 = $200
        assert result.regular_holiday_pay == Decimal("200")

    def test_current_period_daily_zero_work_days(self, mock_supabase):
        """Test current_period_daily with zero work days (line 462)."""
        from app.models.holiday_pay_config import HolidayPayFormulaParams

        # Create config with current_period_daily formula
        # When pay_frequency is not in WORK_DAYS_PER_PERIOD, it defaults to 10
        config = HolidayPayConfig(
            province_code="TEST",
            formula_type="current_period_daily",
            formula_params=HolidayPayFormulaParams(),
            eligibility=HolidayPayEligibility(min_employment_days=0, require_last_first_rule=False),
            premium_rate=Decimal("1.5"),
        )
        loader = MockConfigLoader({"TEST": config})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=loader,
        )

        employee = {
            "id": "emp-zero-days",
            "hourly_rate": 25.00,
            "hire_date": "2024-01-01",
        }
        holidays = [{"holiday_date": "2025-07-01", "name": "Canada Day", "province": "TEST"}]

        # Patch WORK_DAYS_PER_PERIOD to test zero work days
        from app.services.payroll_run.holiday_pay import formula_calculators
        original_dict = formula_calculators.WORK_DAYS_PER_PERIOD
        try:
            formula_calculators.WORK_DAYS_PER_PERIOD = {"bi_weekly": Decimal("0")}

            result = calculator.calculate_holiday_pay(
                employee=employee,
                province="TEST",
                pay_frequency="bi_weekly",
                period_start=date(2025, 6, 28),
                period_end=date(2025, 7, 11),
                holidays_in_period=holidays,
                holiday_work_entries=[],
                current_period_gross=Decimal("2000"),
                current_run_id="run-001",
            )

            # Should return 0 when work_days is 0
            assert result.regular_holiday_pay == Decimal("0")
        finally:
            formula_calculators.WORK_DAYS_PER_PERIOD = original_dict

    def test_four_week_average_ineligible_fallback(self, mock_supabase):
        """Test 4_week_average with ineligible fallback for new employees (lines 522-527)."""
        from app.models.holiday_pay_config import HolidayPayFormulaParams

        # Create ON config with ineligible fallback
        config = HolidayPayConfig(
            province_code="ON",
            formula_type="4_week_average",
            formula_params=HolidayPayFormulaParams(
                lookback_weeks=4,
                divisor=20,
                include_vacation_pay=True,
                new_employee_fallback="ineligible",  # Changed to ineligible
            ),
            eligibility=HolidayPayEligibility(min_employment_days=0, require_last_first_rule=False),
            premium_rate=Decimal("1.5"),
        )
        loader = MockConfigLoader({"ON": config})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=loader,
        )

        # Mock empty historical data
        mock_supabase.table.return_value.select.return_value.eq.return_value.neq.return_value.gte.return_value.lt.return_value.in_.return_value.execute.return_value.data = []

        employee = {
            "id": "emp-new-ineligible",
            "hourly_rate": 25.00,
            "hire_date": "2025-06-15",
        }
        holidays = [{"holiday_date": "2025-07-01", "name": "Canada Day", "province": "ON"}]

        result = calculator.calculate_holiday_pay(
            employee=employee,
            province="ON",
            pay_frequency="bi_weekly",
            period_start=date(2025, 6, 28),
            period_end=date(2025, 7, 11),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("2000"),
            current_run_id="run-001",
        )

        # Should return 0 for ineligible fallback
        assert result.regular_holiday_pay == Decimal("0")

    def test_four_week_average_without_vacation_pay(self, mock_supabase):
        """Test 4_week_average without vacation pay included (line 533)."""
        from app.models.holiday_pay_config import HolidayPayFormulaParams

        # Create ON config without vacation pay (but with overtime)
        config = HolidayPayConfig(
            province_code="ON",
            formula_type="4_week_average",
            formula_params=HolidayPayFormulaParams(
                lookback_weeks=4,
                divisor=20,
                include_vacation_pay=False,  # Exclude vacation pay
                include_overtime=True,  # Include overtime in wages
                new_employee_fallback="pro_rated",
            ),
            eligibility=HolidayPayEligibility(min_employment_days=0, require_last_first_rule=False),
            premium_rate=Decimal("1.5"),
        )
        loader = MockConfigLoader({"ON": config})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=loader,
        )

        # Mock historical data with vacation pay
        mock_supabase.table.return_value.select.return_value.eq.return_value.neq.return_value.gte.return_value.lt.return_value.in_.return_value.execute.return_value.data = [
            {"gross_regular": "1000.00", "gross_overtime": "200.00", "vacation_pay_paid": "100.00"},
            {"gross_regular": "1000.00", "gross_overtime": "0.00", "vacation_pay_paid": "100.00"},
        ]

        employee = {
            "id": "emp-with-history",
            "hourly_rate": 25.00,
            "hire_date": "2024-01-01",
        }
        holidays = [{"holiday_date": "2025-07-01", "name": "Canada Day", "province": "ON"}]

        result = calculator.calculate_holiday_pay(
            employee=employee,
            province="ON",
            pay_frequency="bi_weekly",
            period_start=date(2025, 6, 28),
            period_end=date(2025, 7, 11),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("2000"),
            current_run_id="run-001",
        )

        # Should only include wages, not vacation pay: ($2200) / 20 = $110
        assert result.regular_holiday_pay == Decimal("110")

    def test_four_week_daily_pro_rated_fallback(self, mock_supabase):
        """Test 4_week_daily with pro_rated fallback for new employees (lines 580-585)."""
        from app.models.holiday_pay_config import HolidayPayFormulaParams

        # Create AB config with pro_rated fallback
        config = HolidayPayConfig(
            province_code="AB",
            formula_type="4_week_average_daily",
            formula_params=HolidayPayFormulaParams(
                lookback_weeks=4,
                method="wages_div_days_worked",
                new_employee_fallback="pro_rated",
            ),
            eligibility=HolidayPayEligibility(min_employment_days=0, require_last_first_rule=False),
            premium_rate=Decimal("1.5"),
        )
        loader = MockConfigLoader({"AB": config})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=loader,
        )

        # Mock empty historical data
        mock_supabase.table.return_value.select.return_value.eq.return_value.neq.return_value.gte.return_value.lt.return_value.in_.return_value.execute.return_value.data = []

        employee = {
            "id": "emp-ab-new",
            "hourly_rate": 25.00,
            "hire_date": "2025-06-15",
        }
        holidays = [{"holiday_date": "2025-07-01", "name": "Canada Day", "province": "AB"}]

        result = calculator.calculate_holiday_pay(
            employee=employee,
            province="AB",
            pay_frequency="bi_weekly",
            period_start=date(2025, 6, 28),
            period_end=date(2025, 7, 11),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("2000"),
            current_run_id="run-001",
        )

        # Should use 30-day avg fallback: 8h × $25 = $200
        assert result.regular_holiday_pay == Decimal("200")

    def test_four_week_earnings_exception_handling(self, mock_supabase):
        """Test exception handling in _get_4_week_earnings (lines 673-675)."""
        from app.models.holiday_pay_config import HolidayPayFormulaParams

        config = HolidayPayConfig(
            province_code="ON",
            formula_type="4_week_average",
            formula_params=HolidayPayFormulaParams(
                lookback_weeks=4,
                divisor=20,
                include_vacation_pay=True,
                new_employee_fallback="pro_rated",
            ),
            eligibility=HolidayPayEligibility(min_employment_days=0, require_last_first_rule=False),
            premium_rate=Decimal("1.5"),
        )
        loader = MockConfigLoader({"ON": config})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=loader,
        )

        # Mock exception from Supabase
        mock_supabase.table.return_value.select.return_value.eq.return_value.neq.return_value.gte.return_value.lt.return_value.in_.return_value.execute.side_effect = Exception("DB error")

        employee = {
            "id": "emp-db-error",
            "hourly_rate": 25.00,
            "hire_date": "2024-01-01",
        }
        holidays = [{"holiday_date": "2025-07-01", "name": "Canada Day", "province": "ON"}]

        # Should handle exception gracefully and use fallback
        result = calculator.calculate_holiday_pay(
            employee=employee,
            province="ON",
            pay_frequency="bi_weekly",
            period_start=date(2025, 6, 28),
            period_end=date(2025, 7, 11),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("2000"),
            current_run_id="run-001",
        )

        # Should use pro_rated fallback when exception occurs
        assert result.regular_holiday_pay == Decimal("200")

    def test_twenty_eight_day_earnings_exception_handling(self, mock_supabase):
        """Test exception handling in _get_28_day_earnings (lines 737-739)."""
        from app.models.holiday_pay_config import HolidayPayFormulaParams

        # Create SK config with ineligible fallback
        config = HolidayPayConfig(
            province_code="SK",
            formula_type="5_percent_28_days",
            formula_params=HolidayPayFormulaParams(
                lookback_days=28,
                percentage=Decimal("0.05"),
                include_vacation_pay=True,
                include_previous_holiday_pay=True,
                new_employee_fallback="ineligible",
            ),
            eligibility=HolidayPayEligibility(min_employment_days=0, require_last_first_rule=False),
            premium_rate=Decimal("1.5"),
        )
        loader = MockConfigLoader({"SK": config})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=loader,
        )

        # Mock exception from Supabase
        mock_supabase.table.return_value.select.return_value.eq.return_value.neq.return_value.gte.return_value.lt.return_value.in_.return_value.execute.side_effect = Exception("DB error")

        employee = {
            "id": "emp-sk-db-error",
            "hourly_rate": 25.00,
            "hire_date": "2024-01-01",
        }
        holidays = [{"holiday_date": "2025-07-01", "name": "Canada Day", "province": "SK"}]

        result = calculator.calculate_holiday_pay(
            employee=employee,
            province="SK",
            pay_frequency="bi_weekly",
            period_start=date(2025, 6, 28),
            period_end=date(2025, 7, 11),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("2000"),
            current_run_id="run-001",
        )

        # Should return 0 for ineligible fallback when exception occurs
        assert result.regular_holiday_pay == Decimal("0")

    def test_five_percent_ineligible_fallback(self, mock_supabase):
        """Test 5_percent_28_days with ineligible fallback (lines 803-808)."""
        from app.models.holiday_pay_config import HolidayPayFormulaParams

        # Create SK config with ineligible fallback
        config = HolidayPayConfig(
            province_code="SK",
            formula_type="5_percent_28_days",
            formula_params=HolidayPayFormulaParams(
                lookback_days=28,
                percentage=Decimal("0.05"),
                include_vacation_pay=True,
                include_previous_holiday_pay=True,
                new_employee_fallback="ineligible",
            ),
            eligibility=HolidayPayEligibility(min_employment_days=0, require_last_first_rule=False),
            premium_rate=Decimal("1.5"),
        )
        loader = MockConfigLoader({"SK": config})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=loader,
        )

        # Mock empty historical data
        mock_supabase.table.return_value.select.return_value.eq.return_value.neq.return_value.gte.return_value.lt.return_value.in_.return_value.execute.return_value.data = []

        employee = {
            "id": "emp-sk-new-ineligible",
            "hourly_rate": 25.00,
            "hire_date": "2025-06-15",
        }
        holidays = [{"holiday_date": "2025-07-01", "name": "Canada Day", "province": "SK"}]

        result = calculator.calculate_holiday_pay(
            employee=employee,
            province="SK",
            pay_frequency="bi_weekly",
            period_start=date(2025, 6, 28),
            period_end=date(2025, 7, 11),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("2000"),
            current_run_id="run-001",
        )

        # Should return 0 for ineligible fallback
        assert result.regular_holiday_pay == Decimal("0")

    def test_calculator_without_config_loader(self, mock_supabase):
        """Test calculator without config loader (line 92)."""
        from tests.payroll.conftest import setup_bc_timesheet_mock
        setup_bc_timesheet_mock(mock_supabase)

        # Create calculator without config_loader
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=None,  # No config loader
        )

        employee = {
            "id": "emp-no-loader",
            "hourly_rate": 25.00,
            "hire_date": "2024-01-01",
        }
        holidays = [{"holiday_date": "2025-07-01", "name": "Canada Day", "province": "BC"}]

        result = calculator.calculate_holiday_pay(
            employee=employee,
            province="BC",
            pay_frequency="bi_weekly",
            period_start=date(2025, 6, 28),
            period_end=date(2025, 7, 11),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("2000"),
            current_run_id="run-001",
        )

        # Should use default BC config
        assert result.regular_holiday_pay == Decimal("200")

    def test_four_week_daily_with_historical_data(self, mock_supabase):
        """Test 4_week_daily with timesheet data (lines 588-608).

        After fix: Alberta uses timesheet_entries for both wages AND days worked.
        - 20 days worked × 4.4 hours = 88 hours
        - 88 hours × $25/hour = $2,200 wages
        - $2,200 ÷ 20 days = $110/day
        """
        from app.models.holiday_pay_config import HolidayPayFormulaParams

        # Create AB config with ineligible fallback
        config = HolidayPayConfig(
            province_code="AB",
            formula_type="4_week_average_daily",
            formula_params=HolidayPayFormulaParams(
                lookback_weeks=4,
                method="wages_div_days_worked",
                new_employee_fallback="ineligible",
            ),
            eligibility=HolidayPayEligibility(min_employment_days=0, require_last_first_rule=False),
            premium_rate=Decimal("1.5"),
        )
        loader = MockConfigLoader({"AB": config})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=loader,
        )

        # Mock timesheet_entries for 4-week period (used for both wages AND days)
        # 20 days × 4.4 hours = 88 hours × $25/hour = $2,200
        timesheet_data = []
        for i in range(20):
            timesheet_data.append({
                "work_date": (date(2025, 6, 3) + timedelta(days=i)).isoformat(),
                "regular_hours": "4.4",
                "overtime_hours": "0",
            })

        # Setup table side effect to return timesheet data
        def table_side_effect(table_name):
            mock_table = MagicMock()
            if table_name == "timesheet_entries":
                mock_result = MagicMock()
                mock_result.data = timesheet_data
                mock_table.select.return_value.eq.return_value.gte.return_value.lte.return_value.execute.return_value = mock_result
            return mock_table

        mock_supabase.table.side_effect = table_side_effect

        employee = {
            "id": "emp-ab-with-history",
            "hourly_rate": 25.00,
            "hire_date": "2024-01-01",
        }
        holidays = [{"holiday_date": "2025-07-01", "name": "Canada Day", "province": "AB"}]

        result = calculator.calculate_holiday_pay(
            employee=employee,
            province="AB",
            pay_frequency="bi_weekly",
            period_start=date(2025, 6, 28),
            period_end=date(2025, 7, 11),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("2000"),
            current_run_id="run-001",
        )

        # Should calculate from timesheet data: $2,200 / 20 days = $110
        assert result.regular_holiday_pay == Decimal("110")

    def test_five_percent_with_historical_data(self, mock_supabase):
        """Test 5_percent_28_days with historical data (lines 810-824)."""
        from app.models.holiday_pay_config import HolidayPayFormulaParams

        # Create SK config with pro_rated fallback
        config = HolidayPayConfig(
            province_code="SK",
            formula_type="5_percent_28_days",
            formula_params=HolidayPayFormulaParams(
                lookback_days=28,
                percentage=Decimal("0.05"),
                include_vacation_pay=True,
                include_previous_holiday_pay=True,
                new_employee_fallback="pro_rated",
            ),
            eligibility=HolidayPayEligibility(min_employment_days=0, require_last_first_rule=False),
            premium_rate=Decimal("1.5"),
        )
        loader = MockConfigLoader({"SK": config})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=loader,
        )

        # Mock historical data
        mock_supabase.table.return_value.select.return_value.eq.return_value.neq.return_value.gte.return_value.lt.return_value.in_.return_value.execute.return_value.data = [
            {"gross_regular": "1000.00", "vacation_pay_paid": "100.00", "holiday_pay": "50.00"},
            {"gross_regular": "1000.00", "vacation_pay_paid": "100.00", "holiday_pay": "50.00"},
        ]

        employee = {
            "id": "emp-sk-with-history",
            "hourly_rate": 25.00,
            "hire_date": "2024-01-01",
        }
        holidays = [{"holiday_date": "2025-07-01", "name": "Canada Day", "province": "SK"}]

        result = calculator.calculate_holiday_pay(
            employee=employee,
            province="SK",
            pay_frequency="bi_weekly",
            period_start=date(2025, 6, 28),
            period_end=date(2025, 7, 11),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("2000"),
            current_run_id="run-001",
        )

        # Base = $2000 (wages) + $200 (vacation) + $100 (holiday) = $2300
        # Holiday pay = $2300 × 5% = $115
        assert result.regular_holiday_pay == Decimal("115")

    def test_four_week_average_with_vacation_pay(self, mock_supabase):
        """Test 4_week_average with vacation pay included (line 531)."""
        from app.models.holiday_pay_config import HolidayPayFormulaParams

        # Create ON config with vacation pay and overtime
        config = HolidayPayConfig(
            province_code="ON",
            formula_type="4_week_average",
            formula_params=HolidayPayFormulaParams(
                lookback_weeks=4,
                divisor=20,
                include_vacation_pay=True,  # Include vacation pay
                include_overtime=True,  # Include overtime in wages
                new_employee_fallback="pro_rated",
            ),
            eligibility=HolidayPayEligibility(min_employment_days=0, require_last_first_rule=False),
            premium_rate=Decimal("1.5"),
        )
        loader = MockConfigLoader({"ON": config})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=loader,
        )

        # Mock historical data with vacation pay
        mock_supabase.table.return_value.select.return_value.eq.return_value.neq.return_value.gte.return_value.lt.return_value.in_.return_value.execute.return_value.data = [
            {"gross_regular": "1000.00", "gross_overtime": "200.00", "vacation_pay_paid": "100.00"},
            {"gross_regular": "1000.00", "gross_overtime": "0.00", "vacation_pay_paid": "100.00"},
        ]

        employee = {
            "id": "emp-with-vacation",
            "hourly_rate": 25.00,
            "hire_date": "2024-01-01",
        }
        holidays = [{"holiday_date": "2025-07-01", "name": "Canada Day", "province": "ON"}]

        result = calculator.calculate_holiday_pay(
            employee=employee,
            province="ON",
            pay_frequency="bi_weekly",
            period_start=date(2025, 6, 28),
            period_end=date(2025, 7, 11),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("2000"),
            current_run_id="run-001",
        )

        # Should include wages + vacation pay: ($2200 + $200) / 20 = $120
        assert result.regular_holiday_pay == Decimal("120")

    def test_four_week_daily_ineligible_fallback_with_zero_wages(self, mock_supabase):
        """Test 4_week_daily ineligible fallback (lines 588-593)."""
        from app.models.holiday_pay_config import HolidayPayFormulaParams

        # Create AB config with ineligible fallback
        config = HolidayPayConfig(
            province_code="AB",
            formula_type="4_week_average_daily",
            formula_params=HolidayPayFormulaParams(
                lookback_weeks=4,
                method="wages_div_days_worked",
                new_employee_fallback="ineligible",
            ),
            eligibility=HolidayPayEligibility(min_employment_days=0, require_last_first_rule=False),
            premium_rate=Decimal("1.5"),
        )
        loader = MockConfigLoader({"AB": config})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=loader,
        )

        # Mock empty historical data (zero wages)
        mock_supabase.table.return_value.select.return_value.eq.return_value.neq.return_value.gte.return_value.lt.return_value.in_.return_value.execute.return_value.data = []

        employee = {
            "id": "emp-ab-new",
            "hourly_rate": 25.00,
            "hire_date": "2025-06-15",
        }
        holidays = [{"holiday_date": "2025-07-01", "name": "Canada Day", "province": "AB"}]

        result = calculator.calculate_holiday_pay(
            employee=employee,
            province="AB",
            pay_frequency="bi_weekly",
            period_start=date(2025, 6, 28),
            period_end=date(2025, 7, 11),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("2000"),
            current_run_id="run-001",
        )

        # Should return 0 for ineligible fallback
        assert result.regular_holiday_pay == Decimal("0")

    def test_five_percent_pro_rated_fallback_with_zero_wages(self, mock_supabase):
        """Test 5_percent_28_days pro_rated fallback (lines 794-795)."""
        from app.models.holiday_pay_config import HolidayPayFormulaParams

        # Create SK config with pro_rated fallback
        config = HolidayPayConfig(
            province_code="SK",
            formula_type="5_percent_28_days",
            formula_params=HolidayPayFormulaParams(
                lookback_days=28,
                percentage=Decimal("0.05"),
                include_vacation_pay=True,
                include_previous_holiday_pay=True,
                new_employee_fallback="pro_rated",
            ),
            eligibility=HolidayPayEligibility(min_employment_days=0, require_last_first_rule=False),
            premium_rate=Decimal("1.5"),
        )
        loader = MockConfigLoader({"SK": config})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=loader,
        )

        # Mock empty historical data (zero wages)
        mock_supabase.table.return_value.select.return_value.eq.return_value.neq.return_value.gte.return_value.lt.return_value.in_.return_value.execute.return_value.data = []

        employee = {
            "id": "emp-sk-new",
            "hourly_rate": 25.00,
            "hire_date": "2025-06-15",
        }
        holidays = [{"holiday_date": "2025-07-01", "name": "Canada Day", "province": "SK"}]

        result = calculator.calculate_holiday_pay(
            employee=employee,
            province="SK",
            pay_frequency="bi_weekly",
            period_start=date(2025, 6, 28),
            period_end=date(2025, 7, 11),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("2000"),
            current_run_id="run-001",
        )

        # Should use current period gross as base: $2000 × 5% = $100
        assert result.regular_holiday_pay == Decimal("100")

    def test_ineligible_employee_gets_ineligibility_reason(self, holiday_calculator):
        """Test that ineligible employees get ineligibility reason (lines 321, 325-326, 334)."""
        # Employee with less than 30 days employment
        recent_date = (date.today() - timedelta(days=20)).isoformat()
        employee = {
            "id": "emp-ineligible-reason",
            "first_name": "Test",
            "last_name": "Employee",
            "hourly_rate": 25.00,
            "hire_date": recent_date,
        }
        holidays = [{"holiday_date": "2025-07-01", "name": "Canada Day", "province": "BC"}]

        result = holiday_calculator.calculate_holiday_pay(
            employee=employee,
            province="BC",
            pay_frequency="bi_weekly",
            period_start=date(2025, 6, 28),
            period_end=date(2025, 7, 11),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("2000"),
            current_run_id="run-001",
        )

        # Should be ineligible with reason
        assert result.regular_holiday_pay == Decimal("0")
        details = result.calculation_details
        assert details["holidays"][0]["eligible"] is False
        assert "ineligibility_reason" in details["holidays"][0]
        assert "< 30 days employed" in details["holidays"][0]["ineligibility_reason"]

    def test_ineligible_employee_with_invalid_hire_date(self, holiday_calculator):
        """Test ineligible reason with invalid hire_date format."""
        # Employee with invalid hire_date format
        employee = {
            "id": "emp-invalid-date-reason",
            "first_name": "Test",
            "last_name": "Employee",
            "hourly_rate": 25.00,
            "hire_date": "invalid-date-format",  # Invalid format
        }
        holidays = [{"holiday_date": "2025-07-01", "name": "Canada Day", "province": "BC"}]

        result = holiday_calculator.calculate_holiday_pay(
            employee=employee,
            province="BC",
            pay_frequency="bi_weekly",
            period_start=date(2025, 6, 28),
            period_end=date(2025, 7, 11),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("2000"),
            current_run_id="run-001",
        )

        # Invalid hire_date is a data issue, should be ineligible
        assert result.regular_holiday_pay == Decimal("0")
        assert result.calculation_details["holidays"][0]["eligible"] is False
        assert result.calculation_details["holidays"][0]["ineligibility_reason"] == "invalid hire date"

    def test_ineligible_employee_with_missing_hire_date(self, holiday_calculator):
        """Test ineligible reason with missing hire_date."""
        employee = {
            "id": "emp-missing-date",
            "first_name": "Test",
            "last_name": "Employee",
            "hourly_rate": 25.00,
            "hire_date": None,  # Missing hire_date
        }
        holidays = [{"holiday_date": "2025-07-01", "name": "Canada Day", "province": "BC"}]

        result = holiday_calculator.calculate_holiday_pay(
            employee=employee,
            province="BC",
            pay_frequency="bi_weekly",
            period_start=date(2025, 6, 28),
            period_end=date(2025, 7, 11),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("2000"),
            current_run_id="run-001",
        )

        # Missing hire_date is a data issue, should be ineligible
        assert result.regular_holiday_pay == Decimal("0")
        assert result.calculation_details["holidays"][0]["eligible"] is False
        assert result.calculation_details["holidays"][0]["ineligibility_reason"] == "missing hire date"


# =============================================================================
# Alberta Holiday Pay Tests - Phase 1: Days Worked Calculation
# =============================================================================


class TestAlbertaDaysWorkedCalculation:
    """Tests for actual days worked calculation in 4-week period."""

    def test_get_days_worked_from_timesheet(self, holiday_calculator):
        """Test _get_days_worked_in_4_weeks queries actual timesheet entries."""
        employee_id = "emp-alberta-001"
        holiday_date = date(2025, 12, 25)  # Thursday

        # Mock timesheet entries for 4-week period
        mock_result = MagicMock()
        mock_result.data = [
            {"work_date": "2025-12-04", "regular_hours": "8.0", "overtime_hours": "0"},
            {"work_date": "2025-12-11", "regular_hours": "8.0", "overtime_hours": "0"},
            {"work_date": "2025-12-18", "regular_hours": "5.0", "overtime_hours": "0"},
        ]
        # Properly chain the Supabase query builder methods
        mock_query = MagicMock()
        mock_query.execute.return_value = mock_result
        holiday_calculator.supabase.table.return_value.select.return_value.eq.return_value.gte.return_value.lte.return_value = mock_query

        count = holiday_calculator._get_days_worked_in_4_weeks(employee_id, holiday_date)

        assert count == 3, f"Expected 3 days worked, got {count}"

    def test_get_days_worked_no_timesheet_fallback(self, holiday_calculator):
        """Test fallback when no timesheet entries exist."""
        employee_id = "emp-alberta-002"
        holiday_date = date(2025, 12, 25)

        # Mock empty result
        mock_result = MagicMock()
        mock_result.data = []
        mock_query = MagicMock()
        mock_query.execute.return_value = mock_result
        holiday_calculator.supabase.table.return_value.select.return_value.eq.return_value.gte.return_value.lte.return_value = mock_query

        count = holiday_calculator._get_days_worked_in_4_weeks(employee_id, holiday_date)

        assert count == 0, f"Expected 0 days (no entries), got {count}"

    def test_get_days_worked_db_error_fallback(self, holiday_calculator):
        """Test fallback on database error."""
        employee_id = "emp-alberta-003"
        holiday_date = date(2025, 12, 25)

        # Mock exception
        holiday_calculator.supabase.table.side_effect = Exception("DB error")

        count = holiday_calculator._get_days_worked_in_4_weeks(employee_id, holiday_date)

        assert count == 20, f"Expected 20 (fallback), got {count}"

    def test_apply_4_week_daily_uses_actual_days(self, holiday_calculator):
        """Test _apply_4_week_daily uses actual days worked, not hardcoded 20."""
        employee_id = "emp-jonathan"
        hourly_employee = {
            "id": employee_id,
            "first_name": "Jonathan",
            "last_name": "Fjeld",
            "hourly_rate": 15.00,
            "hire_date": "2025-11-21",
        }
        holiday_date = date(2025, 12, 25)  # Thursday

        # Mock timesheet entries: 15 days worked in 4 weeks
        # For approximate $80.00 result with 15 days and $15/hour:
        # - 15 days × 5.33 hours = 79.95 hours
        # - 79.95 hours × $15/hour = $1,199.25
        # - $1,199.25 ÷ 15 days = $79.95
        mock_timesheet_result = MagicMock()
        mock_timesheet_result.data = []
        # Generate 15 unique work dates in the 4-week period
        for i in range(15):
            work_date = date(2025, 11, 28) + timedelta(days=i)
            mock_timesheet_result.data.append({
                "work_date": work_date.isoformat(),
                "regular_hours": "5.33",
                "overtime_hours": "0",
            })
        mock_timesheet_query = MagicMock()
        mock_timesheet_query.execute.return_value = mock_timesheet_result

        # Setup table to return timesheet data (no longer uses payroll_records)
        def table_side_effect(table_name):
            mock_table = MagicMock()
            if table_name == "timesheet_entries":
                mock_table.select.return_value.eq.return_value.gte.return_value.lte.return_value = mock_timesheet_query
            return mock_table

        holiday_calculator.supabase.table.side_effect = table_side_effect

        result = holiday_calculator._apply_4_week_daily(
            employee_id=employee_id,
            holiday_date=holiday_date,
            current_run_id="run-001",
            include_overtime=True,
            employee_fallback=hourly_employee,
            new_employee_fallback="ineligible",
        )

        # 15 days × 5.33 hours × $15/hour = $1,199.25 ÷ 15 days = $79.95
        # Key assertion: uses actual days worked (15), not hardcoded 20 days
        assert result == Decimal("79.95"), f"Expected $79.95, got ${result}"
        assert result != Decimal("60"), "Should NOT use hardcoded 20 days ($60)"


# =============================================================================
# Alberta Holiday Pay Tests - Phase 2: "5 of 9" Rule
# =============================================================================


class TestAlbertaFiveOfNineRule:
    """Tests for Alberta's "5 of 9" rule for determining regular work days."""

    def test_regular_day_pass_5_mondays(self, holiday_calculator):
        """Test 5 Mondays worked = Monday is regular work day."""
        employee_id = "emp-alberta-monday"
        holiday_date = date(2025, 12, 29)  # Monday

        # Mock timesheet: worked 5 Mondays in last 9 weeks
        mock_result = MagicMock()
        mock_result.data = []
        for i in range(5):
            # 5 Mondays: Nov 3, 10, 17, 24, Dec 1
            work_date = date(2025, 12, 29) - timedelta(weeks=i)
            mock_result.data.append({
                "work_date": work_date.isoformat(),
                "regular_hours": "8.0",
                "overtime_hours": "0",
            })
        mock_query = MagicMock()
        mock_query.execute.return_value = mock_result
        holiday_calculator.supabase.table.return_value.select.return_value.eq.return_value.gte.return_value.lte.return_value = mock_query

        is_regular = holiday_calculator._is_regular_work_day_5_of_9(
            employee_id, holiday_date, date(2025, 1, 1)
        )

        assert is_regular is True, "Monday should be regular (5 Mondays worked)"

    def test_non_regular_day_fail_3_mondays(self, holiday_calculator):
        """Test 3 Mondays worked = Monday is NOT regular work day."""
        employee_id = "emp-alberta-nomondays"
        holiday_date = date(2025, 12, 29)  # Monday

        # Mock timesheet: only 3 Mondays worked
        mock_result = MagicMock()
        mock_result.data = []
        for i in range(3):
            work_date = date(2025, 12, 29) - timedelta(weeks=i)
            mock_result.data.append({
                "work_date": work_date.isoformat(),
                "regular_hours": "4.0",
                "overtime_hours": "0",
            })
        mock_query = MagicMock()
        mock_query.execute.return_value = mock_result
        holiday_calculator.supabase.table.return_value.select.return_value.eq.return_value.gte.return_value.lte.return_value = mock_query

        is_regular = holiday_calculator._is_regular_work_day_5_of_9(
            employee_id, holiday_date, date(2025, 1, 1)
        )

        assert is_regular is False, "Monday should NOT be regular (only 3 Mondays)"

    def test_new_employee_pro_rated_threshold(self, holiday_calculator):
        """Test new employee (< 9 weeks) gets pro-rated threshold."""
        employee_id = "emp-alberta-new"
        holiday_date = date(2025, 12, 25)  # Thursday
        hire_date = date(2025, 11, 21)  # 5 weeks employment

        # Mock timesheet: worked 3 Thursdays in 5 weeks
        mock_result = MagicMock()
        mock_result.data = []
        for i in range(3):
            work_date = date(2025, 11, 27) + timedelta(weeks=i)  # Thursdays
            mock_result.data.append({
                "work_date": work_date.isoformat(),
                "regular_hours": "8.0",
                "overtime_hours": "0",
            })
        mock_query = MagicMock()
        mock_query.execute.return_value = mock_result
        holiday_calculator.supabase.table.return_value.select.return_value.eq.return_value.gte.return_value.lte.return_value = mock_query

        is_regular = holiday_calculator._is_regular_work_day_5_of_9(
            employee_id, holiday_date, hire_date
        )

        # 5 weeks employment: threshold = 5 × 5/9 ≈ 3
        # Worked 3 Thursdays: 3 >= 3 = regular
        assert is_regular is True, "New employee with 3/5 Thursdays should be regular"

    def test_five_of_nine_db_error_conservative(self, holiday_calculator):
        """Test database error returns conservative True (assume regular)."""
        employee_id = "emp-alberta-error"
        holiday_date = date(2025, 12, 25)

        # Mock exception
        holiday_calculator.supabase.table.side_effect = Exception("DB error")

        is_regular = holiday_calculator._is_regular_work_day_5_of_9(
            employee_id, holiday_date, date(2025, 1, 1)
        )

        assert is_regular is True, "DB error should conservatively return True"


# =============================================================================
# Alberta Holiday Pay Tests - Integration: Non-Regular Day Pay
# =============================================================================


class TestAlbertaNonRegularDayPay:
    """Tests for payment logic when holiday is on non-regular work day."""

    def test_non_regular_day_not_worked_zero_pay(self, holiday_calculator, mock_supabase):
        """Test non-regular day + not worked = $0 regular pay."""
        from app.models.holiday_pay_config import HolidayPayConfig, HolidayPayFormulaParams

        # Alberta config with "5 of 9" rule trigger
        ab_config = HolidayPayConfig(
            province_code="AB",
            formula_type="4_week_average_daily",
            formula_params=HolidayPayFormulaParams(
                lookback_weeks=4,
                method="wages_div_days_worked",
                new_employee_fallback="ineligible",
            ),
            eligibility=HolidayPayEligibility(
                min_employment_days=30,
                require_last_first_rule=True,  # Triggers "5 of 9" rule
            ),
            premium_rate=Decimal("1.5"),
        )

        ab_config_loader = MockConfigLoader({"AB": ab_config})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=ab_config_loader,
        )

        employee = {
            "id": "emp-non-regular",
            "first_name": "Non",
            "last_name": "Regular",
            "hourly_rate": 20.00,
            "hire_date": "2025-01-01",
        }

        # Holiday: Thursday Dec 25, 2025
        # Mock "5 of 9": Only 3 Thursdays worked (NOT regular)
        mock_timesheet = MagicMock()
        mock_timesheet.data = []
        for i in range(3):
            work_date = date(2025, 12, 25) - timedelta(weeks=i)
            mock_timesheet.data.append({
                "work_date": work_date.isoformat(),
                "regular_hours": "8.0",
                "overtime_hours": "0",
            })

        # Mock 4-week earnings: $1,000
        mock_earnings = MagicMock()
        mock_earnings.data = [{"gross_regular": "1000.00", "gross_overtime": "0"}]

        def table_side_effect(table_name):
            mock_table = MagicMock()
            if table_name == "timesheet_entries":
                result = MagicMock()
                result.execute.return_value = mock_timesheet
                mock_table.select.return_value.eq.return_value.gte.return_value.lte.return_value = result
            elif table_name == "payroll_records":
                result = MagicMock()
                result.execute.return_value = mock_earnings
                mock_table.select.return_value.eq.return_value.neq.return_value.gte.return_value.lt.return_value.in_.return_value = result
            return mock_table

        mock_supabase.table.side_effect = table_side_effect

        holidays = [{"holiday_date": "2025-12-25", "name": "Christmas Day", "province": "AB"}]

        result = calculator.calculate_holiday_pay(
            employee=employee,
            province="AB",
            pay_frequency="bi_weekly",
            period_start=date(2025, 12, 14),
            period_end=date(2025, 12, 27),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("1000"),
            current_run_id="run-001",
        )

        # Non-regular day + not worked = $0
        assert result.regular_holiday_pay == Decimal("0")
        assert result.calculation_details["holidays"][0]["is_regular_work_day"] is False

    def test_non_regular_day_worked_premium_only(self, holiday_calculator, mock_supabase):
        """Test non-regular day + worked = premium pay only (no regular pay)."""
        from app.models.holiday_pay_config import (
            HolidayPayConfig,
            HolidayPayEligibility,
            HolidayPayFormulaParams,
        )

        ab_config = HolidayPayConfig(
            province_code="AB",
            formula_type="4_week_average_daily",
            formula_params=HolidayPayFormulaParams(
                lookback_weeks=4,
                method="wages_div_days_worked",
                new_employee_fallback="ineligible",
            ),
            eligibility=HolidayPayEligibility(
                min_employment_days=30,
                require_last_first_rule=True,
            ),
            premium_rate=Decimal("1.5"),
        )

        ab_config_loader = MockConfigLoader({"AB": ab_config})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=ab_config_loader,
        )

        employee = {
            "id": "emp-non-regular-work",
            "first_name": "Worker",
            "last_name": "NonRegular",
            "hourly_rate": 20.00,
            "hire_date": "2025-01-01",
        }

        # Mock timesheet with last/first rule compliance
        mock_timesheet = MagicMock()
        mock_timesheet.data = []
        # Add entries around holiday Dec 25 (Thursday) for last/first rule compliance
        dates_to_add = [
            date(2025, 12, 24),  # Wednesday before
            date(2025, 12, 25),  # Holiday (Thursday) - worked
            date(2025, 12, 26),  # Friday after
        ]
        for work_date in dates_to_add:
            mock_timesheet.data.append({
                "work_date": work_date.isoformat(),
                "regular_hours": "8.0",
                "overtime_hours": "0",
            })
        # Add ONLY 3 more Thursdays in 9-week window (FAILS 5 of 9 -> non-regular day)
        # This makes Thursday a NON-regular work day
        for i in range(1, 4):  # Only 3 additional Thursdays (not 5)
            work_date = date(2025, 12, 25) - timedelta(weeks=i)
            mock_timesheet.data.append({
                "work_date": work_date.isoformat(),
                "regular_hours": "8.0",
                "overtime_hours": "0",
            })

        mock_earnings = MagicMock()
        mock_earnings.data = [{"gross_regular": "1000.00", "gross_overtime": "0"}]

        def table_side_effect(table_name):
            mock_table = MagicMock()
            if table_name == "timesheet_entries":
                result = MagicMock()
                result.execute.return_value = mock_timesheet
                mock_table.select.return_value.eq.return_value.gte.return_value.lte.return_value = result
            elif table_name == "payroll_records":
                result = MagicMock()
                result.execute.return_value = mock_earnings
                mock_table.select.return_value.eq.return_value.neq.return_value.gte.return_value.lt.return_value.in_.return_value = result
            return mock_table

        mock_supabase.table.side_effect = table_side_effect

        holidays = [{"holiday_date": "2025-12-25", "name": "Christmas Day", "province": "AB"}]
        work_entries = [{"holidayDate": "2025-12-25", "hoursWorked": 8}]  # Worked 8 hours

        result = calculator.calculate_holiday_pay(
            employee=employee,
            province="AB",
            pay_frequency="bi_weekly",
            period_start=date(2025, 12, 14),
            period_end=date(2025, 12, 27),
            holidays_in_period=holidays,
            holiday_work_entries=work_entries,
            current_period_gross=Decimal("1000"),
            current_run_id="run-001",
        )

        # Non-regular day + worked
        # Regular pay: $0 (not regular)
        # Premium pay: 8h × $20 × 1.5 = $240
        assert result.regular_holiday_pay == Decimal("0")
        assert result.premium_holiday_pay == Decimal("240")
