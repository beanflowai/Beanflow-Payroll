"""
Tests for PayrollRunOperations._update_remittance_period method.

Covers:
- Company not found
- Creates remittance period
"""

from __future__ import annotations

from unittest.mock import MagicMock

from app.services.payroll_run.run_operations import PayrollRunOperations

from .conftest import make_payroll_run


class TestUpdateRemittancePeriod:
    """Tests for _update_remittance_period."""

    def test_company_not_found(
        self,
        run_operations: PayrollRunOperations,
        mock_supabase: MagicMock,
    ):
        """Should log warning when company not found."""
        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.single.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=None)
        mock_supabase.table = MagicMock(return_value=mock_table)

        run = make_payroll_run()

        # Should not raise, just log
        run_operations._update_remittance_period(run)

    def test_creates_remittance_period(
        self,
        run_operations: PayrollRunOperations,
        mock_supabase: MagicMock,
        patch_remittance_service,
    ):
        """Should create remittance period for approved run."""
        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.single.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data={"remitter_type": "regular"})
        mock_supabase.table = MagicMock(return_value=mock_table)

        run = make_payroll_run()

        with patch_remittance_service(result={"id": "remit-123"}):
            run_operations._update_remittance_period(run)

        # Should complete without error
