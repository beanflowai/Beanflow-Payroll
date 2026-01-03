"""
Tests for PayrollRunOperations vacation balance methods.

Covers:
- _validate_vacation_balances
- _update_vacation_balances
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.services.payroll_run.run_operations import PayrollRunOperations

from .conftest import make_employee, make_payroll_record


class TestValidateVacationBalances:
    """Tests for _validate_vacation_balances."""

    def test_no_accrual_employees(self, run_operations: PayrollRunOperations):
        """Should return empty list when no accrual employees."""
        records = [
            make_payroll_record(
                employee=make_employee(
                    vacation_config={"payout_method": "pay_as_you_go"},
                ),
            )
        ]

        errors = run_operations._validate_vacation_balances(records)
        assert errors == []

    def test_sufficient_balance(self, run_operations: PayrollRunOperations):
        """Should return empty list when balance is sufficient."""
        records = [
            make_payroll_record(
                employee=make_employee(
                    first_name="John",
                    last_name="Doe",
                    vacation_config={"payout_method": "accrual"},
                    vacation_balance=200.0,
                ),
                vacation_pay_paid=100.0,
            )
        ]

        errors = run_operations._validate_vacation_balances(records)
        assert errors == []

    def test_insufficient_balance(self, run_operations: PayrollRunOperations):
        """Should return error when balance is insufficient."""
        records = [
            make_payroll_record(
                employee=make_employee(
                    first_name="John",
                    last_name="Doe",
                    vacation_config={"payout_method": "accrual"},
                    vacation_balance=50.0,
                ),
                vacation_pay_paid=100.0,
            )
        ]

        errors = run_operations._validate_vacation_balances(records)
        assert len(errors) == 1
        assert "John Doe" in errors[0]
        assert "balance $50.00" in errors[0]
        assert "requested $100.00" in errors[0]

    def test_zero_vacation_pay(self, run_operations: PayrollRunOperations):
        """Should skip employees with zero vacation pay."""
        records = [
            make_payroll_record(
                employee=make_employee(
                    vacation_config={"payout_method": "accrual"},
                    vacation_balance=50.0,
                ),
                vacation_pay_paid=0.0,
            )
        ]

        errors = run_operations._validate_vacation_balances(records)
        assert errors == []

    def test_multiple_employees_with_errors(self, run_operations: PayrollRunOperations):
        """Should return errors for multiple employees with insufficient balance."""
        records = [
            make_payroll_record(
                employee=make_employee(
                    first_name="John",
                    last_name="Doe",
                    vacation_config={"payout_method": "accrual"},
                    vacation_balance=50.0,
                ),
                vacation_pay_paid=100.0,
            ),
            make_payroll_record(
                employee=make_employee(
                    first_name="Jane",
                    last_name="Smith",
                    vacation_config={"payout_method": "accrual"},
                    vacation_balance=25.0,
                ),
                vacation_pay_paid=75.0,
            ),
        ]

        errors = run_operations._validate_vacation_balances(records)
        assert len(errors) == 2

    def test_more_than_five_errors_truncated(self, run_operations: PayrollRunOperations):
        """Should return only error messages, truncation handled in approve_run."""
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

        errors = run_operations._validate_vacation_balances(records)
        # All 7 errors should be returned (truncation is done in approve_run)
        assert len(errors) == 7


class TestUpdateVacationBalances:
    """Tests for _update_vacation_balances."""

    @pytest.mark.asyncio
    async def test_skip_non_accrual_employees(
        self,
        run_operations: PayrollRunOperations,
        mock_supabase: MagicMock,
    ):
        """Should skip employees with non-accrual payout method."""
        records = [
            make_payroll_record(
                employee=make_employee(
                    vacation_config={"payout_method": "pay_as_you_go"},
                ),
            )
        ]

        mock_table = MagicMock()
        mock_supabase.table = MagicMock(return_value=mock_table)

        await run_operations._update_vacation_balances(records)

        # No update should be called
        mock_table.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_skip_no_changes(
        self,
        run_operations: PayrollRunOperations,
        mock_supabase: MagicMock,
    ):
        """Should skip when no vacation accrued or paid."""
        records = [
            make_payroll_record(
                employee=make_employee(
                    vacation_config={"payout_method": "accrual"},
                ),
                vacation_accrued=0.0,
                vacation_pay_paid=0.0,
            )
        ]

        mock_table = MagicMock()
        mock_supabase.table = MagicMock(return_value=mock_table)

        await run_operations._update_vacation_balances(records)

        mock_table.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_balance_with_accrual_and_payment(
        self,
        run_operations: PayrollRunOperations,
        mock_supabase: MagicMock,
    ):
        """Should update balance: +accrued -paid."""
        employee_id = str(uuid4())
        records = [
            make_payroll_record(
                employee_id=employee_id,
                employee=make_employee(
                    employee_id=employee_id,
                    vacation_config={"payout_method": "accrual"},
                    vacation_balance=500.0,
                ),
                vacation_accrued=80.0,
                vacation_pay_paid=100.0,
            )
        ]

        mock_table = MagicMock()
        mock_table.update.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[])
        mock_supabase.table = MagicMock(return_value=mock_table)

        await run_operations._update_vacation_balances(records)

        # New balance: 500 + 80 - 100 = 480
        mock_table.update.assert_called()
        update_call_args = mock_table.update.call_args[0][0]
        assert update_call_args["vacation_balance"] == 480.0

    @pytest.mark.asyncio
    async def test_balance_does_not_go_negative(
        self,
        run_operations: PayrollRunOperations,
        mock_supabase: MagicMock,
    ):
        """Should not allow balance to go negative."""
        employee_id = str(uuid4())
        records = [
            make_payroll_record(
                employee_id=employee_id,
                employee=make_employee(
                    employee_id=employee_id,
                    vacation_config={"payout_method": "accrual"},
                    vacation_balance=50.0,
                ),
                vacation_accrued=10.0,
                vacation_pay_paid=100.0,  # Would make it -40
            )
        ]

        mock_table = MagicMock()
        mock_table.update.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[])
        mock_supabase.table = MagicMock(return_value=mock_table)

        await run_operations._update_vacation_balances(records)

        # Should be max(50 + 10 - 100, 0) = 0
        update_call_args = mock_table.update.call_args[0][0]
        assert update_call_args["vacation_balance"] == 0.0
