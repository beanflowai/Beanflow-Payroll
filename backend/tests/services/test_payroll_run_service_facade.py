"""
Tests for PayrollRunService facade methods.

Tests the public API methods that are simple pass-throughs or CRUD operations.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

from app.services.payroll_run_service import PayrollRunService, get_payroll_run_service


@pytest.fixture
def mock_supabase():
    """Create a mock Supabase client."""
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_client.table.return_value = mock_table

    # Chain methods
    mock_table.select.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.neq.return_value = mock_table
    mock_table.order.return_value = mock_table
    mock_table.range.return_value = mock_table
    mock_table.limit.return_value = mock_table
    mock_table.update.return_value = mock_table
    mock_table.delete.return_value = mock_table

    return mock_client


@pytest.fixture
def service(mock_supabase) -> PayrollRunService:
    """Create a PayrollRunService with mocked Supabase."""
    with patch("app.services.payroll_run_service.get_supabase_client", return_value=mock_supabase):
        svc = PayrollRunService(user_id="user-123", company_id="company-456")
        return svc


class TestPayrollRunServiceInit:
    """Tests for service initialization."""

    def test_init_sets_user_and_company(self, mock_supabase):
        """Test that init sets user_id and company_id."""
        with patch("app.services.payroll_run_service.get_supabase_client", return_value=mock_supabase):
            svc = PayrollRunService(user_id="user-123", company_id="company-456")

            assert svc.user_id == "user-123"
            assert svc.company_id == "company-456"

    def test_factory_function_creates_service(self, mock_supabase):
        """Test that factory function creates a service."""
        with patch("app.services.payroll_run_service.get_supabase_client", return_value=mock_supabase):
            svc = get_payroll_run_service(user_id="user-123", company_id="company-456")

            assert isinstance(svc, PayrollRunService)
            assert svc.user_id == "user-123"


class TestGetRun:
    """Tests for get_run method."""

    @pytest.mark.asyncio
    async def test_get_run_returns_run_when_found(self, service, mock_supabase):
        """Test get_run returns the run when found."""
        run_id = UUID("12345678-1234-5678-1234-567812345678")
        expected_run = {"id": str(run_id), "status": "draft"}

        mock_result = MagicMock()
        mock_result.data = [expected_run]
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = mock_result

        result = await service.get_run(run_id)

        assert result == expected_run

    @pytest.mark.asyncio
    async def test_get_run_returns_none_when_not_found(self, service, mock_supabase):
        """Test get_run returns None when run not found."""
        run_id = UUID("12345678-1234-5678-1234-567812345678")

        mock_result = MagicMock()
        mock_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = mock_result

        result = await service.get_run(run_id)

        assert result is None


class TestListRuns:
    """Tests for list_runs method."""

    @pytest.mark.asyncio
    async def test_list_runs_returns_runs_and_count(self, service, mock_supabase):
        """Test list_runs returns runs and total count."""
        runs = [
            {"id": "run-1", "status": "draft"},
            {"id": "run-2", "status": "approved"},
        ]

        mock_result = MagicMock()
        mock_result.data = runs
        mock_result.count = 2
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value = mock_result

        result = await service.list_runs()

        assert result["runs"] == runs
        assert result["total"] == 2

    @pytest.mark.asyncio
    async def test_list_runs_filters_by_status(self, service, mock_supabase):
        """Test list_runs filters by status."""
        mock_result = MagicMock()
        mock_result.data = [{"id": "run-1", "status": "draft"}]
        mock_result.count = 1

        mock_chain = MagicMock()
        mock_chain.eq.return_value = mock_chain
        mock_chain.neq.return_value = mock_chain
        mock_chain.order.return_value = mock_chain
        mock_chain.range.return_value = mock_chain
        mock_chain.execute.return_value = mock_result

        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value = mock_chain

        result = await service.list_runs(run_status="draft")

        mock_chain.eq.assert_called_with("status", "draft")

    @pytest.mark.asyncio
    async def test_list_runs_excludes_status(self, service, mock_supabase):
        """Test list_runs excludes specified status."""
        mock_result = MagicMock()
        mock_result.data = []
        mock_result.count = 0

        mock_chain = MagicMock()
        mock_chain.eq.return_value = mock_chain
        mock_chain.neq.return_value = mock_chain
        mock_chain.order.return_value = mock_chain
        mock_chain.range.return_value = mock_chain
        mock_chain.execute.return_value = mock_result

        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value = mock_chain

        result = await service.list_runs(exclude_status="draft")

        mock_chain.neq.assert_called_with("status", "draft")


class TestGetRecord:
    """Tests for get_record method."""

    @pytest.mark.asyncio
    async def test_get_record_returns_record_when_found(self, service, mock_supabase):
        """Test get_record returns the record when found."""
        record_id = UUID("12345678-1234-5678-1234-567812345678")
        expected_record = {"id": str(record_id), "gross_pay": 1000}

        mock_result = MagicMock()
        mock_result.data = [expected_record]
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = mock_result

        result = await service.get_record(record_id)

        assert result == expected_record

    @pytest.mark.asyncio
    async def test_get_record_returns_none_when_not_found(self, service, mock_supabase):
        """Test get_record returns None when not found."""
        record_id = UUID("12345678-1234-5678-1234-567812345678")

        mock_result = MagicMock()
        mock_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = mock_result

        result = await service.get_record(record_id)

        assert result is None


class TestGetRunRecords:
    """Tests for get_run_records method."""

    @pytest.mark.asyncio
    async def test_get_run_records_returns_list(self, service, mock_supabase):
        """Test get_run_records returns list of records."""
        run_id = UUID("12345678-1234-5678-1234-567812345678")
        records = [
            {"id": "rec-1", "gross_pay": 1000},
            {"id": "rec-2", "gross_pay": 2000},
        ]

        mock_result = MagicMock()
        mock_result.data = records
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = mock_result

        result = await service.get_run_records(run_id)

        assert result == records

    @pytest.mark.asyncio
    async def test_get_run_records_returns_empty_list_when_none(self, service, mock_supabase):
        """Test get_run_records returns empty list when no records."""
        run_id = UUID("12345678-1234-5678-1234-567812345678")

        mock_result = MagicMock()
        mock_result.data = None
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = mock_result

        result = await service.get_run_records(run_id)

        assert result == []


class TestUpdateRecord:
    """Tests for update_record method."""

    @pytest.mark.asyncio
    async def test_update_record_raises_when_run_not_found(self, service, mock_supabase):
        """Test update_record raises when run not found."""
        run_id = UUID("12345678-1234-5678-1234-567812345678")
        record_id = UUID("87654321-1234-5678-1234-567812345678")

        # Mock get_run to return None
        service.get_run = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="Payroll run not found"):
            await service.update_record(run_id, record_id, {"hours": 40})

    @pytest.mark.asyncio
    async def test_update_record_raises_when_not_draft(self, service, mock_supabase):
        """Test update_record raises when run is not draft."""
        run_id = UUID("12345678-1234-5678-1234-567812345678")
        record_id = UUID("87654321-1234-5678-1234-567812345678")

        # Mock get_run to return approved run
        service.get_run = AsyncMock(return_value={"id": str(run_id), "status": "approved"})

        with pytest.raises(ValueError, match="not 'draft'"):
            await service.update_record(run_id, record_id, {"hours": 40})

    @pytest.mark.asyncio
    async def test_update_record_raises_when_record_not_found(self, service, mock_supabase):
        """Test update_record raises when record not found."""
        run_id = UUID("12345678-1234-5678-1234-567812345678")
        record_id = UUID("87654321-1234-5678-1234-567812345678")

        # Mock get_run to return draft run
        service.get_run = AsyncMock(return_value={"id": str(run_id), "status": "draft"})

        # Mock record query to return empty
        mock_result = MagicMock()
        mock_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = mock_result

        with pytest.raises(ValueError, match="Payroll record not found"):
            await service.update_record(run_id, record_id, {"hours": 40})

    @pytest.mark.asyncio
    async def test_update_record_merges_input_data(self, service, mock_supabase):
        """Test update_record merges with existing input_data."""
        run_id = UUID("12345678-1234-5678-1234-567812345678")
        record_id = UUID("87654321-1234-5678-1234-567812345678")

        # Mock get_run to return draft run
        service.get_run = AsyncMock(return_value={"id": str(run_id), "status": "draft"})

        # Mock record query to return existing record
        existing_record = {"id": str(record_id), "input_data": {"hours": 40}}
        mock_select_result = MagicMock()
        mock_select_result.data = [existing_record]

        # Mock update to return updated record
        updated_record = {"id": str(record_id), "input_data": {"hours": 40, "overtime_hours": 5}, "is_modified": True}
        mock_update_result = MagicMock()
        mock_update_result.data = [updated_record]

        # Configure the mock chain
        mock_chain = MagicMock()
        mock_chain.select.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain
        mock_chain.update.return_value = mock_chain
        mock_chain.execute.side_effect = [mock_select_result, mock_update_result]

        mock_supabase.table.return_value = mock_chain

        result = await service.update_record(run_id, record_id, {"overtime_hours": 5})

        assert result["input_data"]["hours"] == 40
        assert result["input_data"]["overtime_hours"] == 5

    @pytest.mark.asyncio
    async def test_update_record_raises_when_update_returns_no_data(self, service, mock_supabase):
        """Test update_record raises when update returns no data (line 203)."""
        run_id = UUID("12345678-1234-5678-1234-567812345678")
        record_id = UUID("87654321-1234-5678-1234-567812345678")

        # Mock get_run to return draft run
        service.get_run = AsyncMock(return_value={"id": str(run_id), "status": "draft"})

        # Mock record query to return existing record
        existing_record = {"id": str(record_id), "input_data": {"hours": 40}}
        mock_select_result = MagicMock()
        mock_select_result.data = [existing_record]

        # Mock update to return NO data (simulating update failure)
        mock_update_result = MagicMock()
        mock_update_result.data = []  # Empty data = no record returned

        # Configure the mock chain
        mock_chain = MagicMock()
        mock_chain.select.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain
        mock_chain.update.return_value = mock_chain
        mock_chain.execute.side_effect = [mock_select_result, mock_update_result]

        mock_supabase.table.return_value = mock_chain

        # Should raise ValueError when update returns no data
        with pytest.raises(ValueError, match="Failed to update payroll record"):
            await service.update_record(run_id, record_id, {"overtime_hours": 5})


class TestCheckHasModifiedRecords:
    """Tests for check_has_modified_records method."""

    @pytest.mark.asyncio
    async def test_returns_true_when_modified_records_exist(self, service, mock_supabase):
        """Test returns True when modified records exist."""
        run_id = UUID("12345678-1234-5678-1234-567812345678")

        mock_result = MagicMock()
        mock_result.data = [{"id": "rec-1"}]
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = mock_result

        result = await service.check_has_modified_records(run_id)

        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_when_no_modified_records(self, service, mock_supabase):
        """Test returns False when no modified records."""
        run_id = UUID("12345678-1234-5678-1234-567812345678")

        mock_result = MagicMock()
        mock_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = mock_result

        result = await service.check_has_modified_records(run_id)

        assert result is False


class TestDeleteRun:
    """Tests for delete_run method."""

    @pytest.mark.asyncio
    async def test_delete_run_raises_when_not_found(self, service, mock_supabase):
        """Test delete_run raises when run not found."""
        run_id = UUID("12345678-1234-5678-1234-567812345678")

        service.get_run = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="Payroll run not found"):
            await service.delete_run(run_id)

    @pytest.mark.asyncio
    async def test_delete_run_raises_when_not_draft(self, service, mock_supabase):
        """Test delete_run raises when run is not draft."""
        run_id = UUID("12345678-1234-5678-1234-567812345678")

        service.get_run = AsyncMock(return_value={"id": str(run_id), "status": "approved"})

        with pytest.raises(ValueError, match="Only draft runs can be deleted"):
            await service.delete_run(run_id)

    @pytest.mark.asyncio
    async def test_delete_run_deletes_draft_run(self, service, mock_supabase):
        """Test delete_run successfully deletes draft run."""
        run_id = UUID("12345678-1234-5678-1234-567812345678")

        service.get_run = AsyncMock(return_value={"id": str(run_id), "status": "draft"})

        mock_supabase.table.return_value.delete.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = None

        result = await service.delete_run(run_id)

        assert result["deleted"] is True
        assert result["run_id"] == str(run_id)


class TestDelegatedMethods:
    """Tests for methods that delegate to sub-services."""

    @pytest.mark.asyncio
    async def test_create_or_get_run_delegates(self, service):
        """Test create_or_get_run delegates to run_ops."""
        service._run_ops.create_or_get_run = AsyncMock(return_value={"id": "run-1"})

        result = await service.create_or_get_run("2025-01-15")

        service._run_ops.create_or_get_run.assert_called_once_with("2025-01-15")
        assert result == {"id": "run-1"}

    @pytest.mark.asyncio
    async def test_create_or_get_run_by_period_end_delegates(self, service):
        """Test create_or_get_run_by_period_end delegates to run_ops."""
        service._run_ops.create_or_get_run_by_period_end = AsyncMock(return_value={"id": "run-1"})

        result = await service.create_or_get_run_by_period_end("2025-01-15")

        service._run_ops.create_or_get_run_by_period_end.assert_called_once_with("2025-01-15")

    @pytest.mark.asyncio
    async def test_recalculate_run_delegates(self, service):
        """Test recalculate_run delegates to run_ops."""
        run_id = UUID("12345678-1234-5678-1234-567812345678")
        service._run_ops.recalculate_run = AsyncMock(return_value={"status": "recalculated"})

        result = await service.recalculate_run(run_id)

        service._run_ops.recalculate_run.assert_called_once_with(run_id)

    @pytest.mark.asyncio
    async def test_finalize_run_delegates(self, service):
        """Test finalize_run delegates to run_ops."""
        run_id = UUID("12345678-1234-5678-1234-567812345678")
        service._run_ops.finalize_run = AsyncMock(return_value={"status": "pending_approval"})

        result = await service.finalize_run(run_id)

        service._run_ops.finalize_run.assert_called_once_with(run_id)

    @pytest.mark.asyncio
    async def test_approve_run_delegates(self, service):
        """Test approve_run delegates to run_ops."""
        run_id = UUID("12345678-1234-5678-1234-567812345678")
        service._run_ops.approve_run = AsyncMock(return_value={"status": "approved"})

        result = await service.approve_run(run_id, "admin@example.com")

        service._run_ops.approve_run.assert_called_once_with(run_id, "admin@example.com")

    @pytest.mark.asyncio
    async def test_send_paystubs_delegates(self, service):
        """Test send_paystubs delegates to run_ops."""
        run_id = UUID("12345678-1234-5678-1234-567812345678")
        service._run_ops.send_paystubs = AsyncMock(return_value={"sent": 5})

        result = await service.send_paystubs(run_id)

        service._run_ops.send_paystubs.assert_called_once_with(run_id)

    @pytest.mark.asyncio
    async def test_sync_employees_delegates(self, service):
        """Test sync_employees delegates to emp_mgmt."""
        run_id = UUID("12345678-1234-5678-1234-567812345678")
        service._emp_mgmt.sync_employees = AsyncMock(return_value={"added": 2})

        result = await service.sync_employees(run_id)

        service._emp_mgmt.sync_employees.assert_called_once_with(run_id)

    @pytest.mark.asyncio
    async def test_add_employee_to_run_delegates(self, service):
        """Test add_employee_to_run delegates to emp_mgmt."""
        run_id = UUID("12345678-1234-5678-1234-567812345678")
        employee_id = "emp-123"
        service._emp_mgmt.add_employee_to_run = AsyncMock(return_value={"added": True})

        result = await service.add_employee_to_run(run_id, employee_id)

        service._emp_mgmt.add_employee_to_run.assert_called_once_with(run_id, employee_id)

    @pytest.mark.asyncio
    async def test_remove_employee_from_run_delegates(self, service):
        """Test remove_employee_from_run delegates to emp_mgmt."""
        run_id = UUID("12345678-1234-5678-1234-567812345678")
        employee_id = "emp-123"
        service._emp_mgmt.remove_employee_from_run = AsyncMock(return_value={"removed": True})

        result = await service.remove_employee_from_run(run_id, employee_id)

        service._emp_mgmt.remove_employee_from_run.assert_called_once_with(run_id, employee_id)
