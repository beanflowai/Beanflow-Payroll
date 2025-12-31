"""
Compensation Service - Manages employee compensation history

Provides:
- Update compensation with atomic RPC (transactional)
- Get current and historical compensation records
"""

from __future__ import annotations

import logging
from uuid import UUID

from postgrest.exceptions import APIError

from app.core.supabase_client import get_supabase_client
from app.models.compensation import (
    CompensationHistory,
    CompensationHistoryCreate,
    from_db_record,
)

logger = logging.getLogger(__name__)


class CompensationService:
    """Service for employee compensation operations."""

    def __init__(self, user_id: str, company_id: str):
        """Initialize service with user context."""
        self.user_id = user_id
        self.company_id = company_id
        self.supabase = get_supabase_client()

    async def update_compensation(
        self,
        employee_id: UUID,
        data: CompensationHistoryCreate,
    ) -> CompensationHistory:
        """Update employee compensation with history tracking.

        Uses a database RPC function for atomic transaction that:
        1. Validates new effective date is after current record
        2. Closes the current active record (sets end_date)
        3. Creates a new compensation record
        4. Syncs current values to employees table

        Args:
            employee_id: The employee's UUID
            data: New compensation data

        Returns:
            The newly created compensation history record

        Raises:
            ValueError: If effective date is invalid or other validation fails
        """
        logger.info(
            "Updating compensation via RPC",
            extra={
                "employee_id": str(employee_id),
                "compensation_type": data.compensationType,
                "effective_date": data.effectiveDate.isoformat(),
            },
        )

        try:
            result = self.supabase.rpc(
                "update_employee_compensation",
                {
                    "p_employee_id": str(employee_id),
                    "p_compensation_type": data.compensationType,
                    "p_annual_salary": (
                        float(data.annualSalary) if data.annualSalary else None
                    ),
                    "p_hourly_rate": (
                        float(data.hourlyRate) if data.hourlyRate else None
                    ),
                    "p_effective_date": data.effectiveDate.isoformat(),
                    "p_change_reason": data.changeReason,
                },
            ).execute()

            if not result.data:
                raise ValueError("Failed to create compensation record")

            new_record = from_db_record(result.data[0])

            logger.info(
                "Compensation updated successfully",
                extra={
                    "employee_id": str(employee_id),
                    "record_id": str(new_record.id),
                },
            )

            return new_record

        except APIError as e:
            # Extract meaningful error message from PostgreSQL error
            error_msg = str(e)
            if "must be after current effective date" in error_msg:
                raise ValueError(
                    "New effective date must be after current effective date"
                ) from e
            if "Invalid compensation type" in error_msg:
                raise ValueError(f"Invalid compensation type: {data.compensationType}") from e
            if "is required and must be positive" in error_msg:
                raise ValueError(error_msg) from e
            # Re-raise other API errors
            logger.exception("RPC error updating compensation")
            raise ValueError(f"Database error: {error_msg}") from e

    async def get_current_compensation(
        self,
        employee_id: UUID,
    ) -> CompensationHistory | None:
        """Get the current active compensation for an employee."""
        result = (
            self.supabase.table("employee_compensation_history")
            .select("*")
            .eq("employee_id", str(employee_id))
            .is_("end_date", "null")
            .execute()
        )

        if result.data:
            return from_db_record(result.data[0])
        return None

    async def get_compensation_history(
        self,
        employee_id: UUID,
    ) -> list[CompensationHistory]:
        """Get full compensation history for an employee."""
        result = (
            self.supabase.table("employee_compensation_history")
            .select("*")
            .eq("employee_id", str(employee_id))
            .order("effective_date", desc=True)
            .execute()
        )

        return [from_db_record(record) for record in result.data]
