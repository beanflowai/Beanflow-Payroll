"""
T4 Year-End Processing API Endpoints

Provides REST API for T4 generation, storage, and download.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response

from app.api.deps import CurrentUser
from app.core.security import mask_sin
from app.core.supabase_client import get_supabase_client
from app.models.t4 import (
    T4GenerationRequest,
    T4GenerationResponse,
    T4SlipListResponse,
    T4SlipSummary,
    T4Status,
    T4SummaryResponse,
)
from app.services.t4 import (
    T4AggregationService,
    T4PDFGenerator,
    T4XMLGenerator,
    get_t4_storage,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# T4 Slip Endpoints
# =============================================================================


@router.get(
    "/slips/{company_id}/{tax_year}",
    summary="List T4 slips for a tax year",
    response_model=T4SlipListResponse,
)
async def list_t4_slips(
    company_id: UUID,
    tax_year: int,
    current_user: CurrentUser,
) -> T4SlipListResponse:
    """
    List all T4 slips for a company and tax year.

    Returns summary information for each slip including
    employee name, employment income, and status.
    """
    supabase = get_supabase_client()

    result = (
        supabase.table("t4_slips")
        .select("id, employee_id, status, slip_data, pdf_storage_key")
        .eq("company_id", str(company_id))
        .eq("user_id", current_user.id)
        .eq("tax_year", tax_year)
        .order("created_at", desc=False)
        .execute()
    )

    slips = []
    for row in result.data or []:
        slip_data = row.get("slip_data", {})
        # PDF is available if we have slip_data (can generate on-the-fly) or storage key
        pdf_available = bool(slip_data) or bool(row.get("pdf_storage_key"))
        slips.append(
            T4SlipSummary(
                id=UUID(row["id"]),
                employee_id=UUID(row["employee_id"]),
                employee_name=slip_data.get("employee_full_name", "Unknown"),
                sin_masked=mask_sin(slip_data.get("sin", "")),
                box_14_employment_income=slip_data.get("box_14_employment_income", 0),
                box_22_income_tax_deducted=slip_data.get("box_22_income_tax_deducted", 0),
                status=T4Status(row["status"]),
                pdf_available=pdf_available,
            )
        )

    return T4SlipListResponse(
        tax_year=tax_year,
        total_count=len(slips),
        slips=slips,
    )


@router.post(
    "/slips/{company_id}/{tax_year}/generate",
    summary="Generate T4 slips",
    response_model=T4GenerationResponse,
)
async def generate_t4_slips(
    company_id: UUID,
    tax_year: int,
    current_user: CurrentUser,
    request: T4GenerationRequest | None = None,
) -> T4GenerationResponse:
    """
    Generate T4 slips for all employees (or specific employees).

    This will aggregate payroll data for the tax year and create
    T4 slip records with PDF files stored in cloud storage.
    """
    supabase = get_supabase_client()

    # Initialize services
    aggregation = T4AggregationService(
        supabase=supabase,
        user_id=current_user.id,
        company_id=str(company_id),
    )
    pdf_generator = T4PDFGenerator()

    try:
        storage = get_t4_storage()
    except Exception as e:
        logger.warning(f"Storage not configured: {e}")
        storage = None

    # Get company info
    company = await aggregation.get_company()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    # Generate T4 slips
    employee_ids = request.employee_ids if request else None
    regenerate = request.regenerate if request else False

    slips = await aggregation.generate_all_t4_slips(
        tax_year=tax_year,
        employee_ids=employee_ids,
    )

    if not slips:
        return T4GenerationResponse(
            success=True,
            tax_year=tax_year,
            slips_generated=0,
            message="No payroll data found for the tax year",
        )

    # Generate PDFs and save to database
    slips_generated = 0
    slips_skipped = 0
    errors: list[dict[str, Any]] = []

    for slip in slips:
        try:
            # Check if slip already exists
            existing = (
                supabase.table("t4_slips")
                .select("id")
                .eq("company_id", str(company_id))
                .eq("employee_id", str(slip.employee_id))
                .eq("tax_year", tax_year)
                .eq("amendment_number", 0)
                .maybe_single()
                .execute()
            )

            if existing.data and not regenerate:
                slips_skipped += 1
                continue

            # Generate PDF
            pdf_bytes = pdf_generator.generate_t4_slip_pdf(slip)

            # Save to storage
            pdf_storage_key = None
            if storage:
                pdf_storage_key = await storage.save_t4_slip(
                    pdf_bytes=pdf_bytes,
                    company_name=company.company_name,
                    tax_year=tax_year,
                    employee_id=slip.employee_id,
                )

            # Build slip_data JSON
            slip_data = slip.model_dump(mode="json")

            # Upsert to database
            if existing.data:
                # Update existing
                supabase.table("t4_slips").update({
                    "slip_data": slip_data,
                    "pdf_storage_key": pdf_storage_key,
                    "pdf_generated_at": datetime.now().isoformat(),
                    "status": T4Status.GENERATED.value,
                    "updated_at": datetime.now().isoformat(),
                }).eq("id", existing.data["id"]).execute()
            else:
                # Insert new
                supabase.table("t4_slips").insert({
                    "company_id": str(company_id),
                    "user_id": current_user.id,
                    "employee_id": str(slip.employee_id),
                    "tax_year": tax_year,
                    "slip_data": slip_data,
                    "pdf_storage_key": pdf_storage_key,
                    "pdf_generated_at": datetime.now().isoformat(),
                    "status": T4Status.GENERATED.value,
                }).execute()

            slips_generated += 1

        except Exception as e:
            logger.error(f"Failed to generate T4 for employee {slip.employee_id}: {e}")
            errors.append({
                "employee_id": str(slip.employee_id),
                "message": str(e),
            })

    return T4GenerationResponse(
        success=len(errors) == 0,
        tax_year=tax_year,
        slips_generated=slips_generated,
        slips_skipped=slips_skipped,
        errors=errors,
        message=f"Generated {slips_generated} T4 slips" + (f", skipped {slips_skipped}" if slips_skipped else ""),
    )


@router.get(
    "/slips/{company_id}/{tax_year}/{employee_id}/download",
    summary="Download T4 slip PDF",
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "PDF file for download",
        }
    },
)
async def download_t4_slip(
    company_id: UUID,
    tax_year: int,
    employee_id: UUID,
    current_user: CurrentUser,
) -> Response:
    """
    Download T4 slip PDF for an employee.

    Returns the PDF file directly for download.
    """
    supabase = get_supabase_client()

    # Get T4 slip record
    result = (
        supabase.table("t4_slips")
        .select("id, slip_data, pdf_storage_key")
        .eq("company_id", str(company_id))
        .eq("user_id", current_user.id)
        .eq("employee_id", str(employee_id))
        .eq("tax_year", tax_year)
        .order("amendment_number", desc=True)
        .limit(1)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="T4 slip not found",
        )

    slip_record = result.data[0]
    storage_key = slip_record.get("pdf_storage_key")
    pdf_bytes: bytes | None = None

    # Try to get from storage first
    if storage_key:
        try:
            storage = get_t4_storage()
            pdf_bytes = await storage.get_file_content(storage_key)
        except Exception as e:
            logger.warning(f"Failed to download T4 from storage, will generate on-the-fly: {e}")

    # Fallback: generate on-the-fly
    if not pdf_bytes:
        from app.models.t4 import T4SlipData

        slip_data_json = slip_record.get("slip_data")
        if not slip_data_json:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="T4 data not available",
            )

        try:
            slip_data = T4SlipData.model_validate(slip_data_json)
            pdf_generator = T4PDFGenerator()
            pdf_bytes = pdf_generator.generate_t4_slip_pdf(slip_data)
        except Exception as e:
            logger.error(f"Failed to generate T4 PDF on-the-fly: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate T4 PDF",
            )

    # Build filename
    slip_data = slip_record.get("slip_data", {})
    employee_name = slip_data.get("employee_last_name", "Unknown")
    filename = f"T4_{tax_year}_{employee_name}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


# =============================================================================
# T4 Summary Endpoints
# =============================================================================


@router.get(
    "/summary/{company_id}/{tax_year}",
    summary="Get T4 Summary for a tax year",
    response_model=T4SummaryResponse,
)
async def get_t4_summary(
    company_id: UUID,
    tax_year: int,
    current_user: CurrentUser,
) -> T4SummaryResponse:
    """
    Get the T4 Summary for a company and tax year.

    Returns the summary data if it exists, or 404 if not generated yet.
    """
    supabase = get_supabase_client()

    result = (
        supabase.table("t4_summaries")
        .select("*")
        .eq("company_id", str(company_id))
        .eq("user_id", current_user.id)
        .eq("tax_year", tax_year)
        .limit(1)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="T4 Summary not found. Use POST /generate to create one.",
        )

    from app.models.t4 import T4Summary

    summary = T4Summary.model_validate(result.data[0])

    return T4SummaryResponse(
        success=True,
        summary=summary,
        message="T4 Summary retrieved successfully",
    )


@router.post(
    "/summary/{company_id}/{tax_year}/generate",
    summary="Generate T4 Summary",
    response_model=T4SummaryResponse,
)
async def generate_t4_summary(
    company_id: UUID,
    tax_year: int,
    current_user: CurrentUser,
) -> T4SummaryResponse:
    """
    Generate T4 Summary from existing T4 slips.

    Also generates the T619 XML file for CRA submission.
    """
    supabase = get_supabase_client()

    # Initialize services
    aggregation = T4AggregationService(
        supabase=supabase,
        user_id=current_user.id,
        company_id=str(company_id),
    )
    pdf_generator = T4PDFGenerator()
    xml_generator = T4XMLGenerator()

    try:
        storage = get_t4_storage()
    except Exception as e:
        logger.warning(f"Storage not configured: {e}")
        storage = None

    # Get company info
    company = await aggregation.get_company()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    # Generate T4 slips (or get existing)
    slips = await aggregation.generate_all_t4_slips(tax_year)

    if not slips:
        return T4SummaryResponse(
            success=False,
            message="No T4 slips found for the tax year",
        )

    # Generate summary
    summary = await aggregation.generate_t4_summary(tax_year, slips)
    if not summary:
        return T4SummaryResponse(
            success=False,
            message="Failed to generate T4 Summary",
        )

    # Generate PDF
    summary_pdf = pdf_generator.generate_t4_summary_pdf(summary, slips)

    # Generate XML
    summary_xml = xml_generator.generate_xml(summary, slips)

    # Save to storage
    pdf_storage_key = None
    xml_storage_key = None

    if storage:
        try:
            pdf_storage_key = await storage.save_t4_summary(
                pdf_bytes=summary_pdf,
                company_name=company.company_name,
                tax_year=tax_year,
            )
            xml_storage_key = await storage.save_t4_xml(
                xml_content=summary_xml,
                company_name=company.company_name,
                tax_year=tax_year,
                payroll_account=company.payroll_account_number,
            )
        except Exception as e:
            logger.error(f"Failed to save T4 Summary to storage: {e}")

    # Update summary with storage keys
    summary.pdf_storage_key = pdf_storage_key
    summary.xml_storage_key = xml_storage_key
    summary.generated_at = datetime.now()
    summary.status = T4Status.GENERATED

    # Save to database
    summary_data = summary.model_dump(mode="json")

    # Check if summary exists
    existing = (
        supabase.table("t4_summaries")
        .select("id")
        .eq("company_id", str(company_id))
        .eq("tax_year", tax_year)
        .maybe_single()
        .execute()
    )

    if existing.data:
        supabase.table("t4_summaries").update(summary_data).eq(
            "id", existing.data["id"]
        ).execute()
    else:
        supabase.table("t4_summaries").insert(summary_data).execute()

    return T4SummaryResponse(
        success=True,
        summary=summary,
        message=f"Generated T4 Summary with {summary.total_number_of_t4_slips} slips",
    )


@router.get(
    "/summary/{company_id}/{tax_year}/download-pdf",
    summary="Download T4 Summary PDF",
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "PDF file for download",
        }
    },
)
async def download_t4_summary_pdf(
    company_id: UUID,
    tax_year: int,
    current_user: CurrentUser,
) -> Response:
    """Download T4 Summary PDF."""
    supabase = get_supabase_client()

    result = (
        supabase.table("t4_summaries")
        .select("pdf_storage_key")
        .eq("company_id", str(company_id))
        .eq("user_id", current_user.id)
        .eq("tax_year", tax_year)
        .maybe_single()
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="T4 Summary not found",
        )

    storage_key = result.data.get("pdf_storage_key")
    if not storage_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="T4 Summary PDF not available",
        )

    try:
        storage = get_t4_storage()
        pdf_bytes = await storage.get_file_content(storage_key)
    except Exception as e:
        logger.error(f"Failed to download T4 Summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve T4 Summary PDF",
        )

    filename = f"T4_Summary_{tax_year}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get(
    "/summary/{company_id}/{tax_year}/download-xml",
    summary="Download T4 XML for CRA submission",
    responses={
        200: {
            "content": {"application/xml": {}},
            "description": "XML file for CRA electronic filing",
        }
    },
)
async def download_t4_xml(
    company_id: UUID,
    tax_year: int,
    current_user: CurrentUser,
) -> Response:
    """Download T4 XML file for CRA electronic submission."""
    supabase = get_supabase_client()

    result = (
        supabase.table("t4_summaries")
        .select("xml_storage_key")
        .eq("company_id", str(company_id))
        .eq("user_id", current_user.id)
        .eq("tax_year", tax_year)
        .maybe_single()
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="T4 Summary not found",
        )

    storage_key = result.data.get("xml_storage_key")
    if not storage_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="T4 XML not available",
        )

    try:
        storage = get_t4_storage()
        xml_bytes = await storage.get_file_content(storage_key)
    except Exception as e:
        logger.error(f"Failed to download T4 XML: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve T4 XML",
        )

    # Get company info for filename
    company_result = (
        supabase.table("companies")
        .select("payroll_account_number")
        .eq("id", str(company_id))
        .maybe_single()
        .execute()
    )

    account = company_result.data.get("payroll_account_number", "unknown") if company_result.data else "unknown"
    filename = f"T4_{account}_{tax_year}.xml"

    return Response(
        content=xml_bytes,
        media_type="application/xml",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
