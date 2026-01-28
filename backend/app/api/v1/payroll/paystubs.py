"""
Paystub API Endpoints

Provides endpoints for paystub generation, download, and distribution.
"""

from __future__ import annotations

import io
import logging
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, status
from fastapi.responses import StreamingResponse

from app.api.deps import CurrentUser
from app.core.supabase_client import get_supabase_client
from app.services.payroll import PaystubDataBuilder, PaystubGenerator
from app.services.payroll.paystub_storage import (
    PaystubStorageConfigError,
    get_paystub_storage,
)
from app.services.payroll_run.model_builders import ModelBuilder
from app.services.payroll_run.ytd_calculator import YtdCalculator
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


@router.post(
    "/records/{record_id}/paystub-preview",
    summary="Preview paystub PDF",
    description="Generate and return a paystub PDF preview without storing it.",
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "PDF file stream",
        }
    },
)
async def preview_paystub(
    record_id: str,
    current_user: CurrentUser,
    x_company_id: str | None = Header(None, alias="X-Company-Id"),
) -> StreamingResponse:
    """
    Generate a paystub PDF preview for a payroll record.

    This endpoint generates a PDF without storing it, suitable for:
    - Previewing paystubs before approving a payroll run
    - Reviewing paystub content in pending_approval status

    The PDF is returned as a streaming response.
    """
    try:
        company_id = await get_user_company_id(current_user.id, x_company_id)
        supabase = get_supabase_client()

        # Get the payroll record with full employee, company, and pay group info
        record_result = (
            supabase.table("payroll_records")
            .select(
                """
            *,
            payroll_runs!inner (
                id, user_id, company_id, period_start, period_end, pay_date, status,
                created_at, updated_at
            ),
            employees!inner (
                id, first_name, last_name, email, sin_encrypted,
                province_of_employment, pay_frequency, employment_type,
                annual_salary, hourly_rate, standard_hours_per_week,
                federal_additional_claims,
                provincial_additional_claims, is_cpp_exempt, is_ei_exempt,
                cpp2_exempt, hire_date, termination_date, vacation_config,
                vacation_balance, sick_balance, address_street, address_city,
                address_postal_code, occupation, company_id, pay_group_id,
                companies (
                    id, company_name, business_number, payroll_account_number,
                    province, address_street, address_city, address_postal_code,
                    remitter_type, auto_calculate_deductions, send_paystub_emails,
                    logo_url
                ),
                pay_groups (
                    id, name, description, pay_frequency, employment_type,
                    next_period_end, period_start_day, leave_enabled,
                    overtime_policy, wcb_config, group_benefits
                )
            )
            """
            )
            .eq("id", record_id)
            .eq("user_id", current_user.id)
            .eq("company_id", company_id)
            .execute()
        )

        if not record_result.data or len(record_result.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payroll record not found",
            )

        record_data = record_result.data[0]
        employee_data = record_data["employees"]
        company_data = employee_data.get("companies")
        pay_group_data = employee_data.get("pay_groups")
        run_data = record_data["payroll_runs"]

        if not company_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company data not found for this record",
            )

        # Build domain models
        payroll_run = ModelBuilder.build_payroll_run(run_data)
        employee = ModelBuilder.build_employee(employee_data)
        company = ModelBuilder.build_company(company_data)
        pay_group = ModelBuilder.build_pay_group(pay_group_data) if pay_group_data else None
        payroll_record = ModelBuilder.build_payroll_record(record_data)

        # Get prior YTD records for accurate YTD calculations
        # Use pay_date for YTD year (Canadian payroll tax is based on payment date)
        ytd_calculator = YtdCalculator(supabase, current_user.id, company_id)
        ytd_year = int(run_data["pay_date"][:4])
        ytd_records = await ytd_calculator.get_ytd_records_for_employee(
            record_data["employee_id"],
            str(run_data["id"]),
            ytd_year,
        )

        # Build paystub data
        paystub_builder = PaystubDataBuilder()
        paystub_data = paystub_builder.build(
            record=payroll_record,
            employee=employee,
            payroll_run=payroll_run,
            pay_group=pay_group,
            company=company,
            ytd_records=ytd_records,
            masked_sin="***-***-***",
            skip_logo_download=True,  # Skip logo download for faster preview
        )

        # Generate PDF
        paystub_generator = PaystubGenerator()
        pdf_bytes = paystub_generator.generate_paystub_bytes(paystub_data)

        # Return PDF as streaming response
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'inline; filename="paystub-preview-{record_id}.pdf"',
            },
        )

    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error generating paystub preview")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error generating paystub preview",
        )
