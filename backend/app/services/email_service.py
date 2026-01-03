"""Email service for sending emails via Resend API.

This service provides email sending capabilities using Resend API
for employee portal notifications.
"""

import asyncio
import logging
import urllib.parse
from typing import Any

import resend
from pydantic import BaseModel, EmailStr

from app.core.config import get_config

logger = logging.getLogger(__name__)


class EmailMessage(BaseModel):
    """Email message model for validation and type safety."""

    to: list[EmailStr]
    subject: str
    html_content: str
    from_email: EmailStr | None = None
    from_name: str | None = None


class EmailServiceError(Exception):
    """Email service related errors."""

    pass


class EmailService:
    """Service for sending emails via Resend API."""

    def __init__(self) -> None:
        """Initialize email service."""
        self.config = get_config()
        self._setup_resend()

    def _setup_resend(self) -> None:
        """Setup Resend API client."""
        if self.config.resend_api_key:
            resend.api_key = self.config.resend_api_key
            logger.info("Resend API client initialized")
        else:
            logger.warning("Resend API key not configured - email sending disabled")

    def _build_from_address(self, from_email: str | None, from_name: str | None) -> str:
        """Build the from address string for Resend."""
        email = from_email or self.config.email_from_address
        name = from_name or self.config.email_from_name

        if name:
            return f"{name} <{email}>"
        return email

    async def send_email(self, message: EmailMessage) -> dict[str, Any]:
        """Send an email via Resend API.

        Args:
            message: Email message to send

        Returns:
            Resend API response

        Raises:
            EmailServiceError: If sending fails
        """
        if not self.config.resend_api_key:
            raise EmailServiceError("Resend API key not configured")

        from_address = self._build_from_address(message.from_email, message.from_name)

        params: resend.Emails.SendParams = {
            "from": from_address,
            "to": list(message.to),
            "subject": message.subject,
            "html": message.html_content,
        }

        try:
            logger.info(f"Sending email to {message.to}")
            logger.debug(f"Email subject: '{message.subject}'")

            # Send email via Resend API (run in thread to avoid blocking)
            response = await asyncio.to_thread(resend.Emails.send, params)

            logger.info(f"Email sent successfully. Response: {response}")
            return response  # type: ignore[return-value]

        except Exception as e:
            error_msg = f"Failed to send email: {str(e)}"
            logger.error(error_msg)
            raise EmailServiceError(error_msg) from e

    def create_employee_portal_invite_content(
        self,
        employee_name: str,
        login_url: str,
    ) -> str:
        """Create HTML content for employee portal invite email.

        Args:
            employee_name: Employee's name
            login_url: The portal login page URL with email parameter

        Returns:
            HTML email content
        """
        from datetime import datetime

        current_year = datetime.now().year
        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Employee Portal Access - BeanFlow Payroll</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f4f7fa; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">
  <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f4f7fa;">
    <tr>
      <td align="center" style="padding: 40px 20px;">
        <table role="presentation" cellpadding="0" cellspacing="0" width="600" style="max-width: 600px; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);">
          <!-- Header -->
          <tr>
            <td style="padding: 40px 40px 30px; text-align: center; background: linear-gradient(135deg, #10b981 0%, #059669 100%); border-radius: 12px 12px 0 0;">
              <div style="width: 70px; height: 70px; background-color: rgba(255, 255, 255, 0.2); border-radius: 50%; display: inline-block; line-height: 70px; margin-bottom: 16px;">
                <span style="font-size: 32px; color: #ffffff;">&#x1F389;</span>
              </div>
              <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 600;">BeanFlow Payroll</h1>
              <p style="margin: 8px 0 0; color: rgba(255, 255, 255, 0.9); font-size: 14px;">Employee Portal</p>
            </td>
          </tr>

          <!-- Content -->
          <tr>
            <td style="padding: 40px;">
              <h2 style="margin: 0 0 16px; color: #1f2937; font-size: 22px; font-weight: 600; text-align: center;">Welcome, {employee_name}!</h2>
              <p style="margin: 0 0 24px; color: #6b7280; font-size: 16px; line-height: 24px; text-align: center;">
                You've been invited to access your Employee Portal. View your pay stubs, T4 slips, and manage your profile.
              </p>

              <!-- Features List -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 24px;">
                <tr>
                  <td style="padding: 16px; background-color: #f0fdf4; border-radius: 8px;">
                    <p style="margin: 0 0 12px; color: #166534; font-size: 14px; font-weight: 600;">With your Employee Portal, you can:</p>
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                      <tr><td style="padding: 4px 0; color: #15803d; font-size: 14px;">&#x2713; View and download your pay stubs</td></tr>
                      <tr><td style="padding: 4px 0; color: #15803d; font-size: 14px;">&#x2713; Access your T4 tax slips</td></tr>
                      <tr><td style="padding: 4px 0; color: #15803d; font-size: 14px;">&#x2713; Check vacation and sick leave balances</td></tr>
                      <tr><td style="padding: 4px 0; color: #15803d; font-size: 14px;">&#x2713; Update your personal information</td></tr>
                    </table>
                  </td>
                </tr>
              </table>

              <!-- CTA Button -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td align="center" style="padding: 16px 0 32px;">
                    <a href="{login_url}" target="_blank" style="display: inline-block; padding: 16px 48px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: #ffffff; text-decoration: none; font-size: 16px; font-weight: 600; border-radius: 8px; box-shadow: 0 4px 14px rgba(16, 185, 129, 0.4);">
                      Go to Login Page
                    </a>
                  </td>
                </tr>
              </table>

              <!-- Info Notice -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color: #eff6ff; border-radius: 8px; border: 1px solid #93c5fd;">
                <tr>
                  <td style="padding: 16px;">
                    <p style="margin: 0; color: #1e40af; font-size: 13px; line-height: 20px;">
                      <strong style="color: #1e3a8a;">Note:</strong> On the login page, enter your email and click "Send Verification Code" to receive a one-time code.
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding: 24px 40px 32px; background-color: #f9fafb; border-radius: 0 0 12px 12px; border-top: 1px solid #e5e7eb;">
              <p style="margin: 0 0 8px; color: #9ca3af; font-size: 12px; text-align: center;">
                If you didn't expect this invitation, please ignore this email.
              </p>
              <p style="margin: 0; color: #9ca3af; font-size: 12px; text-align: center;">
                &copy; {current_year} BeanFlow Payroll. All rights reserved.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""
        return html_template

    async def send_employee_portal_invite_email(
        self,
        to_email: str,
        employee_name: str,
        company_slug: str,
    ) -> dict[str, Any]:
        """Send an employee portal invite email.

        Used for existing users who can log in via OTP.
        Only includes login link (no verification code).

        Args:
            to_email: Recipient email address
            employee_name: Employee's full name
            company_slug: Company URL slug for portal routing

        Returns:
            Resend API response
        """
        # Build login URL with company slug and email parameter
        login_url = f"{self.config.frontend_url}/employee/{company_slug}/auth?email={urllib.parse.quote(to_email)}"

        subject = "You're Invited to BeanFlow Employee Portal"

        html_content = self.create_employee_portal_invite_content(
            employee_name=employee_name,
            login_url=login_url,
        )

        message = EmailMessage(
            to=[to_email],
            subject=subject,
            html_content=html_content,
        )

        return await self.send_email(message)


# Global email service instance
_email_service: EmailService | None = None


def get_email_service() -> EmailService:
    """Get the email service singleton instance."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
