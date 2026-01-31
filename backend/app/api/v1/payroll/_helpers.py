"""
Shared helper functions for payroll API endpoints.
"""

from __future__ import annotations

import logging

from fastapi import HTTPException, status

from app.core.supabase_client import get_supabase_client
from app.services.payroll import (
    EmployeePayrollInput,
    PayrollCalculationResult,
)

from ._models import CalculationResponse, EmployeeCalculationRequest

logger = logging.getLogger(__name__)


async def get_user_company_id(
    user_id: str, requested_company_id: str | None = None
) -> str:
    """Get the company ID for a user.

    If requested_company_id is provided, validates that it belongs to the user
    and returns it. Otherwise, returns the oldest (first created) company.

    Args:
        user_id: The user's ID
        requested_company_id: Optional company ID from X-Company-Id header

    Returns:
        The company ID string

    Raises:
        HTTPException: If no company found for user or requested company is invalid
    """
    supabase = get_supabase_client()

    # If a specific company ID is requested, validate it belongs to the user
    if requested_company_id:
        result = supabase.table("companies").select("id").eq(
            "id", requested_company_id
        ).eq("user_id", user_id).execute()

        if result.data and len(result.data) > 0:
            return str(result.data[0]["id"])

        # Invalid company ID provided - return error instead of silent fallback
        logger.warning(
            f"Requested company {requested_company_id} not found for user {user_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found or access denied.",
        )

    # Fallback: return the first (oldest) company for the user
    result = supabase.table("companies").select("id").eq(
        "user_id", user_id
    ).order("created_at", desc=False).limit(1).execute()

    if not result.data or len(result.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No company found for user. Please create a company first.",
        )

    return str(result.data[0]["id"])


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
        bonus_earnings=result.bonus_earnings,
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
        bonus_earnings=request.bonus_earnings,
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
