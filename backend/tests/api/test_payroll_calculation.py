"""
API tests for payroll calculation endpoints.

Tests:
- POST /api/v1/payroll/calculate (single employee)
- POST /api/v1/payroll/calculate/batch (multiple employees)
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestCalculateSingle:
    """Tests for POST /api/v1/payroll/calculate endpoint."""

    def test_calculate_single_employee_success(
        self, client: TestClient, sample_calculation_request: dict
    ):
        """Successfully calculate payroll for a single employee."""
        response = client.post(
            "/api/v1/payroll/calculate",
            json=sample_calculation_request,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["employee_id"] == "emp-001"
        assert data["province"] == "ON"
        assert "total_gross" in data
        assert "cpp_base" in data
        assert "cpp_additional" in data
        assert "cpp_total" in data
        assert "ei_employee" in data
        assert "federal_tax" in data
        assert "provincial_tax" in data
        assert "net_pay" in data
        assert "calculation_details" in data

    def test_calculate_single_employee_different_provinces(
        self, client: TestClient, sample_calculation_request: dict
    ):
        """Calculate payroll for employees in different provinces."""
        # Note: QC not included as Quebec uses QPP instead of CPP
        provinces = ["ON", "BC", "AB", "MB", "SK", "NB"]

        for province in provinces:
            request = sample_calculation_request.copy()
            request["province"] = province
            request["employee_id"] = f"emp-{province}"

            response = client.post(
                "/api/v1/payroll/calculate",
                json=request,
            )

            assert response.status_code == 200, f"Failed for province {province}"
            data = response.json()
            assert data["province"] == province

    def test_calculate_single_employee_with_overtime(
        self, client: TestClient, sample_calculation_request: dict
    ):
        """Calculate payroll with overtime pay."""
        request = sample_calculation_request.copy()
        request["gross_overtime"] = "500.00"

        response = client.post(
            "/api/v1/payroll/calculate",
            json=request,
        )

        assert response.status_code == 200
        data = response.json()
        assert float(data["gross_overtime"]) == 500.00
        assert float(data["total_gross"]) == 3000.00  # 2500 + 500

    def test_calculate_single_employee_with_deductions(
        self, client: TestClient, sample_calculation_request: dict
    ):
        """Calculate payroll with various deductions."""
        request = sample_calculation_request.copy()
        request["rrsp_per_period"] = "200.00"
        request["union_dues_per_period"] = "50.00"
        request["garnishments"] = "100.00"

        response = client.post(
            "/api/v1/payroll/calculate",
            json=request,
        )

        assert response.status_code == 200
        data = response.json()
        assert float(data["rrsp"]) == 200.00
        assert float(data["union_dues"]) == 50.00
        assert float(data["garnishments"]) == 100.00

    def test_calculate_single_employee_cpp_exempt(
        self, client: TestClient, sample_calculation_request: dict
    ):
        """Calculate payroll for CPP-exempt employee."""
        request = sample_calculation_request.copy()
        request["is_cpp_exempt"] = True

        response = client.post(
            "/api/v1/payroll/calculate",
            json=request,
        )

        assert response.status_code == 200
        data = response.json()
        assert float(data["cpp_base"]) == 0
        assert float(data["cpp_additional"]) == 0
        assert float(data["cpp_total"]) == 0

    def test_calculate_single_employee_ei_exempt(
        self, client: TestClient, sample_calculation_request: dict
    ):
        """Calculate payroll for EI-exempt employee."""
        request = sample_calculation_request.copy()
        request["is_ei_exempt"] = True

        response = client.post(
            "/api/v1/payroll/calculate",
            json=request,
        )

        assert response.status_code == 200
        data = response.json()
        assert float(data["ei_employee"]) == 0

    def test_calculate_single_employee_invalid_province(
        self, client: TestClient, sample_calculation_request: dict
    ):
        """Reject invalid province code."""
        request = sample_calculation_request.copy()
        request["province"] = "XX"

        response = client.post(
            "/api/v1/payroll/calculate",
            json=request,
        )

        assert response.status_code == 422  # Validation error

    def test_calculate_single_employee_missing_required_field(
        self, client: TestClient
    ):
        """Reject request missing required fields."""
        incomplete_request = {
            "employee_id": "emp-001",
            "province": "ON",
            # Missing pay_frequency and gross_regular
        }

        response = client.post(
            "/api/v1/payroll/calculate",
            json=incomplete_request,
        )

        assert response.status_code == 422

    def test_calculate_unauthorized(self, unauthenticated_client: TestClient):
        """Reject unauthenticated requests."""
        request = {
            "employee_id": "emp-001",
            "province": "ON",
            "pay_frequency": "bi-weekly",
            "gross_regular": "2500.00",
        }

        response = unauthenticated_client.post(
            "/api/v1/payroll/calculate",
            json=request,
        )

        assert response.status_code == 401


class TestCalculateBatch:
    """Tests for POST /api/v1/payroll/calculate/batch endpoint."""

    def test_calculate_batch_success(
        self, client: TestClient, sample_batch_calculation_request: dict
    ):
        """Successfully calculate payroll for multiple employees."""
        response = client.post(
            "/api/v1/payroll/calculate/batch",
            json=sample_batch_calculation_request,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "results" in data
        assert "summary" in data
        assert len(data["results"]) == 2

        # Verify summary fields
        summary = data["summary"]
        assert summary["total_employees"] == 2
        assert "total_gross" in summary
        assert "total_cpp_employee" in summary
        assert "total_ei_employee" in summary
        assert "total_net_pay" in summary

    def test_calculate_batch_with_details(
        self, client: TestClient, sample_batch_calculation_request: dict
    ):
        """Calculate batch with detailed breakdown."""
        request = sample_batch_calculation_request.copy()
        request["include_details"] = True

        response = client.post(
            "/api/v1/payroll/calculate/batch",
            json=request,
        )

        assert response.status_code == 200
        data = response.json()

        # Each result should have calculation_details when include_details=True
        for result in data["results"]:
            assert "calculation_details" in result

    def test_calculate_batch_empty_list(self, client: TestClient):
        """Reject empty employee list."""
        request = {
            "employees": [],
            "include_details": False,
        }

        response = client.post(
            "/api/v1/payroll/calculate/batch",
            json=request,
        )

        assert response.status_code == 422
        assert "At least one employee is required" in response.json()["detail"]

    def test_calculate_batch_mixed_provinces(
        self, client: TestClient, sample_calculation_request: dict
    ):
        """Calculate batch with employees from different provinces."""
        employees = []
        provinces = ["ON", "BC", "AB", "SK"]  # QC not supported (uses QPP)

        for i, province in enumerate(provinces):
            emp = sample_calculation_request.copy()
            emp["employee_id"] = f"emp-{i+1}"
            emp["province"] = province
            employees.append(emp)

        request = {
            "employees": employees,
            "include_details": False,
        }

        response = client.post(
            "/api/v1/payroll/calculate/batch",
            json=request,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 4

        # Verify each province is present in results
        result_provinces = {r["province"] for r in data["results"]}
        assert result_provinces == set(provinces)

    def test_calculate_batch_validation_error(
        self, client: TestClient, sample_calculation_request: dict
    ):
        """Reject batch with invalid employee data."""
        emp1 = sample_calculation_request.copy()
        emp2 = sample_calculation_request.copy()
        emp2["employee_id"] = "emp-002"
        emp2["province"] = "INVALID"  # Invalid province

        request = {
            "employees": [emp1, emp2],
            "include_details": False,
        }

        response = client.post(
            "/api/v1/payroll/calculate/batch",
            json=request,
        )

        assert response.status_code == 422

    def test_calculate_batch_unauthorized(
        self, unauthenticated_client: TestClient, sample_batch_calculation_request: dict
    ):
        """Reject unauthenticated batch requests."""
        response = unauthenticated_client.post(
            "/api/v1/payroll/calculate/batch",
            json=sample_batch_calculation_request,
        )

        assert response.status_code == 401

    def test_calculate_batch_large_batch(
        self, client: TestClient, sample_calculation_request: dict
    ):
        """Calculate a larger batch of employees."""
        employees = []
        for i in range(10):
            emp = sample_calculation_request.copy()
            emp["employee_id"] = f"emp-{i+1:03d}"
            emp["gross_regular"] = str(2000 + (i * 500))  # Varying salaries
            employees.append(emp)

        request = {
            "employees": employees,
            "include_details": False,
        }

        response = client.post(
            "/api/v1/payroll/calculate/batch",
            json=request,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["summary"]["total_employees"] == 10
