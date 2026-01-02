"""
Model Builders for Payroll Run

Converts database rows to Pydantic domain models.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.models.payroll import (
    BenefitConfig,
    Company,
    Employee,
    GroupBenefits,
    LifeInsuranceConfig,
    OvertimePolicy,
    PayFrequency,
    PayGroup,
    PayrollRecord,
    PayrollRun,
    PeriodStartDay,
    Province,
    RemitterType,
    VacationConfig,
    VacationPayoutMethod,
    WcbConfig,
)


class ModelBuilder:
    """Builds domain models from database rows."""

    @staticmethod
    def build_payroll_run(data: dict[str, Any]) -> PayrollRun:
        """Build PayrollRun model from database row."""
        return PayrollRun(
            id=UUID(data["id"]),
            user_id=data["user_id"],
            company_id=str(data.get("company_id", "")),
            period_start=date.fromisoformat(data["period_start"]),
            period_end=date.fromisoformat(data["period_end"]),
            pay_date=date.fromisoformat(data["pay_date"]),
            status=data.get("status", "draft"),
            total_employees=data.get("total_employees", 0),
            total_gross=Decimal(str(data.get("total_gross", 0))),
            total_cpp_employee=Decimal(str(data.get("total_cpp_employee", 0))),
            total_cpp_employer=Decimal(str(data.get("total_cpp_employer", 0))),
            total_ei_employee=Decimal(str(data.get("total_ei_employee", 0))),
            total_ei_employer=Decimal(str(data.get("total_ei_employer", 0))),
            total_federal_tax=Decimal(str(data.get("total_federal_tax", 0))),
            total_provincial_tax=Decimal(str(data.get("total_provincial_tax", 0))),
            total_net_pay=Decimal(str(data.get("total_net_pay", 0))),
            total_employer_cost=Decimal(str(data.get("total_employer_cost", 0))),
            notes=data.get("notes"),
            approved_by=data.get("approved_by"),
            approved_at=datetime.fromisoformat(data["approved_at"]) if data.get("approved_at") else None,
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )

    @staticmethod
    def build_employee(data: dict[str, Any]) -> Employee:
        """Build Employee model from database row."""
        vacation_config_data = data.get("vacation_config") or {}

        return Employee(
            id=UUID(data["id"]),
            user_id=data.get("user_id", ""),
            company_id=str(data.get("company_id", "")),
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data.get("email"),
            province_of_employment=Province(data["province_of_employment"]),
            pay_frequency=PayFrequency(data.get("pay_frequency", "bi_weekly")),
            employment_type=data.get("employment_type", "full_time"),
            address_street=data.get("address_street"),
            address_city=data.get("address_city"),
            address_postal_code=data.get("address_postal_code"),
            occupation=data.get("occupation"),
            annual_salary=Decimal(str(data["annual_salary"])) if data.get("annual_salary") else None,
            hourly_rate=Decimal(str(data["hourly_rate"])) if data.get("hourly_rate") else None,
            federal_additional_claims=Decimal(str(data.get("federal_additional_claims", 0))),
            provincial_additional_claims=Decimal(str(data.get("provincial_additional_claims", 0))),
            is_cpp_exempt=data.get("is_cpp_exempt", False),
            is_ei_exempt=data.get("is_ei_exempt", False),
            cpp2_exempt=data.get("cpp2_exempt", False),
            hire_date=date.fromisoformat(data["hire_date"]),
            termination_date=date.fromisoformat(data["termination_date"]) if data.get("termination_date") else None,
            vacation_config=VacationConfig(
                payout_method=VacationPayoutMethod(vacation_config_data.get("payout_method", "accrual")),
                # Use vacation_rate from DB; default 0.04 only if missing (not if "0")
                vacation_rate=Decimal(str(vacation_config_data["vacation_rate"])) if vacation_config_data.get("vacation_rate") is not None else Decimal("0.04"),
                lump_sum_month=vacation_config_data.get("lump_sum_month"),
            ),
            sin_encrypted=data.get("sin_encrypted", ""),
            vacation_balance=Decimal(str(data.get("vacation_balance", 0))),
            sick_balance=Decimal(str(data.get("sick_balance", 0))),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now(),
        )

    @staticmethod
    def build_company(data: dict[str, Any]) -> Company:
        """Build Company model from database row."""
        return Company(
            id=UUID(data["id"]),
            user_id=data.get("user_id", ""),
            company_name=data["company_name"],
            business_number=data.get("business_number", "000000000"),
            payroll_account_number=data.get("payroll_account_number", "000000000RP0001"),
            province=Province(data["province"]),
            address_street=data.get("address_street"),
            address_city=data.get("address_city"),
            address_postal_code=data.get("address_postal_code"),
            remitter_type=RemitterType(data.get("remitter_type", "regular")),
            auto_calculate_deductions=data.get("auto_calculate_deductions", True),
            send_paystub_emails=data.get("send_paystub_emails", False),
            bookkeeping_ledger_id=data.get("bookkeeping_ledger_id"),
            bookkeeping_ledger_name=data.get("bookkeeping_ledger_name"),
            bookkeeping_connected_at=datetime.fromisoformat(data["bookkeeping_connected_at"]) if data.get("bookkeeping_connected_at") else None,
            logo_url=data.get("logo_url"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now(),
        )

    @staticmethod
    def _get_benefit_field(
        data: dict[str, Any], camel: str, snake: str, default: Any = 0
    ) -> Any:
        """Get field value supporting both camelCase and snake_case keys.

        Frontend stores camelCase, but backend models use snake_case.
        This helper supports both formats for backwards compatibility.
        """
        return data.get(camel, data.get(snake, default))

    @staticmethod
    def _build_benefit_config(data: dict[str, Any]) -> BenefitConfig:
        """Build BenefitConfig supporting both camelCase and snake_case fields."""
        return BenefitConfig(
            enabled=data.get("enabled", False),
            employee_deduction=Decimal(
                str(ModelBuilder._get_benefit_field(data, "employeeDeduction", "employee_deduction", 0))
            ),
            employer_contribution=Decimal(
                str(ModelBuilder._get_benefit_field(data, "employerContribution", "employer_contribution", 0))
            ),
            is_taxable=ModelBuilder._get_benefit_field(data, "isTaxable", "is_taxable", False),
        )

    @staticmethod
    def build_pay_group(data: dict[str, Any]) -> PayGroup:
        """Build PayGroup model from database row."""
        # Parse group_benefits JSONB
        # Supports both camelCase (frontend) and snake_case field names
        gb_data = data.get("group_benefits") or {}

        # Get benefit data - support both camelCase and snake_case keys
        health_data = gb_data.get("health", {})
        dental_data = gb_data.get("dental", {})
        vision_data = gb_data.get("vision", {})
        # life_insurance: frontend uses "lifeInsurance", backend uses "life_insurance"
        life_data = gb_data.get("lifeInsurance", gb_data.get("life_insurance", {}))
        disability_data = gb_data.get("disability", {})

        group_benefits = GroupBenefits(
            enabled=gb_data.get("enabled", False),
            health=ModelBuilder._build_benefit_config(health_data),
            dental=ModelBuilder._build_benefit_config(dental_data),
            vision=ModelBuilder._build_benefit_config(vision_data),
            life_insurance=LifeInsuranceConfig(
                enabled=life_data.get("enabled", False),
                employee_deduction=Decimal(
                    str(ModelBuilder._get_benefit_field(life_data, "employeeDeduction", "employee_deduction", 0))
                ),
                employer_contribution=Decimal(
                    str(ModelBuilder._get_benefit_field(life_data, "employerContribution", "employer_contribution", 0))
                ),
                is_taxable=ModelBuilder._get_benefit_field(life_data, "isTaxable", "is_taxable", False),
                coverage_amount=Decimal(
                    str(ModelBuilder._get_benefit_field(life_data, "coverageAmount", "coverage_amount", 0))
                ),
            ),
            disability=ModelBuilder._build_benefit_config(disability_data),
        )

        # Parse other JSONB fields
        op_data = data.get("overtime_policy") or {}
        overtime_policy = OvertimePolicy(
            bank_time_enabled=op_data.get("bank_time_enabled", False),
            bank_time_rate=op_data.get("bank_time_rate", 1.5),
            bank_time_expiry_months=op_data.get("bank_time_expiry_months", 3),
            require_written_agreement=op_data.get("require_written_agreement", True),
        )

        wcb_data = data.get("wcb_config") or {}
        wcb_config = WcbConfig(
            enabled=wcb_data.get("enabled", False),
            industry_class_code=wcb_data.get("industry_class_code"),
            industry_name=wcb_data.get("industry_name"),
            assessment_rate=Decimal(str(wcb_data.get("assessment_rate", 0))),
            max_assessable_earnings=Decimal(str(wcb_data["max_assessable_earnings"])) if wcb_data.get("max_assessable_earnings") else None,
        )

        return PayGroup(
            id=UUID(data["id"]),
            company_id=UUID(data["company_id"]) if data.get("company_id") else UUID("00000000-0000-0000-0000-000000000000"),
            name=data["name"],
            description=data.get("description"),
            pay_frequency=PayFrequency(data.get("pay_frequency", "bi_weekly")),
            employment_type=data.get("employment_type", "full_time"),
            next_pay_date=date.fromisoformat(data["next_pay_date"]) if data.get("next_pay_date") else date.today(),
            period_start_day=PeriodStartDay(data.get("period_start_day", "monday")),
            leave_enabled=data.get("leave_enabled", True),
            overtime_policy=overtime_policy,
            wcb_config=wcb_config,
            group_benefits=group_benefits,
            custom_deductions=[],  # Not needed for paystub generation
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now(),
        )

    @staticmethod
    def build_payroll_record(data: dict[str, Any]) -> PayrollRecord:
        """Build PayrollRecord model from database row."""
        return PayrollRecord(
            id=UUID(data["id"]),
            payroll_run_id=UUID(data["payroll_run_id"]),
            employee_id=UUID(data["employee_id"]),
            user_id=data.get("user_id", ""),
            company_id=str(data.get("company_id", "")),
            gross_regular=Decimal(str(data.get("gross_regular", 0))),
            gross_overtime=Decimal(str(data.get("gross_overtime", 0))),
            holiday_pay=Decimal(str(data.get("holiday_pay", 0))),
            holiday_premium_pay=Decimal(str(data.get("holiday_premium_pay", 0))),
            vacation_pay_paid=Decimal(str(data.get("vacation_pay_paid", 0))),
            other_earnings=Decimal(str(data.get("other_earnings", 0))),
            cpp_employee=Decimal(str(data.get("cpp_employee", 0))),
            cpp_additional=Decimal(str(data.get("cpp_additional", 0))),
            ei_employee=Decimal(str(data.get("ei_employee", 0))),
            federal_tax=Decimal(str(data.get("federal_tax", 0))),
            provincial_tax=Decimal(str(data.get("provincial_tax", 0))),
            rrsp=Decimal(str(data.get("rrsp", 0))),
            union_dues=Decimal(str(data.get("union_dues", 0))),
            garnishments=Decimal(str(data.get("garnishments", 0))),
            other_deductions=Decimal(str(data.get("other_deductions", 0))),
            cpp_employer=Decimal(str(data.get("cpp_employer", 0))),
            ei_employer=Decimal(str(data.get("ei_employer", 0))),
            total_gross=Decimal(str(data.get("total_gross", 0))),
            total_deductions=Decimal(str(data.get("total_deductions", 0))),
            net_pay=Decimal(str(data.get("net_pay", 0))),
            total_employer_cost=Decimal(str(data.get("total_employer_cost", 0))),
            ytd_gross=Decimal(str(data.get("ytd_gross", 0))),
            ytd_cpp=Decimal(str(data.get("ytd_cpp", 0))),
            ytd_ei=Decimal(str(data.get("ytd_ei", 0))),
            ytd_federal_tax=Decimal(str(data.get("ytd_federal_tax", 0))),
            ytd_provincial_tax=Decimal(str(data.get("ytd_provincial_tax", 0))),
            vacation_accrued=Decimal(str(data.get("vacation_accrued", 0))),
            vacation_hours_taken=Decimal(str(data.get("vacation_hours_taken", 0))),
            calculation_details=data.get("calculation_details"),
            paystub_storage_key=data.get("paystub_storage_key"),
            paystub_generated_at=datetime.fromisoformat(data["paystub_generated_at"]) if data.get("paystub_generated_at") else None,
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
        )
