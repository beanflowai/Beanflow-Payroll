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

__all__ = [
    "get_federal_config",
    "get_cpp_config",
    "get_ei_config",
    "get_province_config",
    "get_all_provinces",
    "find_tax_bracket",
    "calculate_dynamic_bpa",
    "validate_tax_tables",
]
