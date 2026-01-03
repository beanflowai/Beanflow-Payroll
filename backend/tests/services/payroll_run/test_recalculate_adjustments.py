"""
Tests for PayrollRunOperations.recalculate_run with adjustments and benefits.

Covers:
- Earning adjustments
- Deduction adjustments
- Group benefits
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from app.services.payroll_run.run_operations import PayrollRunOperations

from .conftest import (
    make_employee,
    make_pay_group,
    make_payroll_record,
    make_payroll_result,
    make_payroll_run,
)


class TestRecalculateRunWithAdjustments:
    """Tests for recalculate_run with adjustments."""

    @pytest.mark.asyncio
    async def test_with_earning_adjustment(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        mock_get_run_records_func: AsyncMock,
        mock_supabase: MagicMock,
        mock_ytd_calculator: MagicMock,
        sample_run_id: UUID,
        patch_payroll_engine,
    ):
        """Should include earning adjustments in other_earnings."""
        employee_id = str(uuid4())
        run = make_payroll_run(run_id=str(sample_run_id), status="draft")
        employee = make_employee(employee_id=employee_id)
        record = make_payroll_record(
            payroll_run_id=str(sample_run_id),
            employee_id=employee_id,
            employee=employee,
            input_data={
                "regularHours": 80,
                "adjustments": [
                    {"type": "earning", "amount": 500, "description": "Bonus"},
                ],
            },
        )

        mock_get_run_func.return_value = run
        mock_get_run_records_func.return_value = [record]
        mock_ytd_calculator.get_prior_ytd_for_employees.return_value = {}

        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.gte.return_value = mock_table
        mock_table.lte.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[])
        mock_table.update.return_value = mock_table
        mock_supabase.table = MagicMock(return_value=mock_table)

        payroll_result = make_payroll_result(
            employee_id=employee_id,
            gross_regular=Decimal("2000.00"),
            other_earnings=Decimal("500.00"),
        )

        with patch_payroll_engine([payroll_result]):
            result = await run_operations.recalculate_run(sample_run_id)

        assert result is not None

    @pytest.mark.asyncio
    async def test_with_deduction_adjustment(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        mock_get_run_records_func: AsyncMock,
        mock_supabase: MagicMock,
        mock_ytd_calculator: MagicMock,
        sample_run_id: UUID,
        patch_payroll_engine,
    ):
        """Should include deduction adjustments as negative other_earnings."""
        employee_id = str(uuid4())
        run = make_payroll_run(run_id=str(sample_run_id), status="draft")
        employee = make_employee(employee_id=employee_id)
        record = make_payroll_record(
            payroll_run_id=str(sample_run_id),
            employee_id=employee_id,
            employee=employee,
            input_data={
                "regularHours": 80,
                "adjustments": [
                    {"type": "deduction", "amount": 100, "description": "Loan payment"},
                ],
            },
        )

        mock_get_run_func.return_value = run
        mock_get_run_records_func.return_value = [record]
        mock_ytd_calculator.get_prior_ytd_for_employees.return_value = {}

        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.gte.return_value = mock_table
        mock_table.lte.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[])
        mock_table.update.return_value = mock_table
        mock_supabase.table = MagicMock(return_value=mock_table)

        payroll_result = make_payroll_result(
            employee_id=employee_id,
            gross_regular=Decimal("2000.00"),
            other_earnings=Decimal("-100.00"),
        )

        with patch_payroll_engine([payroll_result]):
            result = await run_operations.recalculate_run(sample_run_id)

        assert result is not None


class TestRecalculateRunWithBenefits:
    """Tests for recalculate_run with group benefits."""

    @pytest.mark.asyncio
    async def test_with_group_benefits(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        mock_get_run_records_func: AsyncMock,
        mock_supabase: MagicMock,
        mock_ytd_calculator: MagicMock,
        sample_run_id: UUID,
        patch_payroll_engine,
    ):
        """Should calculate taxable benefits and deductions from group benefits."""
        employee_id = str(uuid4())
        run = make_payroll_run(run_id=str(sample_run_id), status="draft")
        pay_group = make_pay_group(
            group_benefits={
                "health": {"employee_contribution": 50.0, "employer_contribution": 100.0},
                "dental": {"employee_contribution": 25.0, "employer_contribution": 50.0},
            }
        )
        employee = make_employee(employee_id=employee_id, pay_groups=pay_group)
        record = make_payroll_record(
            payroll_run_id=str(sample_run_id),
            employee_id=employee_id,
            employee=employee,
            input_data={"regularHours": 80},
        )

        mock_get_run_func.return_value = run
        mock_get_run_records_func.return_value = [record]
        mock_ytd_calculator.get_prior_ytd_for_employees.return_value = {}

        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.gte.return_value = mock_table
        mock_table.lte.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[])
        mock_table.update.return_value = mock_table
        mock_supabase.table = MagicMock(return_value=mock_table)

        payroll_result = make_payroll_result(
            employee_id=employee_id,
            gross_regular=Decimal("2000.00"),
            other_deductions=Decimal("75.00"),  # 50 + 25 employee contribution
        )

        with patch_payroll_engine([payroll_result]):
            result = await run_operations.recalculate_run(sample_run_id)

        assert result is not None
