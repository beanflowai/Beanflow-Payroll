"""
API tests for employee tax claims endpoints.

Tests:
- GET /api/v1/employees/{employee_id}/tax-claims
- GET /api/v1/employees/{employee_id}/tax-claims/{tax_year}
- POST /api/v1/employees/{employee_id}/tax-claims
- PUT /api/v1/employees/{employee_id}/tax-claims/{tax_year}

Note: These are unit tests that mock the Supabase client and helper functions.
For integration tests that hit the real database, use a separate test suite.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from tests.api.conftest import TEST_USER_ID

# Use valid UUIDs for testing
TEST_COMPANY_UUID = "12345678-1234-1234-1234-123456789012"


# Helper to create async mock for get_user_company_id
def mock_get_company_id():
    """Create an async mock that returns the test company UUID."""
    async def _mock(*args, **kwargs):
        return TEST_COMPANY_UUID
    return _mock


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def sample_tax_claim() -> dict[str, Any]:
    """Sample tax claim data."""
    return {
        "id": str(uuid4()),
        "employee_id": str(uuid4()),
        "company_id": TEST_COMPANY_UUID,
        "user_id": TEST_USER_ID,
        "tax_year": 2025,
        "federal_bpa": 16129.0,
        "federal_additional_claims": 500.0,
        "provincial_bpa": 12747.0,
        "provincial_additional_claims": 300.0,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }


@pytest.fixture
def sample_employee_with_province() -> dict[str, Any]:
    """Sample employee data with province."""
    return {
        "id": str(uuid4()),
        "province_of_employment": "ON",
        "user_id": TEST_USER_ID,
        "company_id": TEST_COMPANY_UUID,
    }


def create_mock_supabase_for_tax_claims(
    employee_data: dict | None = None,
    tax_claims_data: list[dict] | None = None,
    single_claim_data: dict | None = None,
):
    """Create a mock Supabase client with configurable responses for tax claims tests."""
    mock = MagicMock()

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

        response = MagicMock()

        if table_name == "companies":
            response.data = [{"id": TEST_COMPANY_UUID}]
        elif table_name == "employees":
            response.data = [employee_data] if employee_data else []
        elif table_name == "employee_tax_claims":
            if single_claim_data:
                response.data = [single_claim_data]
            elif tax_claims_data:
                response.data = tax_claims_data
            else:
                response.data = []
        else:
            response.data = []
            response.count = 0

        builder.execute.return_value = response
        return builder

    mock.table.side_effect = table_side_effect
    return mock


# =============================================================================
# GET /employees/{employee_id}/tax-claims Tests
# =============================================================================


class TestGetTaxClaims:
    """Tests for GET /api/v1/employees/{employee_id}/tax-claims endpoint."""

    def test_get_tax_claims_success(
        self,
        client: TestClient,
        sample_employee_with_province: dict,
        sample_tax_claim: dict,
    ):
        """Successfully get tax claims for an employee."""
        employee_id = sample_employee_with_province["id"]
        sample_tax_claim["employee_id"] = employee_id

        mock_supabase = create_mock_supabase_for_tax_claims(
            employee_data=sample_employee_with_province,
            tax_claims_data=[sample_tax_claim],
        )

        with patch("app.api.v1.employees.get_supabase_client", return_value=mock_supabase):
            with patch("app.api.v1.employees.get_user_company_id", new=mock_get_company_id()):
                response = client.get(
                    f"/api/v1/employees/{employee_id}/tax-claims",
                    headers={"X-Company-Id": TEST_COMPANY_UUID},
                )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["tax_year"] == 2025

    def test_get_tax_claims_empty(
        self,
        client: TestClient,
        sample_employee_with_province: dict,
    ):
        """Get empty list when employee has no tax claims."""
        employee_id = sample_employee_with_province["id"]

        mock_supabase = create_mock_supabase_for_tax_claims(
            employee_data=sample_employee_with_province,
            tax_claims_data=[],
        )

        with patch("app.api.v1.employees.get_supabase_client", return_value=mock_supabase):
            with patch("app.api.v1.employees.get_user_company_id", new=mock_get_company_id()):
                response = client.get(
                    f"/api/v1/employees/{employee_id}/tax-claims",
                    headers={"X-Company-Id": TEST_COMPANY_UUID},
                )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_tax_claims_employee_not_found(self, client: TestClient):
        """Return 404 when employee doesn't exist."""
        employee_id = str(uuid4())

        mock_supabase = create_mock_supabase_for_tax_claims(
            employee_data=None,
        )

        with patch("app.api.v1.employees.get_supabase_client", return_value=mock_supabase):
            response = client.get(
                f"/api/v1/employees/{employee_id}/tax-claims",
                headers={"X-Company-Id": TEST_COMPANY_UUID},
            )

        assert response.status_code == 404

    def test_get_tax_claims_unauthorized(self, unauthenticated_client: TestClient):
        """Reject unauthenticated requests."""
        employee_id = str(uuid4())
        response = unauthenticated_client.get(
            f"/api/v1/employees/{employee_id}/tax-claims"
        )
        assert response.status_code == 401


# =============================================================================
# GET /employees/{employee_id}/tax-claims/{tax_year} Tests
# =============================================================================


class TestGetTaxClaimByYear:
    """Tests for GET /api/v1/employees/{employee_id}/tax-claims/{tax_year} endpoint."""

    def test_get_tax_claim_by_year_success(
        self,
        client: TestClient,
        sample_tax_claim: dict,
    ):
        """Successfully get tax claim for a specific year."""
        employee_id = sample_tax_claim["employee_id"]

        mock_supabase = create_mock_supabase_for_tax_claims(
            single_claim_data=sample_tax_claim,
        )

        with patch("app.api.v1.employees.get_supabase_client", return_value=mock_supabase):
            with patch("app.api.v1.employees.get_user_company_id", new=mock_get_company_id()):
                response = client.get(
                    f"/api/v1/employees/{employee_id}/tax-claims/2025",
                    headers={"X-Company-Id": TEST_COMPANY_UUID},
                )

        assert response.status_code == 200
        data = response.json()
        assert data["tax_year"] == 2025
        assert float(data["federal_bpa"]) == 16129.0
        assert float(data["provincial_bpa"]) == 12747.0

    def test_get_tax_claim_by_year_not_found(self, client: TestClient):
        """Return 404 when tax claim for year doesn't exist."""
        employee_id = str(uuid4())

        mock_supabase = create_mock_supabase_for_tax_claims(
            single_claim_data=None,
        )

        with patch("app.api.v1.employees.get_supabase_client", return_value=mock_supabase):
            response = client.get(
                f"/api/v1/employees/{employee_id}/tax-claims/2025",
                headers={"X-Company-Id": TEST_COMPANY_UUID},
            )

        assert response.status_code == 404


# =============================================================================
# POST /employees/{employee_id}/tax-claims Tests
# =============================================================================


class TestCreateTaxClaim:
    """Tests for POST /api/v1/employees/{employee_id}/tax-claims endpoint."""

    def test_create_tax_claim_success(
        self,
        client: TestClient,
        sample_employee_with_province: dict,
        sample_tax_claim: dict,
    ):
        """Successfully create a tax claim."""
        employee_id = sample_employee_with_province["id"]
        sample_tax_claim["employee_id"] = employee_id

        mock_supabase = create_mock_supabase_for_tax_claims(
            employee_data=sample_employee_with_province,
            single_claim_data=sample_tax_claim,
        )

        # Mock tax config functions
        with patch("app.api.v1.employees.get_supabase_client", return_value=mock_supabase):
            with patch("app.api.v1.employees.get_user_company_id", new=mock_get_company_id()):
                with patch("app.services.payroll.get_federal_config") as mock_federal:
                    with patch("app.services.payroll.get_province_config") as mock_province:
                        mock_federal.return_value = {"bpaf": 16129.0}
                        mock_province.return_value = {"bpa": 12747.0}

                        response = client.post(
                            f"/api/v1/employees/{employee_id}/tax-claims",
                            json={
                                "tax_year": 2025,
                                "federal_additional_claims": 500,
                                "provincial_additional_claims": 300,
                            },
                            headers={"X-Company-Id": TEST_COMPANY_UUID},
                        )

        assert response.status_code == 201
        data = response.json()
        assert data["tax_year"] == 2025

    def test_create_tax_claim_employee_not_found(self, client: TestClient):
        """Return 404 when employee doesn't exist."""
        employee_id = str(uuid4())

        mock_supabase = create_mock_supabase_for_tax_claims(
            employee_data=None,
        )

        with patch("app.api.v1.employees.get_supabase_client", return_value=mock_supabase):
            response = client.post(
                f"/api/v1/employees/{employee_id}/tax-claims",
                json={
                    "tax_year": 2025,
                    "federal_additional_claims": 0,
                    "provincial_additional_claims": 0,
                },
                headers={"X-Company-Id": TEST_COMPANY_UUID},
            )

        assert response.status_code == 404

    def test_create_tax_claim_invalid_year(self, client: TestClient):
        """Reject invalid tax year."""
        employee_id = str(uuid4())

        response = client.post(
            f"/api/v1/employees/{employee_id}/tax-claims",
            json={
                "tax_year": 1999,  # Too old
                "federal_additional_claims": 0,
                "provincial_additional_claims": 0,
            },
            headers={"X-Company-Id": TEST_COMPANY_UUID},
        )

        assert response.status_code == 422  # Validation error

    def test_create_tax_claim_negative_claims(self, client: TestClient):
        """Reject negative additional claims."""
        employee_id = str(uuid4())

        response = client.post(
            f"/api/v1/employees/{employee_id}/tax-claims",
            json={
                "tax_year": 2025,
                "federal_additional_claims": -100,  # Invalid
                "provincial_additional_claims": 0,
            },
            headers={"X-Company-Id": TEST_COMPANY_UUID},
        )

        assert response.status_code == 422


# =============================================================================
# PUT /employees/{employee_id}/tax-claims/{tax_year} Tests
# =============================================================================


class TestUpdateTaxClaim:
    """Tests for PUT /api/v1/employees/{employee_id}/tax-claims/{tax_year} endpoint."""

    def test_update_tax_claim_additional_claims(
        self,
        client: TestClient,
        sample_tax_claim: dict,
    ):
        """Successfully update additional claims."""
        employee_id = sample_tax_claim["employee_id"]
        updated_claim = sample_tax_claim.copy()
        updated_claim["federal_additional_claims"] = 1000.0

        mock_supabase = create_mock_supabase_for_tax_claims(
            single_claim_data=updated_claim,
        )

        with patch("app.api.v1.employees.get_supabase_client", return_value=mock_supabase):
            with patch("app.api.v1.employees.get_user_company_id", new=mock_get_company_id()):
                response = client.put(
                    f"/api/v1/employees/{employee_id}/tax-claims/2025",
                    json={
                        "federal_additional_claims": 1000,
                        "provincial_additional_claims": 500,
                    },
                    headers={"X-Company-Id": TEST_COMPANY_UUID},
                )

        assert response.status_code == 200
        data = response.json()
        assert float(data["federal_additional_claims"]) == 1000.0

    def test_update_tax_claim_with_bpa_recalculation(
        self,
        client: TestClient,
        sample_employee_with_province: dict,
        sample_tax_claim: dict,
    ):
        """Successfully update tax claim with BPA recalculation."""
        employee_id = sample_tax_claim["employee_id"]
        sample_employee_with_province["id"] = employee_id

        # Updated claim with new BPA values
        updated_claim = sample_tax_claim.copy()
        updated_claim["federal_bpa"] = 16500.0  # New federal BPA
        updated_claim["provincial_bpa"] = 13000.0  # New provincial BPA

        mock_supabase = create_mock_supabase_for_tax_claims(
            employee_data=sample_employee_with_province,
            single_claim_data=updated_claim,
        )

        with patch("app.api.v1.employees.get_supabase_client", return_value=mock_supabase):
            with patch("app.api.v1.employees.get_user_company_id", new=mock_get_company_id()):
                with patch("app.services.payroll.get_federal_config") as mock_federal:
                    with patch("app.services.payroll.get_province_config") as mock_province:
                        mock_federal.return_value = {"bpaf": 16500.0}
                        mock_province.return_value = {"bpa": 13000.0}

                        response = client.put(
                            f"/api/v1/employees/{employee_id}/tax-claims/2025",
                            json={
                                "federal_additional_claims": 500,
                                "provincial_additional_claims": 300,
                                "recalculate_bpa": True,
                            },
                            headers={"X-Company-Id": TEST_COMPANY_UUID},
                        )

        assert response.status_code == 200

    def test_update_tax_claim_not_found(self, client: TestClient):
        """Return 404 when tax claim doesn't exist."""
        employee_id = str(uuid4())

        mock_supabase = create_mock_supabase_for_tax_claims(
            single_claim_data=None,
        )

        with patch("app.api.v1.employees.get_supabase_client", return_value=mock_supabase):
            response = client.put(
                f"/api/v1/employees/{employee_id}/tax-claims/2025",
                json={
                    "federal_additional_claims": 500,
                },
                headers={"X-Company-Id": TEST_COMPANY_UUID},
            )

        assert response.status_code == 404

    def test_update_tax_claim_no_fields(self, client: TestClient):
        """Return 400 when no fields to update."""
        employee_id = str(uuid4())

        mock_supabase = create_mock_supabase_for_tax_claims()

        with patch("app.api.v1.employees.get_supabase_client", return_value=mock_supabase):
            with patch("app.api.v1.employees.get_user_company_id", new=mock_get_company_id()):
                response = client.put(
                    f"/api/v1/employees/{employee_id}/tax-claims/2025",
                    json={},  # No fields
                    headers={"X-Company-Id": TEST_COMPANY_UUID},
                )

        assert response.status_code == 400

    def test_update_tax_claim_negative_claims(self, client: TestClient):
        """Reject negative additional claims."""
        employee_id = str(uuid4())

        response = client.put(
            f"/api/v1/employees/{employee_id}/tax-claims/2025",
            json={
                "federal_additional_claims": -100,  # Invalid
            },
            headers={"X-Company-Id": TEST_COMPANY_UUID},
        )

        assert response.status_code == 422
