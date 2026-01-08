"""
Shared fixtures for payroll calculator tests.

Provides common test data and calculator instances for CPP, EI,
Federal Tax, Provincial Tax, and Holiday Pay calculations.
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import NamedTuple
from unittest.mock import MagicMock

import pytest

from app.models.holiday_pay_config import (
    HolidayPayConfig,
    HolidayPayEligibility,
    HolidayPayFormulaParams,
)
from app.models.payroll import PayFrequency, Province
from app.services.payroll.cpp_calculator import CPPCalculator
from app.services.payroll.ei_calculator import EICalculator
from app.services.payroll.federal_tax_calculator import FederalTaxCalculator
from app.services.payroll.payroll_engine import EmployeePayrollInput, PayrollEngine
from app.services.payroll.provincial_tax_calculator import ProvincialTaxCalculator
from app.services.payroll_run.holiday_pay_calculator import HolidayPayCalculator

# =============================================================================
# Test Matrix Constants
# =============================================================================

# 2025 CPP Parameters
CPP_YMPE = Decimal("71300.00")
CPP_YAMPE = Decimal("81200.00")
CPP_BASIC_EXEMPTION = Decimal("3500.00")
CPP_BASE_RATE = Decimal("0.0595")
CPP_ADDITIONAL_RATE = Decimal("0.04")
CPP_MAX_BASE = Decimal("4034.10")
CPP_MAX_ADDITIONAL = Decimal("396.00")

# 2025 EI Parameters
EI_MIE = Decimal("65700.00")
EI_RATE = Decimal("0.0164")
EI_MAX = Decimal("1077.48")

# 2025 Federal BPA
FEDERAL_BPA = Decimal("16129.00")

# Provincial BPA 2025 (using Province enum)
PROVINCIAL_BPA = {
    Province.AB: Decimal("22323.00"),
    Province.BC: Decimal("12932.00"),
    Province.MB: Decimal("15780.00"),
    Province.NB: Decimal("13396.00"),
    Province.NL: Decimal("11067.00"),
    Province.NS: Decimal("11744.00"),
    Province.NT: Decimal("17842.00"),
    Province.NU: Decimal("19274.00"),
    Province.ON: Decimal("12747.00"),
    Province.PE: Decimal("14250.00"),
    Province.SK: Decimal("18991.00"),
    Province.YT: Decimal("16129.00"),
}

# Income levels for testing
INCOME_LEVELS = {
    "very_low": Decimal("18000"),      # Below tax threshold (~$692/biweekly)
    "low": Decimal("35000"),           # First tax bracket (~$1,346/biweekly)
    "medium": Decimal("60000"),        # Second tax bracket (~$2,308/biweekly)
    "high": Decimal("85000"),          # Third bracket, CPP2 range (~$3,269/biweekly)
    "very_high": Decimal("150000"),    # Top brackets, all maxes (~$5,769/biweekly)
}


class ExpectedRange(NamedTuple):
    """Expected value range for test validation."""
    min_value: Decimal
    max_value: Decimal


# =============================================================================
# Test Matrix Helper Functions
# =============================================================================


def create_standard_input(
    province: Province,
    pay_frequency: PayFrequency,
    annual_income: Decimal,
    pay_date: date = date(2025, 7, 18),
    ytd_gross: Decimal = Decimal("0"),
    ytd_cpp_base: Decimal = Decimal("0"),
    ytd_cpp_additional: Decimal = Decimal("0"),
    ytd_ei: Decimal = Decimal("0"),
    is_cpp_exempt: bool = False,
    is_ei_exempt: bool = False,
    cpp2_exempt: bool = False,
    rrsp: Decimal = Decimal("0"),
) -> EmployeePayrollInput:
    """Create a standard employee payroll input for testing."""
    periods = pay_frequency.periods_per_year
    gross_per_period = (annual_income / periods).quantize(Decimal("0.01"))

    return EmployeePayrollInput(
        employee_id=f"matrix_{province.value}_{pay_frequency.value}_{annual_income}",
        province=province,
        pay_frequency=pay_frequency,
        pay_date=pay_date,
        gross_regular=gross_per_period,
        federal_claim_amount=FEDERAL_BPA,
        provincial_claim_amount=PROVINCIAL_BPA[province],
        rrsp_per_period=rrsp,
        ytd_gross=ytd_gross,
        ytd_pensionable_earnings=ytd_gross,
        ytd_insurable_earnings=ytd_gross,
        ytd_cpp_base=ytd_cpp_base,
        ytd_cpp_additional=ytd_cpp_additional,
        ytd_ei=ytd_ei,
        is_cpp_exempt=is_cpp_exempt,
        is_ei_exempt=is_ei_exempt,
        cpp2_exempt=cpp2_exempt,
    )


@pytest.fixture
def payroll_engine():
    """PayrollEngine instance for 2025."""
    return PayrollEngine(year=2025)

# =============================================================================
# CPP Calculator Fixtures
# =============================================================================


@pytest.fixture
def cpp_calc_biweekly():
    """CPP calculator for bi-weekly pay (26 periods)."""
    return CPPCalculator(pay_periods_per_year=26, year=2025)


@pytest.fixture
def cpp_calc_weekly():
    """CPP calculator for weekly pay (52 periods)."""
    return CPPCalculator(pay_periods_per_year=52, year=2025)


@pytest.fixture
def cpp_calc_monthly():
    """CPP calculator for monthly pay (12 periods)."""
    return CPPCalculator(pay_periods_per_year=12, year=2025)


# =============================================================================
# EI Calculator Fixtures
# =============================================================================


@pytest.fixture
def ei_calc_biweekly():
    """EI calculator for bi-weekly pay (26 periods)."""
    return EICalculator(pay_periods_per_year=26, year=2025)


@pytest.fixture
def ei_calc_weekly():
    """EI calculator for weekly pay (52 periods)."""
    return EICalculator(pay_periods_per_year=52, year=2025)


@pytest.fixture
def ei_calc_monthly():
    """EI calculator for monthly pay (12 periods)."""
    return EICalculator(pay_periods_per_year=12, year=2025)


# =============================================================================
# Federal Tax Calculator Fixtures
# =============================================================================


@pytest.fixture
def federal_calc_jan2025():
    """Federal tax calculator for January 2025 (15% lowest rate)."""
    return FederalTaxCalculator(
        pay_periods_per_year=26,
        year=2025,
        pay_date=date(2025, 3, 15)
    )


@pytest.fixture
def federal_calc_jul2025():
    """Federal tax calculator for July 2025 (14% lowest rate)."""
    return FederalTaxCalculator(
        pay_periods_per_year=26,
        year=2025,
        pay_date=date(2025, 7, 15)
    )


# =============================================================================
# Provincial Tax Calculator Fixtures
# =============================================================================


@pytest.fixture
def ontario_calc():
    """Ontario provincial tax calculator."""
    return ProvincialTaxCalculator("ON", pay_periods_per_year=26, year=2025)


@pytest.fixture
def bc_calc():
    """BC provincial tax calculator."""
    return ProvincialTaxCalculator("BC", pay_periods_per_year=26, year=2025)


@pytest.fixture
def alberta_calc():
    """Alberta provincial tax calculator."""
    return ProvincialTaxCalculator("AB", pay_periods_per_year=26, year=2025)


# =============================================================================
# Common Test Data
# =============================================================================


@pytest.fixture
def standard_employee_input():
    """Standard test employee: Ontario, $60k, bi-weekly."""
    return {
        "gross_per_period": Decimal("2307.69"),
        "province": "ON",
        "pay_periods": 26,
        "federal_claim": Decimal("16129.00"),
        "provincial_claim": Decimal("12747.00"),
        "ytd_gross": Decimal("0"),
        "ytd_cpp": Decimal("0"),
        "ytd_ei": Decimal("0"),
    }


# =============================================================================
# 2025 Tax Constants Reference
# =============================================================================


# Provincial BPA reference data for 2025
PROVINCIAL_BPA_2025 = {
    "AB": Decimal("22323.00"),
    "BC": Decimal("12932.00"),
    "MB": Decimal("15780.00"),
    "NB": Decimal("13396.00"),
    "NL": Decimal("11067.00"),
    "NS": Decimal("11744.00"),
    "NT": Decimal("17842.00"),
    "NU": Decimal("19274.00"),
    "ON": Decimal("12747.00"),
    "PE": Decimal("14250.00"),
    "SK": Decimal("18991.00"),
    "YT": Decimal("16129.00"),
}


@pytest.fixture
def provincial_bpa():
    """Provincial BPA reference data for 2025."""
    return PROVINCIAL_BPA_2025


# CPP parameters for 2025
CPP_PARAMS_2025 = {
    "ympe": Decimal("71300.00"),
    "yampe": Decimal("81200.00"),
    "basic_exemption": Decimal("3500.00"),
    "base_rate": Decimal("0.0595"),
    "additional_rate": Decimal("0.04"),
    "max_base_contribution": Decimal("4034.10"),
    "max_additional_contribution": Decimal("396.00"),
}


@pytest.fixture
def cpp_params():
    """CPP parameters for 2025."""
    return CPP_PARAMS_2025


# EI parameters for 2025
EI_PARAMS_2025 = {
    "mie": Decimal("65700.00"),
    "employee_rate": Decimal("0.0164"),
    "employer_multiplier": Decimal("1.4"),
    "max_employee_premium": Decimal("1077.48"),
    "max_employer_premium": Decimal("1508.47"),
}


@pytest.fixture
def ei_params():
    """EI parameters for 2025."""
    return EI_PARAMS_2025


# Federal tax parameters for 2025
FEDERAL_PARAMS_2025 = {
    "bpaf": Decimal("16129.00"),
    "cea": Decimal("1471.00"),
    "lowest_rate_jan_jun": Decimal("0.15"),
    "lowest_rate_jul_onwards": Decimal("0.14"),
}


@pytest.fixture
def federal_params():
    """Federal tax parameters for 2025."""
    return FEDERAL_PARAMS_2025


# All province codes for parametrized tests
ALL_PROVINCE_CODES = ["AB", "BC", "MB", "NB", "NL", "NS", "NT", "NU", "ON", "PE", "SK", "YT"]


@pytest.fixture
def all_provinces():
    """All province codes for parametrized tests."""
    return ALL_PROVINCE_CODES


# =============================================================================
# Holiday Pay Calculator Fixtures
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


def make_pe_config() -> HolidayPayConfig:
    """Create PEI test config with min_days_worked_in_period."""
    return HolidayPayConfig(
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
            require_last_first_rule=True,
            min_days_worked_in_period=15,
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


@pytest.fixture
def mock_supabase():
    """Create a mock Supabase client."""
    return MagicMock()


@pytest.fixture
def mock_config_loader():
    """Create a mock config loader."""
    return MockConfigLoader()


@pytest.fixture
def holiday_calculator(mock_supabase, mock_config_loader):
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
