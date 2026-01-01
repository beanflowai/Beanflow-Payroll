"""Remittance Period Service.

Manages remittance period creation and aggregation from approved payroll runs.
"""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from typing import Any, cast
from uuid import uuid4

from app.services.remittance.period_calculator import get_period_bounds_and_due_date

logger = logging.getLogger(__name__)


class RemittancePeriodService:
    """Service for remittance period operations.

    Handles automatic creation and aggregation of remittance periods
    when payroll runs are approved.
    """

    def __init__(self, supabase: Any, user_id: str, company_id: str):
        """Initialize the service.

        Args:
            supabase: Supabase client instance
            user_id: Current user ID
            company_id: Company ID
        """
        self.supabase = supabase
        self.user_id = user_id
        self.company_id = company_id

    def find_or_create_remittance_period(
        self,
        payroll_run: dict[str, Any],
        remitter_type: str,
    ) -> dict[str, Any]:
        """Find existing remittance period or create new one.

        This is the main entry point for auto-generating remittance periods
        from approved payroll runs.

        Algorithm:
        1. Parse payroll run's period_end to determine the remittance month
        2. Calculate period bounds based on remitter_type
        3. Query for existing period with matching bounds
        4. If exists and run NOT already linked: aggregate deductions
        5. If not exists: create new period

        Args:
            payroll_run: The approved payroll run dict with totals
            remitter_type: Company's remitter classification

        Returns:
            The created or updated remittance period

        Raises:
            ValueError: If required data is missing
        """
        run_id = payroll_run.get("id")
        if not run_id:
            raise ValueError("Payroll run ID is required")

        period_end_str = payroll_run.get("period_end")
        if not period_end_str:
            raise ValueError("Payroll run period_end is required")

        # Parse the payroll run's period_end
        if isinstance(period_end_str, date):
            run_period_end = period_end_str
        else:
            run_period_end = date.fromisoformat(period_end_str)

        # Calculate remittance period bounds
        period_start, period_end, due_date = get_period_bounds_and_due_date(
            run_period_end, remitter_type
        )

        logger.info(
            "Processing remittance for run %s: period %s to %s, due %s",
            run_id,
            period_start,
            period_end,
            due_date,
        )

        # Query for existing period
        existing_result = (
            self.supabase.table("remittance_periods")
            .select("*")
            .eq("company_id", self.company_id)
            .eq("period_start", period_start.isoformat())
            .eq("period_end", period_end.isoformat())
            .execute()
        )

        existing_periods = existing_result.data or []

        if existing_periods:
            period = existing_periods[0]
            existing_run_ids = period.get("payroll_run_ids") or []

            # Check idempotency - skip if already processed
            if str(run_id) in [str(rid) for rid in existing_run_ids]:
                logger.info(
                    "Run %s already linked to remittance period %s, skipping",
                    run_id,
                    period["id"],
                )
                return cast(dict[str, Any], period)

            # Aggregate deductions to existing period
            return self._aggregate_deductions_to_period(
                period, payroll_run, existing_run_ids
            )
        else:
            # Create new period
            return self._create_remittance_period(
                period_start, period_end, due_date, payroll_run, remitter_type
            )

    def _aggregate_deductions_to_period(
        self,
        period: dict[str, Any],
        payroll_run: dict[str, Any],
        existing_run_ids: list[str],
    ) -> dict[str, Any]:
        """Add payroll run deductions to existing period.

        Args:
            period: Existing remittance period
            payroll_run: New payroll run to aggregate
            existing_run_ids: List of already linked run IDs

        Returns:
            Updated remittance period
        """
        run_id = payroll_run["id"]
        period_id = period["id"]

        # Get current amounts (as Decimal for precision)
        current_cpp_employee = Decimal(str(period.get("cpp_employee") or 0))
        current_cpp_employer = Decimal(str(period.get("cpp_employer") or 0))
        current_ei_employee = Decimal(str(period.get("ei_employee") or 0))
        current_ei_employer = Decimal(str(period.get("ei_employer") or 0))
        current_federal_tax = Decimal(str(period.get("federal_tax") or 0))
        current_provincial_tax = Decimal(str(period.get("provincial_tax") or 0))

        # Get run amounts
        run_cpp_employee = Decimal(str(payroll_run.get("total_cpp_employee") or 0))
        run_cpp_employer = Decimal(str(payroll_run.get("total_cpp_employer") or 0))
        run_ei_employee = Decimal(str(payroll_run.get("total_ei_employee") or 0))
        run_ei_employer = Decimal(str(payroll_run.get("total_ei_employer") or 0))
        run_federal_tax = Decimal(str(payroll_run.get("total_federal_tax") or 0))
        run_provincial_tax = Decimal(str(payroll_run.get("total_provincial_tax") or 0))

        # Calculate new totals
        new_cpp_employee = current_cpp_employee + run_cpp_employee
        new_cpp_employer = current_cpp_employer + run_cpp_employer
        new_ei_employee = current_ei_employee + run_ei_employee
        new_ei_employer = current_ei_employer + run_ei_employer
        new_federal_tax = current_federal_tax + run_federal_tax
        new_provincial_tax = current_provincial_tax + run_provincial_tax

        # Append run_id to the list
        updated_run_ids = existing_run_ids + [str(run_id)]

        # Update the period
        update_data = {
            "cpp_employee": float(new_cpp_employee),
            "cpp_employer": float(new_cpp_employer),
            "ei_employee": float(new_ei_employee),
            "ei_employer": float(new_ei_employer),
            "federal_tax": float(new_federal_tax),
            "provincial_tax": float(new_provincial_tax),
            "payroll_run_ids": updated_run_ids,
        }

        update_result = (
            self.supabase.table("remittance_periods")
            .update(update_data)
            .eq("id", period_id)
            .execute()
        )

        if not update_result.data:
            raise ValueError(f"Failed to update remittance period {period_id}")

        logger.info(
            "Aggregated run %s to remittance period %s. "
            "New total: CPP=%.2f, EI=%.2f, Tax=%.2f",
            run_id,
            period_id,
            float(new_cpp_employee + new_cpp_employer),
            float(new_ei_employee + new_ei_employer),
            float(new_federal_tax + new_provincial_tax),
        )

        return cast(dict[str, Any], update_result.data[0])

    def _create_remittance_period(
        self,
        period_start: date,
        period_end: date,
        due_date: date,
        payroll_run: dict[str, Any],
        remitter_type: str,
    ) -> dict[str, Any]:
        """Create a new remittance period.

        Args:
            period_start: Start of remittance period
            period_end: End of remittance period
            due_date: Payment due date
            payroll_run: The payroll run with deduction totals
            remitter_type: Company's remitter classification

        Returns:
            Created remittance period
        """
        run_id = payroll_run["id"]

        # Extract deduction totals from payroll run
        cpp_employee = float(payroll_run.get("total_cpp_employee") or 0)
        cpp_employer = float(payroll_run.get("total_cpp_employer") or 0)
        ei_employee = float(payroll_run.get("total_ei_employee") or 0)
        ei_employer = float(payroll_run.get("total_ei_employer") or 0)
        federal_tax = float(payroll_run.get("total_federal_tax") or 0)
        provincial_tax = float(payroll_run.get("total_provincial_tax") or 0)

        insert_data = {
            "id": str(uuid4()),
            "company_id": self.company_id,
            "user_id": self.user_id,
            "remitter_type": remitter_type,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "due_date": due_date.isoformat(),
            "cpp_employee": cpp_employee,
            "cpp_employer": cpp_employer,
            "ei_employee": ei_employee,
            "ei_employer": ei_employer,
            "federal_tax": federal_tax,
            "provincial_tax": provincial_tax,
            "status": "pending",
            "payroll_run_ids": [str(run_id)],
        }

        insert_result = (
            self.supabase.table("remittance_periods").insert(insert_data).execute()
        )

        if not insert_result.data:
            raise ValueError("Failed to create remittance period")

        created_period = cast(dict[str, Any], insert_result.data[0])
        total = (
            cpp_employee
            + cpp_employer
            + ei_employee
            + ei_employer
            + federal_tax
            + provincial_tax
        )

        logger.info(
            "Created remittance period %s for %s to %s. Total: $%.2f",
            created_period["id"],
            period_start,
            period_end,
            total,
        )

        return created_period
