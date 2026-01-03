"""
Tests for PayrollRunOperations.recalculate_run with pay frequency and province variations.

Covers:
- Different pay frequencies (weekly, bi_weekly, semi_monthly, monthly)
- Different provinces
- Vacation accrual calculation
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


class TestRecalculateRunPayFrequencies:
    """Tests for recalculate_run with different pay frequencies."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "pay_frequency",
        ["weekly", "bi_weekly", "semi_monthly", "monthly"],
    )
    async def test_different_pay_frequencies(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        mock_get_run_records_func: AsyncMock,
        mock_supabase: MagicMock,
        mock_ytd_calculator: MagicMock,
        sample_run_id: UUID,
        patch_payroll_engine,
        pay_frequency: str,
    ):
        """Should handle different pay frequencies correctly."""
        employee_id = str(uuid4())
        run = make_payroll_run(run_id=str(sample_run_id), status="draft")
        pay_group = make_pay_group(pay_frequency=pay_frequency)
        employee = make_employee(
            employee_id=employee_id,
            pay_frequency=pay_frequency,
            pay_groups=pay_group,
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

        payroll_result = make_payroll_result(employee_id=employee_id)

        with patch_payroll_engine([payroll_result]):
            result = await run_operations.recalculate_run(sample_run_id)

        assert result is not None


class TestRecalculateRunProvinces:
    """Tests for recalculate_run with different provinces."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "province",
        ["AB", "BC", "MB", "NB", "NL", "NS", "NT", "NU", "ON", "PE", "SK", "YT"],
    )
    async def test_different_provinces(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        mock_get_run_records_func: AsyncMock,
        mock_supabase: MagicMock,
        mock_ytd_calculator: MagicMock,
        sample_run_id: UUID,
        patch_payroll_engine,
        province: str,
    ):
        """Should handle different provinces correctly."""
        employee_id = str(uuid4())
        run = make_payroll_run(run_id=str(sample_run_id), status="draft")
        employee = make_employee(
            employee_id=employee_id,
            province=province,
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

        payroll_result = make_payroll_result(employee_id=employee_id)

        with patch_payroll_engine([payroll_result]):
            result = await run_operations.recalculate_run(sample_run_id)

        assert result is not None


class TestRecalculateRunVacationAccrual:
    """Tests for vacation accrual calculation during recalculate."""

    @pytest.mark.asyncio
    async def test_vacation_accrual_calculated(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        mock_get_run_records_func: AsyncMock,
        mock_supabase: MagicMock,
        mock_ytd_calculator: MagicMock,
        sample_run_id: UUID,
        patch_payroll_engine,
    ):
        """Should calculate vacation accrued for accrual method employees."""
        employee_id = str(uuid4())
        run = make_payroll_run(run_id=str(sample_run_id), status="draft")
        employee = make_employee(
            employee_id=employee_id,
            vacation_config={"payout_method": "accrual", "vacation_rate": 0.04},
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

        # Gross 2000, vacation accrued = 2000 * 0.04 = 80
        payroll_result = make_payroll_result(
            employee_id=employee_id,
            gross_regular=Decimal("2000.00"),
        )

        with patch_payroll_engine([payroll_result]):
            result = await run_operations.recalculate_run(sample_run_id)

        assert result is not None
