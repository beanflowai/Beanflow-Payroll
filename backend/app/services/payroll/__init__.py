"""
Payroll Services Module

Contains tax calculation services, payroll processing, and related utilities.
"""

from app.services.payroll.tax_tables import (
    get_federal_config,
    get_cpp_config,
    get_ei_config,
    get_province_config,
    get_all_provinces,
    find_tax_bracket,
    calculate_dynamic_bpa,
    validate_tax_tables,
)

from app.services.payroll.cpp_calculator import CPPCalculator, CppContribution
from app.services.payroll.ei_calculator import EICalculator, EiPremium
from app.services.payroll.federal_tax_calculator import FederalTaxCalculator, FederalTaxResult
from app.services.payroll.provincial_tax_calculator import ProvincialTaxCalculator, ProvincialTaxResult
from app.services.payroll.payroll_engine import (
    PayrollEngine,
    EmployeePayrollInput,
    PayrollCalculationResult,
)

__all__ = [
    # Tax Tables
    "get_federal_config",
    "get_cpp_config",
    "get_ei_config",
    "get_province_config",
    "get_all_provinces",
    "find_tax_bracket",
    "calculate_dynamic_bpa",
    "validate_tax_tables",
    # Calculators
    "CPPCalculator",
    "CppContribution",
    "EICalculator",
    "EiPremium",
    "FederalTaxCalculator",
    "FederalTaxResult",
    "ProvincialTaxCalculator",
    "ProvincialTaxResult",
    # Engine
    "PayrollEngine",
    "EmployeePayrollInput",
    "PayrollCalculationResult",
]
