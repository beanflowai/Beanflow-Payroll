"""
Payroll Run Service - Manages payroll run lifecycle and operations

Provides:
- Record updates in draft state
- Recalculation of payroll deductions
- Status transitions (draft -> pending_approval -> approved)

This is the public facade that delegates to specialized modules in payroll_run/.
"""

from __future__ import annotations

import logging
from typing import Any, cast
from uuid import UUID

from app.core.supabase_client import get_supabase_client
from app.services.payroll_run import (
    EmployeeManagement,
    PayrollRunOperations,
    YtdCalculator,
)

logger = logging.getLogger(__name__)


class PayrollRunService:
    """Service for payroll run operations - public API facade."""

    def __init__(self, user_id: str, company_id: str):
        """Initialize service with user context."""
        self.user_id = user_id
        self.company_id = company_id
        self.supabase = get_supabase_client()

        # Initialize calculators
        self._ytd_calculator = YtdCalculator(
            self.supabase, user_id, company_id
        )

        # Initialize employee management (needs reference to create_records)
        self._emp_mgmt = EmployeeManagement(
            supabase=self.supabase,
            user_id=user_id,
            company_id=company_id,
            ytd_calculator=self._ytd_calculator,
            get_run_func=self.get_run,
        )

        # Initialize run operations
        self._run_ops = PayrollRunOperations(
            supabase=self.supabase,
            user_id=user_id,
            company_id=company_id,
            ytd_calculator=self._ytd_calculator,
            get_run_func=self.get_run,
            get_run_records_func=self.get_run_records,
            create_records_func=self._emp_mgmt.create_records_for_employees,
        )

    # =========================================================================
    # CRUD Operations (kept inline as they are simple)
    # =========================================================================

    async def get_run(self, run_id: UUID) -> dict[str, Any] | None:
        """Get a payroll run by ID.

        Note: RLS policies using auth.uid() will automatically filter by user.
        The explicit user_id/company_id filters provide defense-in-depth.
        """
        result = self.supabase.table("payroll_runs").select("*").eq(
            "id", str(run_id)
        ).eq("user_id", self.user_id).eq("company_id", self.company_id).execute()

        if result.data and len(result.data) > 0:
            return cast(dict[str, Any], result.data[0])
        return None

    async def list_runs(
        self,
        run_status: str | None = None,
        exclude_status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List payroll runs with optional filtering.

        Args:
            run_status: Filter by specific status (e.g., 'draft', 'pending_approval')
            exclude_status: Exclude runs with this status
            limit: Maximum number of runs to return
            offset: Number of runs to skip for pagination

        Returns:
            Dictionary with 'runs' list and 'total' count
        """
        query = self.supabase.table("payroll_runs").select(
            "*", count="exact"
        ).eq("user_id", self.user_id).eq("company_id", self.company_id)

        if run_status:
            query = query.eq("status", run_status)

        if exclude_status:
            query = query.neq("status", exclude_status)

        query = query.order("pay_date", desc=True).range(offset, offset + limit - 1)

        result = query.execute()

        return {
            "runs": result.data or [],
            "total": result.count or 0,
        }

    async def get_record(self, record_id: UUID | str) -> dict[str, Any] | None:
        """Get a single payroll record by ID."""
        result = self.supabase.table("payroll_records").select("*").eq(
            "id", str(record_id)
        ).eq("user_id", self.user_id).eq("company_id", self.company_id).execute()

        if result.data and len(result.data) > 0:
            return cast(dict[str, Any], result.data[0])
        return None

    async def get_run_records(self, run_id: UUID) -> list[dict[str, Any]]:
        """Get all records for a payroll run with employee info."""
        result = self.supabase.table("payroll_records").select(
            """
            *,
            employees!inner (
                id,
                first_name,
                last_name,
                province_of_employment,
                pay_frequency,
                annual_salary,
                hourly_rate,
                federal_additional_claims,
                provincial_additional_claims,
                is_cpp_exempt,
                is_ei_exempt,
                cpp2_exempt,
                vacation_config,
                vacation_balance,
                pay_group_id,
                pay_groups (
                    id,
                    name,
                    pay_frequency,
                    employment_type,
                    group_benefits
                )
            )
            """
        ).eq("payroll_run_id", str(run_id)).eq("user_id", self.user_id).eq(
            "company_id", self.company_id
        ).execute()

        return result.data or []

    async def update_record(
        self, run_id: UUID, record_id: UUID, input_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update a payroll record's input_data in draft state.

        Raises:
            ValueError: If run is not in draft status
        """
        # Verify run is in draft status
        run = await self.get_run(run_id)
        if not run:
            raise ValueError("Payroll run not found")

        if run["status"] != "draft":
            raise ValueError(
                f"Cannot update record: payroll run is in '{run['status']}' status, "
                "not 'draft'"
            )

        # Get current record
        record_result = self.supabase.table("payroll_records").select("*").eq(
            "id", str(record_id)
        ).eq("payroll_run_id", str(run_id)).eq("user_id", self.user_id).execute()

        if not record_result.data or len(record_result.data) == 0:
            raise ValueError("Payroll record not found")

        current_record = record_result.data[0]

        # Merge with existing input_data
        existing_input_data = current_record.get("input_data") or {}
        merged_input_data = {**existing_input_data, **input_data}

        # Update the record
        update_result = self.supabase.table("payroll_records").update({
            "input_data": merged_input_data,
            "is_modified": True
        }).eq("id", str(record_id)).execute()

        if not update_result.data or len(update_result.data) == 0:
            raise ValueError("Failed to update payroll record")

        return cast(dict[str, Any], update_result.data[0])

    async def check_has_modified_records(self, run_id: UUID) -> bool:
        """Check if any records in the run have is_modified = True."""
        result = self.supabase.table("payroll_records").select("id").eq(
            "payroll_run_id", str(run_id)
        ).eq("is_modified", True).limit(1).execute()

        return bool(result.data and len(result.data) > 0)

    async def delete_run(self, run_id: UUID) -> dict[str, Any]:
        """Delete a draft payroll run.

        Only draft runs can be deleted. The associated payroll_records will be
        automatically deleted via CASCADE.

        Raises:
            ValueError: If run is not in draft status
        """
        run = await self.get_run(run_id)
        if not run:
            raise ValueError("Payroll run not found")

        if run["status"] != "draft":
            raise ValueError(
                f"Cannot delete: payroll run is in '{run['status']}' status. "
                "Only draft runs can be deleted."
            )

        self.supabase.table("payroll_runs").delete().eq(
            "id", str(run_id)
        ).eq("user_id", self.user_id).eq("company_id", self.company_id).execute()

        return {
            "deleted": True,
            "run_id": str(run_id),
        }

    # =========================================================================
    # Delegated Operations - Run Lifecycle
    # =========================================================================

    async def create_or_get_run(self, pay_date: str) -> dict[str, Any]:
        """Create a new draft payroll run or get existing one for a pay date."""
        return await self._run_ops.create_or_get_run(pay_date)

    async def create_or_get_run_by_period_end(self, period_end: str) -> dict[str, Any]:
        """Create a new draft payroll run or get existing one for a period end.

        This is the new entry point that uses period_end as the primary identifier.
        The pay_date is auto-calculated based on province regulations.
        """
        return await self._run_ops.create_or_get_run_by_period_end(period_end)

    async def recalculate_run(self, run_id: UUID) -> dict[str, Any]:
        """Recalculate all records in a draft payroll run."""
        return await self._run_ops.recalculate_run(run_id)

    async def finalize_run(self, run_id: UUID) -> dict[str, Any]:
        """Finalize a draft payroll run, transitioning to pending_approval."""
        return await self._run_ops.finalize_run(run_id)

    async def approve_run(
        self, run_id: UUID, approved_by: str | None = None
    ) -> dict[str, Any]:
        """Approve a pending_approval payroll run."""
        return await self._run_ops.approve_run(run_id, approved_by)

    async def send_paystubs(self, run_id: UUID) -> dict[str, Any]:
        """Send paystub emails to all employees."""
        return await self._run_ops.send_paystubs(run_id)

    # =========================================================================
    # Delegated Operations - Employee Management
    # =========================================================================

    async def sync_employees(self, run_id: UUID) -> dict[str, Any]:
        """Sync new employees to a draft payroll run."""
        return await self._emp_mgmt.sync_employees(run_id)

    async def add_employee_to_run(
        self, run_id: UUID, employee_id: str
    ) -> dict[str, Any]:
        """Add a single employee to a draft payroll run."""
        return await self._emp_mgmt.add_employee_to_run(run_id, employee_id)

    async def remove_employee_from_run(
        self, run_id: UUID, employee_id: str
    ) -> dict[str, Any]:
        """Remove an employee from a draft payroll run."""
        return await self._emp_mgmt.remove_employee_from_run(run_id, employee_id)


# Factory function for creating service instance
def get_payroll_run_service(user_id: str, company_id: str) -> PayrollRunService:
    """Create a PayrollRunService instance with user context."""
    return PayrollRunService(user_id, company_id)
