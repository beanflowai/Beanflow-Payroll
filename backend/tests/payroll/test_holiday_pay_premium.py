"""
Tests for Holiday Pay Premium Calculation.

Tests:
- Premium pay for hourly employees
- Premium pay for salaried employees
- Premium pay for partial hours
"""

from decimal import Decimal

from tests.payroll.conftest import make_bc_config


class TestPremiumPay:
    """Tests for premium pay calculation: hours × rate × premium_rate."""

    def test_premium_hourly_employee(self, holiday_calculator, hourly_employee):
        """Premium pay for hourly employee working on holiday."""
        config = make_bc_config()
        hours_worked = Decimal("8")

        premium = holiday_calculator._calculate_premium_pay(hourly_employee, hours_worked, config)

        # 8h × $25 × 1.5 = $300
        assert premium == Decimal("300")

    def test_premium_salaried_employee(self, holiday_calculator, salaried_employee):
        """Premium pay for salaried employee working on holiday."""
        config = make_bc_config()
        hours_worked = Decimal("8")

        premium = holiday_calculator._calculate_premium_pay(salaried_employee, hours_worked, config)

        # 8h × ($60000/2080) × 1.5
        hourly_rate = Decimal("60000") / Decimal("2080")
        expected = hours_worked * hourly_rate * Decimal("1.5")
        assert premium == expected

    def test_premium_partial_hours(self, holiday_calculator, hourly_employee):
        """Premium pay for partial hours worked."""
        config = make_bc_config()
        hours_worked = Decimal("4.5")

        premium = holiday_calculator._calculate_premium_pay(hourly_employee, hours_worked, config)

        # 4.5h × $25 × 1.5 = $168.75
        assert premium == Decimal("168.75")
