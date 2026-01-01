"""
Shared fixtures for API integration tests.

Provides:
- Mock authentication (overrides get_current_user)
- Mock Supabase client
- Mock payroll run service
- Test client with auth
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.main import app
from app.models.auth import UserResponse

# =============================================================================
# Test Data Constants
# =============================================================================

TEST_USER_ID = "test-user-id-12345"
TEST_COMPANY_ID = "test-company-id-67890"
TEST_USER_EMAIL = "test@example.com"


# =============================================================================
# Authentication Fixtures
# =============================================================================


@pytest.fixture
def mock_user() -> UserResponse:
    """Create a mock authenticated user."""
    return UserResponse(
        id=TEST_USER_ID,
        email=TEST_USER_EMAIL,
        full_name="Test User",
        avatar_url=None,
    )


@pytest.fixture
def mock_get_current_user(mock_user: UserResponse):
    """Override get_current_user dependency."""
    async def _override():
        return mock_user
    return _override


# =============================================================================
# Supabase Mock Fixtures
# =============================================================================


@pytest.fixture
def mock_supabase():
    """Create a mock Supabase client with chainable API."""
    mock = MagicMock()

    # Default empty response
    mock_response = MagicMock()
    mock_response.data = []
    mock_response.count = 0

    # Setup chainable table API
    def create_query_builder():
        builder = MagicMock()
        builder.select.return_value = builder
        builder.insert.return_value = builder
        builder.update.return_value = builder
        builder.delete.return_value = builder
        builder.eq.return_value = builder
        builder.neq.return_value = builder
        builder.order.return_value = builder
        builder.limit.return_value = builder
        builder.range.return_value = builder
        builder.single.return_value = builder
        builder.execute.return_value = mock_response
        return builder

    mock.table.return_value = create_query_builder()
    return mock


@pytest.fixture
def mock_supabase_with_company(mock_supabase):
    """Mock Supabase with a company result for the user."""
    company_response = MagicMock()
    company_response.data = [{"id": TEST_COMPANY_ID}]

    def table_side_effect(table_name: str):
        builder = MagicMock()
        builder.select.return_value = builder
        builder.insert.return_value = builder
        builder.update.return_value = builder
        builder.delete.return_value = builder
        builder.eq.return_value = builder
        builder.neq.return_value = builder
        builder.order.return_value = builder
        builder.limit.return_value = builder
        builder.range.return_value = builder
        builder.single.return_value = builder

        if table_name == "companies":
            builder.execute.return_value = company_response
        else:
            empty_response = MagicMock()
            empty_response.data = []
            empty_response.count = 0
            builder.execute.return_value = empty_response

        return builder

    mock_supabase.table.side_effect = table_side_effect
    return mock_supabase


# =============================================================================
# Test Client Fixtures
# =============================================================================


@pytest.fixture
def client(mock_get_current_user) -> TestClient:
    """Create test client with mocked authentication."""
    app.dependency_overrides[get_current_user] = mock_get_current_user
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def unauthenticated_client() -> TestClient:
    """Create test client without authentication."""
    app.dependency_overrides.clear()
    return TestClient(app)


# =============================================================================
# Payroll Run Service Mock Fixtures
# =============================================================================


@pytest.fixture
def mock_payroll_run_service():
    """Create a mock PayrollRunService."""
    service = MagicMock()

    # Configure async methods
    service.list_runs = AsyncMock(return_value={
        "runs": [],
        "total": 0,
    })
    service.get_run = AsyncMock(return_value=None)
    service.get_record = AsyncMock(return_value=None)
    service.get_run_records = AsyncMock(return_value=[])
    service.update_record = AsyncMock()
    service.create_or_get_run = AsyncMock()
    service.create_or_get_run_by_period_end = AsyncMock()
    service.recalculate_run = AsyncMock()
    service.finalize_run = AsyncMock()
    service.approve_run = AsyncMock()
    service.delete_run = AsyncMock()
    service.sync_employees = AsyncMock()
    service.add_employee_to_run = AsyncMock()
    service.remove_employee_from_run = AsyncMock()
    service.send_paystubs = AsyncMock()

    return service


@pytest.fixture
def mock_get_payroll_run_service(mock_payroll_run_service):
    """Create a factory function that returns the mock service."""
    def _factory(user_id: str, company_id: str):
        return mock_payroll_run_service
    return _factory


# =============================================================================
# Sample Data Fixtures
# =============================================================================


@pytest.fixture
def sample_payroll_run() -> dict[str, Any]:
    """Sample payroll run data."""
    return {
        "id": str(uuid4()),
        "pay_date": "2025-01-15",
        "period_start": "2025-01-01",
        "period_end": "2025-01-15",
        "status": "draft",
        "total_employees": 5,
        "total_gross": 25000.00,
        "total_cpp_employee": 750.00,
        "total_cpp_employer": 750.00,
        "total_ei_employee": 400.00,
        "total_ei_employer": 560.00,
        "total_federal_tax": 3000.00,
        "total_provincial_tax": 1500.00,
        "total_net_pay": 19350.00,
        "total_employer_cost": 26310.00,
        "user_id": TEST_USER_ID,
        "company_id": TEST_COMPANY_ID,
    }


@pytest.fixture
def sample_payroll_record() -> dict[str, Any]:
    """Sample payroll record data."""
    return {
        "id": str(uuid4()),
        "payroll_run_id": str(uuid4()),
        "employee_id": str(uuid4()),
        "gross_pay": 5000.00,
        "cpp_employee": 150.00,
        "cpp_employer": 150.00,
        "ei_employee": 80.00,
        "ei_employer": 112.00,
        "federal_tax": 600.00,
        "provincial_tax": 300.00,
        "net_pay": 3870.00,
        "input_data": {"regularHours": 80},
        "is_modified": False,
        "paystub_storage_key": None,
        "user_id": TEST_USER_ID,
        "company_id": TEST_COMPANY_ID,
    }


@pytest.fixture
def sample_employee() -> dict[str, Any]:
    """Sample employee data."""
    return {
        "id": str(uuid4()),
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "province_of_employment": "ON",
        "pay_frequency": "bi_weekly",
        "annual_salary": 60000.00,
        "hourly_rate": None,
        "federal_additional_claims": 0,
        "provincial_additional_claims": 0,
        "is_cpp_exempt": False,
        "is_ei_exempt": False,
        "cpp2_exempt": False,
        "hire_date": "2024-01-15",
        "user_id": TEST_USER_ID,
        "company_id": TEST_COMPANY_ID,
    }


# =============================================================================
# Calculation Request Fixtures
# =============================================================================


@pytest.fixture
def sample_calculation_request() -> dict[str, Any]:
    """Sample single employee calculation request."""
    return {
        "employee_id": "emp-001",
        "province": "ON",
        "pay_frequency": "bi_weekly",
        "gross_regular": "2500.00",
        "gross_overtime": "0",
        "holiday_pay": "0",
        "holiday_premium_pay": "0",
        "vacation_pay": "0",
        "other_earnings": "0",
        "federal_claim_amount": "16129",
        "provincial_claim_amount": "12399",
        "rrsp_per_period": "0",
        "union_dues_per_period": "0",
        "garnishments": "0",
        "other_deductions": "0",
        "ytd_gross": "0",
        "ytd_pensionable_earnings": "0",
        "ytd_insurable_earnings": "0",
        "ytd_cpp_base": "0",
        "ytd_cpp_additional": "0",
        "ytd_ei": "0",
        "is_cpp_exempt": False,
        "is_ei_exempt": False,
        "cpp2_exempt": False,
    }


@pytest.fixture
def sample_batch_calculation_request(sample_calculation_request) -> dict[str, Any]:
    """Sample batch calculation request."""
    emp2 = sample_calculation_request.copy()
    emp2["employee_id"] = "emp-002"
    emp2["province"] = "BC"
    emp2["gross_regular"] = "3000.00"

    return {
        "employees": [sample_calculation_request, emp2],
        "include_details": False,
    }
