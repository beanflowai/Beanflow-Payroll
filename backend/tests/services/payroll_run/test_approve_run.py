"""
Tests for PayrollRunOperations.approve_run method.

Covers:
- Error handling (run not found, wrong status, no records, insufficient balance, storage config)
- Successful approval
- Logo download (success and failure)
- Vacation balance updates
- approved_by parameter
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from app.services.payroll_run.run_operations import PayrollRunOperations

from .conftest import (
    make_company,
    make_employee,
    make_payroll_record,
    make_payroll_run,
)


class TestApproveRunErrors:
    """Tests for approve_run error handling."""

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
            await run_operations.approve_run(sample_run_id)

    @pytest.mark.asyncio
    async def test_run_not_in_pending_approval_status(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        sample_run_id: UUID,
    ):
        """Should raise ValueError when run is not in pending_approval status."""
        mock_get_run_func.return_value = make_payroll_run(
            run_id=str(sample_run_id),
            status="draft",
        )

        with pytest.raises(ValueError, match="Cannot approve.*draft.*not 'pending_approval'"):
            await run_operations.approve_run(sample_run_id)

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
            status="pending_approval",
        )

        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[])
        mock_supabase.table = MagicMock(return_value=mock_table)

        with pytest.raises(ValueError, match="No records found for payroll run"):
            await run_operations.approve_run(sample_run_id)

    @pytest.mark.asyncio
    async def test_insufficient_vacation_balance(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        mock_supabase: MagicMock,
        sample_run_id: UUID,
    ):
        """Should raise ValueError when vacation balance is insufficient."""
        mock_get_run_func.return_value = make_payroll_run(
            run_id=str(sample_run_id),
            status="pending_approval",
        )

        employee = make_employee(
            vacation_config={"payout_method": "accrual"},
            vacation_balance=50.0,  # Only $50 balance
        )
        record = make_payroll_record(
            employee=employee,
            vacation_pay_paid=100.0,  # Trying to pay $100
        )

        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[record])
        mock_supabase.table = MagicMock(return_value=mock_table)

        with pytest.raises(ValueError, match="Cannot approve: insufficient vacation balance"):
            await run_operations.approve_run(sample_run_id)

    @pytest.mark.asyncio
    async def test_more_than_five_vacation_balance_errors(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        mock_supabase: MagicMock,
        sample_run_id: UUID,
    ):
        """Should show '... and N more' when more than 5 balance errors."""
        mock_get_run_func.return_value = make_payroll_run(
            run_id=str(sample_run_id),
            status="pending_approval",
        )

        # Create 7 employees with insufficient balance
        records = [
            make_payroll_record(
                employee=make_employee(
                    first_name=f"Employee{i}",
                    last_name=f"Last{i}",
                    vacation_config={"payout_method": "accrual"},
                    vacation_balance=10.0,
                ),
                vacation_pay_paid=100.0,
            )
            for i in range(7)
        ]

        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=records)
        mock_supabase.table = MagicMock(return_value=mock_table)

        with pytest.raises(ValueError, match=r"and 2 more"):
            await run_operations.approve_run(sample_run_id)

    @pytest.mark.asyncio
    async def test_paystub_storage_not_configured(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        mock_supabase: MagicMock,
        mock_ytd_calculator: MagicMock,
        sample_run_id: UUID,
        patch_paystub_services,
    ):
        """Should raise ValueError when paystub storage is not configured."""
        mock_get_run_func.return_value = make_payroll_run(
            run_id=str(sample_run_id),
            status="pending_approval",
        )

        employee = make_employee(
            vacation_config={"payout_method": "pay_as_you_go"},
        )
        record = make_payroll_record(employee=employee)

        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[record])
        mock_supabase.table = MagicMock(return_value=mock_table)

        patches = patch_paystub_services(raise_storage_error=True)

        with patches["builder"], patches["generator"], patches["storage"]:
            with pytest.raises(ValueError, match="Paystub storage is not configured"):
                await run_operations.approve_run(sample_run_id)


class TestApproveRunSuccess:
    """Tests for successful approve_run."""

    @pytest.mark.asyncio
    async def test_approve_success(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        mock_supabase: MagicMock,
        mock_ytd_calculator: MagicMock,
        sample_run_id: UUID,
        patch_paystub_services,
        patch_httpx_client,
        patch_remittance_service,
    ):
        """Should approve run and generate paystubs."""
        run = make_payroll_run(
            run_id=str(sample_run_id),
            status="pending_approval",
        )
        mock_get_run_func.return_value = run

        employee = make_employee(
            vacation_config={"payout_method": "pay_as_you_go"},
        )
        record = make_payroll_record(employee=employee)

        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[record])
        mock_table.update.return_value = mock_table
        mock_table.single.return_value = mock_table
        mock_supabase.table = MagicMock(return_value=mock_table)

        # Mock YTD calculator
        mock_ytd_calculator.get_ytd_records_for_employee = AsyncMock(return_value=[])

        patches = patch_paystub_services()

        # Track execute calls to return different data
        call_count = [0]

        def mock_execute():
            call_count[0] += 1
            if call_count[0] == 1:
                # First call returns records
                return MagicMock(data=[record])
            # Subsequent calls return approved run
            return MagicMock(data=[make_payroll_run(run_id=str(sample_run_id), status="approved")])

        mock_table.execute.side_effect = mock_execute

        with (
            patches["builder"],
            patches["generator"],
            patches["storage"],
            patch_httpx_client(),
            patch_remittance_service(),
        ):
            result = await run_operations.approve_run(sample_run_id)

        assert "paystubs_generated" in result

    @pytest.mark.asyncio
    async def test_approve_with_logo_download(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        mock_supabase: MagicMock,
        mock_ytd_calculator: MagicMock,
        sample_run_id: UUID,
        patch_paystub_services,
        patch_httpx_client,
        patch_remittance_service,
    ):
        """Should download company logo for paystub generation."""
        run = make_payroll_run(
            run_id=str(sample_run_id),
            status="pending_approval",
        )
        mock_get_run_func.return_value = run

        company = make_company(logo_url="https://example.com/logo.png")
        employee = make_employee(
            vacation_config={"payout_method": "pay_as_you_go"},
            companies=company,
        )
        record = make_payroll_record(employee=employee)

        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.update.return_value = mock_table
        mock_table.single.return_value = mock_table

        # Configure different execute responses
        execute_responses = iter([
            MagicMock(data=[record]),  # Records query
            MagicMock(data=[record]),  # Any other query
            MagicMock(data=[make_payroll_run(run_id=str(sample_run_id), status="approved")]),
        ])

        def mock_execute():
            try:
                return next(execute_responses)
            except StopIteration:
                return MagicMock(data=[make_payroll_run(run_id=str(sample_run_id), status="approved")])

        mock_table.execute.side_effect = mock_execute
        mock_supabase.table = MagicMock(return_value=mock_table)

        mock_ytd_calculator.get_ytd_records_for_employee = AsyncMock(return_value=[])

        patches = patch_paystub_services()

        with (
            patches["builder"],
            patches["generator"],
            patches["storage"],
            patch_httpx_client(logo_bytes=b"fake-logo-data"),
            patch_remittance_service(),
        ):
            result = await run_operations.approve_run(sample_run_id)

        assert result is not None

    @pytest.mark.asyncio
    async def test_approve_with_logo_download_failure(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        mock_supabase: MagicMock,
        mock_ytd_calculator: MagicMock,
        sample_run_id: UUID,
        patch_paystub_services,
        patch_httpx_client,
        patch_remittance_service,
    ):
        """Should continue even if logo download fails."""
        run = make_payroll_run(
            run_id=str(sample_run_id),
            status="pending_approval",
        )
        mock_get_run_func.return_value = run

        company = make_company(logo_url="https://example.com/logo.png")
        employee = make_employee(
            vacation_config={"payout_method": "pay_as_you_go"},
            companies=company,
        )
        record = make_payroll_record(employee=employee)

        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[record])
        mock_table.update.return_value = mock_table
        mock_table.single.return_value = mock_table
        mock_supabase.table = MagicMock(return_value=mock_table)

        mock_ytd_calculator.get_ytd_records_for_employee = AsyncMock(return_value=[])

        patches = patch_paystub_services()

        # Make the first execute call return records, then return the approved run
        call_count = [0]

        def mock_execute():
            call_count[0] += 1
            if call_count[0] == 1:
                return MagicMock(data=[record])
            return MagicMock(data=[make_payroll_run(run_id=str(sample_run_id), status="approved")])

        mock_table.execute.side_effect = mock_execute

        with (
            patches["builder"],
            patches["generator"],
            patches["storage"],
            patch_httpx_client(raise_error=True),
            patch_remittance_service(),
        ):
            result = await run_operations.approve_run(sample_run_id)

        # Should still succeed even with logo failure
        assert result is not None

    @pytest.mark.asyncio
    async def test_approve_updates_vacation_balance(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        mock_supabase: MagicMock,
        mock_ytd_calculator: MagicMock,
        sample_run_id: UUID,
        patch_paystub_services,
        patch_httpx_client,
        patch_remittance_service,
    ):
        """Should update vacation balances for accrual employees."""
        run = make_payroll_run(
            run_id=str(sample_run_id),
            status="pending_approval",
        )
        mock_get_run_func.return_value = run

        employee = make_employee(
            vacation_config={"payout_method": "accrual", "vacation_rate": 0.04},
            vacation_balance=500.0,
        )
        record = make_payroll_record(
            employee=employee,
            vacation_accrued=80.0,
            vacation_pay_paid=100.0,
        )

        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[record])
        mock_table.update.return_value = mock_table
        mock_table.single.return_value = mock_table
        mock_supabase.table = MagicMock(return_value=mock_table)

        mock_ytd_calculator.get_ytd_records_for_employee = AsyncMock(return_value=[])

        patches = patch_paystub_services()

        call_count = [0]

        def mock_execute():
            call_count[0] += 1
            if call_count[0] == 1:
                return MagicMock(data=[record])
            return MagicMock(data=[make_payroll_run(run_id=str(sample_run_id), status="approved")])

        mock_table.execute.side_effect = mock_execute

        with (
            patches["builder"],
            patches["generator"],
            patches["storage"],
            patch_httpx_client(),
            patch_remittance_service(),
        ):
            result = await run_operations.approve_run(sample_run_id)

        assert result is not None
        # Verify employee update was called
        assert mock_table.update.called


class TestApproveRunWithApprovedBy:
    """Tests for approve_run with approved_by parameter."""

    @pytest.mark.asyncio
    async def test_approve_with_approved_by(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        mock_supabase: MagicMock,
        mock_ytd_calculator: MagicMock,
        sample_run_id: UUID,
        patch_paystub_services,
        patch_httpx_client,
        patch_remittance_service,
    ):
        """Should include approved_by in the update."""
        run = make_payroll_run(
            run_id=str(sample_run_id),
            status="pending_approval",
        )
        mock_get_run_func.return_value = run

        employee = make_employee(
            vacation_config={"payout_method": "pay_as_you_go"},
        )
        record = make_payroll_record(employee=employee)

        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[record])
        mock_table.update.return_value = mock_table
        mock_table.single.return_value = mock_table
        mock_supabase.table = MagicMock(return_value=mock_table)

        mock_ytd_calculator.get_ytd_records_for_employee = AsyncMock(return_value=[])

        patches = patch_paystub_services()

        call_count = [0]

        def mock_execute():
            call_count[0] += 1
            if call_count[0] == 1:
                return MagicMock(data=[record])
            return MagicMock(data=[make_payroll_run(run_id=str(sample_run_id), status="approved")])

        mock_table.execute.side_effect = mock_execute

        with (
            patches["builder"],
            patches["generator"],
            patches["storage"],
            patch_httpx_client(),
            patch_remittance_service(),
        ):
            result = await run_operations.approve_run(sample_run_id, approved_by="admin@test.com")

        assert result is not None


class TestApproveRunPaystubErrors:
    """Tests for approve_run paystub generation error handling."""

    @pytest.mark.asyncio
    async def test_missing_company_data(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        mock_supabase: MagicMock,
        mock_ytd_calculator: MagicMock,
        sample_run_id: UUID,
        patch_paystub_services,
        patch_httpx_client,
    ):
        """Should raise error when company data is missing."""
        run = make_payroll_run(
            run_id=str(sample_run_id),
            status="pending_approval",
        )
        mock_get_run_func.return_value = run

        # Create employee with no company data
        employee = make_employee(
            vacation_config={"payout_method": "pay_as_you_go"},
            companies=None,
        )
        record = make_payroll_record(employee=employee)
        # Remove companies from the record
        record["employees"]["companies"] = None

        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[record])
        mock_table.update.return_value = mock_table
        mock_supabase.table = MagicMock(return_value=mock_table)

        mock_ytd_calculator.get_ytd_records_for_employee = AsyncMock(return_value=[])

        patches = patch_paystub_services()

        with (
            patches["builder"],
            patches["generator"],
            patches["storage"],
            patch_httpx_client(),
        ):
            with pytest.raises(ValueError, match="missing company data"):
                await run_operations.approve_run(sample_run_id)

    @pytest.mark.asyncio
    async def test_paystub_generation_exception(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        mock_supabase: MagicMock,
        mock_ytd_calculator: MagicMock,
        sample_run_id: UUID,
        patch_httpx_client,
    ):
        """Should raise error with details when paystub generation fails."""
        from unittest.mock import patch

        run = make_payroll_run(
            run_id=str(sample_run_id),
            status="pending_approval",
        )
        mock_get_run_func.return_value = run

        employee = make_employee(
            vacation_config={"payout_method": "pay_as_you_go"},
        )
        record = make_payroll_record(employee=employee)

        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[record])
        mock_table.update.return_value = mock_table
        mock_supabase.table = MagicMock(return_value=mock_table)

        mock_ytd_calculator.get_ytd_records_for_employee = AsyncMock(return_value=[])

        # Mock PaystubDataBuilder to raise exception
        mock_builder = MagicMock()
        mock_builder.build.side_effect = Exception("PDF generation failed")

        with (
            patch(
                "app.services.payroll_run.run_operations.PaystubDataBuilder",
                return_value=mock_builder,
            ),
            patch(
                "app.services.payroll_run.run_operations.PaystubGenerator",
                return_value=MagicMock(),
            ),
            patch(
                "app.services.payroll_run.run_operations.PaystubStorage",
                return_value=MagicMock(),
            ),
            patch_httpx_client(),
        ):
            with pytest.raises(ValueError, match="Failed to generate.*paystub"):
                await run_operations.approve_run(sample_run_id)

    @pytest.mark.asyncio
    async def test_more_than_five_paystub_errors(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        mock_supabase: MagicMock,
        mock_ytd_calculator: MagicMock,
        sample_run_id: UUID,
        patch_httpx_client,
    ):
        """Should show '... and N more' when more than 5 paystub errors."""
        from unittest.mock import patch

        run = make_payroll_run(
            run_id=str(sample_run_id),
            status="pending_approval",
        )
        mock_get_run_func.return_value = run

        # Create 7 records with missing company data
        records = [
            make_payroll_record(
                employee=make_employee(
                    first_name=f"Employee{i}",
                    last_name=f"Last{i}",
                    vacation_config={"payout_method": "pay_as_you_go"},
                    companies=None,
                ),
            )
            for i in range(7)
        ]
        # Remove companies from all records
        for record in records:
            record["employees"]["companies"] = None

        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=records)
        mock_table.update.return_value = mock_table
        mock_supabase.table = MagicMock(return_value=mock_table)

        mock_ytd_calculator.get_ytd_records_for_employee = AsyncMock(return_value=[])

        mock_builder = MagicMock()
        mock_builder.build.return_value = MagicMock()

        with (
            patch(
                "app.services.payroll_run.run_operations.PaystubDataBuilder",
                return_value=mock_builder,
            ),
            patch(
                "app.services.payroll_run.run_operations.PaystubGenerator",
                return_value=MagicMock(),
            ),
            patch(
                "app.services.payroll_run.run_operations.PaystubStorage",
                return_value=MagicMock(),
            ),
            patch_httpx_client(),
        ):
            with pytest.raises(ValueError, match=r"and 2 more"):
                await run_operations.approve_run(sample_run_id)

    @pytest.mark.asyncio
    async def test_update_run_status_fails(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        mock_supabase: MagicMock,
        mock_ytd_calculator: MagicMock,
        sample_run_id: UUID,
        patch_paystub_services,
        patch_httpx_client,
        patch_remittance_service,
    ):
        """Should raise error when run status update fails."""
        run = make_payroll_run(
            run_id=str(sample_run_id),
            status="pending_approval",
        )
        mock_get_run_func.return_value = run

        employee = make_employee(
            vacation_config={"payout_method": "pay_as_you_go"},
        )
        record = make_payroll_record(employee=employee)

        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.update.return_value = mock_table
        mock_table.single.return_value = mock_table
        mock_supabase.table = MagicMock(return_value=mock_table)

        mock_ytd_calculator.get_ytd_records_for_employee = AsyncMock(return_value=[])

        patches = patch_paystub_services()

        # Track calls to return different data based on operation
        call_count = [0]

        def mock_execute():
            call_count[0] += 1
            if call_count[0] == 1:
                # First: fetch records
                return MagicMock(data=[record])
            elif call_count[0] == 2:
                # Second: update record with paystub info
                return MagicMock(data=[record])
            elif call_count[0] == 3:
                # Third: update employee vacation balance (skip for pay_as_you_go)
                return MagicMock(data=[])
            elif call_count[0] == 4:
                # Fourth: update run status - FAIL
                return MagicMock(data=[])
            return MagicMock(data=[])

        mock_table.execute.side_effect = mock_execute

        with (
            patches["builder"],
            patches["generator"],
            patches["storage"],
            patch_httpx_client(),
            patch_remittance_service(),
        ):
            with pytest.raises(ValueError, match="Failed to update payroll run status"):
                await run_operations.approve_run(sample_run_id)
