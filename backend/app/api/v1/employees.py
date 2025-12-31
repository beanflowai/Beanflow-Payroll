"""
Employee API Endpoints

Provides REST API for employee-related operations including compensation management.
"""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser
from app.core.supabase_client import get_supabase_client
from app.models.compensation import (
    CompensationHistory,
    CompensationHistoryCreate,
)
from app.services.compensation_service import CompensationService

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_user_company_id(user_id: str) -> str:
    """Get the primary company ID for a user.

    Args:
        user_id: The user's ID

    Returns:
        The company ID string

    Raises:
        HTTPException: If no company found for user
    """
    supabase = get_supabase_client()
    result = (
        supabase.table("companies")
        .select("id")
        .eq("user_id", user_id)
        .order("created_at", desc=False)
        .limit(1)
        .execute()
    )

    if not result.data or len(result.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No company found for user. Please create a company first.",
        )

    return str(result.data[0]["id"])


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
        company_id = await get_user_company_id(current_user.id)
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
