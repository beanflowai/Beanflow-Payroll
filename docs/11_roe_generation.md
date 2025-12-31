# Phase 7 (continued): Record of Employment (ROE) Generation

## Overview

The Record of Employment (ROE) is a **legally required document** that must be issued when an employee experiences an **interruption of earnings**. It is used by Service Canada to determine eligibility for Employment Insurance (EI) benefits.

### Legal Requirements

- **Mandatory Issuance**: ROE must be issued within **5 calendar days** of the first day of the interruption of earnings
- **Interruption of Earnings**: Occurs when employee stops receiving insurable earnings for 7+ consecutive days
- **Common Triggers**:
  - Termination of employment (voluntary or involuntary)
  - Temporary layoff
  - Illness or injury leave (7+ days unpaid)
  - Maternity/parental leave
  - Leave of absence without pay (7+ days)
- **Penalties**: Failure to issue ROE can result in penalties of $2,000 - $12,000

### Official References

- **Service Canada ROE Guide**: https://www.canada.ca/en/employment-social-development/programs/ei/ei-list/reports/roe-guide.html
- **ROE Web**: https://www.canada.ca/en/employment-social-development/programs/ei/ei-list/ei-roe/access-roe.html
- **ROE Reason Codes**: https://www.canada.ca/en/employment-social-development/programs/ei/ei-list/reports/roe-guide/understand.html#h2.02

---

## 1. Data Model

### 1.1 ROE Reason Codes

```python
from enum import Enum

class ROEReasonCode(str, Enum):
    """
    ROE Reason Codes for separation

    Reference: Service Canada ROE Guide Section 2
    """
    A_SHORTAGE_OF_WORK = "A"  # Shortage of work or end of contract/season
    B_STRIKE_OR_LOCKOUT = "B"  # Strike or lockout
    C_RETURN_TO_SCHOOL = "C"  # Return to school
    D_ILLNESS_OR_INJURY = "D"  # Illness or injury
    E_QUIT = "E"  # Quit
    F_MATERNITY = "F"  # Maternity
    G_RETIREMENT = "G"  # Retirement
    H_WORK_SHARING = "H"  # Work-sharing
    J_APPRENTICESHIP_TRAINING = "J"  # Apprenticeship training
    K_OTHER = "K"  # Other
    M_DISMISSAL = "M"  # Dismissal
    N_LEAVE_OF_ABSENCE = "N"  # Leave of absence
    P_PARENTAL = "P"  # Parental
    Z_COMMENT = "Z"  # Comment (requires explanation)

    @classmethod
    def requires_comment(cls, code: str) -> bool:
        """Check if reason code requires additional comment"""
        return code in ["E", "K", "M", "Z"]

    @classmethod
    def get_description(cls, code: str) -> str:
        """Get human-readable description of reason code"""
        descriptions = {
            "A": "Shortage of Work / End of Contract or Season",
            "B": "Strike or Lockout",
            "C": "Return to School",
            "D": "Illness or Injury",
            "E": "Quit (requires comment)",
            "F": "Maternity",
            "G": "Retirement",
            "H": "Work-Sharing",
            "J": "Apprenticeship Training",
            "K": "Other (requires comment)",
            "M": "Dismissal (requires comment)",
            "N": "Leave of Absence",
            "P": "Parental",
            "Z": "Comment Required"
        }
        return descriptions.get(code, "Unknown")
```

### 1.2 ROE Data Model

```python
from decimal import Decimal
from datetime import date
from typing import Optional, List
from pydantic import BaseModel, Field, validator

class ROEPayPeriod(BaseModel):
    """
    Individual pay period for ROE reporting

    ROE requires last 53 weeks (or 27 pay periods) of insurable earnings
    """
    period_number: int = Field(..., ge=1, le=53)
    period_start_date: date
    period_end_date: date
    insurable_earnings: Decimal = Field(..., decimal_places=2)
    insurable_hours: Optional[int] = Field(None, ge=0)  # Required for hourly workers

    class Config:
        json_schema_extra = {
            "example": {
                "period_number": 1,
                "period_start_date": "2024-12-16",
                "period_end_date": "2024-12-31",
                "insurable_earnings": "2500.00",
                "insurable_hours": 80
            }
        }


class RecordOfEmployment(BaseModel):
    """
    Record of Employment (ROE)

    Complete data model for ROE submission to Service Canada
    """
    # ROE Identification
    roe_serial_number: Optional[str] = Field(
        None,
        description="Assigned by ROE Web after submission"
    )
    is_amended: bool = Field(
        default=False,
        description="True if this is an amended ROE"
    )
    original_roe_serial_number: Optional[str] = Field(
        None,
        description="Original ROE serial number if this is an amendment"
    )

    # Employer Information
    employer_name: str = Field(..., max_length=60)
    employer_payroll_account_number: str = Field(..., regex=r"^\d{9}RP\d{4}$")
    employer_address_line1: str = Field(..., max_length=30)
    employer_address_line2: Optional[str] = Field(None, max_length=30)
    employer_city: str = Field(..., max_length=28)
    employer_province: str = Field(..., regex=r"^[A-Z]{2}$")
    employer_postal_code: str = Field(..., regex=r"^[A-Z]\d[A-Z]\s?\d[A-Z]\d$")

    # Employee Information
    employee_id: str
    employee_sin: str = Field(..., regex=r"^\d{9}$")
    employee_first_name: str = Field(..., max_length=25)
    employee_last_name: str = Field(..., max_length=30)
    employee_address_line1: str = Field(..., max_length=30)
    employee_address_line2: Optional[str] = Field(None, max_length=30)
    employee_city: str = Field(..., max_length=28)
    employee_province: str = Field(..., regex=r"^[A-Z]{2}$")
    employee_postal_code: str = Field(..., regex=r"^[A-Z]\d[A-Z]\s?\d[A-Z]\d$")

    # Employment Dates
    first_day_worked: date = Field(..., description="First day of employment")
    last_day_worked: date = Field(..., description="Last day employee actually worked")
    expected_date_of_recall: Optional[date] = Field(
        None,
        description="For temporary layoffs - expected return date"
    )

    # Pay Period Information
    pay_period_type: str = Field(
        ...,
        regex="^(weekly|bi-weekly|semi-monthly|monthly)$",
        description="Pay period frequency"
    )
    final_pay_period_ending_date: date = Field(
        ...,
        description="Ending date of final pay period"
    )

    # Insurable Earnings and Hours
    insurable_earnings_pay_periods: List[ROEPayPeriod] = Field(
        ...,
        min_items=1,
        max_items=53,
        description="Up to 53 pay periods (or 27 for bi-weekly) of insurable earnings"
    )

    total_insurable_earnings: Decimal = Field(..., decimal_places=2)
    total_insurable_hours: Optional[int] = Field(None, ge=0)

    # Separation Information
    reason_for_separation: ROEReasonCode
    comments: Optional[str] = Field(
        None,
        max_length=255,
        description="Required for reason codes E, K, M, Z"
    )

    # Vacation Pay
    vacation_pay_amount: Decimal = Field(
        default=Decimal("0"),
        decimal_places=2,
        description="Vacation pay paid at separation"
    )

    # Special Payments (statutory holiday pay, severance, etc.)
    other_monies: Decimal = Field(
        default=Decimal("0"),
        decimal_places=2,
        description="Other monies paid (severance, statutory holiday pay, etc.)"
    )

    # Occupation
    occupation_code: Optional[str] = Field(
        None,
        description="NOC (National Occupational Classification) code"
    )

    # ROE Status
    status: str = Field(
        default="draft",
        regex="^(draft|submitted|accepted|rejected)$"
    )
    submission_date: Optional[date] = None
    created_at: date = Field(default_factory=date.today)
    created_by: str  # User ID

    @validator("comments")
    def validate_comments(cls, v, values):
        """Ensure comments are provided for reason codes that require them"""
        reason_code = values.get("reason_for_separation")
        if reason_code and ROEReasonCode.requires_comment(reason_code):
            if not v or len(v.strip()) == 0:
                raise ValueError(f"Comments are required for reason code {reason_code}")
        return v

    @validator("total_insurable_earnings")
    def validate_total_earnings(cls, v, values):
        """Validate that total matches sum of pay periods"""
        pay_periods = values.get("insurable_earnings_pay_periods", [])
        if pay_periods:
            calculated_total = sum(p.insurable_earnings for p in pay_periods)
            if abs(v - calculated_total) > Decimal("0.01"):
                raise ValueError(
                    f"Total insurable earnings {v} does not match sum of pay periods {calculated_total}"
                )
        return v

    @validator("last_day_worked")
    def validate_last_day_worked(cls, v, values):
        """Ensure last day worked is after first day worked"""
        first_day = values.get("first_day_worked")
        if first_day and v < first_day:
            raise ValueError("Last day worked must be after first day worked")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "is_amended": False,
                "employer_name": "Example Corp",
                "employer_payroll_account_number": "123456789RP0001",
                "employer_address_line1": "123 Business St",
                "employer_city": "Toronto",
                "employer_province": "ON",
                "employer_postal_code": "M5H2N2",
                "employee_id": "emp_001",
                "employee_sin": "123456782",
                "employee_first_name": "John",
                "employee_last_name": "Doe",
                "employee_address_line1": "456 Home Ave",
                "employee_city": "Toronto",
                "employee_province": "ON",
                "employee_postal_code": "M4B1B3",
                "first_day_worked": "2023-01-15",
                "last_day_worked": "2025-01-10",
                "final_pay_period_ending_date": "2025-01-15",
                "pay_period_type": "bi-weekly",
                "total_insurable_earnings": "65000.00",
                "total_insurable_hours": 2080,
                "reason_for_separation": "E",
                "comments": "Employee resigned to pursue other opportunities",
                "vacation_pay_amount": "2600.00",
                "other_monies": "0.00",
                "status": "draft",
                "created_by": "user_12345"
            }
        }
```

---

## 2. ROE Generation Service

### 2.1 Insurable Earnings Calculation

```python
from typing import List, Tuple
from datetime import date, timedelta
from decimal import Decimal

class ROEGenerationService:
    """
    Generate Record of Employment (ROE) for employees
    """

    def __init__(self, firestore_service):
        self.firestore = firestore_service

    async def calculate_insurable_earnings(
        self,
        ledger_id: str,
        employee_id: str,
        last_day_worked: date,
        pay_period_type: str
    ) -> Tuple[List[ROEPayPeriod], Decimal, int]:
        """
        Calculate insurable earnings for last 53 weeks (or 27 pay periods for bi-weekly)

        Args:
            ledger_id: Ledger identifier
            employee_id: Employee identifier
            last_day_worked: Last day employee worked
            pay_period_type: Pay period frequency

        Returns:
            Tuple of (pay_periods, total_earnings, total_hours)
        """
        # Determine lookback period (53 weeks = 371 days)
        lookback_start = last_day_worked - timedelta(days=371)

        # Fetch all payroll records in lookback period
        payroll_records = await self.firestore.get_payroll_records(
            ledger_id=ledger_id,
            employee_id=employee_id,
            start_date=lookback_start,
            end_date=last_day_worked
        )

        # Sort by pay period end date (descending - most recent first)
        payroll_records = sorted(
            payroll_records,
            key=lambda r: r.pay_period_end_date,
            reverse=True
        )

        # Determine maximum number of periods based on pay frequency
        max_periods = self._get_max_periods(pay_period_type)

        # Build ROE pay periods (up to max_periods)
        roe_pay_periods = []
        total_earnings = Decimal("0")
        total_hours = 0

        for i, record in enumerate(payroll_records[:max_periods]):
            period = ROEPayPeriod(
                period_number=i + 1,
                period_start_date=record.pay_period_start_date,
                period_end_date=record.pay_period_end_date,
                insurable_earnings=record.ei_insurable_earnings,
                insurable_hours=record.hours_worked if hasattr(record, "hours_worked") else None
            )
            roe_pay_periods.append(period)

            total_earnings += record.ei_insurable_earnings
            if period.insurable_hours:
                total_hours += period.insurable_hours

        return roe_pay_periods, total_earnings, total_hours

    def _get_max_periods(self, pay_period_type: str) -> int:
        """
        Get maximum number of pay periods for ROE based on pay frequency

        Reference: Service Canada ROE Guide
        """
        max_periods_map = {
            "weekly": 53,
            "bi-weekly": 27,
            "semi-monthly": 27,
            "monthly": 27
        }
        return max_periods_map.get(pay_period_type, 27)

    async def generate_roe(
        self,
        ledger_id: str,
        employee_id: str,
        last_day_worked: date,
        reason_for_separation: ROEReasonCode,
        comments: Optional[str] = None,
        expected_date_of_recall: Optional[date] = None,
        created_by: str = None
    ) -> RecordOfEmployment:
        """
        Generate ROE for an employee

        Args:
            ledger_id: Ledger identifier
            employee_id: Employee identifier
            last_day_worked: Last day employee worked
            reason_for_separation: ROE reason code
            comments: Comments (required for some reason codes)
            expected_date_of_recall: Expected recall date (for temporary layoffs)
            created_by: User ID creating the ROE

        Returns:
            RecordOfEmployment
        """
        # Fetch employee information
        employee = await self.firestore.get_employee(ledger_id, employee_id)
        if not employee:
            raise ValueError(f"Employee {employee_id} not found")

        # Fetch employer information
        employer = await self.firestore.get_employer_info(ledger_id)

        # Calculate insurable earnings
        pay_periods, total_earnings, total_hours = await self.calculate_insurable_earnings(
            ledger_id=ledger_id,
            employee_id=employee_id,
            last_day_worked=last_day_worked,
            pay_period_type=employee.pay_period_type
        )

        if not pay_periods:
            raise ValueError("No payroll records found for ROE generation")

        # Get final pay period ending date
        final_pay_period_ending_date = pay_periods[0].period_end_date

        # Calculate vacation pay (if any unpaid vacation balance)
        vacation_pay = await self._calculate_final_vacation_pay(ledger_id, employee_id)

        # Calculate other monies (statutory holiday pay, severance, etc.)
        other_monies = await self._calculate_other_monies(ledger_id, employee_id, last_day_worked)

        # Build ROE
        roe = RecordOfEmployment(
            employer_name=employer.legal_name,
            employer_payroll_account_number=employer.cra_payroll_account,
            employer_address_line1=employer.address_line1,
            employer_address_line2=employer.address_line2,
            employer_city=employer.city,
            employer_province=employer.province,
            employer_postal_code=employer.postal_code,
            employee_id=employee_id,
            employee_sin=employee.sin,
            employee_first_name=employee.first_name,
            employee_last_name=employee.last_name,
            employee_address_line1=employee.address_line1,
            employee_address_line2=employee.address_line2,
            employee_city=employee.city,
            employee_province=employee.province,
            employee_postal_code=employee.postal_code,
            first_day_worked=employee.hire_date,
            last_day_worked=last_day_worked,
            expected_date_of_recall=expected_date_of_recall,
            pay_period_type=employee.pay_period_type,
            final_pay_period_ending_date=final_pay_period_ending_date,
            insurable_earnings_pay_periods=pay_periods,
            total_insurable_earnings=total_earnings,
            total_insurable_hours=total_hours if total_hours > 0 else None,
            reason_for_separation=reason_for_separation,
            comments=comments,
            vacation_pay_amount=vacation_pay,
            other_monies=other_monies,
            occupation_code=employee.occupation_code if hasattr(employee, "occupation_code") else None,
            status="draft",
            created_by=created_by
        )

        return roe

    async def _calculate_final_vacation_pay(
        self,
        ledger_id: str,
        employee_id: str
    ) -> Decimal:
        """Calculate any unpaid vacation pay balance"""
        vacation_service = VacationService(self.firestore)
        balance = await vacation_service.get_vacation_balance(ledger_id, employee_id)
        return balance.accrued_amount

    async def _calculate_other_monies(
        self,
        ledger_id: str,
        employee_id: str,
        last_day_worked: date
    ) -> Decimal:
        """
        Calculate other monies (statutory holiday pay, severance, etc.)

        This is a placeholder - actual implementation depends on business rules
        """
        # TODO: Implement calculation for:
        # - Unused statutory holiday entitlement
        # - Severance pay (if applicable)
        # - Termination pay
        return Decimal("0")
```

---

## 3. ROE XML Generation for Service Canada

### 3.1 ROE Web XML Format

```python
import xml.etree.ElementTree as ET
from xml.dom import minidom

class ROEXMLGenerator:
    """
    Generate ROE XML for submission to Service Canada ROE Web

    Reference: ROE Web Developer Guide
    https://www.canada.ca/en/employment-social-development/programs/ei/ei-list/ei-roe/access-roe.html
    """

    def __init__(self):
        self.schema_version = "1.0"

    def generate_xml(self, roe: RecordOfEmployment) -> str:
        """
        Generate ROE XML for Service Canada submission

        Args:
            roe: RecordOfEmployment

        Returns:
            XML string
        """
        # Root element
        root = ET.Element("ROE", {
            "xmlns": "http://www.servicecanada.gc.ca/xmlns/roe",
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsi:schemaLocation": "http://www.servicecanada.gc.ca/xmlns/roe roe-1.0.xsd"
        })

        # ROE Header
        header = ET.SubElement(root, "Header")
        ET.SubElement(header, "PayrollAccountNumber").text = roe.employer_payroll_account_number

        if roe.is_amended:
            ET.SubElement(header, "IsAmended").text = "true"
            ET.SubElement(header, "OriginalROESerial").text = roe.original_roe_serial_number
        else:
            ET.SubElement(header, "IsAmended").text = "false"

        # Employer Information
        employer = ET.SubElement(root, "Employer")
        ET.SubElement(employer, "Name").text = roe.employer_name

        employer_address = ET.SubElement(employer, "Address")
        ET.SubElement(employer_address, "Line1").text = roe.employer_address_line1
        if roe.employer_address_line2:
            ET.SubElement(employer_address, "Line2").text = roe.employer_address_line2
        ET.SubElement(employer_address, "City").text = roe.employer_city
        ET.SubElement(employer_address, "Province").text = roe.employer_province
        ET.SubElement(employer_address, "PostalCode").text = roe.employer_postal_code.replace(' ', '')

        # Employee Information
        employee = ET.SubElement(root, "Employee")
        ET.SubElement(employee, "SIN").text = roe.employee_sin

        employee_name = ET.SubElement(employee, "Name")
        ET.SubElement(employee_name, "FirstName").text = roe.employee_first_name
        ET.SubElement(employee_name, "LastName").text = roe.employee_last_name

        employee_address = ET.SubElement(employee, "Address")
        ET.SubElement(employee_address, "Line1").text = roe.employee_address_line1
        if roe.employee_address_line2:
            ET.SubElement(employee_address, "Line2").text = roe.employee_address_line2
        ET.SubElement(employee_address, "City").text = roe.employee_city
        ET.SubElement(employee_address, "Province").text = roe.employee_province
        ET.SubElement(employee_address, "PostalCode").text = roe.employee_postal_code.replace(' ', '')

        # Employment Information
        employment = ET.SubElement(root, "Employment")
        ET.SubElement(employment, "FirstDayWorked").text = roe.first_day_worked.isoformat()
        ET.SubElement(employment, "LastDayWorked").text = roe.last_day_worked.isoformat()

        if roe.expected_date_of_recall:
            ET.SubElement(employment, "ExpectedDateOfRecall").text = roe.expected_date_of_recall.isoformat()

        # Pay Period Information
        pay_info = ET.SubElement(root, "PayInformation")
        ET.SubElement(pay_info, "PayPeriodType").text = roe.pay_period_type
        ET.SubElement(pay_info, "FinalPayPeriodEndingDate").text = roe.final_pay_period_ending_date.isoformat()

        # Insurable Earnings
        earnings = ET.SubElement(pay_info, "InsurableEarnings")
        ET.SubElement(earnings, "TotalInsurableEarnings").text = f"{roe.total_insurable_earnings:.2f}"

        if roe.total_insurable_hours:
            ET.SubElement(earnings, "TotalInsurableHours").text = str(roe.total_insurable_hours)

        # Pay Periods
        pay_periods_elem = ET.SubElement(earnings, "PayPeriods")
        for period in roe.insurable_earnings_pay_periods:
            period_elem = ET.SubElement(pay_periods_elem, "PayPeriod")
            ET.SubElement(period_elem, "PeriodNumber").text = str(period.period_number)
            ET.SubElement(period_elem, "StartDate").text = period.period_start_date.isoformat()
            ET.SubElement(period_elem, "EndDate").text = period.period_end_date.isoformat()
            ET.SubElement(period_elem, "InsurableEarnings").text = f"{period.insurable_earnings:.2f}"

            if period.insurable_hours:
                ET.SubElement(period_elem, "InsurableHours").text = str(period.insurable_hours)

        # Separation Information
        separation = ET.SubElement(root, "Separation")
        ET.SubElement(separation, "ReasonCode").text = roe.reason_for_separation.value

        if roe.comments:
            ET.SubElement(separation, "Comments").text = roe.comments

        # Other Monies
        if roe.vacation_pay_amount > Decimal("0") or roe.other_monies > Decimal("0"):
            other_monies = ET.SubElement(root, "OtherMonies")

            if roe.vacation_pay_amount > Decimal("0"):
                ET.SubElement(other_monies, "VacationPay").text = f"{roe.vacation_pay_amount:.2f}"

            if roe.other_monies > Decimal("0"):
                ET.SubElement(other_monies, "OtherPayments").text = f"{roe.other_monies:.2f}"

        # Occupation
        if roe.occupation_code:
            ET.SubElement(root, "OccupationCode").text = roe.occupation_code

        # Pretty print XML
        xml_string = ET.tostring(root, encoding='unicode')
        parsed = minidom.parseString(xml_string)
        pretty_xml = parsed.toprettyxml(indent="  ", encoding="UTF-8")

        return pretty_xml.decode('utf-8')
```

---

## 4. ROE PDF Generation

```python
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO

class ROEPDFGenerator:
    """
    Generate ROE PDF for employee copy

    Note: Official submission is via ROE Web XML, but PDF is useful for employee records
    """

    def __init__(self):
        self.styles = getSampleStyleSheet()

    def generate_roe_pdf(self, roe: RecordOfEmployment) -> bytes:
        """
        Generate ROE PDF

        Args:
            roe: RecordOfEmployment

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
        title = Paragraph("Record of Employment (ROE)", self.styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))

        if roe.roe_serial_number:
            serial = Paragraph(f"<b>ROE Serial Number:</b> {roe.roe_serial_number}", self.styles['Normal'])
            story.append(serial)
            story.append(Spacer(1, 6))

        # Employer Information
        story.append(Paragraph("<b>Employer Information</b>", self.styles['Heading2']))
        story.append(Spacer(1, 6))

        employer_data = [
            ['Employer Name', roe.employer_name],
            ['Payroll Account Number', roe.employer_payroll_account_number],
            ['Address', f"{roe.employer_address_line1}\n{roe.employer_city}, {roe.employer_province} {roe.employer_postal_code}"]
        ]
        employer_table = Table(employer_data, colWidths=[2.5 * inch, 4 * inch])
        employer_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6)
        ]))
        story.append(employer_table)
        story.append(Spacer(1, 12))

        # Employee Information
        story.append(Paragraph("<b>Employee Information</b>", self.styles['Heading2']))
        story.append(Spacer(1, 6))

        employee_data = [
            ['Employee Name', f"{roe.employee_first_name} {roe.employee_last_name}"],
            ['SIN', f"{roe.employee_sin[:3]}-{roe.employee_sin[3:6]}-{roe.employee_sin[6:]}"],
            ['Address', f"{roe.employee_address_line1}\n{roe.employee_city}, {roe.employee_province} {roe.employee_postal_code}"]
        ]
        employee_table = Table(employee_data, colWidths=[2.5 * inch, 4 * inch])
        employee_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6)
        ]))
        story.append(employee_table)
        story.append(Spacer(1, 12))

        # Employment Dates
        story.append(Paragraph("<b>Employment Information</b>", self.styles['Heading2']))
        story.append(Spacer(1, 6))

        employment_data = [
            ['First Day Worked', roe.first_day_worked.strftime('%B %d, %Y')],
            ['Last Day Worked', roe.last_day_worked.strftime('%B %d, %Y')],
            ['Final Pay Period Ending', roe.final_pay_period_ending_date.strftime('%B %d, %Y')],
            ['Pay Period Type', roe.pay_period_type.replace('-', ' ').title()]
        ]

        if roe.expected_date_of_recall:
            employment_data.append(['Expected Date of Recall', roe.expected_date_of_recall.strftime('%B %d, %Y')])

        employment_table = Table(employment_data, colWidths=[2.5 * inch, 4 * inch])
        employment_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6)
        ]))
        story.append(employment_table)
        story.append(Spacer(1, 12))

        # Insurable Earnings Summary
        story.append(Paragraph("<b>Insurable Earnings Summary</b>", self.styles['Heading2']))
        story.append(Spacer(1, 6))

        earnings_data = [
            ['Total Insurable Earnings', f"${roe.total_insurable_earnings:,.2f}"]
        ]

        if roe.total_insurable_hours:
            earnings_data.append(['Total Insurable Hours', str(roe.total_insurable_hours)])

        if roe.vacation_pay_amount > Decimal("0"):
            earnings_data.append(['Vacation Pay', f"${roe.vacation_pay_amount:,.2f}"])

        if roe.other_monies > Decimal("0"):
            earnings_data.append(['Other Monies', f"${roe.other_monies:,.2f}"])

        earnings_table = Table(earnings_data, colWidths=[2.5 * inch, 4 * inch])
        earnings_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6)
        ]))
        story.append(earnings_table)
        story.append(Spacer(1, 12))

        # Reason for Separation
        story.append(Paragraph("<b>Reason for Separation</b>", self.styles['Heading2']))
        story.append(Spacer(1, 6))

        reason_text = f"<b>Code {roe.reason_for_separation.value}:</b> {ROEReasonCode.get_description(roe.reason_for_separation.value)}"
        story.append(Paragraph(reason_text, self.styles['Normal']))

        if roe.comments:
            story.append(Spacer(1, 6))
            story.append(Paragraph(f"<b>Comments:</b> {roe.comments}", self.styles['Normal']))

        story.append(Spacer(1, 18))

        # Pay Period Details (show first 10 periods)
        story.append(Paragraph("<b>Insurable Earnings by Pay Period (Most Recent)</b>", self.styles['Heading2']))
        story.append(Spacer(1, 6))

        period_data = [['Period #', 'Start Date', 'End Date', 'Earnings', 'Hours']]

        for period in roe.insurable_earnings_pay_periods[:10]:
            period_data.append([
                str(period.period_number),
                period.period_start_date.strftime('%Y-%m-%d'),
                period.period_end_date.strftime('%Y-%m-%d'),
                f"${period.insurable_earnings:,.2f}",
                str(period.insurable_hours) if period.insurable_hours else "N/A"
            ])

        if len(roe.insurable_earnings_pay_periods) > 10:
            period_data.append(['...', '...', '...', '...', '...'])

        period_table = Table(period_data, colWidths=[0.8 * inch, 1.3 * inch, 1.3 * inch, 1.3 * inch, 0.8 * inch])
        period_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#666666')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
            ('ALIGN', (4, 0), (4, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4)
        ]))
        story.append(period_table)

        story.append(Spacer(1, 24))

        # Footer
        footer = Paragraph(
            "This is a copy of your Record of Employment for your records.<br/>"
            "The official ROE has been submitted to Service Canada electronically.<br/>"
            "For questions about Employment Insurance benefits, visit www.canada.ca/ei or call 1-800-206-7218.",
            self.styles['Normal']
        )
        story.append(footer)

        # Build PDF
        doc.build(story)

        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes
```

---

## 5. API Endpoints

```python
from fastapi import APIRouter, Depends, HTTPException, Response
from typing import Optional
from datetime import date

router = APIRouter(prefix="/api/v1/roe", tags=["roe"])

@router.post("/generate/{ledger_id}/{employee_id}")
async def generate_roe(
    ledger_id: str,
    employee_id: str,
    last_day_worked: date,
    reason_for_separation: ROEReasonCode,
    comments: Optional[str] = None,
    expected_date_of_recall: Optional[date] = None,
    current_user=Depends(get_current_user),
    firestore_service=Depends(get_firestore_service)
):
    """
    Generate ROE for an employee

    - Calculates insurable earnings from last 53 weeks
    - Creates ROE record in draft status
    - Returns ROE data for review
    """
    if not await check_ledger_access(current_user.uid, ledger_id):
        raise HTTPException(status_code=403, detail="Access denied")

    # Generate ROE
    roe_service = ROEGenerationService(firestore_service)

    try:
        roe = await roe_service.generate_roe(
            ledger_id=ledger_id,
            employee_id=employee_id,
            last_day_worked=last_day_worked,
            reason_for_separation=reason_for_separation,
            comments=comments,
            expected_date_of_recall=expected_date_of_recall,
            created_by=current_user.uid
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Save ROE to Firestore
    roe_id = await firestore_service.create_roe(ledger_id, roe)

    return {
        "roe_id": roe_id,
        "status": "draft",
        "roe": roe.dict()
    }


@router.post("/submit/{ledger_id}/{roe_id}")
async def submit_roe_to_service_canada(
    ledger_id: str,
    roe_id: str,
    current_user=Depends(get_current_user),
    firestore_service=Depends(get_firestore_service)
):
    """
    Submit ROE to Service Canada via ROE Web

    - Generates XML for Service Canada
    - Marks ROE as submitted
    - Returns submission confirmation
    """
    if not await check_ledger_access(current_user.uid, ledger_id):
        raise HTTPException(status_code=403, detail="Access denied")

    # Fetch ROE
    roe = await firestore_service.get_roe(ledger_id, roe_id)
    if not roe:
        raise HTTPException(status_code=404, detail="ROE not found")

    if roe.status != "draft":
        raise HTTPException(status_code=400, detail=f"ROE already {roe.status}")

    # Generate XML
    xml_generator = ROEXMLGenerator()
    xml_string = xml_generator.generate_xml(roe)

    # TODO: Submit to Service Canada ROE Web API
    # This would require ROE Web credentials and API integration
    # For now, we'll mark as submitted and store the XML

    # Update ROE status
    roe.status = "submitted"
    roe.submission_date = date.today()
    await firestore_service.update_roe(ledger_id, roe_id, roe)

    # Store XML in Google Drive
    storage_service = T4StorageService(current_user.credentials)
    xml_file_id = await storage_service.upload_roe_xml(
        ledger_id=ledger_id,
        employee_id=roe.employee_id,
        xml_string=xml_string
    )

    return {
        "message": "ROE submitted successfully",
        "roe_id": roe_id,
        "submission_date": roe.submission_date,
        "xml_file_id": xml_file_id
    }


@router.get("/download-pdf/{ledger_id}/{roe_id}")
async def download_roe_pdf(
    ledger_id: str,
    roe_id: str,
    current_user=Depends(get_current_user),
    firestore_service=Depends(get_firestore_service)
):
    """
    Download ROE PDF (employee copy)
    """
    if not await check_ledger_access(current_user.uid, ledger_id):
        raise HTTPException(status_code=403, detail="Access denied")

    # Fetch ROE
    roe = await firestore_service.get_roe(ledger_id, roe_id)
    if not roe:
        raise HTTPException(status_code=404, detail="ROE not found")

    # Generate PDF
    pdf_generator = ROEPDFGenerator()
    pdf_bytes = pdf_generator.generate_roe_pdf(roe)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=ROE_{roe.employee_last_name}_{roe.last_day_worked}.pdf"}
    )


@router.get("/list/{ledger_id}")
async def list_roes(
    ledger_id: str,
    employee_id: Optional[str] = None,
    current_user=Depends(get_current_user),
    firestore_service=Depends(get_firestore_service)
):
    """
    List all ROEs for a ledger (optionally filtered by employee)
    """
    if not await check_ledger_access(current_user.uid, ledger_id):
        raise HTTPException(status_code=403, detail="Access denied")

    roes = await firestore_service.get_roes(ledger_id, employee_id=employee_id)

    return {
        "ledger_id": ledger_id,
        "total_roes": len(roes),
        "roes": [
            {
                "roe_id": roe.id,
                "employee_name": f"{roe.employee_first_name} {roe.employee_last_name}",
                "last_day_worked": roe.last_day_worked,
                "reason": roe.reason_for_separation.value,
                "status": roe.status,
                "submission_date": roe.submission_date
            }
            for roe in roes
        ]
    }
```

---

## 6. Testing

```python
import pytest
from decimal import Decimal
from datetime import date

def test_roe_reason_code_requires_comment():
    """Test reason code comment requirement"""
    assert ROEReasonCode.requires_comment("E") is True  # Quit
    assert ROEReasonCode.requires_comment("M") is True  # Dismissal
    assert ROEReasonCode.requires_comment("A") is False  # Shortage of work


def test_roe_validation_comments():
    """Test ROE validation for required comments"""
    # Should raise error if quit without comments
    with pytest.raises(ValueError, match="Comments are required"):
        RecordOfEmployment(
            employer_name="Test",
            employer_payroll_account_number="123456789RP0001",
            # ... other required fields ...
            reason_for_separation=ROEReasonCode.E_QUIT,
            comments=None  # Missing required comment
        )


def test_roe_insurable_earnings_total():
    """Test total insurable earnings validation"""
    pay_periods = [
        ROEPayPeriod(
            period_number=1,
            period_start_date=date(2025, 1, 1),
            period_end_date=date(2025, 1, 15),
            insurable_earnings=Decimal("2000.00")
        ),
        ROEPayPeriod(
            period_number=2,
            period_start_date=date(2024, 12, 16),
            period_end_date=date(2024, 12, 31),
            insurable_earnings=Decimal("2500.00")
        )
    ]

    # Correct total
    roe = RecordOfEmployment(
        # ... required fields ...
        insurable_earnings_pay_periods=pay_periods,
        total_insurable_earnings=Decimal("4500.00")  # Correct sum
    )
    assert roe.total_insurable_earnings == Decimal("4500.00")

    # Incorrect total should raise error
    with pytest.raises(ValueError, match="does not match sum"):
        RecordOfEmployment(
            # ... required fields ...
            insurable_earnings_pay_periods=pay_periods,
            total_insurable_earnings=Decimal("5000.00")  # Wrong sum
        )
```

---

## 7. ROE Web Electronic Submission Details

> **Note**: For comprehensive submission documentation, see [16_government_electronic_submission.md](./16_government_electronic_submission.md)

### 7.1 ROE Web System Overview

**Official Portal**: https://www.canada.ca/en/employment-social-development/programs/ei/ei-list/ei-roe/access-roe.html

ROE Web is a secure Service Canada portal that allows employers to:
- Create and submit ROEs online
- Upload batch ROEs via Payroll Extract (XML)
- Track submission status
- Import serial numbers back to payroll software

### 7.2 Submission Methods

| Method | Description | Capacity | Best For |
|--------|-------------|----------|----------|
| **Online Form** | Manual entry via portal | 1 ROE at a time | Occasional use |
| **ROE Web Assistant** | Guided completion | 1 ROE at a time | New users |
| **Payroll Extract** | XML batch upload | 1,200 ROEs/file, 10 files/upload | Bulk submissions |

### 7.3 Payroll Extract (XML Batch Upload)

**Documentation**: https://www.canada.ca/en/employment-social-development/programs/ei/ei-list/reports/payroll-extract.html

**Process Flow**:
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Beanflow        │     │ Generate XML    │     │ ROE Web         │
│ ROE Data        │ ──► │ (.BLK file)     │ ──► │ Payroll Extract │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                         │
                                              ┌──────────┴──────────┐
                                              ▼                     ▼
                                    ┌─────────────────┐   ┌─────────────────┐
                                    │ Passed ROEs     │   │ Failed ROEs     │
                                    │ (Submitted)     │   │ (Fix & Resubmit)│
                                    └─────────────────┘   └─────────────────┘
```

**XML File Requirements**:
- File extension: `.BLK`
- Encoding: UTF-8
- Schema: ROE Web Payroll Extract Schema v2.0

**XML Header Structure**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<ROEHEADER version="2.0"
           transmitterNumber="123456789RP0001"
           transmitterName="Company Name"
           contactName="Contact Person"
           contactPhone="4165551234">
  <ROE>
    <!-- Individual ROE data -->
  </ROE>
  <!-- More ROEs... -->
</ROEHEADER>
```

### 7.4 Status Tracking

After uploading to ROE Web:

| Status | Description | Action |
|--------|-------------|--------|
| **Received** | File waiting for processing | Wait |
| **Processing** | Being validated | Wait |
| **Process Completed** | Available under View | Retrieve serial numbers |
| **Invalid File** | Format error | Fix and re-upload |

**For individual ROEs within a file**:

| Status | Description | Action |
|--------|-------------|--------|
| **Passed** | ROE accepted | Submit or review |
| **Failed** | Validation error | Fix via Online Form or re-upload corrected XML |

### 7.5 Import Feature (Serial Number Retrieval)

**Purpose**: Extract ROE Serial Numbers from ROE Web back into Beanflow

**Use Cases**:
1. Record keeping
2. Required for issuing amended ROEs
3. Audit trail

**Import Process**:
1. Login to ROE Web
2. Use Import feature with search criteria
3. Export XML with serial numbers
4. Import into Beanflow database

### 7.6 Testing Environment

**ROE Web Demo Site**: Available for testing payroll extract files before production submission

**Validation Steps**:
1. Generate XML using ROE Web schema (XSD)
2. Validate locally using XSD validator tool
3. Upload to demo site
4. Review validation results
5. Submit to production when validated

### 7.7 Registration Requirements

**Primary Officer Validation** (Required for ROE Web access):

| Method | Description |
|--------|-------------|
| **Online** | Validate via CRA My Business Account |
| **In Person** | Visit Service Canada Centre with photo ID |

**Required Credentials**:
- GCKey, OR
- Sign-In Partner (bank credentials)

### 7.8 Beanflow Implementation Phases

| Phase | Features | User Action |
|-------|----------|-------------|
| **Phase 1 (MVP)** | Generate XML + PDF | Download .BLK, upload to ROE Web manually |
| **Phase 2** | Validation + status tracking | Same, with pre-submission checks |
| **Phase 3 (Enterprise)** | Store ROE Web credentials | Automated submission |

---

## 8. Implementation Checklist

- [ ] **Data Models**
  - [ ] Implement `ROEReasonCode` enum
  - [ ] Implement `ROEPayPeriod` model
  - [ ] Implement `RecordOfEmployment` model with validation
  - [ ] Test validation logic

- [ ] **ROE Generation Service**
  - [ ] Implement insurable earnings calculation (53 weeks lookback)
  - [ ] Implement `generate_roe()` method
  - [ ] Handle vacation pay and other monies
  - [ ] Test with sample payroll data

- [ ] **XML Generation**
  - [ ] Implement ROE XML generator for Service Canada
  - [ ] Generate `.BLK` file format
  - [ ] Validate against ROE Web schema (XSD)
  - [ ] Test with ROE Web demo site
  - [ ] Test XML output

- [ ] **PDF Generation**
  - [ ] Implement ROE PDF generator (employee copy)
  - [ ] Test PDF layout

- [ ] **API Endpoints**
  - [ ] Implement ROE generation endpoint
  - [ ] Implement ROE XML download endpoint
  - [ ] Implement ROE PDF download endpoint
  - [ ] Implement ROE listing endpoint

- [ ] **Submission Integration (Phase 2+)**
  - [ ] Pre-submission validation against schema
  - [ ] Status tracking (draft, submitted, accepted)
  - [ ] Serial number import from ROE Web
  - [ ] Amended ROE support

- [ ] **Storage**
  - [ ] Store ROEs in Supabase
  - [ ] Store ROE PDFs/XML in storage

- [ ] **Testing**
  - [ ] Unit tests for all services
  - [ ] Integration tests
  - [ ] Test XML with ROE Web demo site
  - [ ] Manual testing with real employee data

---

**Document Version**: 1.1
**Created**: 2025-10-09
**Updated**: 2025-12-31
**For**: Beanflow-Payroll System - Phase 7 Implementation (ROE)
