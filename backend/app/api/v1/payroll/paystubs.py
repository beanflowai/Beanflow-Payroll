"""
Paystub API Endpoints

Provides endpoints for paystub generation, download, and distribution.
"""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, status

from app.api.deps import CurrentUser
from app.services.payroll.paystub_storage import (
    PaystubStorageConfigError,
    get_paystub_storage,
)
from app.services.payroll_run_service import get_payroll_run_service

from ._helpers import get_user_company_id
from ._models import PaystubUrlResponse, SendPaystubsResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/runs/{run_id}/send-paystubs",
    response_model=SendPaystubsResponse,
    summary="Send paystub emails",
    description="Send paystub emails to all employees for an approved payroll run.",
)
async def send_paystubs(
    run_id: UUID,
    current_user: CurrentUser,
    x_company_id: str | None = Header(None, alias="X-Company-Id"),
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
        company_id = await get_user_company_id(current_user.id, x_company_id)
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


@router.get(
    "/records/{record_id}/paystub-url",
    response_model=PaystubUrlResponse,
    summary="Get paystub download URL",
    description="Get a presigned URL to download a paystub PDF for a payroll record.",
)
async def get_paystub_download_url(
    record_id: str,
    current_user: CurrentUser,
    x_company_id: str | None = Header(None, alias="X-Company-Id"),
) -> PaystubUrlResponse:
    """
    Get a presigned download URL for a paystub.

    The URL expires after 15 minutes (900 seconds).

    Prerequisites:
    - Paystub must have been generated (paystub_storage_key must exist)
    """
    try:
        # Get the payroll record to verify access and get storage key
        company_id = await get_user_company_id(current_user.id, x_company_id)
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
