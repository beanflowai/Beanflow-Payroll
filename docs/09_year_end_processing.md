# Phase 6: Year-End Processing and T4 Slip Generation

## Overview

Year-end processing is a **legally required compliance task** for all Canadian employers. This phase implements T4 slip generation, T4 Summary calculation, and CRA submission preparation for the tax year.

### Legal Requirements

- **T4 Slips**: Must be issued to all employees by **last day of February** following the tax year
- **T4 Summary**: Must accompany T4 slips when filing with CRA
- **CRA Filing Deadline**: Last day of February (same as employee distribution)
- **Penalties**: Late filing penalties apply ($10-$100 per slip, plus 10% of deductions owing)

### Official References

- **CRA RC4120**: Employers' Guide - Filing the T4 Slip and Summary
- **CRA T4 Guide**: https://www.canada.ca/en/revenue-agency/services/forms-publications/publications/rc4120.html
- **T4 XML Schema**: https://www.canada.ca/en/revenue-agency/services/e-services/e-services-businesses/internet-file-transfer-t4-t5-information-returns.html

---

## 1. Data Model

### 1.1 T4 Slip Data Model

```python
from decimal import Decimal
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, validator

class T4SlipData(BaseModel):
    """
    T4 Statement of Remuneration Paid

    Reference: CRA RC4120 Employers' Guide
    """
    # Identification
    employee_id: str
    tax_year: int = Field(..., ge=2020, le=2099)
    sin: str = Field(..., regex=r"^\d{9}$")

    # Employee Information
    employee_name: str = Field(..., max_length=60)
    employee_address_line1: str = Field(..., max_length=30)
    employee_address_line2: Optional[str] = Field(None, max_length=30)
    employee_city: str = Field(..., max_length=28)
    employee_province: str = Field(..., regex=r"^[A-Z]{2}$")
    employee_postal_code: str = Field(..., regex=r"^[A-Z]\d[A-Z]\s?\d[A-Z]\d$")

    # Employer Information
    employer_name: str = Field(..., max_length=60)
    employer_account_number: str = Field(..., regex=r"^\d{9}RP\d{4}$")  # e.g., 123456789RP0001

    # T4 Boxes (all amounts in CAD)
    box_14_employment_income: Decimal = Field(default=Decimal("0"), decimal_places=2)
    box_16_cpp_contributions: Decimal = Field(default=Decimal("0"), decimal_places=2)
    box_18_ei_premiums: Decimal = Field(default=Decimal("0"), decimal_places=2)
    box_22_income_tax_deducted: Decimal = Field(default=Decimal("0"), decimal_places=2)
    box_24_ei_insurable_earnings: Decimal = Field(default=Decimal("0"), decimal_places=2)
    box_26_cpp_pensionable_earnings: Decimal = Field(default=Decimal("0"), decimal_places=2)

    # Optional Boxes
    box_20_rpp_contributions: Optional[Decimal] = Field(None, decimal_places=2)  # Registered Pension Plan
    box_40_other_taxable_allowances: Optional[Decimal] = Field(None, decimal_places=2)
    box_44_union_dues: Optional[Decimal] = Field(None, decimal_places=2)
    box_46_charitable_donations: Optional[Decimal] = Field(None, decimal_places=2)
    box_52_pension_adjustment: Optional[Decimal] = Field(None, decimal_places=2)

    # Provincial Boxes (code 12-99)
    box_provincial_employment_income: Decimal = Field(default=Decimal("0"), decimal_places=2)
    box_provincial_tax_deducted: Decimal = Field(default=Decimal("0"), decimal_places=2)
    province_of_employment: str = Field(..., regex=r"^[A-Z]{2}$")

    # Other Codes (Box 28-38, 56-66 for various benefits and deductions)
    # Add as needed based on business requirements

    @validator("sin")
    def validate_sin(cls, v):
        """Validate SIN using Luhn algorithm"""
        if not v.isdigit():
            raise ValueError("SIN must be 9 digits")

        # Luhn algorithm for SIN validation
        digits = [int(d) for d in v]
        checksum = 0
        for i, digit in enumerate(digits):
            if i % 2 == 1:  # Even positions (0-indexed)
                doubled = digit * 2
                checksum += doubled if doubled < 10 else doubled - 9
            else:
                checksum += digit

        if checksum % 10 != 0:
            raise ValueError("Invalid SIN checksum")

        return v

    @validator("box_14_employment_income")
    def validate_employment_income(cls, v, values):
        """Employment income should match or exceed CPP/EI insurable earnings"""
        if v < Decimal("0"):
            raise ValueError("Employment income cannot be negative")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "employee_id": "emp_12345",
                "tax_year": 2025,
                "sin": "123456782",
                "employee_name": "John Doe",
                "employee_address_line1": "123 Main St",
                "employee_city": "Toronto",
                "employee_province": "ON",
                "employee_postal_code": "M5H 2N2",
                "employer_name": "Example Corp",
                "employer_account_number": "123456789RP0001",
                "box_14_employment_income": "65000.00",
                "box_16_cpp_contributions": "3754.45",
                "box_18_ei_premiums": "1053.00",
                "box_22_income_tax_deducted": "12450.00",
                "box_24_ei_insurable_earnings": "65000.00",
                "box_26_cpp_pensionable_earnings": "65000.00",
                "box_provincial_employment_income": "65000.00",
                "box_provincial_tax_deducted": "4200.00",
                "province_of_employment": "ON"
            }
        }


class T4Summary(BaseModel):
    """
    T4 Summary - Summary of Remuneration Paid

    Aggregates all T4 slips for the tax year
    """
    tax_year: int = Field(..., ge=2020, le=2099)
    employer_name: str
    employer_account_number: str

    # Summary Totals
    total_number_of_t4_slips: int = Field(..., ge=1)

    total_employment_income: Decimal = Field(default=Decimal("0"), decimal_places=2)
    total_cpp_contributions: Decimal = Field(default=Decimal("0"), decimal_places=2)
    total_ei_premiums: Decimal = Field(default=Decimal("0"), decimal_places=2)
    total_income_tax_deducted: Decimal = Field(default=Decimal("0"), decimal_places=2)

    # Employer Portions (for reconciliation)
    total_employer_cpp_contributions: Decimal = Field(default=Decimal("0"), decimal_places=2)
    total_employer_ei_premiums: Decimal = Field(default=Decimal("0"), decimal_places=2)

    # Total Deductions Remitted to CRA
    total_deductions_remitted: Decimal = Field(default=Decimal("0"), decimal_places=2)

    @validator("total_deductions_remitted")
    def calculate_total_remitted(cls, v, values):
        """
        Total remitted = Employee CPP + Employer CPP + Employee EI + Employer EI + Income Tax
        """
        expected = (
            values.get("total_cpp_contributions", Decimal("0")) +
            values.get("total_employer_cpp_contributions", Decimal("0")) +
            values.get("total_ei_premiums", Decimal("0")) +
            values.get("total_employer_ei_premiums", Decimal("0")) +
            values.get("total_income_tax_deducted", Decimal("0"))
        )

        if v != Decimal("0") and abs(v - expected) > Decimal("1.00"):
            # Allow $1 variance for rounding
            raise ValueError(f"Total remitted {v} does not match calculated {expected}")

        return expected if v == Decimal("0") else v

    class Config:
        json_schema_extra = {
            "example": {
                "tax_year": 2025,
                "employer_name": "Example Corp",
                "employer_account_number": "123456789RP0001",
                "total_number_of_t4_slips": 50,
                "total_employment_income": "3250000.00",
                "total_cpp_contributions": "187722.50",
                "total_ei_premiums": "52650.00",
                "total_income_tax_deducted": "622500.00",
                "total_employer_cpp_contributions": "187722.50",
                "total_employer_ei_premiums": "73710.00",
                "total_deductions_remitted": "1124305.00"
            }
        }
```

---

## 2. T4 Data Aggregation Service

### 2.1 Aggregate Payroll Records for the Year

```python
from typing import List
from decimal import Decimal
from datetime import date

class T4AggregationService:
    """
    Aggregate payroll records for the tax year to generate T4 slips
    """

    def __init__(self, firestore_service):
        self.firestore = firestore_service

    async def aggregate_employee_year(
        self,
        ledger_id: str,
        employee_id: str,
        tax_year: int
    ) -> T4SlipData:
        """
        Aggregate all payroll records for an employee for the tax year

        Args:
            ledger_id: Ledger identifier
            employee_id: Employee identifier
            tax_year: Tax year (e.g., 2025)

        Returns:
            T4SlipData with aggregated amounts
        """
        # Fetch all payroll records for the year
        start_date = date(tax_year, 1, 1)
        end_date = date(tax_year, 12, 31)

        payroll_records = await self.firestore.get_payroll_records(
            ledger_id=ledger_id,
            employee_id=employee_id,
            start_date=start_date,
            end_date=end_date
        )

        # Fetch employee information
        employee = await self.firestore.get_employee(ledger_id, employee_id)
        employer = await self.firestore.get_employer_info(ledger_id)

        # Aggregate amounts
        total_gross = Decimal("0")
        total_cpp = Decimal("0")
        total_ei = Decimal("0")
        total_federal_tax = Decimal("0")
        total_provincial_tax = Decimal("0")
        total_union_dues = Decimal("0")

        cpp_pensionable_earnings = Decimal("0")
        ei_insurable_earnings = Decimal("0")

        for record in payroll_records:
            total_gross += record.gross_pay
            total_cpp += record.cpp_employee
            total_ei += record.ei_employee
            total_federal_tax += record.federal_tax
            total_provincial_tax += record.provincial_tax

            if record.union_dues:
                total_union_dues += record.union_dues

            # CPP pensionable earnings (subject to annual maximum)
            cpp_pensionable_earnings += record.cpp_pensionable_earnings

            # EI insurable earnings (subject to annual maximum)
            ei_insurable_earnings += record.ei_insurable_earnings

        # Build T4 slip
        t4_slip = T4SlipData(
            employee_id=employee_id,
            tax_year=tax_year,
            sin=employee.sin,
            employee_name=f"{employee.first_name} {employee.last_name}",
            employee_address_line1=employee.address_line1,
            employee_address_line2=employee.address_line2,
            employee_city=employee.city,
            employee_province=employee.province,
            employee_postal_code=employee.postal_code,
            employer_name=employer.legal_name,
            employer_account_number=employer.cra_payroll_account,
            box_14_employment_income=total_gross,
            box_16_cpp_contributions=total_cpp,
            box_18_ei_premiums=total_ei,
            box_22_income_tax_deducted=total_federal_tax + total_provincial_tax,
            box_24_ei_insurable_earnings=ei_insurable_earnings,
            box_26_cpp_pensionable_earnings=cpp_pensionable_earnings,
            box_44_union_dues=total_union_dues if total_union_dues > Decimal("0") else None,
            box_provincial_employment_income=total_gross,
            box_provincial_tax_deducted=total_provincial_tax,
            province_of_employment=employee.province
        )

        return t4_slip

    async def generate_all_t4_slips(
        self,
        ledger_id: str,
        tax_year: int
    ) -> List[T4SlipData]:
        """
        Generate T4 slips for all employees in the ledger for the tax year

        Args:
            ledger_id: Ledger identifier
            tax_year: Tax year

        Returns:
            List of T4SlipData
        """
        employees = await self.firestore.get_employees(ledger_id)

        t4_slips = []
        for employee in employees:
            # Check if employee has any payroll records in the year
            payroll_count = await self.firestore.count_payroll_records(
                ledger_id=ledger_id,
                employee_id=employee.id,
                tax_year=tax_year
            )

            if payroll_count > 0:
                t4_slip = await self.aggregate_employee_year(
                    ledger_id=ledger_id,
                    employee_id=employee.id,
                    tax_year=tax_year
                )
                t4_slips.append(t4_slip)

        return t4_slips

    async def generate_t4_summary(
        self,
        ledger_id: str,
        tax_year: int,
        t4_slips: List[T4SlipData]
    ) -> T4Summary:
        """
        Generate T4 Summary from all T4 slips

        Args:
            ledger_id: Ledger identifier
            tax_year: Tax year
            t4_slips: List of T4 slips to summarize

        Returns:
            T4Summary with aggregated totals
        """
        employer = await self.firestore.get_employer_info(ledger_id)

        total_employment_income = sum(slip.box_14_employment_income for slip in t4_slips)
        total_cpp = sum(slip.box_16_cpp_contributions for slip in t4_slips)
        total_ei = sum(slip.box_18_ei_premiums for slip in t4_slips)
        total_tax = sum(slip.box_22_income_tax_deducted for slip in t4_slips)

        # Employer portions (equal to employee for CPP, 1.4x for EI)
        total_employer_cpp = total_cpp  # Employer pays same as employee
        total_employer_ei = total_ei * Decimal("1.4")

        summary = T4Summary(
            tax_year=tax_year,
            employer_name=employer.legal_name,
            employer_account_number=employer.cra_payroll_account,
            total_number_of_t4_slips=len(t4_slips),
            total_employment_income=total_employment_income,
            total_cpp_contributions=total_cpp,
            total_ei_premiums=total_ei,
            total_income_tax_deducted=total_tax,
            total_employer_cpp_contributions=total_employer_cpp,
            total_employer_ei_premiums=total_employer_ei,
            total_deductions_remitted=Decimal("0")  # Will be calculated by validator
        )

        return summary
```

---

## 3. T4 PDF Generation

### 3.1 PDF Layout Service (using ReportLab)

```python
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from io import BytesIO

class T4PDFGenerator:
    """
    Generate T4 slip PDF using ReportLab

    Layout reference: CRA T4 slip (2 copies per page)
    """

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Create custom styles for T4 slip"""
        self.styles.add(ParagraphStyle(
            name='T4Title',
            parent=self.styles['Heading1'],
            fontSize=14,
            textColor=colors.HexColor('#000000'),
            alignment=TA_CENTER,
            spaceAfter=6
        ))

        self.styles.add(ParagraphStyle(
            name='T4BoxLabel',
            parent=self.styles['Normal'],
            fontSize=7,
            textColor=colors.HexColor('#666666'),
            leading=9
        ))

        self.styles.add(ParagraphStyle(
            name='T4BoxValue',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#000000'),
            alignment=TA_RIGHT,
            leading=12
        ))

    def generate_t4_slip_pdf(self, t4_slip: T4SlipData) -> bytes:
        """
        Generate T4 slip PDF for a single employee

        Args:
            t4_slip: T4SlipData

        Returns:
            PDF bytes
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
            leftMargin=0.5 * inch,
            rightMargin=0.5 * inch
        )

        story = []

        # Title
        title = Paragraph(f"T4 - Statement of Remuneration Paid<br/>{t4_slip.tax_year}", self.styles['T4Title'])
        story.append(title)
        story.append(Spacer(1, 12))

        # Employer Information
        employer_data = [
            ['Employer Name', t4_slip.employer_name],
            ['Payroll Account Number', t4_slip.employer_account_number]
        ]
        employer_table = Table(employer_data, colWidths=[2 * inch, 4.5 * inch])
        employer_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6)
        ]))
        story.append(employer_table)
        story.append(Spacer(1, 12))

        # Employee Information
        employee_address = f"{t4_slip.employee_address_line1}"
        if t4_slip.employee_address_line2:
            employee_address += f"\n{t4_slip.employee_address_line2}"
        employee_address += f"\n{t4_slip.employee_city}, {t4_slip.employee_province} {t4_slip.employee_postal_code}"

        employee_data = [
            ['Employee Name', t4_slip.employee_name],
            ['Social Insurance Number', f"{t4_slip.sin[:3]} {t4_slip.sin[3:6]} {t4_slip.sin[6:]}"],
            ['Address', employee_address]
        ]
        employee_table = Table(employee_data, colWidths=[2 * inch, 4.5 * inch])
        employee_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6)
        ]))
        story.append(employee_table)
        story.append(Spacer(1, 18))

        # T4 Boxes
        boxes_data = [
            # Row 1
            [
                'Box 14\nEmployment Income',
                f"${t4_slip.box_14_employment_income:,.2f}",
                'Box 16\nCPP Contributions',
                f"${t4_slip.box_16_cpp_contributions:,.2f}"
            ],
            # Row 2
            [
                'Box 18\nEI Premiums',
                f"${t4_slip.box_18_ei_premiums:,.2f}",
                'Box 22\nIncome Tax Deducted',
                f"${t4_slip.box_22_income_tax_deducted:,.2f}"
            ],
            # Row 3
            [
                'Box 24\nEI Insurable Earnings',
                f"${t4_slip.box_24_ei_insurable_earnings:,.2f}",
                'Box 26\nCPP Pensionable Earnings',
                f"${t4_slip.box_26_cpp_pensionable_earnings:,.2f}"
            ]
        ]

        # Add optional boxes if present
        if t4_slip.box_44_union_dues and t4_slip.box_44_union_dues > Decimal("0"):
            boxes_data.append([
                'Box 44\nUnion Dues',
                f"${t4_slip.box_44_union_dues:,.2f}",
                '',
                ''
            ])

        boxes_table = Table(boxes_data, colWidths=[1.8 * inch, 1.5 * inch, 1.8 * inch, 1.4 * inch])
        boxes_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
            ('FONTNAME', (3, 0), (3, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6)
        ]))
        story.append(boxes_table)
        story.append(Spacer(1, 18))

        # Provincial Information
        provincial_data = [
            ['Province of Employment', t4_slip.province_of_employment],
            ['Provincial Employment Income', f"${t4_slip.box_provincial_employment_income:,.2f}"],
            ['Provincial Tax Deducted', f"${t4_slip.box_provincial_tax_deducted:,.2f}"]
        ]
        provincial_table = Table(provincial_data, colWidths=[2.5 * inch, 2 * inch])
        provincial_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6)
        ]))
        story.append(provincial_table)
        story.append(Spacer(1, 24))

        # Footer
        footer_text = Paragraph(
            "Keep this slip for your income tax return.<br/>"
            "Gardez ce feuillet pour votre déclaration de revenus.",
            self.styles['Normal']
        )
        story.append(footer_text)

        # Build PDF
        doc.build(story)

        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes

    def generate_t4_summary_pdf(self, summary: T4Summary, t4_slips: List[T4SlipData]) -> bytes:
        """
        Generate T4 Summary PDF

        Args:
            summary: T4Summary data
            t4_slips: List of T4 slips (for employee listing)

        Returns:
            PDF bytes
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
            leftMargin=0.5 * inch,
            rightMargin=0.5 * inch
        )

        story = []

        # Title
        title = Paragraph(f"T4 Summary - Summary of Remuneration Paid<br/>{summary.tax_year}", self.styles['T4Title'])
        story.append(title)
        story.append(Spacer(1, 12))

        # Employer Information
        employer_data = [
            ['Employer Name', summary.employer_name],
            ['Payroll Account Number', summary.employer_account_number],
            ['Number of T4 Slips', str(summary.total_number_of_t4_slips)]
        ]
        employer_table = Table(employer_data, colWidths=[2.5 * inch, 4 * inch])
        employer_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6)
        ]))
        story.append(employer_table)
        story.append(Spacer(1, 18))

        # Summary Totals
        summary_data = [
            ['Description', 'Amount'],
            ['Total Employment Income', f"${summary.total_employment_income:,.2f}"],
            ['Total CPP Contributions (Employee)', f"${summary.total_cpp_contributions:,.2f}"],
            ['Total CPP Contributions (Employer)', f"${summary.total_employer_cpp_contributions:,.2f}"],
            ['Total EI Premiums (Employee)', f"${summary.total_ei_premiums:,.2f}"],
            ['Total EI Premiums (Employer)', f"${summary.total_employer_ei_premiums:,.2f}"],
            ['Total Income Tax Deducted', f"${summary.total_income_tax_deducted:,.2f}"],
            ['', ''],
            ['Total Deductions Remitted to CRA', f"${summary.total_deductions_remitted:,.2f}"]
        ]

        summary_table = Table(summary_data, colWidths=[4 * inch, 2.5 * inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#333333')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f0f0f0')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
            ('GRID', (0, -1), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6)
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 24))

        # Employee Listing (first page only)
        story.append(Paragraph("Employee Listing (Partial)", self.styles['Heading2']))
        story.append(Spacer(1, 6))

        employee_listing = [['Employee Name', 'SIN', 'Employment Income']]
        for slip in t4_slips[:10]:  # Show first 10 employees
            employee_listing.append([
                slip.employee_name,
                f"{slip.sin[:3]}-{slip.sin[3:6]}-{slip.sin[6:]}",
                f"${slip.box_14_employment_income:,.2f}"
            ])

        if len(t4_slips) > 10:
            employee_listing.append(['...', '...', '...'])

        listing_table = Table(employee_listing, colWidths=[3 * inch, 1.8 * inch, 1.7 * inch])
        listing_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#666666')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4)
        ]))
        story.append(listing_table)

        # Build PDF
        doc.build(story)

        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes
```

---

## 4. T4 XML Generation for CRA Submission

### 4.1 XML Schema Compliance

CRA accepts T4 submissions via XML following the T619 schema.

```python
import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import List

class T4XMLGenerator:
    """
    Generate T4 XML file for CRA Internet File Transfer

    Reference: CRA T619 XML Schema
    https://www.canada.ca/en/revenue-agency/services/e-services/e-services-businesses/internet-file-transfer-t4-t5-information-returns.html
    """

    def __init__(self):
        self.schema_version = "1.4"

    def generate_xml(
        self,
        summary: T4Summary,
        t4_slips: List[T4SlipData],
        transmitter_number: str,
        transmitter_name: str,
        transmitter_contact_name: str,
        transmitter_contact_phone: str,
        transmitter_contact_email: str
    ) -> str:
        """
        Generate T4 XML for CRA submission

        Args:
            summary: T4Summary
            t4_slips: List of T4SlipData
            transmitter_number: CRA-assigned transmitter number (MM or MMxxxxxx)
            transmitter_name: Company name submitting the file
            transmitter_contact_name: Contact person name
            transmitter_contact_phone: Contact phone (10 digits)
            transmitter_contact_email: Contact email

        Returns:
            Formatted XML string
        """
        # Root element
        root = ET.Element("Return", {
            "xmlns": "http://www.cra-arc.gc.ca/xmlns/t4",
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsi:schemaLocation": "http://www.cra-arc.gc.ca/xmlns/t4 t4-return-1.4.xsd"
        })

        # Transmitter section
        transmitter = ET.SubElement(root, "Transmitter")
        ET.SubElement(transmitter, "TransmitterNumber").text = transmitter_number
        ET.SubElement(transmitter, "TransmitterName").text = transmitter_name

        transmitter_contact = ET.SubElement(transmitter, "TransmitterContact")
        ET.SubElement(transmitter_contact, "ContactName").text = transmitter_contact_name
        ET.SubElement(transmitter_contact, "ContactPhone").text = transmitter_contact_phone
        ET.SubElement(transmitter_contact, "ContactEmail").text = transmitter_contact_email

        # Return section
        return_elem = ET.SubElement(root, "T4")
        ET.SubElement(return_elem, "TaxationYear").text = str(summary.tax_year)
        ET.SubElement(return_elem, "SlipCount").text = str(summary.total_number_of_t4_slips)

        # Summary section
        summary_elem = ET.SubElement(return_elem, "Summary")
        ET.SubElement(summary_elem, "PayrollAccountNumber").text = summary.employer_account_number
        ET.SubElement(summary_elem, "EmployerName").text = summary.employer_name

        summary_amounts = ET.SubElement(summary_elem, "SummaryAmounts")
        ET.SubElement(summary_amounts, "Box14Total").text = f"{summary.total_employment_income:.2f}"
        ET.SubElement(summary_amounts, "Box16Total").text = f"{summary.total_cpp_contributions:.2f}"
        ET.SubElement(summary_amounts, "Box18Total").text = f"{summary.total_ei_premiums:.2f}"
        ET.SubElement(summary_amounts, "Box22Total").text = f"{summary.total_income_tax_deducted:.2f}"

        # Slips section
        slips_elem = ET.SubElement(return_elem, "Slips")
        for slip in t4_slips:
            self._add_slip_to_xml(slips_elem, slip)

        # Pretty print XML
        xml_string = ET.tostring(root, encoding='unicode')
        parsed = minidom.parseString(xml_string)
        pretty_xml = parsed.toprettyxml(indent="  ", encoding="UTF-8")

        return pretty_xml.decode('utf-8')

    def _add_slip_to_xml(self, parent: ET.Element, slip: T4SlipData):
        """Add individual T4 slip to XML"""
        slip_elem = ET.SubElement(parent, "Slip")

        # Employee information
        employee = ET.SubElement(slip_elem, "Employee")
        ET.SubElement(employee, "SIN").text = slip.sin

        name = ET.SubElement(employee, "Name")
        # Split name into first and last
        name_parts = slip.employee_name.split(' ', 1)
        ET.SubElement(name, "FirstName").text = name_parts[0]
        if len(name_parts) > 1:
            ET.SubElement(name, "LastName").text = name_parts[1]
        else:
            ET.SubElement(name, "LastName").text = name_parts[0]

        address = ET.SubElement(employee, "Address")
        ET.SubElement(address, "AddressLine1").text = slip.employee_address_line1
        if slip.employee_address_line2:
            ET.SubElement(address, "AddressLine2").text = slip.employee_address_line2
        ET.SubElement(address, "City").text = slip.employee_city
        ET.SubElement(address, "Province").text = slip.employee_province
        ET.SubElement(address, "PostalCode").text = slip.employee_postal_code.replace(' ', '')

        # T4 amounts
        amounts = ET.SubElement(slip_elem, "Amounts")
        ET.SubElement(amounts, "Box14").text = f"{slip.box_14_employment_income:.2f}"
        ET.SubElement(amounts, "Box16").text = f"{slip.box_16_cpp_contributions:.2f}"
        ET.SubElement(amounts, "Box18").text = f"{slip.box_18_ei_premiums:.2f}"
        ET.SubElement(amounts, "Box22").text = f"{slip.box_22_income_tax_deducted:.2f}"
        ET.SubElement(amounts, "Box24").text = f"{slip.box_24_ei_insurable_earnings:.2f}"
        ET.SubElement(amounts, "Box26").text = f"{slip.box_26_cpp_pensionable_earnings:.2f}"

        # Optional boxes
        if slip.box_44_union_dues and slip.box_44_union_dues > Decimal("0"):
            ET.SubElement(amounts, "Box44").text = f"{slip.box_44_union_dues:.2f}"

        # Provincial information
        provincial = ET.SubElement(slip_elem, "Provincial")
        ET.SubElement(provincial, "ProvinceOfEmployment").text = slip.province_of_employment
        ET.SubElement(provincial, "ProvincialEmploymentIncome").text = f"{slip.box_provincial_employment_income:.2f}"
        ET.SubElement(provincial, "ProvincialTax").text = f"{slip.box_provincial_tax_deducted:.2f}"
```

---

## 5. Storage and Distribution

### 5.1 Google Drive Storage

```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from io import BytesIO

class T4StorageService:
    """
    Store T4 slips and summary in Google Drive
    """

    def __init__(self, credentials: Credentials):
        self.service = build('drive', 'v3', credentials=credentials)

    async def upload_t4_slip(
        self,
        ledger_id: str,
        tax_year: int,
        employee_id: str,
        pdf_bytes: bytes
    ) -> str:
        """
        Upload T4 slip PDF to Google Drive

        Args:
            ledger_id: Ledger identifier
            tax_year: Tax year
            employee_id: Employee identifier
            pdf_bytes: PDF file bytes

        Returns:
            Google Drive file ID
        """
        # Create folder structure: /Payroll/{ledger_id}/T4-{tax_year}/
        folder_id = await self._get_or_create_folder(
            ledger_id=ledger_id,
            folder_name=f"T4-{tax_year}"
        )

        # Upload file
        file_metadata = {
            'name': f"T4_{tax_year}_{employee_id}.pdf",
            'parents': [folder_id],
            'mimeType': 'application/pdf'
        }

        media = MediaIoBaseUpload(
            BytesIO(pdf_bytes),
            mimetype='application/pdf',
            resumable=True
        )

        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()

        return file.get('id')

    async def upload_t4_summary(
        self,
        ledger_id: str,
        tax_year: int,
        pdf_bytes: bytes
    ) -> str:
        """Upload T4 Summary PDF to Google Drive"""
        folder_id = await self._get_or_create_folder(
            ledger_id=ledger_id,
            folder_name=f"T4-{tax_year}"
        )

        file_metadata = {
            'name': f"T4_Summary_{tax_year}.pdf",
            'parents': [folder_id],
            'mimeType': 'application/pdf'
        }

        media = MediaIoBaseUpload(
            BytesIO(pdf_bytes),
            mimetype='application/pdf',
            resumable=True
        )

        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()

        return file.get('id')

    async def upload_t4_xml(
        self,
        ledger_id: str,
        tax_year: int,
        xml_string: str
    ) -> str:
        """Upload T4 XML file for CRA submission"""
        folder_id = await self._get_or_create_folder(
            ledger_id=ledger_id,
            folder_name=f"T4-{tax_year}"
        )

        file_metadata = {
            'name': f"T4_CRA_Submission_{tax_year}.xml",
            'parents': [folder_id],
            'mimeType': 'application/xml'
        }

        media = MediaIoBaseUpload(
            BytesIO(xml_string.encode('utf-8')),
            mimetype='application/xml',
            resumable=True
        )

        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()

        return file.get('id')

    async def _get_or_create_folder(self, ledger_id: str, folder_name: str) -> str:
        """Get or create folder in Google Drive"""
        # Implementation similar to paystub storage service
        # Returns folder ID
        pass
```

---

## 6. API Endpoints

### 6.1 FastAPI Routes

```python
from fastapi import APIRouter, Depends, HTTPException
from typing import List

router = APIRouter(prefix="/api/v1/year-end", tags=["year-end"])

@router.post("/generate-t4-slips/{ledger_id}/{tax_year}")
async def generate_t4_slips(
    ledger_id: str,
    tax_year: int,
    current_user=Depends(get_current_user),
    firestore_service=Depends(get_firestore_service)
):
    """
    Generate T4 slips for all employees for the tax year

    - Aggregates payroll data
    - Generates PDF for each employee
    - Stores in Google Drive
    - Returns list of T4 slips with download links
    """
    # Check authorization
    if not await check_ledger_access(current_user.uid, ledger_id):
        raise HTTPException(status_code=403, detail="Access denied")

    # Generate T4 slips
    aggregation_service = T4AggregationService(firestore_service)
    t4_slips = await aggregation_service.generate_all_t4_slips(ledger_id, tax_year)

    if not t4_slips:
        raise HTTPException(status_code=404, detail="No payroll records found for tax year")

    # Generate PDFs and upload
    pdf_generator = T4PDFGenerator()
    storage_service = T4StorageService(current_user.credentials)

    results = []
    for slip in t4_slips:
        pdf_bytes = pdf_generator.generate_t4_slip_pdf(slip)
        file_id = await storage_service.upload_t4_slip(
            ledger_id=ledger_id,
            tax_year=tax_year,
            employee_id=slip.employee_id,
            pdf_bytes=pdf_bytes
        )

        results.append({
            "employee_id": slip.employee_id,
            "employee_name": slip.employee_name,
            "file_id": file_id,
            "box_14_employment_income": float(slip.box_14_employment_income),
            "box_22_income_tax_deducted": float(slip.box_22_income_tax_deducted)
        })

    return {
        "tax_year": tax_year,
        "total_slips": len(t4_slips),
        "slips": results
    }


@router.post("/generate-t4-summary/{ledger_id}/{tax_year}")
async def generate_t4_summary(
    ledger_id: str,
    tax_year: int,
    current_user=Depends(get_current_user),
    firestore_service=Depends(get_firestore_service)
):
    """
    Generate T4 Summary for the tax year

    - Aggregates all T4 slips
    - Generates summary PDF
    - Generates XML file for CRA submission
    - Returns summary data with download links
    """
    # Check authorization
    if not await check_ledger_access(current_user.uid, ledger_id):
        raise HTTPException(status_code=403, detail="Access denied")

    # Generate T4 slips first
    aggregation_service = T4AggregationService(firestore_service)
    t4_slips = await aggregation_service.generate_all_t4_slips(ledger_id, tax_year)

    if not t4_slips:
        raise HTTPException(status_code=404, detail="No T4 slips found")

    # Generate summary
    summary = await aggregation_service.generate_t4_summary(ledger_id, tax_year, t4_slips)

    # Generate PDF
    pdf_generator = T4PDFGenerator()
    summary_pdf = pdf_generator.generate_t4_summary_pdf(summary, t4_slips)

    # Generate XML
    xml_generator = T4XMLGenerator()
    employer = await firestore_service.get_employer_info(ledger_id)
    xml_string = xml_generator.generate_xml(
        summary=summary,
        t4_slips=t4_slips,
        transmitter_number=employer.cra_transmitter_number,
        transmitter_name=employer.legal_name,
        transmitter_contact_name=employer.contact_name,
        transmitter_contact_phone=employer.contact_phone,
        transmitter_contact_email=employer.contact_email
    )

    # Upload to Google Drive
    storage_service = T4StorageService(current_user.credentials)

    summary_file_id = await storage_service.upload_t4_summary(
        ledger_id=ledger_id,
        tax_year=tax_year,
        pdf_bytes=summary_pdf
    )

    xml_file_id = await storage_service.upload_t4_xml(
        ledger_id=ledger_id,
        tax_year=tax_year,
        xml_string=xml_string
    )

    return {
        "tax_year": tax_year,
        "summary": {
            "total_slips": summary.total_number_of_t4_slips,
            "total_employment_income": float(summary.total_employment_income),
            "total_cpp_contributions": float(summary.total_cpp_contributions),
            "total_ei_premiums": float(summary.total_ei_premiums),
            "total_income_tax": float(summary.total_income_tax_deducted),
            "total_remitted": float(summary.total_deductions_remitted)
        },
        "files": {
            "summary_pdf_id": summary_file_id,
            "xml_submission_id": xml_file_id
        }
    }


@router.get("/t4-slips/{ledger_id}/{tax_year}")
async def list_t4_slips(
    ledger_id: str,
    tax_year: int,
    current_user=Depends(get_current_user),
    firestore_service=Depends(get_firestore_service)
):
    """
    List all T4 slips for the tax year (without generating PDFs)
    """
    if not await check_ledger_access(current_user.uid, ledger_id):
        raise HTTPException(status_code=403, detail="Access denied")

    aggregation_service = T4AggregationService(firestore_service)
    t4_slips = await aggregation_service.generate_all_t4_slips(ledger_id, tax_year)

    return {
        "tax_year": tax_year,
        "total_slips": len(t4_slips),
        "slips": [
            {
                "employee_id": slip.employee_id,
                "employee_name": slip.employee_name,
                "sin": f"{slip.sin[:3]}-{slip.sin[3:6]}-{slip.sin[6:]}",
                "box_14": float(slip.box_14_employment_income),
                "box_16": float(slip.box_16_cpp_contributions),
                "box_18": float(slip.box_18_ei_premiums),
                "box_22": float(slip.box_22_income_tax_deducted)
            }
            for slip in t4_slips
        ]
    }
```

---

## 7. Testing and Validation

### 7.1 Test Cases

```python
import pytest
from decimal import Decimal
from datetime import date

@pytest.fixture
def sample_t4_slip():
    return T4SlipData(
        employee_id="emp_001",
        tax_year=2025,
        sin="123456782",
        employee_name="John Doe",
        employee_address_line1="123 Main St",
        employee_city="Toronto",
        employee_province="ON",
        employee_postal_code="M5H2N2",
        employer_name="Test Corp",
        employer_account_number="123456789RP0001",
        box_14_employment_income=Decimal("65000.00"),
        box_16_cpp_contributions=Decimal("3754.45"),
        box_18_ei_premiums=Decimal("1053.00"),
        box_22_income_tax_deducted=Decimal("12450.00"),
        box_24_ei_insurable_earnings=Decimal("65000.00"),
        box_26_cpp_pensionable_earnings=Decimal("65000.00"),
        box_provincial_employment_income=Decimal("65000.00"),
        box_provincial_tax_deducted=Decimal("4200.00"),
        province_of_employment="ON"
    )


def test_t4_slip_validation(sample_t4_slip):
    """Test T4 slip data validation"""
    assert sample_t4_slip.box_14_employment_income == Decimal("65000.00")
    assert sample_t4_slip.sin == "123456782"

    # Test invalid SIN
    with pytest.raises(ValueError):
        T4SlipData(
            **{**sample_t4_slip.dict(), "sin": "000000000"}  # Invalid checksum
        )


def test_t4_summary_calculation():
    """Test T4 Summary automatic calculation"""
    summary = T4Summary(
        tax_year=2025,
        employer_name="Test Corp",
        employer_account_number="123456789RP0001",
        total_number_of_t4_slips=2,
        total_employment_income=Decimal("130000.00"),
        total_cpp_contributions=Decimal("7508.90"),
        total_ei_premiums=Decimal("2106.00"),
        total_income_tax_deducted=Decimal("24900.00"),
        total_employer_cpp_contributions=Decimal("7508.90"),
        total_employer_ei_premiums=Decimal("2948.40")
    )

    # Check automatic calculation
    expected_remitted = (
        Decimal("7508.90") +  # Employee CPP
        Decimal("7508.90") +  # Employer CPP
        Decimal("2106.00") +  # Employee EI
        Decimal("2948.40") +  # Employer EI
        Decimal("24900.00")   # Income tax
    )
    assert summary.total_deductions_remitted == expected_remitted


def test_t4_pdf_generation(sample_t4_slip):
    """Test T4 PDF generation"""
    generator = T4PDFGenerator()
    pdf_bytes = generator.generate_t4_slip_pdf(sample_t4_slip)

    assert pdf_bytes is not None
    assert len(pdf_bytes) > 0
    assert pdf_bytes[:4] == b'%PDF'  # PDF magic number


def test_t4_xml_generation(sample_t4_slip):
    """Test T4 XML generation for CRA"""
    summary = T4Summary(
        tax_year=2025,
        employer_name="Test Corp",
        employer_account_number="123456789RP0001",
        total_number_of_t4_slips=1,
        total_employment_income=sample_t4_slip.box_14_employment_income,
        total_cpp_contributions=sample_t4_slip.box_16_cpp_contributions,
        total_ei_premiums=sample_t4_slip.box_18_ei_premiums,
        total_income_tax_deducted=sample_t4_slip.box_22_income_tax_deducted,
        total_employer_cpp_contributions=sample_t4_slip.box_16_cpp_contributions,
        total_employer_ei_premiums=sample_t4_slip.box_18_ei_premiums * Decimal("1.4")
    )

    generator = T4XMLGenerator()
    xml_string = generator.generate_xml(
        summary=summary,
        t4_slips=[sample_t4_slip],
        transmitter_number="MM123456",
        transmitter_name="Test Corp",
        transmitter_contact_name="Jane Smith",
        transmitter_contact_phone="4165551234",
        transmitter_contact_email="payroll@testcorp.com"
    )

    assert xml_string is not None
    assert "<?xml" in xml_string
    assert "<Return" in xml_string
    assert "<T4>" in xml_string
    assert sample_t4_slip.sin in xml_string


def test_sin_validation():
    """Test SIN Luhn algorithm validation"""
    # Valid SIN
    valid_sin = "046454286"
    slip = T4SlipData(
        employee_id="emp_001",
        tax_year=2025,
        sin=valid_sin,
        employee_name="Test",
        employee_address_line1="123 St",
        employee_city="City",
        employee_province="ON",
        employee_postal_code="M5H2N2",
        employer_name="Test",
        employer_account_number="123456789RP0001",
        province_of_employment="ON"
    )
    assert slip.sin == valid_sin

    # Invalid SIN (bad checksum)
    with pytest.raises(ValueError, match="Invalid SIN checksum"):
        T4SlipData(
            employee_id="emp_001",
            tax_year=2025,
            sin="046454287",  # Wrong checksum
            employee_name="Test",
            employee_address_line1="123 St",
            employee_city="City",
            employee_province="ON",
            employee_postal_code="M5H2N2",
            employer_name="Test",
            employer_account_number="123456789RP0001",
            province_of_employment="ON"
        )
```

---

## 8. Implementation Checklist

### Phase 6: Year-End Processing (Week 9-10)

- [ ] **Data Models**
  - [ ] Implement `T4SlipData` with all required boxes
  - [ ] Implement `T4Summary` with validation
  - [ ] Add SIN Luhn algorithm validation
  - [ ] Test data model validation

- [ ] **T4 Aggregation Service**
  - [ ] Implement `T4AggregationService.aggregate_employee_year()`
  - [ ] Implement `T4AggregationService.generate_all_t4_slips()`
  - [ ] Implement `T4AggregationService.generate_t4_summary()`
  - [ ] Test aggregation with sample payroll data

- [ ] **PDF Generation**
  - [ ] Implement `T4PDFGenerator.generate_t4_slip_pdf()`
  - [ ] Implement `T4PDFGenerator.generate_t4_summary_pdf()`
  - [ ] Test PDF layout and readability
  - [ ] Validate against official CRA T4 format

- [ ] **XML Generation**
  - [ ] Implement `T4XMLGenerator.generate_xml()`
  - [ ] Validate XML against CRA T619 schema
  - [ ] Test XML with CRA validation tool
  - [ ] Handle optional boxes correctly

- [ ] **Storage Service**
  - [ ] Implement `T4StorageService.upload_t4_slip()`
  - [ ] Implement `T4StorageService.upload_t4_summary()`
  - [ ] Implement `T4StorageService.upload_t4_xml()`
  - [ ] Test Google Drive folder structure

- [ ] **API Endpoints**
  - [ ] Implement `/generate-t4-slips` endpoint
  - [ ] Implement `/generate-t4-summary` endpoint
  - [ ] Implement `/t4-slips` listing endpoint
  - [ ] Add authorization checks
  - [ ] Test end-to-end workflow

- [ ] **Testing**
  - [ ] Write unit tests for all services
  - [ ] Write integration tests for API endpoints
  - [ ] Manual testing with real payroll data
  - [ ] Validate T4 amounts against CRA PDOC

- [ ] **Documentation**
  - [ ] Document T4 generation workflow
  - [ ] Create user guide for year-end processing
  - [ ] Document CRA submission process
  - [ ] Add troubleshooting guide

---

## 9. Important Notes

### 9.1 Deadlines and Penalties

- **Employee Distribution Deadline**: Last day of February following tax year
- **CRA Filing Deadline**: Last day of February following tax year
- **Late Filing Penalty**: $10/slip (small employer) to $100/slip (large employer)
- **Failure to File Penalty**: 10% of deductions owing + 2% per month (max 20 months)

### 9.2 Common Issues

1. **Incorrect CPP/EI Maximums**: Ensure annual maximums are correctly applied across all pay periods
2. **Box 22 Calculation**: Must include both federal AND provincial tax
3. **SIN Validation**: Always validate SIN using Luhn algorithm before submission
4. **Province of Employment**: Must match where employee physically worked, not where company is located

### 9.3 CRA Resources

- **T4 Guide (RC4120)**: https://www.canada.ca/en/revenue-agency/services/forms-publications/publications/rc4120.html
- **Internet File Transfer**: https://www.canada.ca/en/revenue-agency/services/e-services/e-services-businesses/internet-file-transfer.html
- **My Business Account**: https://www.canada.ca/en/revenue-agency/services/e-services/e-services-businesses/business-account.html
- **XML Schema Validator**: Available in CRA Internet File Transfer portal

---

## 10. CRA Electronic Submission Details

> **Note**: For comprehensive submission documentation, see [16_government_electronic_submission.md](./16_government_electronic_submission.md)

### 10.1 Electronic Filing Methods

CRA provides three methods for T4 electronic submission:

| Method | Description | Best For |
|--------|-------------|----------|
| **Internet File Transfer** | Upload XML file via web portal | > 5 slips (required) |
| **Web Forms** | Manual entry via CRA portal | ≤ 5 slips |
| **My Business Account** | Upload XML via business account | All employers |

### 10.2 T619 XML Schema (2025 Updates)

**Schema Version**: xmlschm1-25-4 (December 2024)

**Key 2025 Changes**:
1. **Single return type per submission**: Each submission can only contain one type (e.g., only T4)
2. **Updated T619 Electronic Transmittal record**: New format required starting January 2025
3. **File structure changes**: `layout-topologies.xsd` replaced by `T619_<FormType>.xsd` files

**Download**: https://www.canada.ca/en/revenue-agency/services/e-services/filing-information-returns-electronically-t4-t5-other-types-returns-overview/filing-information-returns-electronically-t4-t5-other-types-returns-file/filing-internet-file-transfer/download-xml-schema.html

### 10.3 Electronic Filing Threshold (2024+)

| Slips Filed | Requirement |
|-------------|-------------|
| **> 5 slips** | **Must** file electronically |
| **≤ 5 slips** | Paper or electronic (optional) |

### 10.4 Submission Process Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Generate T4     │     │ Validate XML    │     │ CRA Internet    │
│ Data + XML      │ ──► │ against T619    │ ──► │ File Transfer   │
│ (Beanflow)      │     │ Schema          │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │ Confirmation    │
                                                │ Number          │
                                                └─────────────────┘
```

### 10.5 Web Access Code (WAC)

**Purpose**: Required for automated submission by payroll software

**How commercial software achieves "automatic" T4 submission**:
1. User provides CRA credentials/WAC during setup
2. Software generates T619-compliant XML
3. Software submits on behalf of user
4. Returns confirmation to user

**Beanflow Implementation Phases**:
- **Phase 1 (MVP)**: Generate XML, user manually uploads
- **Phase 2**: Validate + deep links to CRA portal
- **Phase 3 (Enterprise)**: Store WAC, automatic submission

### 10.6 System Maintenance Windows

- **December 22, 2025**: Electronic filing unavailable
- **January 12, 2026**: System reopens with 2026 schema

---

**Document Version**: 1.1
**Created**: 2025-10-09
**Updated**: 2025-12-31
**For**: Beanflow-Payroll System - Phase 6 Implementation
