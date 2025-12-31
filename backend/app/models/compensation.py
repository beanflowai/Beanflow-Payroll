"""
Compensation History Pydantic Models

Models for tracking employee salary/hourly rate changes over time.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal, cast
from uuid import UUID

from pydantic import BaseModel, model_validator

# =============================================================================
# Compensation Type
# =============================================================================

CompensationType = Literal["salary", "hourly"]


# =============================================================================
# Compensation History Models
# =============================================================================

class CompensationHistoryCreate(BaseModel):
    """Request model for creating/updating compensation."""

    compensationType: CompensationType  # noqa: N815 - camelCase data field
    annualSalary: Decimal | None = None  # noqa: N815
    hourlyRate: Decimal | None = None  # noqa: N815
    effectiveDate: date  # noqa: N815
    changeReason: str | None = None  # noqa: N815

    @model_validator(mode="after")
    def validate_compensation(self) -> "CompensationHistoryCreate":
        """Validate that the correct field is provided based on compensation type."""
        if self.compensationType == "salary" and self.annualSalary is None:
            raise ValueError("annualSalary is required for salary compensation type")
        if self.compensationType == "hourly" and self.hourlyRate is None:
            raise ValueError("hourlyRate is required for hourly compensation type")
        return self


class CompensationHistory(BaseModel):
    """Complete compensation history record from database."""

    id: UUID
    employeeId: UUID  # noqa: N815 - camelCase data field
    compensationType: CompensationType  # noqa: N815
    annualSalary: Decimal | None = None  # noqa: N815
    hourlyRate: Decimal | None = None  # noqa: N815
    effectiveDate: date  # noqa: N815
    endDate: date | None = None  # noqa: N815
    changeReason: str | None = None  # noqa: N815
    createdAt: datetime  # noqa: N815

    model_config = {"from_attributes": True}


class CompensationHistoryResponse(BaseModel):
    """API response for compensation history list."""

    history: list[CompensationHistory]
    currentCompensation: CompensationHistory | None = None  # noqa: N815


# =============================================================================
# Helper for DB field mapping
# =============================================================================

# Map camelCase model fields to snake_case database columns
COMPENSATION_DB_FIELD_MAP: dict[str, str] = {
    "employeeId": "employee_id",
    "compensationType": "compensation_type",
    "annualSalary": "annual_salary",
    "hourlyRate": "hourly_rate",
    "effectiveDate": "effective_date",
    "endDate": "end_date",
    "changeReason": "change_reason",
    "createdAt": "created_at",
}


def to_db_record(data: CompensationHistoryCreate, employee_id: UUID) -> dict[str, object]:
    """Convert model to database record format (snake_case)."""
    return {
        "employee_id": str(employee_id),
        "compensation_type": data.compensationType,
        "annual_salary": float(data.annualSalary) if data.annualSalary else None,
        "hourly_rate": float(data.hourlyRate) if data.hourlyRate else None,
        "effective_date": data.effectiveDate.isoformat(),
        "change_reason": data.changeReason,
    }


def from_db_record(record: dict[str, Any]) -> CompensationHistory:
    """Convert database record to model format (camelCase)."""
    return CompensationHistory(
        id=cast(UUID, record["id"]),
        employeeId=cast(UUID, record["employee_id"]),
        compensationType=cast(CompensationType, record["compensation_type"]),
        annualSalary=Decimal(str(record["annual_salary"])) if record.get("annual_salary") else None,
        hourlyRate=Decimal(str(record["hourly_rate"])) if record.get("hourly_rate") else None,
        effectiveDate=cast(date, record["effective_date"]),
        endDate=cast(date | None, record.get("end_date")),
        changeReason=cast(str | None, record.get("change_reason")),
        createdAt=cast(datetime, record["created_at"]),
    )
