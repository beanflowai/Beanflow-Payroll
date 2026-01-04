"""
Tests for T4 Storage Service.

Tests the T4StorageService class for uploading T4 PDFs and XML to storage.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest

from app.services.t4.storage_service import (
    T4StorageConfigError,
    T4StorageService,
    sanitize_for_path,
)


class TestSanitizeForPath:
    """Tests for sanitize_for_path function."""

    def test_simple_text(self):
        """Test sanitizing simple text."""
        assert sanitize_for_path("Acme Corp") == "Acme_Corp"

    def test_special_characters(self):
        """Test sanitizing text with special characters."""
        assert sanitize_for_path("Company/Name:Test") == "Company_Name_Test"

    def test_multiple_spaces(self):
        """Test sanitizing text with multiple spaces."""
        assert sanitize_for_path("Company   Name") == "Company_Name"

    def test_leading_trailing_underscores(self):
        """Test that leading/trailing underscores are stripped."""
        assert sanitize_for_path("  Test  ") == "Test"

    def test_empty_string_returns_unknown(self):
        """Test that empty string returns 'unknown'."""
        assert sanitize_for_path("") == "unknown"

    def test_only_special_chars_returns_unknown(self):
        """Test that only special characters returns 'unknown'."""
        assert sanitize_for_path("/\\:*?") == "unknown"


class TestT4StorageServiceInit:
    """Tests for T4StorageService initialization."""

    def test_raises_error_without_access_key(self):
        """Test that missing access key raises error."""
        mock_config = MagicMock()
        mock_config.do_spaces_access_key = None
        mock_config.do_spaces_secret_key = "secret"
        mock_config.do_spaces_bucket = "bucket"

        with pytest.raises(T4StorageConfigError) as exc_info:
            T4StorageService(config=mock_config)

        assert "DO_SPACES_ACCESS_KEY" in str(exc_info.value)

    def test_raises_error_without_secret_key(self):
        """Test that missing secret key raises error."""
        mock_config = MagicMock()
        mock_config.do_spaces_access_key = "access"
        mock_config.do_spaces_secret_key = None
        mock_config.do_spaces_bucket = "bucket"

        with pytest.raises(T4StorageConfigError) as exc_info:
            T4StorageService(config=mock_config)

        assert "DO_SPACES_SECRET_KEY" in str(exc_info.value)

    def test_raises_error_without_bucket(self):
        """Test that missing bucket raises error."""
        mock_config = MagicMock()
        mock_config.do_spaces_access_key = "access"
        mock_config.do_spaces_secret_key = "secret"
        mock_config.do_spaces_bucket = None

        with pytest.raises(T4StorageConfigError) as exc_info:
            T4StorageService(config=mock_config)

        assert "DO_SPACES_BUCKET" in str(exc_info.value)

    @patch("app.services.t4.storage_service.boto3.client")
    def test_initializes_with_valid_config(self, mock_boto_client: MagicMock):
        """Test successful initialization with valid config."""
        mock_config = MagicMock()
        mock_config.do_spaces_access_key = "access"
        mock_config.do_spaces_secret_key = "secret"
        mock_config.do_spaces_bucket = "bucket"
        mock_config.do_spaces_endpoint = "nyc3.digitaloceanspaces.com"
        mock_config.do_spaces_region = "nyc3"
        mock_config.do_spaces_root_prefix = "payroll"

        service = T4StorageService(config=mock_config)

        assert service.bucket == "bucket"
        assert service.root_prefix == "payroll"
        mock_boto_client.assert_called_once()

    @patch("app.services.t4.storage_service.boto3.client")
    def test_adds_https_to_endpoint(self, mock_boto_client: MagicMock):
        """Test that https is added to endpoint if missing."""
        mock_config = MagicMock()
        mock_config.do_spaces_access_key = "access"
        mock_config.do_spaces_secret_key = "secret"
        mock_config.do_spaces_bucket = "bucket"
        mock_config.do_spaces_endpoint = "nyc3.digitaloceanspaces.com"
        mock_config.do_spaces_region = "nyc3"
        mock_config.do_spaces_root_prefix = ""

        T4StorageService(config=mock_config)

        # Check that endpoint_url starts with https
        call_kwargs = mock_boto_client.call_args[1]
        assert call_kwargs["endpoint_url"].startswith("https://")


class TestBuildT4SlipKey:
    """Tests for _build_t4_slip_key method."""

    @pytest.fixture
    def service(self) -> T4StorageService:
        """Create a mock T4StorageService."""
        with patch("app.services.t4.storage_service.boto3.client"):
            mock_config = MagicMock()
            mock_config.do_spaces_access_key = "access"
            mock_config.do_spaces_secret_key = "secret"
            mock_config.do_spaces_bucket = "bucket"
            mock_config.do_spaces_endpoint = "nyc3.digitaloceanspaces.com"
            mock_config.do_spaces_region = "nyc3"
            mock_config.do_spaces_root_prefix = "payroll"
            return T4StorageService(config=mock_config)

    def test_original_slip_key(self, service: T4StorageService):
        """Test building key for original T4 slip."""
        employee_id = UUID("12345678-1234-1234-1234-123456789012")
        key = service._build_t4_slip_key("Acme Corp", 2025, employee_id, 0)

        assert key == "payroll/Acme_Corp/t4/2025/T4_12345678-1234-1234-1234-123456789012.pdf"

    def test_amended_slip_key(self, service: T4StorageService):
        """Test building key for amended T4 slip."""
        employee_id = UUID("12345678-1234-1234-1234-123456789012")
        key = service._build_t4_slip_key("Acme Corp", 2025, employee_id, 1)

        assert "amended_1" in key

    def test_key_without_root_prefix(self):
        """Test building key without root prefix."""
        with patch("app.services.t4.storage_service.boto3.client"):
            mock_config = MagicMock()
            mock_config.do_spaces_access_key = "access"
            mock_config.do_spaces_secret_key = "secret"
            mock_config.do_spaces_bucket = "bucket"
            mock_config.do_spaces_endpoint = "nyc3.digitaloceanspaces.com"
            mock_config.do_spaces_region = "nyc3"
            mock_config.do_spaces_root_prefix = ""

            service = T4StorageService(config=mock_config)
            employee_id = UUID("12345678-1234-1234-1234-123456789012")
            key = service._build_t4_slip_key("Acme Corp", 2025, employee_id, 0)

            assert key.startswith("Acme_Corp/")


class TestBuildT4SummaryKey:
    """Tests for _build_t4_summary_key method."""

    @pytest.fixture
    def service(self) -> T4StorageService:
        """Create a mock T4StorageService."""
        with patch("app.services.t4.storage_service.boto3.client"):
            mock_config = MagicMock()
            mock_config.do_spaces_access_key = "access"
            mock_config.do_spaces_secret_key = "secret"
            mock_config.do_spaces_bucket = "bucket"
            mock_config.do_spaces_endpoint = "nyc3.digitaloceanspaces.com"
            mock_config.do_spaces_region = "nyc3"
            mock_config.do_spaces_root_prefix = "payroll"
            return T4StorageService(config=mock_config)

    def test_summary_key(self, service: T4StorageService):
        """Test building key for T4 Summary."""
        key = service._build_t4_summary_key("Acme Corp", 2025)

        assert key == "payroll/Acme_Corp/t4/2025/T4_Summary_2025.pdf"


class TestBuildT4XMLKey:
    """Tests for _build_t4_xml_key method."""

    @pytest.fixture
    def service(self) -> T4StorageService:
        """Create a mock T4StorageService."""
        with patch("app.services.t4.storage_service.boto3.client"):
            mock_config = MagicMock()
            mock_config.do_spaces_access_key = "access"
            mock_config.do_spaces_secret_key = "secret"
            mock_config.do_spaces_bucket = "bucket"
            mock_config.do_spaces_endpoint = "nyc3.digitaloceanspaces.com"
            mock_config.do_spaces_region = "nyc3"
            mock_config.do_spaces_root_prefix = "payroll"
            return T4StorageService(config=mock_config)

    def test_xml_key(self, service: T4StorageService):
        """Test building key for T4 XML."""
        key = service._build_t4_xml_key("Acme Corp", 2025, "123456789RP0001")

        assert key == "payroll/Acme_Corp/t4/2025/T4_123456789RP0001_2025.xml"


class TestSaveT4Slip:
    """Tests for save_t4_slip method."""

    @pytest.fixture
    def service(self) -> T4StorageService:
        """Create a mock T4StorageService."""
        with patch("app.services.t4.storage_service.boto3.client") as mock_client:
            mock_config = MagicMock()
            mock_config.do_spaces_access_key = "access"
            mock_config.do_spaces_secret_key = "secret"
            mock_config.do_spaces_bucket = "bucket"
            mock_config.do_spaces_endpoint = "nyc3.digitaloceanspaces.com"
            mock_config.do_spaces_region = "nyc3"
            mock_config.do_spaces_root_prefix = "payroll"
            service = T4StorageService(config=mock_config)
            service.s3_client = mock_client.return_value
            return service

    @pytest.mark.asyncio
    async def test_save_t4_slip(self, service: T4StorageService):
        """Test saving a T4 slip."""
        employee_id = UUID("12345678-1234-1234-1234-123456789012")
        pdf_bytes = b"%PDF-1.4 test content"

        result = await service.save_t4_slip(
            pdf_bytes=pdf_bytes,
            company_name="Acme Corp",
            tax_year=2025,
            employee_id=employee_id,
        )

        assert "T4_" in result
        assert ".pdf" in result
        service.s3_client.put_object.assert_called_once()


class TestSaveT4Summary:
    """Tests for save_t4_summary method."""

    @pytest.fixture
    def service(self) -> T4StorageService:
        """Create a mock T4StorageService."""
        with patch("app.services.t4.storage_service.boto3.client") as mock_client:
            mock_config = MagicMock()
            mock_config.do_spaces_access_key = "access"
            mock_config.do_spaces_secret_key = "secret"
            mock_config.do_spaces_bucket = "bucket"
            mock_config.do_spaces_endpoint = "nyc3.digitaloceanspaces.com"
            mock_config.do_spaces_region = "nyc3"
            mock_config.do_spaces_root_prefix = "payroll"
            service = T4StorageService(config=mock_config)
            service.s3_client = mock_client.return_value
            return service

    @pytest.mark.asyncio
    async def test_save_t4_summary(self, service: T4StorageService):
        """Test saving a T4 summary."""
        pdf_bytes = b"%PDF-1.4 test content"

        result = await service.save_t4_summary(
            pdf_bytes=pdf_bytes,
            company_name="Acme Corp",
            tax_year=2025,
        )

        assert "T4_Summary" in result
        assert ".pdf" in result
        service.s3_client.put_object.assert_called_once()


class TestSaveT4XML:
    """Tests for save_t4_xml method."""

    @pytest.fixture
    def service(self) -> T4StorageService:
        """Create a mock T4StorageService."""
        with patch("app.services.t4.storage_service.boto3.client") as mock_client:
            mock_config = MagicMock()
            mock_config.do_spaces_access_key = "access"
            mock_config.do_spaces_secret_key = "secret"
            mock_config.do_spaces_bucket = "bucket"
            mock_config.do_spaces_endpoint = "nyc3.digitaloceanspaces.com"
            mock_config.do_spaces_region = "nyc3"
            mock_config.do_spaces_root_prefix = "payroll"
            service = T4StorageService(config=mock_config)
            service.s3_client = mock_client.return_value
            return service

    @pytest.mark.asyncio
    async def test_save_t4_xml(self, service: T4StorageService):
        """Test saving a T4 XML."""
        xml_content = '<?xml version="1.0"?><T4>test</T4>'

        result = await service.save_t4_xml(
            xml_content=xml_content,
            company_name="Acme Corp",
            tax_year=2025,
            payroll_account="123456789RP0001",
        )

        assert "T4_" in result
        assert ".xml" in result
        service.s3_client.put_object.assert_called_once()


class TestGeneratePresignedUrl:
    """Tests for generate_presigned_url method."""

    @pytest.fixture
    def service(self) -> T4StorageService:
        """Create a mock T4StorageService."""
        with patch("app.services.t4.storage_service.boto3.client") as mock_client:
            mock_config = MagicMock()
            mock_config.do_spaces_access_key = "access"
            mock_config.do_spaces_secret_key = "secret"
            mock_config.do_spaces_bucket = "bucket"
            mock_config.do_spaces_endpoint = "nyc3.digitaloceanspaces.com"
            mock_config.do_spaces_region = "nyc3"
            mock_config.do_spaces_root_prefix = "payroll"
            service = T4StorageService(config=mock_config)
            service.s3_client = mock_client.return_value
            service.s3_client.generate_presigned_url.return_value = (
                "https://bucket.nyc3.digitaloceanspaces.com/test?signature=abc"
            )
            return service

    def test_generate_presigned_url(self, service: T4StorageService):
        """Test generating a presigned URL."""
        result = service.generate_presigned_url("test/key.pdf")

        assert "https://" in result
        service.s3_client.generate_presigned_url.assert_called_once()

    def test_generate_presigned_url_with_filename(self, service: T4StorageService):
        """Test generating a presigned URL with filename."""
        service.generate_presigned_url("test/key.pdf", filename="download.pdf")

        call_args = service.s3_client.generate_presigned_url.call_args
        params = call_args[1]["Params"]
        assert "ResponseContentDisposition" in params
        assert "download.pdf" in params["ResponseContentDisposition"]

    @pytest.mark.asyncio
    async def test_generate_presigned_url_async(self, service: T4StorageService):
        """Test generating presigned URL asynchronously."""
        result = await service.generate_presigned_url_async("test/key.pdf")

        assert "https://" in result


class TestFileExists:
    """Tests for file_exists method."""

    @pytest.fixture
    def service(self) -> T4StorageService:
        """Create a mock T4StorageService."""
        with patch("app.services.t4.storage_service.boto3.client") as mock_client:
            mock_config = MagicMock()
            mock_config.do_spaces_access_key = "access"
            mock_config.do_spaces_secret_key = "secret"
            mock_config.do_spaces_bucket = "bucket"
            mock_config.do_spaces_endpoint = "nyc3.digitaloceanspaces.com"
            mock_config.do_spaces_region = "nyc3"
            mock_config.do_spaces_root_prefix = "payroll"
            service = T4StorageService(config=mock_config)
            service.s3_client = mock_client.return_value
            return service

    @pytest.mark.asyncio
    async def test_file_exists_true(self, service: T4StorageService):
        """Test file_exists returns True when file exists."""
        result = await service.file_exists("test/key.pdf")

        assert result is True
        service.s3_client.head_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_file_exists_false(self, service: T4StorageService):
        """Test file_exists returns False when file doesn't exist."""
        from botocore.exceptions import ClientError

        error_response = {"Error": {"Code": "404"}}
        service.s3_client.head_object.side_effect = ClientError(
            error_response, "head_object"
        )

        result = await service.file_exists("test/key.pdf")

        assert result is False


class TestDeleteFile:
    """Tests for delete_file method."""

    @pytest.fixture
    def service(self) -> T4StorageService:
        """Create a mock T4StorageService."""
        with patch("app.services.t4.storage_service.boto3.client") as mock_client:
            mock_config = MagicMock()
            mock_config.do_spaces_access_key = "access"
            mock_config.do_spaces_secret_key = "secret"
            mock_config.do_spaces_bucket = "bucket"
            mock_config.do_spaces_endpoint = "nyc3.digitaloceanspaces.com"
            mock_config.do_spaces_region = "nyc3"
            mock_config.do_spaces_root_prefix = "payroll"
            service = T4StorageService(config=mock_config)
            service.s3_client = mock_client.return_value
            return service

    @pytest.mark.asyncio
    async def test_delete_file(self, service: T4StorageService):
        """Test deleting a file."""
        await service.delete_file("test/key.pdf")

        service.s3_client.delete_object.assert_called_once()


class TestGetFileContent:
    """Tests for get_file_content method."""

    @pytest.fixture
    def service(self) -> T4StorageService:
        """Create a mock T4StorageService."""
        with patch("app.services.t4.storage_service.boto3.client") as mock_client:
            mock_config = MagicMock()
            mock_config.do_spaces_access_key = "access"
            mock_config.do_spaces_secret_key = "secret"
            mock_config.do_spaces_bucket = "bucket"
            mock_config.do_spaces_endpoint = "nyc3.digitaloceanspaces.com"
            mock_config.do_spaces_region = "nyc3"
            mock_config.do_spaces_root_prefix = "payroll"
            service = T4StorageService(config=mock_config)
            service.s3_client = mock_client.return_value
            return service

    @pytest.mark.asyncio
    async def test_get_file_content(self, service: T4StorageService):
        """Test getting file content."""
        mock_body = MagicMock()
        mock_body.read.return_value = b"file content"
        service.s3_client.get_object.return_value = {"Body": mock_body}

        result = await service.get_file_content("test/key.pdf")

        assert result == b"file content"
        service.s3_client.get_object.assert_called_once()


class TestFileExistsErrorHandling:
    """Tests for file_exists error handling."""

    @pytest.fixture
    def service(self) -> T4StorageService:
        """Create a mock T4StorageService."""
        with patch("app.services.t4.storage_service.boto3.client") as mock_client:
            mock_config = MagicMock()
            mock_config.do_spaces_access_key = "access"
            mock_config.do_spaces_secret_key = "secret"
            mock_config.do_spaces_bucket = "bucket"
            mock_config.do_spaces_endpoint = "nyc3.digitaloceanspaces.com"
            mock_config.do_spaces_region = "nyc3"
            mock_config.do_spaces_root_prefix = "payroll"
            service = T4StorageService(config=mock_config)
            service.s3_client = mock_client.return_value
            return service

    @pytest.mark.asyncio
    async def test_file_exists_non_404_error(self, service: T4StorageService):
        """Test file_exists raises for non-404 ClientError."""
        from botocore.exceptions import ClientError

        # Simulate a 403 Forbidden error (not 404)
        error_response = {"Error": {"Code": "403", "Message": "Forbidden"}}
        service.s3_client.head_object.side_effect = ClientError(
            error_response, "head_object"
        )

        with pytest.raises(ClientError) as exc_info:
            await service.file_exists("test/key.pdf")

        assert "403" in str(exc_info.value)


class TestDeleteFileErrorHandling:
    """Tests for delete_file error handling."""

    @pytest.fixture
    def service(self) -> T4StorageService:
        """Create a mock T4StorageService."""
        with patch("app.services.t4.storage_service.boto3.client") as mock_client:
            mock_config = MagicMock()
            mock_config.do_spaces_access_key = "access"
            mock_config.do_spaces_secret_key = "secret"
            mock_config.do_spaces_bucket = "bucket"
            mock_config.do_spaces_endpoint = "nyc3.digitaloceanspaces.com"
            mock_config.do_spaces_region = "nyc3"
            mock_config.do_spaces_root_prefix = "payroll"
            service = T4StorageService(config=mock_config)
            service.s3_client = mock_client.return_value
            return service

    @pytest.mark.asyncio
    async def test_delete_file_raises_on_error(self, service: T4StorageService):
        """Test delete_file raises ClientError on failure."""
        from botocore.exceptions import ClientError

        error_response = {"Error": {"Code": "403", "Message": "Forbidden"}}
        service.s3_client.delete_object.side_effect = ClientError(
            error_response, "delete_object"
        )

        with pytest.raises(ClientError):
            await service.delete_file("test/key.pdf")


class TestGetT4StorageSingleton:
    """Tests for get_t4_storage singleton function."""

    def test_returns_singleton_instance(self):
        """Test that get_t4_storage returns the same instance."""
        with patch("app.services.t4.storage_service.boto3.client"):
            from app.services.t4.storage_service import get_t4_storage

            # Clear the singleton first
            import app.services.t4.storage_service as storage_module
            storage_module._t4_storage = None

            instance1 = get_t4_storage()
            instance2 = get_t4_storage()

            assert instance1 is instance2

    def test_initializes_singleton_on_first_call(self):
        """Test that singleton is initialized on first call."""
        with patch("app.services.t4.storage_service.boto3.client"):
            from app.services.t4.storage_service import get_t4_storage, T4StorageService

            # Clear the singleton first
            import app.services.t4.storage_service as storage_module
            storage_module._t4_storage = None

            instance = get_t4_storage()

            assert isinstance(instance, T4StorageService)
