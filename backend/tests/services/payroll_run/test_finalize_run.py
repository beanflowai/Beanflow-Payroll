"""
Tests for PayrollRunOperations.finalize_run method.

Covers:
- Error handling (run not found, wrong status, modified records)
- Successful finalization
- Update failures
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from app.services.payroll_run.run_operations import PayrollRunOperations

from .conftest import make_payroll_run


class TestFinalizeRunErrors:
    """Tests for finalize_run error handling."""

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
            await run_operations.finalize_run(sample_run_id)

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
            status="approved",
        )

        with pytest.raises(ValueError, match="Cannot finalize.*approved.*not 'draft'"):
            await run_operations.finalize_run(sample_run_id)

    @pytest.mark.asyncio
    async def test_has_modified_records(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        mock_supabase: MagicMock,
        sample_run_id: UUID,
    ):
        """Should raise ValueError when there are modified records."""
        mock_get_run_func.return_value = make_payroll_run(
            run_id=str(sample_run_id),
            status="draft",
        )

        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[
            {"id": "record-1"},
            {"id": "record-2"},
        ])
        mock_supabase.table = MagicMock(return_value=mock_table)

        with pytest.raises(ValueError, match="Cannot finalize.*2 record\\(s\\) have unsaved"):
            await run_operations.finalize_run(sample_run_id)


class TestFinalizeRunSuccess:
    """Tests for successful finalize_run."""

    @pytest.mark.asyncio
    async def test_finalize_success(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        mock_supabase: MagicMock,
        sample_run_id: UUID,
    ):
        """Should transition run to pending_approval status."""
        mock_get_run_func.return_value = make_payroll_run(
            run_id=str(sample_run_id),
            status="draft",
        )

        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.update.return_value = mock_table

        # Use side_effect to return different values for sequential calls
        execute_results = [
            MagicMock(data=[]),  # First: check for modified records (none)
            MagicMock(data=[make_payroll_run(run_id=str(sample_run_id), status="pending_approval")]),
        ]
        mock_table.execute.side_effect = execute_results
        mock_supabase.table = MagicMock(return_value=mock_table)

        result = await run_operations.finalize_run(sample_run_id)

        assert result["status"] == "pending_approval"

    @pytest.mark.asyncio
    async def test_finalize_update_fails(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        mock_supabase: MagicMock,
        sample_run_id: UUID,
    ):
        """Should raise ValueError when update fails."""
        mock_get_run_func.return_value = make_payroll_run(
            run_id=str(sample_run_id),
            status="draft",
        )

        call_count = 0

        def mock_execute():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call: check for modified records
                return MagicMock(data=[])
            else:
                # Second call: update returns empty
                return MagicMock(data=[])

        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.update.return_value = mock_table
        mock_table.execute.side_effect = mock_execute
        mock_supabase.table = MagicMock(return_value=mock_table)

        with pytest.raises(ValueError, match="Failed to update payroll run status"):
            await run_operations.finalize_run(sample_run_id)
