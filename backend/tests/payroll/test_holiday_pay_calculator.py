"""
Tests for Holiday Pay Calculator (Config-Driven)

Tests:
- Config loading and fallback
- BC Hourly employees: single/multiple holidays
- BC Salaried employees: should skip Regular, only Premium
- Alberta formula: uses 4-week daily average
- Ontario formula: with/without historical data, no 30-day requirement
- Premium pay: all employee types
- Config-driven eligibility check
- Edge cases: no holidays, no work entries
"""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.models.holiday_pay_config import (
    HolidayPayConfig,
    HolidayPayEligibility,
    HolidayPayFormulaParams,
)
from app.services.payroll.holiday_pay_config_loader import (
    HolidayPayConfigLoader,
    get_config,
)
from app.services.payroll_run.holiday_pay_calculator import (
    WORK_DAYS_PER_PERIOD,
    HolidayPayCalculator,
    HolidayPayResult,
)


# =============================================================================
# TEST CONFIGS
# =============================================================================


def make_bc_config() -> HolidayPayConfig:
    """Create BC test config."""
    return HolidayPayConfig(
        province_code="BC",
        formula_type="30_day_average",
        formula_params=HolidayPayFormulaParams(
            lookback_days=30,
            method="total_wages_div_days",
            default_daily_hours=Decimal("8"),
        ),
        eligibility=HolidayPayEligibility(
            min_employment_days=30,
            require_last_first_rule=False,
        ),
        premium_rate=Decimal("1.5"),
    )


def make_on_config() -> HolidayPayConfig:
    """Create Ontario test config - no 30-day requirement."""
    return HolidayPayConfig(
        province_code="ON",
        formula_type="4_week_average",
        formula_params=HolidayPayFormulaParams(
            lookback_weeks=4,
            divisor=20,
            include_vacation_pay=True,
            new_employee_fallback="pro_rated",
        ),
        eligibility=HolidayPayEligibility(
            min_employment_days=0,  # Ontario has no min days
            require_last_first_rule=True,
        ),
        premium_rate=Decimal("1.5"),
    )


def make_ab_config() -> HolidayPayConfig:
    """Create Alberta test config."""
    return HolidayPayConfig(
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


class MockConfigLoader:
    """Mock config loader for testing."""

    def __init__(self, configs: dict[str, HolidayPayConfig] | None = None):
        self.configs = configs or {
            "BC": make_bc_config(),
            "ON": make_on_config(),
            "AB": make_ab_config(),
        }

    def get_config(self, province_code: str) -> HolidayPayConfig:
        return self.configs.get(province_code, make_bc_config())


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_supabase():
    """Create a mock Supabase client."""
    return MagicMock()


@pytest.fixture
def mock_config_loader():
    """Create a mock config loader."""
    return MockConfigLoader()


@pytest.fixture
def calculator(mock_supabase, mock_config_loader):
    """Create a HolidayPayCalculator instance with mock config."""
    return HolidayPayCalculator(
        supabase=mock_supabase,
        user_id="test-user-id",
        company_id="test-company-id",
        config_loader=mock_config_loader,
    )


@pytest.fixture
def hourly_employee():
    """Create a test hourly employee."""
    return {
        "id": "emp-001",
        "first_name": "John",
        "last_name": "Doe",
        "hourly_rate": 25.00,
        "annual_salary": None,
        "hire_date": "2024-01-01",  # Eligible (>30 days)
        "province_of_employment": "BC",
    }


@pytest.fixture
def salaried_employee():
    """Create a test salaried employee."""
    return {
        "id": "emp-002",
        "first_name": "Jane",
        "last_name": "Smith",
        "hourly_rate": None,
        "annual_salary": 60000.00,  # ~$28.85/hr based on 2080 hours
        "hire_date": "2024-01-01",
        "province_of_employment": "BC",
    }


@pytest.fixture
def new_hire_employee():
    """Create an employee hired less than 30 days ago."""
    recent_date = (date.today() - timedelta(days=20)).isoformat()
    return {
        "id": "emp-003",
        "first_name": "New",
        "last_name": "Hire",
        "hourly_rate": 20.00,
        "annual_salary": None,
        "hire_date": recent_date,
        "province_of_employment": "BC",
    }


# =============================================================================
# CONFIG LOADING TESTS
# =============================================================================


class TestConfigLoading:
    """Tests for configuration loading."""

    def test_get_bc_config(self):
        """Should load BC config from file."""
        config = get_config("BC")
        assert config.province_code == "BC"
        assert config.formula_type == "30_day_average"
        assert config.eligibility.min_employment_days == 30

    def test_get_on_config(self):
        """Should load Ontario config - no 30-day requirement."""
        config = get_config("ON")
        assert config.province_code == "ON"
        assert config.formula_type == "4_week_average"
        assert config.eligibility.min_employment_days == 0
        assert config.eligibility.require_last_first_rule is True

    def test_get_ab_config(self):
        """Should load Alberta config."""
        config = get_config("AB")
        assert config.province_code == "AB"
        assert config.formula_type == "4_week_average_daily"
        assert config.eligibility.min_employment_days == 30

    def test_unknown_province_fallback(self):
        """Unknown province should fall back to BC config."""
        config = get_config("XX")
        assert config.formula_type == "30_day_average"  # BC default


# =============================================================================
# ELIGIBILITY TESTS (CONFIG-DRIVEN)
# =============================================================================


class TestEligibilityCheck:
    """Tests for config-driven eligibility rules."""

    def test_bc_eligible_employee(self, calculator, hourly_employee):
        """BC: Employee hired >30 days ago should be eligible."""
        config = make_bc_config()
        holiday_date = date(2025, 7, 1)

        result = calculator._is_eligible_for_holiday_pay(hourly_employee, holiday_date, config)

        assert result is True

    def test_bc_ineligible_new_hire(self, calculator, new_hire_employee):
        """BC: Employee hired <30 days ago should not be eligible."""
        config = make_bc_config()
        holiday_date = date.today()

        result = calculator._is_eligible_for_holiday_pay(new_hire_employee, holiday_date, config)

        assert result is False

    def test_ontario_no_min_days_requirement(self, calculator, new_hire_employee):
        """Ontario: No minimum employment days requirement."""
        config = make_on_config()
        holiday_date = date.today()

        # Even a new hire should be eligible in Ontario (no 30-day rule)
        result = calculator._is_eligible_for_holiday_pay(new_hire_employee, holiday_date, config)

        assert result is True  # Ontario has min_employment_days = 0

    def test_exactly_30_days(self, calculator):
        """BC: Employee hired exactly 30 days ago should be eligible."""
        config = make_bc_config()
        holiday_date = date(2025, 2, 1)
        employee = {
            "id": "emp-exact",
            "hire_date": "2025-01-02",  # Exactly 30 days before Feb 1
        }

        result = calculator._is_eligible_for_holiday_pay(employee, holiday_date, config)

        assert result is True

    def test_no_hire_date(self, calculator):
        """Employee without hire_date should be assumed eligible."""
        config = make_bc_config()
        employee = {"id": "emp-no-date"}
        holiday_date = date(2025, 1, 1)

        result = calculator._is_eligible_for_holiday_pay(employee, holiday_date, config)

        assert result is True


# =============================================================================
# FORMULA TESTS
# =============================================================================


class TestBCFormula:
    """Tests for BC holiday pay formula: default_daily_hours × hourly_rate."""

    def test_bc_hourly_employee(self, calculator, hourly_employee):
        """BC formula should calculate 8h × hourly_rate."""
        config = make_bc_config()
        daily_pay = calculator._apply_30_day_average(
            hourly_employee, config.formula_params.default_daily_hours
        )

        # 8h × $25/hr = $200
        assert daily_pay == Decimal("200")

    def test_bc_salaried_employee(self, calculator, salaried_employee):
        """BC formula should derive hourly rate from salary for calculation."""
        config = make_bc_config()
        daily_pay = calculator._apply_30_day_average(
            salaried_employee, config.formula_params.default_daily_hours
        )

        # 8h × ($60000/2080) = 8 × $28.846... ≈ $230.77
        expected = Decimal("8") * (Decimal("60000") / Decimal("2080"))
        assert daily_pay == expected


class TestCurrentPeriodFormula:
    """Tests for current period daily formula."""

    def test_bi_weekly(self, calculator):
        """Current period formula for bi-weekly pay period."""
        current_gross = Decimal("2000")
        pay_frequency = "bi_weekly"

        daily_pay = calculator._apply_current_period_daily(current_gross, pay_frequency)

        # $2000 / 10 work days = $200
        assert daily_pay == Decimal("200")

    def test_weekly(self, calculator):
        """Current period formula for weekly pay period."""
        current_gross = Decimal("1000")
        pay_frequency = "weekly"

        daily_pay = calculator._apply_current_period_daily(current_gross, pay_frequency)

        # $1000 / 5 work days = $200
        assert daily_pay == Decimal("200")

    def test_monthly(self, calculator):
        """Current period formula for monthly pay period."""
        current_gross = Decimal("4000")
        pay_frequency = "monthly"

        daily_pay = calculator._apply_current_period_daily(current_gross, pay_frequency)

        # $4000 / 21.67 work days ≈ $184.59
        expected = current_gross / WORK_DAYS_PER_PERIOD["monthly"]
        assert daily_pay == expected


class TestOntarioFormula:
    """Tests for Ontario formula: (past 4 weeks wages + vacation) / 20."""

    def test_ontario_with_history(self, calculator, mock_supabase):
        """Ontario formula with historical payroll data."""
        # Mock historical data query
        mock_supabase.table.return_value.select.return_value.eq.return_value.neq.return_value.gte.return_value.lt.return_value.in_.return_value.execute.return_value.data = [
            {"gross_regular": 1000, "gross_overtime": 200, "vacation_pay_paid": 50},
            {"gross_regular": 1000, "gross_overtime": 150, "vacation_pay_paid": 50},
        ]

        employee = {"id": "emp-001", "hourly_rate": 25.00}

        daily_pay = calculator._apply_4_week_average(
            employee_id="emp-001",
            holiday_date=date(2025, 7, 1),
            current_run_id="run-001",
            divisor=20,
            include_vacation_pay=True,
            employee_fallback=employee,
            new_employee_fallback="pro_rated",
        )

        # total_wages = (1000+200) + (1000+150) = 2350
        # vacation_pay = 50 + 50 = 100
        # (2350 + 100) / 20 = $122.50
        expected = (Decimal("2350") + Decimal("100")) / Decimal("20")
        assert daily_pay == expected

    def test_ontario_no_history_fallback(self, calculator, mock_supabase):
        """Ontario formula should fall back to 30-day avg when no history."""
        # Mock empty historical data
        mock_supabase.table.return_value.select.return_value.eq.return_value.neq.return_value.gte.return_value.lt.return_value.in_.return_value.execute.return_value.data = []

        employee = {"id": "emp-001", "hourly_rate": 25.00}

        daily_pay = calculator._apply_4_week_average(
            employee_id="emp-001",
            holiday_date=date(2025, 7, 1),
            current_run_id="run-001",
            divisor=20,
            include_vacation_pay=True,
            employee_fallback=employee,
            new_employee_fallback="pro_rated",
        )

        # Falls back to 30-day avg: 8h × $25 = $200
        assert daily_pay == Decimal("200")


# =============================================================================
# PREMIUM PAY TESTS
# =============================================================================


class TestPremiumPay:
    """Tests for premium pay calculation: hours × rate × premium_rate."""

    def test_premium_hourly_employee(self, calculator, hourly_employee):
        """Premium pay for hourly employee working on holiday."""
        config = make_bc_config()
        hours_worked = Decimal("8")

        premium = calculator._calculate_premium_pay(hourly_employee, hours_worked, config)

        # 8h × $25 × 1.5 = $300
        assert premium == Decimal("300")

    def test_premium_salaried_employee(self, calculator, salaried_employee):
        """Premium pay for salaried employee working on holiday."""
        config = make_bc_config()
        hours_worked = Decimal("8")

        premium = calculator._calculate_premium_pay(salaried_employee, hours_worked, config)

        # 8h × ($60000/2080) × 1.5
        hourly_rate = Decimal("60000") / Decimal("2080")
        expected = hours_worked * hourly_rate * Decimal("1.5")
        assert premium == expected

    def test_premium_partial_hours(self, calculator, hourly_employee):
        """Premium pay for partial hours worked."""
        config = make_bc_config()
        hours_worked = Decimal("4.5")

        premium = calculator._calculate_premium_pay(hourly_employee, hours_worked, config)

        # 4.5h × $25 × 1.5 = $168.75
        assert premium == Decimal("168.75")


# =============================================================================
# MAIN CALCULATE HOLIDAY PAY TESTS
# =============================================================================


class TestCalculateHolidayPay:
    """Tests for the main calculate_holiday_pay method."""

    def test_bc_hourly_single_holiday_not_worked(self, calculator, hourly_employee):
        """BC hourly employee with one holiday, not worked."""
        holidays = [{"holiday_date": "2025-07-01", "name": "Canada Day", "province": "BC"}]

        result = calculator.calculate_holiday_pay(
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

    def test_bc_hourly_single_holiday_worked(self, calculator, hourly_employee):
        """BC hourly employee with one holiday, worked 8 hours."""
        holidays = [{"holiday_date": "2025-07-01", "name": "Canada Day", "province": "BC"}]
        work_entries = [{"holidayDate": "2025-07-01", "hoursWorked": 8}]

        result = calculator.calculate_holiday_pay(
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

    def test_salaried_holiday_not_worked(self, calculator, salaried_employee):
        """Salaried employee: skip Regular, $0 Premium when not worked."""
        holidays = [{"holiday_date": "2025-07-01", "name": "Canada Day", "province": "BC"}]

        result = calculator.calculate_holiday_pay(
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

    def test_salaried_holiday_worked(self, calculator, salaried_employee):
        """Salaried employee working on holiday gets Premium pay only."""
        holidays = [{"holiday_date": "2025-07-01", "name": "Canada Day", "province": "BC"}]
        work_entries = [{"holidayDate": "2025-07-01", "hoursWorked": 8}]

        result = calculator.calculate_holiday_pay(
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

    def test_multiple_holidays_in_period(self, calculator, hourly_employee):
        """Multiple holidays in the same pay period."""
        holidays = [
            {"holiday_date": "2025-12-25", "name": "Christmas Day", "province": "BC"},
            {"holiday_date": "2025-12-26", "name": "Boxing Day", "province": "BC"},
        ]
        work_entries = [{"holidayDate": "2025-12-25", "hoursWorked": 4}]

        result = calculator.calculate_holiday_pay(
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

    def test_bc_new_hire_ineligible(self, calculator, new_hire_employee):
        """BC: New hire <30 days should not get Regular pay, but can get Premium."""
        holiday_date = date.today()
        holidays = [{"holiday_date": holiday_date.isoformat(), "name": "Test Holiday", "province": "BC"}]
        work_entries = [{"holidayDate": holiday_date.isoformat(), "hoursWorked": 8}]

        result = calculator.calculate_holiday_pay(
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

    def test_no_holidays_in_period(self, calculator, hourly_employee):
        """No holidays in the pay period."""
        result = calculator.calculate_holiday_pay(
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


# =============================================================================
# CALCULATION DETAILS TESTS
# =============================================================================


class TestCalculationDetails:
    """Tests for calculation details in the result."""

    def test_details_include_config_info(self, calculator, hourly_employee):
        """Details should include config information."""
        holidays = [{"holiday_date": "2025-07-01", "name": "Canada Day", "province": "BC"}]

        result = calculator.calculate_holiday_pay(
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

    def test_details_include_holiday_info(self, calculator, hourly_employee):
        """Details should include information about each holiday."""
        holidays = [{"holiday_date": "2025-07-01", "name": "Canada Day", "province": "BC"}]
        work_entries = [{"holidayDate": "2025-07-01", "hoursWorked": 4}]

        result = calculator.calculate_holiday_pay(
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


# =============================================================================
# FORMULA SELECTION TESTS
# =============================================================================


class TestFormulaSelection:
    """Tests for correct formula selection by province via config."""

    def test_ontario_uses_4_week_formula(self, mock_supabase):
        """Ontario config should specify 4_week_average formula."""
        config = get_config("ON")
        assert config.formula_type == "4_week_average"
        assert config.formula_params.divisor == 20
        assert config.formula_params.include_vacation_pay is True

    def test_alberta_uses_4_week_daily(self):
        """Alberta config should specify 4_week_average_daily formula."""
        config = get_config("AB")
        assert config.formula_type == "4_week_average_daily"

    def test_bc_uses_30_day_average(self):
        """BC config should specify 30_day_average formula."""
        config = get_config("BC")
        assert config.formula_type == "30_day_average"

    def test_unknown_province_uses_bc_default(self):
        """Unknown provinces should fall back to BC formula."""
        config = get_config("XX")
        assert config.formula_type == "30_day_average"


# =============================================================================
# NEW EMPLOYEE FALLBACK TESTS
# =============================================================================


def make_sk_config() -> HolidayPayConfig:
    """Create Saskatchewan test config with pro_rated fallback."""
    return HolidayPayConfig(
        province_code="SK",
        formula_type="5_percent_28_days",
        formula_params=HolidayPayFormulaParams(
            lookback_days=28,
            percentage=Decimal("0.05"),
            include_vacation_pay=True,
            include_previous_holiday_pay=True,
            new_employee_fallback="pro_rated",
        ),
        eligibility=HolidayPayEligibility(
            min_employment_days=0,
            require_last_first_rule=False,
        ),
        premium_rate=Decimal("1.5"),
    )


def make_qc_config() -> HolidayPayConfig:
    """Create Quebec test config with pro_rated fallback."""
    return HolidayPayConfig(
        province_code="QC",
        formula_type="30_day_average",
        formula_params=HolidayPayFormulaParams(
            lookback_days=30,
            method="total_wages_div_days",
            default_daily_hours=Decimal("8"),
            new_employee_fallback="pro_rated",
        ),
        eligibility=HolidayPayEligibility(
            min_employment_days=0,
            require_last_first_rule=False,
        ),
        premium_rate=Decimal("1.5"),
    )


class TestNewEmployeeFallback:
    """Tests for new_employee_fallback config behavior.

    Tests the difference between:
    - "pro_rated": Use current period gross or 30-day avg fallback
    - "ineligible": Return $0 when no historical data
    """

    @pytest.fixture
    def new_hire_sk(self):
        """New employee in Saskatchewan (no 30-day min)."""
        return {
            "id": "emp-sk-new",
            "first_name": "New",
            "last_name": "Saskatchewan",
            "hourly_rate": 20.00,
            "annual_salary": None,
            "hire_date": (date.today() - timedelta(days=10)).isoformat(),
            "province_of_employment": "SK",
        }

    @pytest.fixture
    def new_hire_ab(self):
        """New employee in Alberta (30-day min required)."""
        return {
            "id": "emp-ab-new",
            "first_name": "New",
            "last_name": "Alberta",
            "hourly_rate": 25.00,
            "annual_salary": None,
            "hire_date": (date.today() - timedelta(days=10)).isoformat(),
            "province_of_employment": "AB",
        }

    def test_sk_new_employee_pro_rated_uses_current_gross(self, mock_supabase):
        """SK: New employee with no history uses current_period_gross (pro_rated)."""
        # Setup calculator with SK config
        sk_loader = MockConfigLoader({"SK": make_sk_config()})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=sk_loader,
        )

        # Mock empty historical data
        mock_supabase.table.return_value.select.return_value.eq.return_value.neq.return_value.gte.return_value.lt.return_value.in_.return_value.execute.return_value.data = []

        new_hire = {
            "id": "emp-sk-new",
            "first_name": "New",
            "last_name": "SK",
            "hourly_rate": 20.00,
            "hire_date": (date.today() - timedelta(days=10)).isoformat(),
        }

        holiday_date = date.today()
        holidays = [{"holiday_date": holiday_date.isoformat(), "name": "Test Holiday", "province": "SK"}]

        result = calculator.calculate_holiday_pay(
            employee=new_hire,
            province="SK",
            pay_frequency="bi_weekly",
            period_start=holiday_date - timedelta(days=7),
            period_end=holiday_date + timedelta(days=7),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("1600"),  # Use this as base
            current_run_id="run-001",
        )

        # SK pro_rated: uses current_period_gross × 5% = $1600 × 0.05 = $80
        assert result.regular_holiday_pay == Decimal("80")
        assert result.premium_holiday_pay == Decimal("0")

    def test_ab_new_employee_ineligible_returns_zero(self, mock_supabase):
        """AB: New employee with no history returns $0 (ineligible fallback)."""
        # Setup calculator with AB config (ineligible fallback)
        ab_loader = MockConfigLoader({"AB": make_ab_config()})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=ab_loader,
        )

        # Mock empty historical data
        mock_supabase.table.return_value.select.return_value.eq.return_value.neq.return_value.gte.return_value.lt.return_value.in_.return_value.execute.return_value.data = []

        # Employee with >30 days employment (eligible by min_days) but no historical payroll
        eligible_no_history = {
            "id": "emp-ab-eligible",
            "first_name": "Eligible",
            "last_name": "NoHistory",
            "hourly_rate": 25.00,
            "hire_date": (date.today() - timedelta(days=45)).isoformat(),
        }

        holiday_date = date.today()
        holidays = [{"holiday_date": holiday_date.isoformat(), "name": "Test Holiday", "province": "AB"}]

        result = calculator.calculate_holiday_pay(
            employee=eligible_no_history,
            province="AB",
            pay_frequency="bi_weekly",
            period_start=holiday_date - timedelta(days=7),
            period_end=holiday_date + timedelta(days=7),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("2000"),
            current_run_id="run-001",
        )

        # AB ineligible: no historical data → $0
        assert result.regular_holiday_pay == Decimal("0")

    def test_on_new_employee_pro_rated_uses_30_day_avg(self, mock_supabase):
        """ON: New employee with no history uses 30-day avg fallback (pro_rated)."""
        # Setup calculator with ON config
        on_loader = MockConfigLoader({"ON": make_on_config()})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=on_loader,
        )

        # Mock empty historical data
        mock_supabase.table.return_value.select.return_value.eq.return_value.neq.return_value.gte.return_value.lt.return_value.in_.return_value.execute.return_value.data = []

        new_hire = {
            "id": "emp-on-new",
            "first_name": "New",
            "last_name": "Ontario",
            "hourly_rate": 22.00,
            "hire_date": (date.today() - timedelta(days=5)).isoformat(),
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
            current_period_gross=Decimal("1760"),
            current_run_id="run-001",
        )

        # ON pro_rated: falls back to 30-day avg: 8h × $22 = $176
        assert result.regular_holiday_pay == Decimal("176")

    def test_bc_new_hire_ineligible_by_min_days(self, mock_supabase):
        """BC: New hire <30 days is ineligible by min_employment_days."""
        bc_loader = MockConfigLoader({"BC": make_bc_config()})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=bc_loader,
        )

        new_hire = {
            "id": "emp-bc-new",
            "first_name": "New",
            "last_name": "BC",
            "hourly_rate": 20.00,
            "hire_date": (date.today() - timedelta(days=15)).isoformat(),
        }

        holiday_date = date.today()
        holidays = [{"holiday_date": holiday_date.isoformat(), "name": "Test Holiday", "province": "BC"}]

        result = calculator.calculate_holiday_pay(
            employee=new_hire,
            province="BC",
            pay_frequency="bi_weekly",
            period_start=holiday_date - timedelta(days=7),
            period_end=holiday_date + timedelta(days=7),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("1600"),
            current_run_id="run-001",
        )

        # BC: <30 days employed → ineligible (not due to fallback, but min_days)
        assert result.regular_holiday_pay == Decimal("0")
        # Check details show ineligibility
        assert result.calculation_details["holidays"][0]["eligible"] is False

    def test_qc_new_employee_eligible_no_min_days(self, mock_supabase):
        """QC: New employee is eligible (no min employment days)."""
        qc_loader = MockConfigLoader({"QC": make_qc_config()})
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
            config_loader=qc_loader,
        )

        new_hire = {
            "id": "emp-qc-new",
            "first_name": "New",
            "last_name": "Quebec",
            "hourly_rate": 18.00,
            "hire_date": (date.today() - timedelta(days=5)).isoformat(),
        }

        holiday_date = date.today()
        holidays = [{"holiday_date": holiday_date.isoformat(), "name": "Test Holiday", "province": "QC"}]

        result = calculator.calculate_holiday_pay(
            employee=new_hire,
            province="QC",
            pay_frequency="bi_weekly",
            period_start=holiday_date - timedelta(days=7),
            period_end=holiday_date + timedelta(days=7),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("1440"),
            current_run_id="run-001",
        )

        # QC: min_employment_days=0, uses 30-day avg: 8h × $18 = $144
        assert result.regular_holiday_pay == Decimal("144")
        assert result.calculation_details["holidays"][0]["eligible"] is True


# =============================================================================
# ALL PROVINCES CONFIG LOADING TESTS
# =============================================================================


class TestAllProvincesConfigLoading:
    """Tests for loading configs for all provinces and territories."""

    ALL_PROVINCES = [
        "ON", "BC", "AB", "SK", "QC", "MB",
        "NB", "NS", "PE", "NL", "NT", "NU", "YT", "Federal"
    ]

    def test_all_provinces_load_successfully(self):
        """All provinces should load without errors."""
        for province in self.ALL_PROVINCES:
            config = get_config(province)
            assert config is not None, f"Config for {province} should not be None"
            assert config.province_code == province, f"Province code mismatch for {province}"

    def test_all_provinces_have_valid_formula_type(self):
        """All provinces should have a valid formula_type."""
        valid_formulas = {
            "4_week_average",
            "30_day_average",
            "4_week_average_daily",
            "5_percent_28_days",
            "current_period_daily",
        }
        for province in self.ALL_PROVINCES:
            config = get_config(province)
            assert config.formula_type in valid_formulas, (
                f"{province} has invalid formula_type: {config.formula_type}"
            )

    def test_all_provinces_have_new_employee_fallback(self):
        """All provinces should have new_employee_fallback defined."""
        for province in self.ALL_PROVINCES:
            config = get_config(province)
            fallback = config.formula_params.new_employee_fallback
            assert fallback in ("pro_rated", "ineligible"), (
                f"{province} should have valid new_employee_fallback, got: {fallback}"
            )

    def test_sk_uses_5_percent_formula(self):
        """SK should use the 5_percent_28_days formula."""
        config = get_config("SK")
        assert config.formula_type == "5_percent_28_days"
        assert config.formula_params.percentage == Decimal("0.05")
        assert config.formula_params.include_vacation_pay is True
        assert config.formula_params.include_previous_holiday_pay is True
        assert config.formula_params.new_employee_fallback == "pro_rated"

    def test_qc_has_no_min_employment_days(self):
        """QC should have min_employment_days = 0."""
        config = get_config("QC")
        assert config.eligibility.min_employment_days == 0
        assert config.formula_params.new_employee_fallback == "pro_rated"

    def test_nb_has_90_day_requirement(self):
        """NB should require 90 days of employment."""
        config = get_config("NB")
        assert config.eligibility.min_employment_days == 90

    def test_pro_rated_provinces(self):
        """Provinces with pro_rated fallback: SK, ON, QC."""
        pro_rated_provinces = ["SK", "ON", "QC"]
        for province in pro_rated_provinces:
            config = get_config(province)
            assert config.formula_params.new_employee_fallback == "pro_rated", (
                f"{province} should use pro_rated fallback"
            )

    def test_ineligible_provinces(self):
        """Provinces with ineligible fallback: BC, AB, and others."""
        ineligible_provinces = ["BC", "AB", "MB", "NB", "NS", "PE", "NL", "NT", "NU", "YT", "Federal"]
        for province in ineligible_provinces:
            config = get_config(province)
            assert config.formula_params.new_employee_fallback == "ineligible", (
                f"{province} should use ineligible fallback"
            )


# =============================================================================
# SASKATCHEWAN INTEGRATION TESTS
# =============================================================================


class TestSaskatchewanIntegration:
    """Integration tests for Saskatchewan 5% formula through calculate_holiday_pay()."""

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


# =============================================================================
# NB 90-DAY REQUIREMENT TESTS
# =============================================================================


class TestNBEligibility:
    """Tests for New Brunswick's 90-day employment requirement."""

    def test_nb_employee_under_90_days_ineligible(self, mock_supabase):
        """NB: Employee with <90 days employment is not eligible."""
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
        )

        # Employee hired 60 days ago (< 90 days required)
        employee = {
            "id": "emp-nb-new",
            "first_name": "New",
            "last_name": "Brunswick",
            "hourly_rate": 20.00,
            "hire_date": (date.today() - timedelta(days=60)).isoformat(),
        }

        holiday_date = date.today()
        holidays = [{"holiday_date": holiday_date.isoformat(), "name": "Test Holiday", "province": "NB"}]

        result = calculator.calculate_holiday_pay(
            employee=employee,
            province="NB",
            pay_frequency="bi_weekly",
            period_start=holiday_date - timedelta(days=7),
            period_end=holiday_date + timedelta(days=7),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("1600"),
            current_run_id="run-001",
        )

        # NB: <90 days employed → ineligible for regular pay
        assert result.regular_holiday_pay == Decimal("0")
        assert result.calculation_details["holidays"][0]["eligible"] is False
        assert "< 90 days" in result.calculation_details["holidays"][0].get("ineligibility_reason", "")

    def test_nb_employee_over_90_days_eligible(self, mock_supabase):
        """NB: Employee with ≥90 days employment is eligible."""
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
        )

        # Employee hired 100 days ago (≥ 90 days)
        employee = {
            "id": "emp-nb-senior",
            "first_name": "Senior",
            "last_name": "Brunswick",
            "hourly_rate": 22.00,
            "hire_date": (date.today() - timedelta(days=100)).isoformat(),
        }

        holiday_date = date.today()
        holidays = [{"holiday_date": holiday_date.isoformat(), "name": "Test Holiday", "province": "NB"}]

        result = calculator.calculate_holiday_pay(
            employee=employee,
            province="NB",
            pay_frequency="bi_weekly",
            period_start=holiday_date - timedelta(days=7),
            period_end=holiday_date + timedelta(days=7),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("1760"),
            current_run_id="run-002",
        )

        # NB: ≥90 days employed → eligible
        # Uses 30_day_average: 8h × $22 = $176
        assert result.regular_holiday_pay == Decimal("176")
        assert result.calculation_details["holidays"][0]["eligible"] is True

    def test_nb_exactly_90_days_eligible(self, mock_supabase):
        """NB: Employee with exactly 90 days employment is eligible."""
        calculator = HolidayPayCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company",
        )

        holiday_date = date(2025, 4, 1)
        # Hired exactly 90 days before holiday
        hire_date = holiday_date - timedelta(days=90)

        employee = {
            "id": "emp-nb-exact",
            "first_name": "Exact",
            "last_name": "Ninety",
            "hourly_rate": 20.00,
            "hire_date": hire_date.isoformat(),
        }

        holidays = [{"holiday_date": holiday_date.isoformat(), "name": "Test Holiday", "province": "NB"}]

        result = calculator.calculate_holiday_pay(
            employee=employee,
            province="NB",
            pay_frequency="bi_weekly",
            period_start=holiday_date - timedelta(days=7),
            period_end=holiday_date + timedelta(days=7),
            holidays_in_period=holidays,
            holiday_work_entries=[],
            current_period_gross=Decimal("1600"),
            current_run_id="run-003",
        )

        # NB: exactly 90 days → eligible
        assert result.regular_holiday_pay == Decimal("160")  # 8h × $20
        assert result.calculation_details["holidays"][0]["eligible"] is True
