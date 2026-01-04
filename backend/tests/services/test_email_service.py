"""Tests for email service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.email_service import (
    EmailMessage,
    EmailService,
    EmailServiceError,
    get_email_service,
)


class TestEmailMessage:
    """Tests for EmailMessage model."""

    def test_valid_email_message(self):
        """Test creating a valid EmailMessage."""
        message = EmailMessage(
            to=["test@example.com"],
            subject="Test Subject",
            html_content="<p>Hello</p>",
        )

        assert message.to == ["test@example.com"]
        assert message.subject == "Test Subject"
        assert message.html_content == "<p>Hello</p>"
        assert message.from_email is None
        assert message.from_name is None

    def test_email_message_with_from(self):
        """Test EmailMessage with from details."""
        message = EmailMessage(
            to=["user@example.com"],
            subject="Test",
            html_content="<p>Hi</p>",
            from_email="sender@example.com",
            from_name="Sender Name",
        )

        assert message.from_email == "sender@example.com"
        assert message.from_name == "Sender Name"

    def test_email_message_multiple_recipients(self):
        """Test EmailMessage with multiple recipients."""
        message = EmailMessage(
            to=["user1@example.com", "user2@example.com"],
            subject="Multi",
            html_content="<p>Group</p>",
        )

        assert len(message.to) == 2


class TestEmailServiceSetup:
    """Tests for EmailService initialization."""

    def test_setup_with_api_key(self):
        """Test EmailService setup with API key configured."""
        mock_config = MagicMock()
        mock_config.resend_api_key = "test-api-key"
        mock_config.email_from_address = "noreply@example.com"
        mock_config.email_from_name = "Test App"
        mock_config.frontend_url = "https://example.com"

        with patch("app.services.email_service.get_config", return_value=mock_config):
            with patch("app.services.email_service.resend") as mock_resend:
                service = EmailService()

                assert mock_resend.api_key == "test-api-key"

    def test_setup_without_api_key(self):
        """Test EmailService setup without API key."""
        mock_config = MagicMock()
        mock_config.resend_api_key = None

        with patch("app.services.email_service.get_config", return_value=mock_config):
            with patch("app.services.email_service.resend"):
                service = EmailService()
                # Should not raise, just log warning


class TestBuildFromAddress:
    """Tests for _build_from_address method."""

    def test_build_with_name(self):
        """Test building from address with name."""
        mock_config = MagicMock()
        mock_config.resend_api_key = "key"
        mock_config.email_from_address = "default@example.com"
        mock_config.email_from_name = "Default Name"

        with patch("app.services.email_service.get_config", return_value=mock_config):
            with patch("app.services.email_service.resend"):
                service = EmailService()
                result = service._build_from_address(
                    "custom@example.com", "Custom Name"
                )

                assert result == "Custom Name <custom@example.com>"

    def test_build_without_name(self):
        """Test building from address without name."""
        mock_config = MagicMock()
        mock_config.resend_api_key = "key"
        mock_config.email_from_address = "default@example.com"
        mock_config.email_from_name = None

        with patch("app.services.email_service.get_config", return_value=mock_config):
            with patch("app.services.email_service.resend"):
                service = EmailService()
                result = service._build_from_address("custom@example.com", None)

                assert result == "custom@example.com"

    def test_build_with_defaults(self):
        """Test building from address using defaults."""
        mock_config = MagicMock()
        mock_config.resend_api_key = "key"
        mock_config.email_from_address = "default@example.com"
        mock_config.email_from_name = "Default Sender"

        with patch("app.services.email_service.get_config", return_value=mock_config):
            with patch("app.services.email_service.resend"):
                service = EmailService()
                result = service._build_from_address(None, None)

                assert result == "Default Sender <default@example.com>"


class TestSendEmail:
    """Tests for send_email method."""

    @pytest.mark.asyncio
    async def test_send_email_without_api_key_raises(self):
        """Test that sending email without API key raises error."""
        mock_config = MagicMock()
        mock_config.resend_api_key = None

        with patch("app.services.email_service.get_config", return_value=mock_config):
            with patch("app.services.email_service.resend"):
                service = EmailService()

                message = EmailMessage(
                    to=["test@example.com"],
                    subject="Test",
                    html_content="<p>Hi</p>",
                )

                with pytest.raises(EmailServiceError, match="API key not configured"):
                    await service.send_email(message)

    @pytest.mark.asyncio
    async def test_send_email_success(self):
        """Test successful email sending."""
        mock_config = MagicMock()
        mock_config.resend_api_key = "test-key"
        mock_config.email_from_address = "noreply@example.com"
        mock_config.email_from_name = "Test App"

        with patch("app.services.email_service.get_config", return_value=mock_config):
            with patch("app.services.email_service.resend") as mock_resend:
                with patch("asyncio.to_thread") as mock_to_thread:
                    mock_to_thread.return_value = {"id": "email-123"}

                    service = EmailService()

                    message = EmailMessage(
                        to=["test@example.com"],
                        subject="Test Subject",
                        html_content="<p>Hello</p>",
                    )

                    result = await service.send_email(message)

                    assert result == {"id": "email-123"}

    @pytest.mark.asyncio
    async def test_send_email_failure_raises(self):
        """Test that email sending failure raises EmailServiceError."""
        mock_config = MagicMock()
        mock_config.resend_api_key = "test-key"
        mock_config.email_from_address = "noreply@example.com"
        mock_config.email_from_name = "Test App"

        with patch("app.services.email_service.get_config", return_value=mock_config):
            with patch("app.services.email_service.resend"):
                with patch("asyncio.to_thread") as mock_to_thread:
                    mock_to_thread.side_effect = Exception("Network error")

                    service = EmailService()

                    message = EmailMessage(
                        to=["test@example.com"],
                        subject="Test",
                        html_content="<p>Hi</p>",
                    )

                    with pytest.raises(EmailServiceError, match="Failed to send email"):
                        await service.send_email(message)


class TestCreateEmployeePortalInviteContent:
    """Tests for create_employee_portal_invite_content method."""

    def test_creates_html_content(self):
        """Test that HTML content is created with employee name and login URL."""
        mock_config = MagicMock()
        mock_config.resend_api_key = "key"
        mock_config.email_from_address = "noreply@example.com"
        mock_config.email_from_name = None

        with patch("app.services.email_service.get_config", return_value=mock_config):
            with patch("app.services.email_service.resend"):
                service = EmailService()

                result = service.create_employee_portal_invite_content(
                    employee_name="John Doe",
                    login_url="https://example.com/login?email=john@example.com",
                )

                assert "John Doe" in result
                assert "https://example.com/login?email=john@example.com" in result
                assert "BeanFlow Payroll" in result
                assert "Employee Portal" in result

    def test_content_includes_feature_list(self):
        """Test that HTML content includes feature list."""
        mock_config = MagicMock()
        mock_config.resend_api_key = "key"
        mock_config.email_from_address = "noreply@example.com"
        mock_config.email_from_name = None

        with patch("app.services.email_service.get_config", return_value=mock_config):
            with patch("app.services.email_service.resend"):
                service = EmailService()

                result = service.create_employee_portal_invite_content(
                    employee_name="Test User",
                    login_url="https://example.com/login",
                )

                assert "pay stubs" in result
                assert "T4" in result
                assert "vacation" in result


class TestSendEmployeePortalInviteEmail:
    """Tests for send_employee_portal_invite_email method."""

    @pytest.mark.asyncio
    async def test_sends_invite_email(self):
        """Test sending employee portal invite email."""
        mock_config = MagicMock()
        mock_config.resend_api_key = "test-key"
        mock_config.email_from_address = "noreply@example.com"
        mock_config.email_from_name = "BeanFlow"
        mock_config.frontend_url = "https://app.example.com"

        with patch("app.services.email_service.get_config", return_value=mock_config):
            with patch("app.services.email_service.resend"):
                with patch("asyncio.to_thread") as mock_to_thread:
                    mock_to_thread.return_value = {"id": "email-456"}

                    service = EmailService()

                    result = await service.send_employee_portal_invite_email(
                        to_email="employee@example.com",
                        employee_name="Jane Smith",
                        company_slug="acme-corp",
                    )

                    assert result == {"id": "email-456"}

                    # Verify the correct URL was constructed
                    call_args = mock_to_thread.call_args
                    params = call_args[0][1]
                    assert "employee@example.com" in params["to"]
                    assert "Invited" in params["subject"]


class TestGetEmailService:
    """Tests for get_email_service singleton function."""

    def test_returns_email_service_instance(self):
        """Test that get_email_service returns EmailService instance."""
        mock_config = MagicMock()
        mock_config.resend_api_key = "key"
        mock_config.email_from_address = "noreply@example.com"
        mock_config.email_from_name = None

        # Reset singleton for testing
        import app.services.email_service as email_module

        email_module._email_service = None

        with patch("app.services.email_service.get_config", return_value=mock_config):
            with patch("app.services.email_service.resend"):
                service = get_email_service()
                assert isinstance(service, EmailService)

                # Calling again should return same instance
                service2 = get_email_service()
                assert service is service2

        # Cleanup
        email_module._email_service = None


class TestEmailServiceError:
    """Tests for EmailServiceError exception."""

    def test_error_message(self):
        """Test EmailServiceError exception."""
        error = EmailServiceError("Test error message")
        assert str(error) == "Test error message"
