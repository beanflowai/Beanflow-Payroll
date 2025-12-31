"""
Remittance API Endpoints

Provides REST API for PD7A PDF generation.
Frontend handles CRUD operations directly via Supabase.
"""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response

from app.api.deps import CurrentUser
from app.core.supabase_client import get_supabase_client
from app.models.remittance import PD7ARemittanceVoucher
from app.services.remittance.pd7a_generator import PD7APDFGenerator

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/pd7a/{company_id}/{remittance_id}",
    summary="Generate PD7A remittance voucher PDF",
    description="Generate and download a PD7A Statement of Account PDF.",
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "PDF file for download"
        }
    }
)
async def generate_pd7a_voucher(
    company_id: UUID,
    remittance_id: UUID,
    current_user: CurrentUser,
) -> Response:
    """
    Generate PD7A remittance voucher PDF.

    Returns PDF file for download.
    """
    try:
        supabase = get_supabase_client()

        # Get remittance period
        period_result = (
            supabase.table("remittance_periods")
            .select("*")
            .eq("id", str(remittance_id))
            .eq("company_id", str(company_id))
            .eq("user_id", current_user.id)
            .single()
            .execute()
        )

        if not period_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Remittance period not found"
            )

        period = period_result.data

        # Get company info for employer name and payroll account
        company_result = (
            supabase.table("companies")
            .select("company_name, payroll_account_number")
            .eq("id", str(company_id))
            .eq("user_id", current_user.id)
            .single()
            .execute()
        )

        if not company_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found"
            )

        company = company_result.data

        # Build PD7A voucher
        voucher = PD7ARemittanceVoucher(
            employer_name=company["company_name"],
            payroll_account_number=company["payroll_account_number"],
            period_start=date.fromisoformat(period["period_start"]),
            period_end=date.fromisoformat(period["period_end"]),
            due_date=date.fromisoformat(period["due_date"]),
            line_10_cpp_employee=Decimal(str(period["cpp_employee"])),
            line_10_cpp_employer=Decimal(str(period["cpp_employer"])),
            line_10_ei_employee=Decimal(str(period["ei_employee"])),
            line_10_ei_employer=Decimal(str(period["ei_employer"])),
            line_10_income_tax=Decimal(str(period["federal_tax"])) + Decimal(str(period["provincial_tax"]))
        )

        # Generate PDF
        generator = PD7APDFGenerator()
        pdf_bytes = generator.generate_pdf(voucher)

        # Generate filename
        filename = f"PD7A_{period['period_start']}_{period['period_end']}.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error generating PD7A PDF")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error generating PDF"
        )
