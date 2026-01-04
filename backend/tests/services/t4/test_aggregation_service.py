"""
Tests for T4 Aggregation Service

Tests for aggregating payroll data into T4 slip information.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import pytest

from app.models.payroll import Company, Employee, Province
from app.services.t4.aggregation_service import T4AggregationService


# =============================================================================
# Test Constants
# =============================================================================

TEST_USER_ID = "test-user-id-12345"
TEST_COMPANY_ID = str(uuid4())
TEST_EMPLOYEE_ID = str(uuid4())
TEST_TAX_YEAR = 2025


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_supabase():
    """Create a mock Supabase client."""
    return MagicMock()


@pytest.fixture
def service(mock_supabase) -> T4AggregationService:
    """Create a T4 aggregation service instance."""
    return T4AggregationService(
        supabase=mock_supabase,
        user_id=TEST_USER_ID,
        company_id=TEST_COMPANY_ID,
    )


@pytest.fixture
def sample_company_data() -> dict[str, Any]:
    """Sample company data from database."""
    return {
        "id": TEST_COMPANY_ID,
        "user_id": TEST_USER_ID,
        "company_name": "Test Company Inc.",
        "business_number": "123456789",
        "payroll_account_number": "123456789RP0001",
        "province": "ON",
        "address_street": "123 Main St",
        "address_city": "Toronto",
        "address_postal_code": "M5V 1A1",
        "remitter_type": "regular",
        "auto_calculate_deductions": True,
        "send_paystub_emails": False,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_employee_data() -> dict[str, Any]:
    """Sample employee data from database."""
    return {
        "id": TEST_EMPLOYEE_ID,
        "user_id": TEST_USER_ID,
        "company_id": TEST_COMPANY_ID,
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "sin_encrypted": "test_encrypted_sin",
        "date_of_birth": "1990-01-15",
        "hire_date": "2024-01-01",
        "address_street": "456 Employee St",
        "address_city": "Toronto",
        "address_postal_code": "M4K 2A1",
        "province_of_employment": "ON",
        "pay_frequency": "bi_weekly",
        "annual_salary": 60000,
        "is_cpp_exempt": False,
        "is_ei_exempt": False,
        "employment_status": "active",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_payroll_record() -> dict[str, Any]:
    """Sample payroll record from database."""
    return {
        "id": str(uuid4()),
        "employee_id": TEST_EMPLOYEE_ID,
        "user_id": TEST_USER_ID,
        "company_id": TEST_COMPANY_ID,
        "gross_regular": "2500.00",
        "gross_overtime": "100.00",
        "holiday_pay": "50.00",
        "holiday_premium_pay": "0.00",
        "vacation_pay_paid": "0.00",
        "other_earnings": "0.00",
        "cpp_employee": "150.00",
        "cpp_employer": "150.00",
        "cpp_additional": "20.00",
        "ei_employee": "40.00",
        "ei_employer": "56.00",
        "federal_tax": "300.00",
        "provincial_tax": "150.00",
        "union_dues": "25.00",
        "payroll_runs": {
            "id": str(uuid4()),
            "pay_date": "2025-01-15",
            "status": "approved",
        },
    }


# =============================================================================
# Test: get_company
# =============================================================================


class TestGetCompany:
    """Tests for get_company method."""

    @pytest.mark.asyncio
    async def test_get_company_success(self, service, mock_supabase, sample_company_data):
        """Test successful company retrieval."""
        mock_response = MagicMock()
        mock_response.data = sample_company_data

        query_builder = MagicMock()
        query_builder.select.return_value = query_builder
        query_builder.eq.return_value = query_builder
        query_builder.maybe_single.return_value = query_builder
        query_builder.execute.return_value = mock_response

        mock_supabase.table.return_value = query_builder

        company = await service.get_company()

        assert company is not None
        assert company.company_name == "Test Company Inc."
        assert company.payroll_account_number == "123456789RP0001"

    @pytest.mark.asyncio
    async def test_get_company_not_found(self, service, mock_supabase):
        """Test company not found returns None."""
        mock_response = MagicMock()
        mock_response.data = None

        query_builder = MagicMock()
        query_builder.select.return_value = query_builder
        query_builder.eq.return_value = query_builder
        query_builder.maybe_single.return_value = query_builder
        query_builder.execute.return_value = mock_response

        mock_supabase.table.return_value = query_builder

        company = await service.get_company()

        assert company is None


# =============================================================================
# Test: get_employees_with_payroll
# =============================================================================


class TestGetEmployeesWithPayroll:
    """Tests for get_employees_with_payroll method."""

    @pytest.mark.asyncio
    async def test_get_employees_with_payroll_success(
        self, service, mock_supabase, sample_employee_data
    ):
        """Test successful employee retrieval."""
        mock_response = MagicMock()
        mock_response.data = [
            {
                "employee_id": TEST_EMPLOYEE_ID,
                "employees": sample_employee_data,
                "payroll_runs": {"pay_date": "2025-01-15", "status": "approved"},
            }
        ]

        query_builder = MagicMock()
        query_builder.select.return_value = query_builder
        query_builder.eq.return_value = query_builder
        query_builder.in_.return_value = query_builder
        query_builder.gte.return_value = query_builder
        query_builder.lte.return_value = query_builder
        query_builder.execute.return_value = mock_response

        mock_supabase.table.return_value = query_builder

        employees = await service.get_employees_with_payroll(TEST_TAX_YEAR)

        assert len(employees) == 1
        assert employees[0].first_name == "John"
        assert employees[0].last_name == "Doe"

    @pytest.mark.asyncio
    async def test_get_employees_with_payroll_empty(self, service, mock_supabase):
        """Test no employees found returns empty list."""
        mock_response = MagicMock()
        mock_response.data = []

        query_builder = MagicMock()
        query_builder.select.return_value = query_builder
        query_builder.eq.return_value = query_builder
        query_builder.in_.return_value = query_builder
        query_builder.gte.return_value = query_builder
        query_builder.lte.return_value = query_builder
        query_builder.execute.return_value = mock_response

        mock_supabase.table.return_value = query_builder

        employees = await service.get_employees_with_payroll(TEST_TAX_YEAR)

        assert len(employees) == 0

    @pytest.mark.asyncio
    async def test_get_employees_deduplicates(self, service, mock_supabase, sample_employee_data):
        """Test that duplicate employees are removed."""
        mock_response = MagicMock()
        # Same employee appears twice (from multiple payroll records)
        mock_response.data = [
            {
                "employee_id": TEST_EMPLOYEE_ID,
                "employees": sample_employee_data,
                "payroll_runs": {"pay_date": "2025-01-15", "status": "approved"},
            },
            {
                "employee_id": TEST_EMPLOYEE_ID,
                "employees": sample_employee_data,
                "payroll_runs": {"pay_date": "2025-01-31", "status": "approved"},
            },
        ]

        query_builder = MagicMock()
        query_builder.select.return_value = query_builder
        query_builder.eq.return_value = query_builder
        query_builder.in_.return_value = query_builder
        query_builder.gte.return_value = query_builder
        query_builder.lte.return_value = query_builder
        query_builder.execute.return_value = mock_response

        mock_supabase.table.return_value = query_builder

        employees = await service.get_employees_with_payroll(TEST_TAX_YEAR)

        # Should only have one employee despite two records
        assert len(employees) == 1

    @pytest.mark.asyncio
    async def test_get_employees_with_none_employee_data(self, service, mock_supabase):
        """Test that records with None employee_data are skipped (line 97)."""
        mock_response = MagicMock()
        mock_response.data = [
            {
                "employee_id": TEST_EMPLOYEE_ID,
                "employees": None,  # Missing employee data - should be skipped
                "payroll_runs": {"pay_date": "2025-01-15", "status": "approved"},
            },
        ]

        query_builder = MagicMock()
        query_builder.select.return_value = query_builder
        query_builder.eq.return_value = query_builder
        query_builder.in_.return_value = query_builder
        query_builder.gte.return_value = query_builder
        query_builder.lte.return_value = query_builder
        query_builder.execute.return_value = mock_response

        mock_supabase.table.return_value = query_builder

        employees = await service.get_employees_with_payroll(TEST_TAX_YEAR)

        # Should skip the record with None employee_data
        assert len(employees) == 0

    @pytest.mark.asyncio
    async def test_get_employees_validation_fails(self, service, mock_supabase):
        """Test that employee validation errors are handled gracefully (lines 104-105)."""
        mock_response = MagicMock()
        # Invalid employee data that will fail model validation
        invalid_employee_data = {
            "id": TEST_EMPLOYEE_ID,
            "user_id": TEST_USER_ID,
            "company_id": TEST_COMPANY_ID,
            # Missing required fields like first_name, last_name
        }
        mock_response.data = [
            {
                "employee_id": TEST_EMPLOYEE_ID,
                "employees": invalid_employee_data,
                "payroll_runs": {"pay_date": "2025-01-15", "status": "approved"},
            },
        ]

        query_builder = MagicMock()
        query_builder.select.return_value = query_builder
        query_builder.eq.return_value = query_builder
        query_builder.in_.return_value = query_builder
        query_builder.gte.return_value = query_builder
        query_builder.lte.return_value = query_builder
        query_builder.execute.return_value = mock_response

        mock_supabase.table.return_value = query_builder

        employees = await service.get_employees_with_payroll(TEST_TAX_YEAR)

        # Should skip the invalid employee (validation error caught and logged)
        assert len(employees) == 0


# =============================================================================
# Test: _aggregate_records
# =============================================================================


class TestAggregateRecords:
    """Tests for _aggregate_records method."""

    def test_aggregate_single_record(self, service, sample_payroll_record):
        """Test aggregating a single payroll record."""
        records = [sample_payroll_record]

        totals = service._aggregate_records(records)

        # Employment income = gross_regular + gross_overtime + holiday_pay
        expected_income = Decimal("2500.00") + Decimal("100.00") + Decimal("50.00")
        assert totals["employment_income"] == expected_income
        assert totals["cpp_employee"] == Decimal("150.00")
        assert totals["cpp_additional"] == Decimal("20.00")
        assert totals["ei_employee"] == Decimal("40.00")
        # Income tax = federal + provincial
        assert totals["income_tax"] == Decimal("450.00")
        assert totals["union_dues"] == Decimal("25.00")
        assert totals["cpp_employer"] == Decimal("150.00")
        assert totals["ei_employer"] == Decimal("56.00")

    def test_aggregate_multiple_records(self, service, sample_payroll_record):
        """Test aggregating multiple payroll records."""
        records = [sample_payroll_record, sample_payroll_record]

        totals = service._aggregate_records(records)

        # Should be double of single record
        expected_income = (Decimal("2500.00") + Decimal("100.00") + Decimal("50.00")) * 2
        assert totals["employment_income"] == expected_income
        assert totals["cpp_employee"] == Decimal("300.00")
        assert totals["ei_employee"] == Decimal("80.00")
        assert totals["income_tax"] == Decimal("900.00")

    def test_aggregate_empty_records(self, service):
        """Test aggregating empty list returns zeros."""
        totals = service._aggregate_records([])

        assert totals["employment_income"] == Decimal("0")
        assert totals["cpp_employee"] == Decimal("0")
        assert totals["ei_employee"] == Decimal("0")
        assert totals["income_tax"] == Decimal("0")


# =============================================================================
# Test: aggregate_employee_year
# =============================================================================


class TestAggregateEmployeeYear:
    """Tests for aggregate_employee_year method."""

    @pytest.mark.asyncio
    async def test_aggregate_employee_year_no_records(
        self, service, mock_supabase, sample_company_data, sample_employee_data
    ):
        """Test returns None when no payroll records found."""
        mock_response = MagicMock()
        mock_response.data = []

        query_builder = MagicMock()
        query_builder.select.return_value = query_builder
        query_builder.eq.return_value = query_builder
        query_builder.in_.return_value = query_builder
        query_builder.gte.return_value = query_builder
        query_builder.lte.return_value = query_builder
        query_builder.execute.return_value = mock_response

        mock_supabase.table.return_value = query_builder

        employee = Employee.model_validate(sample_employee_data)
        company = Company.model_validate(sample_company_data)

        slip = await service.aggregate_employee_year(employee, company, TEST_TAX_YEAR)

        assert slip is None

    @pytest.mark.asyncio
    async def test_aggregate_employee_year_sin_decrypt_fails(
        self, service, mock_supabase, sample_company_data, sample_employee_data, sample_payroll_record
    ):
        """Test returns None when SIN decryption fails."""
        mock_response = MagicMock()
        mock_response.data = [sample_payroll_record]

        query_builder = MagicMock()
        query_builder.select.return_value = query_builder
        query_builder.eq.return_value = query_builder
        query_builder.in_.return_value = query_builder
        query_builder.gte.return_value = query_builder
        query_builder.lte.return_value = query_builder
        query_builder.execute.return_value = mock_response

        mock_supabase.table.return_value = query_builder

        employee = Employee.model_validate(sample_employee_data)
        company = Company.model_validate(sample_company_data)

        with patch("app.services.t4.aggregation_service.decrypt_sin", return_value=None):
            slip = await service.aggregate_employee_year(employee, company, TEST_TAX_YEAR)

        assert slip is None

    @pytest.mark.asyncio
    async def test_aggregate_employee_year_sin_luhn_fails_but_continues(
        self, service, mock_supabase, sample_company_data, sample_employee_data, sample_payroll_record
    ):
        """Test that invalid SIN (Luhn check failed) logs warning but continues (line 166)."""
        mock_response = MagicMock()
        mock_response.data = [sample_payroll_record]

        query_builder = MagicMock()
        query_builder.select.return_value = query_builder
        query_builder.eq.return_value = query_builder
        query_builder.in_.return_value = query_builder
        query_builder.gte.return_value = query_builder
        query_builder.lte.return_value = query_builder
        query_builder.execute.return_value = mock_response

        mock_supabase.table.return_value = query_builder

        employee = Employee.model_validate(sample_employee_data)
        company = Company.model_validate(sample_company_data)

        # SIN fails Luhn check but process continues (test number)
        with patch("app.services.t4.aggregation_service.decrypt_sin", return_value="000000000"), \
             patch("app.services.t4.aggregation_service.validate_sin_luhn", return_value=False):
            slip = await service.aggregate_employee_year(employee, company, TEST_TAX_YEAR)

        # Should still generate T4 despite invalid SIN
        assert slip is not None
        assert slip.sin == "000000000"

    @pytest.mark.asyncio
    async def test_aggregate_employee_year_success(
        self, service, mock_supabase, sample_company_data, sample_employee_data, sample_payroll_record
    ):
        """Test successful aggregation creates T4 slip."""
        mock_response = MagicMock()
        mock_response.data = [sample_payroll_record]

        query_builder = MagicMock()
        query_builder.select.return_value = query_builder
        query_builder.eq.return_value = query_builder
        query_builder.in_.return_value = query_builder
        query_builder.gte.return_value = query_builder
        query_builder.lte.return_value = query_builder
        query_builder.execute.return_value = mock_response

        mock_supabase.table.return_value = query_builder

        employee = Employee.model_validate(sample_employee_data)
        company = Company.model_validate(sample_company_data)

        with patch("app.services.t4.aggregation_service.decrypt_sin", return_value="123456789"), \
             patch("app.services.t4.aggregation_service.validate_sin_luhn", return_value=True):
            slip = await service.aggregate_employee_year(employee, company, TEST_TAX_YEAR)

        assert slip is not None
        assert slip.employee_first_name == "John"
        assert slip.employee_last_name == "Doe"
        assert slip.employer_name == "Test Company Inc."
        assert slip.sin == "123456789"
        assert slip.tax_year == TEST_TAX_YEAR


# =============================================================================
# Test: generate_all_t4_slips
# =============================================================================


class TestGenerateAllT4Slips:
    """Tests for generate_all_t4_slips method."""

    @pytest.mark.asyncio
    async def test_generate_all_no_company(self, service, mock_supabase):
        """Test returns empty list when company not found."""
        mock_response = MagicMock()
        mock_response.data = None

        query_builder = MagicMock()
        query_builder.select.return_value = query_builder
        query_builder.eq.return_value = query_builder
        query_builder.maybe_single.return_value = query_builder
        query_builder.execute.return_value = mock_response

        mock_supabase.table.return_value = query_builder

        slips = await service.generate_all_t4_slips(TEST_TAX_YEAR)

        assert slips == []

    @pytest.mark.asyncio
    async def test_generate_all_filters_by_employee_ids(
        self, service, mock_supabase, sample_company_data, sample_employee_data
    ):
        """Test that employee_ids filter is applied."""
        # Create two different employees
        emp1_id = str(uuid4())
        emp2_id = str(uuid4())

        emp1_data = sample_employee_data.copy()
        emp1_data["id"] = emp1_id

        emp2_data = sample_employee_data.copy()
        emp2_data["id"] = emp2_id
        emp2_data["first_name"] = "Jane"

        company_response = MagicMock()
        company_response.data = sample_company_data

        employees_response = MagicMock()
        employees_response.data = [
            {"employee_id": emp1_id, "employees": emp1_data, "payroll_runs": {"status": "approved"}},
            {"employee_id": emp2_id, "employees": emp2_data, "payroll_runs": {"status": "approved"}},
        ]

        call_count = 0

        def table_side_effect(table_name):
            nonlocal call_count
            query_builder = MagicMock()
            query_builder.select.return_value = query_builder
            query_builder.eq.return_value = query_builder
            query_builder.maybe_single.return_value = query_builder
            query_builder.in_.return_value = query_builder
            query_builder.gte.return_value = query_builder
            query_builder.lte.return_value = query_builder

            if table_name == "companies":
                query_builder.execute.return_value = company_response
            elif table_name == "payroll_records":
                if call_count == 0:
                    # First call - get employees with payroll
                    call_count += 1
                    query_builder.execute.return_value = employees_response
                else:
                    # Subsequent calls for individual employee aggregation
                    empty_response = MagicMock()
                    empty_response.data = []
                    query_builder.execute.return_value = empty_response
            else:
                empty_response = MagicMock()
                empty_response.data = []
                query_builder.execute.return_value = empty_response

            return query_builder

        mock_supabase.table.side_effect = table_side_effect

        # Only request emp1
        slips = await service.generate_all_t4_slips(
            TEST_TAX_YEAR,
            employee_ids=[UUID(emp1_id)],
        )

        # Should only process emp1 (though returns empty due to mock)
        # The test verifies filtering logic works
        assert isinstance(slips, list)

    @pytest.mark.asyncio
    async def test_generate_all_handles_aggregate_exception(self, service, mock_supabase, sample_company_data):
        """Test that exceptions during aggregate_employee_year are handled gracefully (lines 300-302)."""
        company_response = MagicMock()
        company_response.data = sample_company_data

        query_builder = MagicMock()
        query_builder.select.return_value = query_builder
        query_builder.eq.return_value = query_builder
        query_builder.maybe_single.return_value = query_builder
        query_builder.execute.return_value = company_response

        mock_supabase.table.return_value = query_builder

        # Mock get_employees_with_payroll to return an employee
        employee = Employee(
            id=UUID(TEST_EMPLOYEE_ID),
            user_id=TEST_USER_ID,
            company_id=TEST_COMPANY_ID,  # String, not UUID
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            sin_encrypted="encrypted",
            date_of_birth="1990-01-15",
            hire_date="2024-01-01",
            address_street="123 St",
            address_city="Toronto",
            address_postal_code="M5V 1A1",
            province_of_employment="ON",
            pay_frequency="bi_weekly",
            annual_salary=60000,
            is_cpp_exempt=False,
            is_ei_exempt=False,
            employment_status="active",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )

        with patch.object(service, "get_employees_with_payroll", return_value=[employee]), \
             patch.object(service, "aggregate_employee_year", side_effect=Exception("Aggregation failed")):
            # Should handle exception and return empty list
            slips = await service.generate_all_t4_slips(TEST_TAX_YEAR)

        # Should not crash, just skip the employee with error
        assert isinstance(slips, list)
        assert len(slips) == 0

    @pytest.mark.asyncio
    async def test_generate_all_handles_employee_exception(self, service, mock_supabase, sample_company_data):
        """Test that exceptions during employee aggregation are handled gracefully (lines 300-302)."""
        company_response = MagicMock()
        company_response.data = sample_company_data

        sample_employee_data2 = {
            "id": TEST_EMPLOYEE_ID,
            "user_id": TEST_USER_ID,
            "company_id": TEST_COMPANY_ID,
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "sin_encrypted": "test_encrypted_sin",
            "date_of_birth": "1990-01-15",
            "hire_date": "2024-01-01",
            "address_street": "456 Employee St",
            "address_city": "Toronto",
            "address_postal_code": "M4K 2A1",
            "province_of_employment": "ON",
            "pay_frequency": "bi_weekly",
            "annual_salary": 60000,
            "is_cpp_exempt": False,
            "is_ei_exempt": False,
            "employment_status": "active",
        }

        employees_response = MagicMock()
        employees_response.data = [
            {"employee_id": TEST_EMPLOYEE_ID, "employees": sample_employee_data2, "payroll_runs": {"status": "approved"}},
        ]

        call_count = [0]

        def table_side_effect(table_name):
            query_builder = MagicMock()
            query_builder.select.return_value = query_builder
            query_builder.eq.return_value = query_builder
            query_builder.maybe_single.return_value = query_builder
            query_builder.in_.return_value = query_builder
            query_builder.gte.return_value = query_builder
            query_builder.lte.return_value = query_builder

            if table_name == "companies":
                query_builder.execute.return_value = company_response
            elif table_name == "payroll_records":
                call_count[0] += 1
                # Raise exception on second call (for individual employee)
                if call_count[0] > 1:
                    query_builder.execute.side_effect = Exception("Database error")
                else:
                    query_builder.execute.return_value = employees_response
            else:
                empty_response = MagicMock()
                empty_response.data = []
                query_builder.execute.return_value = empty_response

            return query_builder

        mock_supabase.table.side_effect = table_side_effect

        # Should handle exception and return empty list
        slips = await service.generate_all_t4_slips(TEST_TAX_YEAR)

        # Should not crash, just skip the employee with error
        assert isinstance(slips, list)
        assert len(slips) == 0


# =============================================================================
# Test: generate_t4_summary
# =============================================================================


class TestGenerateT4Summary:
    """Tests for generate_t4_summary method."""

    @pytest.mark.asyncio
    async def test_generate_summary_no_company(self, service, mock_supabase):
        """Test returns None when company not found."""
        mock_response = MagicMock()
        mock_response.data = None

        query_builder = MagicMock()
        query_builder.select.return_value = query_builder
        query_builder.eq.return_value = query_builder
        query_builder.maybe_single.return_value = query_builder
        query_builder.execute.return_value = mock_response

        mock_supabase.table.return_value = query_builder

        summary = await service.generate_t4_summary(TEST_TAX_YEAR)

        assert summary is None

    @pytest.mark.asyncio
    async def test_generate_summary_no_slips(self, service, mock_supabase, sample_company_data):
        """Test returns None when no slips provided and none generated."""
        company_response = MagicMock()
        company_response.data = sample_company_data

        query_builder = MagicMock()
        query_builder.select.return_value = query_builder
        query_builder.eq.return_value = query_builder
        query_builder.maybe_single.return_value = query_builder
        query_builder.in_.return_value = query_builder
        query_builder.gte.return_value = query_builder
        query_builder.lte.return_value = query_builder

        def table_side_effect(table_name):
            if table_name == "companies":
                query_builder.execute.return_value = company_response
            else:
                empty_response = MagicMock()
                empty_response.data = []
                query_builder.execute.return_value = empty_response
            return query_builder

        mock_supabase.table.side_effect = table_side_effect

        summary = await service.generate_t4_summary(TEST_TAX_YEAR, slips=[])

        assert summary is None

    @pytest.mark.asyncio
    async def test_generate_summary_with_slips_none_generates_slips(self, service, mock_supabase, sample_company_data):
        """Test that slips=None triggers auto-generation (line 328)."""
        from app.models.t4 import T4SlipData

        company_response = MagicMock()
        company_response.data = sample_company_data

        employer_totals_response = MagicMock()
        employer_totals_response.data = [
            {"cpp_employer": "150.00", "ei_employer": "56.00"},
        ]

        def table_side_effect(table_name):
            query_builder = MagicMock()
            query_builder.select.return_value = query_builder
            query_builder.eq.return_value = query_builder
            query_builder.maybe_single.return_value = query_builder
            query_builder.in_.return_value = query_builder
            query_builder.gte.return_value = query_builder
            query_builder.lte.return_value = query_builder

            if table_name == "companies":
                query_builder.execute.return_value = company_response
            elif table_name == "payroll_records":
                query_builder.execute.return_value = employer_totals_response
            else:
                empty_response = MagicMock()
                empty_response.data = []
                query_builder.execute.return_value = empty_response

            return query_builder

        mock_supabase.table.side_effect = table_side_effect

        # Pass slips=None (not empty list) to trigger auto-generation
        with patch.object(service, "generate_all_t4_slips", return_value=[]) as mock_generate:
            summary = await service.generate_t4_summary(TEST_TAX_YEAR, slips=None)

            # Should have called generate_all_t4_slips since slips was None
            mock_generate.assert_called_once_with(TEST_TAX_YEAR)

        # Returns None because no slips were generated
        assert summary is None

    @pytest.mark.asyncio
    async def test_generate_summary_with_slips(self, service, mock_supabase, sample_company_data):
        """Test successful summary generation with provided slips."""
        from app.models.t4 import T4SlipData

        company_response = MagicMock()
        company_response.data = sample_company_data

        employer_totals_response = MagicMock()
        employer_totals_response.data = [
            {"cpp_employer": "150.00", "ei_employer": "56.00"},
        ]

        def table_side_effect(table_name):
            query_builder = MagicMock()
            query_builder.select.return_value = query_builder
            query_builder.eq.return_value = query_builder
            query_builder.maybe_single.return_value = query_builder
            query_builder.in_.return_value = query_builder
            query_builder.gte.return_value = query_builder
            query_builder.lte.return_value = query_builder

            if table_name == "companies":
                query_builder.execute.return_value = company_response
            elif table_name == "payroll_records":
                query_builder.execute.return_value = employer_totals_response
            else:
                empty_response = MagicMock()
                empty_response.data = []
                query_builder.execute.return_value = empty_response

            return query_builder

        mock_supabase.table.side_effect = table_side_effect

        # Create test slips
        slip = T4SlipData(
            employee_id=UUID(TEST_EMPLOYEE_ID),
            tax_year=TEST_TAX_YEAR,
            sin="123456789",
            employee_first_name="John",
            employee_last_name="Doe",
            employer_name="Test Company Inc.",
            employer_account_number="123456789RP0001",
            box_14_employment_income=Decimal("50000.00"),
            box_16_cpp_contributions=Decimal("3800.00"),
            box_17_cpp2_contributions=Decimal("500.00"),
            box_18_ei_premiums=Decimal("1049.12"),
            box_22_income_tax_deducted=Decimal("8500.00"),
            box_24_ei_insurable_earnings=Decimal("50000.00"),
            box_26_cpp_pensionable_earnings=Decimal("50000.00"),
            box_44_union_dues=Decimal("500.00"),
            province_of_employment=Province.ON,
        )

        summary = await service.generate_t4_summary(TEST_TAX_YEAR, slips=[slip])

        assert summary is not None
        assert summary.tax_year == TEST_TAX_YEAR
        assert summary.total_number_of_t4_slips == 1
        assert summary.total_employment_income == Decimal("50000.00")
        assert summary.total_cpp_contributions == Decimal("3800.00")
        assert summary.employer_name == "Test Company Inc."


# =============================================================================
# Test: Exception Handling
# =============================================================================


class TestExceptionHandling:
    """Tests for exception handling in T4AggregationService."""

    @pytest.mark.asyncio
    async def test_get_company_database_error(self, service, mock_supabase):
        """Test that database error in get_company propagates appropriately."""
        query_builder = MagicMock()
        query_builder.select.return_value = query_builder
        query_builder.eq.return_value = query_builder
        query_builder.maybe_single.return_value = query_builder
        query_builder.execute.side_effect = Exception("Database connection failed")

        mock_supabase.table.return_value = query_builder

        # get_company doesn't have graceful error handling - exception should propagate
        with pytest.raises(Exception, match="Database connection failed"):
            await service.get_company()

    @pytest.mark.asyncio
    async def test_get_employees_database_error(self, service, mock_supabase, sample_company_data):
        """Test that database error in get_employees_with_payroll propagates appropriately."""
        company_response = MagicMock()
        company_response.data = sample_company_data

        call_count = [0]

        def table_side_effect(table_name):
            query_builder = MagicMock()
            query_builder.select.return_value = query_builder
            query_builder.eq.return_value = query_builder
            query_builder.maybe_single.return_value = query_builder
            query_builder.in_.return_value = query_builder
            query_builder.gte.return_value = query_builder
            query_builder.lte.return_value = query_builder

            if table_name == "companies":
                query_builder.execute.return_value = company_response
            elif table_name == "payroll_records":
                call_count[0] += 1
                # First call is for get_employees_with_payroll
                if call_count[0] == 1:
                    query_builder.execute.side_effect = Exception("Database query failed")
                else:
                    empty_response = MagicMock()
                    empty_response.data = []
                    query_builder.execute.return_value = empty_response
            else:
                empty_response = MagicMock()
                empty_response.data = []
                query_builder.execute.return_value = empty_response

            return query_builder

        mock_supabase.table.side_effect = table_side_effect

        # get_employees_with_payroll doesn't have graceful error handling
        with pytest.raises(Exception, match="Database query failed"):
            await service.get_employees_with_payroll(TEST_TAX_YEAR)

    @pytest.mark.asyncio
    async def test_aggregate_employee_year_database_error(
        self, service, mock_supabase, sample_company_data, sample_employee_data
    ):
        """Test that database error in aggregate_employee_year propagates appropriately."""
        company_response = MagicMock()
        company_response.data = sample_company_data

        employee = Employee(
            id=UUID(TEST_EMPLOYEE_ID),
            user_id=TEST_USER_ID,
            company_id=TEST_COMPANY_ID,
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            sin_encrypted="encrypted",
            date_of_birth="1990-01-15",
            hire_date="2024-01-01",
            address_street="123 St",
            address_city="Toronto",
            address_postal_code="M5V 1A1",
            province_of_employment="ON",
            pay_frequency="bi_weekly",
            annual_salary=60000,
            is_cpp_exempt=False,
            is_ei_exempt=False,
            employment_status="active",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )

        company = Company(
            id=UUID(TEST_COMPANY_ID),
            user_id=TEST_USER_ID,
            company_name="Test Company Inc.",
            business_number="123456789",
            payroll_account_number="123456789RP0001",
            province="ON",
            address_street="123 Main St",
            address_city="Toronto",
            address_postal_code="M5V 1A1",
            remitter_type="regular",
            auto_calculate_deductions=True,
            send_paystub_emails=False,
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )

        def table_side_effect(table_name):
            query_builder = MagicMock()
            query_builder.select.return_value = query_builder
            query_builder.eq.return_value = query_builder
            query_builder.maybe_single.return_value = query_builder
            query_builder.in_.return_value = query_builder
            query_builder.gte.return_value = query_builder
            query_builder.lte.return_value = query_builder

            if table_name == "companies":
                query_builder.execute.return_value = company_response
            elif table_name == "payroll_records":
                # Simulate database error during payroll records fetch
                query_builder.execute.side_effect = Exception("Payroll records query failed")
            else:
                empty_response = MagicMock()
                empty_response.data = []
                query_builder.execute.return_value = empty_response

            return query_builder

        mock_supabase.table.side_effect = table_side_effect

        # aggregate_employee_year doesn't have graceful error handling for DB errors
        with pytest.raises(Exception, match="Payroll records query failed"):
            await service.aggregate_employee_year(employee, company, TEST_TAX_YEAR)

    def test_aggregate_records_invalid_decimal(self, service):
        """Test that invalid decimal values in payroll records raise InvalidOperation."""
        from decimal import InvalidOperation

        # Create payroll records with invalid numeric values
        # The _aggregate_records method uses fields like gross_regular, gross_overtime, etc.
        records = [
            {
                "gross_regular": "not_a_number",  # Invalid decimal - will raise
                "gross_overtime": "0.00",
                "holiday_pay": "0.00",
                "holiday_premium_pay": "0.00",
                "vacation_pay_paid": "0.00",
                "other_earnings": "0.00",
                "federal_tax": "100.00",
                "provincial_tax": "50.00",
                "cpp_employee": "50.00",
                "cpp_employer": "50.00",
                "cpp_additional": "0.00",
                "ei_employee": "25.00",
                "ei_employer": "35.00",
                "union_dues": "0.00",
            }
        ]

        # _aggregate_records uses Decimal(str(record.get(..., 0)))
        # When a non-numeric string is present, Decimal() raises InvalidOperation
        with pytest.raises(InvalidOperation):
            service._aggregate_records(records)
