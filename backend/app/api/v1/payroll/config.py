"""
Tax Configuration API Endpoints

Provides endpoints for retrieving tax configuration data.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser
from app.models.payroll import Province

from ._models import BPADefaultsResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/tax-config/{province}",
    summary="Get tax configuration for a province",
    description="Get CPP, EI, and tax configuration for a specific province.",
)
async def get_tax_config(
    province: Province,
    current_user: CurrentUser,
    year: int | None = Query(default=None, description="Tax year, defaults to current year"),
    pay_date: date | None = Query(default=None, description="Pay date for edition selection"),
) -> dict[str, Any]:
    """
    Get tax configuration for a specific province.

    Supports year and pay_date parameters for edition selection.
    If versioned config files exist (e.g., provinces_jan.json, provinces_jul.json),
    the pay_date determines which edition to use:
    - Before July 1: January edition
    - July 1 onwards: July edition (default)
    """
    from app.services.payroll import (
        get_cpp_config,
        get_ei_config,
        get_federal_config,
        get_province_config,
    )

    if year is None:
        year = pay_date.year if pay_date else date.today().year

    try:
        return {
            "year": year,
            "province": province.value,
            "cpp": get_cpp_config(year),
            "ei": get_ei_config(year),
            "federal": get_federal_config(year, pay_date),
            "provincial": get_province_config(province.value, year, pay_date),
        }
    except Exception as e:
        logger.exception(f"Error getting tax config for {province}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting tax configuration: {str(e)}",
        )


@router.get(
    "/tax-config",
    summary="Get all tax configuration",
    description="Get CPP, EI, and federal tax configuration.",
)
async def get_all_tax_config(
    current_user: CurrentUser,
    year: int | None = Query(default=None, description="Tax year, defaults to current year"),
    pay_date: date | None = Query(default=None, description="Pay date for edition selection"),
) -> dict[str, Any]:
    """
    Get all tax configuration.

    Supports year and pay_date parameters for edition selection.
    """
    from app.services.payroll import (
        get_all_provinces,
        get_cpp_config,
        get_ei_config,
        get_federal_config,
    )

    if year is None:
        year = pay_date.year if pay_date else date.today().year

    try:
        return {
            "year": year,
            "cpp": get_cpp_config(year),
            "ei": get_ei_config(year),
            "federal": get_federal_config(year, pay_date),
            "supported_provinces": get_all_provinces(year),
        }
    except Exception as e:
        logger.exception("Error getting tax config")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting tax configuration: {str(e)}",
        )


@router.get(
    "/bpa-defaults/{province}",
    response_model=BPADefaultsResponse,
    summary="Get default BPA values",
    description="Get default Basic Personal Amount values for a province.",
)
async def get_bpa_defaults(
    province: Province,
    current_user: CurrentUser,
    year: int | None = Query(default=None, description="Tax year, defaults to current year"),
    pay_date: date | None = Query(default=None, description="Pay date for edition selection"),
) -> BPADefaultsResponse:
    """
    Get default BPA values for frontend forms.

    Returns the federal and provincial BPA based on year and pay_date.
    This endpoint is used by frontend to dynamically set default values
    instead of hardcoding them.
    """
    from app.services.payroll import get_federal_config, get_province_config

    if year is None:
        year = pay_date.year if pay_date else date.today().year

    # Determine edition based on pay date
    if pay_date is not None and pay_date.month < 7:
        edition = "jan"
    else:
        edition = "jul"

    try:
        federal_config = get_federal_config(year, pay_date)
        province_config = get_province_config(province.value, year, pay_date)

        return BPADefaultsResponse(
            year=year,
            edition=edition,
            federalBPA=float(federal_config["bpaf"]),
            provincialBPA=float(province_config["bpa"]),
            province=province.value,
        )
    except Exception as e:
        logger.exception(f"Error getting BPA defaults for {province}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting BPA defaults: {str(e)}",
        )
