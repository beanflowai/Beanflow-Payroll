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
    PayFrequency,
    PayGroup,
    PayrollRecord,
    PayrollRun,
)
from app.models.paystub import (
    BenefitLine,
    EarningLine,
    PaystubData,
    SickLeaveInfo,
    TaxLine,
    VacationInfo,
)

# Pay periods per year by frequency
PERIODS_PER_YEAR: dict[str, int] = {
    "weekly": 52,
    "bi_weekly": 26,
    "semi_monthly": 24,
    "monthly": 12,
}

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
        skip_logo_download: bool = False,
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
            logo_bytes: Pre-downloaded logo bytes (optional)
            skip_logo_download: If True, skip logo entirely (for preview mode)

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
        earnings = self._build_earnings(record, employee, ytd_records)
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

        total_benefit_deductions = sum((d.current for d in benefit_deductions), Decimal("0"))
        ytd_benefit_deductions = sum((d.ytd for d in benefit_deductions), Decimal("0"))

        # Build vacation info
        vacation = self._build_vacation(record, employee)

        # Build sick leave info
        sick_leave = self._build_sick_leave(employee)

        # Calculate YTD net pay
        ytd_net_pay = self._calculate_ytd_net_pay(record, ytd_records)

        # Build masked SIN if not provided
        if masked_sin is None:
            masked_sin = "***-***-***"  # Placeholder if SIN decryption not available

        # Build pay rate string
        pay_rate = self._build_pay_rate(employee)

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
            # Sick Leave
            sickLeave=sick_leave,
            # Company branding (skip logo entirely if skip_logo_download=True)
            logoUrl=None if skip_logo_download else company.logo_url,
            logoBytes=None if skip_logo_download else logo_bytes,
            # Pay rate
            payRate=pay_rate,
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

    def _format_hours(self, hours: Decimal | None) -> str | None:
        """Format hours as HH:MM string for paystub display.

        Args:
            hours: Hours as decimal (e.g., 80.5 = 80 hours 30 minutes)

        Returns:
            Formatted string like "80:30" or None if hours is None or zero
        """
        if hours is None or hours == 0:
            return None
        total_minutes = int(hours * 60)
        h, m = divmod(total_minutes, 60)
        return f"{h}:{m:02d}"

    def _format_hours_decimal(self, hours: Decimal) -> str:
        """Format hours as decimal string for paystub display (e.g., '86.67 hrs').

        Args:
            hours: Hours as decimal

        Returns:
            Formatted string like "86.67" (without 'hrs' suffix)
        """
        return f"{hours:.2f}"

    def _calculate_hours_per_period(
        self, weekly_hours: Decimal, pay_frequency: PayFrequency
    ) -> Decimal:
        """Calculate standard hours per pay period for salaried employees.

        Args:
            weekly_hours: Standard hours per week (e.g., 40)
            pay_frequency: Pay frequency enum

        Returns:
            Hours per pay period (e.g., 86.67 for semi-monthly at 40h/week)
        """
        periods_per_year = PERIODS_PER_YEAR.get(pay_frequency.value, 26)
        # Hours per year = weekly_hours * 52, then divide by periods
        annual_hours = weekly_hours * Decimal("52")
        return (annual_hours / Decimal(periods_per_year)).quantize(Decimal("0.01"))

    def _calculate_equivalent_hourly_rate(
        self, annual_salary: Decimal, weekly_hours: Decimal
    ) -> Decimal:
        """Calculate equivalent hourly rate from annual salary and weekly hours.

        Args:
            annual_salary: Annual salary amount
            weekly_hours: Standard hours per week

        Returns:
            Equivalent hourly rate (e.g., $48.08/hr for $100k at 40h/week)
        """
        annual_hours = weekly_hours * Decimal("52")
        if annual_hours == 0:
            return Decimal("0")
        return (annual_salary / annual_hours).quantize(Decimal("0.01"))

    def _is_salaried_employee(self, employee: Employee) -> bool:
        """Check if an employee is salaried (has annual salary, no hourly rate).

        Args:
            employee: Employee model

        Returns:
            True if employee is salaried, False if hourly
        """
        return (
            employee.annual_salary is not None
            and employee.annual_salary > 0
            and (employee.hourly_rate is None or employee.hourly_rate == 0)
        )

    def _build_earnings(
        self,
        record: PayrollRecord,
        employee: Employee,
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
        ytd_vacation = sum(r.vacation_pay_paid for r in ytd_records) + record.vacation_pay_paid
        ytd_other = sum(r.other_earnings for r in ytd_records) + record.other_earnings

        # Regular earnings - different display for salaried vs hourly
        if self._is_salaried_employee(employee):
            # Salaried employee: show hours @ equivalent hourly rate
            standard_hours = self._calculate_hours_per_period(
                employee.standard_hours_per_week, employee.pay_frequency
            )
            equivalent_hourly_rate = self._calculate_equivalent_hourly_rate(
                employee.annual_salary, employee.standard_hours_per_week  # type: ignore
            )
            # Show actual worked hours if available and different from standard (proration)
            # Otherwise show standard hours per period
            if record.regular_hours_worked is not None and record.regular_hours_worked > 0:
                display_hours = record.regular_hours_worked
            else:
                display_hours = standard_hours
            earnings.append(
                EarningLine(
                    description="Regular Salary",
                    qty=self._format_hours_decimal(display_hours),
                    rate=equivalent_hourly_rate,
                    current=record.gross_regular,
                    ytd=ytd_regular,
                )
            )
        else:
            # Hourly employee: show actual hours worked @ hourly rate
            earnings.append(
                EarningLine(
                    description="Regular Earnings",
                    qty=self._format_hours(record.regular_hours_worked),
                    rate=employee.hourly_rate,
                    current=record.gross_regular,
                    ytd=ytd_regular,
                )
            )

        # Overtime (if any)
        if record.gross_overtime > 0:
            # Calculate OT rate (1.5x hourly rate)
            # For salaried employees, use implied hourly rate since they don't have hourly_rate
            if employee.hourly_rate:
                ot_rate = employee.hourly_rate * Decimal("1.5")
            elif self._is_salaried_employee(employee):
                implied_rate = self._calculate_equivalent_hourly_rate(
                    employee.annual_salary, employee.standard_hours_per_week  # type: ignore
                )
                ot_rate = implied_rate * Decimal("1.5")
            else:
                ot_rate = None
            earnings.append(
                EarningLine(
                    description="Overtime",
                    qty=self._format_hours(record.overtime_hours_worked),
                    rate=ot_rate,
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

        # Bonus earnings
        if record.bonus_earnings > 0:
            ytd_bonus = sum(r.bonus_earnings for r in ytd_records) + record.bonus_earnings
            earnings.append(
                EarningLine(
                    description="Bonus",
                    qty=None,
                    rate=None,
                    current=record.bonus_earnings,
                    ytd=ytd_bonus,
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
                        ytd=group_benefits.life_insurance.employer_contribution * periods_count,
                    )
                )

            if group_benefits.life_insurance.employee_deduction > 0:
                deductions.append(
                    BenefitLine(
                        description="Life & AD&D - Employee",
                        current=-group_benefits.life_insurance.employee_deduction,
                        ytd=-group_benefits.life_insurance.employee_deduction * periods_count,
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
        # Calculate available balance: old balance + accrued - paid
        available_balance = (
            employee.vacation_balance + record.vacation_accrued - record.vacation_pay_paid
        )

        # Only include if there's vacation accrued or balance
        if record.vacation_accrued > 0 or record.vacation_hours_taken > 0 or available_balance > 0:
            return VacationInfo(
                earned=record.vacation_accrued,
                ytdUsed=record.vacation_hours_taken,  # This might need YTD calculation
                available=available_balance,
            )
        return None

    def _build_sick_leave(
        self,
        employee: Employee,
    ) -> SickLeaveInfo | None:
        """Build sick leave info from employee data."""
        sick_balance = employee.sick_balance or Decimal("0")

        # Only include if there's a balance
        if sick_balance > 0:
            return SickLeaveInfo(
                paidDaysRemaining=Decimal(str(sick_balance)),
                unpaidDaysRemaining=Decimal("0"),  # Would need province config
                daysUsedYtd=Decimal("0"),  # Would need YTD tracking
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

    def _build_pay_rate(self, employee: Employee) -> str | None:
        """Build pay rate string from employee salary/hourly rate.

        Returns:
            Formatted string like "$100,000.00/yr" or "$25.00/hr", or None if not available
        """
        if employee.annual_salary and employee.annual_salary > 0:
            return f"${employee.annual_salary:,.2f}/yr"
        elif employee.hourly_rate and employee.hourly_rate > 0:
            return f"${employee.hourly_rate:,.2f}/hr"
        return None


# Export types for type hints
__all__ = ["PaystubDataBuilder"]
