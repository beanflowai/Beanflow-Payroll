"""
Overtime Calculation API Endpoints

POST /api/v1/overtime/calculate - Calculate regular/overtime split for daily hours
"""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.services.overtime_calculator import (
    DailyHoursEntry,
    InvalidDateFormatError,
    InvalidProvinceCodeError,
    calculate_overtime_split,
)


router = APIRouter()


class DailyHoursEntryRequest(BaseModel):
    """Request model for a single daily hours entry."""

    date: str = Field(..., description="ISO date string (YYYY-MM-DD)")
    totalHours: float = Field(..., ge=0, le=24, description="Total hours worked (0-24)")
    isHoliday: bool = Field(default=False, description="Whether this day is a holiday")


class OvertimeCalculateRequest(BaseModel):
    """Request model for overtime calculation."""

    province: str = Field(..., min_length=2, max_length=10, description="Province code (e.g., 'ON', 'BC')")
    entries: list[DailyHoursEntryRequest] = Field(..., description="Daily hours entries")


class OvertimeCalculateResponse(BaseModel):
    """Response model for overtime calculation."""

    regularHours: float = Field(..., description="Total regular hours")
    overtimeHours: float = Field(..., description="Total overtime hours (1.5x rate)")
    doubleTimeHours: float = Field(..., description="Total double-time hours (2x rate, BC only)")


@router.post("/calculate", response_model=OvertimeCalculateResponse)
async def calculate_overtime(
    request: OvertimeCalculateRequest,
    _current_user: Annotated[dict, Depends(get_current_user)],
) -> OvertimeCalculateResponse:
    """
    Calculate regular/overtime split for daily hours based on province rules.

    This endpoint accepts daily hours entries and returns the calculated split
    between regular hours, overtime hours, and double-time hours based on
    provincial employment standards.

    Province-specific rules:
    - ON, QC, MB, etc.: Weekly threshold only (typically 44h or 40h/week)
    - AB, BC, NT, NU, YT: Daily threshold (typically 8h/day) + weekly threshold
    - BC special: Double-time for hours > 12/day
    """
    try:
        # Convert request entries to service model
        entries = [
            DailyHoursEntry(
                date=e.date,
                total_hours=Decimal(str(e.totalHours)),
                is_holiday=e.isHoliday,
            )
            for e in request.entries
        ]

        # Calculate overtime split
        result = calculate_overtime_split(entries, request.province)

        return OvertimeCalculateResponse(
            regularHours=float(result.regular_hours),
            overtimeHours=float(result.overtime_hours),
            doubleTimeHours=float(result.double_time_hours),
        )

    except InvalidProvinceCodeError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except InvalidDateFormatError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
