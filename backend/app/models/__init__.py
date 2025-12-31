"""Pydantic models for request/response schemas"""

from app.models.auth import UserResponse
from app.models.compensation import (
    CompensationHistory,
    CompensationHistoryCreate,
    CompensationHistoryResponse,
)
from app.models.payroll import (
    CppConfig,
    EiConfig,
    Employee,
    EmployeeBase,
    EmployeeCreate,
    EmployeeListFilters,
    EmployeeResponse,
    EmployeeUpdate,
    EmploymentType,
    FederalTaxConfig,
    PayFrequency,
    PayrollCalculationRequest,
    PayrollCalculationResult,
    PayrollRecord,
    PayrollRecordBase,
    PayrollRun,
    PayrollRunBase,
    PayrollRunCreate,
    PayrollRunListFilters,
    PayrollRunStatus,
    Province,
    ProvinceTaxConfig,
    TaxBracket,
    VacationConfig,
    VacationPayoutMethod,
)
from app.models.schemas import BaseResponse, ErrorResponse, HealthCheckResponse, SuccessResponse

__all__ = [
    # Base schemas
    "BaseResponse",
    "SuccessResponse",
    "ErrorResponse",
    "HealthCheckResponse",
    "UserResponse",
    # Compensation models
    "CompensationHistory",
    "CompensationHistoryCreate",
    "CompensationHistoryResponse",
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
