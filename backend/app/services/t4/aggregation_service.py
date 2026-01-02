"""
T4 Aggregation Service

Aggregates payroll data for T4 slip generation.
Queries completed payroll records and computes annual totals for each employee.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.core.security import decrypt_sin
from app.models.payroll import Company, Employee
from app.models.t4 import T4SlipData, T4Status, T4Summary
from app.utils.sin_validator import validate_sin_luhn

logger = logging.getLogger(__name__)

# Statuses that count as "completed" for T4 aggregation
COMPLETED_RUN_STATUSES = ["approved", "paid"]


class T4AggregationService:
    """
    Aggregates annual payroll data for T4 generation.

    Uses payroll_records from completed (approved/paid) payroll runs
    to calculate annual totals for each employee.
    """

    def __init__(self, supabase: Any, user_id: str, company_id: str):
        """
        Initialize T4 aggregation service.

        Args:
            supabase: Supabase client instance
            user_id: Current user ID
            company_id: Current company ID
        """
        self.supabase = supabase
        self.user_id = user_id
        self.company_id = company_id

    async def get_company(self) -> Company | None:
        """Get company data for T4 employer info."""
        result = self.supabase.table("companies").select("*").eq(
            "id", self.company_id
        ).eq("user_id", self.user_id).maybe_single().execute()

        if result.data:
            return Company.model_validate(result.data)
        return None

    async def get_employees_with_payroll(self, tax_year: int) -> list[Employee]:
        """
        Get all employees who have payroll records in the given tax year.

        Args:
            tax_year: The tax year to query

        Returns:
            List of Employee models
        """
        year_start = f"{tax_year}-01-01"
        year_end = f"{tax_year}-12-31"

        # Query payroll_records with inner joins to payroll_runs and employees
        # Filter by completed run status and pay_date in the tax year
        # CRA T4 uses cash basis: report income when PAID, not when earned
        result = self.supabase.table("payroll_records").select(
            """
            employee_id,
            employees!inner (*),
            payroll_runs!inner (
                id,
                pay_date,
                status
            )
            """
        ).eq("user_id", self.user_id).eq("company_id", self.company_id).in_(
            "payroll_runs.status", COMPLETED_RUN_STATUSES
        ).gte(
            "payroll_runs.pay_date", year_start
        ).lte(
            "payroll_runs.pay_date", year_end
        ).execute()

        # Extract unique employees from the results
        seen_ids: set[str] = set()
        employees = []
        for row in result.data or []:
            employee_data = row.get("employees")
            if not employee_data:
                continue
            employee_id = employee_data.get("id")
            if employee_id in seen_ids:
                continue
            seen_ids.add(employee_id)
            try:
                employees.append(Employee.model_validate(employee_data))
            except Exception as e:
                logger.warning(f"Failed to validate employee {employee_id}: {e}")

        return employees

    async def aggregate_employee_year(
        self,
        employee: Employee,
        company: Company,
        tax_year: int,
    ) -> T4SlipData | None:
        """
        Aggregate all payroll data for one employee for the tax year.

        Args:
            employee: Employee model
            company: Company model (employer info)
            tax_year: Tax year to aggregate

        Returns:
            T4SlipData with all boxes populated, or None if no data
        """
        year_start = f"{tax_year}-01-01"
        year_end = f"{tax_year}-12-31"

        # Query all payroll records for this employee in the year
        # CRA T4 uses cash basis: filter by pay_date (when paid)
        result = self.supabase.table("payroll_records").select(
            """
            *,
            payroll_runs!inner (
                id,
                pay_date,
                status
            )
            """
        ).eq("employee_id", str(employee.id)).eq(
            "user_id", self.user_id
        ).eq("company_id", self.company_id).in_(
            "payroll_runs.status", COMPLETED_RUN_STATUSES
        ).gte(
            "payroll_runs.pay_date", year_start
        ).lte(
            "payroll_runs.pay_date", year_end
        ).execute()

        records = result.data or []

        if not records:
            logger.info(f"No payroll records for employee {employee.id} in {tax_year}")
            return None

        # Aggregate totals
        totals = self._aggregate_records(records)

        # Decrypt and validate SIN
        sin = decrypt_sin(employee.sin_encrypted)
        if not sin:
            logger.error(f"Failed to decrypt SIN for employee {employee.id}")
            return None

        if not validate_sin_luhn(sin):
            logger.warning(f"Invalid SIN for employee {employee.id} (Luhn check failed)")
            # Continue anyway - SIN might be a test number

        # Build T4SlipData
        return T4SlipData(
            employee_id=employee.id,
            tax_year=tax_year,
            sin=sin,
            # Employee info
            employee_first_name=employee.first_name,
            employee_last_name=employee.last_name,
            employee_address_line1=employee.address_street,
            employee_city=employee.address_city,
            employee_province=employee.province_of_employment,
            employee_postal_code=employee.address_postal_code,
            # Employer info
            employer_name=company.company_name,
            employer_account_number=company.payroll_account_number,
            employer_address_line1=company.address_street,
            employer_city=company.address_city,
            employer_province=company.province,
            employer_postal_code=company.address_postal_code,
            # T4 Boxes
            box_14_employment_income=totals["employment_income"],
            box_16_cpp_contributions=totals["cpp_employee"],
            box_17_cpp2_contributions=totals["cpp_additional"],
            box_18_ei_premiums=totals["ei_employee"],
            box_22_income_tax_deducted=totals["income_tax"],
            box_24_ei_insurable_earnings=totals["ei_insurable_earnings"],
            box_26_cpp_pensionable_earnings=totals["cpp_pensionable_earnings"],
            box_44_union_dues=totals["union_dues"] if totals["union_dues"] > 0 else None,
            # Province of employment
            province_of_employment=employee.province_of_employment,
            # Exemptions
            cpp_exempt=employee.is_cpp_exempt,
            ei_exempt=employee.is_ei_exempt,
        )

    def _aggregate_records(self, records: list[dict[str, Any]]) -> dict[str, Decimal]:
        """
        Aggregate payroll record fields into T4 totals.

        Args:
            records: List of payroll record dicts from database

        Returns:
            Dict with aggregated totals for T4 boxes
        """
        totals = {
            "employment_income": Decimal("0"),
            "cpp_employee": Decimal("0"),
            "cpp_additional": Decimal("0"),
            "ei_employee": Decimal("0"),
            "income_tax": Decimal("0"),
            "ei_insurable_earnings": Decimal("0"),
            "cpp_pensionable_earnings": Decimal("0"),
            "union_dues": Decimal("0"),
            "cpp_employer": Decimal("0"),
            "ei_employer": Decimal("0"),
        }

        for record in records:
            # Box 14: Employment income (all gross earnings)
            gross = (
                Decimal(str(record.get("gross_regular", 0)))
                + Decimal(str(record.get("gross_overtime", 0)))
                + Decimal(str(record.get("holiday_pay", 0)))
                + Decimal(str(record.get("holiday_premium_pay", 0)))
                + Decimal(str(record.get("vacation_pay_paid", 0)))
                + Decimal(str(record.get("other_earnings", 0)))
            )
            totals["employment_income"] += gross

            # Box 16: CPP contributions (base)
            totals["cpp_employee"] += Decimal(str(record.get("cpp_employee", 0)))

            # Box 17: CPP2 contributions (additional)
            totals["cpp_additional"] += Decimal(str(record.get("cpp_additional", 0)))

            # Box 18: EI premiums
            totals["ei_employee"] += Decimal(str(record.get("ei_employee", 0)))

            # Box 22: Income tax deducted (federal + provincial)
            totals["income_tax"] += (
                Decimal(str(record.get("federal_tax", 0)))
                + Decimal(str(record.get("provincial_tax", 0)))
            )

            # Box 44: Union dues
            totals["union_dues"] += Decimal(str(record.get("union_dues", 0)))

            # Employer contributions (for summary)
            totals["cpp_employer"] += Decimal(str(record.get("cpp_employer", 0)))
            totals["ei_employer"] += Decimal(str(record.get("ei_employer", 0)))

        # Box 24 & 26: Use employment income as insurable/pensionable earnings
        # (In a full implementation, these would be capped at YMPE/MIE)
        totals["ei_insurable_earnings"] = totals["employment_income"]
        totals["cpp_pensionable_earnings"] = totals["employment_income"]

        return totals

    async def generate_all_t4_slips(
        self,
        tax_year: int,
        employee_ids: list[UUID] | None = None,
    ) -> list[T4SlipData]:
        """
        Generate T4 slips for all employees (or specified employees).

        Args:
            tax_year: Tax year to generate T4s for
            employee_ids: Optional list of specific employee IDs

        Returns:
            List of T4SlipData objects
        """
        company = await self.get_company()
        if not company:
            logger.error(f"Company not found: {self.company_id}")
            return []

        employees = await self.get_employees_with_payroll(tax_year)

        # Filter to specific employees if requested
        if employee_ids:
            employee_id_set = set(employee_ids)
            employees = [e for e in employees if e.id in employee_id_set]

        slips = []
        for employee in employees:
            try:
                slip = await self.aggregate_employee_year(employee, company, tax_year)
                if slip:
                    slips.append(slip)
            except Exception as e:
                logger.error(f"Failed to generate T4 for employee {employee.id}: {e}")

        logger.info(f"Generated {len(slips)} T4 slips for tax year {tax_year}")
        return slips

    async def generate_t4_summary(
        self,
        tax_year: int,
        slips: list[T4SlipData] | None = None,
    ) -> T4Summary | None:
        """
        Generate T4 Summary from T4 slips.

        Args:
            tax_year: Tax year
            slips: Pre-generated slips, or None to generate

        Returns:
            T4Summary object
        """
        company = await self.get_company()
        if not company:
            logger.error(f"Company not found: {self.company_id}")
            return None

        if slips is None:
            slips = await self.generate_all_t4_slips(tax_year)

        if not slips:
            logger.warning(f"No T4 slips to summarize for {tax_year}")
            return None

        # Calculate employer totals from payroll records
        employer_totals = await self._get_employer_totals(tax_year)

        summary = T4Summary(
            company_id=UUID(self.company_id),
            user_id=self.user_id,
            tax_year=tax_year,
            employer_name=company.company_name,
            employer_account_number=company.payroll_account_number,
            employer_address_line1=company.address_street,
            employer_city=company.address_city,
            employer_province=company.province,
            employer_postal_code=company.address_postal_code,
            total_number_of_t4_slips=len(slips),
            total_employment_income=sum((s.box_14_employment_income for s in slips), Decimal("0")),
            total_cpp_contributions=sum((s.box_16_cpp_contributions for s in slips), Decimal("0")),
            total_cpp2_contributions=sum((s.box_17_cpp2_contributions for s in slips), Decimal("0")),
            total_ei_premiums=sum((s.box_18_ei_premiums for s in slips), Decimal("0")),
            total_income_tax_deducted=sum((s.box_22_income_tax_deducted for s in slips), Decimal("0")),
            total_union_dues=sum((s.box_44_union_dues or Decimal("0") for s in slips), Decimal("0")),
            total_cpp_employer=employer_totals["cpp_employer"],
            total_ei_employer=employer_totals["ei_employer"],
            status=T4Status.DRAFT,
        )

        return summary

    async def _get_employer_totals(self, tax_year: int) -> dict[str, Decimal]:
        """Get employer contribution totals for the year."""
        year_start = f"{tax_year}-01-01"
        year_end = f"{tax_year}-12-31"

        # CRA T4 uses cash basis: filter by pay_date (when paid)
        result = self.supabase.table("payroll_records").select(
            """
            cpp_employer,
            ei_employer,
            payroll_runs!inner (
                pay_date,
                status
            )
            """
        ).eq("user_id", self.user_id).eq("company_id", self.company_id).in_(
            "payroll_runs.status", COMPLETED_RUN_STATUSES
        ).gte(
            "payroll_runs.pay_date", year_start
        ).lte(
            "payroll_runs.pay_date", year_end
        ).execute()

        cpp_employer = Decimal("0")
        ei_employer = Decimal("0")

        for record in result.data or []:
            cpp_employer += Decimal(str(record.get("cpp_employer", 0)))
            ei_employer += Decimal(str(record.get("ei_employer", 0)))

        return {
            "cpp_employer": cpp_employer,
            "ei_employer": ei_employer,
        }
