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
