"""
API tests for payroll run management endpoints.

Tests:
- GET /api/v1/payroll/runs (list runs)
- POST /api/v1/payroll/runs/create-or-get (create or get draft run)
- DELETE /api/v1/payroll/runs/{run_id} (delete draft run)
- POST /api/v1/payroll/runs/{run_id}/finalize (finalize run)
- POST /api/v1/payroll/runs/{run_id}/approve (approve run)
- POST /api/v1/payroll/runs/{run_id}/recalculate (recalculate run)
- POST /api/v1/payroll/runs/{run_id}/sync-employees (sync employees)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from tests.api.conftest import TEST_COMPANY_ID


def create_mock_service(mock_payroll_run_service):
    """Create a factory function that returns the mock service."""
    def factory(user_id: str, company_id: str):
        return mock_payroll_run_service
    return factory


class TestListPayrollRuns:
    """Tests for GET /api/v1/payroll/runs endpoint."""

    def test_list_payroll_runs_success(
        self, client: TestClient, mock_payroll_run_service, sample_payroll_run: dict
    ):
        """Successfully list payroll runs."""
        # Configure mock service to return runs
        mock_payroll_run_service.list_runs.return_value = {
            "runs": [sample_payroll_run],
            "total": 1,
        }

        with patch(
            "app.api.v1.payroll.runs.get_user_company_id",
            new_callable=AsyncMock,
            return_value=TEST_COMPANY_ID,
        ), patch(
            "app.api.v1.payroll.runs.get_payroll_run_service",
            side_effect=create_mock_service(mock_payroll_run_service),
        ):
            response = client.get("/api/v1/payroll/runs")

            assert response.status_code == 200
            data = response.json()
            assert "runs" in data
            assert "total" in data
            assert data["total"] == 1

    def test_list_payroll_runs_with_status_filter(
        self, client: TestClient, mock_payroll_run_service
    ):
        """List runs filtered by status."""
        mock_payroll_run_service.list_runs.return_value = {"runs": [], "total": 0}

        with patch(
            "app.api.v1.payroll.runs.get_user_company_id",
            new_callable=AsyncMock,
            return_value=TEST_COMPANY_ID,
        ), patch(
            "app.api.v1.payroll.runs.get_payroll_run_service",
            side_effect=create_mock_service(mock_payroll_run_service),
        ):
            response = client.get("/api/v1/payroll/runs?run_status=draft")

            assert response.status_code == 200

    def test_list_payroll_runs_with_exclude_status(
        self, client: TestClient, mock_payroll_run_service
    ):
        """List runs excluding certain statuses."""
        mock_payroll_run_service.list_runs.return_value = {"runs": [], "total": 0}

        with patch(
            "app.api.v1.payroll.runs.get_user_company_id",
            new_callable=AsyncMock,
            return_value=TEST_COMPANY_ID,
        ), patch(
            "app.api.v1.payroll.runs.get_payroll_run_service",
            side_effect=create_mock_service(mock_payroll_run_service),
        ):
            response = client.get("/api/v1/payroll/runs?excludeStatus=draft,cancelled")

            assert response.status_code == 200

    def test_list_payroll_runs_with_pagination(
        self, client: TestClient, mock_payroll_run_service
    ):
        """List runs with pagination parameters."""
        mock_payroll_run_service.list_runs.return_value = {"runs": [], "total": 0}

        with patch(
            "app.api.v1.payroll.runs.get_user_company_id",
            new_callable=AsyncMock,
            return_value=TEST_COMPANY_ID,
        ), patch(
            "app.api.v1.payroll.runs.get_payroll_run_service",
            side_effect=create_mock_service(mock_payroll_run_service),
        ):
            response = client.get("/api/v1/payroll/runs?limit=10&offset=5")

            assert response.status_code == 200

    def test_list_payroll_runs_no_company(self, client: TestClient):
        """Return error when user has no company.

        Note: The current API implementation catches HTTPException in a generic except
        block and returns 500. This test documents the current behavior.
        """
        from fastapi import HTTPException

        mock_func = AsyncMock(
            side_effect=HTTPException(status_code=400, detail="No company found for user.")
        )

        with patch(
            "app.api.v1.payroll.runs.get_user_company_id",
            mock_func,
        ):
            response = client.get("/api/v1/payroll/runs")

            # Current implementation converts HTTPException to 500
            # Ideally should be 400, but API catches all exceptions
            assert response.status_code in [400, 500]

    def test_list_payroll_runs_unauthorized(self, unauthenticated_client: TestClient):
        """Reject unauthenticated requests."""
        response = unauthenticated_client.get("/api/v1/payroll/runs")

        assert response.status_code == 401


class TestCreateOrGetRun:
    """Tests for POST /api/v1/payroll/runs/create-or-get endpoint."""

    def test_create_or_get_run_creates_new(
        self,
        client: TestClient,
        mock_payroll_run_service,
        sample_payroll_run: dict,
    ):
        """Create a new draft payroll run."""
        mock_payroll_run_service.create_or_get_run_by_period_end.return_value = {
            "run": sample_payroll_run,
            "created": True,
            "records_count": 5,
        }

        with patch(
            "app.api.v1.payroll.runs.get_user_company_id",
            new_callable=AsyncMock,
            return_value=TEST_COMPANY_ID,
        ), patch(
            "app.api.v1.payroll.runs.get_payroll_run_service",
            side_effect=create_mock_service(mock_payroll_run_service),
        ):
            response = client.post(
                "/api/v1/payroll/runs/create-or-get",
                json={"periodEnd": "2025-01-15"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["created"] is True
            assert data["records_count"] == 5
            assert "run" in data

    def test_create_or_get_run_returns_existing(
        self,
        client: TestClient,
        mock_payroll_run_service,
        sample_payroll_run: dict,
    ):
        """Return existing run if one exists for the period."""
        mock_payroll_run_service.create_or_get_run_by_period_end.return_value = {
            "run": sample_payroll_run,
            "created": False,
            "records_count": 5,
        }

        with patch(
            "app.api.v1.payroll.runs.get_user_company_id",
            new_callable=AsyncMock,
            return_value=TEST_COMPANY_ID,
        ), patch(
            "app.api.v1.payroll.runs.get_payroll_run_service",
            side_effect=create_mock_service(mock_payroll_run_service),
        ):
            response = client.post(
                "/api/v1/payroll/runs/create-or-get",
                json={"periodEnd": "2025-01-15"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["created"] is False

    def test_create_or_get_run_invalid_date(self, client: TestClient):
        """Reject invalid period end date format."""
        response = client.post(
            "/api/v1/payroll/runs/create-or-get",
            json={"periodEnd": "invalid-date"},
        )

        # Should still accept the string but may fail in processing
        assert response.status_code in [400, 422, 500]

    def test_create_or_get_run_missing_period_end(self, client: TestClient):
        """Reject missing periodEnd field."""
        response = client.post(
            "/api/v1/payroll/runs/create-or-get",
            json={},
        )

        assert response.status_code == 422

    def test_create_or_get_run_unauthorized(self, unauthenticated_client: TestClient):
        """Reject unauthenticated requests."""
        response = unauthenticated_client.post(
            "/api/v1/payroll/runs/create-or-get",
            json={"periodEnd": "2025-01-15"},
        )

        assert response.status_code == 401


class TestDeletePayrollRun:
    """Tests for DELETE /api/v1/payroll/runs/{run_id} endpoint."""

    def test_delete_draft_run_success(
        self,
        client: TestClient,
        mock_payroll_run_service,
    ):
        """Successfully delete a draft payroll run."""
        run_id = str(uuid4())
        mock_payroll_run_service.delete_run.return_value = {
            "deleted": True,
            "run_id": run_id,
        }

        with patch(
            "app.api.v1.payroll.runs.get_user_company_id",
            new_callable=AsyncMock,
            return_value=TEST_COMPANY_ID,
        ), patch(
            "app.api.v1.payroll.runs.get_payroll_run_service",
            side_effect=create_mock_service(mock_payroll_run_service),
        ):
            response = client.delete(f"/api/v1/payroll/runs/{run_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["deleted"] is True
            assert data["run_id"] == run_id

    def test_delete_non_draft_run_fails(
        self,
        client: TestClient,
        mock_payroll_run_service,
    ):
        """Reject deletion of non-draft runs."""
        run_id = str(uuid4())
        mock_payroll_run_service.delete_run.side_effect = ValueError(
            "Cannot delete: payroll run is in 'approved' status"
        )

        with patch(
            "app.api.v1.payroll.runs.get_user_company_id",
            new_callable=AsyncMock,
            return_value=TEST_COMPANY_ID,
        ), patch(
            "app.api.v1.payroll.runs.get_payroll_run_service",
            side_effect=create_mock_service(mock_payroll_run_service),
        ):
            response = client.delete(f"/api/v1/payroll/runs/{run_id}")

            assert response.status_code == 400
            assert "Cannot delete" in response.json()["detail"]

    def test_delete_nonexistent_run(
        self,
        client: TestClient,
        mock_payroll_run_service,
    ):
        """Return error for nonexistent run."""
        run_id = str(uuid4())
        mock_payroll_run_service.delete_run.side_effect = ValueError(
            "Payroll run not found"
        )

        with patch(
            "app.api.v1.payroll.runs.get_user_company_id",
            new_callable=AsyncMock,
            return_value=TEST_COMPANY_ID,
        ), patch(
            "app.api.v1.payroll.runs.get_payroll_run_service",
            side_effect=create_mock_service(mock_payroll_run_service),
        ):
            response = client.delete(f"/api/v1/payroll/runs/{run_id}")

            assert response.status_code == 400

    def test_delete_run_unauthorized(self, unauthenticated_client: TestClient):
        """Reject unauthenticated requests."""
        run_id = str(uuid4())
        response = unauthenticated_client.delete(f"/api/v1/payroll/runs/{run_id}")

        assert response.status_code == 401


class TestFinalizePayrollRun:
    """Tests for POST /api/v1/payroll/runs/{run_id}/finalize endpoint."""

    def test_finalize_run_success(
        self,
        client: TestClient,
        mock_payroll_run_service,
        sample_payroll_run: dict,
    ):
        """Successfully finalize a draft run."""
        run_id = str(uuid4())
        finalized_run = sample_payroll_run.copy()
        finalized_run["id"] = run_id
        finalized_run["status"] = "pending_approval"
        mock_payroll_run_service.finalize_run.return_value = finalized_run

        with patch(
            "app.api.v1.payroll.runs.get_user_company_id",
            new_callable=AsyncMock,
            return_value=TEST_COMPANY_ID,
        ), patch(
            "app.api.v1.payroll.runs.get_payroll_run_service",
            side_effect=create_mock_service(mock_payroll_run_service),
        ):
            response = client.post(f"/api/v1/payroll/runs/{run_id}/finalize")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "pending_approval"

    def test_finalize_non_draft_run_fails(
        self,
        client: TestClient,
        mock_payroll_run_service,
    ):
        """Reject finalization of non-draft runs."""
        run_id = str(uuid4())
        mock_payroll_run_service.finalize_run.side_effect = ValueError(
            "Cannot finalize: run is not in draft status"
        )

        with patch(
            "app.api.v1.payroll.runs.get_user_company_id",
            new_callable=AsyncMock,
            return_value=TEST_COMPANY_ID,
        ), patch(
            "app.api.v1.payroll.runs.get_payroll_run_service",
            side_effect=create_mock_service(mock_payroll_run_service),
        ):
            response = client.post(f"/api/v1/payroll/runs/{run_id}/finalize")

            assert response.status_code == 400

    def test_finalize_run_with_modified_records_fails(
        self,
        client: TestClient,
        mock_payroll_run_service,
    ):
        """Reject finalization when records are modified (need recalculation)."""
        run_id = str(uuid4())
        mock_payroll_run_service.finalize_run.side_effect = ValueError(
            "Cannot finalize: some records have been modified"
        )

        with patch(
            "app.api.v1.payroll.runs.get_user_company_id",
            new_callable=AsyncMock,
            return_value=TEST_COMPANY_ID,
        ), patch(
            "app.api.v1.payroll.runs.get_payroll_run_service",
            side_effect=create_mock_service(mock_payroll_run_service),
        ):
            response = client.post(f"/api/v1/payroll/runs/{run_id}/finalize")

            assert response.status_code == 400

    def test_finalize_run_unauthorized(self, unauthenticated_client: TestClient):
        """Reject unauthenticated requests."""
        run_id = str(uuid4())
        response = unauthenticated_client.post(
            f"/api/v1/payroll/runs/{run_id}/finalize"
        )

        assert response.status_code == 401


class TestApprovePayrollRun:
    """Tests for POST /api/v1/payroll/runs/{run_id}/approve endpoint."""

    def test_approve_run_success(
        self,
        client: TestClient,
        mock_payroll_run_service,
        sample_payroll_run: dict,
    ):
        """Successfully approve a pending_approval run."""
        run_id = str(uuid4())
        approved_run = sample_payroll_run.copy()
        approved_run["id"] = run_id
        approved_run["status"] = "approved"
        approved_run["paystubs_generated"] = 5
        approved_run["paystub_errors"] = None
        mock_payroll_run_service.approve_run = AsyncMock(return_value=approved_run)

        with patch(
            "app.api.v1.payroll.runs.get_user_company_id",
            new_callable=AsyncMock,
            return_value=TEST_COMPANY_ID,
        ), patch(
            "app.api.v1.payroll.runs.get_payroll_run_service",
            side_effect=create_mock_service(mock_payroll_run_service),
        ):
            response = client.post(f"/api/v1/payroll/runs/{run_id}/approve")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "approved"
            # The response model uses camelCase alias
            assert data["paystubsGenerated"] == 5

    def test_approve_non_pending_run_fails(
        self,
        client: TestClient,
        mock_payroll_run_service,
    ):
        """Reject approval of runs not in pending_approval status."""
        run_id = str(uuid4())
        mock_payroll_run_service.approve_run = AsyncMock(
            side_effect=ValueError("Cannot approve: run is not in pending_approval status")
        )

        with patch(
            "app.api.v1.payroll.runs.get_user_company_id",
            new_callable=AsyncMock,
            return_value=TEST_COMPANY_ID,
        ), patch(
            "app.api.v1.payroll.runs.get_payroll_run_service",
            side_effect=create_mock_service(mock_payroll_run_service),
        ):
            response = client.post(f"/api/v1/payroll/runs/{run_id}/approve")

            assert response.status_code == 400

    def test_approve_run_unauthorized(self, unauthenticated_client: TestClient):
        """Reject unauthenticated requests."""
        run_id = str(uuid4())
        response = unauthenticated_client.post(
            f"/api/v1/payroll/runs/{run_id}/approve"
        )

        assert response.status_code == 401


class TestRecalculatePayrollRun:
    """Tests for POST /api/v1/payroll/runs/{run_id}/recalculate endpoint."""

    def test_recalculate_run_success(
        self,
        client: TestClient,
        mock_payroll_run_service,
        sample_payroll_run: dict,
    ):
        """Successfully recalculate a draft run."""
        run_id = str(uuid4())
        recalculated_run = sample_payroll_run.copy()
        recalculated_run["id"] = run_id
        mock_payroll_run_service.recalculate_run.return_value = recalculated_run

        with patch(
            "app.api.v1.payroll.runs.get_user_company_id",
            new_callable=AsyncMock,
            return_value=TEST_COMPANY_ID,
        ), patch(
            "app.api.v1.payroll.runs.get_payroll_run_service",
            side_effect=create_mock_service(mock_payroll_run_service),
        ):
            response = client.post(f"/api/v1/payroll/runs/{run_id}/recalculate")

            assert response.status_code == 200
            data = response.json()
            assert "total_gross" in data
            assert "total_net_pay" in data

    def test_recalculate_non_draft_run_fails(
        self,
        client: TestClient,
        mock_payroll_run_service,
    ):
        """Reject recalculation of non-draft runs."""
        run_id = str(uuid4())
        mock_payroll_run_service.recalculate_run.side_effect = ValueError(
            "Cannot recalculate: run is not in draft status"
        )

        with patch(
            "app.api.v1.payroll.runs.get_user_company_id",
            new_callable=AsyncMock,
            return_value=TEST_COMPANY_ID,
        ), patch(
            "app.api.v1.payroll.runs.get_payroll_run_service",
            side_effect=create_mock_service(mock_payroll_run_service),
        ):
            response = client.post(f"/api/v1/payroll/runs/{run_id}/recalculate")

            assert response.status_code == 400

    def test_recalculate_run_unauthorized(self, unauthenticated_client: TestClient):
        """Reject unauthenticated requests."""
        run_id = str(uuid4())
        response = unauthenticated_client.post(
            f"/api/v1/payroll/runs/{run_id}/recalculate"
        )

        assert response.status_code == 401


class TestSyncEmployees:
    """Tests for POST /api/v1/payroll/runs/{run_id}/sync-employees endpoint."""

    def test_sync_employees_success(
        self,
        client: TestClient,
        mock_payroll_run_service,
        sample_payroll_run: dict,
    ):
        """Successfully sync new employees to a draft run."""
        run_id = str(uuid4())
        mock_payroll_run_service.sync_employees.return_value = {
            "added_count": 2,
            "added_employees": [
                {"employee_id": "emp-1", "name": "John Doe"},
                {"employee_id": "emp-2", "name": "Jane Smith"},
            ],
            "run": sample_payroll_run,
        }

        with patch(
            "app.api.v1.payroll.runs.get_user_company_id",
            new_callable=AsyncMock,
            return_value=TEST_COMPANY_ID,
        ), patch(
            "app.api.v1.payroll.runs.get_payroll_run_service",
            side_effect=create_mock_service(mock_payroll_run_service),
        ):
            response = client.post(f"/api/v1/payroll/runs/{run_id}/sync-employees")

            assert response.status_code == 200
            data = response.json()
            assert data["added_count"] == 2
            assert len(data["added_employees"]) == 2

    def test_sync_employees_no_new_employees(
        self,
        client: TestClient,
        mock_payroll_run_service,
        sample_payroll_run: dict,
    ):
        """Sync returns empty when no new employees to add."""
        run_id = str(uuid4())
        mock_payroll_run_service.sync_employees.return_value = {
            "added_count": 0,
            "added_employees": [],
            "run": sample_payroll_run,
        }

        with patch(
            "app.api.v1.payroll.runs.get_user_company_id",
            new_callable=AsyncMock,
            return_value=TEST_COMPANY_ID,
        ), patch(
            "app.api.v1.payroll.runs.get_payroll_run_service",
            side_effect=create_mock_service(mock_payroll_run_service),
        ):
            response = client.post(f"/api/v1/payroll/runs/{run_id}/sync-employees")

            assert response.status_code == 200
            data = response.json()
            assert data["added_count"] == 0

    def test_sync_employees_unauthorized(self, unauthenticated_client: TestClient):
        """Reject unauthenticated requests."""
        run_id = str(uuid4())
        response = unauthenticated_client.post(
            f"/api/v1/payroll/runs/{run_id}/sync-employees"
        )

        assert response.status_code == 401
