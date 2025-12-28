"""
Payroll Run Module

Manages payroll run lifecycle: creation, calculation, approval, and employee management.
"""

from app.services.payroll_run.benefits_calculator import BenefitsCalculator
from app.services.payroll_run.constants import (
    COMPLETED_RUN_STATUSES,
    DEFAULT_FEDERAL_BPA_FALLBACK,
    DEFAULT_TAX_YEAR,
    PERIODS_PER_YEAR,
    calculate_next_pay_date,
    extract_year_from_date,
    get_federal_bpa,
    get_provincial_bpa,
)
from app.services.payroll_run.employee_management import EmployeeManagement
from app.services.payroll_run.gross_calculator import GrossCalculator
from app.services.payroll_run.model_builders import ModelBuilder
from app.services.payroll_run.run_operations import PayrollRunOperations
from app.services.payroll_run.ytd_calculator import YtdCalculator

__all__ = [
    # Constants
    "DEFAULT_FEDERAL_BPA_FALLBACK",
    "COMPLETED_RUN_STATUSES",
    "DEFAULT_TAX_YEAR",
    "PERIODS_PER_YEAR",
    # Utility functions
    "extract_year_from_date",
    "calculate_next_pay_date",
    "get_federal_bpa",
    "get_provincial_bpa",
    # Classes
    "ModelBuilder",
    "GrossCalculator",
    "BenefitsCalculator",
    "YtdCalculator",
    "PayrollRunOperations",
    "EmployeeManagement",
]
