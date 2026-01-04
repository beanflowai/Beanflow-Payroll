"""
Tests for PaystubStorage service.

Tests the paystub storage service for DigitalOcean Spaces.
"""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from app.services.payroll.paystub_storage import (
    PaystubStorage,
    PaystubStorageConfigError,
    sanitize_for_path,
)


class TestSanitizeForPath:
    """Tests for sanitize_for_path function."""

    def test_replaces_spaces_with_underscore(self):
        """Test that spaces are replaced with underscores."""
        result = sanitize_for_path("hello world")
        assert result == "hello_world"

    def test_replaces_slashes_with_underscore(self):
        """Test that slashes are replaced with underscores."""
        result = sanitize_for_path("path/to/file")
        assert result == "path_to_file"

    def test_replaces_backslashes_with_underscore(self):
        """Test that backslashes are replaced with underscores."""
        result = sanitize_for_path("path\\to\\file")
        assert result == "path_to_file"

    def test_replaces_colons_with_underscore(self):
        """Test that colons are replaced with underscores."""
        result = sanitize_for_path("time:12:30")
        assert result == "time_12_30"

    def test_replaces_asterisks_with_underscore(self):
        """Test that asterisks are replaced with underscores."""
        result = sanitize_for_path("file*name")
        assert result == "file_name"

    def test_replaces_question_marks_with_underscore(self):
        """Test that question marks are replaced with underscores."""
        result = sanitize_for_path("what?")
        assert result == "what"

    def test_replaces_quotes_with_underscore(self):
        """Test that quotes are replaced with underscores."""
        result = sanitize_for_path('file"name')
        assert result == "file_name"

    def test_replaces_angle_brackets_with_underscore(self):
        """Test that angle brackets are replaced with underscores."""
        result = sanitize_for_path("file<name>")
        assert result == "file_name"

    def test_replaces_pipe_with_underscore(self):
        """Test that pipe characters are replaced with underscores."""
        result = sanitize_for_path("file|name")
        assert result == "file_name"

    def test_collapses_multiple_underscores(self):
        """Test that multiple consecutive underscores are collapsed."""
        result = sanitize_for_path("file   name")
        assert result == "file_name"

    def test_strips_leading_underscores(self):
        """Test that leading underscores are stripped."""
        result = sanitize_for_path("  name")
        assert result == "name"

    def test_strips_trailing_underscores(self):
        """Test that trailing underscores are stripped."""
        result = sanitize_for_path("name  ")
        assert result == "name"

    def test_returns_unknown_for_empty_result(self):
        """Test that 'unknown' is returned for empty result."""
        result = sanitize_for_path("   ")
        assert result == "unknown"

    def test_returns_unknown_for_all_special_chars(self):
        """Test that 'unknown' is returned for all special characters."""
        result = sanitize_for_path("***")
        assert result == "unknown"

    def test_preserves_alphanumeric_chars(self):
        """Test that alphanumeric characters are preserved."""
        result = sanitize_for_path("Company123")
        assert result == "Company123"

    def test_preserves_hyphens(self):
        """Test that hyphens are preserved."""
        result = sanitize_for_path("company-name")
        assert result == "company-name"

    def test_real_company_name(self):
        """Test with a realistic company name."""
        result = sanitize_for_path("Acme Corp Inc.")
        assert result == "Acme_Corp_Inc."


class TestPaystubStorageInit:
    """Tests for PaystubStorage initialization."""

    def test_raises_error_when_access_key_missing(self):
        """Test that error is raised when access key is missing."""
        mock_config = MagicMock()
        mock_config.do_spaces_access_key = None
        mock_config.do_spaces_secret_key = "secret"
        mock_config.do_spaces_bucket = "bucket"

        with pytest.raises(PaystubStorageConfigError) as exc_info:
            PaystubStorage(config=mock_config)

        assert "DO_SPACES_ACCESS_KEY is not configured" in str(exc_info.value)

    def test_raises_error_when_secret_key_missing(self):
        """Test that error is raised when secret key is missing."""
        mock_config = MagicMock()
        mock_config.do_spaces_access_key = "access"
        mock_config.do_spaces_secret_key = None
        mock_config.do_spaces_bucket = "bucket"

        with pytest.raises(PaystubStorageConfigError) as exc_info:
            PaystubStorage(config=mock_config)

        assert "DO_SPACES_SECRET_KEY is not configured" in str(exc_info.value)

    def test_raises_error_when_bucket_missing(self):
        """Test that error is raised when bucket is missing."""
        mock_config = MagicMock()
        mock_config.do_spaces_access_key = "access"
        mock_config.do_spaces_secret_key = "secret"
        mock_config.do_spaces_bucket = None

        with pytest.raises(PaystubStorageConfigError) as exc_info:
            PaystubStorage(config=mock_config)

        assert "DO_SPACES_BUCKET is not configured" in str(exc_info.value)

    @patch("app.services.payroll.paystub_storage.boto3.client")
    def test_initializes_with_valid_config(self, mock_boto_client):
        """Test successful initialization with valid config."""
        mock_config = MagicMock()
        mock_config.do_spaces_access_key = "access"
        mock_config.do_spaces_secret_key = "secret"
        mock_config.do_spaces_bucket = "test-bucket"
        mock_config.do_spaces_endpoint = "https://nyc3.digitaloceanspaces.com"
        mock_config.do_spaces_region = "nyc3"
        mock_config.do_spaces_root_prefix = "paystubs"

        storage = PaystubStorage(config=mock_config)

        assert storage.bucket == "test-bucket"
        assert storage.root_prefix == "paystubs"
        mock_boto_client.assert_called_once_with(
            "s3",
            endpoint_url="https://nyc3.digitaloceanspaces.com",
            aws_access_key_id="access",
            aws_secret_access_key="secret",
            region_name="nyc3",
        )

    @patch("app.services.payroll.paystub_storage.boto3.client")
    def test_adds_https_prefix_to_endpoint(self, mock_boto_client):
        """Test that https:// is added to endpoint if missing."""
        mock_config = MagicMock()
        mock_config.do_spaces_access_key = "access"
        mock_config.do_spaces_secret_key = "secret"
        mock_config.do_spaces_bucket = "test-bucket"
        mock_config.do_spaces_endpoint = "nyc3.digitaloceanspaces.com"
        mock_config.do_spaces_region = "nyc3"
        mock_config.do_spaces_root_prefix = ""

        PaystubStorage(config=mock_config)

        mock_boto_client.assert_called_once()
        call_kwargs = mock_boto_client.call_args[1]
        assert call_kwargs["endpoint_url"] == "https://nyc3.digitaloceanspaces.com"

    @patch("app.services.payroll.paystub_storage.boto3.client")
    def test_preserves_http_prefix(self, mock_boto_client):
        """Test that http:// prefix is preserved."""
        mock_config = MagicMock()
        mock_config.do_spaces_access_key = "access"
        mock_config.do_spaces_secret_key = "secret"
        mock_config.do_spaces_bucket = "test-bucket"
        mock_config.do_spaces_endpoint = "http://localhost:9000"
        mock_config.do_spaces_region = "us-east-1"
        mock_config.do_spaces_root_prefix = ""

        PaystubStorage(config=mock_config)

        call_kwargs = mock_boto_client.call_args[1]
        assert call_kwargs["endpoint_url"] == "http://localhost:9000"


class TestBuildStorageKey:
    """Tests for _build_storage_key method."""

    @pytest.fixture
    def storage(self):
        """Create a PaystubStorage instance with mocked dependencies."""
        with patch("app.services.payroll.paystub_storage.boto3.client"):
            mock_config = MagicMock()
            mock_config.do_spaces_access_key = "access"
            mock_config.do_spaces_secret_key = "secret"
            mock_config.do_spaces_bucket = "test-bucket"
            mock_config.do_spaces_endpoint = "https://nyc3.digitaloceanspaces.com"
            mock_config.do_spaces_region = "nyc3"
            mock_config.do_spaces_root_prefix = "paystubs"
            return PaystubStorage(config=mock_config)

    def test_builds_key_with_root_prefix(self, storage):
        """Test key building with root prefix."""
        key = storage._build_storage_key(
            company_name="Acme Corp",
            employee_id="emp-123",
            pay_date=date(2025, 1, 15),
        )

        assert key == "paystubs/Acme_Corp/emp-123/2025/paystub_2025-01-15.pdf"

    def test_builds_key_with_record_id(self, storage):
        """Test key building with record ID."""
        key = storage._build_storage_key(
            company_name="Acme Corp",
            employee_id="emp-123",
            pay_date=date(2025, 1, 15),
            record_id="abc12345-6789-0000-0000-000000000000",
        )

        assert key == "paystubs/Acme_Corp/emp-123/2025/paystub_2025-01-15_abc12345.pdf"

    def test_builds_key_without_root_prefix(self):
        """Test key building without root prefix."""
        with patch("app.services.payroll.paystub_storage.boto3.client"):
            mock_config = MagicMock()
            mock_config.do_spaces_access_key = "access"
            mock_config.do_spaces_secret_key = "secret"
            mock_config.do_spaces_bucket = "test-bucket"
            mock_config.do_spaces_endpoint = "https://nyc3.digitaloceanspaces.com"
            mock_config.do_spaces_region = "nyc3"
            mock_config.do_spaces_root_prefix = ""

            storage = PaystubStorage(config=mock_config)
            key = storage._build_storage_key(
                company_name="Acme Corp",
                employee_id="emp-123",
                pay_date=date(2025, 1, 15),
            )

            assert key == "Acme_Corp/emp-123/2025/paystub_2025-01-15.pdf"

    def test_sanitizes_company_name(self, storage):
        """Test that company name is sanitized."""
        key = storage._build_storage_key(
            company_name="Acme/Corp Inc.",
            employee_id="emp-123",
            pay_date=date(2025, 1, 15),
        )

        assert "Acme_Corp_Inc." in key
        assert "/" not in key.split("/")[1]  # Company name part should have no slashes

    def test_uses_year_from_pay_date(self, storage):
        """Test that year is extracted from pay date."""
        key = storage._build_storage_key(
            company_name="Acme",
            employee_id="emp-123",
            pay_date=date(2024, 12, 31),
        )

        assert "/2024/" in key

    def test_record_id_removes_hyphens(self, storage):
        """Test that record ID hyphens are removed."""
        key = storage._build_storage_key(
            company_name="Acme",
            employee_id="emp-123",
            pay_date=date(2025, 1, 15),
            record_id="12345678-abcd-1234-5678-abcdef123456",
        )

        # Should use first 8 chars without hyphens
        assert "12345678" in key
        assert "-" not in key.split("/")[-1].replace("2025-01-15", "")


class TestSavePaystub:
    """Tests for save_paystub method."""

    @pytest.fixture
    def storage(self):
        """Create a PaystubStorage instance with mocked S3 client."""
        with patch("app.services.payroll.paystub_storage.boto3.client") as mock_boto:
            mock_config = MagicMock()
            mock_config.do_spaces_access_key = "access"
            mock_config.do_spaces_secret_key = "secret"
            mock_config.do_spaces_bucket = "test-bucket"
            mock_config.do_spaces_endpoint = "https://nyc3.digitaloceanspaces.com"
            mock_config.do_spaces_region = "nyc3"
            mock_config.do_spaces_root_prefix = "paystubs"

            storage = PaystubStorage(config=mock_config)
            storage.s3_client = MagicMock()
            return storage

    @pytest.mark.asyncio
    async def test_uploads_pdf_to_spaces(self, storage):
        """Test that PDF is uploaded to DO Spaces."""
        pdf_bytes = b"%PDF-1.4 test content"

        result = await storage.save_paystub(
            pdf_bytes=pdf_bytes,
            company_name="Acme Corp",
            employee_id="emp-123",
            pay_date=date(2025, 1, 15),
        )

        storage.s3_client.put_object.assert_called_once()
        call_kwargs = storage.s3_client.put_object.call_args[1]
        assert call_kwargs["Bucket"] == "test-bucket"
        assert call_kwargs["Body"] == pdf_bytes
        assert call_kwargs["ContentType"] == "application/pdf"
        assert call_kwargs["ACL"] == "private"
        assert "paystubs/Acme_Corp/emp-123/2025/paystub_2025-01-15.pdf" == result

    @pytest.mark.asyncio
    async def test_uploads_with_record_id(self, storage):
        """Test upload with record ID for uniqueness."""
        pdf_bytes = b"%PDF-1.4 test content"

        result = await storage.save_paystub(
            pdf_bytes=pdf_bytes,
            company_name="Acme Corp",
            employee_id="emp-123",
            pay_date=date(2025, 1, 15),
            record_id="abc12345-6789-0000-0000-000000000000",
        )

        assert "abc12345" in result

    @pytest.mark.asyncio
    async def test_includes_metadata(self, storage):
        """Test that metadata is included in upload."""
        pdf_bytes = b"%PDF-1.4 test content"

        await storage.save_paystub(
            pdf_bytes=pdf_bytes,
            company_name="Acme Corp",
            employee_id="emp-123",
            pay_date=date(2025, 1, 15),
        )

        call_kwargs = storage.s3_client.put_object.call_args[1]
        metadata = call_kwargs["Metadata"]
        assert metadata["company_name"] == "Acme_Corp"
        assert metadata["employee_id"] == "emp-123"
        assert metadata["pay_date"] == "2025-01-15"

    @pytest.mark.asyncio
    async def test_returns_storage_key(self, storage):
        """Test that storage key is returned."""
        pdf_bytes = b"%PDF-1.4 test content"

        result = await storage.save_paystub(
            pdf_bytes=pdf_bytes,
            company_name="Acme",
            employee_id="emp-123",
            pay_date=date(2025, 1, 15),
        )

        assert result.endswith(".pdf")
        assert "emp-123" in result


class TestGeneratePresignedUrl:
    """Tests for generate_presigned_url method."""

    @pytest.fixture
    def storage(self):
        """Create a PaystubStorage instance with mocked S3 client."""
        with patch("app.services.payroll.paystub_storage.boto3.client"):
            mock_config = MagicMock()
            mock_config.do_spaces_access_key = "access"
            mock_config.do_spaces_secret_key = "secret"
            mock_config.do_spaces_bucket = "test-bucket"
            mock_config.do_spaces_endpoint = "https://nyc3.digitaloceanspaces.com"
            mock_config.do_spaces_region = "nyc3"
            mock_config.do_spaces_root_prefix = "paystubs"

            storage = PaystubStorage(config=mock_config)
            storage.s3_client = MagicMock()
            storage.s3_client.generate_presigned_url.return_value = (
                "https://test-bucket.nyc3.digitaloceanspaces.com/paystubs/test.pdf?signature=abc"
            )
            return storage

    def test_generates_presigned_url(self, storage):
        """Test presigned URL generation."""
        url = storage.generate_presigned_url("paystubs/test.pdf")

        storage.s3_client.generate_presigned_url.assert_called_once_with(
            "get_object",
            Params={"Bucket": "test-bucket", "Key": "paystubs/test.pdf"},
            ExpiresIn=900,
        )
        assert "https://" in url

    def test_uses_custom_expiration(self, storage):
        """Test presigned URL with custom expiration."""
        storage.generate_presigned_url("paystubs/test.pdf", expires_in=3600)

        call_kwargs = storage.s3_client.generate_presigned_url.call_args
        assert call_kwargs[1]["ExpiresIn"] == 3600

    @pytest.mark.asyncio
    async def test_async_version(self, storage):
        """Test async presigned URL generation."""
        url = await storage.generate_presigned_url_async("paystubs/test.pdf")

        assert "https://" in url

    @pytest.mark.asyncio
    async def test_async_with_custom_expiration(self, storage):
        """Test async presigned URL with custom expiration."""
        await storage.generate_presigned_url_async(
            "paystubs/test.pdf", expires_in=1800
        )

        call_kwargs = storage.s3_client.generate_presigned_url.call_args
        assert call_kwargs[1]["ExpiresIn"] == 1800


class TestPaystubExists:
    """Tests for paystub_exists method."""

    @pytest.fixture
    def storage(self):
        """Create a PaystubStorage instance with mocked S3 client."""
        with patch("app.services.payroll.paystub_storage.boto3.client"):
            mock_config = MagicMock()
            mock_config.do_spaces_access_key = "access"
            mock_config.do_spaces_secret_key = "secret"
            mock_config.do_spaces_bucket = "test-bucket"
            mock_config.do_spaces_endpoint = "https://nyc3.digitaloceanspaces.com"
            mock_config.do_spaces_region = "nyc3"
            mock_config.do_spaces_root_prefix = "paystubs"

            storage = PaystubStorage(config=mock_config)
            storage.s3_client = MagicMock()
            return storage

    @pytest.mark.asyncio
    async def test_returns_true_when_file_exists(self, storage):
        """Test returns True when file exists."""
        storage.s3_client.head_object.return_value = {"ContentLength": 1000}

        result = await storage.paystub_exists("paystubs/test.pdf")

        assert result is True
        storage.s3_client.head_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="paystubs/test.pdf",
        )

    @pytest.mark.asyncio
    async def test_returns_false_when_file_not_found(self, storage):
        """Test returns False when file not found."""
        error_response = {"Error": {"Code": "404"}}
        storage.s3_client.head_object.side_effect = ClientError(
            error_response, "HeadObject"
        )

        result = await storage.paystub_exists("paystubs/nonexistent.pdf")

        assert result is False

    @pytest.mark.asyncio
    async def test_raises_on_other_errors(self, storage):
        """Test that other errors are re-raised."""
        error_response = {"Error": {"Code": "403"}}
        storage.s3_client.head_object.side_effect = ClientError(
            error_response, "HeadObject"
        )

        with pytest.raises(ClientError):
            await storage.paystub_exists("paystubs/test.pdf")


class TestDeletePaystub:
    """Tests for delete_paystub method."""

    @pytest.fixture
    def storage(self):
        """Create a PaystubStorage instance with mocked S3 client."""
        with patch("app.services.payroll.paystub_storage.boto3.client"):
            mock_config = MagicMock()
            mock_config.do_spaces_access_key = "access"
            mock_config.do_spaces_secret_key = "secret"
            mock_config.do_spaces_bucket = "test-bucket"
            mock_config.do_spaces_endpoint = "https://nyc3.digitaloceanspaces.com"
            mock_config.do_spaces_region = "nyc3"
            mock_config.do_spaces_root_prefix = "paystubs"

            storage = PaystubStorage(config=mock_config)
            storage.s3_client = MagicMock()
            return storage

    @pytest.mark.asyncio
    async def test_deletes_paystub(self, storage):
        """Test successful deletion."""
        await storage.delete_paystub("paystubs/test.pdf")

        storage.s3_client.delete_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="paystubs/test.pdf",
        )

    @pytest.mark.asyncio
    async def test_raises_on_deletion_error(self, storage):
        """Test that deletion errors are re-raised."""
        error_response = {"Error": {"Code": "500"}}
        storage.s3_client.delete_object.side_effect = ClientError(
            error_response, "DeleteObject"
        )

        with pytest.raises(ClientError):
            await storage.delete_paystub("paystubs/test.pdf")


class TestGetPaystubStorage:
    """Tests for get_paystub_storage singleton function."""

    def test_returns_singleton_instance(self):
        """Test that singleton returns the same instance."""
        # Import the module to access the global
        import app.services.payroll.paystub_storage as storage_module

        # Reset singleton
        storage_module._paystub_storage = None

        with patch("app.services.payroll.paystub_storage.boto3.client"):
            with patch(
                "app.services.payroll.paystub_storage.get_config"
            ) as mock_get_config:
                mock_config = MagicMock()
                mock_config.do_spaces_access_key = "access"
                mock_config.do_spaces_secret_key = "secret"
                mock_config.do_spaces_bucket = "test-bucket"
                mock_config.do_spaces_endpoint = "https://nyc3.digitaloceanspaces.com"
                mock_config.do_spaces_region = "nyc3"
                mock_config.do_spaces_root_prefix = "paystubs"
                mock_get_config.return_value = mock_config

                from app.services.payroll.paystub_storage import get_paystub_storage

                instance1 = get_paystub_storage()
                instance2 = get_paystub_storage()

                assert instance1 is instance2

        # Cleanup
        storage_module._paystub_storage = None
