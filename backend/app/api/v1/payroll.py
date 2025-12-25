"""
Payroll API Endpoints

Provides REST API for payroll calculations and payroll run management.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser
from app.models.payroll import PayFrequency, Province
from app.services.payroll import (
    EmployeePayrollInput,
    PayrollCalculationResult,
    PayrollEngine,
)
from app.services.payroll_run_service import get_payroll_run_service

logger = logging.getLogger(__name__)

router = APIRouter()


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
) -> dict[str, Any]:
    """
    Get tax configuration for a specific province.

    Returns the current year's CPP, EI, federal, and provincial tax rates.
    """
    from app.services.payroll import (
        get_cpp_config,
        get_ei_config,
        get_federal_config,
        get_province_config,
    )

    try:
        return {
            "year": 2025,
            "province": province.value,
            "cpp": get_cpp_config(2025),
            "ei": get_ei_config(2025),
            "federal": get_federal_config(2025),
            "provincial": get_province_config(province.value, 2025),
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
) -> dict[str, Any]:
    """
    Get all tax configuration.

    Returns the current year's CPP, EI, and federal tax rates.
    """
    from app.services.payroll import (
        get_all_provinces,
        get_cpp_config,
        get_ei_config,
        get_federal_config,
    )

    try:
        return {
            "year": 2025,
            "cpp": get_cpp_config(2025),
            "ei": get_ei_config(2025),
            "federal": get_federal_config(2025),
            "supported_provinces": get_all_provinces(2025),
        }
    except Exception as e:
        logger.exception("Error getting tax config")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting tax configuration: {str(e)}",
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
        service = get_payroll_run_service(current_user.id, current_user.id)

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
        service = get_payroll_run_service(current_user.id, current_user.id)
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
        service = get_payroll_run_service(current_user.id, current_user.id)
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
        service = get_payroll_run_service(current_user.id, current_user.id)
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
