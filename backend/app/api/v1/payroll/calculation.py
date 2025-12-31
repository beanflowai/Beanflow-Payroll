"""
Payroll Calculation API Endpoints

Provides endpoints for single and batch payroll calculations.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser
from app.services.payroll import PayrollEngine

from ._helpers import request_to_input, result_to_response
from ._models import (
    BatchCalculationRequest,
    BatchCalculationResponse,
    CalculationResponse,
    EmployeeCalculationRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter()


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
    except Exception:
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
    except Exception:
        logger.exception("Unexpected error during batch calculation")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error during batch payroll calculation",
        )
