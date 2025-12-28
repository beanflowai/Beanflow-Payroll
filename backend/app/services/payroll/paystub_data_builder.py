"""
PaystubDataBuilder - Builds PaystubData from database records.

Transforms payroll records, employee data, and company data into the
PaystubData structure required for PDF generation.
"""

from __future__ import annotations

from decimal import Decimal

from app.models.payroll import (
    Company,
    Employee,
    GroupBenefits,
    PayGroup,
    PayrollRecord,
    PayrollRun,
)
from app.models.paystub import (
    BenefitLine,
    EarningLine,
    PaystubData,
    TaxLine,
    VacationInfo,
)

# Province name mapping for display
PROVINCE_NAMES: dict[str, str] = {
    "AB": "Alberta",
    "BC": "British Columbia",
    "MB": "Manitoba",
    "NB": "New Brunswick",
    "NL": "Newfoundland and Labrador",
    "NS": "Nova Scotia",
    "NT": "Northwest Territories",
    "NU": "Nunavut",
    "ON": "Ontario",
    "PE": "Prince Edward Island",
    "SK": "Saskatchewan",
    "YT": "Yukon",
}


class PaystubDataBuilder:
    """
    Builds PaystubData from database records for PDF generation.

    This service transforms various database models into the unified
    PaystubData structure that the PaystubGenerator expects.
    """

    def build(
        self,
        record: PayrollRecord,
        employee: Employee,
        payroll_run: PayrollRun,
        pay_group: PayGroup | None,
        company: Company,
        ytd_records: list[PayrollRecord] | None = None,
        masked_sin: str | None = None,
        logo_bytes: bytes | None = None,
    ) -> PaystubData:
        """
        Build PaystubData from database records.

        Args:
            record: Current period's payroll record
            employee: Employee data
            payroll_run: Payroll run metadata
            pay_group: Pay group (for benefits config), can be None
            company: Company data
            ytd_records: Historical records from same year for YTD calculations
            masked_sin: Pre-masked SIN (e.g., "***-***-XXX"), if not provided will mask

        Returns:
            PaystubData ready for PDF generation
        """
        ytd_records = ytd_records or []

        # Build employee address
        employee_address = self._build_address(
            street=employee.address_street,
            city=employee.address_city,
            province=employee.province_of_employment.value,
            postal_code=employee.address_postal_code,
        )

        # Build employer address
        employer_address = self._build_address(
            street=company.address_street,
            city=company.address_city,
            province=company.province.value,
            postal_code=company.address_postal_code,
        )

        # Build earnings lines
        earnings = self._build_earnings(record, ytd_records)
        total_earnings = sum((e.current for e in earnings), Decimal("0"))
        ytd_earnings = record.ytd_gross

        # Build tax lines
        taxes = self._build_taxes(record)
        total_taxes = sum((t.current for t in taxes), Decimal("0"))
        ytd_taxes = sum((t.ytd for t in taxes), Decimal("0"))

        # Build benefits (if pay group has benefits configured)
        non_taxable_benefits: list[BenefitLine] = []
        taxable_benefits: list[BenefitLine] = []
        benefit_deductions: list[BenefitLine] = []

        if pay_group and pay_group.group_benefits.enabled:
            (
                non_taxable_benefits,
                taxable_benefits,
                benefit_deductions,
            ) = self._build_benefits(pay_group.group_benefits, ytd_records)

        total_benefit_deductions = sum(
            (d.current for d in benefit_deductions), Decimal("0")
        )
        ytd_benefit_deductions = sum(
            (d.ytd for d in benefit_deductions), Decimal("0")
        )

        # Build vacation info
        vacation = self._build_vacation(record, employee)

        # Calculate YTD net pay
        ytd_net_pay = self._calculate_ytd_net_pay(record, ytd_records)

        # Build masked SIN if not provided
        if masked_sin is None:
            masked_sin = "***-***-***"  # Placeholder if SIN decryption not available

        return PaystubData(
            # Employee info
            employeeName=f"{employee.first_name} {employee.last_name}",
            employeeAddress=employee_address,
            sinMasked=masked_sin,
            occupation=employee.occupation,
            # Employer info
            employerName=company.company_name,
            employerAddress=employer_address,
            # Period info
            periodStart=payroll_run.period_start,
            periodEnd=payroll_run.period_end,
            payDate=payroll_run.pay_date,
            # Earnings
            earnings=earnings,
            totalEarnings=total_earnings,
            ytdEarnings=ytd_earnings,
            # Taxes
            taxes=taxes,
            totalTaxes=total_taxes,
            ytdTaxes=ytd_taxes,
            # Benefits
            nonTaxableBenefits=non_taxable_benefits,
            taxableBenefits=taxable_benefits,
            benefitDeductions=benefit_deductions,
            totalBenefitDeductions=total_benefit_deductions,
            ytdBenefitDeductions=ytd_benefit_deductions,
            # Net pay
            netPay=record.net_pay,
            ytdNetPay=ytd_net_pay,
            # Vacation
            vacation=vacation,
            # Company branding
            logoUrl=company.logo_url,
            logoBytes=logo_bytes,
        )

    def _build_address(
        self,
        street: str | None,
        city: str | None,
        province: str,
        postal_code: str | None,
    ) -> str:
        """Build formatted address string."""
        parts: list[str] = []

        if street:
            parts.append(street)

        # City, Province Postal
        location_parts: list[str] = []
        if city:
            location_parts.append(city)

        province_name = PROVINCE_NAMES.get(province, province)
        location_parts.append(province_name)

        if postal_code:
            location_parts.append(postal_code)

        if location_parts:
            parts.append(", ".join(location_parts))

        return "\n".join(parts) if parts else ""

    def _build_earnings(
        self,
        record: PayrollRecord,
        ytd_records: list[PayrollRecord],
    ) -> list[EarningLine]:
        """Build earnings line items from payroll record."""
        earnings: list[EarningLine] = []

        # Calculate YTD amounts from historical records
        ytd_regular = sum(r.gross_regular for r in ytd_records) + record.gross_regular
        ytd_overtime = sum(r.gross_overtime for r in ytd_records) + record.gross_overtime
        ytd_holiday = (
            sum(r.holiday_pay + r.holiday_premium_pay for r in ytd_records)
            + record.holiday_pay
            + record.holiday_premium_pay
        )
        ytd_vacation = (
            sum(r.vacation_pay_paid for r in ytd_records) + record.vacation_pay_paid
        )
        ytd_other = sum(r.other_earnings for r in ytd_records) + record.other_earnings

        # Regular earnings (always present)
        earnings.append(
            EarningLine(
                description="Regular Earnings",
                qty=None,  # Could add hours if tracked
                rate=None,
                current=record.gross_regular,
                ytd=ytd_regular,
            )
        )

        # Overtime (if any)
        if record.gross_overtime > 0:
            earnings.append(
                EarningLine(
                    description="Overtime",
                    qty=None,
                    rate=None,
                    current=record.gross_overtime,
                    ytd=ytd_overtime,
                )
            )

        # Holiday pay (combine regular and premium)
        holiday_total = record.holiday_pay + record.holiday_premium_pay
        if holiday_total > 0:
            earnings.append(
                EarningLine(
                    description="Holiday Pay",
                    qty=None,
                    rate=None,
                    current=holiday_total,
                    ytd=ytd_holiday,
                )
            )

        # Vacation pay paid
        if record.vacation_pay_paid > 0:
            earnings.append(
                EarningLine(
                    description="Vacation Pay",
                    qty=None,
                    rate=None,
                    current=record.vacation_pay_paid,
                    ytd=ytd_vacation,
                )
            )

        # Other earnings
        if record.other_earnings > 0:
            earnings.append(
                EarningLine(
                    description="Other Earnings",
                    qty=None,
                    rate=None,
                    current=record.other_earnings,
                    ytd=ytd_other,
                )
            )

        return earnings

    def _build_taxes(self, record: PayrollRecord) -> list[TaxLine]:
        """Build tax deduction lines from payroll record.

        All tax values should be displayed as negative (deductions).
        """
        taxes: list[TaxLine] = []

        # CPP (combine base and additional)
        cpp_total = record.cpp_employee + record.cpp_additional
        ytd_cpp = record.ytd_cpp  # Already includes both base + additional
        if cpp_total > 0 or ytd_cpp > 0:
            taxes.append(
                TaxLine(
                    description="CPP",
                    current=-cpp_total,
                    ytd=-ytd_cpp,
                )
            )

        # EI
        if record.ei_employee > 0 or record.ytd_ei > 0:
            taxes.append(
                TaxLine(
                    description="EI",
                    current=-record.ei_employee,
                    ytd=-record.ytd_ei,
                )
            )

        # Federal Tax
        if record.federal_tax > 0 or record.ytd_federal_tax > 0:
            taxes.append(
                TaxLine(
                    description="Federal Tax",
                    current=-record.federal_tax,
                    ytd=-record.ytd_federal_tax,
                )
            )

        # Provincial Tax (now shown separately as per user confirmation)
        if record.provincial_tax > 0 or record.ytd_provincial_tax > 0:
            taxes.append(
                TaxLine(
                    description="Provincial Tax",
                    current=-record.provincial_tax,
                    ytd=-record.ytd_provincial_tax,
                )
            )

        return taxes

    def _build_benefits(
        self,
        group_benefits: GroupBenefits,
        ytd_records: list[PayrollRecord],
    ) -> tuple[list[BenefitLine], list[BenefitLine], list[BenefitLine]]:
        """Build benefits lines from pay group configuration.

        Returns:
            Tuple of (non_taxable_benefits, taxable_benefits, benefit_deductions)
        """
        non_taxable: list[BenefitLine] = []
        taxable: list[BenefitLine] = []
        deductions: list[BenefitLine] = []

        # Count periods for YTD calculation (current period is not in ytd_records)
        periods_count = len(ytd_records) + 1

        # Health benefits
        if group_benefits.health.enabled:
            if group_benefits.health.employer_contribution > 0:
                benefit = BenefitLine(
                    description="Health - Employer",
                    current=group_benefits.health.employer_contribution,
                    ytd=group_benefits.health.employer_contribution * periods_count,
                )
                if group_benefits.health.is_taxable:
                    taxable.append(benefit)
                else:
                    non_taxable.append(benefit)

            if group_benefits.health.employee_deduction > 0:
                deductions.append(
                    BenefitLine(
                        description="Health - Employee",
                        current=-group_benefits.health.employee_deduction,
                        ytd=-group_benefits.health.employee_deduction * periods_count,
                    )
                )

        # Dental benefits
        if group_benefits.dental.enabled:
            if group_benefits.dental.employer_contribution > 0:
                benefit = BenefitLine(
                    description="Dental - Employer",
                    current=group_benefits.dental.employer_contribution,
                    ytd=group_benefits.dental.employer_contribution * periods_count,
                )
                if group_benefits.dental.is_taxable:
                    taxable.append(benefit)
                else:
                    non_taxable.append(benefit)

            if group_benefits.dental.employee_deduction > 0:
                deductions.append(
                    BenefitLine(
                        description="Dental - Employee",
                        current=-group_benefits.dental.employee_deduction,
                        ytd=-group_benefits.dental.employee_deduction * periods_count,
                    )
                )

        # Vision benefits
        if group_benefits.vision.enabled:
            if group_benefits.vision.employer_contribution > 0:
                benefit = BenefitLine(
                    description="Vision - Employer",
                    current=group_benefits.vision.employer_contribution,
                    ytd=group_benefits.vision.employer_contribution * periods_count,
                )
                if group_benefits.vision.is_taxable:
                    taxable.append(benefit)
                else:
                    non_taxable.append(benefit)

            if group_benefits.vision.employee_deduction > 0:
                deductions.append(
                    BenefitLine(
                        description="Vision - Employee",
                        current=-group_benefits.vision.employee_deduction,
                        ytd=-group_benefits.vision.employee_deduction * periods_count,
                    )
                )

        # Life Insurance (employer contribution is typically taxable)
        if group_benefits.life_insurance.enabled:
            if group_benefits.life_insurance.employer_contribution > 0:
                # Life insurance employer premium is ALWAYS taxable
                taxable.append(
                    BenefitLine(
                        description="Life & AD&D - Employer",
                        current=group_benefits.life_insurance.employer_contribution,
                        ytd=group_benefits.life_insurance.employer_contribution
                        * periods_count,
                    )
                )

            if group_benefits.life_insurance.employee_deduction > 0:
                deductions.append(
                    BenefitLine(
                        description="Life & AD&D - Employee",
                        current=-group_benefits.life_insurance.employee_deduction,
                        ytd=-group_benefits.life_insurance.employee_deduction
                        * periods_count,
                    )
                )

        # Disability benefits
        if group_benefits.disability.enabled:
            if group_benefits.disability.employer_contribution > 0:
                benefit = BenefitLine(
                    description="Disability - Employer",
                    current=group_benefits.disability.employer_contribution,
                    ytd=group_benefits.disability.employer_contribution * periods_count,
                )
                if group_benefits.disability.is_taxable:
                    taxable.append(benefit)
                else:
                    non_taxable.append(benefit)

            if group_benefits.disability.employee_deduction > 0:
                deductions.append(
                    BenefitLine(
                        description="Disability - Employee",
                        current=-group_benefits.disability.employee_deduction,
                        ytd=-group_benefits.disability.employee_deduction * periods_count,
                    )
                )

        return non_taxable, taxable, deductions

    def _build_vacation(
        self,
        record: PayrollRecord,
        employee: Employee,
    ) -> VacationInfo | None:
        """Build vacation info from payroll record and employee data."""
        # Only include if there's vacation accrued or balance
        if (
            record.vacation_accrued > 0
            or record.vacation_hours_taken > 0
            or employee.vacation_balance > 0
        ):
            return VacationInfo(
                earned=record.vacation_accrued,
                ytdUsed=record.vacation_hours_taken,  # This might need YTD calculation
                available=employee.vacation_balance,
            )
        return None

    def _calculate_ytd_net_pay(
        self,
        current_record: PayrollRecord,
        ytd_records: list[PayrollRecord],
    ) -> Decimal:
        """Calculate YTD net pay from current and historical records."""
        ytd_net = sum(r.net_pay for r in ytd_records)
        return ytd_net + current_record.net_pay


# Export types for type hints
__all__ = ["PaystubDataBuilder"]
