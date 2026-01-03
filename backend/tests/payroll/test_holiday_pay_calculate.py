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
        """BC: New hire <30 days should not get Regular pay, but can get Premium."""
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
        # Premium: 8h × $20 × 1.5 = $240
        assert result.regular_holiday_pay == Decimal("0")
        assert result.premium_holiday_pay == Decimal("240")
        assert result.total_holiday_pay == Decimal("240")

    def test_ontario_new_hire_eligible(self, mock_supabase):
        """Ontario: New hire IS eligible (no 30-day requirement)."""
        # Create calculator with Ontario config
        on_config_loader = MockConfigLoader({"ON": make_on_config()})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=on_config_loader,
        )

        # Mock empty historical data (will fall back to 30-day avg)
        mock_supabase.table.return_value.select.return_value.eq.return_value.neq.return_value.gte.return_value.lt.return_value.in_.return_value.execute.return_value.data = []

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

        # Ontario: New hire IS eligible (no min days requirement)
        # Regular: 8h × $20 = $160 (fallback to 30-day avg since no history)
        assert result.regular_holiday_pay == Decimal("160")
        assert result.premium_holiday_pay == Decimal("0")

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
