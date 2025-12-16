"""Pydantic models for request/response schemas"""

from app.models.auth import UserResponse
from app.models.schemas import BaseResponse, ErrorResponse, HealthCheckResponse, SuccessResponse
from app.models.payroll import (
    Province,
    PayFrequency,
    PayrollRunStatus,
    EmploymentType,
    VacationPayoutMethod,
    TaxBracket,
    ProvinceTaxConfig,
    FederalTaxConfig,
    CppConfig,
    EiConfig,
    VacationConfig,
    EmployeeBase,
    EmployeeCreate,
    EmployeeUpdate,
    Employee,
    EmployeeResponse,
    PayrollRunBase,
    PayrollRunCreate,
    PayrollRun,
    PayrollRecordBase,
    PayrollRecord,
    PayrollCalculationRequest,
    PayrollCalculationResult,
    EmployeeListFilters,
    PayrollRunListFilters,
)

__all__ = [
    # Base schemas
    "BaseResponse",
    "SuccessResponse",
    "ErrorResponse",
    "HealthCheckResponse",
    "UserResponse",
    # Payroll enums
    "Province",
    "PayFrequency",
    "PayrollRunStatus",
    "EmploymentType",
    "VacationPayoutMethod",
    # Tax config models
    "TaxBracket",
    "ProvinceTaxConfig",
    "FederalTaxConfig",
    "CppConfig",
    "EiConfig",
    # Vacation config
    "VacationConfig",
    # Employee models
    "EmployeeBase",
    "EmployeeCreate",
    "EmployeeUpdate",
    "Employee",
    "EmployeeResponse",
    # Payroll run models
    "PayrollRunBase",
    "PayrollRunCreate",
    "PayrollRun",
    # Payroll record models
    "PayrollRecordBase",
    "PayrollRecord",
    # Calculation models
    "PayrollCalculationRequest",
    "PayrollCalculationResult",
    # Filter models
    "EmployeeListFilters",
    "PayrollRunListFilters",
]
