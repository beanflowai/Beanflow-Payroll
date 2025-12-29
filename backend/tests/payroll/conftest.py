"""
Shared fixtures for payroll calculator tests.

Provides common test data and calculator instances for CPP, EI,
Federal Tax, and Provincial Tax calculations.
"""

import pytest
from datetime import date
from decimal import Decimal

from app.services.payroll.cpp_calculator import CPPCalculator
from app.services.payroll.ei_calculator import EICalculator
from app.services.payroll.federal_tax_calculator import FederalTaxCalculator
from app.services.payroll.provincial_tax_calculator import ProvincialTaxCalculator


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
