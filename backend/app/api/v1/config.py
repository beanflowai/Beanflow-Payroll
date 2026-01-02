"""Configuration API endpoints.

Provides access to payroll configuration data for frontend display.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from app.services.payroll.province_standards import (
    InvalidProvinceCodeError,
    get_province_standards,
)
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


# =============================================================================
# Province Standards Endpoint
# =============================================================================


class VacationStandardsResponse(BaseModel):
    """Vacation standards summary."""

    minimumWeeks: int
    minimumRate: float
    rateDisplay: str
    upgradeYears: int | None = None
    upgradeWeeks: int | None = None
    notes: str | None = None


class SickLeaveStandardsResponse(BaseModel):
    """Sick leave standards summary."""

    paidDays: int
    unpaidDays: int
    waitingPeriodDays: int
    notes: str | None = None


class OvertimeRulesResponse(BaseModel):
    """Overtime rules for a province."""

    dailyThreshold: int | None = None
    weeklyThreshold: int
    overtimeRate: float
    doubleTimeDaily: int | None = None
    notes: str


class ProvinceStandardsResponse(BaseModel):
    """Aggregated employment standards for a province."""

    provinceCode: str
    provinceName: str
    vacation: VacationStandardsResponse
    sickLeave: SickLeaveStandardsResponse
    overtime: OvertimeRulesResponse
    statutoryHolidaysCount: int


@router.get("/province-standards/{province}", response_model=ProvinceStandardsResponse)
async def get_province_standards_endpoint(
    province: str,
    year: int = Query(default=2025, description="Configuration year"),
) -> ProvinceStandardsResponse:
    """
    Get aggregated employment standards for a province.

    Returns vacation, sick leave, overtime rules, and statutory holiday count.
    Used by frontend to display province-specific employment standards info card.

    Example:
        GET /api/v1/config/province-standards/ON?year=2025

        Response:
        {
            "provinceCode": "ON",
            "provinceName": "Ontario",
            "vacation": {
                "minimumWeeks": 2,
                "minimumRate": 0.04,
                "rateDisplay": "4.00%",
                "upgradeYears": 5,
                "upgradeWeeks": 3
            },
            "sickLeave": {
                "paidDays": 0,
                "unpaidDays": 3,
                "waitingPeriodDays": 0
            },
            "overtime": {
                "dailyThreshold": null,
                "weeklyThreshold": 44,
                "overtimeRate": 1.5,
                "notes": "No daily overtime. Weekly overtime after 44 hours."
            },
            "statutoryHolidaysCount": 9
        }
    """
    try:
        standards = get_province_standards(province, year)
    except InvalidProvinceCodeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return ProvinceStandardsResponse(
        provinceCode=standards.province_code,
        provinceName=standards.province_name,
        vacation=VacationStandardsResponse(
            minimumWeeks=standards.vacation.minimum_weeks,
            minimumRate=standards.vacation.minimum_rate,
            rateDisplay=standards.vacation.rate_display,
            upgradeYears=standards.vacation.upgrade_years,
            upgradeWeeks=standards.vacation.upgrade_weeks,
            notes=standards.vacation.notes,
        ),
        sickLeave=SickLeaveStandardsResponse(
            paidDays=standards.sick_leave.paid_days,
            unpaidDays=standards.sick_leave.unpaid_days,
            waitingPeriodDays=standards.sick_leave.waiting_period_days,
            notes=standards.sick_leave.notes,
        ),
        overtime=OvertimeRulesResponse(
            dailyThreshold=standards.overtime.daily_threshold,
            weeklyThreshold=standards.overtime.weekly_threshold,
            overtimeRate=standards.overtime.overtime_rate,
            doubleTimeDaily=standards.overtime.double_time_daily,
            notes=standards.overtime.notes,
        ),
        statutoryHolidaysCount=standards.statutory_holidays_count,
    )
