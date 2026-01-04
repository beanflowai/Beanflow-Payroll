"""
Tests for EmployeeManagement class.
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

from app.services.payroll_run.employee_management import EmployeeManagement


@pytest.fixture
def mock_supabase():
    """Create a mock Supabase client."""
    return MagicMock()


@pytest.fixture
def mock_ytd_calculator():
    """Create a mock YTD calculator."""
    calculator = MagicMock()
    calculator.get_prior_ytd_for_employees.return_value = {}
    return calculator


@pytest.fixture
def mock_get_run():
    """Create a mock get_run function."""
    return AsyncMock()


@pytest.fixture
def employee_mgmt(mock_supabase, mock_ytd_calculator, mock_get_run):
    """Create an EmployeeManagement instance."""
    return EmployeeManagement(
        supabase=mock_supabase,
        user_id="user-123",
        company_id="company-456",
        ytd_calculator=mock_ytd_calculator,
        get_run_func=mock_get_run,
    )


class TestSyncEmployees:
    """Tests for sync_employees method."""

    @pytest.mark.asyncio
    async def test_raises_when_run_not_found(self, employee_mgmt, mock_get_run):
        """Test that ValueError is raised when run is not found."""
        mock_get_run.return_value = None

        with pytest.raises(ValueError, match="Payroll run not found"):
            await employee_mgmt.sync_employees(UUID("12345678-1234-5678-1234-567812345678"))

    @pytest.mark.asyncio
    async def test_returns_empty_when_not_draft(self, employee_mgmt, mock_get_run):
        """Test that empty result is returned when run is not in draft status."""
        mock_get_run.return_value = {
            "id": "run-123",
            "status": "approved",
            "period_end": "2025-01-31",
            "pay_date": "2025-02-06",
        }

        result = await employee_mgmt.sync_employees(UUID("12345678-1234-5678-1234-567812345678"))

        assert result["added_count"] == 0
        assert result["added_employees"] == []

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_pay_groups(
        self, employee_mgmt, mock_get_run, mock_supabase
    ):
        """Test that empty result is returned when no pay groups match."""
        mock_get_run.return_value = {
            "id": "run-123",
            "status": "draft",
            "period_end": "2025-01-31",
            "pay_date": "2025-02-06",
        }

        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]
        )

        result = await employee_mgmt.sync_employees(UUID("12345678-1234-5678-1234-567812345678"))

        assert result["added_count"] == 0
        assert result["added_employees"] == []

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_missing_employees(
        self, employee_mgmt, mock_get_run, mock_supabase
    ):
        """Test that empty result is returned when all employees already in run."""
        mock_get_run.return_value = {
            "id": "run-123",
            "status": "draft",
            "period_end": "2025-01-31",
            "pay_date": "2025-02-06",
        }

        # Mock pay groups query
        pay_groups_mock = MagicMock()
        pay_groups_mock.data = [{"id": "pg-1", "name": "Salaried", "pay_frequency": "bi_weekly"}]

        # Mock employees query
        employees_mock = MagicMock()
        employees_mock.data = [{"id": "emp-1", "first_name": "John", "last_name": "Doe"}]

        # Mock existing records query
        records_mock = MagicMock()
        records_mock.data = [{"employee_id": "emp-1"}]  # Employee already in run

        # Configure mock to return different results for different tables
        def table_side_effect(table_name):
            mock_table = MagicMock()
            if table_name == "pay_groups":
                mock_table.select.return_value.eq.return_value.execute.return_value = pay_groups_mock
            elif table_name == "employees":
                mock_table.select.return_value.eq.return_value.eq.return_value.in_.return_value.is_.return_value.execute.return_value = employees_mock
            elif table_name == "payroll_records":
                mock_table.select.return_value.eq.return_value.execute.return_value = records_mock
            return mock_table

        mock_supabase.table.side_effect = table_side_effect

        result = await employee_mgmt.sync_employees(UUID("12345678-1234-5678-1234-567812345678"))

        assert result["added_count"] == 0
        assert result["added_employees"] == []


class TestAddEmployeeToRun:
    """Tests for add_employee_to_run method."""

    @pytest.mark.asyncio
    async def test_raises_when_run_not_found(self, employee_mgmt, mock_get_run):
        """Test that ValueError is raised when run is not found."""
        mock_get_run.return_value = None

        with pytest.raises(ValueError, match="Payroll run not found"):
            await employee_mgmt.add_employee_to_run(
                UUID("12345678-1234-5678-1234-567812345678"), "emp-1"
            )

    @pytest.mark.asyncio
    async def test_raises_when_not_draft(self, employee_mgmt, mock_get_run):
        """Test that ValueError is raised when run is not in draft status."""
        mock_get_run.return_value = {
            "id": "run-123",
            "status": "approved",
        }

        with pytest.raises(ValueError, match="Cannot add employee"):
            await employee_mgmt.add_employee_to_run(
                UUID("12345678-1234-5678-1234-567812345678"), "emp-1"
            )

    @pytest.mark.asyncio
    async def test_raises_when_employee_already_in_run(
        self, employee_mgmt, mock_get_run, mock_supabase
    ):
        """Test that ValueError is raised when employee already in run."""
        mock_get_run.return_value = {
            "id": "run-123",
            "status": "draft",
            "pay_date": "2025-02-06",
        }

        # Mock existing record check
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": "record-1"}]
        )

        with pytest.raises(ValueError, match="Employee already exists"):
            await employee_mgmt.add_employee_to_run(
                UUID("12345678-1234-5678-1234-567812345678"), "emp-1"
            )

    @pytest.mark.asyncio
    async def test_raises_when_employee_not_found(
        self, employee_mgmt, mock_get_run, mock_supabase
    ):
        """Test that ValueError is raised when employee not found."""
        mock_get_run.return_value = {
            "id": "run-123",
            "status": "draft",
            "pay_date": "2025-02-06",
        }

        # Mock existing record check (no records)
        existing_record_mock = MagicMock()
        existing_record_mock.data = []

        # Mock employee query (not found)
        employee_mock = MagicMock()
        employee_mock.data = None

        def table_side_effect(table_name):
            mock_table = MagicMock()
            if table_name == "payroll_records":
                mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = existing_record_mock
            elif table_name == "employees":
                mock_table.select.return_value.eq.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value = employee_mock
            return mock_table

        mock_supabase.table.side_effect = table_side_effect

        with pytest.raises(ValueError, match="Employee not found"):
            await employee_mgmt.add_employee_to_run(
                UUID("12345678-1234-5678-1234-567812345678"), "emp-1"
            )


class TestRemoveEmployeeFromRun:
    """Tests for remove_employee_from_run method."""

    @pytest.mark.asyncio
    async def test_raises_when_run_not_found(self, employee_mgmt, mock_get_run):
        """Test that ValueError is raised when run is not found."""
        mock_get_run.return_value = None

        with pytest.raises(ValueError, match="Payroll run not found"):
            await employee_mgmt.remove_employee_from_run(
                UUID("12345678-1234-5678-1234-567812345678"), "emp-1"
            )

    @pytest.mark.asyncio
    async def test_raises_when_not_draft(self, employee_mgmt, mock_get_run):
        """Test that ValueError is raised when run is not in draft status."""
        mock_get_run.return_value = {
            "id": "run-123",
            "status": "paid",
        }

        with pytest.raises(ValueError, match="Cannot remove employee"):
            await employee_mgmt.remove_employee_from_run(
                UUID("12345678-1234-5678-1234-567812345678"), "emp-1"
            )

    @pytest.mark.asyncio
    async def test_raises_when_employee_not_in_run(
        self, employee_mgmt, mock_get_run, mock_supabase
    ):
        """Test that ValueError is raised when employee not in run."""
        mock_get_run.return_value = {
            "id": "run-123",
            "status": "draft",
        }

        # Mock record query (not found)
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]
        )

        with pytest.raises(ValueError, match="Employee not found in this payroll run"):
            await employee_mgmt.remove_employee_from_run(
                UUID("12345678-1234-5678-1234-567812345678"), "emp-1"
            )

    @pytest.mark.asyncio
    async def test_removes_employee_successfully(
        self, employee_mgmt, mock_get_run, mock_supabase
    ):
        """Test that employee is removed successfully."""
        mock_get_run.return_value = {
            "id": "run-123",
            "status": "draft",
            "total_employees": 5,
            "total_gross": 10000.0,
            "total_cpp_employee": 500.0,
            "total_cpp_employer": 500.0,
            "total_ei_employee": 200.0,
            "total_ei_employer": 280.0,
            "total_federal_tax": 1500.0,
            "total_provincial_tax": 800.0,
            "total_net_pay": 7000.0,
            "total_employer_cost": 780.0,
        }

        # Mock record query
        record_mock = MagicMock()
        record_mock.data = [
            {
                "id": "record-1",
                "gross_regular": 2000.0,
                "gross_overtime": 0.0,
                "cpp_employee": 100.0,
                "cpp_additional": 0.0,
                "cpp_employer": 100.0,
                "ei_employee": 40.0,
                "ei_employer": 56.0,
                "federal_tax": 300.0,
                "provincial_tax": 160.0,
            }
        ]

        call_count = 0

        def table_side_effect(table_name):
            nonlocal call_count
            mock_table = MagicMock()
            if table_name == "payroll_records":
                call_count += 1
                if call_count == 1:
                    # First call is select
                    mock_table.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = record_mock
                else:
                    # Second call is delete
                    mock_table.delete.return_value.eq.return_value.execute.return_value = MagicMock()
            elif table_name == "employees":
                mock_table.update.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock()
            elif table_name == "payroll_runs":
                mock_table.update.return_value.eq.return_value.execute.return_value = MagicMock()
            return mock_table

        mock_supabase.table.side_effect = table_side_effect

        result = await employee_mgmt.remove_employee_from_run(
            UUID("12345678-1234-5678-1234-567812345678"), "emp-1"
        )

        assert result["removed"] is True
        assert result["employee_id"] == "emp-1"


class TestCreateRecordsForEmployees:
    """Tests for create_records_for_employees method."""

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_employees(self, employee_mgmt):
        """Test that empty result is returned when no employees provided."""
        result = await employee_mgmt.create_records_for_employees(
            UUID("12345678-1234-5678-1234-567812345678"),
            employees=[],
            pay_group_map={},
        )

        assert result == ([], [])

    @pytest.mark.asyncio
    async def test_creates_records_for_salaried_employee(
        self, employee_mgmt, mock_supabase, mock_ytd_calculator
    ):
        """Test creating payroll records for a salaried employee."""
        run_id = UUID("12345678-1234-5678-1234-567812345678")

        employees = [
            {
                "id": "emp-1",
                "first_name": "John",
                "last_name": "Doe",
                "province_of_employment": "ON",
                "pay_group_id": "pg-1",
                "annual_salary": 78000,
                "hourly_rate": None,
                "federal_additional_claims": 0,
                "provincial_additional_claims": 0,
                "is_cpp_exempt": False,
                "is_ei_exempt": False,
                "cpp2_exempt": False,
                "vacation_config": {"payout_method": "accrual", "vacation_rate": 0.04},
            }
        ]

        pay_group_map = {
            "pg-1": {
                "id": "pg-1",
                "name": "Salaried",
                "pay_frequency": "bi_weekly",
                "employment_type": "full_time",
                "group_benefits": None,
            }
        }

        # Mock YTD calculator
        mock_ytd_calculator.get_prior_ytd_for_employees.return_value = {}

        # Mock insert
        mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock()

        # Patch PayrollEngine to return a mock result
        with patch("app.services.payroll_run.employee_management.PayrollEngine") as MockEngine:
            mock_engine = MagicMock()
            mock_result = MagicMock()
            mock_result.employee_id = "emp-1"
            mock_result.gross_regular = Decimal("3000")
            mock_result.gross_overtime = Decimal("0")
            mock_result.total_gross = Decimal("3000")
            mock_result.holiday_pay = Decimal("0")
            mock_result.holiday_premium_pay = Decimal("0")
            mock_result.vacation_pay = Decimal("0")
            mock_result.other_earnings = Decimal("0")
            mock_result.cpp_base = Decimal("150")
            mock_result.cpp_additional = Decimal("0")
            mock_result.cpp_total = Decimal("150")
            mock_result.cpp_employer = Decimal("150")
            mock_result.ei_employee = Decimal("50")
            mock_result.ei_employer = Decimal("70")
            mock_result.federal_tax = Decimal("400")
            mock_result.provincial_tax = Decimal("200")
            mock_result.rrsp = Decimal("0")
            mock_result.union_dues = Decimal("0")
            mock_result.garnishments = Decimal("0")
            mock_result.other_deductions = Decimal("0")
            mock_result.net_pay = Decimal("2200")
            mock_result.new_ytd_gross = Decimal("3000")
            mock_result.new_ytd_cpp = Decimal("150")
            mock_result.new_ytd_ei = Decimal("50")
            mock_result.new_ytd_federal_tax = Decimal("400")
            mock_result.new_ytd_provincial_tax = Decimal("200")

            mock_engine.calculate_batch.return_value = [mock_result]
            MockEngine.return_value = mock_engine

            added, results = await employee_mgmt.create_records_for_employees(
                run_id,
                employees=employees,
                pay_group_map=pay_group_map,
                tax_year=2025,
            )

        assert len(added) == 1
        assert added[0]["employee_id"] == "emp-1"
        assert added[0]["employee_name"] == "John Doe"
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_handles_hourly_employee(
        self, employee_mgmt, mock_supabase, mock_ytd_calculator
    ):
        """Test creating payroll records for an hourly employee."""
        run_id = UUID("12345678-1234-5678-1234-567812345678")

        employees = [
            {
                "id": "emp-2",
                "first_name": "Jane",
                "last_name": "Smith",
                "province_of_employment": "BC",
                "pay_group_id": "pg-2",
                "annual_salary": None,
                "hourly_rate": 25,
                "federal_additional_claims": 0,
                "provincial_additional_claims": 0,
                "is_cpp_exempt": False,
                "is_ei_exempt": False,
                "cpp2_exempt": False,
                "vacation_config": None,
            }
        ]

        pay_group_map = {
            "pg-2": {
                "id": "pg-2",
                "name": "Hourly",
                "pay_frequency": "bi_weekly",
                "employment_type": "full_time",
                "group_benefits": None,
            }
        }

        mock_ytd_calculator.get_prior_ytd_for_employees.return_value = {}
        mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock()

        with patch("app.services.payroll_run.employee_management.PayrollEngine") as MockEngine:
            mock_engine = MagicMock()
            mock_result = MagicMock()
            mock_result.employee_id = "emp-2"
            mock_result.gross_regular = Decimal("2000")
            mock_result.gross_overtime = Decimal("0")
            mock_result.total_gross = Decimal("2000")
            mock_result.holiday_pay = Decimal("0")
            mock_result.holiday_premium_pay = Decimal("0")
            mock_result.vacation_pay = Decimal("0")
            mock_result.other_earnings = Decimal("0")
            mock_result.cpp_base = Decimal("100")
            mock_result.cpp_additional = Decimal("0")
            mock_result.cpp_total = Decimal("100")
            mock_result.cpp_employer = Decimal("100")
            mock_result.ei_employee = Decimal("33")
            mock_result.ei_employer = Decimal("46")
            mock_result.federal_tax = Decimal("250")
            mock_result.provincial_tax = Decimal("125")
            mock_result.rrsp = Decimal("0")
            mock_result.union_dues = Decimal("0")
            mock_result.garnishments = Decimal("0")
            mock_result.other_deductions = Decimal("0")
            mock_result.net_pay = Decimal("1492")
            mock_result.new_ytd_gross = Decimal("2000")
            mock_result.new_ytd_cpp = Decimal("100")
            mock_result.new_ytd_ei = Decimal("33")
            mock_result.new_ytd_federal_tax = Decimal("250")
            mock_result.new_ytd_provincial_tax = Decimal("125")

            mock_engine.calculate_batch.return_value = [mock_result]
            MockEngine.return_value = mock_engine

            added, results = await employee_mgmt.create_records_for_employees(
                run_id,
                employees=employees,
                pay_group_map=pay_group_map,
                tax_year=2025,
            )

        assert len(added) == 1
        assert added[0]["employee_name"] == "Jane Smith"

    @pytest.mark.asyncio
    async def test_handles_pay_as_you_go_vacation(
        self, employee_mgmt, mock_supabase, mock_ytd_calculator
    ):
        """Test that pay_as_you_go vacation is added to gross."""
        run_id = UUID("12345678-1234-5678-1234-567812345678")

        employees = [
            {
                "id": "emp-3",
                "first_name": "Bob",
                "last_name": "Wilson",
                "province_of_employment": "SK",
                "pay_group_id": "pg-1",
                "annual_salary": 52000,
                "hourly_rate": None,
                "federal_additional_claims": 0,
                "provincial_additional_claims": 0,
                "is_cpp_exempt": False,
                "is_ei_exempt": False,
                "cpp2_exempt": False,
                "vacation_config": {"payout_method": "pay_as_you_go", "vacation_rate": 0.06},
            }
        ]

        pay_group_map = {
            "pg-1": {
                "id": "pg-1",
                "name": "Salaried",
                "pay_frequency": "bi_weekly",
            }
        }

        mock_ytd_calculator.get_prior_ytd_for_employees.return_value = {}
        mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock()

        with patch("app.services.payroll_run.employee_management.PayrollEngine") as MockEngine:
            mock_engine = MagicMock()
            mock_result = MagicMock()
            mock_result.employee_id = "emp-3"
            mock_result.gross_regular = Decimal("2000")
            mock_result.gross_overtime = Decimal("0")
            mock_result.total_gross = Decimal("2120")  # Includes vacation pay
            mock_result.holiday_pay = Decimal("0")
            mock_result.holiday_premium_pay = Decimal("0")
            mock_result.vacation_pay = Decimal("120")  # 2000 * 0.06
            mock_result.other_earnings = Decimal("0")
            mock_result.cpp_base = Decimal("106")
            mock_result.cpp_additional = Decimal("0")
            mock_result.cpp_total = Decimal("106")
            mock_result.cpp_employer = Decimal("106")
            mock_result.ei_employee = Decimal("35")
            mock_result.ei_employer = Decimal("49")
            mock_result.federal_tax = Decimal("300")
            mock_result.provincial_tax = Decimal("150")
            mock_result.rrsp = Decimal("0")
            mock_result.union_dues = Decimal("0")
            mock_result.garnishments = Decimal("0")
            mock_result.other_deductions = Decimal("0")
            mock_result.net_pay = Decimal("1529")
            mock_result.new_ytd_gross = Decimal("2120")
            mock_result.new_ytd_cpp = Decimal("106")
            mock_result.new_ytd_ei = Decimal("35")
            mock_result.new_ytd_federal_tax = Decimal("300")
            mock_result.new_ytd_provincial_tax = Decimal("150")

            mock_engine.calculate_batch.return_value = [mock_result]
            MockEngine.return_value = mock_engine

            # Capture the input to calculate_batch
            added, results = await employee_mgmt.create_records_for_employees(
                run_id,
                employees=employees,
                pay_group_map=pay_group_map,
                tax_year=2025,
            )

            # Verify calculation was called
            mock_engine.calculate_batch.assert_called_once()
            calc_inputs = mock_engine.calculate_batch.call_args[0][0]
            assert len(calc_inputs) == 1
            # With pay_as_you_go, vacation_pay should be included
            assert calc_inputs[0].vacation_pay == Decimal("120")

    @pytest.mark.asyncio
    async def test_uses_prior_ytd_data(
        self, employee_mgmt, mock_supabase, mock_ytd_calculator
    ):
        """Test that prior YTD data is passed to calculations."""
        run_id = UUID("12345678-1234-5678-1234-567812345678")

        employees = [
            {
                "id": "emp-4",
                "first_name": "Alice",
                "last_name": "Brown",
                "province_of_employment": "AB",
                "pay_group_id": "pg-1",
                "annual_salary": 60000,
                "hourly_rate": None,
                "federal_additional_claims": 1000,
                "provincial_additional_claims": 500,
                "is_cpp_exempt": False,
                "is_ei_exempt": False,
                "cpp2_exempt": False,
                "vacation_config": None,
            }
        ]

        pay_group_map = {
            "pg-1": {"pay_frequency": "bi_weekly"}
        }

        # Set up prior YTD data
        mock_ytd_calculator.get_prior_ytd_for_employees.return_value = {
            "emp-4": {
                "ytd_gross": Decimal("30000"),
                "ytd_cpp": Decimal("1500"),
                "ytd_cpp_additional": Decimal("0"),
                "ytd_ei": Decimal("500"),
                "ytd_federal_tax": Decimal("4000"),
                "ytd_provincial_tax": Decimal("2000"),
                "ytd_net_pay": Decimal("22000"),
            }
        }

        mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock()

        with patch("app.services.payroll_run.employee_management.PayrollEngine") as MockEngine:
            mock_engine = MagicMock()
            mock_result = MagicMock()
            mock_result.employee_id = "emp-4"
            mock_result.gross_regular = Decimal("2307.69")
            mock_result.gross_overtime = Decimal("0")
            mock_result.total_gross = Decimal("2307.69")
            mock_result.holiday_pay = Decimal("0")
            mock_result.holiday_premium_pay = Decimal("0")
            mock_result.vacation_pay = Decimal("0")
            mock_result.other_earnings = Decimal("0")
            mock_result.cpp_base = Decimal("115")
            mock_result.cpp_additional = Decimal("0")
            mock_result.cpp_total = Decimal("115")
            mock_result.cpp_employer = Decimal("115")
            mock_result.ei_employee = Decimal("38")
            mock_result.ei_employer = Decimal("53")
            mock_result.federal_tax = Decimal("280")
            mock_result.provincial_tax = Decimal("140")
            mock_result.rrsp = Decimal("0")
            mock_result.union_dues = Decimal("0")
            mock_result.garnishments = Decimal("0")
            mock_result.other_deductions = Decimal("0")
            mock_result.net_pay = Decimal("1734.69")
            mock_result.new_ytd_gross = Decimal("32307.69")
            mock_result.new_ytd_cpp = Decimal("1615")
            mock_result.new_ytd_ei = Decimal("538")
            mock_result.new_ytd_federal_tax = Decimal("4280")
            mock_result.new_ytd_provincial_tax = Decimal("2140")

            mock_engine.calculate_batch.return_value = [mock_result]
            MockEngine.return_value = mock_engine

            added, results = await employee_mgmt.create_records_for_employees(
                run_id,
                employees=employees,
                pay_group_map=pay_group_map,
                tax_year=2025,
            )

            # Verify YTD calculator was called
            mock_ytd_calculator.get_prior_ytd_for_employees.assert_called_once()

            # Verify calculation inputs include YTD values
            calc_inputs = mock_engine.calculate_batch.call_args[0][0]
            assert len(calc_inputs) == 1
            assert calc_inputs[0].ytd_gross == Decimal("30000")
            assert calc_inputs[0].ytd_cpp_base == Decimal("1500")
