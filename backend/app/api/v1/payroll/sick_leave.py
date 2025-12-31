"""
Sick Leave API Endpoints

Provides endpoints for sick leave configuration and balance management.
"""

from __future__ import annotations

import logging
from datetime import date

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser
from app.core.supabase_client import get_supabase_client

from ._models import SickLeaveBalanceResponse, SickLeaveConfigResponse

logger = logging.getLogger(__name__)

router = APIRouter()


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
            initial_days_after_qualifying=config.initial_days_after_qualifying,
            days_per_month_after_initial=config.days_per_month_after_initial,
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
        initial_days_after_qualifying=config.initial_days_after_qualifying,
        days_per_month_after_initial=config.days_per_month_after_initial,
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
