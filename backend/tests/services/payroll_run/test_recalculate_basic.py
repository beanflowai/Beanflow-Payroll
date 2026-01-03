"""
Tests for PayrollRunOperations.recalculate_run basic functionality.

Covers:
- Single salaried employee
- Hourly employee
- Multiple employees
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from app.services.payroll_run.run_operations import PayrollRunOperations

from .conftest import (
    make_employee,
    make_payroll_record,
    make_payroll_result,
    make_payroll_run,
)


class TestRecalculateRunBasic:
    """Tests for basic recalculate_run functionality."""

    @pytest.mark.asyncio
    async def test_single_salaried_employee(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        mock_get_run_records_func: AsyncMock,
        mock_supabase: MagicMock,
        mock_ytd_calculator: MagicMock,
        sample_run_id: UUID,
        patch_payroll_engine,
    ):
        """Should recalculate a single salaried employee correctly."""
        employee_id = str(uuid4())
        run = make_payroll_run(run_id=str(sample_run_id), status="draft")
        employee = make_employee(
            employee_id=employee_id,
            annual_salary=60000.0,
            province="SK",
        )
        record = make_payroll_record(
            payroll_run_id=str(sample_run_id),
            employee_id=employee_id,
            employee=employee,
            input_data={"regularHours": 80},
        )

        mock_get_run_func.return_value = run
        mock_get_run_records_func.return_value = [record]
        mock_ytd_calculator.get_prior_ytd_for_employees.return_value = {}

        # Mock supabase table operations
        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.gte.return_value = mock_table
        mock_table.lte.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[])
        mock_table.update.return_value = mock_table
        mock_supabase.table = MagicMock(return_value=mock_table)

        # Create mock payroll result
        payroll_result = make_payroll_result(employee_id=employee_id)

        with patch_payroll_engine([payroll_result]):
            result = await run_operations.recalculate_run(sample_run_id)

        # Verify run was returned
        assert result is not None
        # Verify update was called on payroll_records
        assert mock_table.update.called

    @pytest.mark.asyncio
    async def test_hourly_employee(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        mock_get_run_records_func: AsyncMock,
        mock_supabase: MagicMock,
        mock_ytd_calculator: MagicMock,
        sample_run_id: UUID,
        patch_payroll_engine,
    ):
        """Should recalculate an hourly employee correctly."""
        employee_id = str(uuid4())
        run = make_payroll_run(run_id=str(sample_run_id), status="draft")
        employee = make_employee(
            employee_id=employee_id,
            annual_salary=None,
            hourly_rate=25.0,
            province="SK",
        )
        record = make_payroll_record(
            payroll_run_id=str(sample_run_id),
            employee_id=employee_id,
            employee=employee,
            input_data={"regularHours": 80},
        )

        mock_get_run_func.return_value = run
        mock_get_run_records_func.return_value = [record]
        mock_ytd_calculator.get_prior_ytd_for_employees.return_value = {}

        # Mock supabase table operations
        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.gte.return_value = mock_table
        mock_table.lte.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[])
        mock_table.update.return_value = mock_table
        mock_supabase.table = MagicMock(return_value=mock_table)

        # Create mock payroll result (hourly: 80 * 25 = 2000)
        payroll_result = make_payroll_result(
            employee_id=employee_id,
            gross_regular=Decimal("2000.00"),
        )

        with patch_payroll_engine([payroll_result]):
            result = await run_operations.recalculate_run(sample_run_id)

        assert result is not None

    @pytest.mark.asyncio
    async def test_multiple_employees(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        mock_get_run_records_func: AsyncMock,
        mock_supabase: MagicMock,
        mock_ytd_calculator: MagicMock,
        sample_run_id: UUID,
        patch_payroll_engine,
    ):
        """Should recalculate multiple employees correctly."""
        emp1_id = str(uuid4())
        emp2_id = str(uuid4())
        run = make_payroll_run(run_id=str(sample_run_id), status="draft")

        records = [
            make_payroll_record(
                payroll_run_id=str(sample_run_id),
                employee_id=emp1_id,
                employee=make_employee(employee_id=emp1_id, first_name="John"),
                input_data={"regularHours": 80},
            ),
            make_payroll_record(
                payroll_run_id=str(sample_run_id),
                employee_id=emp2_id,
                employee=make_employee(employee_id=emp2_id, first_name="Jane"),
                input_data={"regularHours": 80},
            ),
        ]

        mock_get_run_func.return_value = run
        mock_get_run_records_func.return_value = records
        mock_ytd_calculator.get_prior_ytd_for_employees.return_value = {}

        # Mock supabase table operations
        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.gte.return_value = mock_table
        mock_table.lte.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[])
        mock_table.update.return_value = mock_table
        mock_supabase.table = MagicMock(return_value=mock_table)

        # Create mock payroll results
        payroll_results = [
            make_payroll_result(employee_id=emp1_id),
            make_payroll_result(employee_id=emp2_id),
        ]

        with patch_payroll_engine(payroll_results):
            result = await run_operations.recalculate_run(sample_run_id)

        assert result is not None
        # Verify update was called for each employee record
        assert mock_table.update.call_count >= 2
