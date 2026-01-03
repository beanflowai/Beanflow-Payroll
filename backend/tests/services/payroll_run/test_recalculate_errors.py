"""
Tests for PayrollRunOperations.recalculate_run error handling.

Covers:
- Run not found
- Wrong status (not draft)
- No records found
"""

from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from app.services.payroll_run.run_operations import PayrollRunOperations

from .conftest import (
    make_payroll_run,
)


class TestRecalculateRunErrors:
    """Tests for recalculate_run error handling."""

    @pytest.mark.asyncio
    async def test_run_not_found(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        sample_run_id: UUID,
    ):
        """Should raise ValueError when run is not found."""
        mock_get_run_func.return_value = None

        with pytest.raises(ValueError, match="Payroll run not found"):
            await run_operations.recalculate_run(sample_run_id)

    @pytest.mark.asyncio
    async def test_run_not_in_draft_status(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        sample_run_id: UUID,
    ):
        """Should raise ValueError when run is not in draft status."""
        mock_get_run_func.return_value = make_payroll_run(
            run_id=str(sample_run_id),
            status="pending_approval",
        )

        with pytest.raises(ValueError, match="Cannot recalculate.*pending_approval.*not 'draft'"):
            await run_operations.recalculate_run(sample_run_id)

    @pytest.mark.asyncio
    async def test_run_in_approved_status(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        sample_run_id: UUID,
    ):
        """Should raise ValueError when run is in approved status."""
        mock_get_run_func.return_value = make_payroll_run(
            run_id=str(sample_run_id),
            status="approved",
        )

        with pytest.raises(ValueError, match="Cannot recalculate.*approved.*not 'draft'"):
            await run_operations.recalculate_run(sample_run_id)

    @pytest.mark.asyncio
    async def test_no_records_found(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        mock_get_run_records_func: AsyncMock,
        sample_run_id: UUID,
    ):
        """Should raise ValueError when no records exist for the run."""
        mock_get_run_func.return_value = make_payroll_run(
            run_id=str(sample_run_id),
            status="draft",
        )
        mock_get_run_records_func.return_value = []

        with pytest.raises(ValueError, match="No records found for payroll run"):
            await run_operations.recalculate_run(sample_run_id)
