"""
Payroll Run Operations

Core lifecycle operations for payroll runs:
- create_or_get_run
- recalculate_run
- finalize_run
- approve_run
- send_paystubs

This module serves as an orchestration layer, delegating to specialized modules:
- input_preparation: Prepares calculation inputs
- result_persister: Persists calculation results
- paystub_orchestrator: Generates paystubs
- vacation_manager: Manages vacation balances
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, cast
from uuid import UUID

from app.services.payroll import PayrollEngine
from app.services.payroll.paystub_storage import (
    PaystubStorage,
    PaystubStorageConfigError,
)
from app.services.payroll_run.constants import (
    calculate_next_period_end,
    calculate_pay_date,
    extract_year_from_date,
    get_province_name,
    is_pay_date_compliant,
)
from app.services.payroll_run.holiday_pay_calculator import HolidayPayCalculator
from app.services.payroll_run.input_preparation import PayrollInputPreparer
from app.services.payroll_run.paystub_orchestrator import PaystubOrchestrator
from app.services.payroll_run.result_persister import PayrollResultPersister
from app.services.payroll_run.vacation_manager import VacationManager
from app.services.payroll_run.ytd_calculator import YtdCalculator
from app.services.remittance import RemittancePeriodService

logger = logging.getLogger(__name__)


class PayrollRunOperations:
    """Core payroll run lifecycle operations."""

    def __init__(
        self,
        supabase: Any,
        user_id: str,
        company_id: str,
        ytd_calculator: YtdCalculator,
        get_run_func: Any,
        get_run_records_func: Any,
        create_records_func: Any,
        sync_employees_func: Any | None = None,
    ):
        """Initialize payroll run operations.

        Args:
            supabase: Supabase client instance
            user_id: Current user ID
            company_id: Current company ID
            ytd_calculator: YTD calculator instance
            get_run_func: Function to get a payroll run by ID
            get_run_records_func: Function to get run records with employee info
            create_records_func: Function to create records for employees
            sync_employees_func: Optional function to sync employees for a draft run
        """
        self.supabase = supabase
        self.user_id = user_id
        self.company_id = company_id
        self.ytd_calculator = ytd_calculator
        self.holiday_calculator = HolidayPayCalculator(supabase, user_id, company_id)
        self._get_run = get_run_func
        self._get_run_records = get_run_records_func
        self._create_records_for_employees = create_records_func
        self._sync_employees = sync_employees_func

        # Initialize sub-modules
        self.input_preparer = PayrollInputPreparer(
            supabase=supabase,
            user_id=user_id,
            company_id=company_id,
            ytd_calculator=ytd_calculator,
            holiday_calculator=self.holiday_calculator,
        )
        self.result_persister = PayrollResultPersister(supabase)
        self.vacation_manager = VacationManager(supabase)

    async def recalculate_run(self, run_id: UUID) -> dict[str, Any]:
        """Recalculate all records in a draft payroll run.

        1. Reads input_data from all payroll_records
        2. Calls PayrollEngine.calculate_batch()
        3. Updates payroll_records with new CPP/EI/Tax values
        4. Updates payroll_runs summary totals
        5. Clears is_modified flags

        Returns:
            Updated payroll run data

        Raises:
            ValueError: If run is not in draft status
        """
        # Verify run is in draft status
        run = await self._get_run(run_id)
        if not run:
            raise ValueError("Payroll run not found")

        if run["status"] != "draft":
            raise ValueError(
                f"Cannot recalculate: payroll run is in '{run['status']}' status, "
                "not 'draft'"
            )

        # Get all records with employee info
        records = await self._get_run_records(run_id)
        if not records:
            raise ValueError("No records found for payroll run")

        # Parse dates
        pay_date_str = run.get("pay_date", "")
        tax_year = extract_year_from_date(pay_date_str)
        pay_date_obj = datetime.strptime(pay_date_str, "%Y-%m-%d").date() if pay_date_str else None

        period_start_str = run.get("period_start", "")
        period_end_str = run.get("period_end", "")
        period_start_obj = datetime.strptime(period_start_str, "%Y-%m-%d").date() if period_start_str else None
        period_end_obj = datetime.strptime(period_end_str, "%Y-%m-%d").date() if period_end_str else None

        # 1. Prepare calculation inputs
        calculation_inputs, record_map = await self.input_preparer.prepare_all_inputs(
            run=run,
            records=records,
            run_id=str(run_id),
            tax_year=tax_year,
            pay_date=pay_date_obj,
            period_start=period_start_obj,
            period_end=period_end_obj,
        )

        # 2. Calculate using PayrollEngine
        engine = PayrollEngine(year=tax_year)
        results = engine.calculate_batch(calculation_inputs)

        # 3. Get prior YTD for persistence
        employee_ids = [record["employee_id"] for record in records]
        prior_ytd_data = self.ytd_calculator.get_prior_ytd_for_employees(
            employee_ids, str(run_id), year=tax_year
        )

        # 4. Persist results
        self.result_persister.persist_results(results, record_map, prior_ytd_data)
        self.result_persister.update_run_totals(str(run_id), results)

        return await self._get_run(run_id) or {}

    async def finalize_run(self, run_id: UUID) -> dict[str, Any]:
        """Finalize a draft payroll run, transitioning to pending_approval.

        Returns:
            Updated payroll run data

        Raises:
            ValueError: If run is not in draft or has modified records
        """
        run = await self._get_run(run_id)
        if not run:
            raise ValueError("Payroll run not found")

        if run["status"] != "draft":
            raise ValueError(
                f"Cannot finalize: payroll run is in '{run['status']}' status, "
                "not 'draft'"
            )

        # Check for modified records
        modified_result = self.supabase.table("payroll_records").select(
            "id"
        ).eq("payroll_run_id", str(run_id)).eq("is_modified", True).execute()

        if modified_result.data and len(modified_result.data) > 0:
            raise ValueError(
                f"Cannot finalize: {len(modified_result.data)} record(s) have unsaved "
                "changes. Please recalculate before finalizing."
            )

        update_result = self.supabase.table("payroll_runs").update({
            "status": "pending_approval"
        }).eq("id", str(run_id)).execute()

        if not update_result.data or len(update_result.data) == 0:
            raise ValueError("Failed to update payroll run status")

        return cast(dict[str, Any], update_result.data[0])

    async def approve_run(
        self, run_id: UUID, approved_by: str | None = None
    ) -> dict[str, Any]:
        """Approve a pending_approval payroll run.

        Generates paystub PDFs, stores them, and updates status to approved.

        Returns:
            Updated payroll run data with paystubs_generated count

        Raises:
            ValueError: If run is not in pending_approval status
        """
        run = await self._get_run(run_id)
        if not run:
            raise ValueError("Payroll run not found")

        if run["status"] != "pending_approval":
            raise ValueError(
                f"Cannot approve: payroll run is in '{run['status']}' status, "
                "not 'pending_approval'"
            )

        # Get all records with employee, pay group, and company info
        records = await self._get_records_with_full_info(run_id)
        if not records:
            raise ValueError("No records found for payroll run")

        # 1. Validate vacation balances
        balance_errors = self.vacation_manager.validate_balances(records)
        if balance_errors:
            error_msg = "Cannot approve: insufficient vacation balance. "
            error_msg += "; ".join(balance_errors[:5])
            if len(balance_errors) > 5:
                error_msg += f" ... and {len(balance_errors) - 5} more"
            raise ValueError(error_msg)

        # 2. Generate paystubs
        try:
            paystub_storage = PaystubStorage()
        except PaystubStorageConfigError as e:
            raise ValueError(
                f"Paystub storage is not configured. Cannot approve payroll run. "
                f"Please configure DO Spaces environment variables. Error: {e}"
            ) from e

        paystub_orchestrator = PaystubOrchestrator(
            supabase=self.supabase,
            ytd_calculator=self.ytd_calculator,
            paystub_storage=paystub_storage,
        )

        paystubs_generated, paystub_errors = await paystub_orchestrator.generate_all_paystubs(
            run=run,
            records=records,
        )

        if paystub_errors:
            error_summary = f"Failed to generate {len(paystub_errors)} paystub(s). "
            error_summary += "Cannot approve payroll run until all paystubs are generated. "
            error_summary += f"Errors: {'; '.join(paystub_errors[:5])}"
            if len(paystub_errors) > 5:
                error_summary += f" ... and {len(paystub_errors) - 5} more"
            raise ValueError(error_summary)

        # 3. Update vacation balances
        await self.vacation_manager.update_balances(records)

        # 4. Update run status
        update_data: dict[str, Any] = {
            "status": "approved",
            "approved_at": datetime.now().isoformat(),
        }
        if approved_by:
            update_data["approved_by"] = approved_by

        update_result = self.supabase.table("payroll_runs").update(
            update_data
        ).eq("id", str(run_id)).execute()

        if not update_result.data or len(update_result.data) == 0:
            raise ValueError("Failed to update payroll run status")

        # 5. Update pay group next_period_end
        self._update_pay_group_periods(records, run)

        # 6. Auto-generate/aggregate remittance period
        try:
            self._update_remittance_period(update_result.data[0])
        except Exception as e:
            logger.error("Failed to update remittance period: %s", e)

        return {
            **update_result.data[0],
            "paystubs_generated": paystubs_generated,
        }

    async def _get_records_with_full_info(self, run_id: UUID) -> list[dict[str, Any]]:
        """Get payroll records with full employee, company, and pay group info."""
        records_result = self.supabase.table("payroll_records").select(
            """
            *,
            employees!inner (
                id, first_name, last_name, email, sin_encrypted,
                province_of_employment, pay_frequency, employment_type,
                annual_salary, hourly_rate, federal_additional_claims,
                provincial_additional_claims, is_cpp_exempt, is_ei_exempt,
                cpp2_exempt, hire_date, termination_date, vacation_config,
                vacation_balance, address_street, address_city,
                address_postal_code, occupation, company_id, pay_group_id,
                companies (
                    id, company_name, business_number, payroll_account_number,
                    province, address_street, address_city, address_postal_code,
                    remitter_type, auto_calculate_deductions, send_paystub_emails,
                    logo_url
                ),
                pay_groups (
                    id, name, description, pay_frequency, employment_type,
                    next_period_end, period_start_day, leave_enabled,
                    overtime_policy, wcb_config, group_benefits
                )
            )
            """
        ).eq("payroll_run_id", str(run_id)).eq(
            "user_id", self.user_id
        ).eq("company_id", self.company_id).execute()

        return records_result.data or []

    def _update_pay_group_periods(
        self, records: list[dict[str, Any]], run: dict[str, Any]
    ) -> None:
        """Update next_period_end for all affected pay groups."""
        pay_group_updates: dict[str, str] = {}
        for record_data in records:
            pay_group_data = record_data["employees"].get("pay_groups")
            if pay_group_data:
                pg_id = pay_group_data["id"]
                if pg_id not in pay_group_updates:
                    pay_group_updates[pg_id] = pay_group_data.get("pay_frequency", "bi_weekly")

        current_period_end = datetime.strptime(run["period_end"], "%Y-%m-%d").date()
        for pg_id, pay_frequency in pay_group_updates.items():
            next_period_end = calculate_next_period_end(current_period_end, pay_frequency)
            self.supabase.table("pay_groups").update({
                "next_period_end": next_period_end.strftime("%Y-%m-%d")
            }).eq("id", pg_id).execute()
            logger.info("Updated pay_group %s next_period_end to %s", pg_id, next_period_end)

    def _update_remittance_period(self, run: dict[str, Any]) -> None:
        """Auto-generate or aggregate remittance period for approved run.

        Args:
            run: The approved payroll run data with totals
        """
        company_result = (
            self.supabase.table("companies")
            .select("remitter_type")
            .eq("id", self.company_id)
            .single()
            .execute()
        )

        if not company_result.data:
            logger.warning(
                "Company %s not found for remittance period generation",
                self.company_id,
            )
            return

        remitter_type = company_result.data.get("remitter_type", "regular")

        service = RemittancePeriodService(
            self.supabase, self.user_id, self.company_id
        )
        result = service.find_or_create_remittance_period(run, remitter_type)
        logger.info(
            "Remittance period %s updated for run %s",
            result.get("id"),
            run.get("id"),
        )

    async def send_paystubs(self, run_id: UUID) -> dict[str, Any]:
        """Send paystub emails to all employees.

        Returns:
            Dict with 'sent' count and optional 'errors' list

        Raises:
            ValueError: If run is not in approved status
        """
        run = await self._get_run(run_id)
        if not run:
            raise ValueError("Payroll run not found")

        if run["status"] != "approved":
            raise ValueError(
                f"Cannot send paystubs: payroll run is in '{run['status']}' status, "
                "not 'approved'"
            )

        records_result = self.supabase.table("payroll_records").select(
            """
            id, employee_id, paystub_storage_key,
            employees!inner (id, first_name, last_name, email)
            """
        ).eq("payroll_run_id", str(run_id)).eq(
            "user_id", self.user_id
        ).eq("company_id", self.company_id).execute()

        records = records_result.data or []
        if not records:
            raise ValueError("No records found for payroll run")

        sent_count = 0
        sent_record_ids: list[str] = []
        send_errors: list[str] = []

        for record in records:
            try:
                storage_key = record.get("paystub_storage_key")
                if not storage_key:
                    send_errors.append(f"Record {record['id']}: paystub not generated")
                    continue

                employee = record.get("employees", {})
                email = employee.get("email")
                if not email:
                    send_errors.append(f"Record {record['id']}: employee has no email")
                    continue

                # TODO: Integrate actual email service
                logger.info(
                    f"Would send paystub to {email} for employee "
                    f"{employee.get('first_name')} {employee.get('last_name')}"
                )

                self.supabase.table("payroll_records").update({
                    "paystub_sent_at": datetime.now().isoformat(),
                }).eq("id", record["id"]).execute()

                sent_count += 1
                sent_record_ids.append(record["id"])

            except Exception as e:
                logger.error("Failed to send paystub for record %s: %s", record['id'], e)
                send_errors.append(f"Record {record['id']}: {str(e)}")

        return {
            "sent": sent_count,
            "sent_record_ids": sent_record_ids,
            "errors": send_errors if send_errors else None,
        }

    async def create_or_get_run(self, pay_date: str) -> dict[str, Any]:
        """Create a new draft payroll run or get existing one for a pay date.

        DEPRECATED: Use create_or_get_run_by_period_end() instead.
        This method converts pay_date to period_end (pay_date - 6 days for SK)
        and delegates to the new method.

        Returns:
            Dict with 'run', 'created' bool, 'records_count', and sync metadata
        """
        pay_date_obj = datetime.strptime(pay_date, "%Y-%m-%d").date()
        period_end = pay_date_obj - timedelta(days=6)
        return await self.create_or_get_run_by_period_end(period_end.strftime("%Y-%m-%d"))

    async def create_or_get_run_by_period_end(
        self, period_end: str, pay_date: str | None = None
    ) -> dict[str, Any]:
        """Create a new draft payroll run or get existing one for a period end.

        This is the new entry point that uses period_end as the primary identifier.
        Pay date is auto-calculated based on province regulations, or can be provided.

        Args:
            period_end: The pay period end date (YYYY-MM-DD)
            pay_date: Optional pay date (YYYY-MM-DD). If not provided, calculated from
                     period_end + province delay. If provided, must be compliant with
                     province regulations (on or after period_end, on or before legal deadline).

        Returns:
            Dict with 'run', 'created' bool, 'records_count', and sync metadata

        Raises:
            ValueError: If pay_date is provided but not compliant with province regulations
        """
        # Check if run already exists for this period_end
        existing_result = self.supabase.table("payroll_runs").select("*").eq(
            "user_id", self.user_id
        ).eq("company_id", self.company_id).eq("period_end", period_end).execute()

        if existing_result.data and len(existing_result.data) > 0:
            existing_run = existing_result.data[0]
            if existing_run.get("status") == "draft" and self._sync_employees:
                sync_result = await self._sync_employees(UUID(existing_run["id"]))
                added_count = sync_result.get("added_count", 0)
                removed_count = sync_result.get("removed_count", 0)
                return {
                    "run": sync_result.get("run", existing_run),
                    "created": False,
                    "records_count": 0,
                    "synced": added_count > 0 or removed_count > 0,
                    "added_count": added_count,
                }

            return {
                "run": existing_run,
                "created": False,
                "records_count": 0,
                "synced": False,
                "added_count": 0,
            }

        # Get pay groups with matching next_period_end for this company
        pay_groups_result = self.supabase.table("pay_groups").select(
            "id, name, pay_frequency, employment_type, group_benefits, province"
        ).eq("company_id", self.company_id).eq("next_period_end", period_end).eq("is_active", True).execute()

        pay_groups = pay_groups_result.data or []
        if not pay_groups:
            raise ValueError(f"No pay groups found with period end {period_end}")

        pay_group_ids = [pg["id"] for pg in pay_groups]
        pay_group_map = {pg["id"]: pg for pg in pay_groups}

        # Collect all provinces from pay groups for compliance validation
        pay_group_provinces: set[str] = {
            pg.get("province") for pg in pay_groups if pg.get("province")
        }
        if not pay_group_provinces:
            pay_group_provinces = {"SK"}  # Default fallback

        # Get all active employees
        employees_result = self.supabase.table("employees").select(
            "id, first_name, last_name, province_of_employment, pay_group_id, "
            "annual_salary, hourly_rate, federal_additional_claims, provincial_additional_claims, "
            "is_cpp_exempt, is_ei_exempt, cpp2_exempt, vacation_config"
        ).eq("user_id", self.user_id).eq("company_id", self.company_id).in_(
            "pay_group_id", pay_group_ids
        ).is_("termination_date", "null").execute()

        employees = employees_result.data or []
        if not employees:
            raise ValueError("No active employees found for these pay groups")

        # Parse period_end and calculate dates
        period_end_obj = datetime.strptime(period_end, "%Y-%m-%d").date()
        pay_frequency = pay_groups[0].get("pay_frequency", "bi_weekly")

        # Calculate period_start based on frequency
        if pay_frequency == "monthly":
            period_start = period_end_obj.replace(day=1)
        elif pay_frequency == "semi_monthly":
            if period_end_obj.day <= 15:
                period_start = period_end_obj.replace(day=1)
            else:
                period_start = period_end_obj.replace(day=16)
        elif pay_frequency == "weekly":
            period_start = period_end_obj - timedelta(days=6)
        else:  # bi_weekly
            period_start = period_end_obj - timedelta(days=13)

        # Determine pay_date - use the most restrictive province for compliance
        most_restrictive_province = min(
            pay_group_provinces,
            key=lambda p: calculate_pay_date(period_end_obj, p)
        )

        if pay_date:
            # Validate custom pay_date is compliant with the most restrictive province
            pay_date_obj = datetime.strptime(pay_date, "%Y-%m-%d").date()
            if not is_pay_date_compliant(pay_date_obj, period_end_obj, most_restrictive_province):
                province_name = get_province_name(most_restrictive_province)
                legal_deadline = calculate_pay_date(period_end_obj, most_restrictive_province)
                raise ValueError(
                    f"Pay date {pay_date} is not compliant with {province_name} labour standards. "
                    f"Pay date must be between {period_end} and {legal_deadline.strftime('%Y-%m-%d')} (inclusive)."
                )
        else:
            # Calculate pay_date from period_end using most restrictive province
            pay_date_obj = calculate_pay_date(period_end_obj, most_restrictive_province)

        # Create the payroll run
        run_insert_result = self.supabase.table("payroll_runs").insert({
            "user_id": self.user_id,
            "company_id": self.company_id,
            "period_start": period_start.strftime("%Y-%m-%d"),
            "period_end": period_end,
            "pay_date": pay_date_obj.strftime("%Y-%m-%d"),
            "status": "draft",
            "pay_group_ids": pay_group_ids,
            "total_employees": len(employees),
            "total_gross": 0,
            "total_cpp_employee": 0,
            "total_cpp_employer": 0,
            "total_ei_employee": 0,
            "total_ei_employer": 0,
            "total_federal_tax": 0,
            "total_provincial_tax": 0,
            "total_net_pay": 0,
            "total_employer_cost": 0,
        }).execute()

        if not run_insert_result.data or len(run_insert_result.data) == 0:
            raise ValueError("Failed to create payroll run")

        run = run_insert_result.data[0]
        run_id = run["id"]

        tax_year = extract_year_from_date(period_end)

        _, results = await self._create_records_for_employees(
            UUID(run_id), employees, pay_group_map, tax_year, pay_date_obj
        )

        if results:
            total_gross = sum(float(r.total_gross) for r in results)
            total_cpp_employee = sum(float(r.cpp_total) for r in results)
            total_cpp_employer = sum(float(r.cpp_employer) for r in results)
            total_ei_employee = sum(float(r.ei_employee) for r in results)
            total_ei_employer = sum(float(r.ei_employer) for r in results)
            total_federal_tax = sum(float(r.federal_tax) for r in results)
            total_provincial_tax = sum(float(r.provincial_tax) for r in results)
            total_net_pay = sum(float(r.net_pay) for r in results)
            total_employer_cost = total_cpp_employer + total_ei_employer

            self.supabase.table("payroll_runs").update({
                "total_gross": total_gross,
                "total_cpp_employee": total_cpp_employee,
                "total_cpp_employer": total_cpp_employer,
                "total_ei_employee": total_ei_employee,
                "total_ei_employer": total_ei_employer,
                "total_federal_tax": total_federal_tax,
                "total_provincial_tax": total_provincial_tax,
                "total_net_pay": total_net_pay,
                "total_employer_cost": total_employer_cost,
            }).eq("id", run_id).execute()

            run = await self._get_run(UUID(run_id)) or run

        return {
            "run": run,
            "created": True,
            "records_count": len(employees),
            "synced": False,
            "added_count": 0,
        }

    async def update_pay_date(self, run_id: UUID, pay_date: str) -> dict[str, Any]:
        """Update the pay date of an existing payroll run.

        Args:
            run_id: The payroll run ID
            pay_date: New pay date (YYYY-MM-DD)

        Returns:
            Updated payroll run data with needs_recalculation flag

        Raises:
            ValueError: If run not found, not in draft status, or pay_date is not compliant
        """
        # Get the run with payroll records to determine province
        run = await self._get_run(run_id)
        if not run:
            raise ValueError("Payroll run not found")

        # Only allow updating pay_date for draft runs
        if run["status"] != "draft":
            raise ValueError(
                f"Cannot update pay date: payroll run is in '{run['status']}' status. "
                "Only draft runs can have their pay date modified."
            )

        # Get payroll records to determine provinces from employees
        records_result = self.supabase.table("payroll_records").select(
            "id, employee_id, employees!inner(province_of_employment)"
        ).eq("payroll_run_id", str(run_id)).execute()

        # Collect all unique provinces from employee records
        provinces: set[str] = set()
        if records_result.data:
            for record in records_result.data:
                prov = record.get("employees", {}).get("province_of_employment")
                if prov:
                    provinces.add(prov)

        # Default to SK if no provinces found
        if not provinces:
            provinces = {"SK"}

        # Parse dates
        pay_date_obj = datetime.strptime(pay_date, "%Y-%m-%d").date()
        period_end_str = run.get("period_end", "")
        period_end_obj = datetime.strptime(period_end_str, "%Y-%m-%d").date()

        # Validate compliance against ALL provinces (use the most restrictive deadline)
        # Find the province with the shortest deadline
        most_restrictive_province = min(
            provinces,
            key=lambda p: calculate_pay_date(period_end_obj, p)
        )

        if not is_pay_date_compliant(pay_date_obj, period_end_obj, most_restrictive_province, allow_early_days=10):
            province_name = get_province_name(most_restrictive_province)
            legal_deadline = calculate_pay_date(period_end_obj, most_restrictive_province)
            earliest_date = period_end_obj - timedelta(days=10)
            raise ValueError(
                f"Pay date {pay_date} is not compliant with {province_name} labour standards. "
                f"Pay date must be between {earliest_date.strftime('%Y-%m-%d')} and {legal_deadline.strftime('%Y-%m-%d')} (inclusive)."
            )

        # Update the pay_date
        update_result = self.supabase.table("payroll_runs").update({
            "pay_date": pay_date,
        }).eq("id", str(run_id)).eq("user_id", self.user_id).eq("company_id", self.company_id).execute()

        if not update_result.data or len(update_result.data) == 0:
            raise ValueError("Failed to update pay date")

        # Mark all records as is_modified=True so finalize will require recalculation
        # This persists the needs_recalculation state in the database
        if records_result.data:
            record_ids = [r["id"] for r in records_result.data]
            self.supabase.table("payroll_records").update({
                "is_modified": True,
            }).in_("id", record_ids).execute()
            logger.info(
                "Marked %d records as modified after pay_date change for run %s",
                len(record_ids), run_id
            )

        # Return updated run with needs_recalculation flag for immediate UI feedback
        updated_run = cast(dict[str, Any], update_result.data[0])
        updated_run["needs_recalculation"] = True
        return updated_run
