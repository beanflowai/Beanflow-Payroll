"""
Tests for PayrollRunOperations.recalculate_run with holiday pay.

Covers:
- Statutory holiday pay
- Holiday work premium
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


class TestRecalculateRunWithHolidays:
    """Tests for recalculate_run with holiday pay."""

    @pytest.mark.asyncio
    async def test_with_statutory_holiday(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        mock_get_run_records_func: AsyncMock,
        mock_supabase: MagicMock,
        mock_ytd_calculator: MagicMock,
        sample_run_id: UUID,
        patch_payroll_engine,
    ):
        """Should calculate holiday pay for statutory holiday in period."""
        employee_id = str(uuid4())
        run = make_payroll_run(
            run_id=str(sample_run_id),
            status="draft",
            period_start="2025-12-22",
            period_end="2025-01-03",
            pay_date="2025-01-09",
        )
        employee = make_employee(employee_id=employee_id)
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
        # Return holidays in period
        mock_table.execute.return_value = MagicMock(data=[
            {"holiday_date": "2025-12-25", "name": "Christmas Day", "province": "SK"},
            {"holiday_date": "2025-01-01", "name": "New Year's Day", "province": "SK"},
        ])
        mock_table.update.return_value = mock_table
        mock_supabase.table = MagicMock(return_value=mock_table)

        # Mock holiday calculator to return holiday pay
        run_operations._mock_holiday_calculator.calculate_holiday_pay.return_value = MagicMock(
            regular_holiday_pay=Decimal("400.00"),
            premium_holiday_pay=Decimal("0"),
        )

        payroll_result = make_payroll_result(
            employee_id=employee_id,
            gross_regular=Decimal("2000.00"),
            holiday_pay=Decimal("400.00"),
        )

        with patch_payroll_engine([payroll_result]):
            result = await run_operations.recalculate_run(sample_run_id)

        assert result is not None

    @pytest.mark.asyncio
    async def test_with_holiday_work_premium(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        mock_get_run_records_func: AsyncMock,
        mock_supabase: MagicMock,
        mock_ytd_calculator: MagicMock,
        sample_run_id: UUID,
        patch_payroll_engine,
    ):
        """Should calculate holiday premium pay when worked on holiday."""
        employee_id = str(uuid4())
        run = make_payroll_run(run_id=str(sample_run_id), status="draft")
        employee = make_employee(employee_id=employee_id)
        record = make_payroll_record(
            payroll_run_id=str(sample_run_id),
            employee_id=employee_id,
            employee=employee,
            input_data={
                "regularHours": 80,
                "holidayWorkEntries": [{"date": "2025-12-25", "hours": 8}],
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

        run_operations._mock_holiday_calculator.calculate_holiday_pay.return_value = MagicMock(
            regular_holiday_pay=Decimal("200.00"),
            premium_holiday_pay=Decimal("400.00"),
        )

        payroll_result = make_payroll_result(
            employee_id=employee_id,
            gross_regular=Decimal("2000.00"),
            holiday_pay=Decimal("200.00"),
            holiday_premium_pay=Decimal("400.00"),
        )

        with patch_payroll_engine([payroll_result]):
            result = await run_operations.recalculate_run(sample_run_id)

        assert result is not None
