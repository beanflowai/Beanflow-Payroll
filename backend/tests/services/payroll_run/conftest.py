"""
Shared fixtures for payroll_run service tests.

Provides mocks for supabase, YtdCalculator, HolidayPayCalculator,
and factory fixtures for creating test data.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from app.services.payroll_run.run_operations import PayrollRunOperations


# =============================================================================
# Test Data Factories
# =============================================================================


@pytest.fixture
def sample_run_id() -> UUID:
    """A consistent run ID for tests."""
    return UUID("12345678-1234-1234-1234-123456789012")


@pytest.fixture
def sample_employee_id() -> str:
    """A consistent employee ID for tests."""
    return "emp-12345678-1234-1234-1234-123456789012"


@pytest.fixture
def sample_user_id() -> str:
    """A consistent user ID for tests."""
    return "user-12345678-1234-1234-1234-123456789012"


@pytest.fixture
def sample_company_id() -> str:
    """A consistent company ID for tests."""
    return "company-12345678-1234-1234-1234-123456789012"


def make_employee(
    employee_id: str | None = None,
    first_name: str = "John",
    last_name: str = "Doe",
    province: str = "SK",
    pay_frequency: str = "bi_weekly",
    annual_salary: float | None = 60000.0,
    hourly_rate: float | None = None,
    federal_additional_claims: float = 0.0,
    provincial_additional_claims: float = 0.0,
    is_cpp_exempt: bool = False,
    is_ei_exempt: bool = False,
    cpp2_exempt: bool = False,
    vacation_config: dict[str, Any] | None = None,
    vacation_balance: float = 0.0,
    sick_balance: float = 0.0,
    pay_groups: dict[str, Any] | None = None,
    companies: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Factory for creating employee test data."""
    return {
        "id": employee_id or str(uuid4()),
        "first_name": first_name,
        "last_name": last_name,
        "email": f"{first_name.lower()}.{last_name.lower()}@test.com",
        "province_of_employment": province,
        "pay_frequency": pay_frequency,
        "annual_salary": annual_salary,
        "hourly_rate": hourly_rate,
        "federal_additional_claims": federal_additional_claims,
        "provincial_additional_claims": provincial_additional_claims,
        "is_cpp_exempt": is_cpp_exempt,
        "is_ei_exempt": is_ei_exempt,
        "cpp2_exempt": cpp2_exempt,
        "vacation_config": vacation_config or {"payout_method": "accrual", "vacation_rate": 0.04},
        "vacation_balance": vacation_balance,
        "sick_balance": sick_balance,
        "hire_date": "2020-01-15",
        "termination_date": None,
        "sin_encrypted": "encrypted_sin",
        "employment_type": "full_time",
        "address_street": "123 Test St",
        "address_city": "Saskatoon",
        "address_postal_code": "S7K 0A1",
        "occupation": "Developer",
        "company_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "pay_group_id": "b1c2d3e4-f5a6-7890-bcde-f12345678901",
        "pay_groups": pay_groups or make_pay_group(),
        "companies": companies or make_company(),
    }


def make_pay_group(
    pay_group_id: str | None = None,
    name: str = "Default Pay Group",
    pay_frequency: str = "bi_weekly",
    employment_type: str = "full_time",
    next_period_end: str = "2025-01-17",
    group_benefits: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Factory for creating pay group test data."""
    return {
        "id": pay_group_id or str(uuid4()),
        "name": name,
        "description": "Test pay group",
        "pay_frequency": pay_frequency,
        "employment_type": employment_type,
        "next_period_end": next_period_end,
        "period_start_day": "monday",
        "leave_enabled": True,
        "overtime_policy": {},
        "wcb_config": {},
        "group_benefits": group_benefits or {},
    }


def make_company(
    company_id: str | None = None,
    company_name: str = "Test Company Inc",
    province: str = "SK",
    remitter_type: str = "regular",
    logo_url: str | None = None,
) -> dict[str, Any]:
    """Factory for creating company test data."""
    return {
        "id": company_id or str(uuid4()),
        "company_name": company_name,
        "business_number": "123456789",
        "payroll_account_number": "123456789RP0001",
        "province": province,
        "address_street": "456 Business Ave",
        "address_city": "Saskatoon",
        "address_postal_code": "S7K 0B1",
        "remitter_type": remitter_type,
        "auto_calculate_deductions": True,
        "send_paystub_emails": True,
        "logo_url": logo_url,
    }


def make_payroll_run(
    run_id: str | None = None,
    user_id: str = "c1d2e3f4-a5b6-7890-cdef-123456789012",
    company_id: str = "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    status: str = "draft",
    period_start: str = "2025-01-04",
    period_end: str = "2025-01-17",
    pay_date: str = "2025-01-23",
    total_employees: int = 1,
    total_gross: float = 2307.69,
    total_cpp_employee: float = 100.0,
    total_cpp_employer: float = 100.0,
    total_ei_employee: float = 37.85,
    total_ei_employer: float = 52.99,
    total_federal_tax: float = 200.0,
    total_provincial_tax: float = 150.0,
    total_net_pay: float = 1819.84,
    total_employer_cost: float = 152.99,
    created_at: str = "2025-01-20T10:00:00",
    updated_at: str = "2025-01-20T10:00:00",
    approved_at: str | None = None,
    approved_by: str | None = None,
) -> dict[str, Any]:
    """Factory for creating payroll run test data."""
    return {
        "id": run_id or str(uuid4()),
        "user_id": user_id,
        "company_id": company_id,
        "status": status,
        "period_start": period_start,
        "period_end": period_end,
        "pay_date": pay_date,
        "total_employees": total_employees,
        "total_gross": total_gross,
        "total_cpp_employee": total_cpp_employee,
        "total_cpp_employer": total_cpp_employer,
        "total_ei_employee": total_ei_employee,
        "total_ei_employer": total_ei_employer,
        "total_federal_tax": total_federal_tax,
        "total_provincial_tax": total_provincial_tax,
        "total_net_pay": total_net_pay,
        "total_employer_cost": total_employer_cost,
        "created_at": created_at,
        "updated_at": updated_at,
        "approved_at": approved_at,
        "approved_by": approved_by,
        "notes": None,
    }


def make_payroll_record(
    record_id: str | None = None,
    payroll_run_id: str = "d1e2f3a4-b5c6-7890-defa-234567890123",
    employee_id: str = "e1f2a3b4-c5d6-7890-efab-345678901234",
    user_id: str = "c1d2e3f4-a5b6-7890-cdef-123456789012",
    company_id: str = "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    employee: dict[str, Any] | None = None,
    input_data: dict[str, Any] | None = None,
    gross_regular: float = 2307.69,
    gross_overtime: float = 0.0,
    holiday_pay: float = 0.0,
    holiday_premium_pay: float = 0.0,
    vacation_pay_paid: float = 0.0,
    vacation_hours_taken: float = 0.0,
    vacation_accrued: float = 0.0,
    sick_hours_taken: float = 0.0,
    sick_pay_paid: float = 0.0,
    other_earnings: float = 0.0,
    cpp_employee: float = 100.0,
    cpp_additional: float = 0.0,
    ei_employee: float = 37.85,
    federal_tax: float = 200.0,
    provincial_tax: float = 150.0,
    other_deductions: float = 0.0,
    cpp_employer: float = 100.0,
    ei_employer: float = 52.99,
    is_modified: bool = False,
    paystub_storage_key: str | None = None,
    paystub_generated_at: str | None = None,
) -> dict[str, Any]:
    """Factory for creating payroll record test data."""
    return {
        "id": record_id or str(uuid4()),
        "payroll_run_id": payroll_run_id,
        "employee_id": employee_id,
        "user_id": user_id,
        "company_id": company_id,
        "employees": employee or make_employee(employee_id=employee_id),
        "input_data": input_data or {},
        "gross_regular": gross_regular,
        "gross_overtime": gross_overtime,
        "holiday_pay": holiday_pay,
        "holiday_premium_pay": holiday_premium_pay,
        "vacation_pay_paid": vacation_pay_paid,
        "vacation_hours_taken": vacation_hours_taken,
        "vacation_accrued": vacation_accrued,
        "sick_hours_taken": sick_hours_taken,
        "sick_pay_paid": sick_pay_paid,
        "other_earnings": other_earnings,
        "cpp_employee": cpp_employee,
        "cpp_additional": cpp_additional,
        "ei_employee": ei_employee,
        "federal_tax": federal_tax,
        "provincial_tax": provincial_tax,
        "other_deductions": other_deductions,
        "cpp_employer": cpp_employer,
        "ei_employer": ei_employer,
        "ytd_gross": gross_regular + gross_overtime,
        "ytd_cpp": cpp_employee,
        "ytd_ei": ei_employee,
        "ytd_federal_tax": federal_tax,
        "ytd_provincial_tax": provincial_tax,
        "ytd_net_pay": gross_regular - cpp_employee - ei_employee - federal_tax - provincial_tax,
        "is_modified": is_modified,
        "regular_hours_worked": 80.0,
        "overtime_hours_worked": 0.0,
        "paystub_storage_key": paystub_storage_key,
        "paystub_generated_at": paystub_generated_at,
    }


# =============================================================================
# Mock Supabase Client
# =============================================================================


class MockSupabaseTable:
    """Mock for supabase table operations with chainable methods."""

    def __init__(self, table_name: str, mock_data: dict[str, list[dict[str, Any]]] | None = None):
        self.table_name = table_name
        self._mock_data = mock_data or {}
        self._query_filters: dict[str, Any] = {}
        self._select_fields: str = "*"
        self._update_data: dict[str, Any] = {}
        self._insert_data: dict[str, Any] = {}

    def select(self, fields: str = "*") -> MockSupabaseTable:
        self._select_fields = fields
        return self

    def insert(self, data: dict[str, Any]) -> MockSupabaseTable:
        self._insert_data = data
        return self

    def update(self, data: dict[str, Any]) -> MockSupabaseTable:
        self._update_data = data
        return self

    def eq(self, field: str, value: Any) -> MockSupabaseTable:
        self._query_filters[f"eq_{field}"] = value
        return self

    def in_(self, field: str, values: list[Any]) -> MockSupabaseTable:
        self._query_filters[f"in_{field}"] = values
        return self

    def is_(self, field: str, value: Any) -> MockSupabaseTable:
        self._query_filters[f"is_{field}"] = value
        return self

    def gte(self, field: str, value: Any) -> MockSupabaseTable:
        self._query_filters[f"gte_{field}"] = value
        return self

    def lte(self, field: str, value: Any) -> MockSupabaseTable:
        self._query_filters[f"lte_{field}"] = value
        return self

    def single(self) -> MockSupabaseTable:
        return self

    def execute(self) -> MagicMock:
        result = MagicMock()
        table_data = self._mock_data.get(self.table_name, [])
        result.data = table_data
        return result


class MockSupabaseClient:
    """Mock Supabase client for testing."""

    def __init__(self):
        self._tables: dict[str, list[dict[str, Any]]] = {}
        self._table_mocks: dict[str, MagicMock] = {}

    def set_table_data(self, table_name: str, data: list[dict[str, Any]]) -> None:
        """Set mock data for a specific table."""
        self._tables[table_name] = data

    def get_table_mock(self, table_name: str) -> MagicMock:
        """Get or create a mock for a specific table."""
        if table_name not in self._table_mocks:
            self._table_mocks[table_name] = MagicMock()
        return self._table_mocks[table_name]

    def table(self, name: str) -> MagicMock:
        """Return a mock table with configured data."""
        return self.get_table_mock(name)


@pytest.fixture
def mock_supabase() -> MockSupabaseClient:
    """Create a mock Supabase client."""
    return MockSupabaseClient()


# =============================================================================
# Mock YtdCalculator
# =============================================================================


@pytest.fixture
def mock_ytd_calculator() -> MagicMock:
    """Create a mock YtdCalculator."""
    calculator = MagicMock()

    # Default: return empty YTD data
    calculator.get_prior_ytd_for_employees.return_value = {}

    # Async method for getting YTD records
    calculator.get_ytd_records_for_employee = AsyncMock(return_value=[])

    return calculator


# =============================================================================
# Mock Callback Functions
# =============================================================================


@pytest.fixture
def mock_get_run_func() -> AsyncMock:
    """Create a mock get_run function."""
    return AsyncMock(return_value=None)


@pytest.fixture
def mock_get_run_records_func() -> AsyncMock:
    """Create a mock get_run_records function."""
    return AsyncMock(return_value=[])


@pytest.fixture
def mock_create_records_func() -> AsyncMock:
    """Create a mock create_records function."""
    return AsyncMock(return_value=([], []))


# =============================================================================
# PayrollRunOperations Fixture
# =============================================================================


@pytest.fixture
def run_operations(
    mock_supabase: MockSupabaseClient,
    mock_ytd_calculator: MagicMock,
    mock_get_run_func: AsyncMock,
    mock_get_run_records_func: AsyncMock,
    mock_create_records_func: AsyncMock,
    sample_user_id: str,
    sample_company_id: str,
) -> PayrollRunOperations:
    """Create a PayrollRunOperations instance with mocked dependencies."""
    with patch(
        "app.services.payroll_run.run_operations.HolidayPayCalculator"
    ) as mock_holiday_calc_class:
        mock_holiday_calc = MagicMock()
        mock_holiday_calc.calculate_holiday_pay.return_value = MagicMock(
            regular_holiday_pay=Decimal("0"),
            premium_holiday_pay=Decimal("0"),
        )
        mock_holiday_calc_class.return_value = mock_holiday_calc

        ops = PayrollRunOperations(
            supabase=mock_supabase,
            user_id=sample_user_id,
            company_id=sample_company_id,
            ytd_calculator=mock_ytd_calculator,
            get_run_func=mock_get_run_func,
            get_run_records_func=mock_get_run_records_func,
            create_records_func=mock_create_records_func,
        )

        # Store the mock for later access in tests
        ops._mock_holiday_calculator = mock_holiday_calc

        return ops


# =============================================================================
# PayrollEngine Mock Result Factory
# =============================================================================


def make_payroll_result(
    employee_id: str,
    gross_regular: Decimal = Decimal("2307.69"),
    gross_overtime: Decimal = Decimal("0"),
    holiday_pay: Decimal = Decimal("0"),
    holiday_premium_pay: Decimal = Decimal("0"),
    vacation_pay: Decimal = Decimal("0"),
    other_earnings: Decimal = Decimal("0"),
    cpp_base: Decimal = Decimal("100.00"),
    cpp_additional: Decimal = Decimal("0"),
    ei_employee: Decimal = Decimal("37.85"),
    federal_tax: Decimal = Decimal("200.00"),
    provincial_tax: Decimal = Decimal("150.00"),
    other_deductions: Decimal = Decimal("0"),
    cpp_employer: Decimal = Decimal("100.00"),
    ei_employer: Decimal = Decimal("52.99"),
) -> MagicMock:
    """Factory for creating mock PayrollResult objects."""
    result = MagicMock()
    result.employee_id = employee_id
    result.gross_regular = gross_regular
    result.gross_overtime = gross_overtime
    result.holiday_pay = holiday_pay
    result.holiday_premium_pay = holiday_premium_pay
    result.vacation_pay = vacation_pay
    result.other_earnings = other_earnings
    result.cpp_base = cpp_base
    result.cpp_additional = cpp_additional
    result.cpp_total = cpp_base + cpp_additional
    result.ei_employee = ei_employee
    result.federal_tax = federal_tax
    result.provincial_tax = provincial_tax
    result.other_deductions = other_deductions
    result.cpp_employer = cpp_employer
    result.ei_employer = ei_employer

    total_gross = gross_regular + gross_overtime + holiday_pay + holiday_premium_pay + vacation_pay + other_earnings
    total_deductions = cpp_base + cpp_additional + ei_employee + federal_tax + provincial_tax + other_deductions
    net_pay = total_gross - total_deductions

    result.total_gross = total_gross
    result.net_pay = net_pay

    # YTD values
    result.new_ytd_gross = total_gross
    result.new_ytd_cpp = cpp_base + cpp_additional
    result.new_ytd_ei = ei_employee
    result.new_ytd_federal_tax = federal_tax
    result.new_ytd_provincial_tax = provincial_tax

    return result


# =============================================================================
# Helper Context Managers for Patching
# =============================================================================


@pytest.fixture
def patch_payroll_engine():
    """Patch PayrollEngine for testing."""
    def _patch(results: list[MagicMock]):
        mock_engine = MagicMock()
        mock_engine.calculate_batch.return_value = results
        return patch(
            "app.services.payroll_run.run_operations.PayrollEngine",
            return_value=mock_engine,
        )
    return _patch


@pytest.fixture
def patch_paystub_services():
    """Patch paystub generation services for testing."""
    def _patch(
        storage_key: str = "test-storage-key",
        pdf_bytes: bytes = b"test-pdf-content",
        raise_storage_error: bool = False,
    ):
        patches = {}

        # PaystubDataBuilder - now in paystub_orchestrator
        mock_builder = MagicMock()
        mock_builder.build.return_value = MagicMock()
        patches["builder"] = patch(
            "app.services.payroll_run.paystub_orchestrator.PaystubDataBuilder",
            return_value=mock_builder,
        )

        # PaystubGenerator - now in paystub_orchestrator
        mock_generator = MagicMock()
        mock_generator.generate_paystub_bytes.return_value = pdf_bytes
        patches["generator"] = patch(
            "app.services.payroll_run.paystub_orchestrator.PaystubGenerator",
            return_value=mock_generator,
        )

        # PaystubStorage - still imported in run_operations for config check
        if raise_storage_error:
            from app.services.payroll.paystub_storage import PaystubStorageConfigError
            patches["storage"] = patch(
                "app.services.payroll_run.run_operations.PaystubStorage",
                side_effect=PaystubStorageConfigError("Test error"),
            )
        else:
            mock_storage = MagicMock()
            mock_storage.save_paystub = AsyncMock(return_value=storage_key)
            patches["storage"] = patch(
                "app.services.payroll_run.run_operations.PaystubStorage",
                return_value=mock_storage,
            )

        return patches

    return _patch


@pytest.fixture
def patch_httpx_client():
    """Patch httpx.AsyncClient for logo download testing."""
    def _patch(
        logo_bytes: bytes | None = None,
        raise_error: bool = False,
    ):
        mock_response = MagicMock()
        if logo_bytes:
            mock_response.content = logo_bytes
            mock_response.raise_for_status = MagicMock()
        elif raise_error:
            mock_response.raise_for_status.side_effect = Exception("Download failed")

        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)

        # httpx is now in paystub_orchestrator
        return patch(
            "app.services.payroll_run.paystub_orchestrator.httpx.AsyncClient",
            return_value=mock_client,
        )

    return _patch


@pytest.fixture
def patch_remittance_service():
    """Patch RemittancePeriodService for testing."""
    def _patch(result: dict[str, Any] | None = None, raise_error: bool = False):
        mock_service = MagicMock()
        if raise_error:
            mock_service.find_or_create_remittance_period.side_effect = Exception("Remittance error")
        else:
            mock_service.find_or_create_remittance_period.return_value = result or {"id": "remit-123"}

        return patch(
            "app.services.payroll_run.run_operations.RemittancePeriodService",
            return_value=mock_service,
        )

    return _patch
