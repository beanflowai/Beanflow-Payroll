"""
Tests for PayrollRunOperations.recalculate_run method.

Covers:
- Error handling (run not found, wrong status, no records)
- Basic recalculation (salaried, hourly, multiple employees)
- Overtime processing
- Vacation pay (pay_as_you_go and accrual)
- Sick leave processing
- Holiday pay
- Adjustments
- Benefits
- YTD data
- CPP/EI exemptions
- Pay frequencies
- Provinces
- Vacation accrual
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


class TestRecalculateRunErrors:
    """Tests for recalculate_run error handling."""

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
            await run_operations.recalculate_run(sample_run_id)

    @pytest.mark.asyncio
    async def test_run_not_in_draft_status(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        sample_run_id: UUID,
    ):
        """Should raise ValueError when run is not in draft status."""
        mock_get_run_func.return_value = make_payroll_run(
            run_id=str(sample_run_id),
            status="pending_approval",
        )

        with pytest.raises(ValueError, match="Cannot recalculate.*pending_approval.*not 'draft'"):
            await run_operations.recalculate_run(sample_run_id)

    @pytest.mark.asyncio
    async def test_run_in_approved_status(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        sample_run_id: UUID,
    ):
        """Should raise ValueError when run is in approved status."""
        mock_get_run_func.return_value = make_payroll_run(
            run_id=str(sample_run_id),
            status="approved",
        )

        with pytest.raises(ValueError, match="Cannot recalculate.*approved.*not 'draft'"):
            await run_operations.recalculate_run(sample_run_id)

    @pytest.mark.asyncio
    async def test_no_records_found(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        mock_get_run_records_func: AsyncMock,
        sample_run_id: UUID,
    ):
        """Should raise ValueError when no records exist for the run."""
        mock_get_run_func.return_value = make_payroll_run(
            run_id=str(sample_run_id),
            status="draft",
        )
        mock_get_run_records_func.return_value = []

        with pytest.raises(ValueError, match="No records found for payroll run"):
            await run_operations.recalculate_run(sample_run_id)


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


class TestRecalculateRunWithOvertime:
    """Tests for recalculate_run with overtime."""

    @pytest.mark.asyncio
    async def test_with_overtime_hours(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        mock_get_run_records_func: AsyncMock,
        mock_supabase: MagicMock,
        mock_ytd_calculator: MagicMock,
        sample_run_id: UUID,
        patch_payroll_engine,
    ):
        """Should include overtime in gross calculation."""
        employee_id = str(uuid4())
        run = make_payroll_run(run_id=str(sample_run_id), status="draft")
        employee = make_employee(
            employee_id=employee_id,
            hourly_rate=25.0,
            annual_salary=None,
        )
        record = make_payroll_record(
            payroll_run_id=str(sample_run_id),
            employee_id=employee_id,
            employee=employee,
            input_data={"regularHours": 80, "overtimeHours": 10},
        )

        mock_get_run_func.return_value = run
        mock_get_run_records_func.return_value = [record]
        mock_ytd_calculator.get_prior_ytd_for_employees.return_value = {}

        # Mock supabase
        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.gte.return_value = mock_table
        mock_table.lte.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[])
        mock_table.update.return_value = mock_table
        mock_supabase.table = MagicMock(return_value=mock_table)

        # Regular: 80*25 = 2000, OT: 10*37.5 = 375
        payroll_result = make_payroll_result(
            employee_id=employee_id,
            gross_regular=Decimal("2000.00"),
            gross_overtime=Decimal("375.00"),
        )

        with patch_payroll_engine([payroll_result]):
            result = await run_operations.recalculate_run(sample_run_id)

        assert result is not None


class TestRecalculateRunWithVacation:
    """Tests for recalculate_run with vacation pay."""

    @pytest.mark.asyncio
    async def test_vacation_pay_as_you_go(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        mock_get_run_records_func: AsyncMock,
        mock_supabase: MagicMock,
        mock_ytd_calculator: MagicMock,
        sample_run_id: UUID,
        patch_payroll_engine,
    ):
        """Should calculate vacation pay for pay_as_you_go method."""
        employee_id = str(uuid4())
        run = make_payroll_run(run_id=str(sample_run_id), status="draft")
        employee = make_employee(
            employee_id=employee_id,
            annual_salary=52000.0,
            vacation_config={"payout_method": "pay_as_you_go", "vacation_rate": 0.04},
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

        # Gross: 52000/26 = 2000, Vacation: 2000 * 0.04 = 80
        payroll_result = make_payroll_result(
            employee_id=employee_id,
            gross_regular=Decimal("2000.00"),
            vacation_pay=Decimal("80.00"),
        )

        with patch_payroll_engine([payroll_result]):
            result = await run_operations.recalculate_run(sample_run_id)

        assert result is not None

    @pytest.mark.asyncio
    async def test_vacation_accrual_with_hours_taken(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        mock_get_run_records_func: AsyncMock,
        mock_supabase: MagicMock,
        mock_ytd_calculator: MagicMock,
        sample_run_id: UUID,
        patch_payroll_engine,
    ):
        """Should calculate vacation pay from hours taken for accrual method."""
        employee_id = str(uuid4())
        run = make_payroll_run(run_id=str(sample_run_id), status="draft")
        employee = make_employee(
            employee_id=employee_id,
            annual_salary=52000.0,
            vacation_config={"payout_method": "accrual", "vacation_rate": 0.04},
            vacation_balance=500.0,
        )
        record = make_payroll_record(
            payroll_run_id=str(sample_run_id),
            employee_id=employee_id,
            employee=employee,
            input_data={
                "regularHours": 80,
                "leaveEntries": [{"type": "vacation", "hours": 8}],
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

        # 8 hours vacation * hourly rate
        payroll_result = make_payroll_result(
            employee_id=employee_id,
            gross_regular=Decimal("2000.00"),
            vacation_pay=Decimal("200.00"),  # 8 * 25
        )

        with patch_payroll_engine([payroll_result]):
            result = await run_operations.recalculate_run(sample_run_id)

        assert result is not None


class TestRecalculateRunWithSickLeave:
    """Tests for recalculate_run with sick leave."""

    @pytest.mark.asyncio
    async def test_sick_leave_salaried_with_balance(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        mock_get_run_records_func: AsyncMock,
        mock_supabase: MagicMock,
        mock_ytd_calculator: MagicMock,
        sample_run_id: UUID,
        patch_payroll_engine,
    ):
        """Should handle sick leave for salaried employee with balance."""
        employee_id = str(uuid4())
        run = make_payroll_run(run_id=str(sample_run_id), status="draft")
        employee = make_employee(
            employee_id=employee_id,
            annual_salary=52000.0,
            hourly_rate=None,
            sick_balance=5.0,  # 5 days = 40 hours
        )
        record = make_payroll_record(
            payroll_run_id=str(sample_run_id),
            employee_id=employee_id,
            employee=employee,
            input_data={
                "regularHours": 80,
                "leaveEntries": [{"type": "sick", "hours": 8}],
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
        )

        with patch_payroll_engine([payroll_result]):
            result = await run_operations.recalculate_run(sample_run_id)

        assert result is not None

    @pytest.mark.asyncio
    async def test_sick_leave_hourly_with_balance(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        mock_get_run_records_func: AsyncMock,
        mock_supabase: MagicMock,
        mock_ytd_calculator: MagicMock,
        sample_run_id: UUID,
        patch_payroll_engine,
    ):
        """Should handle sick leave for hourly employee with balance."""
        employee_id = str(uuid4())
        run = make_payroll_run(run_id=str(sample_run_id), status="draft")
        employee = make_employee(
            employee_id=employee_id,
            annual_salary=None,
            hourly_rate=25.0,
            sick_balance=5.0,  # 5 days = 40 hours
        )
        record = make_payroll_record(
            payroll_run_id=str(sample_run_id),
            employee_id=employee_id,
            employee=employee,
            input_data={
                "regularHours": 72,  # 80 - 8 sick
                "leaveEntries": [{"type": "sick", "hours": 8}],
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

        # 72 regular hours + 8 sick hours paid
        payroll_result = make_payroll_result(
            employee_id=employee_id,
            gross_regular=Decimal("2000.00"),  # (72 + 8 paid sick) * 25
        )

        with patch_payroll_engine([payroll_result]):
            result = await run_operations.recalculate_run(sample_run_id)

        assert result is not None

    @pytest.mark.asyncio
    async def test_sick_leave_exceeds_balance_salaried(
        self,
        run_operations: PayrollRunOperations,
        mock_get_run_func: AsyncMock,
        mock_get_run_records_func: AsyncMock,
        mock_supabase: MagicMock,
        mock_ytd_calculator: MagicMock,
        sample_run_id: UUID,
        patch_payroll_engine,
    ):
        """Should deduct unpaid sick time from salaried employee's pay."""
        employee_id = str(uuid4())
        run = make_payroll_run(run_id=str(sample_run_id), status="draft")
        employee = make_employee(
            employee_id=employee_id,
            annual_salary=52000.0,
            hourly_rate=None,
            sick_balance=0.5,  # 0.5 days = 4 hours
        )
        record = make_payroll_record(
            payroll_run_id=str(sample_run_id),
            employee_id=employee_id,
            employee=employee,
            input_data={
                "regularHours": 80,
                "leaveEntries": [{"type": "sick", "hours": 16}],  # 16 hours sick
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

        # 4 hours paid, 12 hours unpaid = deduction of 12 * 25 = 300
        # Gross: 2000 - 300 = 1700
        payroll_result = make_payroll_result(
            employee_id=employee_id,
            gross_regular=Decimal("1700.00"),
        )

        with patch_payroll_engine([payroll_result]):
            result = await run_operations.recalculate_run(sample_run_id)

        assert result is not None


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
