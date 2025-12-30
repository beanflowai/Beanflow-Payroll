"""
API tests for sick leave endpoints.

Tests:
- GET /api/v1/payroll/sick-leave/configs (get all configs)
- GET /api/v1/payroll/sick-leave/configs/{province_code} (get config by province)
- GET /api/v1/payroll/employees/{employee_id}/sick-leave/{year} (get balance)
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from tests.api.conftest import TEST_USER_ID


class TestGetAllSickLeaveConfigs:
    """Tests for GET /api/v1/payroll/sick-leave/configs endpoint."""

    def test_get_all_sick_leave_configs(self, client: TestClient):
        """Get sick leave configurations for all provinces."""
        response = client.get("/api/v1/payroll/sick-leave/configs")

        assert response.status_code == 200
        data = response.json()

        # Should return a list of configs
        assert isinstance(data, list)
        assert len(data) > 0

        # Each config should have required fields (snake_case from API)
        for config in data:
            assert "province_code" in config
            assert "paid_days_per_year" in config
            assert "unpaid_days_per_year" in config
            assert "waiting_period_days" in config
            assert "allows_carryover" in config
            assert "accrual_method" in config

    def test_get_all_sick_leave_configs_with_year(self, client: TestClient):
        """Get sick leave configs for a specific year."""
        response = client.get("/api/v1/payroll/sick-leave/configs?year=2025")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_all_sick_leave_configs_with_pay_date(self, client: TestClient):
        """Get sick leave configs with pay date for version selection."""
        response = client.get(
            "/api/v1/payroll/sick-leave/configs?pay_date=2025-06-15"
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_all_sick_leave_configs_unauthorized(
        self, unauthenticated_client: TestClient
    ):
        """Reject unauthenticated requests."""
        response = unauthenticated_client.get("/api/v1/payroll/sick-leave/configs")

        assert response.status_code == 401


class TestGetSickLeaveConfigByProvince:
    """Tests for GET /api/v1/payroll/sick-leave/configs/{province_code} endpoint."""

    def test_get_sick_leave_config_ontario(self, client: TestClient):
        """Get sick leave config for Ontario."""
        response = client.get("/api/v1/payroll/sick-leave/configs/ON")

        assert response.status_code == 200
        data = response.json()

        assert data["province_code"] == "ON"
        assert "paid_days_per_year" in data
        assert "unpaid_days_per_year" in data
        assert "waiting_period_days" in data
        assert "allows_carryover" in data
        assert "max_carryover_days" in data
        assert "accrual_method" in data

    def test_get_sick_leave_config_all_provinces(self, client: TestClient):
        """Get sick leave config for various provinces."""
        # Note: QC not supported as Quebec uses QPP instead of CPP
        provinces = ["ON", "BC", "AB", "SK", "MB", "NS", "NB"]

        for province in provinces:
            response = client.get(f"/api/v1/payroll/sick-leave/configs/{province}")

            assert response.status_code == 200, f"Failed for province {province}"
            data = response.json()
            assert data["province_code"] == province

    def test_get_sick_leave_config_with_year(self, client: TestClient):
        """Get sick leave config for a specific year."""
        response = client.get("/api/v1/payroll/sick-leave/configs/ON?year=2025")

        assert response.status_code == 200
        data = response.json()
        assert data["province_code"] == "ON"

    def test_get_sick_leave_config_invalid_province(self, client: TestClient):
        """Return 404 for invalid province code."""
        response = client.get("/api/v1/payroll/sick-leave/configs/XX")

        assert response.status_code == 404
        assert "No sick leave configuration found" in response.json()["detail"]

    def test_get_sick_leave_config_unauthorized(
        self, unauthenticated_client: TestClient
    ):
        """Reject unauthenticated requests."""
        response = unauthenticated_client.get("/api/v1/payroll/sick-leave/configs/ON")

        assert response.status_code == 401


class TestGetEmployeeSickLeaveBalance:
    """Tests for GET /api/v1/payroll/employees/{employee_id}/sick-leave/{year} endpoint."""

    def test_get_sick_leave_balance_from_database(
        self, client: TestClient, mock_supabase, sample_employee: dict
    ):
        """Get existing sick leave balance from database."""
        employee_id = str(uuid4())

        # Mock employee data
        employee_response = MagicMock()
        employee_response.data = {
            "province_of_employment": "ON",
            "hire_date": "2024-01-15",
        }

        # Mock existing balance
        balance_response = MagicMock()
        balance_response.data = [{
            "employee_id": employee_id,
            "year": 2025,
            "paid_days_entitled": 3.0,
            "unpaid_days_entitled": 0.0,
            "paid_days_used": 1.0,
            "unpaid_days_used": 0.0,
            "carried_over_days": 0.0,
            "is_eligible": True,
            "eligibility_date": "2024-04-15",
        }]

        def table_side_effect(table_name: str):
            builder = MagicMock()
            builder.select.return_value = builder
            builder.eq.return_value = builder
            builder.single.return_value = builder

            if table_name == "employees":
                builder.execute.return_value = employee_response
            elif table_name == "employee_sick_leave_balances":
                builder.execute.return_value = balance_response
            else:
                empty_response = MagicMock()
                empty_response.data = []
                builder.execute.return_value = empty_response

            return builder

        mock_supabase.table.side_effect = table_side_effect

        with patch(
            "app.api.v1.payroll.get_supabase_client",
            return_value=mock_supabase,
        ):
            response = client.get(
                f"/api/v1/payroll/employees/{employee_id}/sick-leave/2025"
            )

            assert response.status_code == 200
            data = response.json()

            assert data["employee_id"] == employee_id
            assert data["year"] == 2025
            assert data["paid_days_entitled"] == 3.0
            assert data["paid_days_used"] == 1.0
            assert data["paid_days_remaining"] == 2.0  # 3 - 1
            assert data["is_eligible"] is True

    def test_get_sick_leave_balance_creates_default(
        self, client: TestClient, mock_supabase
    ):
        """Create default balance when none exists."""
        employee_id = str(uuid4())

        # Mock employee data
        employee_response = MagicMock()
        employee_response.data = {
            "province_of_employment": "ON",
            "hire_date": "2024-01-15",
        }

        # Mock no existing balance
        empty_balance_response = MagicMock()
        empty_balance_response.data = []

        def table_side_effect(table_name: str):
            builder = MagicMock()
            builder.select.return_value = builder
            builder.eq.return_value = builder
            builder.single.return_value = builder

            if table_name == "employees":
                builder.execute.return_value = employee_response
            elif table_name == "employee_sick_leave_balances":
                builder.execute.return_value = empty_balance_response
            else:
                empty_response = MagicMock()
                empty_response.data = []
                builder.execute.return_value = empty_response

            return builder

        mock_supabase.table.side_effect = table_side_effect

        with patch(
            "app.api.v1.payroll.get_supabase_client",
            return_value=mock_supabase,
        ):
            response = client.get(
                f"/api/v1/payroll/employees/{employee_id}/sick-leave/2025"
            )

            assert response.status_code == 200
            data = response.json()

            assert data["employee_id"] == employee_id
            assert data["year"] == 2025
            # Should have default values based on province config
            assert "paid_days_entitled" in data
            assert "paid_days_remaining" in data

    def test_get_sick_leave_balance_employee_not_found(
        self, client: TestClient, mock_supabase
    ):
        """Return 404 when employee doesn't exist."""
        employee_id = str(uuid4())

        # Mock no employee found
        empty_response = MagicMock()
        empty_response.data = None

        def table_side_effect(table_name: str):
            builder = MagicMock()
            builder.select.return_value = builder
            builder.eq.return_value = builder
            builder.single.return_value = builder
            builder.execute.return_value = empty_response
            return builder

        mock_supabase.table.side_effect = table_side_effect

        with patch(
            "app.api.v1.payroll.get_supabase_client",
            return_value=mock_supabase,
        ):
            response = client.get(
                f"/api/v1/payroll/employees/{employee_id}/sick-leave/2025"
            )

            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()

    def test_get_sick_leave_balance_unauthorized(
        self, unauthenticated_client: TestClient
    ):
        """Reject unauthenticated requests."""
        employee_id = str(uuid4())
        response = unauthenticated_client.get(
            f"/api/v1/payroll/employees/{employee_id}/sick-leave/2025"
        )

        assert response.status_code == 401

    def test_get_sick_leave_balance_different_years(
        self, client: TestClient, mock_supabase
    ):
        """Get sick leave balance for different years."""
        employee_id = str(uuid4())

        # Mock employee data
        employee_response = MagicMock()
        employee_response.data = {
            "province_of_employment": "ON",
            "hire_date": "2023-01-15",
        }

        # Mock no existing balance
        empty_balance_response = MagicMock()
        empty_balance_response.data = []

        def table_side_effect(table_name: str):
            builder = MagicMock()
            builder.select.return_value = builder
            builder.eq.return_value = builder
            builder.single.return_value = builder

            if table_name == "employees":
                builder.execute.return_value = employee_response
            else:
                builder.execute.return_value = empty_balance_response

            return builder

        mock_supabase.table.side_effect = table_side_effect

        with patch(
            "app.api.v1.payroll.get_supabase_client",
            return_value=mock_supabase,
        ):
            for year in [2024, 2025, 2026]:
                response = client.get(
                    f"/api/v1/payroll/employees/{employee_id}/sick-leave/{year}"
                )

                assert response.status_code == 200
                data = response.json()
                assert data["year"] == year
