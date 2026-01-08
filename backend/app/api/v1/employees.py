"""
Employee API Endpoints

Provides REST API for employee-related operations including compensation management.
"""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, status

from app.api.deps import CurrentUser
from app.api.v1.payroll._helpers import get_user_company_id
from app.core.supabase_client import get_supabase_client
from app.models.compensation import (
    CompensationHistory,
    CompensationHistoryCreate,
)
from app.models.payroll import (
    EmployeeTaxClaim,
    EmployeeTaxClaimCreate,
    EmployeeTaxClaimUpdate,
)
from app.services.compensation_service import CompensationService

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Compensation Endpoints
# =============================================================================


@router.post(
    "/{employee_id}/compensation",
    response_model=CompensationHistory,
    summary="Update employee compensation",
    description="Update salary or hourly rate with history tracking.",
)
async def update_compensation(
    employee_id: UUID,
    request: CompensationHistoryCreate,
    current_user: CurrentUser,
    x_company_id: str | None = Header(None, alias="X-Company-Id"),
) -> CompensationHistory:
    """
    Update employee compensation with history tracking.

    This endpoint:
    1. Closes the current compensation record (sets end_date)
    2. Creates a new compensation record with the new values
    3. Syncs the current values to the employees table

    The effective_date determines when the new compensation takes effect.
    """
    try:
        company_id = await get_user_company_id(current_user.id, x_company_id)
        service = CompensationService(current_user.id, company_id)

        # Verify employee belongs to user
        supabase = get_supabase_client()
        employee_result = (
            supabase.table("employees")
            .select("id")
            .eq("id", str(employee_id))
            .eq("user_id", current_user.id)
            .execute()
        )

        if not employee_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found",
            )

        result = await service.update_compensation(employee_id, request)
        return result

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Compensation update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception:
        logger.exception("Unexpected error updating compensation")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error updating compensation",
        )


# =============================================================================
# Tax Claims Endpoints (TD1 by year)
# =============================================================================


@router.get(
    "/{employee_id}/tax-claims",
    response_model=list[EmployeeTaxClaim],
    summary="Get employee tax claims",
    description="Get all TD1 tax claims for an employee, ordered by year descending.",
)
async def get_tax_claims(
    employee_id: UUID,
    current_user: CurrentUser,
    x_company_id: str | None = Header(None, alias="X-Company-Id"),
) -> list[EmployeeTaxClaim]:
    """Get all tax claims for an employee."""
    try:
        company_id = await get_user_company_id(current_user.id, x_company_id)
        supabase = get_supabase_client()

        # Verify employee belongs to user/company
        employee_result = (
            supabase.table("employees")
            .select("id")
            .eq("id", str(employee_id))
            .eq("user_id", current_user.id)
            .eq("company_id", company_id)
            .execute()
        )

        if not employee_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found",
            )

        # Get tax claims (filter by company_id for multi-company support)
        result = (
            supabase.table("employee_tax_claims")
            .select("*")
            .eq("employee_id", str(employee_id))
            .eq("user_id", current_user.id)
            .eq("company_id", company_id)
            .order("tax_year", desc=True)
            .execute()
        )

        return [EmployeeTaxClaim(**row) for row in result.data]

    except HTTPException:
        raise
    except Exception:
        logger.exception("Error fetching tax claims")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error fetching tax claims",
        )


@router.get(
    "/{employee_id}/tax-claims/{tax_year}",
    response_model=EmployeeTaxClaim,
    summary="Get tax claim for specific year",
    description="Get TD1 tax claim for a specific year.",
)
async def get_tax_claim_by_year(
    employee_id: UUID,
    tax_year: int,
    current_user: CurrentUser,
    x_company_id: str | None = Header(None, alias="X-Company-Id"),
) -> EmployeeTaxClaim:
    """Get tax claim for a specific year."""
    try:
        company_id = await get_user_company_id(current_user.id, x_company_id)
        supabase = get_supabase_client()

        # Use limit(1) instead of single() to avoid exception when no record found
        result = (
            supabase.table("employee_tax_claims")
            .select("*")
            .eq("employee_id", str(employee_id))
            .eq("user_id", current_user.id)
            .eq("company_id", company_id)
            .eq("tax_year", tax_year)
            .limit(1)
            .execute()
        )

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tax claim not found for year {tax_year}",
            )

        return EmployeeTaxClaim(**result.data[0])

    except HTTPException:
        raise
    except Exception:
        logger.exception("Error fetching tax claim")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error fetching tax claim",
        )


@router.post(
    "/{employee_id}/tax-claims",
    response_model=EmployeeTaxClaim,
    status_code=status.HTTP_201_CREATED,
    summary="Create tax claim for a year",
    description="Create a new TD1 tax claim record for a specific year. BPA values are derived from tax configuration.",
)
async def create_tax_claim(
    employee_id: UUID,
    request: EmployeeTaxClaimCreate,
    current_user: CurrentUser,
    x_company_id: str | None = Header(None, alias="X-Company-Id"),
) -> EmployeeTaxClaim:
    """Create a tax claim record for a specific year.

    BPA values are automatically derived from tax configuration based on
    the employee's province and the requested tax year.
    """
    from app.services.payroll import get_federal_config, get_province_config

    try:
        company_id = await get_user_company_id(current_user.id, x_company_id)
        supabase = get_supabase_client()

        # Get employee with province for BPA lookup
        employee_result = (
            supabase.table("employees")
            .select("id, province_of_employment")
            .eq("id", str(employee_id))
            .eq("user_id", current_user.id)
            .eq("company_id", company_id)
            .execute()
        )

        if not employee_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found",
            )

        province = employee_result.data[0]["province_of_employment"]

        # Derive BPA from tax configuration (server-side)
        try:
            federal_config = get_federal_config(request.tax_year, None)
            province_config = get_province_config(province, request.tax_year, None)
            federal_bpa = float(federal_config["bpaf"])
            provincial_bpa = float(province_config["bpa"])
        except Exception as e:
            logger.warning(f"Failed to get BPA from tax config: {e}, using fallback")
            # Fallback to default values if tax config not available
            federal_bpa = 16129.0  # 2025 federal BPA
            provincial_bpa = 12000.0  # Conservative default

        # Create tax claim with server-derived BPA
        record = {
            "employee_id": str(employee_id),
            "company_id": company_id,
            "user_id": current_user.id,
            "tax_year": request.tax_year,
            "federal_bpa": federal_bpa,
            "federal_additional_claims": float(request.federal_additional_claims),
            "provincial_bpa": provincial_bpa,
            "provincial_additional_claims": float(request.provincial_additional_claims),
        }

        result = (
            supabase.table("employee_tax_claims")
            .insert(record)
            .execute()
        )

        # Verify insert succeeded
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create tax claim",
            )

        return EmployeeTaxClaim(**result.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error creating tax claim")
        if "duplicate key" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Tax claim already exists for year {request.tax_year}",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error creating tax claim",
        )


@router.put(
    "/{employee_id}/tax-claims/{tax_year}",
    response_model=EmployeeTaxClaim,
    summary="Update tax claim for a year",
    description="Update TD1 additional claims for a specific year. Set recalculate_bpa=true to refresh BPA values (e.g., after province change).",
)
async def update_tax_claim(
    employee_id: UUID,
    tax_year: int,
    request: EmployeeTaxClaimUpdate,
    current_user: CurrentUser,
    x_company_id: str | None = Header(None, alias="X-Company-Id"),
) -> EmployeeTaxClaim:
    """Update tax claim for a specific year.

    By default, only additional claims can be updated. Set recalculate_bpa=true
    to refresh BPA values from tax config (useful when employee's province changes).
    """
    from app.services.payroll import get_federal_config, get_province_config

    try:
        company_id = await get_user_company_id(current_user.id, x_company_id)
        supabase = get_supabase_client()

        # Build update data
        update_data: dict[str, float] = {}
        if request.federal_additional_claims is not None:
            update_data["federal_additional_claims"] = float(request.federal_additional_claims)
        if request.provincial_additional_claims is not None:
            update_data["provincial_additional_claims"] = float(request.provincial_additional_claims)

        # Handle BPA recalculation if requested (Fix #3)
        if request.recalculate_bpa:
            # Get employee's current province
            employee_result = (
                supabase.table("employees")
                .select("province_of_employment")
                .eq("id", str(employee_id))
                .eq("user_id", current_user.id)
                .eq("company_id", company_id)
                .execute()
            )

            if not employee_result.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Employee not found",
                )

            province = employee_result.data[0]["province_of_employment"]

            # Derive BPA from tax configuration
            try:
                federal_config = get_federal_config(tax_year, None)
                province_config = get_province_config(province, tax_year, None)
                update_data["federal_bpa"] = float(federal_config["bpaf"])
                update_data["provincial_bpa"] = float(province_config["bpa"])
            except Exception as e:
                logger.warning(f"Failed to get BPA from tax config: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to get BPA for province {province} and year {tax_year}",
                )

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update",
            )

        result = (
            supabase.table("employee_tax_claims")
            .update(update_data)
            .eq("employee_id", str(employee_id))
            .eq("user_id", current_user.id)
            .eq("company_id", company_id)
            .eq("tax_year", tax_year)
            .execute()
        )

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tax claim not found for year {tax_year}",
            )

        return EmployeeTaxClaim(**result.data[0])

    except HTTPException:
        raise
    except Exception:
        logger.exception("Error updating tax claim")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error updating tax claim",
        )
