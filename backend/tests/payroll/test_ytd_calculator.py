"""Tests for YtdCalculator - Initial YTD merge logic for transferred employees"""

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.services.payroll_run.ytd_calculator import YtdCalculator


class TestYtdCalculatorInitialYtd:
    """Test YTD calculation including initial_ytd_* values from transferred employees"""

    @pytest.fixture
    def mock_supabase(self):
        """Create a mock Supabase client"""
        return MagicMock()

    @pytest.fixture
    def calculator(self, mock_supabase):
        """Create YtdCalculator instance with mock Supabase"""
        return YtdCalculator(
            supabase=mock_supabase,
            user_id="test-user",
            company_id="test-company"
        )

    def test_get_initial_ytd_for_employees_empty_list(self, calculator):
        """Test _get_initial_ytd_for_employees with empty employee list"""
        result = calculator._get_initial_ytd_for_employees([])
        assert result == {}

    def test_get_initial_ytd_for_employees_with_values(self, calculator, mock_supabase):
        """Test _get_initial_ytd_for_employees returns employee initial YTD values"""
        # Setup mock response
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.in_.return_value.execute.return_value = MagicMock(
            data=[
                {
                    "id": "emp-1",
                    "initial_ytd_cpp": "1500.00",
                    "initial_ytd_cpp2": "200.00",
                    "initial_ytd_ei": "500.00",
                    "initial_ytd_year": 2025
                },
                {
                    "id": "emp-2",
                    "initial_ytd_cpp": "0",
                    "initial_ytd_cpp2": "0",
                    "initial_ytd_ei": "0",
                    "initial_ytd_year": 2025
                }
            ]
        )

        result = calculator._get_initial_ytd_for_employees(["emp-1", "emp-2"], year=2025)

        assert result["emp-1"]["initial_ytd_cpp"] == Decimal("1500.00")
        assert result["emp-1"]["initial_ytd_cpp2"] == Decimal("200.00")
        assert result["emp-1"]["initial_ytd_ei"] == Decimal("500.00")

        assert result["emp-2"]["initial_ytd_cpp"] == Decimal("0")
        assert result["emp-2"]["initial_ytd_cpp2"] == Decimal("0")
        assert result["emp-2"]["initial_ytd_ei"] == Decimal("0")

    def test_get_initial_ytd_for_employees_handles_null_values(self, calculator, mock_supabase):
        """Test _get_initial_ytd_for_employees handles NULL values from database"""
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.in_.return_value.execute.return_value = MagicMock(
            data=[
                {
                    "id": "emp-1",
                    "initial_ytd_cpp": None,
                    "initial_ytd_cpp2": None,
                    "initial_ytd_ei": None,
                    "initial_ytd_year": 2025
                }
            ]
        )

        result = calculator._get_initial_ytd_for_employees(["emp-1"], year=2025)

        # NULL values should be converted to Decimal("0")
        assert result["emp-1"]["initial_ytd_cpp"] == Decimal("0")
        assert result["emp-1"]["initial_ytd_cpp2"] == Decimal("0")
        assert result["emp-1"]["initial_ytd_ei"] == Decimal("0")

    def test_get_prior_ytd_includes_initial_values(self, calculator, mock_supabase):
        """Test get_prior_ytd_for_employees includes initial YTD from transferred employees"""
        # Setup mock for employees table (initial YTD)
        def mock_table(table_name):
            if table_name == "employees":
                mock_result = MagicMock()
                mock_result.select.return_value.eq.return_value.eq.return_value.in_.return_value.execute.return_value = MagicMock(
                    data=[
                        {
                            "id": "emp-1",
                            "initial_ytd_cpp": "1000.00",
                            "initial_ytd_cpp2": "100.00",
                            "initial_ytd_ei": "300.00",
                            "initial_ytd_year": 2025
                        }
                    ]
                )
                return mock_result
            elif table_name == "payroll_records":
                # No prior payroll records
                mock_result = MagicMock()
                mock_result.select.return_value.eq.return_value.eq.return_value.in_.return_value.in_.return_value.gte.return_value.lte.return_value.neq.return_value.execute.return_value = MagicMock(
                    data=[]
                )
                return mock_result
            return MagicMock()

        mock_supabase.table.side_effect = mock_table

        result = calculator.get_prior_ytd_for_employees(
            employee_ids=["emp-1"],
            current_run_id="run-123",
            year=2025
        )

        # Initial YTD values should be included
        assert result["emp-1"]["ytd_cpp"] == Decimal("1000.00")
        assert result["emp-1"]["ytd_cpp_additional"] == Decimal("100.00")
        assert result["emp-1"]["ytd_ei"] == Decimal("300.00")
        # Gross and tax should be 0 (no payroll records)
        assert result["emp-1"]["ytd_gross"] == Decimal("0")
        assert result["emp-1"]["ytd_federal_tax"] == Decimal("0")
        assert result["emp-1"]["ytd_provincial_tax"] == Decimal("0")

    def test_get_prior_ytd_merges_initial_and_records(self, calculator, mock_supabase):
        """Test get_prior_ytd_for_employees merges initial YTD with payroll records"""
        # Setup mock for employees table (initial YTD)
        def mock_table(table_name):
            if table_name == "employees":
                mock_result = MagicMock()
                mock_result.select.return_value.eq.return_value.eq.return_value.in_.return_value.execute.return_value = MagicMock(
                    data=[
                        {
                            "id": "emp-1",
                            "initial_ytd_cpp": "1000.00",
                            "initial_ytd_cpp2": "50.00",
                            "initial_ytd_ei": "300.00",
                            "initial_ytd_year": 2025
                        }
                    ]
                )
                return mock_result
            elif table_name == "payroll_records":
                # One prior payroll record
                mock_result = MagicMock()
                mock_result.select.return_value.eq.return_value.eq.return_value.in_.return_value.in_.return_value.gte.return_value.lte.return_value.neq.return_value.execute.return_value = MagicMock(
                    data=[
                        {
                            "employee_id": "emp-1",
                            "gross_regular": "2000.00",
                            "gross_overtime": "0",
                            "holiday_pay": "0",
                            "holiday_premium_pay": "0",
                            "vacation_pay_paid": "0",
                            "other_earnings": "0",
                            "cpp_employee": "115.00",
                            "cpp_additional": "10.00",
                            "ei_employee": "32.80",
                            "federal_tax": "200.00",
                            "provincial_tax": "100.00",
                            "net_pay": "1542.20",
                            "payroll_runs": {
                                "id": "run-prev",
                                "pay_date": "2025-06-15",
                                "status": "paid"
                            }
                        }
                    ]
                )
                return mock_result
            return MagicMock()

        mock_supabase.table.side_effect = mock_table

        result = calculator.get_prior_ytd_for_employees(
            employee_ids=["emp-1"],
            current_run_id="run-123",
            year=2025
        )

        # Initial YTD + payroll record values should be merged
        # CPP: 1000 (initial) + 115 (record) = 1115
        assert result["emp-1"]["ytd_cpp"] == Decimal("1115.00")
        # CPP2: 50 (initial) + 10 (record) = 60
        assert result["emp-1"]["ytd_cpp_additional"] == Decimal("60.00")
        # EI: 300 (initial) + 32.80 (record) = 332.80
        assert result["emp-1"]["ytd_ei"] == Decimal("332.80")
        # Gross: only from record (no initial)
        assert result["emp-1"]["ytd_gross"] == Decimal("2000.00")
        # Tax: only from record (no initial)
        assert result["emp-1"]["ytd_federal_tax"] == Decimal("200.00")
        assert result["emp-1"]["ytd_provincial_tax"] == Decimal("100.00")

    def test_get_prior_ytd_empty_employee_list(self, calculator):
        """Test get_prior_ytd_for_employees with empty employee list"""
        result = calculator.get_prior_ytd_for_employees(
            employee_ids=[],
            current_run_id="run-123",
            year=2025
        )
        assert result == {}

    def test_get_prior_ytd_with_multiple_payroll_records(self, calculator, mock_supabase):
        """Test get_prior_ytd_for_employees accumulates multiple payroll records correctly"""
        def mock_table(table_name):
            if table_name == "employees":
                mock_result = MagicMock()
                mock_result.select.return_value.eq.return_value.eq.return_value.in_.return_value.execute.return_value = MagicMock(
                    data=[
                        {
                            "id": "emp-1",
                            "initial_ytd_cpp": "500.00",
                            "initial_ytd_cpp2": "0",
                            "initial_ytd_ei": "200.00",
                            "initial_ytd_year": 2025
                        }
                    ]
                )
                return mock_result
            elif table_name == "payroll_records":
                # Multiple prior payroll records
                mock_result = MagicMock()
                mock_result.select.return_value.eq.return_value.eq.return_value.in_.return_value.in_.return_value.gte.return_value.lte.return_value.neq.return_value.execute.return_value = MagicMock(
                    data=[
                        {
                            "employee_id": "emp-1",
                            "gross_regular": "3000.00",
                            "gross_overtime": "0",
                            "holiday_pay": "0",
                            "holiday_premium_pay": "0",
                            "vacation_pay_paid": "0",
                            "other_earnings": "0",
                            "cpp_employee": "172.50",
                            "cpp_additional": "0",
                            "ei_employee": "49.20",
                            "federal_tax": "300.00",
                            "provincial_tax": "150.00",
                            "net_pay": "2328.30",
                            "payroll_runs": {
                                "id": "run-1",
                                "pay_date": "2025-01-15",
                                "status": "paid"
                            }
                        },
                        {
                            "employee_id": "emp-1",
                            "gross_regular": "3000.00",
                            "gross_overtime": "500.00",
                            "holiday_pay": "0",
                            "holiday_premium_pay": "0",
                            "vacation_pay_paid": "0",
                            "other_earnings": "0",
                            "cpp_employee": "201.25",
                            "cpp_additional": "0",
                            "ei_employee": "57.40",
                            "federal_tax": "350.00",
                            "provincial_tax": "175.00",
                            "net_pay": "2716.35",
                            "payroll_runs": {
                                "id": "run-2",
                                "pay_date": "2025-01-31",
                                "status": "paid"
                            }
                        }
                    ]
                )
                return mock_result
            return MagicMock()

        mock_supabase.table.side_effect = mock_table

        result = calculator.get_prior_ytd_for_employees(
            employee_ids=["emp-1"],
            current_run_id="run-123",
            year=2025
        )

        # Initial + record1 + record2
        # CPP: 500 + 172.50 + 201.25 = 873.75
        assert result["emp-1"]["ytd_cpp"] == Decimal("873.75")
        # EI: 200 + 49.20 + 57.40 = 306.60
        assert result["emp-1"]["ytd_ei"] == Decimal("306.60")
        # Gross: 3000 + 3500 = 6500
        assert result["emp-1"]["ytd_gross"] == Decimal("6500.00")
        # Federal tax: 300 + 350 = 650
        assert result["emp-1"]["ytd_federal_tax"] == Decimal("650.00")
        # Provincial tax: 150 + 175 = 325
        assert result["emp-1"]["ytd_provincial_tax"] == Decimal("325.00")

    def test_get_prior_ytd_initial_at_max_limit(self, calculator, mock_supabase):
        """Test get_prior_ytd_for_employees when initial YTD is at annual max"""
        # 2025 max values: CPP=4034.10, CPP2=396.00, EI=1077.48
        def mock_table(table_name):
            if table_name == "employees":
                mock_result = MagicMock()
                mock_result.select.return_value.eq.return_value.eq.return_value.in_.return_value.execute.return_value = MagicMock(
                    data=[
                        {
                            "id": "emp-1",
                            "initial_ytd_cpp": "4034.10",  # At max
                            "initial_ytd_cpp2": "396.00",  # At max
                            "initial_ytd_ei": "1077.48",   # At max
                            "initial_ytd_year": 2025
                        }
                    ]
                )
                return mock_result
            elif table_name == "payroll_records":
                mock_result = MagicMock()
                mock_result.select.return_value.eq.return_value.eq.return_value.in_.return_value.in_.return_value.gte.return_value.lte.return_value.neq.return_value.execute.return_value = MagicMock(
                    data=[]
                )
                return mock_result
            return MagicMock()

        mock_supabase.table.side_effect = mock_table

        result = calculator.get_prior_ytd_for_employees(
            employee_ids=["emp-1"],
            current_run_id="run-123",
            year=2025
        )

        # Should return exact max values
        assert result["emp-1"]["ytd_cpp"] == Decimal("4034.10")
        assert result["emp-1"]["ytd_cpp_additional"] == Decimal("396.00")
        assert result["emp-1"]["ytd_ei"] == Decimal("1077.48")

    def test_get_prior_ytd_multiple_employees_mixed_scenarios(self, calculator, mock_supabase):
        """Test get_prior_ytd_for_employees with multiple employees having different scenarios"""
        def mock_table(table_name):
            if table_name == "employees":
                mock_result = MagicMock()
                mock_result.select.return_value.eq.return_value.eq.return_value.in_.return_value.execute.return_value = MagicMock(
                    data=[
                        {
                            "id": "emp-new",
                            "initial_ytd_cpp": "0",
                            "initial_ytd_cpp2": "0",
                            "initial_ytd_ei": "0",
                            "initial_ytd_year": 2025
                        },
                        {
                            "id": "emp-transfer",
                            "initial_ytd_cpp": "2000.00",
                            "initial_ytd_cpp2": "100.00",
                            "initial_ytd_ei": "600.00",
                            "initial_ytd_year": 2025
                        },
                        {
                            "id": "emp-maxed",
                            "initial_ytd_cpp": "4034.10",
                            "initial_ytd_cpp2": "396.00",
                            "initial_ytd_ei": "1077.48",
                            "initial_ytd_year": 2025
                        }
                    ]
                )
                return mock_result
            elif table_name == "payroll_records":
                mock_result = MagicMock()
                mock_result.select.return_value.eq.return_value.eq.return_value.in_.return_value.in_.return_value.gte.return_value.lte.return_value.neq.return_value.execute.return_value = MagicMock(
                    data=[
                        {
                            "employee_id": "emp-new",
                            "gross_regular": "2000.00",
                            "gross_overtime": "0",
                            "holiday_pay": "0",
                            "holiday_premium_pay": "0",
                            "vacation_pay_paid": "0",
                            "other_earnings": "0",
                            "cpp_employee": "115.00",
                            "cpp_additional": "0",
                            "ei_employee": "32.80",
                            "federal_tax": "200.00",
                            "provincial_tax": "100.00",
                            "net_pay": "1552.20",
                            "payroll_runs": {"id": "run-1", "pay_date": "2025-06-15", "status": "paid"}
                        },
                        {
                            "employee_id": "emp-transfer",
                            "gross_regular": "3000.00",
                            "gross_overtime": "0",
                            "holiday_pay": "0",
                            "holiday_premium_pay": "0",
                            "vacation_pay_paid": "0",
                            "other_earnings": "0",
                            "cpp_employee": "172.50",
                            "cpp_additional": "20.00",
                            "ei_employee": "49.20",
                            "federal_tax": "300.00",
                            "provincial_tax": "150.00",
                            "net_pay": "2308.30",
                            "payroll_runs": {"id": "run-1", "pay_date": "2025-06-15", "status": "paid"}
                        }
                        # emp-maxed has no payroll records (already maxed from previous employer)
                    ]
                )
                return mock_result
            return MagicMock()

        mock_supabase.table.side_effect = mock_table

        result = calculator.get_prior_ytd_for_employees(
            employee_ids=["emp-new", "emp-transfer", "emp-maxed"],
            current_run_id="run-123",
            year=2025
        )

        # emp-new: 0 initial + payroll record
        assert result["emp-new"]["ytd_cpp"] == Decimal("115.00")
        assert result["emp-new"]["ytd_cpp_additional"] == Decimal("0")
        assert result["emp-new"]["ytd_ei"] == Decimal("32.80")
        assert result["emp-new"]["ytd_gross"] == Decimal("2000.00")

        # emp-transfer: 2000 initial + 172.50 record = 2172.50
        assert result["emp-transfer"]["ytd_cpp"] == Decimal("2172.50")
        assert result["emp-transfer"]["ytd_cpp_additional"] == Decimal("120.00")  # 100 + 20
        assert result["emp-transfer"]["ytd_ei"] == Decimal("649.20")  # 600 + 49.20
        assert result["emp-transfer"]["ytd_gross"] == Decimal("3000.00")

        # emp-maxed: only initial values, no payroll records
        assert result["emp-maxed"]["ytd_cpp"] == Decimal("4034.10")
        assert result["emp-maxed"]["ytd_cpp_additional"] == Decimal("396.00")
        assert result["emp-maxed"]["ytd_ei"] == Decimal("1077.48")
        assert result["emp-maxed"]["ytd_gross"] == Decimal("0")

    def test_get_initial_ytd_ignores_mismatched_year(self, calculator, mock_supabase):
        """Test that initial YTD values are ignored when year doesn't match"""
        # Setup mock response with 2024 data when requesting 2025
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.in_.return_value.execute.return_value = MagicMock(
            data=[
                {
                    "id": "emp-1",
                    "initial_ytd_cpp": "1500.00",
                    "initial_ytd_cpp2": "200.00",
                    "initial_ytd_ei": "500.00",
                    "initial_ytd_year": 2024  # Previous year data
                }
            ]
        )

        # Request 2025 data - should ignore 2024 initial values
        result = calculator._get_initial_ytd_for_employees(["emp-1"], year=2025)

        # Should return empty dict since year doesn't match
        assert "emp-1" not in result

    def test_get_initial_ytd_ignores_null_year(self, calculator, mock_supabase):
        """Test that initial YTD values are ignored when year is NULL"""
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.in_.return_value.execute.return_value = MagicMock(
            data=[
                {
                    "id": "emp-1",
                    "initial_ytd_cpp": "1500.00",
                    "initial_ytd_cpp2": "200.00",
                    "initial_ytd_ei": "500.00",
                    "initial_ytd_year": None  # NULL year
                }
            ]
        )

        result = calculator._get_initial_ytd_for_employees(["emp-1"], year=2025)

        # Should return empty dict since year is NULL
        assert "emp-1" not in result
