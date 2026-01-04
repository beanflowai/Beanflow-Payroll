"""
API tests for paystub endpoints.

Tests:
- GET /api/v1/payroll/records/{record_id}/paystub-url (get download URL)
- POST /api/v1/payroll/runs/{run_id}/send-paystubs (send paystub emails)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient


class TestGetPaystubDownloadUrl:
    """Tests for GET /api/v1/payroll/records/{record_id}/paystub-url endpoint."""

    def test_get_paystub_url_success(
        self,
        client: TestClient,
        mock_supabase_with_company,
        mock_payroll_run_service,
        sample_payroll_record: dict,
    ):
        """Successfully get presigned download URL for paystub."""
        record_id = str(uuid4())
        storage_key = f"paystubs/2025/01/{record_id}.pdf"
        download_url = f"https://storage.example.com/{storage_key}?signed=abc123"

        record_with_paystub = sample_payroll_record.copy()
        record_with_paystub["id"] = record_id
        record_with_paystub["paystub_storage_key"] = storage_key
        mock_payroll_run_service.get_record.return_value = record_with_paystub

        # Mock paystub storage
        mock_storage = MagicMock()
        mock_storage.generate_presigned_url_async = AsyncMock(return_value=download_url)

        with patch(
            "app.api.v1.payroll._helpers.get_supabase_client",
            return_value=mock_supabase_with_company,
        ), patch(
            "app.api.v1.payroll.paystubs.get_payroll_run_service",
            return_value=mock_payroll_run_service,
        ), patch(
            "app.api.v1.payroll.paystubs.get_paystub_storage",
            return_value=mock_storage,
        ):
            response = client.get(f"/api/v1/payroll/records/{record_id}/paystub-url")

            assert response.status_code == 200
            data = response.json()
            assert data["storageKey"] == storage_key
            assert data["downloadUrl"] == download_url
            assert data["expiresIn"] == 900  # 15 minutes

    def test_get_paystub_url_not_generated(
        self,
        client: TestClient,
        mock_supabase_with_company,
        mock_payroll_run_service,
        sample_payroll_record: dict,
    ):
        """Return 404 when paystub has not been generated."""
        record_id = str(uuid4())
        record_without_paystub = sample_payroll_record.copy()
        record_without_paystub["id"] = record_id
        record_without_paystub["paystub_storage_key"] = None
        mock_payroll_run_service.get_record.return_value = record_without_paystub

        with patch(
            "app.api.v1.payroll._helpers.get_supabase_client",
            return_value=mock_supabase_with_company,
        ), patch(
            "app.api.v1.payroll.paystubs.get_payroll_run_service",
            return_value=mock_payroll_run_service,
        ):
            response = client.get(f"/api/v1/payroll/records/{record_id}/paystub-url")

            assert response.status_code == 404
            assert "not yet generated" in response.json()["detail"]

    def test_get_paystub_url_record_not_found(
        self,
        client: TestClient,
        mock_supabase_with_company,
        mock_payroll_run_service,
    ):
        """Return 404 when payroll record doesn't exist."""
        record_id = str(uuid4())
        mock_payroll_run_service.get_record.return_value = None

        with patch(
            "app.api.v1.payroll._helpers.get_supabase_client",
            return_value=mock_supabase_with_company,
        ), patch(
            "app.api.v1.payroll.paystubs.get_payroll_run_service",
            return_value=mock_payroll_run_service,
        ):
            response = client.get(f"/api/v1/payroll/records/{record_id}/paystub-url")

            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

    def test_get_paystub_url_storage_not_configured(
        self,
        client: TestClient,
        mock_supabase_with_company,
        mock_payroll_run_service,
        sample_payroll_record: dict,
    ):
        """Return 503 when storage is not configured."""
        from app.services.payroll.paystub_storage import PaystubStorageConfigError

        record_id = str(uuid4())
        record_with_paystub = sample_payroll_record.copy()
        record_with_paystub["id"] = record_id
        record_with_paystub["paystub_storage_key"] = "some-key.pdf"
        mock_payroll_run_service.get_record.return_value = record_with_paystub

        with patch(
            "app.api.v1.payroll._helpers.get_supabase_client",
            return_value=mock_supabase_with_company,
        ), patch(
            "app.api.v1.payroll.paystubs.get_payroll_run_service",
            return_value=mock_payroll_run_service,
        ), patch(
            "app.api.v1.payroll.paystubs.get_paystub_storage",
            side_effect=PaystubStorageConfigError("Storage not configured"),
        ):
            response = client.get(f"/api/v1/payroll/records/{record_id}/paystub-url")

            assert response.status_code == 503
            assert "not configured" in response.json()["detail"]

    def test_get_paystub_url_unexpected_error(
        self,
        client: TestClient,
        mock_supabase_with_company,
        mock_payroll_run_service,
        sample_payroll_record: dict,
    ):
        """Return 500 on unexpected error (lines 130-132)."""
        record_id = str(uuid4())
        record_with_paystub = sample_payroll_record.copy()
        record_with_paystub["id"] = record_id
        record_with_paystub["paystub_storage_key"] = "some-key.pdf"
        mock_payroll_run_service.get_record.return_value = record_with_paystub

        # Mock generate_presigned_url_async to raise generic Exception
        mock_storage = MagicMock()
        mock_storage.generate_presigned_url_async = AsyncMock(
            side_effect=RuntimeError("Unexpected storage error")
        )

        with patch(
            "app.api.v1.payroll._helpers.get_supabase_client",
            return_value=mock_supabase_with_company,
        ), patch(
            "app.api.v1.payroll.paystubs.get_payroll_run_service",
            return_value=mock_payroll_run_service,
        ), patch(
            "app.api.v1.payroll.paystubs.get_paystub_storage",
            return_value=mock_storage,
        ):
            response = client.get(f"/api/v1/payroll/records/{record_id}/paystub-url")

            assert response.status_code == 500
            assert "Internal error getting paystub URL" in response.json()["detail"]

    def test_get_paystub_url_unauthorized(self, unauthenticated_client: TestClient):
        """Reject unauthenticated requests."""
        record_id = str(uuid4())
        response = unauthenticated_client.get(
            f"/api/v1/payroll/records/{record_id}/paystub-url"
        )

        assert response.status_code == 401


class TestSendPaystubs:
    """Tests for POST /api/v1/payroll/runs/{run_id}/send-paystubs endpoint."""

    def test_send_paystubs_success(
        self,
        client: TestClient,
        mock_supabase_with_company,
        mock_payroll_run_service,
    ):
        """Successfully send paystub emails to all employees."""
        run_id = str(uuid4())
        mock_payroll_run_service.send_paystubs.return_value = {
            "sent": 5,
            "errors": None,
        }

        with patch(
            "app.api.v1.payroll._helpers.get_supabase_client",
            return_value=mock_supabase_with_company,
        ), patch(
            "app.api.v1.payroll.paystubs.get_payroll_run_service",
            return_value=mock_payroll_run_service,
        ):
            response = client.post(f"/api/v1/payroll/runs/{run_id}/send-paystubs")

            assert response.status_code == 200
            data = response.json()
            assert data["sent"] == 5
            assert data["errors"] is None

    def test_send_paystubs_partial_failure(
        self,
        client: TestClient,
        mock_supabase_with_company,
        mock_payroll_run_service,
    ):
        """Return success with errors when some emails fail."""
        run_id = str(uuid4())
        mock_payroll_run_service.send_paystubs.return_value = {
            "sent": 3,
            "errors": [
                "Failed to send to employee emp-004: Invalid email",
                "Failed to send to employee emp-005: SMTP error",
            ],
        }

        with patch(
            "app.api.v1.payroll._helpers.get_supabase_client",
            return_value=mock_supabase_with_company,
        ), patch(
            "app.api.v1.payroll.paystubs.get_payroll_run_service",
            return_value=mock_payroll_run_service,
        ):
            response = client.post(f"/api/v1/payroll/runs/{run_id}/send-paystubs")

            assert response.status_code == 200
            data = response.json()
            assert data["sent"] == 3
            assert len(data["errors"]) == 2

    def test_send_paystubs_not_approved_run(
        self,
        client: TestClient,
        mock_supabase_with_company,
        mock_payroll_run_service,
    ):
        """Reject sending paystubs for non-approved runs."""
        run_id = str(uuid4())
        mock_payroll_run_service.send_paystubs.side_effect = ValueError(
            "Cannot send paystubs: run is not in approved status"
        )

        with patch(
            "app.api.v1.payroll._helpers.get_supabase_client",
            return_value=mock_supabase_with_company,
        ), patch(
            "app.api.v1.payroll.paystubs.get_payroll_run_service",
            return_value=mock_payroll_run_service,
        ):
            response = client.post(f"/api/v1/payroll/runs/{run_id}/send-paystubs")

            assert response.status_code == 400

    def test_send_paystubs_no_paystubs_generated(
        self,
        client: TestClient,
        mock_supabase_with_company,
        mock_payroll_run_service,
    ):
        """Reject when no paystubs have been generated."""
        run_id = str(uuid4())
        mock_payroll_run_service.send_paystubs.side_effect = ValueError(
            "No paystubs available to send"
        )

        with patch(
            "app.api.v1.payroll._helpers.get_supabase_client",
            return_value=mock_supabase_with_company,
        ), patch(
            "app.api.v1.payroll.paystubs.get_payroll_run_service",
            return_value=mock_payroll_run_service,
        ):
            response = client.post(f"/api/v1/payroll/runs/{run_id}/send-paystubs")

            assert response.status_code == 400

    def test_send_paystubs_unauthorized(self, unauthenticated_client: TestClient):
        """Reject unauthenticated requests."""
        run_id = str(uuid4())
        response = unauthenticated_client.post(
            f"/api/v1/payroll/runs/{run_id}/send-paystubs"
        )

        assert response.status_code == 401

    def test_send_paystubs_unexpected_error(
        self,
        client: TestClient,
        mock_supabase_with_company,
        mock_payroll_run_service,
    ):
        """Return 500 on unexpected error (lines 65-67)."""
        run_id = str(uuid4())
        # Mock send_paystubs to raise a non-ValueError exception
        mock_payroll_run_service.send_paystubs.side_effect = RuntimeError(
            "Unexpected system error"
        )

        with patch(
            "app.api.v1.payroll._helpers.get_supabase_client",
            return_value=mock_supabase_with_company,
        ), patch(
            "app.api.v1.payroll.paystubs.get_payroll_run_service",
            return_value=mock_payroll_run_service,
        ):
            response = client.post(f"/api/v1/payroll/runs/{run_id}/send-paystubs")

            assert response.status_code == 500
            assert "Internal error sending paystubs" in response.json()["detail"]
