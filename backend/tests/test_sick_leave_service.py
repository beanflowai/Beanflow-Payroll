"""
Tests for Sick Leave Service

Tests sick leave calculation logic for BC and Federal jurisdictions,
including part-time employee calculations and year-end carryover.

Reference: docs/08_holidays_vacation.md Task 8.7
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.services.payroll.sick_leave_service import (
    AverageDayPayResult,
    SickLeaveBalance,
    SickLeaveConfig,
    SickLeaveService,
    SickPayResult,
)


@pytest.fixture
def sick_leave_service():
    """Create sick leave service with default configs."""
    return SickLeaveService()


# =============================================================================
# CONFIGURATION TESTS
# =============================================================================


class TestSickLeaveConfig:
    """Test sick leave configurations."""

    def test_bc_config_exists(self, sick_leave_service: SickLeaveService):
        """BC should have 5 paid days with 90-day waiting period."""
        config = sick_leave_service.get_config("BC")
        assert config is not None
        assert config.paid_days_per_year == 5
        assert config.unpaid_days_per_year == 3
        assert config.waiting_period_days == 90
        assert config.allows_carryover is False

    def test_federal_config_exists(self, sick_leave_service: SickLeaveService):
        """Federal should have 10 paid days with monthly accrual and carryover."""
        config = sick_leave_service.get_config("Federal")
        assert config is not None
        assert config.paid_days_per_year == 10
        assert config.waiting_period_days == 30
        assert config.allows_carryover is True
        assert config.max_carryover_days == 10
        assert config.accrual_method == "monthly"
        assert config.initial_days_after_qualifying == 3
        assert config.days_per_month_after_initial == 1

    def test_ontario_no_paid_sick_leave(self, sick_leave_service: SickLeaveService):
        """Ontario should have 0 paid days and 3 unpaid days."""
        config = sick_leave_service.get_config("ON")
        assert config is not None
        assert config.paid_days_per_year == 0
        assert config.unpaid_days_per_year == 3

    def test_alberta_no_sick_leave(self, sick_leave_service: SickLeaveService):
        """Alberta has no statutory sick leave."""
        config = sick_leave_service.get_config("AB")
        assert config is not None
        assert config.paid_days_per_year == 0
        assert config.unpaid_days_per_year == 0

    def test_quebec_config_exists(self, sick_leave_service: SickLeaveService):
        """Quebec should have 2 paid days with 90-day waiting period."""
        config = sick_leave_service.get_config("QC")
        assert config is not None
        assert config.paid_days_per_year == 2
        assert config.waiting_period_days == 90
        assert config.allows_carryover is False

    def test_unknown_province_returns_none(self, sick_leave_service: SickLeaveService):
        """Unknown province should return None."""
        config = sick_leave_service.get_config("INVALID")
        assert config is None

    def test_all_provinces_loaded(self, sick_leave_service: SickLeaveService):
        """All 14 jurisdictions should be loaded from JSON."""
        expected_provinces = {
            "BC", "ON", "AB", "MB", "SK", "QC",
            "NB", "NS", "PE", "NL", "NT", "NU", "YT", "Federal"
        }
        loaded_provinces = set(sick_leave_service.configs.keys())
        assert loaded_provinces == expected_provinces


# =============================================================================
# ELIGIBILITY TESTS
# =============================================================================


class TestEligibility:
    """Test sick leave eligibility based on waiting period."""

    def test_bc_not_eligible_before_90_days(self, sick_leave_service: SickLeaveService):
        """BC employee should not be eligible before 90 days."""
        hire_date = date(2025, 1, 1)
        reference_date = date(2025, 3, 1)  # 59 days

        is_eligible, eligibility_date = sick_leave_service.check_eligibility(
            hire_date, "BC", reference_date
        )

        assert is_eligible is False
        assert eligibility_date == date(2025, 4, 1)  # 90 days after hire

    def test_bc_eligible_after_90_days(self, sick_leave_service: SickLeaveService):
        """BC employee should be eligible after 90 days."""
        hire_date = date(2025, 1, 1)
        reference_date = date(2025, 4, 2)  # 91 days

        is_eligible, eligibility_date = sick_leave_service.check_eligibility(
            hire_date, "BC", reference_date
        )

        assert is_eligible is True
        assert eligibility_date == date(2025, 4, 1)

    def test_ontario_immediately_eligible(self, sick_leave_service: SickLeaveService):
        """Ontario employee should be immediately eligible (no paid, but unpaid)."""
        hire_date = date(2025, 1, 1)
        reference_date = date(2025, 1, 2)  # Day 2

        is_eligible, eligibility_date = sick_leave_service.check_eligibility(
            hire_date, "ON", reference_date
        )

        assert is_eligible is True
        assert eligibility_date == hire_date

    def test_federal_eligible_after_30_days(self, sick_leave_service: SickLeaveService):
        """Federal employee should be eligible after 30 days."""
        hire_date = date(2025, 1, 1)
        reference_date = date(2025, 2, 1)  # 31 days

        is_eligible, eligibility_date = sick_leave_service.check_eligibility(
            hire_date, "Federal", reference_date
        )

        assert is_eligible is True


# =============================================================================
# BC AVERAGE DAY'S PAY CALCULATION TESTS
# =============================================================================


class TestBCAverageDayPay:
    """Test BC average day's pay calculation."""

    def test_bc_full_time_employee(self, sick_leave_service: SickLeaveService):
        """Full-time employee: 22 days worked, $4,400 earned."""
        wages_past_30_days = Decimal("4400.00")
        days_worked = 22

        result = sick_leave_service.calculate_bc_average_day_pay(
            wages_past_30_days, days_worked
        )

        assert result.amount == Decimal("200.00")  # $4400 / 22 = $200
        assert result.calculation_method == "bc_30_day_avg"
        assert result.days_counted == 22

    def test_bc_part_time_employee(self, sick_leave_service: SickLeaveService):
        """Part-time employee: 12 days worked, $1,440 earned."""
        # Part-time: 3 days/week, $20/hr, 6 hrs/day = $120/day
        wages_past_30_days = Decimal("1440.00")  # 12 days × $120
        days_worked = 12

        result = sick_leave_service.calculate_bc_average_day_pay(
            wages_past_30_days, days_worked
        )

        assert result.amount == Decimal("120.00")  # $1440 / 12 = $120
        assert result.calculation_method == "bc_30_day_avg"
        assert result.days_counted == 12

    def test_bc_variable_hours_employee(self, sick_leave_service: SickLeaveService):
        """Variable hours employee with different daily earnings."""
        # Some days 4 hrs ($80), some days 8 hrs ($160)
        wages_past_30_days = Decimal("1800.00")
        days_worked = 15

        result = sick_leave_service.calculate_bc_average_day_pay(
            wages_past_30_days, days_worked
        )

        assert result.amount == Decimal("120.00")  # $1800 / 15 = $120

    def test_bc_no_days_worked_returns_zero(self, sick_leave_service: SickLeaveService):
        """Zero days worked should return zero."""
        result = sick_leave_service.calculate_bc_average_day_pay(
            Decimal("0"), 0
        )

        assert result.amount == Decimal("0")
        assert result.days_counted == 0


# =============================================================================
# FEDERAL AVERAGE DAY'S PAY CALCULATION TESTS
# =============================================================================


class TestFederalAverageDayPay:
    """Test Federal average day's pay calculation."""

    def test_federal_standard_20_days(self, sick_leave_service: SickLeaveService):
        """Standard calculation with 20 days of earnings."""
        earnings_past_20_days = Decimal("2400.00")

        result = sick_leave_service.calculate_federal_average_day_pay(
            earnings_past_20_days, 20
        )

        assert result.amount == Decimal("120.00")  # $2400 / 20 = $120
        assert result.calculation_method == "federal_20_day_avg"

    def test_federal_part_time_variable_hours(
        self, sick_leave_service: SickLeaveService
    ):
        """Part-time with variable daily hours."""
        # 20 days of variable work
        earnings_past_20_days = Decimal("1600.00")

        result = sick_leave_service.calculate_federal_average_day_pay(
            earnings_past_20_days, 20
        )

        assert result.amount == Decimal("80.00")  # $1600 / 20 = $80


# =============================================================================
# FEDERAL ACCRUAL TESTS
# =============================================================================


class TestFederalAccrual:
    """Test Federal sick leave accrual."""

    def test_federal_not_eligible_before_30_days(
        self, sick_leave_service: SickLeaveService
    ):
        """Should have 0 days before qualifying period."""
        hire_date = date(2025, 1, 1)
        reference_date = date(2025, 1, 15)  # 14 days

        accrued = sick_leave_service.calculate_federal_accrued_days(
            hire_date, reference_date
        )

        assert accrued == Decimal("0")

    def test_federal_3_days_after_qualifying(
        self, sick_leave_service: SickLeaveService
    ):
        """Should have 3 days immediately after qualifying period."""
        hire_date = date(2025, 1, 1)
        reference_date = date(2025, 1, 31)  # Exactly 30 days

        accrued = sick_leave_service.calculate_federal_accrued_days(
            hire_date, reference_date
        )

        assert accrued == Decimal("3")

    def test_federal_accrual_after_months(self, sick_leave_service: SickLeaveService):
        """Should accrue additional days after initial period."""
        hire_date = date(2025, 1, 1)
        reference_date = date(2025, 4, 1)  # ~90 days = 30 + 60

        # 30 days qualifying + 2 months = 3 + 2 = 5 days
        accrued = sick_leave_service.calculate_federal_accrued_days(
            hire_date, reference_date
        )

        assert accrued == Decimal("5")

    def test_federal_max_10_days(self, sick_leave_service: SickLeaveService):
        """Should cap at 10 days maximum."""
        hire_date = date(2024, 1, 1)
        reference_date = date(2025, 12, 31)  # Well over a year

        accrued = sick_leave_service.calculate_federal_accrued_days(
            hire_date, reference_date
        )

        assert accrued == Decimal("10")

    def test_federal_carryover_adds_to_accrued(
        self, sick_leave_service: SickLeaveService
    ):
        """Carryover should add to accrued days (up to max 10)."""
        hire_date = date(2025, 1, 1)
        reference_date = date(2025, 2, 15)  # ~45 days = 3 accrued
        carried_over = Decimal("4")

        accrued = sick_leave_service.calculate_federal_accrued_days(
            hire_date, reference_date, carried_over_days=carried_over
        )

        # 3 accrued + 4 carryover = 7 (under max)
        assert accrued == Decimal("7")

    def test_federal_carryover_capped_at_max(
        self, sick_leave_service: SickLeaveService
    ):
        """Carryover + accrued should not exceed 10."""
        hire_date = date(2025, 1, 1)
        reference_date = date(2025, 6, 1)  # ~150 days = 7 accrued
        carried_over = Decimal("6")

        accrued = sick_leave_service.calculate_federal_accrued_days(
            hire_date, reference_date, carried_over_days=carried_over
        )

        # Would be 7 + 6 = 13, but capped at 10
        assert accrued == Decimal("10")


# =============================================================================
# SICK PAY CALCULATION TESTS
# =============================================================================


class TestSickPayCalculation:
    """Test sick pay calculation."""

    def test_bc_full_day_sick_pay(self, sick_leave_service: SickLeaveService):
        """BC employee takes 1 full day of sick leave."""
        balance = SickLeaveBalance(
            employee_id="test-123",
            year=2025,
            paid_days_entitled=Decimal("5"),
            unpaid_days_entitled=Decimal("3"),
            paid_days_used=Decimal("0"),
            unpaid_days_used=Decimal("0"),
            carried_over_days=Decimal("0"),
            is_eligible=True,
        )

        result = sick_leave_service.calculate_sick_pay(
            province_code="BC",
            sick_hours_taken=Decimal("8"),  # 1 day
            average_day_pay=Decimal("200.00"),
            balance=balance,
        )

        assert result.eligible is True
        assert result.days_used == Decimal("1.00")
        assert result.paid_days == Decimal("1.00")
        assert result.unpaid_days == Decimal("0")
        assert result.amount == Decimal("200.00")
        assert result.balance_after == Decimal("4.00")

    def test_bc_partial_day_sick_leave(self, sick_leave_service: SickLeaveService):
        """BC: Even partial hours count as full day under ESA."""
        balance = SickLeaveBalance(
            employee_id="test-123",
            year=2025,
            paid_days_entitled=Decimal("5"),
            unpaid_days_entitled=Decimal("3"),
            paid_days_used=Decimal("0"),
            unpaid_days_used=Decimal("0"),
            carried_over_days=Decimal("0"),
            is_eligible=True,
        )

        # 4 hours = 0.5 days in our system
        result = sick_leave_service.calculate_sick_pay(
            province_code="BC",
            sick_hours_taken=Decimal("4"),
            average_day_pay=Decimal("200.00"),
            balance=balance,
        )

        assert result.days_used == Decimal("0.50")
        assert result.amount == Decimal("100.00")

    def test_exceeds_paid_balance_uses_unpaid(
        self, sick_leave_service: SickLeaveService
    ):
        """When paid balance exceeded, remainder should be unpaid."""
        balance = SickLeaveBalance(
            employee_id="test-123",
            year=2025,
            paid_days_entitled=Decimal("5"),
            unpaid_days_entitled=Decimal("3"),
            paid_days_used=Decimal("4"),  # Already used 4 days
            unpaid_days_used=Decimal("0"),
            carried_over_days=Decimal("0"),
            is_eligible=True,
        )

        # Take 2 days (16 hours) - only 1 paid day remaining
        result = sick_leave_service.calculate_sick_pay(
            province_code="BC",
            sick_hours_taken=Decimal("16"),
            average_day_pay=Decimal("200.00"),
            balance=balance,
        )

        assert result.days_used == Decimal("2.00")
        assert result.paid_days == Decimal("1.00")
        assert result.unpaid_days == Decimal("1.00")
        assert result.amount == Decimal("200.00")  # Only 1 paid day × $200
        assert result.balance_after == Decimal("0")

    def test_not_eligible_returns_zero(self, sick_leave_service: SickLeaveService):
        """Ineligible employee should get zero pay."""
        balance = SickLeaveBalance(
            employee_id="test-123",
            year=2025,
            paid_days_entitled=Decimal("5"),
            unpaid_days_entitled=Decimal("3"),
            paid_days_used=Decimal("0"),
            unpaid_days_used=Decimal("0"),
            carried_over_days=Decimal("0"),
            is_eligible=False,  # Not eligible yet
        )

        result = sick_leave_service.calculate_sick_pay(
            province_code="BC",
            sick_hours_taken=Decimal("8"),
            average_day_pay=Decimal("200.00"),
            balance=balance,
        )

        assert result.eligible is False
        assert result.amount == Decimal("0")
        assert "waiting period" in (result.reason or "").lower()

    def test_province_without_paid_sick_leave(
        self, sick_leave_service: SickLeaveService
    ):
        """Alberta employee should get no sick pay (no statutory paid leave)."""
        balance = SickLeaveBalance(
            employee_id="test-123",
            year=2025,
            paid_days_entitled=Decimal("0"),
            unpaid_days_entitled=Decimal("0"),
            paid_days_used=Decimal("0"),
            unpaid_days_used=Decimal("0"),
            carried_over_days=Decimal("0"),
            is_eligible=True,
        )

        result = sick_leave_service.calculate_sick_pay(
            province_code="AB",
            sick_hours_taken=Decimal("8"),
            average_day_pay=Decimal("0"),  # No statutory pay
            balance=balance,
        )

        assert result.paid_days == Decimal("0")
        assert result.amount == Decimal("0")


# =============================================================================
# YEAR-END CARRYOVER TESTS
# =============================================================================


class TestYearEndCarryover:
    """Test year-end carryover processing."""

    def test_bc_no_carryover(self, sick_leave_service: SickLeaveService):
        """BC should have zero carryover."""
        carryover = sick_leave_service.calculate_year_end_carryover(
            province_code="BC", paid_days_remaining=Decimal("3")
        )

        assert carryover == Decimal("0")

    def test_federal_carryover_within_limit(
        self, sick_leave_service: SickLeaveService
    ):
        """Federal should carry over remaining days up to limit."""
        carryover = sick_leave_service.calculate_year_end_carryover(
            province_code="Federal", paid_days_remaining=Decimal("7")
        )

        assert carryover == Decimal("7")

    def test_federal_carryover_capped_at_max(
        self, sick_leave_service: SickLeaveService
    ):
        """Federal carryover should be capped at 10."""
        carryover = sick_leave_service.calculate_year_end_carryover(
            province_code="Federal", paid_days_remaining=Decimal("15")
        )

        assert carryover == Decimal("10")


# =============================================================================
# NEW YEAR BALANCE CREATION TESTS
# =============================================================================


class TestNewYearBalance:
    """Test creating new year's sick leave balance."""

    def test_bc_new_year_balance_eligible(self, sick_leave_service: SickLeaveService):
        """BC employee with sufficient tenure should be eligible."""
        balance = sick_leave_service.create_new_year_balance(
            employee_id="test-123",
            year=2025,
            province_code="BC",
            hire_date=date(2024, 1, 1),  # Over 90 days
        )

        assert balance.paid_days_entitled == Decimal("5")
        assert balance.unpaid_days_entitled == Decimal("3")
        assert balance.is_eligible is True
        assert balance.carried_over_days == Decimal("0")

    def test_bc_new_year_balance_not_eligible(
        self, sick_leave_service: SickLeaveService
    ):
        """BC employee without sufficient tenure should not be eligible yet."""
        balance = sick_leave_service.create_new_year_balance(
            employee_id="test-123",
            year=2025,
            province_code="BC",
            hire_date=date(2024, 12, 1),  # Less than 90 days
        )

        assert balance.is_eligible is False
        assert balance.eligibility_date is not None

    def test_federal_new_year_with_carryover(
        self, sick_leave_service: SickLeaveService
    ):
        """Federal employee should have carryover applied."""
        balance = sick_leave_service.create_new_year_balance(
            employee_id="test-123",
            year=2025,
            province_code="Federal",
            hire_date=date(2024, 1, 1),
            carried_over_days=Decimal("5"),
        )

        assert balance.paid_days_entitled == Decimal("10")
        assert balance.carried_over_days == Decimal("5")
        assert balance.is_eligible is True


# =============================================================================
# PART-TIME EMPLOYEE SPECIFIC TESTS
# =============================================================================


class TestPartTimeEmployees:
    """Test that part-time employees are NOT pro-rated."""

    def test_part_time_gets_full_entitlement(
        self, sick_leave_service: SickLeaveService
    ):
        """Part-time employee should get full 5 days in BC."""
        # Part-time employee (doesn't matter - full entitlement)
        balance = sick_leave_service.create_new_year_balance(
            employee_id="part-time-123",
            year=2025,
            province_code="BC",
            hire_date=date(2024, 1, 1),
        )

        # Part-time still gets full 5 paid days
        assert balance.paid_days_entitled == Decimal("5")

    def test_part_time_average_day_pay_reflects_actual_earnings(
        self, sick_leave_service: SickLeaveService
    ):
        """Part-time average day's pay reflects their actual daily earnings."""
        # Part-time: 3 days/week, 6 hrs/day at $20/hr = $120/day
        # 30 days = ~13 work days (3/week × 4.3 weeks)
        wages = Decimal("1560.00")  # 13 days × $120
        days = 13

        result = sick_leave_service.calculate_bc_average_day_pay(wages, days)

        assert result.amount == Decimal("120.00")  # Their actual daily rate

    def test_federal_part_time_full_10_days(
        self, sick_leave_service: SickLeaveService
    ):
        """Federal part-time employee gets full 10 days."""
        balance = sick_leave_service.create_new_year_balance(
            employee_id="federal-part-time",
            year=2025,
            province_code="Federal",
            hire_date=date(2024, 1, 1),
        )

        assert balance.paid_days_entitled == Decimal("10")
