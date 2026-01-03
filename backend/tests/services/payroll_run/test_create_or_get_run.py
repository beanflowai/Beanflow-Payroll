"""
Tests for PayrollRunOperations run creation methods.

Covers:
- create_or_get_run (deprecated)
- create_or_get_run_by_period_end
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.services.payroll_run.run_operations import PayrollRunOperations

from .conftest import make_pay_group, make_payroll_result, make_payroll_run


class TestCreateOrGetRun:
    """Tests for create_or_get_run (deprecated method)."""

    @pytest.mark.asyncio
    async def test_delegates_to_create_or_get_run_by_period_end(
        self,
        run_operations: PayrollRunOperations,
        mock_supabase: MagicMock,
    ):
        """Should delegate to create_or_get_run_by_period_end."""
        # Setup mock for existing run
        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        existing_run = make_payroll_run(period_end="2025-01-17")
        mock_table.execute.return_value = MagicMock(data=[existing_run])
        mock_supabase.table = MagicMock(return_value=mock_table)

        # pay_date = period_end + 6 days (for SK)
        # So pay_date 2025-01-23 -> period_end 2025-01-17
        result = await run_operations.create_or_get_run("2025-01-23")

        assert result["created"] is False
        assert result["run"] == existing_run


class TestCreateOrGetRunByPeriodEnd:
    """Tests for create_or_get_run_by_period_end."""

    @pytest.mark.asyncio
    async def test_returns_existing_run(
        self,
        run_operations: PayrollRunOperations,
        mock_supabase: MagicMock,
    ):
        """Should return existing run without creating new one."""
        existing_run = make_payroll_run(period_end="2025-01-17")

        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[existing_run])
        mock_supabase.table = MagicMock(return_value=mock_table)

        result = await run_operations.create_or_get_run_by_period_end("2025-01-17")

        assert result["created"] is False
        assert result["run"] == existing_run
        assert result["records_count"] == 0

    @pytest.mark.asyncio
    async def test_no_pay_groups_found(
        self,
        run_operations: PayrollRunOperations,
        mock_supabase: MagicMock,
    ):
        """Should raise ValueError when no pay groups found."""
        call_count = [0]

        def mock_execute():
            call_count[0] += 1
            if call_count[0] == 1:
                # First call: no existing run
                return MagicMock(data=[])
            elif call_count[0] == 2:
                # Second call: no pay groups
                return MagicMock(data=[])
            return MagicMock(data=[])

        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.side_effect = mock_execute
        mock_supabase.table = MagicMock(return_value=mock_table)

        with pytest.raises(ValueError, match="No pay groups found with period end"):
            await run_operations.create_or_get_run_by_period_end("2025-01-17")

    @pytest.mark.asyncio
    async def test_no_active_employees(
        self,
        run_operations: PayrollRunOperations,
        mock_supabase: MagicMock,
    ):
        """Should raise ValueError when no active employees found."""
        call_count = [0]

        def mock_execute():
            call_count[0] += 1
            if call_count[0] == 1:
                # First call: no existing run
                return MagicMock(data=[])
            elif call_count[0] == 2:
                # Second call: pay groups found
                return MagicMock(data=[make_pay_group()])
            elif call_count[0] == 3:
                # Third call: no employees
                return MagicMock(data=[])
            return MagicMock(data=[])

        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_table.is_.return_value = mock_table
        mock_table.execute.side_effect = mock_execute
        mock_supabase.table = MagicMock(return_value=mock_table)

        with pytest.raises(ValueError, match="No active employees found"):
            await run_operations.create_or_get_run_by_period_end("2025-01-17")

    @pytest.mark.asyncio
    async def test_creates_new_run(
        self,
        run_operations: PayrollRunOperations,
        mock_supabase: MagicMock,
        mock_create_records_func: AsyncMock,
        mock_get_run_func: AsyncMock,
    ):
        """Should create new run with records."""
        employee_id = str(uuid4())
        pay_group_id = str(uuid4())
        pay_group = make_pay_group(pay_group_id=pay_group_id)
        employee = {
            "id": employee_id,
            "first_name": "John",
            "last_name": "Doe",
            "province_of_employment": "SK",
            "pay_group_id": pay_group_id,
            "annual_salary": 60000.0,
            "hourly_rate": None,
            "federal_additional_claims": 0,
            "provincial_additional_claims": 0,
            "is_cpp_exempt": False,
            "is_ei_exempt": False,
            "cpp2_exempt": False,
            "vacation_config": {"payout_method": "accrual"},
        }

        call_count = [0]
        new_run_id = str(uuid4())

        def mock_execute():
            call_count[0] += 1
            if call_count[0] == 1:
                # First call: no existing run
                return MagicMock(data=[])
            elif call_count[0] == 2:
                # Second call: pay groups found
                return MagicMock(data=[pay_group])
            elif call_count[0] == 3:
                # Third call: employees found
                return MagicMock(data=[employee])
            elif call_count[0] == 4:
                # Fourth call: run created
                return MagicMock(data=[make_payroll_run(run_id=new_run_id)])
            return MagicMock(data=[])

        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_table.is_.return_value = mock_table
        mock_table.insert.return_value = mock_table
        mock_table.update.return_value = mock_table
        mock_table.execute.side_effect = mock_execute
        mock_supabase.table = MagicMock(return_value=mock_table)

        # Mock create_records_func to return payroll results
        payroll_result = make_payroll_result(employee_id=employee_id)
        mock_create_records_func.return_value = ([], [payroll_result])

        # Mock get_run to return the updated run
        mock_get_run_func.return_value = make_payroll_run(run_id=new_run_id)

        result = await run_operations.create_or_get_run_by_period_end("2025-01-17")

        assert result["created"] is True
        assert result["records_count"] == 1

    @pytest.mark.asyncio
    async def test_period_start_calculation_weekly(
        self,
        run_operations: PayrollRunOperations,
        mock_supabase: MagicMock,
        mock_create_records_func: AsyncMock,
        mock_get_run_func: AsyncMock,
    ):
        """Should calculate correct period_start for weekly frequency."""
        pay_group = make_pay_group(pay_frequency="weekly")
        employee = {
            "id": str(uuid4()),
            "first_name": "John",
            "last_name": "Doe",
            "province_of_employment": "SK",
            "pay_group_id": pay_group["id"],
            "annual_salary": 60000.0,
            "hourly_rate": None,
            "federal_additional_claims": 0,
            "provincial_additional_claims": 0,
            "is_cpp_exempt": False,
            "is_ei_exempt": False,
            "cpp2_exempt": False,
            "vacation_config": {},
        }

        call_count = [0]
        new_run_id = str(uuid4())

        def mock_execute():
            call_count[0] += 1
            if call_count[0] == 1:
                return MagicMock(data=[])
            elif call_count[0] == 2:
                return MagicMock(data=[pay_group])
            elif call_count[0] == 3:
                return MagicMock(data=[employee])
            elif call_count[0] == 4:
                return MagicMock(data=[make_payroll_run(
                    run_id=new_run_id,
                    period_start="2025-01-11",
                    period_end="2025-01-17",
                )])
            return MagicMock(data=[])

        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_table.is_.return_value = mock_table
        mock_table.insert.return_value = mock_table
        mock_table.update.return_value = mock_table
        mock_table.execute.side_effect = mock_execute
        mock_supabase.table = MagicMock(return_value=mock_table)

        mock_create_records_func.return_value = ([], [])
        mock_get_run_func.return_value = None

        result = await run_operations.create_or_get_run_by_period_end("2025-01-17")

        # Verify insert was called with correct period_start
        insert_call = mock_table.insert.call_args[0][0]
        # Weekly: period_end - 6 days
        assert insert_call["period_start"] == "2025-01-11"

    @pytest.mark.asyncio
    async def test_period_start_calculation_monthly(
        self,
        run_operations: PayrollRunOperations,
        mock_supabase: MagicMock,
        mock_create_records_func: AsyncMock,
        mock_get_run_func: AsyncMock,
    ):
        """Should calculate correct period_start for monthly frequency."""
        pay_group = make_pay_group(pay_frequency="monthly")
        employee = {
            "id": str(uuid4()),
            "first_name": "John",
            "last_name": "Doe",
            "province_of_employment": "SK",
            "pay_group_id": pay_group["id"],
            "annual_salary": 60000.0,
            "hourly_rate": None,
            "federal_additional_claims": 0,
            "provincial_additional_claims": 0,
            "is_cpp_exempt": False,
            "is_ei_exempt": False,
            "cpp2_exempt": False,
            "vacation_config": {},
        }

        call_count = [0]
        new_run_id = str(uuid4())

        def mock_execute():
            call_count[0] += 1
            if call_count[0] == 1:
                return MagicMock(data=[])
            elif call_count[0] == 2:
                return MagicMock(data=[pay_group])
            elif call_count[0] == 3:
                return MagicMock(data=[employee])
            elif call_count[0] == 4:
                return MagicMock(data=[make_payroll_run(
                    run_id=new_run_id,
                    period_start="2025-01-01",
                    period_end="2025-01-31",
                )])
            return MagicMock(data=[])

        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_table.is_.return_value = mock_table
        mock_table.insert.return_value = mock_table
        mock_table.update.return_value = mock_table
        mock_table.execute.side_effect = mock_execute
        mock_supabase.table = MagicMock(return_value=mock_table)

        mock_create_records_func.return_value = ([], [])
        mock_get_run_func.return_value = None

        result = await run_operations.create_or_get_run_by_period_end("2025-01-31")

        # Verify insert was called with correct period_start
        insert_call = mock_table.insert.call_args[0][0]
        # Monthly: first day of month
        assert insert_call["period_start"] == "2025-01-01"

    @pytest.mark.asyncio
    async def test_period_start_calculation_semi_monthly_first_half(
        self,
        run_operations: PayrollRunOperations,
        mock_supabase: MagicMock,
        mock_create_records_func: AsyncMock,
        mock_get_run_func: AsyncMock,
    ):
        """Should calculate correct period_start for semi_monthly first half (day <= 15)."""
        pay_group = make_pay_group(pay_frequency="semi_monthly")
        employee = {
            "id": str(uuid4()),
            "first_name": "John",
            "last_name": "Doe",
            "province_of_employment": "SK",
            "pay_group_id": pay_group["id"],
            "annual_salary": 60000.0,
            "hourly_rate": None,
            "federal_additional_claims": 0,
            "provincial_additional_claims": 0,
            "is_cpp_exempt": False,
            "is_ei_exempt": False,
            "cpp2_exempt": False,
            "vacation_config": {},
        }

        call_count = [0]
        new_run_id = str(uuid4())

        def mock_execute():
            call_count[0] += 1
            if call_count[0] == 1:
                return MagicMock(data=[])
            elif call_count[0] == 2:
                return MagicMock(data=[pay_group])
            elif call_count[0] == 3:
                return MagicMock(data=[employee])
            elif call_count[0] == 4:
                return MagicMock(data=[make_payroll_run(
                    run_id=new_run_id,
                    period_start="2025-01-01",
                    period_end="2025-01-15",
                )])
            return MagicMock(data=[])

        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_table.is_.return_value = mock_table
        mock_table.insert.return_value = mock_table
        mock_table.update.return_value = mock_table
        mock_table.execute.side_effect = mock_execute
        mock_supabase.table = MagicMock(return_value=mock_table)

        mock_create_records_func.return_value = ([], [])
        mock_get_run_func.return_value = None

        result = await run_operations.create_or_get_run_by_period_end("2025-01-15")

        # Verify insert was called with correct period_start
        insert_call = mock_table.insert.call_args[0][0]
        # Semi-monthly first half: period_end day <= 15, so period_start = 1st of month
        assert insert_call["period_start"] == "2025-01-01"

    @pytest.mark.asyncio
    async def test_period_start_calculation_semi_monthly_second_half(
        self,
        run_operations: PayrollRunOperations,
        mock_supabase: MagicMock,
        mock_create_records_func: AsyncMock,
        mock_get_run_func: AsyncMock,
    ):
        """Should calculate correct period_start for semi_monthly second half (day > 15)."""
        pay_group = make_pay_group(pay_frequency="semi_monthly")
        employee = {
            "id": str(uuid4()),
            "first_name": "John",
            "last_name": "Doe",
            "province_of_employment": "SK",
            "pay_group_id": pay_group["id"],
            "annual_salary": 60000.0,
            "hourly_rate": None,
            "federal_additional_claims": 0,
            "provincial_additional_claims": 0,
            "is_cpp_exempt": False,
            "is_ei_exempt": False,
            "cpp2_exempt": False,
            "vacation_config": {},
        }

        call_count = [0]
        new_run_id = str(uuid4())

        def mock_execute():
            call_count[0] += 1
            if call_count[0] == 1:
                return MagicMock(data=[])
            elif call_count[0] == 2:
                return MagicMock(data=[pay_group])
            elif call_count[0] == 3:
                return MagicMock(data=[employee])
            elif call_count[0] == 4:
                return MagicMock(data=[make_payroll_run(
                    run_id=new_run_id,
                    period_start="2025-01-16",
                    period_end="2025-01-31",
                )])
            return MagicMock(data=[])

        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_table.is_.return_value = mock_table
        mock_table.insert.return_value = mock_table
        mock_table.update.return_value = mock_table
        mock_table.execute.side_effect = mock_execute
        mock_supabase.table = MagicMock(return_value=mock_table)

        mock_create_records_func.return_value = ([], [])
        mock_get_run_func.return_value = None

        result = await run_operations.create_or_get_run_by_period_end("2025-01-31")

        # Verify insert was called with correct period_start
        insert_call = mock_table.insert.call_args[0][0]
        # Semi-monthly second half: period_end day > 15, so period_start = 16th
        assert insert_call["period_start"] == "2025-01-16"

    @pytest.mark.asyncio
    async def test_create_run_insert_fails(
        self,
        run_operations: PayrollRunOperations,
        mock_supabase: MagicMock,
    ):
        """Should raise ValueError when run insert fails."""
        pay_group = make_pay_group()
        employee = {
            "id": str(uuid4()),
            "first_name": "John",
            "last_name": "Doe",
            "province_of_employment": "SK",
            "pay_group_id": pay_group["id"],
            "annual_salary": 60000.0,
            "hourly_rate": None,
            "federal_additional_claims": 0,
            "provincial_additional_claims": 0,
            "is_cpp_exempt": False,
            "is_ei_exempt": False,
            "cpp2_exempt": False,
            "vacation_config": {},
        }

        call_count = [0]

        def mock_execute():
            call_count[0] += 1
            if call_count[0] == 1:
                # First call: no existing run
                return MagicMock(data=[])
            elif call_count[0] == 2:
                # Second call: pay groups found
                return MagicMock(data=[pay_group])
            elif call_count[0] == 3:
                # Third call: employees found
                return MagicMock(data=[employee])
            elif call_count[0] == 4:
                # Fourth call: run insert FAILS
                return MagicMock(data=[])
            return MagicMock(data=[])

        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_table.is_.return_value = mock_table
        mock_table.insert.return_value = mock_table
        mock_table.execute.side_effect = mock_execute
        mock_supabase.table = MagicMock(return_value=mock_table)

        with pytest.raises(ValueError, match="Failed to create payroll run"):
            await run_operations.create_or_get_run_by_period_end("2025-01-17")
