"""
Payroll API Endpoints

Provides REST API for payroll calculations and payroll run management.
"""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser
from app.models.payroll import PayFrequency, Province
from app.services.payroll import (
    EmployeePayrollInput,
    PayrollCalculationResult,
    PayrollEngine,
)
from app.core.supabase_client import get_supabase_client
from app.services.payroll.paystub_storage import (
    get_paystub_storage,
    PaystubStorageConfigError,
)
from app.services.payroll_run_service import get_payroll_run_service

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_user_company_id(user_id: str) -> str:
    """Get the primary company ID for a user.

    Note: Currently the system assumes one company per user.
    This function returns the oldest (first created) company for the user.
    If multi-company support is added in the future, this should be updated
    to accept company_id as a parameter or use a user preference.

    Args:
        user_id: The user's ID

    Returns:
        The company ID string

    Raises:
        HTTPException: If no company found for user
    """
    supabase = get_supabase_client()
    result = supabase.table("companies").select("id").eq(
        "user_id", user_id
    ).order("created_at", desc=False).limit(1).execute()

    if not result.data or len(result.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No company found for user. Please create a company first.",
        )

    return str(result.data[0]["id"])


# =============================================================================
# Request/Response Models
# =============================================================================


class EmployeeCalculationRequest(BaseModel):
    """Single employee calculation request."""

    employee_id: str
    province: Province
    pay_frequency: PayFrequency

    # Earnings
    gross_regular: Decimal = Field(..., description="Regular gross pay")
    gross_overtime: Decimal = Field(default=Decimal("0"), description="Overtime pay")
    holiday_pay: Decimal = Field(default=Decimal("0"), description="Holiday pay")
    holiday_premium_pay: Decimal = Field(
        default=Decimal("0"), description="Holiday premium pay (1.5x or 2x)"
    )
    vacation_pay: Decimal = Field(default=Decimal("0"), description="Vacation pay")
    other_earnings: Decimal = Field(default=Decimal("0"), description="Other earnings")

    # TD1 Claims
    federal_claim_amount: Decimal = Field(
        default=Decimal("16129"), description="Federal TD1 claim amount"
    )
    provincial_claim_amount: Decimal = Field(
        default=Decimal("12747"), description="Provincial TD1 claim amount"
    )

    # Pre-tax Deductions
    rrsp_per_period: Decimal = Field(default=Decimal("0"), description="RRSP deduction")
    union_dues_per_period: Decimal = Field(
        default=Decimal("0"), description="Union dues"
    )

    # Post-tax Deductions
    garnishments: Decimal = Field(default=Decimal("0"), description="Court-ordered garnishments")
    other_deductions: Decimal = Field(
        default=Decimal("0"), description="Other post-tax deductions"
    )

    # YTD Values
    ytd_gross: Decimal = Field(
        default=Decimal("0"), description="Year-to-date gross earnings"
    )
    ytd_pensionable_earnings: Decimal = Field(
        default=Decimal("0"), description="Year-to-date pensionable earnings"
    )
    ytd_insurable_earnings: Decimal = Field(
        default=Decimal("0"), description="Year-to-date insurable earnings"
    )
    ytd_cpp_base: Decimal = Field(
        default=Decimal("0"), description="Year-to-date base CPP contributions"
    )
    ytd_cpp_additional: Decimal = Field(
        default=Decimal("0"), description="Year-to-date CPP2 contributions"
    )
    ytd_ei: Decimal = Field(
        default=Decimal("0"), description="Year-to-date EI premiums"
    )

    # Exemptions
    is_cpp_exempt: bool = Field(default=False, description="CPP exemption status")
    is_ei_exempt: bool = Field(default=False, description="EI exemption status")
    cpp2_exempt: bool = Field(
        default=False, description="CPP2 exemption (CPT30 on file)"
    )


class CalculationResponse(BaseModel):
    """Single employee calculation response."""

    employee_id: str
    province: str

    # Earnings
    gross_regular: Decimal
    gross_overtime: Decimal
    holiday_pay: Decimal
    holiday_premium_pay: Decimal
    vacation_pay: Decimal
    other_earnings: Decimal
    total_gross: Decimal

    # Employee Deductions
    cpp_base: Decimal
    cpp_additional: Decimal
    cpp_total: Decimal
    ei_employee: Decimal
    federal_tax: Decimal
    provincial_tax: Decimal
    rrsp: Decimal
    union_dues: Decimal
    garnishments: Decimal
    other_deductions: Decimal
    total_employee_deductions: Decimal

    # Employer Costs
    cpp_employer: Decimal
    ei_employer: Decimal
    total_employer_costs: Decimal

    # Net Pay
    net_pay: Decimal

    # Updated YTD
    new_ytd_gross: Decimal
    new_ytd_cpp: Decimal
    new_ytd_ei: Decimal

    # Calculation Details (optional, for debugging)
    calculation_details: dict[str, Any] | None = None

    model_config = {"json_encoders": {Decimal: str}}


class BatchCalculationRequest(BaseModel):
    """Batch calculation request for multiple employees."""

    employees: list[EmployeeCalculationRequest]
    include_details: bool = Field(
        default=False, description="Include calculation details in response"
    )


class BatchCalculationResponse(BaseModel):
    """Batch calculation response."""

    results: list[CalculationResponse]
    summary: dict[str, Any]


class PayrollRunCalculationRequest(BaseModel):
    """Request to calculate a complete payroll run."""

    pay_date: str = Field(..., description="Pay date in YYYY-MM-DD format")
    include_details: bool = Field(
        default=False, description="Include calculation details"
    )


class PayrollRunCalculationResponse(BaseModel):
    """Response from payroll run calculation."""

    pay_date: str
    total_employees: int
    total_gross: Decimal
    total_cpp_employee: Decimal
    total_cpp_employer: Decimal
    total_ei_employee: Decimal
    total_ei_employer: Decimal
    total_federal_tax: Decimal
    total_provincial_tax: Decimal
    total_deductions: Decimal
    total_net_pay: Decimal
    total_employer_cost: Decimal
    records: list[CalculationResponse]


# =============================================================================
# Helper Functions
# =============================================================================


def result_to_response(
    result: PayrollCalculationResult, include_details: bool = False
) -> CalculationResponse:
    """Convert engine result to API response."""
    return CalculationResponse(
        employee_id=result.employee_id,
        province=result.province,
        gross_regular=result.gross_regular,
        gross_overtime=result.gross_overtime,
        holiday_pay=result.holiday_pay,
        holiday_premium_pay=result.holiday_premium_pay,
        vacation_pay=result.vacation_pay,
        other_earnings=result.other_earnings,
        total_gross=result.total_gross,
        cpp_base=result.cpp_base,
        cpp_additional=result.cpp_additional,
        cpp_total=result.cpp_total,
        ei_employee=result.ei_employee,
        federal_tax=result.federal_tax,
        provincial_tax=result.provincial_tax,
        rrsp=result.rrsp,
        union_dues=result.union_dues,
        garnishments=result.garnishments,
        other_deductions=result.other_deductions,
        total_employee_deductions=result.total_employee_deductions,
        cpp_employer=result.cpp_employer,
        ei_employer=result.ei_employer,
        total_employer_costs=result.total_employer_costs,
        net_pay=result.net_pay,
        new_ytd_gross=result.new_ytd_gross,
        new_ytd_cpp=result.new_ytd_cpp,
        new_ytd_ei=result.new_ytd_ei,
        calculation_details=result.calculation_details if include_details else None,
    )


def request_to_input(request: EmployeeCalculationRequest) -> EmployeePayrollInput:
    """Convert API request to engine input."""
    return EmployeePayrollInput(
        employee_id=request.employee_id,
        province=request.province,
        pay_frequency=request.pay_frequency,
        gross_regular=request.gross_regular,
        gross_overtime=request.gross_overtime,
        holiday_pay=request.holiday_pay,
        holiday_premium_pay=request.holiday_premium_pay,
        vacation_pay=request.vacation_pay,
        other_earnings=request.other_earnings,
        federal_claim_amount=request.federal_claim_amount,
        provincial_claim_amount=request.provincial_claim_amount,
        rrsp_per_period=request.rrsp_per_period,
        union_dues_per_period=request.union_dues_per_period,
        garnishments=request.garnishments,
        other_deductions=request.other_deductions,
        ytd_gross=request.ytd_gross,
        ytd_pensionable_earnings=request.ytd_pensionable_earnings,
        ytd_insurable_earnings=request.ytd_insurable_earnings,
        ytd_cpp_base=request.ytd_cpp_base,
        ytd_cpp_additional=request.ytd_cpp_additional,
        ytd_ei=request.ytd_ei,
        is_cpp_exempt=request.is_cpp_exempt,
        is_ei_exempt=request.is_ei_exempt,
        cpp2_exempt=request.cpp2_exempt,
    )


# =============================================================================
# API Endpoints
# =============================================================================


@router.post(
    "/calculate",
    response_model=CalculationResponse,
    summary="Calculate payroll for single employee",
    description="Calculate CPP, EI, federal tax, and provincial tax for one employee.",
)
async def calculate_single(
    request: EmployeeCalculationRequest,
    current_user: CurrentUser,
) -> CalculationResponse:
    """
    Calculate payroll deductions for a single employee.

    This endpoint performs a complete payroll calculation including:
    - CPP contributions (base and CPP2)
    - EI premiums
    - Federal income tax
    - Provincial income tax

    The calculation follows CRA T4127 guidelines for Canadian payroll.
    """
    try:
        engine = PayrollEngine(year=2025)
        input_data = request_to_input(request)

        # Validate input
        errors = engine.validate_input(input_data)
        if errors:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"errors": errors},
            )

        result = engine.calculate(input_data)
        return result_to_response(result, include_details=True)

    except ValueError as e:
        logger.error(f"Calculation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.exception("Unexpected error during calculation")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error during payroll calculation",
        )


@router.post(
    "/calculate/batch",
    response_model=BatchCalculationResponse,
    summary="Calculate payroll for multiple employees",
    description="Calculate payroll for a batch of employees in one request.",
)
async def calculate_batch(
    request: BatchCalculationRequest,
    current_user: CurrentUser,
) -> BatchCalculationResponse:
    """
    Calculate payroll deductions for multiple employees.

    Batch processing is more efficient than making individual requests.
    Returns individual results plus a summary of totals.
    """
    if not request.employees:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one employee is required",
        )

    try:
        engine = PayrollEngine(year=2025)

        # Convert requests to inputs
        inputs = [request_to_input(emp) for emp in request.employees]

        # Validate all inputs
        all_errors = []
        for i, input_data in enumerate(inputs):
            errors = engine.validate_input(input_data)
            if errors:
                all_errors.append({"employee_index": i, "errors": errors})

        if all_errors:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"validation_errors": all_errors},
            )

        # Calculate all
        results = engine.calculate_batch(inputs)
        responses = [
            result_to_response(r, include_details=request.include_details)
            for r in results
        ]

        # Calculate summary
        summary = {
            "total_employees": len(results),
            "total_gross": str(sum(r.total_gross for r in results)),
            "total_cpp_employee": str(sum(r.cpp_total for r in results)),
            "total_cpp_employer": str(sum(r.cpp_employer for r in results)),
            "total_ei_employee": str(sum(r.ei_employee for r in results)),
            "total_ei_employer": str(sum(r.ei_employer for r in results)),
            "total_federal_tax": str(sum(r.federal_tax for r in results)),
            "total_provincial_tax": str(sum(r.provincial_tax for r in results)),
            "total_deductions": str(sum(r.total_employee_deductions for r in results)),
            "total_net_pay": str(sum(r.net_pay for r in results)),
            "total_employer_costs": str(sum(r.total_employer_costs for r in results)),
        }

        return BatchCalculationResponse(results=responses, summary=summary)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error during batch calculation")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error during batch payroll calculation",
        )


@router.get(
    "/tax-config/{province}",
    summary="Get tax configuration for a province",
    description="Get CPP, EI, and tax configuration for a specific province.",
)
async def get_tax_config(
    province: Province,
    current_user: CurrentUser,
    year: int | None = Query(default=None, description="Tax year, defaults to current year"),
    pay_date: date | None = Query(default=None, description="Pay date for edition selection"),
) -> dict[str, Any]:
    """
    Get tax configuration for a specific province.

    Supports year and pay_date parameters for edition selection.
    If versioned config files exist (e.g., provinces_jan.json, provinces_jul.json),
    the pay_date determines which edition to use:
    - Before July 1: January edition
    - July 1 onwards: July edition (default)
    """
    from app.services.payroll import (
        get_cpp_config,
        get_ei_config,
        get_federal_config,
        get_province_config,
    )

    if year is None:
        year = pay_date.year if pay_date else date.today().year

    try:
        return {
            "year": year,
            "province": province.value,
            "cpp": get_cpp_config(year),
            "ei": get_ei_config(year),
            "federal": get_federal_config(year, pay_date),
            "provincial": get_province_config(province.value, year, pay_date),
        }
    except Exception as e:
        logger.exception(f"Error getting tax config for {province}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting tax configuration: {str(e)}",
        )


@router.get(
    "/tax-config",
    summary="Get all tax configuration",
    description="Get CPP, EI, and federal tax configuration.",
)
async def get_all_tax_config(
    current_user: CurrentUser,
    year: int | None = Query(default=None, description="Tax year, defaults to current year"),
    pay_date: date | None = Query(default=None, description="Pay date for edition selection"),
) -> dict[str, Any]:
    """
    Get all tax configuration.

    Supports year and pay_date parameters for edition selection.
    """
    from app.services.payroll import (
        get_all_provinces,
        get_cpp_config,
        get_ei_config,
        get_federal_config,
    )

    if year is None:
        year = pay_date.year if pay_date else date.today().year

    try:
        return {
            "year": year,
            "cpp": get_cpp_config(year),
            "ei": get_ei_config(year),
            "federal": get_federal_config(year, pay_date),
            "supported_provinces": get_all_provinces(year),
        }
    except Exception as e:
        logger.exception("Error getting tax config")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting tax configuration: {str(e)}",
        )


# =============================================================================
# BPA Defaults Endpoint
# =============================================================================


class BPADefaultsResponse(BaseModel):
    """Response for BPA defaults endpoint."""

    year: int
    edition: str = Field(description="'jan' or 'jul' based on pay_date")
    federalBPA: float = Field(description="Federal Basic Personal Amount")
    provincialBPA: float = Field(description="Provincial Basic Personal Amount")
    province: str


@router.get(
    "/bpa-defaults/{province}",
    response_model=BPADefaultsResponse,
    summary="Get default BPA values",
    description="Get default Basic Personal Amount values for a province.",
)
async def get_bpa_defaults(
    province: Province,
    current_user: CurrentUser,
    year: int | None = Query(default=None, description="Tax year, defaults to current year"),
    pay_date: date | None = Query(default=None, description="Pay date for edition selection"),
) -> BPADefaultsResponse:
    """
    Get default BPA values for frontend forms.

    Returns the federal and provincial BPA based on year and pay_date.
    This endpoint is used by frontend to dynamically set default values
    instead of hardcoding them.
    """
    from app.services.payroll import get_federal_config, get_province_config

    if year is None:
        year = pay_date.year if pay_date else date.today().year

    # Determine edition based on pay date
    if pay_date is not None and pay_date.month < 7:
        edition = "jan"
    else:
        edition = "jul"

    try:
        federal_config = get_federal_config(year, pay_date)
        province_config = get_province_config(province.value, year, pay_date)

        return BPADefaultsResponse(
            year=year,
            edition=edition,
            federalBPA=float(federal_config["bpaf"]),
            provincialBPA=float(province_config["bpa"]),
            province=province.value,
        )
    except Exception as e:
        logger.exception(f"Error getting BPA defaults for {province}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting BPA defaults: {str(e)}",
        )


# =============================================================================
# Payroll Runs List Endpoint
# =============================================================================


class PayrollRunListItem(BaseModel):
    """Payroll run item for list response."""

    id: str
    payDate: str = Field(validation_alias="pay_date")
    periodStart: str = Field(validation_alias="period_start")
    periodEnd: str = Field(validation_alias="period_end")
    status: str
    totalEmployees: int = Field(validation_alias="total_employees")
    totalGross: float = Field(validation_alias="total_gross")
    totalNetPay: float = Field(validation_alias="total_net_pay")
    totalEmployerCost: float = Field(validation_alias="total_employer_cost")

    model_config = {"populate_by_name": True}


class PayrollRunListResponse(BaseModel):
    """Response for listing payroll runs."""

    runs: list[PayrollRunListItem]
    total: int


@router.get(
    "/runs",
    response_model=PayrollRunListResponse,
    summary="List payroll runs",
    description="List payroll runs with optional status filtering and pagination.",
)
async def list_payroll_runs(
    current_user: CurrentUser,
    run_status: str | None = None,
    excludeStatus: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> PayrollRunListResponse:
    """
    List payroll runs with filtering and pagination.

    Query parameters:
    - run_status: Filter by a single status (e.g., 'pending_approval')
    - excludeStatus: Comma-separated statuses to exclude (e.g., 'draft,cancelled')
    - limit: Maximum number of runs to return (default 20)
    - offset: Number of runs to skip for pagination (default 0)

    Returns runs sorted by pay_date descending.
    """
    try:
        company_id = await get_user_company_id(current_user.id)
        service = get_payroll_run_service(current_user.id, company_id)

        # Parse excludeStatus into list
        exclude_statuses = None
        if excludeStatus:
            exclude_statuses = [s.strip() for s in excludeStatus.split(",")]

        result = await service.list_runs(
            status=run_status,
            exclude_statuses=exclude_statuses,
            limit=limit,
            offset=offset,
        )

        runs = [
            PayrollRunListItem.model_validate(run) for run in result["runs"]
        ]

        return PayrollRunListResponse(runs=runs, total=result["total"])

    except Exception as e:
        logger.exception("Unexpected error listing payroll runs")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error listing payroll runs",
        )


# =============================================================================
# Payroll Run Management Endpoints (Draft State Editing)
# =============================================================================


class LeaveEntryInput(BaseModel):
    """Leave entry input for payroll record update."""

    type: str = Field(..., description="Leave type: 'vacation' or 'sick'")
    hours: float = Field(..., description="Hours of leave taken")


class HolidayWorkInput(BaseModel):
    """Holiday work entry input for payroll record update."""

    holidayDate: str = Field(..., description="Holiday date in YYYY-MM-DD format")
    holidayName: str = Field(..., description="Name of the holiday")
    hoursWorked: float = Field(..., description="Hours worked on the holiday")


class AdjustmentInput(BaseModel):
    """Adjustment input for payroll record update."""

    type: str = Field(
        ..., description="Adjustment type: 'bonus', 'deduction', 'reimbursement', etc."
    )
    amount: float = Field(..., description="Adjustment amount")
    description: str = Field(default="", description="Description of the adjustment")
    taxable: bool = Field(default=True, description="Whether the adjustment is taxable")


class PayrollOverrides(BaseModel):
    """Override values for automatic calculations."""

    regularPay: float | None = Field(default=None, description="Override regular pay")
    overtimePay: float | None = Field(default=None, description="Override overtime pay")
    holidayPay: float | None = Field(default=None, description="Override holiday pay")


class UpdatePayrollRecordRequest(BaseModel):
    """Request to update a payroll record's input data."""

    regularHours: float | None = Field(default=None, description="Regular hours worked")
    overtimeHours: float | None = Field(
        default=None, description="Overtime hours worked"
    )
    leaveEntries: list[LeaveEntryInput] | None = Field(
        default=None, description="Leave entries"
    )
    holidayWorkEntries: list[HolidayWorkInput] | None = Field(
        default=None, description="Holiday work entries"
    )
    adjustments: list[AdjustmentInput] | None = Field(
        default=None, description="One-time adjustments"
    )
    overrides: PayrollOverrides | None = Field(
        default=None, description="Manual override values"
    )


class PayrollRecordResponse(BaseModel):
    """Response from payroll record update."""

    id: str
    employeeId: str = Field(alias="employee_id")
    inputData: dict[str, Any] | None = Field(alias="input_data")
    isModified: bool = Field(alias="is_modified")

    model_config = {"populate_by_name": True}


class PayrollRunResponse(BaseModel):
    """Response from payroll run operations."""

    id: str
    payDate: str = Field(alias="pay_date")
    status: str
    totalEmployees: int = Field(alias="total_employees")
    totalGross: float = Field(alias="total_gross")
    totalCppEmployee: float = Field(alias="total_cpp_employee")
    totalCppEmployer: float = Field(alias="total_cpp_employer")
    totalEiEmployee: float = Field(alias="total_ei_employee")
    totalEiEmployer: float = Field(alias="total_ei_employer")
    totalFederalTax: float = Field(alias="total_federal_tax")
    totalProvincialTax: float = Field(alias="total_provincial_tax")
    totalNetPay: float = Field(alias="total_net_pay")
    totalEmployerCost: float = Field(alias="total_employer_cost")

    model_config = {"populate_by_name": True}


@router.patch(
    "/runs/{run_id}/records/{record_id}",
    response_model=PayrollRecordResponse,
    summary="Update a payroll record",
    description="Update input data for a payroll record in draft status.",
)
async def update_payroll_record(
    run_id: UUID,
    record_id: UUID,
    request: UpdatePayrollRecordRequest,
    current_user: CurrentUser,
) -> PayrollRecordResponse:
    """
    Update a payroll record's input data while in draft status.

    This allows editing:
    - Regular hours (hourly employees only)
    - Overtime hours
    - Leave entries (vacation, sick)
    - Holiday work entries
    - One-time adjustments (bonus, deduction, reimbursement)
    - Manual override values

    The record will be marked as modified, requiring recalculation.
    """
    try:
        company_id = await get_user_company_id(current_user.id)
        service = get_payroll_run_service(current_user.id, company_id)

        # Build input_data from request
        input_data: dict[str, Any] = {}
        if request.regularHours is not None:
            input_data["regularHours"] = request.regularHours
        if request.overtimeHours is not None:
            input_data["overtimeHours"] = request.overtimeHours
        if request.leaveEntries is not None:
            input_data["leaveEntries"] = [
                {"type": e.type, "hours": e.hours} for e in request.leaveEntries
            ]
        if request.holidayWorkEntries is not None:
            input_data["holidayWorkEntries"] = [
                {
                    "holidayDate": e.holidayDate,
                    "holidayName": e.holidayName,
                    "hoursWorked": e.hoursWorked,
                }
                for e in request.holidayWorkEntries
            ]
        if request.adjustments is not None:
            input_data["adjustments"] = [
                {
                    "type": a.type,
                    "amount": a.amount,
                    "description": a.description,
                    "taxable": a.taxable,
                }
                for a in request.adjustments
            ]
        if request.overrides is not None:
            input_data["overrides"] = {
                "regularPay": request.overrides.regularPay,
                "overtimePay": request.overrides.overtimePay,
                "holidayPay": request.overrides.holidayPay,
            }

        result = await service.update_record(run_id, record_id, input_data)

        return PayrollRecordResponse(
            id=result["id"],
            employee_id=result["employee_id"],
            input_data=result.get("input_data"),
            is_modified=result.get("is_modified", False),
        )

    except ValueError as e:
        logger.error(f"Update record error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error updating payroll record")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error updating payroll record",
        )


@router.post(
    "/runs/{run_id}/recalculate",
    response_model=PayrollRunResponse,
    summary="Recalculate payroll run",
    description="Recalculate all records in a draft payroll run.",
)
async def recalculate_payroll_run(
    run_id: UUID,
    current_user: CurrentUser,
) -> PayrollRunResponse:
    """
    Recalculate all payroll deductions for a draft run.

    This:
    1. Reads input_data from all payroll_records
    2. Recalculates CPP, EI, federal tax, and provincial tax
    3. Updates all payroll_records with new values
    4. Updates payroll_runs summary totals
    5. Clears all is_modified flags

    Only works on runs in 'draft' status.
    """
    try:
        company_id = await get_user_company_id(current_user.id)
        service = get_payroll_run_service(current_user.id, company_id)
        result = await service.recalculate_run(run_id)

        return PayrollRunResponse(
            id=result["id"],
            pay_date=result["pay_date"],
            status=result["status"],
            total_employees=result.get("total_employees", 0),
            total_gross=float(result.get("total_gross", 0)),
            total_cpp_employee=float(result.get("total_cpp_employee", 0)),
            total_cpp_employer=float(result.get("total_cpp_employer", 0)),
            total_ei_employee=float(result.get("total_ei_employee", 0)),
            total_ei_employer=float(result.get("total_ei_employer", 0)),
            total_federal_tax=float(result.get("total_federal_tax", 0)),
            total_provincial_tax=float(result.get("total_provincial_tax", 0)),
            total_net_pay=float(result.get("total_net_pay", 0)),
            total_employer_cost=float(result.get("total_employer_cost", 0)),
        )

    except ValueError as e:
        logger.error(f"Recalculate error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error recalculating payroll run")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error recalculating payroll run",
        )


class SyncEmployeesResponse(BaseModel):
    """Response from sync employees operation."""

    addedCount: int = Field(alias="added_count")
    addedEmployees: list[dict[str, str]] = Field(alias="added_employees")
    run: PayrollRunResponse

    model_config = {"populate_by_name": True}


@router.post(
    "/runs/{run_id}/sync-employees",
    response_model=SyncEmployeesResponse,
    summary="Sync new employees to draft payroll run",
    description="Add any new employees from pay groups to an existing draft payroll run.",
)
async def sync_employees(
    run_id: UUID,
    current_user: CurrentUser,
) -> SyncEmployeesResponse:
    """
    Sync new employees to a draft payroll run.

    When employees are added to pay groups after a payroll run is created,
    this endpoint will:
    1. Find pay groups for the run's pay_date
    2. Get active employees from those pay groups
    3. Create payroll_records for any employees not yet in the run
    4. Update the run's total_employees count

    Only works on runs in 'draft' status. Non-draft runs return empty result.
    """
    try:
        company_id = await get_user_company_id(current_user.id)
        service = get_payroll_run_service(current_user.id, company_id)
        result = await service.sync_employees(run_id)

        run_data = result["run"]
        return SyncEmployeesResponse(
            added_count=result["added_count"],
            added_employees=result["added_employees"],
            run=PayrollRunResponse(
                id=run_data["id"],
                pay_date=run_data["pay_date"],
                status=run_data["status"],
                total_employees=run_data.get("total_employees", 0),
                total_gross=float(run_data.get("total_gross", 0)),
                total_cpp_employee=float(run_data.get("total_cpp_employee", 0)),
                total_cpp_employer=float(run_data.get("total_cpp_employer", 0)),
                total_ei_employee=float(run_data.get("total_ei_employee", 0)),
                total_ei_employer=float(run_data.get("total_ei_employer", 0)),
                total_federal_tax=float(run_data.get("total_federal_tax", 0)),
                total_provincial_tax=float(run_data.get("total_provincial_tax", 0)),
                total_net_pay=float(run_data.get("total_net_pay", 0)),
                total_employer_cost=float(run_data.get("total_employer_cost", 0)),
            ),
        )

    except ValueError as e:
        logger.error(f"Sync employees error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error syncing employees")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error syncing employees",
        )


class CreateOrGetRunRequest(BaseModel):
    """Request to create or get a draft payroll run."""

    periodEnd: str = Field(..., description="Period end date in YYYY-MM-DD format")


class CreateOrGetRunResponse(BaseModel):
    """Response from create or get payroll run operation."""

    run: PayrollRunResponse
    created: bool = Field(description="True if a new run was created, False if existing")
    recordsCount: int = Field(alias="records_count", description="Number of records created")

    model_config = {"populate_by_name": True}


@router.post(
    "/runs/create-or-get",
    response_model=CreateOrGetRunResponse,
    summary="Create or get a draft payroll run",
    description="Create a new draft payroll run or return existing one for a period end.",
)
async def create_or_get_run(
    request: CreateOrGetRunRequest,
    current_user: CurrentUser,
) -> CreateOrGetRunResponse:
    """
    Create a new draft payroll run or get existing one for a period end.

    This endpoint:
    1. Checks if a payroll run already exists for this period end
    2. If exists, returns the existing run
    3. If not, creates a new draft run with payroll records for all eligible employees

    The run is automatically populated with employees from pay groups that have
    this date as their next_period_end.
    """
    try:
        company_id = await get_user_company_id(current_user.id)
        service = get_payroll_run_service(current_user.id, company_id)
        result = await service.create_or_get_run_by_period_end(request.periodEnd)

        run_data = result["run"]
        return CreateOrGetRunResponse(
            run=PayrollRunResponse(
                id=run_data["id"],
                pay_date=run_data["pay_date"],
                status=run_data["status"],
                total_employees=run_data.get("total_employees", 0),
                total_gross=float(run_data.get("total_gross", 0)),
                total_cpp_employee=float(run_data.get("total_cpp_employee", 0)),
                total_cpp_employer=float(run_data.get("total_cpp_employer", 0)),
                total_ei_employee=float(run_data.get("total_ei_employee", 0)),
                total_ei_employer=float(run_data.get("total_ei_employer", 0)),
                total_federal_tax=float(run_data.get("total_federal_tax", 0)),
                total_provincial_tax=float(run_data.get("total_provincial_tax", 0)),
                total_net_pay=float(run_data.get("total_net_pay", 0)),
                total_employer_cost=float(run_data.get("total_employer_cost", 0)),
            ),
            created=result["created"],
            records_count=result["records_count"],
        )

    except ValueError as e:
        logger.error(f"Create or get run error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error creating/getting payroll run")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error creating/getting payroll run",
        )


class AddEmployeeRequest(BaseModel):
    """Request to add an employee to a payroll run."""

    employeeId: str = Field(..., description="Employee ID to add")


class AddEmployeeResponse(BaseModel):
    """Response from adding an employee to a payroll run."""

    employeeId: str = Field(alias="employee_id")
    employeeName: str = Field(alias="employee_name")

    model_config = {"populate_by_name": True}


@router.post(
    "/runs/{run_id}/employees",
    response_model=AddEmployeeResponse,
    summary="Add an employee to a draft payroll run",
    description="Add a single employee to a draft payroll run.",
)
async def add_employee_to_run(
    run_id: UUID,
    request: AddEmployeeRequest,
    current_user: CurrentUser,
) -> AddEmployeeResponse:
    """
    Add an employee to a draft payroll run.

    This creates a payroll record for the employee in the run.
    Only works on runs in 'draft' status.
    """
    try:
        company_id = await get_user_company_id(current_user.id)
        service = get_payroll_run_service(current_user.id, company_id)
        result = await service.add_employee_to_run(run_id, request.employeeId)

        return AddEmployeeResponse(
            employee_id=result["employee_id"],
            employee_name=result["employee_name"],
        )

    except ValueError as e:
        logger.error(f"Add employee error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error adding employee to payroll run")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error adding employee to payroll run",
        )


class RemoveEmployeeResponse(BaseModel):
    """Response from removing an employee from a payroll run."""

    removed: bool
    employeeId: str = Field(alias="employee_id")

    model_config = {"populate_by_name": True}


@router.delete(
    "/runs/{run_id}/employees/{employee_id}",
    response_model=RemoveEmployeeResponse,
    summary="Remove an employee from a draft payroll run",
    description="Remove a single employee from a draft payroll run.",
)
async def remove_employee_from_run(
    run_id: UUID,
    employee_id: str,
    current_user: CurrentUser,
) -> RemoveEmployeeResponse:
    """
    Remove an employee from a draft payroll run.

    This deletes the payroll record for the employee.
    Only works on runs in 'draft' status.
    """
    try:
        company_id = await get_user_company_id(current_user.id)
        service = get_payroll_run_service(current_user.id, company_id)
        result = await service.remove_employee_from_run(run_id, employee_id)

        return RemoveEmployeeResponse(
            removed=result["removed"],
            employee_id=result["employee_id"],
        )

    except ValueError as e:
        logger.error(f"Remove employee error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error removing employee from payroll run")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error removing employee from payroll run",
        )


class DeleteRunResponse(BaseModel):
    """Response from deleting a payroll run."""

    deleted: bool
    runId: str = Field(alias="run_id")

    model_config = {"populate_by_name": True}


@router.delete(
    "/runs/{run_id}",
    response_model=DeleteRunResponse,
    summary="Delete a draft payroll run",
    description="Delete a draft payroll run and all its records.",
)
async def delete_payroll_run(
    run_id: UUID,
    current_user: CurrentUser,
) -> DeleteRunResponse:
    """
    Delete a draft payroll run.

    This permanently deletes the run and all associated payroll records.
    Only works on runs in 'draft' status.
    """
    try:
        company_id = await get_user_company_id(current_user.id)
        service = get_payroll_run_service(current_user.id, company_id)
        result = await service.delete_run(run_id)

        return DeleteRunResponse(
            deleted=result["deleted"],
            run_id=result["run_id"],
        )

    except ValueError as e:
        logger.error(f"Delete run error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error deleting payroll run")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error deleting payroll run",
        )


@router.post(
    "/runs/{run_id}/finalize",
    response_model=PayrollRunResponse,
    summary="Finalize payroll run",
    description="Transition payroll run from draft to pending_approval.",
)
async def finalize_payroll_run(
    run_id: UUID,
    current_user: CurrentUser,
) -> PayrollRunResponse:
    """
    Finalize a draft payroll run.

    This transitions the run from 'draft' to 'pending_approval' status.
    After finalization, the run becomes read-only.

    Prerequisites:
    - Run must be in 'draft' status
    - No records can have is_modified = True (must recalculate first)
    """
    try:
        company_id = await get_user_company_id(current_user.id)
        service = get_payroll_run_service(current_user.id, company_id)
        result = await service.finalize_run(run_id)

        return PayrollRunResponse(
            id=result["id"],
            pay_date=result["pay_date"],
            status=result["status"],
            total_employees=result.get("total_employees", 0),
            total_gross=float(result.get("total_gross", 0)),
            total_cpp_employee=float(result.get("total_cpp_employee", 0)),
            total_cpp_employer=float(result.get("total_cpp_employer", 0)),
            total_ei_employee=float(result.get("total_ei_employee", 0)),
            total_ei_employer=float(result.get("total_ei_employer", 0)),
            total_federal_tax=float(result.get("total_federal_tax", 0)),
            total_provincial_tax=float(result.get("total_provincial_tax", 0)),
            total_net_pay=float(result.get("total_net_pay", 0)),
            total_employer_cost=float(result.get("total_employer_cost", 0)),
        )

    except ValueError as e:
        logger.error(f"Finalize error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error finalizing payroll run")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error finalizing payroll run",
        )


class ApprovePayrollRunResponse(BaseModel):
    """Response from approving a payroll run"""

    id: str
    pay_date: str = Field(alias="payDate")
    status: str
    total_employees: int = Field(alias="totalEmployees")
    total_gross: float = Field(alias="totalGross")
    total_net_pay: float = Field(alias="totalNetPay")
    paystubs_generated: int = Field(alias="paystubsGenerated")
    paystub_errors: list[str] | None = Field(default=None, alias="paystubErrors")

    model_config = {"populate_by_name": True}


@router.post(
    "/runs/{run_id}/approve",
    response_model=ApprovePayrollRunResponse,
    summary="Approve payroll run",
    description="Approve a pending_approval payroll run, generate paystubs, and advance next_pay_date.",
)
async def approve_payroll_run(
    run_id: UUID,
    current_user: CurrentUser,
) -> ApprovePayrollRunResponse:
    """
    Approve a pending_approval payroll run.

    This:
    1. Verifies run is in pending_approval status
    2. Generates paystub PDFs for all records
    3. Updates status to approved
    4. Advances next_pay_date for all affected pay groups

    Prerequisites:
    - Run must be in 'pending_approval' status
    """
    try:
        company_id = await get_user_company_id(current_user.id)
        service = get_payroll_run_service(current_user.id, company_id)
        result = await service.approve_run(run_id, approved_by=current_user.id)

        return ApprovePayrollRunResponse(
            id=result["id"],
            payDate=result["pay_date"],
            status=result["status"],
            totalEmployees=result.get("total_employees", 0),
            totalGross=float(result.get("total_gross", 0)),
            totalNetPay=float(result.get("total_net_pay", 0)),
            paystubsGenerated=result.get("paystubs_generated", 0),
            paystubErrors=result.get("paystub_errors"),
        )

    except ValueError as e:
        logger.error(f"Approve error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        logger.exception("Unexpected error approving payroll run")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error approving payroll run",
        )


# =============================================================================
# Send Paystubs API
# =============================================================================


class SendPaystubsResponse(BaseModel):
    """Response from sending paystubs"""

    sent: int = Field(..., description="Number of paystubs sent")
    errors: list[str] | None = Field(default=None, description="List of send errors")


@router.post(
    "/runs/{run_id}/send-paystubs",
    response_model=SendPaystubsResponse,
    summary="Send paystub emails",
    description="Send paystub emails to all employees for an approved payroll run.",
)
async def send_paystubs(
    run_id: UUID,
    current_user: CurrentUser,
) -> SendPaystubsResponse:
    """
    Send paystub emails to all employees.

    This:
    1. Verifies run is in approved status
    2. Sends paystub PDFs to each employee via email
    3. Updates paystub_sent_at for each record

    Prerequisites:
    - Run must be in 'approved' status
    - Paystubs must have been generated (have storage keys)
    """
    try:
        company_id = await get_user_company_id(current_user.id)
        service = get_payroll_run_service(current_user.id, company_id)
        result = await service.send_paystubs(run_id)

        return SendPaystubsResponse(
            sent=result.get("sent", 0),
            errors=result.get("errors"),
        )

    except ValueError as e:
        logger.error(f"Send paystubs error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        logger.exception("Unexpected error sending paystubs")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error sending paystubs",
        )


# =============================================================================
# Paystub Download API
# =============================================================================


class PaystubUrlResponse(BaseModel):
    """Response for paystub download URL."""

    storageKey: str = Field(..., description="Storage key in DO Spaces")
    downloadUrl: str = Field(..., description="Presigned download URL")
    expiresIn: int = Field(default=900, description="URL expiration in seconds")

    model_config = {"populate_by_name": True}


@router.get(
    "/records/{record_id}/paystub-url",
    response_model=PaystubUrlResponse,
    summary="Get paystub download URL",
    description="Get a presigned URL to download a paystub PDF for a payroll record.",
)
async def get_paystub_download_url(
    record_id: str,
    current_user: CurrentUser,
) -> PaystubUrlResponse:
    """
    Get a presigned download URL for a paystub.

    The URL expires after 15 minutes (900 seconds).

    Prerequisites:
    - Paystub must have been generated (paystub_storage_key must exist)
    """
    try:
        # Get the payroll record to verify access and get storage key
        company_id = await get_user_company_id(current_user.id)
        service = get_payroll_run_service(current_user.id, company_id)
        record = await service.get_record(record_id)

        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payroll record not found",
            )

        storage_key = record.get("paystub_storage_key")
        if not storage_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Paystub not yet generated for this record",
            )

        # Generate presigned URL
        storage = get_paystub_storage()
        expires_in = 900  # 15 minutes
        download_url = await storage.generate_presigned_url_async(storage_key, expires_in)

        return PaystubUrlResponse(
            storageKey=storage_key,
            downloadUrl=download_url,
            expiresIn=expires_in,
        )

    except HTTPException:
        raise
    except PaystubStorageConfigError as e:
        logger.error(f"Paystub storage not configured: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Paystub storage is not configured. Please contact administrator.",
        )
    except Exception:
        logger.exception("Unexpected error getting paystub URL")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error getting paystub URL",
        )


# =============================================================================
# Sick Leave Endpoints
# =============================================================================


class SickLeaveConfigResponse(BaseModel):
    """Sick leave configuration for a province."""

    provinceCode: str = Field(alias="province_code")
    paidDaysPerYear: int = Field(alias="paid_days_per_year")
    unpaidDaysPerYear: int = Field(alias="unpaid_days_per_year")
    waitingPeriodDays: int = Field(alias="waiting_period_days")
    allowsCarryover: bool = Field(alias="allows_carryover")
    maxCarryoverDays: int = Field(alias="max_carryover_days")
    accrualMethod: str = Field(alias="accrual_method")
    notes: str | None = None

    model_config = {"populate_by_name": True}


class SickLeaveBalanceResponse(BaseModel):
    """Employee sick leave balance."""

    employeeId: str = Field(alias="employee_id")
    year: int
    paidDaysEntitled: float = Field(alias="paid_days_entitled")
    unpaidDaysEntitled: float = Field(alias="unpaid_days_entitled")
    paidDaysUsed: float = Field(alias="paid_days_used")
    unpaidDaysUsed: float = Field(alias="unpaid_days_used")
    paidDaysRemaining: float = Field(alias="paid_days_remaining")
    unpaidDaysRemaining: float = Field(alias="unpaid_days_remaining")
    carriedOverDays: float = Field(alias="carried_over_days")
    isEligible: bool = Field(alias="is_eligible")
    eligibilityDate: str | None = Field(default=None, alias="eligibility_date")

    model_config = {"populate_by_name": True}


@router.get(
    "/sick-leave/configs",
    response_model=list[SickLeaveConfigResponse],
    summary="Get all sick leave configurations",
    description="Get sick leave rules for all provinces. Supports year and pay_date for version selection.",
)
async def get_sick_leave_configs(
    current_user: CurrentUser,
    year: int = 2025,
    pay_date: date | None = None,
) -> list[SickLeaveConfigResponse]:
    """
    Get sick leave configurations for all provinces.

    Loads configurations from JSON files with support for mid-year changes.
    Use pay_date to get the configuration effective at a specific date.

    Returns the statutory sick leave rules including:
    - Paid and unpaid days per year
    - Waiting period requirements
    - Carryover rules
    """
    from app.services.payroll.sick_leave_config_loader import get_all_configs

    configs = get_all_configs(year, pay_date)
    return [
        SickLeaveConfigResponse(
            province_code=config.province_code,
            paid_days_per_year=config.paid_days_per_year,
            unpaid_days_per_year=config.unpaid_days_per_year,
            waiting_period_days=config.waiting_period_days,
            allows_carryover=config.allows_carryover,
            max_carryover_days=config.max_carryover_days,
            accrual_method=config.accrual_method,
        )
        for config in configs.values()
    ]


@router.get(
    "/sick-leave/configs/{province_code}",
    response_model=SickLeaveConfigResponse,
    summary="Get sick leave configuration for a province",
    description="Get sick leave rules for a specific province. Supports year and pay_date for version selection.",
)
async def get_sick_leave_config_by_province(
    province_code: str,
    current_user: CurrentUser,
    year: int = 2025,
    pay_date: date | None = None,
) -> SickLeaveConfigResponse:
    """
    Get sick leave configuration for a specific province.

    Loads configuration from JSON files with support for mid-year changes.
    Use pay_date to get the configuration effective at a specific date.
    """
    from app.services.payroll.sick_leave_config_loader import get_config

    config = get_config(province_code, year, pay_date)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No sick leave configuration found for province: {province_code}",
        )

    return SickLeaveConfigResponse(
        province_code=config.province_code,
        paid_days_per_year=config.paid_days_per_year,
        unpaid_days_per_year=config.unpaid_days_per_year,
        waiting_period_days=config.waiting_period_days,
        allows_carryover=config.allows_carryover,
        max_carryover_days=config.max_carryover_days,
        accrual_method=config.accrual_method,
    )


@router.get(
    "/employees/{employee_id}/sick-leave/{year}",
    response_model=SickLeaveBalanceResponse,
    summary="Get employee sick leave balance",
    description="Get sick leave balance for an employee for a specific year.",
)
async def get_employee_sick_leave_balance(
    employee_id: str,
    year: int,
    current_user: CurrentUser,
) -> SickLeaveBalanceResponse:
    """
    Get sick leave balance for an employee.

    Returns the employee's sick leave entitlement and usage for the specified year.
    """
    try:
        supabase = get_supabase_client()

        # Get employee's province and hire date
        employee_result = supabase.table("employees").select(
            "province_of_employment, hire_date"
        ).eq("id", employee_id).eq("user_id", current_user.id).single().execute()

        if not employee_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found",
            )

        province = employee_result.data["province_of_employment"]
        hire_date_str = employee_result.data["hire_date"]

        # Try to get existing balance from database
        balance_result = supabase.table("employee_sick_leave_balances").select(
            "*"
        ).eq("employee_id", employee_id).eq("year", year).execute()

        if balance_result.data:
            # Return existing balance
            b = balance_result.data[0]
            paid_remaining = (
                float(b["paid_days_entitled"])
                + float(b["carried_over_days"])
                - float(b["paid_days_used"])
            )
            unpaid_remaining = float(b["unpaid_days_entitled"]) - float(b["unpaid_days_used"])

            return SickLeaveBalanceResponse(
                employee_id=employee_id,
                year=year,
                paid_days_entitled=float(b["paid_days_entitled"]),
                unpaid_days_entitled=float(b["unpaid_days_entitled"]),
                paid_days_used=float(b["paid_days_used"]),
                unpaid_days_used=float(b["unpaid_days_used"]),
                paid_days_remaining=paid_remaining,
                unpaid_days_remaining=unpaid_remaining,
                carried_over_days=float(b["carried_over_days"]),
                is_eligible=b["is_eligible"],
                eligibility_date=b.get("eligibility_date"),
            )

        # Calculate default balance based on province config
        from app.services.payroll.sick_leave_service import SickLeaveService

        service = SickLeaveService()
        hire_date = date.fromisoformat(hire_date_str) if hire_date_str else date.today()

        balance = service.create_new_year_balance(
            employee_id=employee_id,
            year=year,
            province_code=province,
            hire_date=hire_date,
        )

        return SickLeaveBalanceResponse(
            employee_id=balance.employee_id,
            year=balance.year,
            paid_days_entitled=float(balance.paid_days_entitled),
            unpaid_days_entitled=float(balance.unpaid_days_entitled),
            paid_days_used=float(balance.paid_days_used),
            unpaid_days_used=float(balance.unpaid_days_used),
            paid_days_remaining=float(balance.paid_days_remaining),
            unpaid_days_remaining=float(balance.unpaid_days_remaining),
            carried_over_days=float(balance.carried_over_days),
            is_eligible=balance.is_eligible,
            eligibility_date=(
                balance.eligibility_date.isoformat() if balance.eligibility_date else None
            ),
        )

    except HTTPException:
        raise
    except Exception:
        logger.exception("Error getting sick leave balance")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error getting sick leave balance",
        )
