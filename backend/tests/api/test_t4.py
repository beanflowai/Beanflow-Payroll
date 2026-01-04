"""
T4 API Endpoint Tests

Tests for T4 slip generation, listing, downloading, and CRA submission endpoints.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.core.supabase_client import get_supabase_client
from app.main import app
from app.models.auth import UserResponse
from app.models.t4 import (
    T4Status,
    T4ValidationError,
    T4ValidationResult,
    T4ValidationWarning,
)


# =============================================================================
# Test Constants
# =============================================================================

TEST_USER_ID = "test-user-id-12345"
TEST_COMPANY_ID = str(uuid4())
TEST_EMPLOYEE_ID = str(uuid4())
TEST_SLIP_ID = str(uuid4())
TEST_TAX_YEAR = 2025


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_user() -> UserResponse:
    """Create a mock authenticated user."""
    return UserResponse(
        id=TEST_USER_ID,
        email="test@example.com",
        full_name="Test User",
        avatar_url=None,
    )


@pytest.fixture
def mock_get_current_user(mock_user: UserResponse):
    """Override get_current_user dependency."""
    async def _override():
        return mock_user
    return _override


@pytest.fixture
def mock_supabase():
    """Create a mock Supabase client."""
    mock = MagicMock()
    return mock


@pytest.fixture
def client(mock_get_current_user, mock_supabase) -> TestClient:
    """Create test client with mocked dependencies."""
    app.dependency_overrides[get_current_user] = mock_get_current_user

    with patch("app.api.v1.t4.get_supabase_client", return_value=mock_supabase):
        yield TestClient(app)

    app.dependency_overrides.clear()


@pytest.fixture
def sample_slip_data() -> dict[str, Any]:
    """Sample T4 slip data from database."""
    return {
        "id": TEST_SLIP_ID,
        "employee_id": TEST_EMPLOYEE_ID,
        "status": "generated",
        "pdf_storage_key": "t4/2025/test-company/test-employee.pdf",
        "slip_data": {
            "employee_id": TEST_EMPLOYEE_ID,
            "tax_year": TEST_TAX_YEAR,
            "sin": "123456789",
            "employee_first_name": "John",
            "employee_last_name": "Doe",
            "employee_city": "Toronto",
            "employee_province": "ON",
            "employer_name": "Test Company Inc.",
            "employer_account_number": "123456789RP0001",
            "box_14_employment_income": "50000.00",
            "box_16_cpp_contributions": "3800.00",
            "box_17_cpp2_contributions": "500.00",
            "box_18_ei_premiums": "1049.12",
            "box_22_income_tax_deducted": "8500.00",
            "box_24_ei_insurable_earnings": "50000.00",
            "box_26_cpp_pensionable_earnings": "50000.00",
            "province_of_employment": "ON",
            "cpp_exempt": False,
            "ei_exempt": False,
        },
    }


@pytest.fixture
def sample_company_data() -> dict[str, Any]:
    """Sample company data."""
    return {
        "id": TEST_COMPANY_ID,
        "company_name": "Test Company Inc.",
        "payroll_account_number": "123456789RP0001",
        "province": "ON",
        "address_street": "123 Main St",
        "address_city": "Toronto",
        "address_postal_code": "M5V 1A1",
    }


@pytest.fixture
def sample_summary_data() -> dict[str, Any]:
    """Sample T4 summary data."""
    return {
        "id": str(uuid4()),
        "company_id": TEST_COMPANY_ID,
        "user_id": TEST_USER_ID,
        "tax_year": TEST_TAX_YEAR,
        "total_number_of_t4_slips": 5,
        "total_employment_income": "250000.00",
        "total_cpp_contributions": "19000.00",
        "total_cpp2_contributions": "2500.00",
        "total_ei_premiums": "5245.60",
        "total_income_tax_deducted": "42500.00",
        "total_union_dues": "1200.00",
        "total_cpp_employer": "19000.00",
        "total_ei_employer": "7343.84",
        "remittance_difference": "0.00",
        "status": "generated",
        "pdf_storage_key": "t4/summary/2025/test-company.pdf",
        "xml_storage_key": "t4/xml/2025/test-company.xml",
    }


# =============================================================================
# List T4 Slips Tests
# =============================================================================


class TestListT4Slips:
    """Tests for GET /api/v1/t4/slips/{company_id}/{tax_year}"""

    def test_list_t4_slips_success(
        self,
        mock_get_current_user,
        sample_slip_data,
    ):
        """Test listing T4 slips returns correct data."""
        mock_supabase = MagicMock()

        # Setup mock response
        mock_response = MagicMock()
        mock_response.data = [sample_slip_data]

        query_builder = MagicMock()
        query_builder.select.return_value = query_builder
        query_builder.eq.return_value = query_builder
        query_builder.order.return_value = query_builder
        query_builder.execute.return_value = mock_response

        mock_supabase.table.return_value = query_builder

        app.dependency_overrides[get_current_user] = mock_get_current_user

        with patch("app.api.v1.t4.get_supabase_client", return_value=mock_supabase):
            client = TestClient(app)
            response = client.get(f"/api/v1/t4/slips/{TEST_COMPANY_ID}/{TEST_TAX_YEAR}")

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["tax_year"] == TEST_TAX_YEAR
        assert data["total_count"] == 1
        assert len(data["slips"]) == 1
        assert data["slips"][0]["employee_name"] == "Doe, John"
        assert data["slips"][0]["status"] == "generated"
        assert data["slips"][0]["pdf_available"] is True

    def test_list_t4_slips_empty(self, mock_get_current_user):
        """Test listing T4 slips when none exist."""
        mock_supabase = MagicMock()

        mock_response = MagicMock()
        mock_response.data = []

        query_builder = MagicMock()
        query_builder.select.return_value = query_builder
        query_builder.eq.return_value = query_builder
        query_builder.order.return_value = query_builder
        query_builder.execute.return_value = mock_response

        mock_supabase.table.return_value = query_builder

        app.dependency_overrides[get_current_user] = mock_get_current_user

        with patch("app.api.v1.t4.get_supabase_client", return_value=mock_supabase):
            client = TestClient(app)
            response = client.get(f"/api/v1/t4/slips/{TEST_COMPANY_ID}/{TEST_TAX_YEAR}")

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 0
        assert data["slips"] == []

    def test_list_t4_slips_masks_sin(self, mock_get_current_user, sample_slip_data):
        """Test that SIN is properly masked in the response."""
        mock_supabase = MagicMock()

        mock_response = MagicMock()
        mock_response.data = [sample_slip_data]

        query_builder = MagicMock()
        query_builder.select.return_value = query_builder
        query_builder.eq.return_value = query_builder
        query_builder.order.return_value = query_builder
        query_builder.execute.return_value = mock_response

        mock_supabase.table.return_value = query_builder

        app.dependency_overrides[get_current_user] = mock_get_current_user

        with patch("app.api.v1.t4.get_supabase_client", return_value=mock_supabase):
            client = TestClient(app)
            response = client.get(f"/api/v1/t4/slips/{TEST_COMPANY_ID}/{TEST_TAX_YEAR}")

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        # SIN should be masked
        assert "***" in data["slips"][0]["sin_masked"]


# =============================================================================
# Generate T4 Slips Tests
# =============================================================================


class TestGenerateT4Slips:
    """Tests for POST /api/v1/t4/slips/{company_id}/{tax_year}/generate"""

    def test_generate_t4_slips_company_not_found(self, mock_get_current_user):
        """Test generation fails when company not found."""
        mock_supabase = MagicMock()

        # Mock aggregation service that returns no company
        with patch("app.api.v1.t4.get_supabase_client", return_value=mock_supabase), \
             patch("app.api.v1.t4.T4AggregationService") as mock_agg_cls, \
             patch("app.api.v1.t4.T4PDFGenerator"), \
             patch("app.api.v1.t4.get_t4_storage", side_effect=Exception("No storage")):

            mock_agg = MagicMock()
            mock_agg.get_company = AsyncMock(return_value=None)
            mock_agg_cls.return_value = mock_agg

            app.dependency_overrides[get_current_user] = mock_get_current_user
            client = TestClient(app)
            response = client.post(f"/api/v1/t4/slips/{TEST_COMPANY_ID}/{TEST_TAX_YEAR}/generate")

        app.dependency_overrides.clear()

        assert response.status_code == 404
        assert "Company not found" in response.json()["detail"]

    def test_generate_t4_slips_no_payroll_data(self, mock_get_current_user, sample_company_data):
        """Test generation with no payroll data returns success with zero slips."""
        mock_supabase = MagicMock()

        with patch("app.api.v1.t4.get_supabase_client", return_value=mock_supabase), \
             patch("app.api.v1.t4.T4AggregationService") as mock_agg_cls, \
             patch("app.api.v1.t4.T4PDFGenerator"), \
             patch("app.api.v1.t4.get_t4_storage", side_effect=Exception("No storage")):

            # Create mock company object
            mock_company = MagicMock()
            mock_company.company_name = "Test Company Inc."

            mock_agg = MagicMock()
            mock_agg.get_company = AsyncMock(return_value=mock_company)
            mock_agg.generate_all_t4_slips = AsyncMock(return_value=[])
            mock_agg_cls.return_value = mock_agg

            app.dependency_overrides[get_current_user] = mock_get_current_user
            client = TestClient(app)
            response = client.post(f"/api/v1/t4/slips/{TEST_COMPANY_ID}/{TEST_TAX_YEAR}/generate")

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["slips_generated"] == 0
        assert "No payroll data" in data["message"]


# =============================================================================
# Download T4 Slip Tests
# =============================================================================


class TestDownloadT4Slip:
    """Tests for GET /api/v1/t4/slips/{company_id}/{tax_year}/{employee_id}/download"""

    def test_download_t4_slip_not_found(self, mock_get_current_user):
        """Test download fails when slip not found."""
        mock_supabase = MagicMock()

        mock_response = MagicMock()
        mock_response.data = []

        query_builder = MagicMock()
        query_builder.select.return_value = query_builder
        query_builder.eq.return_value = query_builder
        query_builder.order.return_value = query_builder
        query_builder.limit.return_value = query_builder
        query_builder.execute.return_value = mock_response

        mock_supabase.table.return_value = query_builder

        app.dependency_overrides[get_current_user] = mock_get_current_user

        with patch("app.api.v1.t4.get_supabase_client", return_value=mock_supabase):
            client = TestClient(app)
            response = client.get(
                f"/api/v1/t4/slips/{TEST_COMPANY_ID}/{TEST_TAX_YEAR}/{TEST_EMPLOYEE_ID}/download"
            )

        app.dependency_overrides.clear()

        assert response.status_code == 404
        assert "T4 slip not found" in response.json()["detail"]

    def test_download_t4_slip_generates_on_the_fly(
        self,
        mock_get_current_user,
        sample_slip_data,
    ):
        """Test download generates PDF on-the-fly when not in storage."""
        mock_supabase = MagicMock()

        # Remove storage key to force on-the-fly generation
        slip_without_storage = sample_slip_data.copy()
        slip_without_storage["pdf_storage_key"] = None

        mock_response = MagicMock()
        mock_response.data = [slip_without_storage]

        query_builder = MagicMock()
        query_builder.select.return_value = query_builder
        query_builder.eq.return_value = query_builder
        query_builder.order.return_value = query_builder
        query_builder.limit.return_value = query_builder
        query_builder.execute.return_value = mock_response

        mock_supabase.table.return_value = query_builder

        app.dependency_overrides[get_current_user] = mock_get_current_user

        with patch("app.api.v1.t4.get_supabase_client", return_value=mock_supabase), \
             patch("app.api.v1.t4.T4PDFGenerator") as mock_pdf_cls:

            mock_pdf = MagicMock()
            mock_pdf.generate_t4_slip_pdf.return_value = b"%PDF-1.4 test content"
            mock_pdf_cls.return_value = mock_pdf

            client = TestClient(app)
            response = client.get(
                f"/api/v1/t4/slips/{TEST_COMPANY_ID}/{TEST_TAX_YEAR}/{TEST_EMPLOYEE_ID}/download"
            )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "T4_2025_Doe.pdf" in response.headers["content-disposition"]

    def test_download_t4_slip_no_data_available(self, mock_get_current_user):
        """Test download fails when no slip data available for on-the-fly generation."""
        mock_supabase = MagicMock()

        # Slip record with no storage key and no slip_data
        slip_no_data = {
            "id": TEST_SLIP_ID,
            "pdf_storage_key": None,
            "slip_data": None,
        }

        mock_response = MagicMock()
        mock_response.data = [slip_no_data]

        query_builder = MagicMock()
        query_builder.select.return_value = query_builder
        query_builder.eq.return_value = query_builder
        query_builder.order.return_value = query_builder
        query_builder.limit.return_value = query_builder
        query_builder.execute.return_value = mock_response

        mock_supabase.table.return_value = query_builder

        app.dependency_overrides[get_current_user] = mock_get_current_user

        with patch("app.api.v1.t4.get_supabase_client", return_value=mock_supabase):
            client = TestClient(app)
            response = client.get(
                f"/api/v1/t4/slips/{TEST_COMPANY_ID}/{TEST_TAX_YEAR}/{TEST_EMPLOYEE_ID}/download"
            )

        app.dependency_overrides.clear()

        assert response.status_code == 404
        assert "T4 data not available" in response.json()["detail"]


# =============================================================================
# T4 Summary Tests
# =============================================================================


class TestGetT4Summary:
    """Tests for GET /api/v1/t4/summary/{company_id}/{tax_year}"""

    def test_get_t4_summary_not_found(self, mock_get_current_user):
        """Test get summary returns 404 when not generated."""
        mock_supabase = MagicMock()

        mock_response = MagicMock()
        mock_response.data = []

        query_builder = MagicMock()
        query_builder.select.return_value = query_builder
        query_builder.eq.return_value = query_builder
        query_builder.limit.return_value = query_builder
        query_builder.execute.return_value = mock_response

        mock_supabase.table.return_value = query_builder

        app.dependency_overrides[get_current_user] = mock_get_current_user

        with patch("app.api.v1.t4.get_supabase_client", return_value=mock_supabase):
            client = TestClient(app)
            response = client.get(f"/api/v1/t4/summary/{TEST_COMPANY_ID}/{TEST_TAX_YEAR}")

        app.dependency_overrides.clear()

        assert response.status_code == 404
        assert "T4 Summary not found" in response.json()["detail"]

    def test_get_t4_summary_success(
        self,
        mock_get_current_user,
        sample_summary_data,
        sample_company_data,
    ):
        """Test get summary returns correct data."""
        mock_supabase = MagicMock()

        summary_response = MagicMock()
        summary_response.data = [sample_summary_data]

        company_response = MagicMock()
        company_response.data = [sample_company_data]

        call_count = 0

        def table_side_effect(table_name):
            nonlocal call_count
            query_builder = MagicMock()
            query_builder.select.return_value = query_builder
            query_builder.eq.return_value = query_builder
            query_builder.limit.return_value = query_builder

            if table_name == "t4_summaries":
                query_builder.execute.return_value = summary_response
            elif table_name == "companies":
                query_builder.execute.return_value = company_response
            else:
                empty_response = MagicMock()
                empty_response.data = []
                query_builder.execute.return_value = empty_response

            return query_builder

        mock_supabase.table.side_effect = table_side_effect

        app.dependency_overrides[get_current_user] = mock_get_current_user

        with patch("app.api.v1.t4.get_supabase_client", return_value=mock_supabase):
            client = TestClient(app)
            response = client.get(f"/api/v1/t4/summary/{TEST_COMPANY_ID}/{TEST_TAX_YEAR}")

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["summary"]["tax_year"] == TEST_TAX_YEAR
        assert data["summary"]["total_number_of_t4_slips"] == 5


# =============================================================================
# Generate T4 Summary Tests
# =============================================================================


class TestGenerateT4Summary:
    """Tests for POST /api/v1/t4/summary/{company_id}/{tax_year}/generate"""

    def test_generate_t4_summary_company_not_found(self, mock_get_current_user):
        """Test summary generation fails when company not found."""
        mock_supabase = MagicMock()

        with patch("app.api.v1.t4.get_supabase_client", return_value=mock_supabase), \
             patch("app.api.v1.t4.T4AggregationService") as mock_agg_cls, \
             patch("app.api.v1.t4.T4PDFGenerator"), \
             patch("app.api.v1.t4.T4XMLGenerator"), \
             patch("app.api.v1.t4.get_t4_storage", side_effect=Exception("No storage")):

            mock_agg = MagicMock()
            mock_agg.get_company = AsyncMock(return_value=None)
            mock_agg_cls.return_value = mock_agg

            app.dependency_overrides[get_current_user] = mock_get_current_user
            client = TestClient(app)
            response = client.post(f"/api/v1/t4/summary/{TEST_COMPANY_ID}/{TEST_TAX_YEAR}/generate")

        app.dependency_overrides.clear()

        assert response.status_code == 404
        assert "Company not found" in response.json()["detail"]

    def test_generate_t4_summary_no_slips(self, mock_get_current_user):
        """Test summary generation when no slips exist."""
        mock_supabase = MagicMock()

        with patch("app.api.v1.t4.get_supabase_client", return_value=mock_supabase), \
             patch("app.api.v1.t4.T4AggregationService") as mock_agg_cls, \
             patch("app.api.v1.t4.T4PDFGenerator"), \
             patch("app.api.v1.t4.T4XMLGenerator"), \
             patch("app.api.v1.t4.get_t4_storage", side_effect=Exception("No storage")):

            mock_company = MagicMock()
            mock_company.company_name = "Test Company"

            mock_agg = MagicMock()
            mock_agg.get_company = AsyncMock(return_value=mock_company)
            mock_agg.generate_all_t4_slips = AsyncMock(return_value=[])
            mock_agg_cls.return_value = mock_agg

            app.dependency_overrides[get_current_user] = mock_get_current_user
            client = TestClient(app)
            response = client.post(f"/api/v1/t4/summary/{TEST_COMPANY_ID}/{TEST_TAX_YEAR}/generate")

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "No T4 slips found" in data["message"]


# =============================================================================
# Download T4 Summary PDF Tests
# =============================================================================


class TestDownloadT4SummaryPdf:
    """Tests for GET /api/v1/t4/summary/{company_id}/{tax_year}/download-pdf"""

    def test_download_summary_pdf_not_found(self, mock_get_current_user):
        """Test download fails when summary not found."""
        mock_supabase = MagicMock()

        mock_response = MagicMock()
        mock_response.data = None

        query_builder = MagicMock()
        query_builder.select.return_value = query_builder
        query_builder.eq.return_value = query_builder
        query_builder.maybe_single.return_value = query_builder
        query_builder.execute.return_value = mock_response

        mock_supabase.table.return_value = query_builder

        app.dependency_overrides[get_current_user] = mock_get_current_user

        with patch("app.api.v1.t4.get_supabase_client", return_value=mock_supabase):
            client = TestClient(app)
            response = client.get(f"/api/v1/t4/summary/{TEST_COMPANY_ID}/{TEST_TAX_YEAR}/download-pdf")

        app.dependency_overrides.clear()

        assert response.status_code == 404

    def test_download_summary_pdf_not_available(self, mock_get_current_user):
        """Test download fails when PDF not available."""
        mock_supabase = MagicMock()

        mock_response = MagicMock()
        mock_response.data = {"pdf_storage_key": None}

        query_builder = MagicMock()
        query_builder.select.return_value = query_builder
        query_builder.eq.return_value = query_builder
        query_builder.maybe_single.return_value = query_builder
        query_builder.execute.return_value = mock_response

        mock_supabase.table.return_value = query_builder

        app.dependency_overrides[get_current_user] = mock_get_current_user

        with patch("app.api.v1.t4.get_supabase_client", return_value=mock_supabase):
            client = TestClient(app)
            response = client.get(f"/api/v1/t4/summary/{TEST_COMPANY_ID}/{TEST_TAX_YEAR}/download-pdf")

        app.dependency_overrides.clear()

        assert response.status_code == 404
        assert "PDF not available" in response.json()["detail"]


# =============================================================================
# Download T4 XML Tests
# =============================================================================


class TestDownloadT4Xml:
    """Tests for GET /api/v1/t4/summary/{company_id}/{tax_year}/download-xml"""

    def test_download_xml_not_found(self, mock_get_current_user):
        """Test download fails when summary not found."""
        mock_supabase = MagicMock()

        mock_response = MagicMock()
        mock_response.data = None

        query_builder = MagicMock()
        query_builder.select.return_value = query_builder
        query_builder.eq.return_value = query_builder
        query_builder.maybe_single.return_value = query_builder
        query_builder.execute.return_value = mock_response

        mock_supabase.table.return_value = query_builder

        app.dependency_overrides[get_current_user] = mock_get_current_user

        with patch("app.api.v1.t4.get_supabase_client", return_value=mock_supabase):
            client = TestClient(app)
            response = client.get(f"/api/v1/t4/summary/{TEST_COMPANY_ID}/{TEST_TAX_YEAR}/download-xml")

        app.dependency_overrides.clear()

        assert response.status_code == 404

    def test_download_xml_not_available(self, mock_get_current_user):
        """Test download fails when XML not available."""
        mock_supabase = MagicMock()

        mock_response = MagicMock()
        mock_response.data = {"xml_storage_key": None}

        query_builder = MagicMock()
        query_builder.select.return_value = query_builder
        query_builder.eq.return_value = query_builder
        query_builder.maybe_single.return_value = query_builder
        query_builder.execute.return_value = mock_response

        mock_supabase.table.return_value = query_builder

        app.dependency_overrides[get_current_user] = mock_get_current_user

        with patch("app.api.v1.t4.get_supabase_client", return_value=mock_supabase):
            client = TestClient(app)
            response = client.get(f"/api/v1/t4/summary/{TEST_COMPANY_ID}/{TEST_TAX_YEAR}/download-xml")

        app.dependency_overrides.clear()

        assert response.status_code == 404
        assert "XML not available" in response.json()["detail"]


# =============================================================================
# Validate T4 XML Tests
# =============================================================================


class TestValidateT4Xml:
    """Tests for POST /api/v1/t4/summary/{company_id}/{tax_year}/validate"""

    def test_validate_xml_summary_not_found(self, mock_get_current_user):
        """Test validation fails when summary not found."""
        mock_supabase = MagicMock()

        mock_response = MagicMock()
        mock_response.data = None

        query_builder = MagicMock()
        query_builder.select.return_value = query_builder
        query_builder.eq.return_value = query_builder
        query_builder.maybe_single.return_value = query_builder
        query_builder.execute.return_value = mock_response

        mock_supabase.table.return_value = query_builder

        app.dependency_overrides[get_current_user] = mock_get_current_user

        with patch("app.api.v1.t4.get_supabase_client", return_value=mock_supabase):
            client = TestClient(app)
            response = client.post(f"/api/v1/t4/summary/{TEST_COMPANY_ID}/{TEST_TAX_YEAR}/validate")

        app.dependency_overrides.clear()

        assert response.status_code == 404
        assert "T4 Summary not found" in response.json()["detail"]

    def test_validate_xml_not_available(self, mock_get_current_user):
        """Test validation fails when XML not available."""
        mock_supabase = MagicMock()

        mock_response = MagicMock()
        mock_response.data = {"xml_storage_key": None, "status": "generated"}

        query_builder = MagicMock()
        query_builder.select.return_value = query_builder
        query_builder.eq.return_value = query_builder
        query_builder.maybe_single.return_value = query_builder
        query_builder.execute.return_value = mock_response

        mock_supabase.table.return_value = query_builder

        app.dependency_overrides[get_current_user] = mock_get_current_user

        with patch("app.api.v1.t4.get_supabase_client", return_value=mock_supabase):
            client = TestClient(app)
            response = client.post(f"/api/v1/t4/summary/{TEST_COMPANY_ID}/{TEST_TAX_YEAR}/validate")

        app.dependency_overrides.clear()

        assert response.status_code == 404
        assert "T4 XML not available" in response.json()["detail"]

    def test_validate_xml_success(self, mock_get_current_user):
        """Test successful XML validation."""
        mock_supabase = MagicMock()

        mock_response = MagicMock()
        mock_response.data = {
            "xml_storage_key": "t4/xml/2025/test.xml",
            "status": "generated",
        }

        query_builder = MagicMock()
        query_builder.select.return_value = query_builder
        query_builder.eq.return_value = query_builder
        query_builder.maybe_single.return_value = query_builder
        query_builder.execute.return_value = mock_response

        mock_supabase.table.return_value = query_builder

        mock_storage = MagicMock()
        mock_storage.get_file_content = AsyncMock(return_value=b"<xml>test</xml>")

        mock_validation_result = T4ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
        )

        app.dependency_overrides[get_current_user] = mock_get_current_user

        with patch("app.api.v1.t4.get_supabase_client", return_value=mock_supabase), \
             patch("app.api.v1.t4.get_t4_storage", return_value=mock_storage), \
             patch("app.api.v1.t4.T4XMLValidator") as mock_validator_cls:

            mock_validator = MagicMock()
            mock_validator.validate.return_value = mock_validation_result
            mock_validator_cls.return_value = mock_validator

            client = TestClient(app)
            response = client.post(f"/api/v1/t4/summary/{TEST_COMPANY_ID}/{TEST_TAX_YEAR}/validate")

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["validation"]["is_valid"] is True


# =============================================================================
# Record T4 Submission Tests
# =============================================================================


class TestRecordT4Submission:
    """Tests for POST /api/v1/t4/summary/{company_id}/{tax_year}/record-submission"""

    def test_record_submission_summary_not_found(self, mock_get_current_user):
        """Test recording fails when summary not found."""
        mock_supabase = MagicMock()

        mock_response = MagicMock()
        mock_response.data = None

        query_builder = MagicMock()
        query_builder.select.return_value = query_builder
        query_builder.eq.return_value = query_builder
        query_builder.maybe_single.return_value = query_builder
        query_builder.execute.return_value = mock_response

        mock_supabase.table.return_value = query_builder

        app.dependency_overrides[get_current_user] = mock_get_current_user

        with patch("app.api.v1.t4.get_supabase_client", return_value=mock_supabase):
            client = TestClient(app)
            response = client.post(
                f"/api/v1/t4/summary/{TEST_COMPANY_ID}/{TEST_TAX_YEAR}/record-submission",
                json={"confirmation_number": "CRA123456789"},
            )

        app.dependency_overrides.clear()

        assert response.status_code == 404

    def test_record_submission_already_filed(self, mock_get_current_user):
        """Test recording fails when already filed."""
        mock_supabase = MagicMock()

        mock_response = MagicMock()
        mock_response.data = {
            "id": str(uuid4()),
            "status": "filed",
            "xml_storage_key": "t4/xml/2025/test.xml",
        }

        query_builder = MagicMock()
        query_builder.select.return_value = query_builder
        query_builder.eq.return_value = query_builder
        query_builder.maybe_single.return_value = query_builder
        query_builder.execute.return_value = mock_response

        mock_supabase.table.return_value = query_builder

        app.dependency_overrides[get_current_user] = mock_get_current_user

        with patch("app.api.v1.t4.get_supabase_client", return_value=mock_supabase):
            client = TestClient(app)
            response = client.post(
                f"/api/v1/t4/summary/{TEST_COMPANY_ID}/{TEST_TAX_YEAR}/record-submission",
                json={"confirmation_number": "CRA123456789"},
            )

        app.dependency_overrides.clear()

        assert response.status_code == 400
        assert "already been filed" in response.json()["detail"]

    def test_record_submission_not_generated(self, mock_get_current_user):
        """Test recording fails when not in generated status."""
        mock_supabase = MagicMock()

        mock_response = MagicMock()
        mock_response.data = {
            "id": str(uuid4()),
            "status": "draft",
            "xml_storage_key": None,
        }

        query_builder = MagicMock()
        query_builder.select.return_value = query_builder
        query_builder.eq.return_value = query_builder
        query_builder.maybe_single.return_value = query_builder
        query_builder.execute.return_value = mock_response

        mock_supabase.table.return_value = query_builder

        app.dependency_overrides[get_current_user] = mock_get_current_user

        with patch("app.api.v1.t4.get_supabase_client", return_value=mock_supabase):
            client = TestClient(app)
            response = client.post(
                f"/api/v1/t4/summary/{TEST_COMPANY_ID}/{TEST_TAX_YEAR}/record-submission",
                json={"confirmation_number": "CRA123456789"},
            )

        app.dependency_overrides.clear()

        assert response.status_code == 400
        assert "generated" in response.json()["detail"]

    def test_record_submission_empty_confirmation(self, mock_get_current_user):
        """Test recording fails with empty confirmation number."""
        mock_supabase = MagicMock()

        mock_response = MagicMock()
        mock_response.data = {
            "id": str(uuid4()),
            "status": "generated",
            "xml_storage_key": "t4/xml/2025/test.xml",
        }

        query_builder = MagicMock()
        query_builder.select.return_value = query_builder
        query_builder.eq.return_value = query_builder
        query_builder.maybe_single.return_value = query_builder
        query_builder.execute.return_value = mock_response

        mock_supabase.table.return_value = query_builder

        app.dependency_overrides[get_current_user] = mock_get_current_user

        with patch("app.api.v1.t4.get_supabase_client", return_value=mock_supabase):
            client = TestClient(app)
            response = client.post(
                f"/api/v1/t4/summary/{TEST_COMPANY_ID}/{TEST_TAX_YEAR}/record-submission",
                json={"confirmation_number": "   "},
            )

        app.dependency_overrides.clear()

        assert response.status_code == 400
        assert "cannot be empty" in response.json()["detail"]

    def test_record_submission_no_xml_key(self, mock_get_current_user):
        """Test recording fails when XML not generated."""
        mock_supabase = MagicMock()

        mock_response = MagicMock()
        mock_response.data = {
            "id": str(uuid4()),
            "status": "generated",
            "xml_storage_key": None,
        }

        query_builder = MagicMock()
        query_builder.select.return_value = query_builder
        query_builder.eq.return_value = query_builder
        query_builder.maybe_single.return_value = query_builder
        query_builder.execute.return_value = mock_response

        mock_supabase.table.return_value = query_builder

        app.dependency_overrides[get_current_user] = mock_get_current_user

        with patch("app.api.v1.t4.get_supabase_client", return_value=mock_supabase):
            client = TestClient(app)
            response = client.post(
                f"/api/v1/t4/summary/{TEST_COMPANY_ID}/{TEST_TAX_YEAR}/record-submission",
                json={"confirmation_number": "CRA123"},
            )

        app.dependency_overrides.clear()

        assert response.status_code == 400
        assert "XML file must be generated" in response.json()["detail"]

    def test_record_submission_success(self, mock_get_current_user, sample_company_data):
        """Test successful submission recording."""
        mock_supabase = MagicMock()
        summary_id = str(uuid4())

        # First call: get summary
        mock_get_response = MagicMock()
        mock_get_response.data = {
            "id": summary_id,
            "status": "generated",
            "xml_storage_key": "t4/xml/2025/test.xml",
        }

        # Second call: get updated summary
        mock_updated_response = MagicMock()
        mock_updated_response.data = {
            "id": summary_id,
            "company_id": TEST_COMPANY_ID,
            "user_id": TEST_USER_ID,
            "status": "filed",
            "cra_confirmation_number": "CRA123456",
            "submitted_at": "2025-01-15T10:00:00Z",
            "tax_year": TEST_TAX_YEAR,
            "total_number_of_t4_slips": 5,
        }

        # Third call: get company
        mock_company_response = MagicMock()
        mock_company_response.data = sample_company_data

        call_count = [0]

        def table_side_effect(table_name):
            nonlocal call_count
            query_builder = MagicMock()
            query_builder.select.return_value = query_builder
            query_builder.eq.return_value = query_builder
            query_builder.maybe_single.return_value = query_builder

            if table_name == "t4_summaries":
                query_builder.execute.return_value = [mock_get_response, mock_updated_response, mock_updated_response][min(call_count[0], 2)]
                call_count[0] += 1
            elif table_name == "companies":
                query_builder.execute.return_value = mock_company_response

            return query_builder

        mock_supabase.table.side_effect = table_side_effect

        # Mock update response
        update_builder = MagicMock()
        update_builder.execute.return_value = MagicMock(data=[{"id": summary_id}])
        mock_supabase.table.return_value.update.return_value.eq.return_value = update_builder

        app.dependency_overrides[get_current_user] = mock_get_current_user

        with patch("app.api.v1.t4.get_supabase_client", return_value=mock_supabase):
            client = TestClient(app)
            response = client.post(
                f"/api/v1/t4/summary/{TEST_COMPANY_ID}/{TEST_TAX_YEAR}/record-submission",
                json={"confirmation_number": "CRA123456", "submission_notes": "Submitted via portal"},
            )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["summary"]["status"] == "filed"


class TestGenerateT4SlipsSuccess:
    """Tests for successful T4 slip generation."""

    def test_generate_t4_slips_with_existing_skip(self, mock_get_current_user):
        """Test generation skips existing slips when not regenerating."""
        from app.models.t4 import T4SlipData

        mock_supabase = MagicMock()

        mock_company = MagicMock()
        mock_company.company_name = "Test Company"

        mock_slip = T4SlipData(
            employee_id=UUID(TEST_EMPLOYEE_ID),
            tax_year=TEST_TAX_YEAR,
            sin="123456789",
            employee_first_name="John",
            employee_last_name="Doe",
            employer_name="Test Company",
            employer_account_number="123456789RP0001",
            province_of_employment="ON",
            box_14_employment_income=Decimal("50000.00"),
            box_22_income_tax_deducted=Decimal("8500.00"),
        )

        with patch("app.api.v1.t4.get_supabase_client", return_value=mock_supabase), \
             patch("app.api.v1.t4.T4AggregationService") as mock_agg_cls, \
             patch("app.api.v1.t4.T4PDFGenerator") as mock_pdf_cls, \
             patch("app.api.v1.t4.get_t4_storage", side_effect=Exception("No storage")):

            mock_agg = MagicMock()
            mock_agg.get_company = AsyncMock(return_value=mock_company)
            mock_agg.generate_all_t4_slips = AsyncMock(return_value=[mock_slip])
            mock_agg_cls.return_value = mock_agg

            # Mock existing slip check - returns existing slip
            mock_existing_response = MagicMock()
            mock_existing_response.data = [{"id": TEST_SLIP_ID}]

            query_builder = MagicMock()
            query_builder.select.return_value = query_builder
            query_builder.eq.return_value = query_builder
            query_builder.limit.return_value = query_builder
            query_builder.execute.return_value = mock_existing_response
            mock_supabase.table.return_value = query_builder

            app.dependency_overrides[get_current_user] = mock_get_current_user
            client = TestClient(app)
            response = client.post(
                f"/api/v1/t4/slips/{TEST_COMPANY_ID}/{TEST_TAX_YEAR}/generate",
                json={"tax_year": TEST_TAX_YEAR, "regenerate": False},
            )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["slips_generated"] == 0
        assert data["slips_skipped"] == 1

    def test_generate_t4_slips_with_regenerate(self, mock_get_current_user):
        """Test regeneration overwrites existing slips."""
        from app.models.t4 import T4SlipData

        mock_supabase = MagicMock()

        mock_company = MagicMock()
        mock_company.company_name = "Test Company"

        mock_slip = T4SlipData(
            employee_id=UUID(TEST_EMPLOYEE_ID),
            tax_year=TEST_TAX_YEAR,
            sin="123456789",
            employee_first_name="John",
            employee_last_name="Doe",
            employer_name="Test Company",
            employer_account_number="123456789RP0001",
            province_of_employment="ON",
            box_14_employment_income=Decimal("50000.00"),
            box_22_income_tax_deducted=Decimal("8500.00"),
        )

        mock_pdf = MagicMock()
        mock_pdf.generate_t4_slip_pdf.return_value = b"%PDF-1.4 test"

        with patch("app.api.v1.t4.get_supabase_client", return_value=mock_supabase), \
             patch("app.api.v1.t4.T4AggregationService") as mock_agg_cls, \
             patch("app.api.v1.t4.T4PDFGenerator", return_value=mock_pdf), \
             patch("app.api.v1.t4.get_t4_storage", side_effect=Exception("No storage")):

            mock_agg = MagicMock()
            mock_agg.get_company = AsyncMock(return_value=mock_company)
            mock_agg.generate_all_t4_slips = AsyncMock(return_value=[mock_slip])
            mock_agg_cls.return_value = mock_agg

            # Mock existing slip check - returns existing slip
            mock_existing_response = MagicMock()
            mock_existing_response.data = [{"id": TEST_SLIP_ID}]

            # Mock update response
            query_builder = MagicMock()
            query_builder.select.return_value = query_builder
            query_builder.eq.return_value = query_builder
            query_builder.limit.return_value = query_builder
            query_builder.execute.return_value = mock_existing_response

            update_builder = MagicMock()
            update_builder.execute.return_value = MagicMock(data=[{"id": TEST_SLIP_ID}])

            call_count = [0]

            def table_side_effect(table_name):
                nonlocal call_count
                if call_count[0] == 0:
                    # First call is to check existing
                    call_count[0] += 1
                    return query_builder
                else:
                    # Second call is to update
                    return update_builder

            mock_supabase.table.side_effect = table_side_effect

            app.dependency_overrides[get_current_user] = mock_get_current_user
            client = TestClient(app)
            response = client.post(
                f"/api/v1/t4/slips/{TEST_COMPANY_ID}/{TEST_TAX_YEAR}/generate",
                json={"tax_year": TEST_TAX_YEAR, "regenerate": True, "employee_ids": [TEST_EMPLOYEE_ID]},
            )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["slips_generated"] == 1
        assert data["slips_skipped"] == 0


class TestDownloadT4SlipStoragePath:
    """Tests for T4 slip download from storage."""

    def test_download_from_storage(self, mock_get_current_user):
        """Test successful download from storage."""
        mock_supabase = MagicMock()

        slip_data = {
            "id": TEST_SLIP_ID,
            "pdf_storage_key": "t4/2025/test.pdf",
            "slip_data": {"employee_last_name": "Doe"},
        }

        mock_response = MagicMock()
        mock_response.data = [slip_data]

        query_builder = MagicMock()
        query_builder.select.return_value = query_builder
        query_builder.eq.return_value = query_builder
        query_builder.order.return_value = query_builder
        query_builder.limit.return_value = query_builder
        query_builder.execute.return_value = mock_response

        mock_supabase.table.return_value = query_builder

        mock_storage = MagicMock()
        mock_storage.get_file_content = AsyncMock(return_value=b"%PDF-1.4 test content")

        app.dependency_overrides[get_current_user] = mock_get_current_user

        with patch("app.api.v1.t4.get_supabase_client", return_value=mock_supabase), \
             patch("app.api.v1.t4.get_t4_storage", return_value=mock_storage):
            client = TestClient(app)
            response = client.get(
                f"/api/v1/t4/slips/{TEST_COMPANY_ID}/{TEST_TAX_YEAR}/{TEST_EMPLOYEE_ID}/download"
            )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    def test_download_pdf_generation_error(self, mock_get_current_user):
        """Test download when PDF generation fails."""
        mock_supabase = MagicMock()

        slip_data = {
            "id": TEST_SLIP_ID,
            "pdf_storage_key": None,
            "slip_data": {
                "employee_id": TEST_EMPLOYEE_ID,
                "tax_year": TEST_TAX_YEAR,
                "sin": "123456789",
                "employee_first_name": "John",
                "employee_last_name": "Doe",
                "employer_name": "Test Company",
                "employer_account_number": "123456789RP0001",
                "box_14_employment_income": "50000.00",
            },
        }

        mock_response = MagicMock()
        mock_response.data = [slip_data]

        query_builder = MagicMock()
        query_builder.select.return_value = query_builder
        query_builder.eq.return_value = query_builder
        query_builder.order.return_value = query_builder
        query_builder.limit.return_value = query_builder
        query_builder.execute.return_value = mock_response

        mock_supabase.table.return_value = query_builder

        with patch("app.api.v1.t4.get_supabase_client", return_value=mock_supabase), \
             patch("app.api.v1.t4.T4PDFGenerator") as mock_pdf_cls:

            mock_pdf = MagicMock()
            mock_pdf.generate_t4_slip_pdf.side_effect = Exception("PDF generation failed")
            mock_pdf_cls.return_value = mock_pdf

            app.dependency_overrides[get_current_user] = mock_get_current_user
            client = TestClient(app)
            response = client.get(
                f"/api/v1/t4/slips/{TEST_COMPANY_ID}/{TEST_TAX_YEAR}/{TEST_EMPLOYEE_ID}/download"
            )

        app.dependency_overrides.clear()

        assert response.status_code == 500
        assert "Failed to generate" in response.json()["detail"]


class TestDownloadT4SummaryPdfSuccess:
    """Tests for successful T4 summary PDF download."""

    def test_download_summary_pdf_success(self, mock_get_current_user):
        """Test successful summary PDF download."""
        mock_supabase = MagicMock()

        mock_response = MagicMock()
        mock_response.data = {"pdf_storage_key": "t4/summary/2025/test.pdf"}

        query_builder = MagicMock()
        query_builder.select.return_value = query_builder
        query_builder.eq.return_value = query_builder
        query_builder.maybe_single.return_value = query_builder
        query_builder.execute.return_value = mock_response

        mock_supabase.table.return_value = query_builder

        mock_storage = MagicMock()
        mock_storage.get_file_content = AsyncMock(return_value=b"%PDF-1.4 summary")

        app.dependency_overrides[get_current_user] = mock_get_current_user

        with patch("app.api.v1.t4.get_supabase_client", return_value=mock_supabase), \
             patch("app.api.v1.t4.get_t4_storage", return_value=mock_storage):
            client = TestClient(app)
            response = client.get(
                f"/api/v1/t4/summary/{TEST_COMPANY_ID}/{TEST_TAX_YEAR}/download-pdf"
            )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "T4_Summary_2025.pdf" in response.headers["content-disposition"]


class TestDownloadT4XmlSuccess:
    """Tests for successful T4 XML download."""

    def test_download_xml_success(self, mock_get_current_user):
        """Test successful XML download."""
        mock_supabase = MagicMock()

        mock_response = MagicMock()
        mock_response.data = {"xml_storage_key": "t4/xml/2025/test.xml"}

        query_builder = MagicMock()
        query_builder.select.return_value = query_builder
        query_builder.eq.return_value = query_builder
        query_builder.maybe_single.return_value = query_builder
        query_builder.execute.return_value = mock_response

        mock_supabase.table.return_value = query_builder

        # Mock company query
        mock_company_response = MagicMock()
        mock_company_response.data = {"payroll_account_number": "123456789RP0001"}

        company_builder = MagicMock()
        company_builder.select.return_value = company_builder
        company_builder.eq.return_value = company_builder
        company_builder.maybe_single.return_value = company_builder
        company_builder.execute.return_value = mock_company_response

        call_count = [0]

        def table_side_effect(table_name):
            nonlocal call_count
            call_count[0] += 1
            if call_count[0] == 1:
                return query_builder
            else:
                return company_builder

        mock_supabase.table.side_effect = table_side_effect

        mock_storage = MagicMock()
        mock_storage.get_file_content = AsyncMock(return_value=b"<?xml version='1.0'?>")

        app.dependency_overrides[get_current_user] = mock_get_current_user

        with patch("app.api.v1.t4.get_supabase_client", return_value=mock_supabase), \
             patch("app.api.v1.t4.get_t4_storage", return_value=mock_storage):
            client = TestClient(app)
            response = client.get(
                f"/api/v1/t4/summary/{TEST_COMPANY_ID}/{TEST_TAX_YEAR}/download-xml"
            )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/xml"
        assert "T4_123456789RP0001_2025.xml" in response.headers["content-disposition"]


class TestValidateT4XmlStorageError:
    """Tests for T4 XML validation with storage errors."""

    def test_validate_xml_storage_error(self, mock_get_current_user):
        """Test validation handles storage errors."""
        mock_supabase = MagicMock()

        mock_response = MagicMock()
        mock_response.data = {
            "xml_storage_key": "t4/xml/2025/test.xml",
            "status": "generated",
        }

        query_builder = MagicMock()
        query_builder.select.return_value = query_builder
        query_builder.eq.return_value = query_builder
        query_builder.maybe_single.return_value = query_builder
        query_builder.execute.return_value = mock_response

        mock_supabase.table.return_value = query_builder

        mock_storage = MagicMock()
        mock_storage.get_file_content = AsyncMock(side_effect=Exception("Storage error"))

        app.dependency_overrides[get_current_user] = mock_get_current_user

        with patch("app.api.v1.t4.get_supabase_client", return_value=mock_supabase), \
             patch("app.api.v1.t4.get_t4_storage", return_value=mock_storage):
            client = TestClient(app)
            response = client.post(
                f"/api/v1/t4/summary/{TEST_COMPANY_ID}/{TEST_TAX_YEAR}/validate"
            )

        app.dependency_overrides.clear()

        assert response.status_code == 500
        assert "Failed to retrieve" in response.json()["detail"]


class TestGetT4SummaryCompanyNotFound:
    """Tests for get T4 summary when company not found."""

    def test_get_summary_company_not_found(self, mock_get_current_user, sample_summary_data):
        """Test get summary fails when company not found."""
        mock_supabase = MagicMock()

        summary_response = MagicMock()
        summary_response.data = [sample_summary_data]

        company_response = MagicMock()
        company_response.data = []

        query_builder = MagicMock()
        query_builder.select.return_value = query_builder
        query_builder.eq.return_value = query_builder
        query_builder.limit.return_value = query_builder

        call_count = [0]

        def execute_side_effect():
            nonlocal call_count
            if call_count[0] == 0:
                call_count[0] += 1
                return summary_response
            else:
                return company_response

        query_builder.execute.side_effect = execute_side_effect
        mock_supabase.table.return_value = query_builder

        app.dependency_overrides[get_current_user] = mock_get_current_user

        with patch("app.api.v1.t4.get_supabase_client", return_value=mock_supabase):
            client = TestClient(app)
            response = client.get(f"/api/v1/t4/summary/{TEST_COMPANY_ID}/{TEST_TAX_YEAR}")

        app.dependency_overrides.clear()

        assert response.status_code == 404
        assert "Company not found" in response.json()["detail"]
