"""Paystub storage service for DigitalOcean Spaces."""

import asyncio
import logging
import re
from datetime import date

import boto3
from botocore.exceptions import ClientError

from app.core.config import Config, get_config

logger = logging.getLogger(__name__)


def sanitize_for_path(text: str) -> str:
    """Sanitize text for use in file paths.

    Replaces spaces and special characters with underscores.
    """
    # Replace spaces and common special chars with underscore
    sanitized = re.sub(r"[\s/\\:*?\"<>|]+", "_", text)
    # Remove leading/trailing underscores
    sanitized = sanitized.strip("_")
    # Collapse multiple underscores
    sanitized = re.sub(r"_+", "_", sanitized)
    return sanitized or "unknown"


class PaystubStorageConfigError(Exception):
    """Raised when DO Spaces configuration is missing or invalid."""

    pass


class PaystubStorage:
    """Service for storing and retrieving paystubs from DigitalOcean Spaces."""

    def __init__(self, config: Config | None = None):
        """Initialize storage client.

        Args:
            config: Application configuration. Uses get_config() if not provided.

        Raises:
            PaystubStorageConfigError: If required DO Spaces configuration is missing.
        """
        self.config = config or get_config()

        # Validate required configuration
        if not self.config.do_spaces_access_key:
            raise PaystubStorageConfigError(
                "DO_SPACES_ACCESS_KEY is not configured. "
                "Set the environment variable to enable paystub storage."
            )
        if not self.config.do_spaces_secret_key:
            raise PaystubStorageConfigError(
                "DO_SPACES_SECRET_KEY is not configured. "
                "Set the environment variable to enable paystub storage."
            )
        if not self.config.do_spaces_bucket:
            raise PaystubStorageConfigError(
                "DO_SPACES_BUCKET is not configured. "
                "Set the environment variable to enable paystub storage."
            )

        # Build endpoint URL
        endpoint = self.config.do_spaces_endpoint
        if not endpoint.startswith(("http://", "https://")):
            endpoint = f"https://{endpoint}"

        self.s3_client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=self.config.do_spaces_access_key,
            aws_secret_access_key=self.config.do_spaces_secret_key,
            region_name=self.config.do_spaces_region,
        )
        self.bucket = self.config.do_spaces_bucket
        self.root_prefix = self.config.do_spaces_root_prefix

    def _build_storage_key(
        self,
        company_name: str,
        employee_id: str,
        pay_date: date,
        record_id: str | None = None,
    ) -> str:
        """Build storage key for paystub.

        Path format: {root_prefix}/{company_name}/{employee_id}/{year}/paystub_{pay_date}_{record_id}.pdf

        The record_id suffix ensures uniqueness when the same employee is processed
        multiple times for the same pay date (e.g., error retries, corrections).

        Args:
            company_name: Company name (will be sanitized)
            employee_id: Employee ID
            pay_date: Pay date for the paystub
            record_id: Payroll record ID for uniqueness (optional for backwards compat)

        Returns:
            Storage key string
        """
        safe_company = sanitize_for_path(company_name)
        year = str(pay_date.year)

        # Include record_id in filename for uniqueness
        if record_id:
            # Use first 8 chars of record_id to keep filename reasonable
            short_id = record_id.replace("-", "")[:8]
            filename = f"paystub_{pay_date.isoformat()}_{short_id}.pdf"
        else:
            filename = f"paystub_{pay_date.isoformat()}.pdf"

        parts = [safe_company, employee_id, year, filename]
        if self.root_prefix:
            parts.insert(0, self.root_prefix)

        return "/".join(parts)

    async def save_paystub(
        self,
        pdf_bytes: bytes,
        company_name: str,
        employee_id: str,
        pay_date: date,
        record_id: str | None = None,
    ) -> str:
        """Save paystub PDF to DigitalOcean Spaces.

        Args:
            pdf_bytes: PDF file content
            company_name: Company name
            employee_id: Employee ID
            pay_date: Pay date for the paystub
            record_id: Payroll record ID for uniqueness (recommended)

        Returns:
            Storage key for the saved file

        Raises:
            ClientError: If upload fails
        """
        storage_key = self._build_storage_key(
            company_name, employee_id, pay_date, record_id
        )

        logger.info(f"Uploading paystub to DO Spaces: {storage_key}")

        await asyncio.to_thread(
            self.s3_client.put_object,
            Bucket=self.bucket,
            Key=storage_key,
            Body=pdf_bytes,
            ContentType="application/pdf",
            ACL="private",
            Metadata={
                "company_name": sanitize_for_path(company_name),
                "employee_id": employee_id,
                "pay_date": pay_date.isoformat(),
            },
        )

        logger.info(f"Paystub uploaded successfully: {storage_key}")
        return storage_key

    def generate_presigned_url(
        self,
        storage_key: str,
        expires_in: int = 900,
    ) -> str:
        """Generate presigned URL for downloading paystub.

        Args:
            storage_key: Storage key of the paystub
            expires_in: URL expiration in seconds (default 15 minutes)

        Returns:
            Presigned URL for download

        Raises:
            ClientError: If URL generation fails
        """
        url: str = self.s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": storage_key},
            ExpiresIn=expires_in,
        )
        return url

    async def generate_presigned_url_async(
        self,
        storage_key: str,
        expires_in: int = 900,
    ) -> str:
        """Generate presigned URL asynchronously.

        Args:
            storage_key: Storage key of the paystub
            expires_in: URL expiration in seconds (default 15 minutes)

        Returns:
            Presigned URL for download
        """
        return await asyncio.to_thread(
            self.generate_presigned_url,
            storage_key,
            expires_in,
        )

    async def paystub_exists(self, storage_key: str) -> bool:
        """Check if paystub exists in storage.

        Args:
            storage_key: Storage key to check

        Returns:
            True if file exists, False otherwise
        """
        try:
            await asyncio.to_thread(
                self.s3_client.head_object,
                Bucket=self.bucket,
                Key=storage_key,
            )
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            raise

    async def delete_paystub(self, storage_key: str) -> None:
        """Delete paystub from storage.

        Args:
            storage_key: Storage key of the paystub to delete

        Raises:
            ClientError: If deletion fails
        """
        try:
            await asyncio.to_thread(
                self.s3_client.delete_object,
                Bucket=self.bucket,
                Key=storage_key,
            )
            logger.info(f"Paystub deleted: {storage_key}")
        except ClientError as e:
            logger.error(f"Failed to delete paystub {storage_key}: {e}")
            raise


# Singleton instance
_paystub_storage: PaystubStorage | None = None


def get_paystub_storage() -> PaystubStorage:
    """Get PaystubStorage singleton instance."""
    global _paystub_storage
    if _paystub_storage is None:
        _paystub_storage = PaystubStorage()
    return _paystub_storage
