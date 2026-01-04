"""
Tests for Province-Specific Holiday Pay Integration.

Tests:
- Saskatchewan 5% formula integration
- SK with historical data
- SK with vacation and holiday pay
- SK new employee fallback
- SK premium pay for worked holidays
"""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.services.payroll_run.holiday_pay_calculator import HolidayPayCalculator


class TestSaskatchewanIntegration:
    """Integration tests for Saskatchewan 5% formula through calculate_holiday_pay()."""

    @pytest.fixture
    def mock_supabase(self):
        """Create a mock Supabase client."""
        return MagicMock()

    @pytest.fixture
    def sk_calculator(self, mock_supabase):
        """Create calculator with real SK config from file."""
        return HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=None,  # Use real config loader
        )

    @pytest.fixture
    def sk_hourly_employee(self):
        """SK hourly employee with sufficient employment history."""
        return {
            "id": "emp-sk-001",
            "first_name": "John",
            "last_name": "Saskatchewan",
            "hourly_rate": 35.00,
            "annual_salary": None,
            "hire_date": "2024-01-01",
            "province_of_employment": "SK",
        }

    def test_sk_with_historical_data(self, sk_calculator, sk_hourly_employee, mock_supabase):
        """SK: Calculate with 28-day historical earnings."""
        # Mock historical data: $2800 in wages over 28 days
        mock_supabase.table.return_value.select.return_value.eq.return_value.neq.return_value.gte.return_value.lt.return_value.in_.return_value.execute.return_value.data = [
            {"gross_regular": 1400, "vacation_pay_paid": 0, "holiday_pay": 0},
            {"gross_regular": 1400, "vacation_pay_paid": 0, "holiday_pay": 0},
        ]

        result = sk_calculator.calculate_holiday_pay(
            employee=sk_hourly_employee,
            province="SK",
            pay_frequency="bi_weekly",
            period_start=date(2025, 1, 1),
            period_end=date(2025, 1, 14),
            holidays_in_period=[{"holiday_date": "2025-01-01", "name": "New Year's Day", "province": "SK"}],
            holiday_work_entries=[],
            current_period_gross=Decimal("1400"),
            current_run_id="run-001",
        )

        # $2800 × 5% = $140
        assert result.regular_holiday_pay == Decimal("140")
        assert result.calculation_details["config"]["formula_type"] == "5_percent_28_days"

    def test_sk_with_vacation_and_holiday_pay(self, sk_calculator, sk_hourly_employee, mock_supabase):
        """SK: Include vacation pay and previous holiday pay in base."""
        # Mock: $2400 wages + $96 vacation + $120 holiday
        mock_supabase.table.return_value.select.return_value.eq.return_value.neq.return_value.gte.return_value.lt.return_value.in_.return_value.execute.return_value.data = [
            {"gross_regular": 1200, "vacation_pay_paid": 48, "holiday_pay": 60},
            {"gross_regular": 1200, "vacation_pay_paid": 48, "holiday_pay": 60},
        ]

        result = sk_calculator.calculate_holiday_pay(
            employee=sk_hourly_employee,
            province="SK",
            pay_frequency="bi_weekly",
            period_start=date(2025, 2, 15),
            period_end=date(2025, 2, 28),
            holidays_in_period=[{"holiday_date": "2025-02-17", "name": "Family Day", "province": "SK"}],
            holiday_work_entries=[],
            current_period_gross=Decimal("1200"),
            current_run_id="run-002",
        )

        # ($2400 + $96 + $120) × 5% = $2616 × 0.05 = $130.80
        assert result.regular_holiday_pay == Decimal("130.80")

    def test_sk_new_employee_no_history(self, sk_calculator, mock_supabase):
        """SK: New employee with no history uses current_period_gross."""
        # Mock empty historical data
        mock_supabase.table.return_value.select.return_value.eq.return_value.neq.return_value.gte.return_value.lt.return_value.in_.return_value.execute.return_value.data = []

        new_hire = {
            "id": "emp-sk-new",
            "first_name": "New",
            "last_name": "Hire",
            "hourly_rate": 18.00,
            "hire_date": "2024-12-20",  # Less than 30 days before holiday
        }

        result = sk_calculator.calculate_holiday_pay(
            employee=new_hire,
            province="SK",
            pay_frequency="bi_weekly",
            period_start=date(2024, 12, 28),
            period_end=date(2025, 1, 10),
            holidays_in_period=[{"holiday_date": "2025-01-01", "name": "New Year's Day", "province": "SK"}],
            holiday_work_entries=[],
            current_period_gross=Decimal("720"),  # 40 hours × $18
            current_run_id="run-003",
        )

        # SK new employee: no history → uses current_period_gross
        # $720 × 5% = $36
        assert result.regular_holiday_pay == Decimal("36")
        # Verify employee is still eligible (no min days in SK)
        assert result.calculation_details["holidays"][0]["eligible"] is True

    def test_sk_holiday_worked_gets_premium(self, sk_calculator, sk_hourly_employee, mock_supabase):
        """SK: Employee working on holiday gets both regular and premium pay."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.neq.return_value.gte.return_value.lt.return_value.in_.return_value.execute.return_value.data = [
            {"gross_regular": 1400, "vacation_pay_paid": 0, "holiday_pay": 0},
            {"gross_regular": 1400, "vacation_pay_paid": 0, "holiday_pay": 0},
        ]

        result = sk_calculator.calculate_holiday_pay(
            employee=sk_hourly_employee,
            province="SK",
            pay_frequency="bi_weekly",
            period_start=date(2025, 1, 1),
            period_end=date(2025, 1, 14),
            holidays_in_period=[{"holiday_date": "2025-01-01", "name": "New Year's Day", "province": "SK"}],
            holiday_work_entries=[{"holidayDate": "2025-01-01", "hoursWorked": 8}],
            current_period_gross=Decimal("1400"),
            current_run_id="run-004",
        )

        # Regular: $2800 × 5% = $140
        # Premium: 8h × $35 × 1.5 = $420
        assert result.regular_holiday_pay == Decimal("140")
        assert result.premium_holiday_pay == Decimal("420")
        assert result.total_holiday_pay == Decimal("560")

    def test_sk_part_time_low_hours(self, sk_calculator, mock_supabase):
        """SK: Part-time employee with minimal hours still qualifies."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.neq.return_value.gte.return_value.lt.return_value.in_.return_value.execute.return_value.data = [
            {"gross_regular": 60, "vacation_pay_paid": 0, "holiday_pay": 0},
        ]

        part_time = {
            "id": "emp-sk-pt",
            "first_name": "Part",
            "last_name": "Time",
            "hourly_rate": 20.00,
            "hire_date": "2024-06-01",
        }

        result = sk_calculator.calculate_holiday_pay(
            employee=part_time,
            province="SK",
            pay_frequency="bi_weekly",
            period_start=date(2024, 12, 28),
            period_end=date(2025, 1, 10),
            holidays_in_period=[{"holiday_date": "2025-01-01", "name": "New Year's Day", "province": "SK"}],
            holiday_work_entries=[],
            current_period_gross=Decimal("60"),
            current_run_id="run-005",
        )

        # $60 × 5% = $3
        assert result.regular_holiday_pay == Decimal("3")
