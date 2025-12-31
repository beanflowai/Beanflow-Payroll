"""
Payroll Services Module

Contains tax calculation services, payroll processing, and related utilities.
"""

from app.services.payroll.cpp_calculator import CPPCalculator, CppContribution
from app.services.payroll.ei_calculator import EICalculator, EiPremium
from app.services.payroll.federal_tax_calculator import FederalTaxCalculator, FederalTaxResult
from app.services.payroll.payroll_engine import (
    EmployeePayrollInput,
    PayrollCalculationResult,
    PayrollEngine,
)
from app.services.payroll.paystub_data_builder import PaystubDataBuilder
from app.services.payroll.paystub_generator import PaystubGenerator
from app.services.payroll.provincial_tax_calculator import (
    ProvincialTaxCalculator,
    ProvincialTaxResult,
)
from app.services.payroll.sick_leave_config_loader import (
    SickLeaveConfigLoader,
    get_provinces_with_paid_sick_leave,
    get_provinces_with_sick_leave_carryover,
)
from app.services.payroll.sick_leave_config_loader import (
    get_all_configs as get_all_sick_leave_configs,
)
from app.services.payroll.sick_leave_config_loader import (
    get_config as get_sick_leave_config,
)
from app.services.payroll.sick_leave_config_loader import (
    get_config_metadata as get_sick_leave_config_metadata,
)
from app.services.payroll.sick_leave_service import (
    AverageDayPayResult,
    SickLeaveBalance,
    SickLeaveConfig,
    SickLeaveService,
    SickPayResult,
)
from app.services.payroll.tax_tables import (
    calculate_dynamic_bpa,
    find_tax_bracket,
    get_all_provinces,
    get_cpp_config,
    get_ei_config,
    get_federal_config,
    get_province_config,
    validate_tax_tables,
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
    # Paystub
    "PaystubGenerator",
    "PaystubDataBuilder",
    # Sick Leave
    "SickLeaveService",
    "SickLeaveConfig",
    "SickLeaveBalance",
    "SickPayResult",
    "AverageDayPayResult",
    "SickLeaveConfigLoader",
    "get_sick_leave_config",
    "get_all_sick_leave_configs",
    "get_provinces_with_paid_sick_leave",
    "get_provinces_with_sick_leave_carryover",
    "get_sick_leave_config_metadata",
]
