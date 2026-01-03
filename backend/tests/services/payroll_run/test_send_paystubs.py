"""
Tests for PayrollRunOperations.send_paystubs method.

Covers:
- Error handling (run not found, wrong status, no records)
- Successful sending
- Missing storage key
- Missing email
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from app.services.payroll_run.run_operations import PayrollRunOperations

from .conftest import make_payroll_run


class TestSendPaystubsErrors:
    """Tests for send_paystubs error handling."""

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
            await run_operations.send_paystubs(sample_run_id)

    @pytest.mark.asyncio
    async def test_run_not_in_approved_status(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        sample_run_id: UUID,
    ):
        """Should raise ValueError when run is not in approved status."""
        mock_get_run_func.return_value = make_payroll_run(
            run_id=str(sample_run_id),
            status="draft",
        )

        with pytest.raises(ValueError, match="Cannot send paystubs.*draft.*not 'approved'"):
            await run_operations.send_paystubs(sample_run_id)

    @pytest.mark.asyncio
    async def test_no_records_found(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        mock_supabase: MagicMock,
        sample_run_id: UUID,
    ):
        """Should raise ValueError when no records found."""
        mock_get_run_func.return_value = make_payroll_run(
            run_id=str(sample_run_id),
            status="approved",
        )

        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[])
        mock_supabase.table = MagicMock(return_value=mock_table)

        with pytest.raises(ValueError, match="No records found for payroll run"):
            await run_operations.send_paystubs(sample_run_id)


class TestSendPaystubsSuccess:
    """Tests for successful send_paystubs."""

    @pytest.mark.asyncio
    async def test_send_success(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        mock_supabase: MagicMock,
        sample_run_id: UUID,
    ):
        """Should send paystubs and return count."""
        mock_get_run_func.return_value = make_payroll_run(
            run_id=str(sample_run_id),
            status="approved",
        )

        record = {
            "id": str(uuid4()),
            "employee_id": str(uuid4()),
            "paystub_storage_key": "test-key",
            "employees": {
                "id": str(uuid4()),
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@test.com",
            },
        }

        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[record])
        mock_table.update.return_value = mock_table
        mock_supabase.table = MagicMock(return_value=mock_table)

        result = await run_operations.send_paystubs(sample_run_id)

        assert result["sent"] == 1
        assert len(result["sent_record_ids"]) == 1
        assert result["errors"] is None

    @pytest.mark.asyncio
    async def test_send_no_storage_key(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        mock_supabase: MagicMock,
        sample_run_id: UUID,
    ):
        """Should report error when paystub not generated."""
        mock_get_run_func.return_value = make_payroll_run(
            run_id=str(sample_run_id),
            status="approved",
        )

        record = {
            "id": "record-123",
            "employee_id": str(uuid4()),
            "paystub_storage_key": None,  # Not generated
            "employees": {
                "id": str(uuid4()),
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@test.com",
            },
        }

        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[record])
        mock_supabase.table = MagicMock(return_value=mock_table)

        result = await run_operations.send_paystubs(sample_run_id)

        assert result["sent"] == 0
        assert result["errors"] is not None
        assert "paystub not generated" in result["errors"][0]

    @pytest.mark.asyncio
    async def test_send_no_email(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        mock_supabase: MagicMock,
        sample_run_id: UUID,
    ):
        """Should report error when employee has no email."""
        mock_get_run_func.return_value = make_payroll_run(
            run_id=str(sample_run_id),
            status="approved",
        )

        record = {
            "id": "record-123",
            "employee_id": str(uuid4()),
            "paystub_storage_key": "test-key",
            "employees": {
                "id": str(uuid4()),
                "first_name": "John",
                "last_name": "Doe",
                "email": None,  # No email
            },
        }

        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[record])
        mock_supabase.table = MagicMock(return_value=mock_table)

        result = await run_operations.send_paystubs(sample_run_id)

        assert result["sent"] == 0
        assert result["errors"] is not None
        assert "employee has no email" in result["errors"][0]

    @pytest.mark.asyncio
    async def test_send_exception_during_processing(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        mock_supabase: MagicMock,
        sample_run_id: UUID,
    ):
        """Should catch exception and report error when sending fails."""
        mock_get_run_func.return_value = make_payroll_run(
            run_id=str(sample_run_id),
            status="approved",
        )

        record = {
            "id": "record-123",
            "employee_id": str(uuid4()),
            "paystub_storage_key": "test-key",
            "employees": {
                "id": str(uuid4()),
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@test.com",
            },
        }

        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[record])
        # Make update raise an exception to simulate email sending failure
        mock_table.update.side_effect = Exception("Email service unavailable")
        mock_supabase.table = MagicMock(return_value=mock_table)

        result = await run_operations.send_paystubs(sample_run_id)

        assert result["sent"] == 0
        assert result["errors"] is not None
        assert "record-123" in result["errors"][0]
        assert "Email service unavailable" in result["errors"][0]
