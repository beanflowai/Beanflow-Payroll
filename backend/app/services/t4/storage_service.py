"""
T4 Storage Service

Stores T4 PDFs and XML files to DigitalOcean Spaces.
"""

from __future__ import annotations

import asyncio
import logging
import re
from uuid import UUID

import boto3
from botocore.exceptions import ClientError

from app.core.config import Config, get_config

logger = logging.getLogger(__name__)


def sanitize_for_path(text: str) -> str:
    """Sanitize text for use in file paths."""
    sanitized = re.sub(r"[\s/\\:*?\"<>|]+", "_", text)
    sanitized = sanitized.strip("_")
    sanitized = re.sub(r"_+", "_", sanitized)
    return sanitized or "unknown"


class T4StorageConfigError(Exception):
    """Raised when DO Spaces configuration is missing or invalid."""

    pass


class T4StorageService:
    """Service for storing T4 PDFs and XML files to DigitalOcean Spaces."""

    def __init__(self, config: Config | None = None):
        """
        Initialize storage client.

        Args:
            config: Application configuration. Uses get_config() if not provided.

        Raises:
            T4StorageConfigError: If required DO Spaces configuration is missing.
        """
        self.config = config or get_config()

        # Validate required configuration
        if not self.config.do_spaces_access_key:
            raise T4StorageConfigError(
                "DO_SPACES_ACCESS_KEY is not configured. "
                "Set the environment variable to enable T4 storage."
            )
        if not self.config.do_spaces_secret_key:
            raise T4StorageConfigError(
                "DO_SPACES_SECRET_KEY is not configured. "
                "Set the environment variable to enable T4 storage."
            )
        if not self.config.do_spaces_bucket:
            raise T4StorageConfigError(
                "DO_SPACES_BUCKET is not configured. "
                "Set the environment variable to enable T4 storage."
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

    def _build_t4_slip_key(
        self,
        company_name: str,
        tax_year: int,
        employee_id: UUID,
        amendment_number: int = 0,
    ) -> str:
        """
        Build storage key for T4 slip PDF.

        Path format: {root_prefix}/{company}/t4/{year}/T4_{employee_id}[_amended_N].pdf

        Args:
            company_name: Company name (will be sanitized)
            tax_year: Tax year
            employee_id: Employee ID
            amendment_number: Amendment number (0 for original)

        Returns:
            Storage key string
        """
        safe_company = sanitize_for_path(company_name)

        if amendment_number > 0:
            filename = f"T4_{employee_id}_amended_{amendment_number}.pdf"
        else:
            filename = f"T4_{employee_id}.pdf"

        parts = [safe_company, "t4", str(tax_year), filename]
        if self.root_prefix:
            parts.insert(0, self.root_prefix)

        return "/".join(parts)

    def _build_t4_summary_key(
        self,
        company_name: str,
        tax_year: int,
    ) -> str:
        """
        Build storage key for T4 Summary PDF.

        Path format: {root_prefix}/{company}/t4/{year}/T4_Summary_{year}.pdf

        Args:
            company_name: Company name (will be sanitized)
            tax_year: Tax year

        Returns:
            Storage key string
        """
        safe_company = sanitize_for_path(company_name)
        filename = f"T4_Summary_{tax_year}.pdf"

        parts = [safe_company, "t4", str(tax_year), filename]
        if self.root_prefix:
            parts.insert(0, self.root_prefix)

        return "/".join(parts)

    def _build_t4_xml_key(
        self,
        company_name: str,
        tax_year: int,
        payroll_account: str,
    ) -> str:
        """
        Build storage key for T4 XML file.

        Path format: {root_prefix}/{company}/t4/{year}/T4_{account}_{year}.xml

        Args:
            company_name: Company name (will be sanitized)
            tax_year: Tax year
            payroll_account: Payroll account number

        Returns:
            Storage key string
        """
        safe_company = sanitize_for_path(company_name)
        safe_account = payroll_account.replace(" ", "")
        filename = f"T4_{safe_account}_{tax_year}.xml"

        parts = [safe_company, "t4", str(tax_year), filename]
        if self.root_prefix:
            parts.insert(0, self.root_prefix)

        return "/".join(parts)

    async def save_t4_slip(
        self,
        pdf_bytes: bytes,
        company_name: str,
        tax_year: int,
        employee_id: UUID,
        amendment_number: int = 0,
    ) -> str:
        """
        Save T4 slip PDF to storage.

        Args:
            pdf_bytes: PDF file content
            company_name: Company name
            tax_year: Tax year
            employee_id: Employee ID
            amendment_number: Amendment number (0 for original)

        Returns:
            Storage key for the saved file

        Raises:
            ClientError: If upload fails
        """
        storage_key = self._build_t4_slip_key(
            company_name, tax_year, employee_id, amendment_number
        )

        logger.info(f"Uploading T4 slip to DO Spaces: {storage_key}")

        await asyncio.to_thread(
            self.s3_client.put_object,
            Bucket=self.bucket,
            Key=storage_key,
            Body=pdf_bytes,
            ContentType="application/pdf",
            ACL="private",
            Metadata={
                "type": "t4_slip",
                "tax_year": str(tax_year),
                "employee_id": str(employee_id),
                "amendment": str(amendment_number),
            },
        )

        logger.info(f"T4 slip uploaded successfully: {storage_key}")
        return storage_key

    async def save_t4_summary(
        self,
        pdf_bytes: bytes,
        company_name: str,
        tax_year: int,
    ) -> str:
        """
        Save T4 Summary PDF to storage.

        Args:
            pdf_bytes: PDF file content
            company_name: Company name
            tax_year: Tax year

        Returns:
            Storage key for the saved file

        Raises:
            ClientError: If upload fails
        """
        storage_key = self._build_t4_summary_key(company_name, tax_year)

        logger.info(f"Uploading T4 Summary to DO Spaces: {storage_key}")

        await asyncio.to_thread(
            self.s3_client.put_object,
            Bucket=self.bucket,
            Key=storage_key,
            Body=pdf_bytes,
            ContentType="application/pdf",
            ACL="private",
            Metadata={
                "type": "t4_summary",
                "tax_year": str(tax_year),
            },
        )

        logger.info(f"T4 Summary uploaded successfully: {storage_key}")
        return storage_key

    async def save_t4_xml(
        self,
        xml_content: str,
        company_name: str,
        tax_year: int,
        payroll_account: str,
    ) -> str:
        """
        Save T4 XML file to storage.

        Args:
            xml_content: XML file content as string
            company_name: Company name
            tax_year: Tax year
            payroll_account: Payroll account number

        Returns:
            Storage key for the saved file

        Raises:
            ClientError: If upload fails
        """
        storage_key = self._build_t4_xml_key(company_name, tax_year, payroll_account)

        logger.info(f"Uploading T4 XML to DO Spaces: {storage_key}")

        await asyncio.to_thread(
            self.s3_client.put_object,
            Bucket=self.bucket,
            Key=storage_key,
            Body=xml_content.encode("utf-8"),
            ContentType="application/xml",
            ACL="private",
            Metadata={
                "type": "t4_xml",
                "tax_year": str(tax_year),
                "payroll_account": payroll_account,
            },
        )

        logger.info(f"T4 XML uploaded successfully: {storage_key}")
        return storage_key

    def generate_presigned_url(
        self,
        storage_key: str,
        expires_in: int = 900,
        filename: str | None = None,
    ) -> str:
        """
        Generate presigned URL for downloading.

        Args:
            storage_key: Storage key of the file
            expires_in: URL expiration in seconds (default 15 minutes)
            filename: Optional filename for Content-Disposition header

        Returns:
            Presigned URL for download

        Raises:
            ClientError: If URL generation fails
        """
        params: dict[str, str] = {"Bucket": self.bucket, "Key": storage_key}

        if filename:
            params["ResponseContentDisposition"] = f'attachment; filename="{filename}"'

        url: str = self.s3_client.generate_presigned_url(
            "get_object",
            Params=params,
            ExpiresIn=expires_in,
        )
        return url

    async def generate_presigned_url_async(
        self,
        storage_key: str,
        expires_in: int = 900,
        filename: str | None = None,
    ) -> str:
        """Generate presigned URL asynchronously."""
        return await asyncio.to_thread(
            self.generate_presigned_url,
            storage_key,
            expires_in,
            filename,
        )

    async def file_exists(self, storage_key: str) -> bool:
        """Check if file exists in storage."""
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

    async def delete_file(self, storage_key: str) -> None:
        """Delete file from storage."""
        try:
            await asyncio.to_thread(
                self.s3_client.delete_object,
                Bucket=self.bucket,
                Key=storage_key,
            )
            logger.info(f"File deleted: {storage_key}")
        except ClientError as e:
            logger.error(f"Failed to delete file {storage_key}: {e}")
            raise

    async def get_file_content(self, storage_key: str) -> bytes:
        """
        Download file content from storage.

        Args:
            storage_key: Storage key of the file

        Returns:
            File content as bytes

        Raises:
            ClientError: If download fails
        """
        response = await asyncio.to_thread(
            self.s3_client.get_object,
            Bucket=self.bucket,
            Key=storage_key,
        )
        content: bytes = response["Body"].read()
        return content


# Singleton instance
_t4_storage: T4StorageService | None = None


def get_t4_storage() -> T4StorageService:
    """Get T4StorageService singleton instance."""
    global _t4_storage
    if _t4_storage is None:
        _t4_storage = T4StorageService()
    return _t4_storage
