"""Configuration API endpoints.

Provides access to payroll configuration data for frontend display.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.services.payroll.vacation_pay_config_loader import get_config

router = APIRouter()


class VacationTierResponse(BaseModel):
    """Vacation rate tier based on years of service."""

    minYearsOfService: int
    vacationWeeks: int
    vacationRate: str  # Decimal as string, e.g., "0.04", "0.0577"
    notes: str | None = None


class VacationRatesResponse(BaseModel):
    """Vacation rates configuration for a province."""

    province: str
    name: str
    tiers: list[VacationTierResponse]
    notes: str | None = None


@router.get("/vacation-rates/{province}", response_model=VacationRatesResponse)
async def get_vacation_rates(
    province: str,
    year: int = Query(default=2025, description="Configuration year"),
) -> VacationRatesResponse:
    """
    Get vacation pay rate tiers for a province.

    Returns the minimum vacation rates based on years of service.
    Frontend uses this to show appropriate rate options for the province.

    Example:
        GET /api/v1/config/vacation-rates/SK?year=2025

        Response:
        {
            "province": "SK",
            "name": "Saskatchewan",
            "tiers": [
                {"minYearsOfService": 0, "vacationWeeks": 3, "vacationRate": "0.0577"},
                {"minYearsOfService": 10, "vacationWeeks": 4, "vacationRate": "0.0769"}
            ]
        }
    """
    config = get_config(province, year)

    return VacationRatesResponse(
        province=config.province_code,
        name=config.name,
        tiers=[
            VacationTierResponse(
                minYearsOfService=tier.min_years_of_service,
                vacationWeeks=tier.vacation_weeks,
                vacationRate=str(tier.vacation_rate),
                notes=tier.notes,
            )
            for tier in config.tiers
        ],
        notes=config.notes,
    )
