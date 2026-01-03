"""
Paystub Generation Orchestrator

Orchestrates paystub PDF generation and storage.
Extracted from run_operations.py for better modularity.
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any

import httpx

from app.services.payroll import PaystubDataBuilder, PaystubGenerator
from app.services.payroll.paystub_storage import PaystubStorage
from app.services.payroll_run.model_builders import ModelBuilder
from app.services.payroll_run.ytd_calculator import YtdCalculator

logger = logging.getLogger(__name__)


class PaystubOrchestrator:
    """Orchestrates paystub generation and storage."""

    def __init__(
        self,
        supabase: Any,
        ytd_calculator: YtdCalculator,
        paystub_storage: PaystubStorage,
    ):
        """Initialize paystub orchestrator.

        Args:
            supabase: Supabase client instance
            ytd_calculator: YTD calculator for fetching prior records
            paystub_storage: Storage service for paystubs
        """
        self.supabase = supabase
        self.ytd_calculator = ytd_calculator
        self.paystub_storage = paystub_storage
        self.paystub_builder = PaystubDataBuilder()
        self.paystub_generator = PaystubGenerator()

    async def generate_all_paystubs(
        self,
        run: dict[str, Any],
        records: list[dict[str, Any]],
    ) -> tuple[int, list[str]]:
        """Generate paystubs for all employees in a payroll run.

        Args:
            run: Payroll run data
            records: List of payroll records with employee data

        Returns:
            Tuple of (paystubs_generated_count, error_messages)
        """
        # Build PayrollRun model
        payroll_run = ModelBuilder.build_payroll_run(run)

        # Pre-download company logo (only once for all employees)
        logo_bytes = await self._download_company_logo(records)

        paystubs_generated = 0
        paystub_errors: list[str] = []

        for record_data in records:
            try:
                success, error = await self._generate_single_paystub(
                    record_data=record_data,
                    run=run,
                    payroll_run=payroll_run,
                    logo_bytes=logo_bytes,
                )
                if success:
                    paystubs_generated += 1
                elif error:
                    paystub_errors.append(error)
            except Exception as e:
                logger.error("Failed to generate paystub for record %s: %s", record_data['id'], e)
                paystub_errors.append(f"Record {record_data['id']}: {str(e)}")

        return paystubs_generated, paystub_errors

    async def _download_company_logo(
        self, records: list[dict[str, Any]]
    ) -> bytes | None:
        """Download company logo for paystub generation.

        Args:
            records: List of payroll records

        Returns:
            Logo bytes or None if not available
        """
        first_company_data = records[0]["employees"].get("companies") if records else None
        if not first_company_data:
            return None

        logo_url = first_company_data.get("logo_url")
        if not logo_url:
            return None

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(logo_url)
                response.raise_for_status()
                logo_bytes = response.content
                logger.info("Downloaded company logo from %s (%d bytes)", logo_url, len(logo_bytes))
                return logo_bytes
        except Exception as e:
            logger.warning("Failed to download company logo from %s: %s", logo_url, e)
            return None

    async def _generate_single_paystub(
        self,
        record_data: dict[str, Any],
        run: dict[str, Any],
        payroll_run: Any,
        logo_bytes: bytes | None,
    ) -> tuple[bool, str | None]:
        """Generate a single paystub for an employee.

        Args:
            record_data: Payroll record data
            run: Payroll run data
            payroll_run: PayrollRun model
            logo_bytes: Company logo bytes

        Returns:
            Tuple of (success, error_message)
        """
        employee_data = record_data["employees"]
        company_data = employee_data.get("companies")
        pay_group_data = employee_data.get("pay_groups")

        employee = ModelBuilder.build_employee(employee_data)
        company = ModelBuilder.build_company(company_data) if company_data else None
        pay_group = ModelBuilder.build_pay_group(pay_group_data) if pay_group_data else None
        payroll_record = ModelBuilder.build_payroll_record(record_data)

        if not company:
            logger.warning(
                f"Skipping paystub for record {record_data['id']}: no company data"
            )
            return False, f"Record {record_data['id']}: missing company data"

        # Get prior YTD records
        ytd_records = await self.ytd_calculator.get_ytd_records_for_employee(
            record_data["employee_id"],
            str(run["id"]),
            int(run["pay_date"][:4]),
        )

        masked_sin = "***-***-***"

        paystub_data = self.paystub_builder.build(
            record=payroll_record,
            employee=employee,
            payroll_run=payroll_run,
            pay_group=pay_group,
            company=company,
            ytd_records=ytd_records,
            masked_sin=masked_sin,
            logo_bytes=logo_bytes,
        )

        pdf_bytes = self.paystub_generator.generate_paystub_bytes(paystub_data)

        pay_date = date.fromisoformat(run["pay_date"])
        storage_key = await self.paystub_storage.save_paystub(
            pdf_bytes=pdf_bytes,
            company_name=company.company_name,
            employee_id=record_data["employee_id"],
            pay_date=pay_date,
            record_id=record_data["id"],
        )

        self.supabase.table("payroll_records").update({
            "paystub_generated_at": datetime.now().isoformat(),
            "paystub_storage_key": storage_key,
        }).eq("id", record_data["id"]).execute()

        logger.info(
            "Generated paystub for employee %s %s (record %s), size: %d bytes",
            employee.first_name, employee.last_name, record_data['id'], len(pdf_bytes)
        )

        return True, None
