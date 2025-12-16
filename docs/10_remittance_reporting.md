# Phase 7: Remittance Reporting and CRA Submission

## Overview

Payroll remittance is the process of **sending deducted CPP, EI, and income tax to the Canada Revenue Agency (CRA)**. This is a **legally required compliance task** with strict deadlines and penalties for late or incorrect remittances.

### Legal Requirements

- **Remittance Deadline**: 15th day of the month following payment (or next business day if 15th falls on weekend/holiday)
- **Remittance Types**: Regular, Quarterly, Accelerated Threshold 1, Accelerated Threshold 2
- **Required Forms**: PD7A Remittance Voucher (for manual payments)
- **Electronic Submission**: My Payment (online), Pre-Authorized Debit, Wire Transfer
- **Penalties**:
  - 3% if 1-3 days late
  - 5% if 4-5 days late
  - 7% if 6-7 days late
  - 10% if 8+ days late or not paid at all
  - Additional 20% for repeated failures

### Official References

- **CRA T4001**: Employers' Guide - Payroll Deductions and Remittances
- **Guide**: https://www.canada.ca/en/revenue-agency/services/forms-publications/publications/t4001.html
- **PD7A Form**: https://www.canada.ca/en/revenue-agency/services/forms-publications/forms/pd7a.html
- **My Business Account**: https://www.canada.ca/en/revenue-agency/services/e-services/e-services-businesses/business-account.html

---

## 1. Remitter Type Determination

### 1.1 Four Remitter Types

The CRA assigns remitter types based on the **Average Monthly Withholding Amount (AMWA)** from **two calendar years ago**.

| Remitter Type | AMWA Range | Remittance Frequency | Due Date |
|---------------|------------|---------------------|----------|
| **Regular** | < $25,000 | Monthly | 15th of following month |
| **Quarterly** | < $3,000 | Quarterly (Jan-Mar, Apr-Jun, Jul-Sep, Oct-Dec) | 15th of month after quarter end |
| **Accelerated Threshold 1** | $25,000 - $99,999.99 | Twice monthly | 25th for 1st-15th, 10th for 16th-31st |
| **Accelerated Threshold 2** | ≥ $100,000 | Four times monthly (with withholding timing) | Day 1, 4, 11, 20 of following month |

### 1.2 Data Model for Remitter Type

```python
from enum import Enum
from decimal import Decimal
from datetime import date
from pydantic import BaseModel, Field

class RemitterType(str, Enum):
    """
    CRA Remitter Types

    Reference: CRA T4001 Chapter 8
    """
    QUARTERLY = "quarterly"
    REGULAR = "regular"
    THRESHOLD_1 = "accelerated_threshold_1"
    THRESHOLD_2 = "accelerated_threshold_2"


class RemitterClassification(BaseModel):
    """
    Remitter classification for a ledger
    """
    ledger_id: str
    effective_year: int  # Year this classification applies to
    classification_based_on_year: int  # AMWA calculated from this year (usually effective_year - 2)

    average_monthly_withholding_amount: Decimal = Field(
        ...,
        description="AMWA calculated from two years ago"
    )

    remitter_type: RemitterType

    @classmethod
    def determine_remitter_type(cls, amwa: Decimal) -> RemitterType:
        """
        Determine remitter type based on AMWA

        Args:
            amwa: Average Monthly Withholding Amount from two years ago

        Returns:
            RemitterType
        """
        if amwa < Decimal("3000"):
            return RemitterType.QUARTERLY
        elif amwa < Decimal("25000"):
            return RemitterType.REGULAR
        elif amwa < Decimal("100000"):
            return RemitterType.THRESHOLD_1
        else:
            return RemitterType.THRESHOLD_2

    class Config:
        json_schema_extra = {
            "example": {
                "ledger_id": "ledger_12345",
                "effective_year": 2025,
                "classification_based_on_year": 2023,
                "average_monthly_withholding_amount": "45000.00",
                "remitter_type": "accelerated_threshold_1"
            }
        }
```

### 1.3 AMWA Calculation Service

```python
from typing import List
from decimal import Decimal
from datetime import date

class AMWACalculationService:
    """
    Calculate Average Monthly Withholding Amount (AMWA) for remitter classification
    """

    def __init__(self, firestore_service):
        self.firestore = firestore_service

    async def calculate_amwa(
        self,
        ledger_id: str,
        year: int
    ) -> Decimal:
        """
        Calculate AMWA for a given year

        AMWA = Total deductions for the year / 12 months

        Total deductions = Employee CPP + Employer CPP + Employee EI + Employer EI + Federal Tax + Provincial Tax

        Args:
            ledger_id: Ledger identifier
            year: Calendar year

        Returns:
            AMWA (Average Monthly Withholding Amount)
        """
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)

        # Fetch all payroll records for the year
        payroll_records = await self.firestore.get_payroll_records(
            ledger_id=ledger_id,
            start_date=start_date,
            end_date=end_date
        )

        total_deductions = Decimal("0")

        for record in payroll_records:
            # Employee portions
            employee_cpp = record.cpp_employee
            employee_ei = record.ei_employee
            federal_tax = record.federal_tax
            provincial_tax = record.provincial_tax

            # Employer portions
            employer_cpp = record.cpp_employee  # Employer pays same as employee
            employer_ei = record.ei_employee * Decimal("1.4")  # Employer pays 1.4x employee

            total_deductions += (
                employee_cpp + employer_cpp +
                employee_ei + employer_ei +
                federal_tax + provincial_tax
            )

        # AMWA = Total / 12 months
        amwa = total_deductions / Decimal("12")

        return amwa.quantize(Decimal("0.01"))

    async def determine_remitter_classification(
        self,
        ledger_id: str,
        effective_year: int
    ) -> RemitterClassification:
        """
        Determine remitter classification for a given year

        Uses AMWA from two calendar years ago

        Args:
            ledger_id: Ledger identifier
            effective_year: Year the classification applies to (e.g., 2025)

        Returns:
            RemitterClassification
        """
        classification_year = effective_year - 2

        # Calculate AMWA from two years ago
        amwa = await self.calculate_amwa(ledger_id, classification_year)

        # Determine remitter type
        remitter_type = RemitterClassification.determine_remitter_type(amwa)

        return RemitterClassification(
            ledger_id=ledger_id,
            effective_year=effective_year,
            classification_based_on_year=classification_year,
            average_monthly_withholding_amount=amwa,
            remitter_type=remitter_type
        )
```

---

## 2. Remittance Calculation

### 2.1 Remittance Data Model

```python
from datetime import date, datetime
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field

class RemittancePeriod(BaseModel):
    """
    Represents a remittance period (monthly, quarterly, or accelerated)
    """
    ledger_id: str
    remitter_type: RemitterType

    period_start_date: date
    period_end_date: date
    due_date: date

    # Employee deductions
    total_cpp_employee: Decimal = Field(default=Decimal("0"), decimal_places=2)
    total_ei_employee: Decimal = Field(default=Decimal("0"), decimal_places=2)
    total_federal_tax: Decimal = Field(default=Decimal("0"), decimal_places=2)
    total_provincial_tax: Decimal = Field(default=Decimal("0"), decimal_places=2)

    # Employer portions
    total_cpp_employer: Decimal = Field(default=Decimal("0"), decimal_places=2)
    total_ei_employer: Decimal = Field(default=Decimal("0"), decimal_places=2)

    # Total remittance
    total_remittance: Decimal = Field(default=Decimal("0"), decimal_places=2)

    # Payment tracking
    paid: bool = False
    payment_date: Optional[date] = None
    payment_method: Optional[str] = None  # "my_payment", "pre_authorized_debit", "wire_transfer", "cheque"
    payment_confirmation_number: Optional[str] = None

    @property
    def is_overdue(self) -> bool:
        """Check if remittance is overdue"""
        if self.paid:
            return False
        return date.today() > self.due_date

    @property
    def days_overdue(self) -> int:
        """Calculate days overdue"""
        if not self.is_overdue:
            return 0
        return (date.today() - self.due_date).days

    @property
    def late_penalty_rate(self) -> Decimal:
        """
        Calculate late penalty rate based on days overdue

        Reference: CRA T4001 Chapter 8
        """
        days = self.days_overdue

        if days == 0:
            return Decimal("0")
        elif days <= 3:
            return Decimal("0.03")  # 3%
        elif days <= 5:
            return Decimal("0.05")  # 5%
        elif days <= 7:
            return Decimal("0.07")  # 7%
        else:
            return Decimal("0.10")  # 10%

    @property
    def late_penalty_amount(self) -> Decimal:
        """Calculate late penalty amount"""
        return (self.total_remittance * self.late_penalty_rate).quantize(Decimal("0.01"))

    class Config:
        json_schema_extra = {
            "example": {
                "ledger_id": "ledger_12345",
                "remitter_type": "regular",
                "period_start_date": "2025-01-01",
                "period_end_date": "2025-01-31",
                "due_date": "2025-02-15",
                "total_cpp_employee": "1500.00",
                "total_ei_employee": "400.00",
                "total_federal_tax": "3000.00",
                "total_provincial_tax": "1200.00",
                "total_cpp_employer": "1500.00",
                "total_ei_employer": "560.00",
                "total_remittance": "8160.00",
                "paid": False
            }
        }
```

### 2.2 Remittance Calculation Service

```python
from typing import List
from datetime import date, timedelta
from decimal import Decimal
import calendar

class RemittanceCalculationService:
    """
    Calculate remittance amounts for different remitter types
    """

    def __init__(self, firestore_service):
        self.firestore = firestore_service

    async def calculate_remittance_period(
        self,
        ledger_id: str,
        remitter_type: RemitterType,
        period_start_date: date,
        period_end_date: date
    ) -> RemittancePeriod:
        """
        Calculate remittance for a specific period

        Args:
            ledger_id: Ledger identifier
            remitter_type: Remitter type
            period_start_date: Start of remittance period
            period_end_date: End of remittance period

        Returns:
            RemittancePeriod with calculated amounts
        """
        # Fetch all payroll records in the period
        payroll_records = await self.firestore.get_payroll_records(
            ledger_id=ledger_id,
            start_date=period_start_date,
            end_date=period_end_date
        )

        # Aggregate deductions
        total_cpp_employee = Decimal("0")
        total_ei_employee = Decimal("0")
        total_federal_tax = Decimal("0")
        total_provincial_tax = Decimal("0")

        for record in payroll_records:
            total_cpp_employee += record.cpp_employee
            total_ei_employee += record.ei_employee
            total_federal_tax += record.federal_tax
            total_provincial_tax += record.provincial_tax

        # Calculate employer portions
        total_cpp_employer = total_cpp_employee  # Employer matches employee
        total_ei_employer = (total_ei_employee * Decimal("1.4")).quantize(Decimal("0.01"))

        # Total remittance
        total_remittance = (
            total_cpp_employee + total_cpp_employer +
            total_ei_employee + total_ei_employer +
            total_federal_tax + total_provincial_tax
        )

        # Calculate due date
        due_date = self._calculate_due_date(remitter_type, period_end_date)

        return RemittancePeriod(
            ledger_id=ledger_id,
            remitter_type=remitter_type,
            period_start_date=period_start_date,
            period_end_date=period_end_date,
            due_date=due_date,
            total_cpp_employee=total_cpp_employee,
            total_ei_employee=total_ei_employee,
            total_federal_tax=total_federal_tax,
            total_provincial_tax=total_provincial_tax,
            total_cpp_employer=total_cpp_employer,
            total_ei_employer=total_ei_employer,
            total_remittance=total_remittance
        )

    def _calculate_due_date(self, remitter_type: RemitterType, period_end_date: date) -> date:
        """
        Calculate remittance due date based on remitter type

        Args:
            remitter_type: Remitter type
            period_end_date: End of remittance period

        Returns:
            Due date
        """
        if remitter_type == RemitterType.REGULAR:
            # Regular: 15th of following month
            if period_end_date.month == 12:
                due_month = 1
                due_year = period_end_date.year + 1
            else:
                due_month = period_end_date.month + 1
                due_year = period_end_date.year

            due_date = date(due_year, due_month, 15)

        elif remitter_type == RemitterType.QUARTERLY:
            # Quarterly: 15th of month after quarter end
            quarter_end_month = period_end_date.month
            if quarter_end_month in [3, 6, 9, 12]:
                if quarter_end_month == 12:
                    due_month = 1
                    due_year = period_end_date.year + 1
                else:
                    due_month = quarter_end_month + 1
                    due_year = period_end_date.year
            else:
                raise ValueError(f"Invalid quarter end month: {quarter_end_month}")

            due_date = date(due_year, due_month, 15)

        elif remitter_type == RemitterType.THRESHOLD_1:
            # Accelerated Threshold 1
            # For 1st-15th: due 25th of same month
            # For 16th-last day: due 10th of following month
            if period_end_date.day == 15:
                due_date = date(period_end_date.year, period_end_date.month, 25)
            else:
                # Last day of month
                if period_end_date.month == 12:
                    due_month = 1
                    due_year = period_end_date.year + 1
                else:
                    due_month = period_end_date.month + 1
                    due_year = period_end_date.year
                due_date = date(due_year, due_month, 10)

        elif remitter_type == RemitterType.THRESHOLD_2:
            # Accelerated Threshold 2 (complex - based on withholding dates)
            # For simplicity, use next month 1st, 4th, 11th, 20th
            # Actual implementation should track withholding dates
            if period_end_date.month == 12:
                due_month = 1
                due_year = period_end_date.year + 1
            else:
                due_month = period_end_date.month + 1
                due_year = period_end_date.year

            # Use 1st as default (adjust based on actual withholding schedule)
            due_date = date(due_year, due_month, 1)

        else:
            raise ValueError(f"Unknown remitter type: {remitter_type}")

        # Adjust if due date falls on weekend or holiday
        due_date = self._adjust_for_business_day(due_date)

        return due_date

    def _adjust_for_business_day(self, target_date: date) -> date:
        """
        Adjust date to next business day if it falls on weekend

        Note: Does not account for statutory holidays (would require holiday calendar)
        """
        if target_date.weekday() == 5:  # Saturday
            return target_date + timedelta(days=2)
        elif target_date.weekday() == 6:  # Sunday
            return target_date + timedelta(days=1)
        return target_date

    async def generate_remittance_schedule(
        self,
        ledger_id: str,
        remitter_type: RemitterType,
        year: int
    ) -> List[RemittancePeriod]:
        """
        Generate remittance schedule for the entire year

        Args:
            ledger_id: Ledger identifier
            remitter_type: Remitter type
            year: Calendar year

        Returns:
            List of RemittancePeriod
        """
        remittances = []

        if remitter_type == RemitterType.QUARTERLY:
            # Quarterly periods
            quarters = [
                (date(year, 1, 1), date(year, 3, 31)),
                (date(year, 4, 1), date(year, 6, 30)),
                (date(year, 7, 1), date(year, 9, 30)),
                (date(year, 10, 1), date(year, 12, 31))
            ]
            for start, end in quarters:
                remittance = await self.calculate_remittance_period(
                    ledger_id, remitter_type, start, end
                )
                remittances.append(remittance)

        elif remitter_type == RemitterType.REGULAR:
            # Monthly periods
            for month in range(1, 13):
                start = date(year, month, 1)
                last_day = calendar.monthrange(year, month)[1]
                end = date(year, month, last_day)

                remittance = await self.calculate_remittance_period(
                    ledger_id, remitter_type, start, end
                )
                remittances.append(remittance)

        elif remitter_type == RemitterType.THRESHOLD_1:
            # Twice monthly periods
            for month in range(1, 13):
                # First half (1st-15th)
                start1 = date(year, month, 1)
                end1 = date(year, month, 15)
                remittance1 = await self.calculate_remittance_period(
                    ledger_id, remitter_type, start1, end1
                )
                remittances.append(remittance1)

                # Second half (16th-last day)
                start2 = date(year, month, 16)
                last_day = calendar.monthrange(year, month)[1]
                end2 = date(year, month, last_day)
                remittance2 = await self.calculate_remittance_period(
                    ledger_id, remitter_type, start2, end2
                )
                remittances.append(remittance2)

        elif remitter_type == RemitterType.THRESHOLD_2:
            # Accelerated Threshold 2 (based on withholding dates)
            # Simplified: treat as weekly periods
            # Actual implementation should track withholding timing
            current_date = date(year, 1, 1)
            end_date = date(year, 12, 31)

            while current_date <= end_date:
                period_end = min(current_date + timedelta(days=6), end_date)
                remittance = await self.calculate_remittance_period(
                    ledger_id, remitter_type, current_date, period_end
                )
                remittances.append(remittance)
                current_date = period_end + timedelta(days=1)

        return remittances
```

---

## 3. PD7A Remittance Voucher Generation

### 3.1 PD7A Data Model

```python
from pydantic import BaseModel, Field
from datetime import date
from decimal import Decimal

class PD7ARemittanceVoucher(BaseModel):
    """
    PD7A Statement of Account for Current Source Deductions

    Used for manual remittance payments (cheque, in-person)
    """
    # Employer Information
    employer_name: str
    payroll_account_number: str = Field(..., regex=r"^\d{9}RP\d{4}$")

    # Remittance Period
    period_start_date: date
    period_end_date: date
    due_date: date

    # Line 10: Current Source Deductions
    line_10_cpp_employee: Decimal = Field(default=Decimal("0"), decimal_places=2)
    line_10_cpp_employer: Decimal = Field(default=Decimal("0"), decimal_places=2)
    line_10_ei_employee: Decimal = Field(default=Decimal("0"), decimal_places=2)
    line_10_ei_employer: Decimal = Field(default=Decimal("0"), decimal_places=2)
    line_10_income_tax: Decimal = Field(default=Decimal("0"), decimal_places=2)

    # Line 11: Total Current Source Deductions
    @property
    def line_11_total_deductions(self) -> Decimal:
        return (
            self.line_10_cpp_employee +
            self.line_10_cpp_employer +
            self.line_10_ei_employee +
            self.line_10_ei_employer +
            self.line_10_income_tax
        ).quantize(Decimal("0.01"))

    # Line 12: Previous balance owing (if any)
    line_12_previous_balance: Decimal = Field(default=Decimal("0"), decimal_places=2)

    # Line 13: Total amount due
    @property
    def line_13_total_due(self) -> Decimal:
        return (self.line_11_total_deductions + self.line_12_previous_balance).quantize(Decimal("0.01"))

    class Config:
        json_schema_extra = {
            "example": {
                "employer_name": "Example Corp",
                "payroll_account_number": "123456789RP0001",
                "period_start_date": "2025-01-01",
                "period_end_date": "2025-01-31",
                "due_date": "2025-02-15",
                "line_10_cpp_employee": "1500.00",
                "line_10_cpp_employer": "1500.00",
                "line_10_ei_employee": "400.00",
                "line_10_ei_employer": "560.00",
                "line_10_income_tax": "4200.00"
            }
        }
```

### 3.2 PD7A PDF Generation

```python
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO

class PD7APDFGenerator:
    """
    Generate PD7A Remittance Voucher PDF
    """

    def __init__(self):
        self.styles = getSampleStyleSheet()

    def generate_pd7a_pdf(self, voucher: PD7ARemittanceVoucher) -> bytes:
        """
        Generate PD7A PDF

        Args:
            voucher: PD7ARemittanceVoucher data

        Returns:
            PDF bytes
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            rightMargin=0.75 * inch
        )

        story = []

        # Title
        title = Paragraph(
            "PD7A - Statement of Account for Current Source Deductions",
            self.styles['Title']
        )
        story.append(title)
        story.append(Spacer(1, 12))

        # Employer Information
        employer_data = [
            ['Employer Name:', voucher.employer_name],
            ['Payroll Account Number:', voucher.payroll_account_number]
        ]
        employer_table = Table(employer_data, colWidths=[2.5 * inch, 4 * inch])
        employer_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0)
        ]))
        story.append(employer_table)
        story.append(Spacer(1, 18))

        # Remittance Period
        period_data = [
            ['Remittance Period:', f"{voucher.period_start_date.strftime('%B %d, %Y')} to {voucher.period_end_date.strftime('%B %d, %Y')}"],
            ['Due Date:', voucher.due_date.strftime('%B %d, %Y')]
        ]
        period_table = Table(period_data, colWidths=[2.5 * inch, 4 * inch])
        period_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0)
        ]))
        story.append(period_table)
        story.append(Spacer(1, 24))

        # Line 10: Current Source Deductions
        deductions_data = [
            ['Line 10: Current Source Deductions', ''],
            ['CPP - Employee Contributions', f"${voucher.line_10_cpp_employee:,.2f}"],
            ['CPP - Employer Contributions', f"${voucher.line_10_cpp_employer:,.2f}"],
            ['EI - Employee Premiums', f"${voucher.line_10_ei_employee:,.2f}"],
            ['EI - Employer Premiums', f"${voucher.line_10_ei_employer:,.2f}"],
            ['Income Tax (Federal + Provincial)', f"${voucher.line_10_income_tax:,.2f}"]
        ]

        deductions_table = Table(deductions_data, colWidths=[4.5 * inch, 2 * inch])
        deductions_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#333333')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6)
        ]))
        story.append(deductions_table)
        story.append(Spacer(1, 12))

        # Line 11: Total
        total_data = [
            ['Line 11: Total Current Source Deductions', f"${voucher.line_11_total_deductions:,.2f}"]
        ]
        total_table = Table(total_data, colWidths=[4.5 * inch, 2 * inch])
        total_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f0f0')),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8)
        ]))
        story.append(total_table)
        story.append(Spacer(1, 18))

        # Line 12 & 13 (if previous balance exists)
        if voucher.line_12_previous_balance > Decimal("0"):
            balance_data = [
                ['Line 12: Previous Balance Owing', f"${voucher.line_12_previous_balance:,.2f}"],
                ['Line 13: Total Amount Due', f"${voucher.line_13_total_due:,.2f}"]
            ]
            balance_table = Table(balance_data, colWidths=[4.5 * inch, 2 * inch])
            balance_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica'),
                ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#ffcccc')),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6)
            ]))
            story.append(balance_table)

        story.append(Spacer(1, 36))

        # Payment Instructions
        instructions = Paragraph(
            "<b>Payment Instructions:</b><br/><br/>"
            "1. Pay online through CRA My Business Account (recommended)<br/>"
            "2. Pre-authorized debit through CRA<br/>"
            "3. Wire transfer to CRA account<br/>"
            "4. Mail cheque with this voucher to:<br/>"
            "&nbsp;&nbsp;&nbsp;&nbsp;Sudbury Tax Centre<br/>"
            "&nbsp;&nbsp;&nbsp;&nbsp;1050 Notre Dame Avenue<br/>"
            "&nbsp;&nbsp;&nbsp;&nbsp;Sudbury ON P3A 5C1",
            self.styles['Normal']
        )
        story.append(instructions)

        # Build PDF
        doc.build(story)

        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes
```

---

## 4. Beancount Integration for Remittance Tracking

### 4.1 Remittance Liability Accounts

```python
class BeancountRemittanceService:
    """
    Track remittance liabilities and payments in Beancount
    """

    def __init__(self, beancount_service):
        self.beancount = beancount_service

    async def record_remittance_liability(
        self,
        ledger_id: str,
        remittance: RemittancePeriod
    ) -> str:
        """
        Record remittance liability in Beancount

        This entry is created at period end to track what is owed to CRA

        Args:
            ledger_id: Ledger identifier
            remittance: RemittancePeriod data

        Returns:
            Beancount transaction ID
        """
        transaction_date = remittance.period_end_date
        description = f"Remittance Liability - {remittance.period_start_date.strftime('%b %d')} to {remittance.period_end_date.strftime('%b %d, %Y')}"

        # Build Beancount entry
        entry_lines = [
            f"{transaction_date} * \"Payroll\" \"{description}\"",
        ]

        # Debit: Payroll Tax Expense (employer portions already expensed during payroll)
        # This entry is just to consolidate liabilities

        # Credit: CPP Remittance Liability
        total_cpp = remittance.total_cpp_employee + remittance.total_cpp_employer
        if total_cpp > Decimal("0"):
            entry_lines.append(f"  Liabilities:Payroll:CPP-Remittance  {total_cpp:.2f} CAD")

        # Credit: EI Remittance Liability
        total_ei = remittance.total_ei_employee + remittance.total_ei_employer
        if total_ei > Decimal("0"):
            entry_lines.append(f"  Liabilities:Payroll:EI-Remittance  {total_ei:.2f} CAD")

        # Credit: Tax Remittance Liability
        total_tax = remittance.total_federal_tax + remittance.total_provincial_tax
        if total_tax > Decimal("0"):
            entry_lines.append(f"  Liabilities:Payroll:Tax-Remittance  {total_tax:.2f} CAD")

        # This is a liability-only entry (no asset/expense change)
        # The actual expenses were recorded during individual payroll entries
        # This entry just consolidates the liability for remittance tracking

        entry_text = "\n".join(entry_lines)

        # Append to ledger file
        transaction_id = await self.beancount.append_transaction(ledger_id, entry_text)

        return transaction_id

    async def record_remittance_payment(
        self,
        ledger_id: str,
        remittance: RemittancePeriod,
        payment_date: date,
        payment_method: str
    ) -> str:
        """
        Record remittance payment in Beancount

        Args:
            ledger_id: Ledger identifier
            remittance: RemittancePeriod data
            payment_date: Date payment was made
            payment_method: Payment method

        Returns:
            Beancount transaction ID
        """
        description = f"Remittance Payment - {remittance.period_start_date.strftime('%b %Y')} via {payment_method}"

        entry_lines = [
            f"{payment_date} * \"CRA Remittance\" \"{description}\"",
        ]

        # Debit: Clear liability accounts
        total_cpp = remittance.total_cpp_employee + remittance.total_cpp_employer
        if total_cpp > Decimal("0"):
            entry_lines.append(f"  Liabilities:Payroll:CPP-Remittance  -{total_cpp:.2f} CAD")

        total_ei = remittance.total_ei_employee + remittance.total_ei_employer
        if total_ei > Decimal("0"):
            entry_lines.append(f"  Liabilities:Payroll:EI-Remittance  -{total_ei:.2f} CAD")

        total_tax = remittance.total_federal_tax + remittance.total_provincial_tax
        if total_tax > Decimal("0"):
            entry_lines.append(f"  Liabilities:Payroll:Tax-Remittance  -{total_tax:.2f} CAD")

        # Credit: Bank account
        total_payment = remittance.total_remittance
        entry_lines.append(f"  Assets:Bank:Chequing  -{total_payment:.2f} CAD")

        entry_text = "\n".join(entry_lines)

        transaction_id = await self.beancount.append_transaction(ledger_id, entry_text)

        return transaction_id
```

---

## 5. API Endpoints

### 5.1 FastAPI Routes

```python
from fastapi import APIRouter, Depends, HTTPException
from typing import List

router = APIRouter(prefix="/api/v1/remittance", tags=["remittance"])

@router.get("/classification/{ledger_id}/{year}")
async def get_remitter_classification(
    ledger_id: str,
    year: int,
    current_user=Depends(get_current_user),
    firestore_service=Depends(get_firestore_service)
):
    """
    Get remitter classification for a given year

    Uses AMWA from two years ago to determine remitter type
    """
    if not await check_ledger_access(current_user.uid, ledger_id):
        raise HTTPException(status_code=403, detail="Access denied")

    amwa_service = AMWACalculationService(firestore_service)
    classification = await amwa_service.determine_remitter_classification(ledger_id, year)

    return classification.dict()


@router.get("/schedule/{ledger_id}/{year}")
async def get_remittance_schedule(
    ledger_id: str,
    year: int,
    current_user=Depends(get_current_user),
    firestore_service=Depends(get_firestore_service)
):
    """
    Generate remittance schedule for the entire year
    """
    if not await check_ledger_access(current_user.uid, ledger_id):
        raise HTTPException(status_code=403, detail="Access denied")

    # Get remitter classification
    amwa_service = AMWACalculationService(firestore_service)
    classification = await amwa_service.determine_remitter_classification(ledger_id, year)

    # Generate schedule
    calc_service = RemittanceCalculationService(firestore_service)
    schedule = await calc_service.generate_remittance_schedule(
        ledger_id=ledger_id,
        remitter_type=classification.remitter_type,
        year=year
    )

    return {
        "year": year,
        "remitter_type": classification.remitter_type,
        "schedule": [r.dict() for r in schedule]
    }


@router.post("/generate-pd7a/{ledger_id}")
async def generate_pd7a_voucher(
    ledger_id: str,
    period_start_date: date,
    period_end_date: date,
    current_user=Depends(get_current_user),
    firestore_service=Depends(get_firestore_service)
):
    """
    Generate PD7A remittance voucher PDF
    """
    if not await check_ledger_access(current_user.uid, ledger_id):
        raise HTTPException(status_code=403, detail="Access denied")

    # Calculate remittance
    amwa_service = AMWACalculationService(firestore_service)
    classification = await amwa_service.determine_remitter_classification(ledger_id, period_start_date.year)

    calc_service = RemittanceCalculationService(firestore_service)
    remittance = await calc_service.calculate_remittance_period(
        ledger_id=ledger_id,
        remitter_type=classification.remitter_type,
        period_start_date=period_start_date,
        period_end_date=period_end_date
    )

    # Build PD7A voucher
    employer = await firestore_service.get_employer_info(ledger_id)
    voucher = PD7ARemittanceVoucher(
        employer_name=employer.legal_name,
        payroll_account_number=employer.cra_payroll_account,
        period_start_date=remittance.period_start_date,
        period_end_date=remittance.period_end_date,
        due_date=remittance.due_date,
        line_10_cpp_employee=remittance.total_cpp_employee,
        line_10_cpp_employer=remittance.total_cpp_employer,
        line_10_ei_employee=remittance.total_ei_employee,
        line_10_ei_employer=remittance.total_ei_employer,
        line_10_income_tax=remittance.total_federal_tax + remittance.total_provincial_tax
    )

    # Generate PDF
    pdf_generator = PD7APDFGenerator()
    pdf_bytes = pdf_generator.generate_pd7a_pdf(voucher)

    # Return PDF as response
    from fastapi.responses import Response
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=PD7A_{period_start_date}_{period_end_date}.pdf"}
    )


@router.post("/record-payment/{ledger_id}/{remittance_id}")
async def record_remittance_payment(
    ledger_id: str,
    remittance_id: str,
    payment_date: date,
    payment_method: str,
    confirmation_number: Optional[str] = None,
    current_user=Depends(get_current_user),
    firestore_service=Depends(get_firestore_service)
):
    """
    Record remittance payment

    Updates remittance record and creates Beancount entry
    """
    if not await check_ledger_access(current_user.uid, ledger_id):
        raise HTTPException(status_code=403, detail="Access denied")

    # Fetch remittance
    remittance = await firestore_service.get_remittance(ledger_id, remittance_id)
    if not remittance:
        raise HTTPException(status_code=404, detail="Remittance not found")

    # Update remittance record
    remittance.paid = True
    remittance.payment_date = payment_date
    remittance.payment_method = payment_method
    remittance.payment_confirmation_number = confirmation_number

    await firestore_service.update_remittance(ledger_id, remittance_id, remittance)

    # Record in Beancount
    beancount_service = BeancountRemittanceService(get_beancount_service())
    transaction_id = await beancount_service.record_remittance_payment(
        ledger_id=ledger_id,
        remittance=remittance,
        payment_date=payment_date,
        payment_method=payment_method
    )

    return {
        "message": "Payment recorded successfully",
        "remittance_id": remittance_id,
        "beancount_transaction_id": transaction_id
    }
```

---

## 6. Testing

```python
import pytest
from decimal import Decimal
from datetime import date

def test_remitter_classification():
    """Test remitter type determination"""
    assert RemitterClassification.determine_remitter_type(Decimal("2000")) == RemitterType.QUARTERLY
    assert RemitterClassification.determine_remitter_type(Decimal("10000")) == RemitterType.REGULAR
    assert RemitterClassification.determine_remitter_type(Decimal("50000")) == RemitterType.THRESHOLD_1
    assert RemitterClassification.determine_remitter_type(Decimal("150000")) == RemitterType.THRESHOLD_2


def test_late_penalty_calculation():
    """Test late penalty rates"""
    remittance = RemittancePeriod(
        ledger_id="test",
        remitter_type=RemitterType.REGULAR,
        period_start_date=date(2025, 1, 1),
        period_end_date=date(2025, 1, 31),
        due_date=date(2025, 2, 1),  # Overdue
        total_remittance=Decimal("10000.00")
    )

    # Mock today's date as 5 days late
    from unittest.mock import patch
    with patch('datetime.date') as mock_date:
        mock_date.today.return_value = date(2025, 2, 6)
        mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

        assert remittance.days_overdue == 5
        assert remittance.late_penalty_rate == Decimal("0.05")
        assert remittance.late_penalty_amount == Decimal("500.00")


def test_pd7a_voucher_totals():
    """Test PD7A total calculation"""
    voucher = PD7ARemittanceVoucher(
        employer_name="Test Corp",
        payroll_account_number="123456789RP0001",
        period_start_date=date(2025, 1, 1),
        period_end_date=date(2025, 1, 31),
        due_date=date(2025, 2, 15),
        line_10_cpp_employee=Decimal("1000.00"),
        line_10_cpp_employer=Decimal("1000.00"),
        line_10_ei_employee=Decimal("300.00"),
        line_10_ei_employer=Decimal("420.00"),
        line_10_income_tax=Decimal("3000.00")
    )

    assert voucher.line_11_total_deductions == Decimal("5720.00")
    assert voucher.line_13_total_due == Decimal("5720.00")

    # With previous balance
    voucher.line_12_previous_balance = Decimal("500.00")
    assert voucher.line_13_total_due == Decimal("6220.00")
```

---

## 7. Implementation Checklist

- [ ] **Remitter Classification**
  - [ ] Implement `AMWACalculationService`
  - [ ] Implement `RemitterClassification` model
  - [ ] Test AMWA calculation with sample data

- [ ] **Remittance Calculation**
  - [ ] Implement `RemittanceCalculationService`
  - [ ] Implement due date calculation for all remitter types
  - [ ] Test remittance schedule generation

- [ ] **PD7A Generation**
  - [ ] Implement `PD7ARemittanceVoucher` model
  - [ ] Implement `PD7APDFGenerator`
  - [ ] Test PDF generation

- [ ] **Beancount Integration**
  - [ ] Implement liability tracking
  - [ ] Implement payment recording
  - [ ] Test double-entry bookkeeping

- [ ] **API Endpoints**
  - [ ] Implement classification endpoint
  - [ ] Implement schedule endpoint
  - [ ] Implement PD7A generation endpoint
  - [ ] Implement payment recording endpoint

- [ ] **Testing**
  - [ ] Unit tests for all services
  - [ ] Integration tests for workflows
  - [ ] Manual testing with real data

---

**Document Version**: 1.0
**Created**: 2025-10-09
**For**: Beancount-LLM Canadian Payroll System - Phase 7 Implementation
