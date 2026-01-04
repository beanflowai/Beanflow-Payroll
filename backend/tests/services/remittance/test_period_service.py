"""
Tests for Remittance Period Service

Tests for automatic remittance period creation and aggregation
from approved payroll runs.
"""

from __future__ import annotations

from datetime import date
from typing import Any
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.services.remittance.period_service import RemittancePeriodService


# =============================================================================
# Test Constants
# =============================================================================

TEST_USER_ID = "test-user-id-12345"
TEST_COMPANY_ID = str(uuid4())
TEST_RUN_ID = str(uuid4())
TEST_PERIOD_ID = str(uuid4())


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_supabase():
    """Create a mock Supabase client."""
    return MagicMock()


@pytest.fixture
def service(mock_supabase) -> RemittancePeriodService:
    """Create a remittance period service instance."""
    return RemittancePeriodService(
        supabase=mock_supabase,
        user_id=TEST_USER_ID,
        company_id=TEST_COMPANY_ID,
    )


@pytest.fixture
def sample_payroll_run() -> dict[str, Any]:
    """Sample approved payroll run with deduction totals."""
    return {
        "id": TEST_RUN_ID,
        "period_start": "2025-01-01",
        "period_end": "2025-01-15",
        "pay_date": "2025-01-17",
        "status": "approved",
        "total_cpp_employee": 750.00,
        "total_cpp_employer": 750.00,
        "total_ei_employee": 400.00,
        "total_ei_employer": 560.00,
        "total_federal_tax": 2500.00,
        "total_provincial_tax": 1250.00,
    }


@pytest.fixture
def sample_remittance_period() -> dict[str, Any]:
    """Sample remittance period from database."""
    return {
        "id": TEST_PERIOD_ID,
        "company_id": TEST_COMPANY_ID,
        "user_id": TEST_USER_ID,
        "remitter_type": "regular",
        "period_start": "2025-01-01",
        "period_end": "2025-01-31",
        "due_date": "2025-02-15",
        "cpp_employee": 500.00,
        "cpp_employer": 500.00,
        "ei_employee": 200.00,
        "ei_employer": 280.00,
        "federal_tax": 1500.00,
        "provincial_tax": 750.00,
        "status": "pending",
        "payroll_run_ids": [str(uuid4())],  # Existing run
    }


# =============================================================================
# Test: find_or_create_remittance_period - Validation
# =============================================================================


class TestFindOrCreateValidation:
    """Tests for find_or_create_remittance_period validation."""

    def test_missing_run_id_raises_error(self, service, sample_payroll_run):
        """Test that missing run ID raises ValueError."""
        run_without_id = sample_payroll_run.copy()
        del run_without_id["id"]

        with pytest.raises(ValueError, match="run ID is required"):
            service.find_or_create_remittance_period(run_without_id, "regular")

    def test_missing_period_end_raises_error(self, service, sample_payroll_run):
        """Test that missing period_end raises ValueError."""
        run_without_period = sample_payroll_run.copy()
        del run_without_period["period_end"]

        with pytest.raises(ValueError, match="period_end is required"):
            service.find_or_create_remittance_period(run_without_period, "regular")


# =============================================================================
# Test: find_or_create_remittance_period - Create New
# =============================================================================


class TestCreateRemittancePeriod:
    """Tests for creating new remittance periods."""

    def test_creates_new_period_when_none_exists(
        self, service, mock_supabase, sample_payroll_run
    ):
        """Test creating a new remittance period when none exists."""
        # Mock no existing periods
        mock_select_response = MagicMock()
        mock_select_response.data = []

        # Mock successful insert
        created_period = {
            "id": str(uuid4()),
            "company_id": TEST_COMPANY_ID,
            "user_id": TEST_USER_ID,
            "period_start": "2025-01-01",
            "period_end": "2025-01-31",
            "cpp_employee": 750.00,
            "cpp_employer": 750.00,
            "ei_employee": 400.00,
            "ei_employer": 560.00,
            "federal_tax": 2500.00,
            "provincial_tax": 1250.00,
            "status": "pending",
        }
        mock_insert_response = MagicMock()
        mock_insert_response.data = [created_period]

        # Create separate builders for select and insert operations
        select_builder = MagicMock()
        select_builder.select.return_value = select_builder
        select_builder.eq.return_value = select_builder
        select_builder.execute.return_value = mock_select_response

        insert_builder = MagicMock()
        insert_builder.insert.return_value = insert_builder
        insert_builder.execute.return_value = mock_insert_response

        call_count = 0

        def table_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return select_builder
            else:
                return insert_builder

        mock_supabase.table.side_effect = table_side_effect

        result = service.find_or_create_remittance_period(sample_payroll_run, "regular")

        assert result["cpp_employee"] == 750.00
        assert result["cpp_employer"] == 750.00
        assert result["ei_employee"] == 400.00
        assert result["ei_employer"] == 560.00
        assert result["status"] == "pending"

    def test_handles_date_object_period_end(
        self, service, mock_supabase, sample_payroll_run
    ):
        """Test handling period_end as date object."""
        run_with_date = sample_payroll_run.copy()
        run_with_date["period_end"] = date(2025, 1, 15)

        # Mock responses
        mock_select_response = MagicMock()
        mock_select_response.data = []

        mock_insert_response = MagicMock()
        mock_insert_response.data = [{"id": str(uuid4())}]

        # Create separate builders for select and insert operations
        select_builder = MagicMock()
        select_builder.select.return_value = select_builder
        select_builder.eq.return_value = select_builder
        select_builder.execute.return_value = mock_select_response

        insert_builder = MagicMock()
        insert_builder.insert.return_value = insert_builder
        insert_builder.execute.return_value = mock_insert_response

        call_count = 0

        def table_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return select_builder
            else:
                return insert_builder

        mock_supabase.table.side_effect = table_side_effect

        # Should not raise an error
        result = service.find_or_create_remittance_period(run_with_date, "regular")
        assert result is not None


# =============================================================================
# Test: find_or_create_remittance_period - Aggregate Existing
# =============================================================================


class TestAggregateRemittancePeriod:
    """Tests for aggregating to existing remittance periods."""

    def test_aggregates_to_existing_period(
        self, service, mock_supabase, sample_payroll_run, sample_remittance_period
    ):
        """Test aggregating deductions to existing period."""
        # Mock existing period found
        mock_select_response = MagicMock()
        mock_select_response.data = [sample_remittance_period]

        # Mock update response
        updated_period = sample_remittance_period.copy()
        updated_period["cpp_employee"] = 1250.00  # 500 + 750
        updated_period["cpp_employer"] = 1250.00  # 500 + 750
        updated_period["ei_employee"] = 600.00  # 200 + 400
        updated_period["ei_employer"] = 840.00  # 280 + 560
        updated_period["federal_tax"] = 4000.00  # 1500 + 2500
        updated_period["provincial_tax"] = 2000.00  # 750 + 1250
        updated_period["payroll_run_ids"] = list(updated_period["payroll_run_ids"]) + [TEST_RUN_ID]

        mock_update_response = MagicMock()
        mock_update_response.data = [updated_period]

        # Create separate builders for select and update operations
        select_builder = MagicMock()
        select_builder.select.return_value = select_builder
        select_builder.eq.return_value = select_builder
        select_builder.execute.return_value = mock_select_response

        update_builder = MagicMock()
        update_builder.update.return_value = update_builder
        update_builder.eq.return_value = update_builder
        update_builder.execute.return_value = mock_update_response

        call_count = 0

        def table_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return select_builder
            else:
                return update_builder

        mock_supabase.table.side_effect = table_side_effect

        result = service.find_or_create_remittance_period(sample_payroll_run, "regular")

        assert result["cpp_employee"] == 1250.00
        assert result["cpp_employer"] == 1250.00
        assert result["federal_tax"] == 4000.00

    def test_skips_if_run_already_linked(
        self, service, mock_supabase, sample_payroll_run, sample_remittance_period
    ):
        """Test that idempotency check skips already linked runs."""
        # Add the current run ID to existing linked runs
        period_with_run = sample_remittance_period.copy()
        period_with_run["payroll_run_ids"] = [TEST_RUN_ID]

        mock_select_response = MagicMock()
        mock_select_response.data = [period_with_run]

        query_builder = MagicMock()
        query_builder.select.return_value = query_builder
        query_builder.eq.return_value = query_builder
        query_builder.execute.return_value = mock_select_response

        mock_supabase.table.return_value = query_builder

        result = service.find_or_create_remittance_period(sample_payroll_run, "regular")

        # Should return the existing period without update
        assert result["id"] == TEST_PERIOD_ID
        # Update should not have been called
        query_builder.update.assert_not_called()


# =============================================================================
# Test: _aggregate_deductions_to_period
# =============================================================================


class TestAggregateDeductions:
    """Tests for _aggregate_deductions_to_period method."""

    def test_aggregates_with_decimal_precision(
        self, service, mock_supabase, sample_payroll_run, sample_remittance_period
    ):
        """Test that deduction aggregation maintains precision."""
        # Mock update response
        mock_update_response = MagicMock()
        mock_update_response.data = [sample_remittance_period]

        query_builder = MagicMock()
        query_builder.update.return_value = query_builder
        query_builder.eq.return_value = query_builder
        query_builder.execute.return_value = mock_update_response

        mock_supabase.table.return_value = query_builder

        existing_run_ids = sample_remittance_period["payroll_run_ids"]

        result = service._aggregate_deductions_to_period(
            sample_remittance_period,
            sample_payroll_run,
            existing_run_ids,
        )

        # Verify update was called with correct aggregated values
        query_builder.update.assert_called_once()
        update_call = query_builder.update.call_args[0][0]

        # CPP employee: 500 + 750 = 1250
        assert update_call["cpp_employee"] == 1250.00
        # CPP employer: 500 + 750 = 1250
        assert update_call["cpp_employer"] == 1250.00
        # EI employee: 200 + 400 = 600
        assert update_call["ei_employee"] == 600.00
        # EI employer: 280 + 560 = 840
        assert update_call["ei_employer"] == 840.00
        # Federal tax: 1500 + 2500 = 4000
        assert update_call["federal_tax"] == 4000.00
        # Provincial tax: 750 + 1250 = 2000
        assert update_call["provincial_tax"] == 2000.00

    def test_handles_missing_deduction_values(
        self, service, mock_supabase, sample_remittance_period
    ):
        """Test handling payroll run with missing deduction values."""
        # Payroll run with None values
        run_with_nones = {
            "id": TEST_RUN_ID,
            "total_cpp_employee": None,
            "total_cpp_employer": None,
            "total_ei_employee": None,
            "total_ei_employer": None,
            "total_federal_tax": None,
            "total_provincial_tax": None,
        }

        mock_update_response = MagicMock()
        mock_update_response.data = [sample_remittance_period]

        query_builder = MagicMock()
        query_builder.update.return_value = query_builder
        query_builder.eq.return_value = query_builder
        query_builder.execute.return_value = mock_update_response

        mock_supabase.table.return_value = query_builder

        result = service._aggregate_deductions_to_period(
            sample_remittance_period,
            run_with_nones,
            [],
        )

        # Values should remain the same (added 0)
        update_call = query_builder.update.call_args[0][0]
        assert update_call["cpp_employee"] == 500.00
        assert update_call["federal_tax"] == 1500.00

    def test_raises_error_on_update_failure(
        self, service, mock_supabase, sample_payroll_run, sample_remittance_period
    ):
        """Test that update failure raises ValueError."""
        mock_update_response = MagicMock()
        mock_update_response.data = None  # Update failed

        query_builder = MagicMock()
        query_builder.update.return_value = query_builder
        query_builder.eq.return_value = query_builder
        query_builder.execute.return_value = mock_update_response

        mock_supabase.table.return_value = query_builder

        with pytest.raises(ValueError, match="Failed to update"):
            service._aggregate_deductions_to_period(
                sample_remittance_period,
                sample_payroll_run,
                [],
            )


# =============================================================================
# Test: _create_remittance_period
# =============================================================================


class TestCreatePeriod:
    """Tests for _create_remittance_period method."""

    def test_creates_period_with_correct_data(
        self, service, mock_supabase, sample_payroll_run
    ):
        """Test that new period is created with correct data."""
        mock_insert_response = MagicMock()
        mock_insert_response.data = [{"id": str(uuid4())}]

        query_builder = MagicMock()
        query_builder.insert.return_value = query_builder
        query_builder.execute.return_value = mock_insert_response

        mock_supabase.table.return_value = query_builder

        result = service._create_remittance_period(
            period_start=date(2025, 1, 1),
            period_end=date(2025, 1, 31),
            due_date=date(2025, 2, 15),
            payroll_run=sample_payroll_run,
            remitter_type="regular",
        )

        # Verify insert was called with correct data
        query_builder.insert.assert_called_once()
        insert_call = query_builder.insert.call_args[0][0]

        assert insert_call["company_id"] == TEST_COMPANY_ID
        assert insert_call["user_id"] == TEST_USER_ID
        assert insert_call["remitter_type"] == "regular"
        assert insert_call["period_start"] == "2025-01-01"
        assert insert_call["period_end"] == "2025-01-31"
        assert insert_call["due_date"] == "2025-02-15"
        assert insert_call["cpp_employee"] == 750.00
        assert insert_call["cpp_employer"] == 750.00
        assert insert_call["status"] == "pending"
        assert TEST_RUN_ID in insert_call["payroll_run_ids"]

    def test_handles_missing_deduction_totals(self, service, mock_supabase):
        """Test creating period when payroll run has no deduction totals."""
        run_without_totals = {
            "id": TEST_RUN_ID,
        }

        mock_insert_response = MagicMock()
        mock_insert_response.data = [{"id": str(uuid4())}]

        query_builder = MagicMock()
        query_builder.insert.return_value = query_builder
        query_builder.execute.return_value = mock_insert_response

        mock_supabase.table.return_value = query_builder

        result = service._create_remittance_period(
            period_start=date(2025, 1, 1),
            period_end=date(2025, 1, 31),
            due_date=date(2025, 2, 15),
            payroll_run=run_without_totals,
            remitter_type="regular",
        )

        # All deductions should be 0
        insert_call = query_builder.insert.call_args[0][0]
        assert insert_call["cpp_employee"] == 0
        assert insert_call["cpp_employer"] == 0
        assert insert_call["ei_employee"] == 0
        assert insert_call["federal_tax"] == 0

    def test_raises_error_on_insert_failure(
        self, service, mock_supabase, sample_payroll_run
    ):
        """Test that insert failure raises ValueError."""
        mock_insert_response = MagicMock()
        mock_insert_response.data = None  # Insert failed

        query_builder = MagicMock()
        query_builder.insert.return_value = query_builder
        query_builder.execute.return_value = mock_insert_response

        mock_supabase.table.return_value = query_builder

        with pytest.raises(ValueError, match="Failed to create"):
            service._create_remittance_period(
                period_start=date(2025, 1, 1),
                period_end=date(2025, 1, 31),
                due_date=date(2025, 2, 15),
                payroll_run=sample_payroll_run,
                remitter_type="regular",
            )
