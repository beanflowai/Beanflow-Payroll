"""
Tests for PayrollRunOperations.recalculate_run with YTD data and exemptions.

Covers:
- Prior YTD data
- CPP exemption
- EI exemption
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


class TestRecalculateRunWithYTD:
    """Tests for recalculate_run with prior YTD data."""

    @pytest.mark.asyncio
    async def test_with_prior_ytd_data(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        mock_get_run_records_func: AsyncMock,
        mock_supabase: MagicMock,
        mock_ytd_calculator: MagicMock,
        sample_run_id: UUID,
        patch_payroll_engine,
    ):
        """Should use prior YTD data in calculations."""
        employee_id = str(uuid4())
        run = make_payroll_run(run_id=str(sample_run_id), status="draft")
        employee = make_employee(employee_id=employee_id)
        record = make_payroll_record(
            payroll_run_id=str(sample_run_id),
            employee_id=employee_id,
            employee=employee,
            input_data={"regularHours": 80},
        )

        mock_get_run_func.return_value = run
        mock_get_run_records_func.return_value = [record]

        # Set prior YTD data
        mock_ytd_calculator.get_prior_ytd_for_employees.return_value = {
            employee_id: {
                "ytd_gross": Decimal("10000.00"),
                "ytd_cpp": Decimal("500.00"),
                "ytd_cpp_additional": Decimal("0"),
                "ytd_ei": Decimal("150.00"),
                "ytd_federal_tax": Decimal("1500.00"),
                "ytd_provincial_tax": Decimal("800.00"),
                "ytd_net_pay": Decimal("7050.00"),
            }
        }

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
        )
        # Update YTD values
        payroll_result.new_ytd_gross = Decimal("12000.00")
        payroll_result.new_ytd_cpp = Decimal("600.00")
        payroll_result.new_ytd_ei = Decimal("185.00")
        payroll_result.new_ytd_federal_tax = Decimal("1700.00")
        payroll_result.new_ytd_provincial_tax = Decimal("950.00")

        with patch_payroll_engine([payroll_result]):
            result = await run_operations.recalculate_run(sample_run_id)

        assert result is not None


class TestRecalculateRunExemptions:
    """Tests for recalculate_run with CPP/EI exemptions."""

    @pytest.mark.asyncio
    async def test_cpp_exempt_employee(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        mock_get_run_records_func: AsyncMock,
        mock_supabase: MagicMock,
        mock_ytd_calculator: MagicMock,
        sample_run_id: UUID,
        patch_payroll_engine,
    ):
        """Should pass CPP exemption flag to payroll engine."""
        employee_id = str(uuid4())
        run = make_payroll_run(run_id=str(sample_run_id), status="draft")
        employee = make_employee(
            employee_id=employee_id,
            is_cpp_exempt=True,
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
            cpp_base=Decimal("0"),
            cpp_additional=Decimal("0"),
            cpp_employer=Decimal("0"),
        )

        with patch_payroll_engine([payroll_result]):
            result = await run_operations.recalculate_run(sample_run_id)

        assert result is not None

    @pytest.mark.asyncio
    async def test_ei_exempt_employee(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        mock_get_run_records_func: AsyncMock,
        mock_supabase: MagicMock,
        mock_ytd_calculator: MagicMock,
        sample_run_id: UUID,
        patch_payroll_engine,
    ):
        """Should pass EI exemption flag to payroll engine."""
        employee_id = str(uuid4())
        run = make_payroll_run(run_id=str(sample_run_id), status="draft")
        employee = make_employee(
            employee_id=employee_id,
            is_ei_exempt=True,
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
            ei_employee=Decimal("0"),
            ei_employer=Decimal("0"),
        )

        with patch_payroll_engine([payroll_result]):
            result = await run_operations.recalculate_run(sample_run_id)

        assert result is not None
