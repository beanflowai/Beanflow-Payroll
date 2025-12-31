"""
API tests for payroll record management endpoints.

Tests:
- PATCH /api/v1/payroll/runs/{run_id}/records/{record_id} (update record)
- POST /api/v1/payroll/runs/{run_id}/employees (add employee)
- DELETE /api/v1/payroll/runs/{run_id}/employees/{employee_id} (remove employee)
"""

from __future__ import annotations

from typing import Any
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


class TestUpdatePayrollRecord:
    """Tests for PATCH /api/v1/payroll/runs/{run_id}/records/{record_id} endpoint."""

    def test_update_record_regular_hours(
        self,
        client: TestClient,
        mock_supabase_with_company,
        mock_payroll_run_service,
        sample_payroll_record: dict,
    ):
        """Update regular hours for a payroll record."""
        run_id = str(uuid4())
        record_id = str(uuid4())
        updated_record = sample_payroll_record.copy()
        updated_record["id"] = record_id
        updated_record["input_data"] = {"regularHours": 85}
        updated_record["is_modified"] = True
        mock_payroll_run_service.update_record.return_value = updated_record

        with patch(
            "app.api.v1.payroll._helpers.get_supabase_client",
            return_value=mock_supabase_with_company,
        ), patch(
            "app.api.v1.payroll.runs.get_payroll_run_service",
            return_value=mock_payroll_run_service,
        ):
            response = client.patch(
                f"/api/v1/payroll/runs/{run_id}/records/{record_id}",
                json={"regularHours": 85},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["is_modified"] is True

    def test_update_record_overtime_hours(
        self,
        client: TestClient,
        mock_supabase_with_company,
        mock_payroll_run_service,
        sample_payroll_record: dict,
    ):
        """Update overtime hours for a payroll record."""
        run_id = str(uuid4())
        record_id = str(uuid4())
        updated_record = sample_payroll_record.copy()
        updated_record["id"] = record_id
        updated_record["input_data"] = {"overtimeHours": 10}
        updated_record["is_modified"] = True
        mock_payroll_run_service.update_record.return_value = updated_record

        with patch(
            "app.api.v1.payroll._helpers.get_supabase_client",
            return_value=mock_supabase_with_company,
        ), patch(
            "app.api.v1.payroll.runs.get_payroll_run_service",
            return_value=mock_payroll_run_service,
        ):
            response = client.patch(
                f"/api/v1/payroll/runs/{run_id}/records/{record_id}",
                json={"overtimeHours": 10},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["is_modified"] is True

    def test_update_record_with_leave_entries(
        self,
        client: TestClient,
        mock_supabase_with_company,
        mock_payroll_run_service,
        sample_payroll_record: dict,
    ):
        """Update payroll record with leave entries."""
        run_id = str(uuid4())
        record_id = str(uuid4())
        updated_record = sample_payroll_record.copy()
        updated_record["id"] = record_id
        updated_record["input_data"] = {
            "leaveEntries": [
                {"type": "vacation", "hours": 8},
                {"type": "sick", "hours": 4},
            ]
        }
        updated_record["is_modified"] = True
        mock_payroll_run_service.update_record.return_value = updated_record

        with patch(
            "app.api.v1.payroll._helpers.get_supabase_client",
            return_value=mock_supabase_with_company,
        ), patch(
            "app.api.v1.payroll.runs.get_payroll_run_service",
            return_value=mock_payroll_run_service,
        ):
            response = client.patch(
                f"/api/v1/payroll/runs/{run_id}/records/{record_id}",
                json={
                    "leaveEntries": [
                        {"type": "vacation", "hours": 8},
                        {"type": "sick", "hours": 4},
                    ]
                },
            )

            assert response.status_code == 200

    def test_update_record_with_holiday_work(
        self,
        client: TestClient,
        mock_supabase_with_company,
        mock_payroll_run_service,
        sample_payroll_record: dict,
    ):
        """Update payroll record with holiday work entries."""
        run_id = str(uuid4())
        record_id = str(uuid4())
        updated_record = sample_payroll_record.copy()
        updated_record["id"] = record_id
        updated_record["is_modified"] = True
        mock_payroll_run_service.update_record.return_value = updated_record

        with patch(
            "app.api.v1.payroll._helpers.get_supabase_client",
            return_value=mock_supabase_with_company,
        ), patch(
            "app.api.v1.payroll.runs.get_payroll_run_service",
            return_value=mock_payroll_run_service,
        ):
            response = client.patch(
                f"/api/v1/payroll/runs/{run_id}/records/{record_id}",
                json={
                    "holidayWorkEntries": [
                        {
                            "holidayDate": "2025-01-01",
                            "holidayName": "New Year's Day",
                            "hoursWorked": 8,
                        }
                    ]
                },
            )

            assert response.status_code == 200

    def test_update_record_with_adjustments(
        self,
        client: TestClient,
        mock_supabase_with_company,
        mock_payroll_run_service,
        sample_payroll_record: dict,
    ):
        """Update payroll record with one-time adjustments."""
        run_id = str(uuid4())
        record_id = str(uuid4())
        updated_record = sample_payroll_record.copy()
        updated_record["id"] = record_id
        updated_record["is_modified"] = True
        mock_payroll_run_service.update_record.return_value = updated_record

        with patch(
            "app.api.v1.payroll._helpers.get_supabase_client",
            return_value=mock_supabase_with_company,
        ), patch(
            "app.api.v1.payroll.runs.get_payroll_run_service",
            return_value=mock_payroll_run_service,
        ):
            response = client.patch(
                f"/api/v1/payroll/runs/{run_id}/records/{record_id}",
                json={
                    "adjustments": [
                        {
                            "type": "bonus",
                            "amount": 500,
                            "description": "Year-end bonus",
                            "taxable": True,
                        },
                        {
                            "type": "reimbursement",
                            "amount": 100,
                            "description": "Mileage",
                            "taxable": False,
                        },
                    ]
                },
            )

            assert response.status_code == 200

    def test_update_record_with_overrides(
        self,
        client: TestClient,
        mock_supabase_with_company,
        mock_payroll_run_service,
        sample_payroll_record: dict,
    ):
        """Update payroll record with manual override values."""
        run_id = str(uuid4())
        record_id = str(uuid4())
        updated_record = sample_payroll_record.copy()
        updated_record["id"] = record_id
        updated_record["is_modified"] = True
        mock_payroll_run_service.update_record.return_value = updated_record

        with patch(
            "app.api.v1.payroll._helpers.get_supabase_client",
            return_value=mock_supabase_with_company,
        ), patch(
            "app.api.v1.payroll.runs.get_payroll_run_service",
            return_value=mock_payroll_run_service,
        ):
            response = client.patch(
                f"/api/v1/payroll/runs/{run_id}/records/{record_id}",
                json={
                    "overrides": {
                        "regularPay": 2600.00,
                        "overtimePay": None,
                        "holidayPay": None,
                    }
                },
            )

            assert response.status_code == 200

    def test_update_record_non_draft_run_fails(
        self,
        client: TestClient,
        mock_supabase_with_company,
        mock_payroll_run_service,
    ):
        """Reject updates to records in non-draft runs."""
        run_id = str(uuid4())
        record_id = str(uuid4())
        mock_payroll_run_service.update_record.side_effect = ValueError(
            "Cannot update record: payroll run is in 'approved' status"
        )

        with patch(
            "app.api.v1.payroll._helpers.get_supabase_client",
            return_value=mock_supabase_with_company,
        ), patch(
            "app.api.v1.payroll.runs.get_payroll_run_service",
            return_value=mock_payroll_run_service,
        ):
            response = client.patch(
                f"/api/v1/payroll/runs/{run_id}/records/{record_id}",
                json={"regularHours": 80},
            )

            assert response.status_code == 400

    def test_update_nonexistent_record(
        self,
        client: TestClient,
        mock_supabase_with_company,
        mock_payroll_run_service,
    ):
        """Return error for nonexistent record."""
        run_id = str(uuid4())
        record_id = str(uuid4())
        mock_payroll_run_service.update_record.side_effect = ValueError(
            "Payroll record not found"
        )

        with patch(
            "app.api.v1.payroll._helpers.get_supabase_client",
            return_value=mock_supabase_with_company,
        ), patch(
            "app.api.v1.payroll.runs.get_payroll_run_service",
            return_value=mock_payroll_run_service,
        ):
            response = client.patch(
                f"/api/v1/payroll/runs/{run_id}/records/{record_id}",
                json={"regularHours": 80},
            )

            assert response.status_code == 400

    def test_update_record_unauthorized(self, unauthenticated_client: TestClient):
        """Reject unauthenticated requests."""
        run_id = str(uuid4())
        record_id = str(uuid4())
        response = unauthenticated_client.patch(
            f"/api/v1/payroll/runs/{run_id}/records/{record_id}",
            json={"regularHours": 80},
        )

        assert response.status_code == 401


class TestAddEmployeeToRun:
    """Tests for POST /api/v1/payroll/runs/{run_id}/employees endpoint."""

    def test_add_employee_success(
        self,
        client: TestClient,
        mock_supabase_with_company,
        mock_payroll_run_service,
    ):
        """Successfully add an employee to a draft run."""
        run_id = str(uuid4())
        employee_id = str(uuid4())
        mock_payroll_run_service.add_employee_to_run.return_value = {
            "employee_id": employee_id,
            "employee_name": "John Doe",
        }

        with patch(
            "app.api.v1.payroll._helpers.get_supabase_client",
            return_value=mock_supabase_with_company,
        ), patch(
            "app.api.v1.payroll.runs.get_payroll_run_service",
            return_value=mock_payroll_run_service,
        ):
            response = client.post(
                f"/api/v1/payroll/runs/{run_id}/employees",
                json={"employeeId": employee_id},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["employee_id"] == employee_id
            assert data["employee_name"] == "John Doe"

    def test_add_employee_already_in_run(
        self,
        client: TestClient,
        mock_supabase_with_company,
        mock_payroll_run_service,
    ):
        """Return error when employee is already in the run."""
        run_id = str(uuid4())
        employee_id = str(uuid4())
        mock_payroll_run_service.add_employee_to_run.side_effect = ValueError(
            "Employee is already in this payroll run"
        )

        with patch(
            "app.api.v1.payroll._helpers.get_supabase_client",
            return_value=mock_supabase_with_company,
        ), patch(
            "app.api.v1.payroll.runs.get_payroll_run_service",
            return_value=mock_payroll_run_service,
        ):
            response = client.post(
                f"/api/v1/payroll/runs/{run_id}/employees",
                json={"employeeId": employee_id},
            )

            assert response.status_code == 400

    def test_add_employee_non_draft_run_fails(
        self,
        client: TestClient,
        mock_supabase_with_company,
        mock_payroll_run_service,
    ):
        """Reject adding employee to non-draft run."""
        run_id = str(uuid4())
        employee_id = str(uuid4())
        mock_payroll_run_service.add_employee_to_run.side_effect = ValueError(
            "Cannot add employee: run is not in draft status"
        )

        with patch(
            "app.api.v1.payroll._helpers.get_supabase_client",
            return_value=mock_supabase_with_company,
        ), patch(
            "app.api.v1.payroll.runs.get_payroll_run_service",
            return_value=mock_payroll_run_service,
        ):
            response = client.post(
                f"/api/v1/payroll/runs/{run_id}/employees",
                json={"employeeId": employee_id},
            )

            assert response.status_code == 400

    def test_add_employee_unauthorized(self, unauthenticated_client: TestClient):
        """Reject unauthenticated requests."""
        run_id = str(uuid4())
        response = unauthenticated_client.post(
            f"/api/v1/payroll/runs/{run_id}/employees",
            json={"employeeId": "emp-001"},
        )

        assert response.status_code == 401


class TestRemoveEmployeeFromRun:
    """Tests for DELETE /api/v1/payroll/runs/{run_id}/employees/{employee_id} endpoint."""

    def test_remove_employee_success(
        self,
        client: TestClient,
        mock_supabase_with_company,
        mock_payroll_run_service,
    ):
        """Successfully remove an employee from a draft run."""
        run_id = str(uuid4())
        employee_id = str(uuid4())
        mock_payroll_run_service.remove_employee_from_run.return_value = {
            "removed": True,
            "employee_id": employee_id,
        }

        with patch(
            "app.api.v1.payroll._helpers.get_supabase_client",
            return_value=mock_supabase_with_company,
        ), patch(
            "app.api.v1.payroll.runs.get_payroll_run_service",
            return_value=mock_payroll_run_service,
        ):
            response = client.delete(
                f"/api/v1/payroll/runs/{run_id}/employees/{employee_id}"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["removed"] is True
            assert data["employee_id"] == employee_id

    def test_remove_employee_not_in_run(
        self,
        client: TestClient,
        mock_supabase_with_company,
        mock_payroll_run_service,
    ):
        """Return error when employee is not in the run."""
        run_id = str(uuid4())
        employee_id = str(uuid4())
        mock_payroll_run_service.remove_employee_from_run.side_effect = ValueError(
            "Employee not found in this payroll run"
        )

        with patch(
            "app.api.v1.payroll._helpers.get_supabase_client",
            return_value=mock_supabase_with_company,
        ), patch(
            "app.api.v1.payroll.runs.get_payroll_run_service",
            return_value=mock_payroll_run_service,
        ):
            response = client.delete(
                f"/api/v1/payroll/runs/{run_id}/employees/{employee_id}"
            )

            assert response.status_code == 400

    def test_remove_employee_non_draft_run_fails(
        self,
        client: TestClient,
        mock_supabase_with_company,
        mock_payroll_run_service,
    ):
        """Reject removing employee from non-draft run."""
        run_id = str(uuid4())
        employee_id = str(uuid4())
        mock_payroll_run_service.remove_employee_from_run.side_effect = ValueError(
            "Cannot remove employee: run is not in draft status"
        )

        with patch(
            "app.api.v1.payroll._helpers.get_supabase_client",
            return_value=mock_supabase_with_company,
        ), patch(
            "app.api.v1.payroll.runs.get_payroll_run_service",
            return_value=mock_payroll_run_service,
        ):
            response = client.delete(
                f"/api/v1/payroll/runs/{run_id}/employees/{employee_id}"
            )

            assert response.status_code == 400

    def test_remove_employee_unauthorized(self, unauthenticated_client: TestClient):
        """Reject unauthenticated requests."""
        run_id = str(uuid4())
        employee_id = str(uuid4())
        response = unauthenticated_client.delete(
            f"/api/v1/payroll/runs/{run_id}/employees/{employee_id}"
        )

        assert response.status_code == 401
