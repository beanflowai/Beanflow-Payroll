# Phase 3: Paystub Generation

**Duration**: 1.5 weeks
**Complexity**: Low
**Prerequisites**: Phase 1-2 completed

> **Last Updated**: 2025-12-07
> **Architecture Version**: v2.0 (DigitalOcean Spaces storage)

---

## 🎯 Objectives

Generate compliant PDF paystubs that meet Canadian legal requirements and store them in DigitalOcean Spaces.

### Deliverables
1. ✅ PDF paystub generator using ReportLab
2. ✅ Paystub template with all mandatory fields
3. ✅ YTD (year-to-date) totals display
4. ✅ Employer information section
5. ✅ **DigitalOcean Spaces storage** (NEW)
6. ✅ **Pre-signed URLs for secure download** (NEW)

---

## 🔄 Architecture Changes

| Component | Old Plan | Current Architecture |
|-----------|----------|---------------------|
| **File Storage** | Google Drive | **DigitalOcean Spaces** |
| **URL Generation** | Drive file ID | **Pre-signed URLs (15 min expiry)** |
| **Path Format** | Folder hierarchy | **Object key pattern** |
| **Service** | GoogleDriveService | **DO Spaces client** |

---

## 📋 Canadian Paystub Requirements

### Mandatory Fields (Varies by Province)

**All Provinces Must Include**:
- Employee name and address
- Employer name and address
- Pay period dates
- Pay date
- Gross earnings breakdown
- All deductions (itemized)
- Net pay
- YTD totals

**Province-Specific**:
- **Ontario**: Must show vacation pay accrued
- **Quebec**: Not applicable (we don't support Quebec)
- **BC**: Must show employer portion of CPP/EI

### Vacation Pay Display

系统支持两种 vacation pay 方法，在 paystub 上的显示方式不同：

| 方法 | 字段 | 显示位置 | 说明 |
|------|------|----------|------|
| **Pay-as-you-go** | `vacation_pay_paid` | Earnings section | 每期发放 vacation pay，直接加到当期收入 |
| **Accrual** | `vacation_accrued` | Vacation Tracking section | 累积 vacation，休假时才发放 |

- `vacation_pay_paid`: 在 Earnings section 显示，仅当值 > 0 时
- `vacation_accrued`: 在 Vacation Tracking section 显示（Ontario 强制要求，其他省可选）
- 两种方法的计算均基于 `vacation_rate` × `gross_earnings`

详见 `docs/08_holidays_vacation.md` 获取完整的 vacation pay 计算逻辑。

---

## 📦 Task 3.1: Create Paystub Generator

### LLM Agent Prompt

```markdown
TASK: Create PDF Paystub Generator

FILE TO CREATE:
backend/app/services/payroll/paystub_generator.py

REQUIREMENTS:

1. Install dependencies (add to pyproject.toml):
```bash
cd backend
uv add reportlab
```

2. Implement PaystubGenerator class:

```python
"""
PDF Paystub Generator for Canadian payroll.

Generates compliant PDF paystubs that meet provincial legal requirements.
Uses ReportLab for PDF generation.
"""

from __future__ import annotations

from decimal import Decimal
from datetime import date
from io import BytesIO
from typing import Any

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

from app.models.payroll import PayrollRecord, Province


class PaystubGenerator:
    """
    Generate Canadian payroll paystubs in PDF format.

    Meets requirements for all provinces except Quebec.
    """

    def __init__(self):
        self.page_width = letter[0]
        self.page_height = letter[1]
        self.margin = 0.75 * inch
        self.styles = getSampleStyleSheet()

        # Custom styles
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=12,
            alignment=TA_CENTER
        )

        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#333333'),
            spaceAfter=6,
            spaceBefore=12
        )

    def generate_paystub_bytes(
        self,
        employee_name: str,
        employee_id: str,
        sin_masked: str,
        province: Province,
        employer_name: str,
        employer_address: str,
        period_start: date,
        period_end: date,
        pay_date: date,
        record: PayrollRecord
    ) -> bytes:
        """
        Generate a PDF paystub as bytes.

        Args:
            employee_name: Employee full name
            employee_id: Employee UUID string
            sin_masked: Masked SIN (***-***-XXX)
            province: Province of employment
            employer_name: Company name
            employer_address: Company address
            period_start: Pay period start date
            period_end: Pay period end date
            pay_date: Date of payment
            record: Payroll record with calculated amounts

        Returns:
            PDF file as bytes
        """
        # Create PDF in memory
        buffer = BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin
        )

        # Build content
        story = []

        # 1. Header
        story.extend(self._build_header(employer_name))

        # 2. Employee and period info
        story.extend(self._build_employee_info(
            employee_name=employee_name,
            employee_id=employee_id,
            sin_masked=sin_masked,
            province=province,
            employer_address=employer_address,
            period_start=period_start,
            period_end=period_end,
            pay_date=pay_date
        ))

        # 3. Earnings section
        story.extend(self._build_earnings_section(record))

        # 4. Deductions section
        story.extend(self._build_deductions_section(record))

        # 5. Summary section
        story.extend(self._build_summary_section(record))

        # 6. YTD totals
        story.extend(self._build_ytd_section(record))

        # 7. Vacation tracking (Ontario requirement)
        if province == Province.ON:
            story.extend(self._build_vacation_section(record))

        # 8. Employer contributions (BC requirement)
        if province == Province.BC:
            story.extend(self._build_employer_contributions(record))

        # 9. Footer
        story.extend(self._build_footer())

        # Generate PDF
        doc.build(story)

        # Get bytes and reset buffer
        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes

    def generate_paystub_file(
        self,
        output_path: str,
        **kwargs
    ) -> str:
        """
        Generate a PDF paystub and save to file.

        Args:
            output_path: Where to save PDF
            **kwargs: Same as generate_paystub_bytes

        Returns:
            Path to generated PDF file
        """
        pdf_bytes = self.generate_paystub_bytes(**kwargs)

        with open(output_path, 'wb') as f:
            f.write(pdf_bytes)

        return output_path

    def _build_header(self, employer_name: str) -> list:
        """Build paystub header"""
        title = Paragraph(
            f"<b>{employer_name}</b><br/>STATEMENT OF EARNINGS",
            self.title_style
        )
        return [title, Spacer(1, 0.2 * inch)]

    def _build_employee_info(
        self,
        employee_name: str,
        employee_id: str,
        sin_masked: str,
        province: Province,
        employer_address: str,
        period_start: date,
        period_end: date,
        pay_date: date
    ) -> list:
        """Build employee and employer info section"""
        data = [
            ['Employer:', employer_address, 'Employee:', employee_name],
            ['', '', 'Employee ID:', employee_id[:8] + '...'],  # Truncate UUID
            ['Pay Period:', f"{period_start} to {period_end}", 'Province:', province.value],
            ['Pay Date:', str(pay_date), 'SIN:', sin_masked]
        ]

        table = Table(data, colWidths=[1.2*inch, 2.5*inch, 1.2*inch, 2.5*inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#666666')),
            ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#666666')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))

        return [table, Spacer(1, 0.3 * inch)]

    def _build_earnings_section(self, record: PayrollRecord) -> list:
        """Build earnings breakdown"""
        heading = Paragraph("<b>EARNINGS</b>", self.heading_style)

        data = [
            ['Description', 'Hours', 'Rate', 'Current', 'YTD'],
            ['Regular Earnings', '-', '-', f"${record.gross_regular:.2f}", f"${record.ytd_gross:.2f}"],
        ]

        if record.gross_overtime > 0:
            data.append([
                'Overtime Earnings', '-', '-', f"${record.gross_overtime:.2f}", '-'
            ])

        if record.holiday_pay > 0:
            data.append([
                'Holiday Pay', '-', '-', f"${record.holiday_pay:.2f}", '-'
            ])

        if record.vacation_pay_paid > 0:
            data.append([
                'Vacation Pay', '-', '-', f"${record.vacation_pay_paid:.2f}", '-'
            ])

        # Total earnings row
        data.append([
            '<b>TOTAL EARNINGS</b>', '', '', f"<b>${record.total_gross:.2f}</b>", f"<b>${record.ytd_gross:.2f}</b>"
        ])

        table = Table(data, colWidths=[2.5*inch, 1*inch, 1*inch, 1.2*inch, 1.2*inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8e8e8')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#333333')),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('LINEBELOW', (0, -1), (-1, -1), 1.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))

        return [heading, table, Spacer(1, 0.2 * inch)]

    def _build_deductions_section(self, record: PayrollRecord) -> list:
        """Build deductions breakdown"""
        heading = Paragraph("<b>DEDUCTIONS</b>", self.heading_style)

        data = [
            ['Description', 'Current', 'YTD'],
            ['CPP - Employee', f"${record.cpp_employee:.2f}", f"${record.ytd_cpp:.2f}"],
        ]

        if record.cpp_additional > 0:
            data.append([
                'CPP2 - Additional (above YMPE)', f"${record.cpp_additional:.2f}", '-'
            ])

        data.extend([
            ['EI - Employee', f"${record.ei_employee:.2f}", f"${record.ytd_ei:.2f}"],
            ['Federal Income Tax', f"${record.federal_tax:.2f}", f"${record.ytd_federal_tax:.2f}"],
            ['Provincial Income Tax', f"${record.provincial_tax:.2f}", f"${record.ytd_provincial_tax:.2f}"],
        ])

        # Optional deductions
        if record.rrsp > 0:
            data.append(['RRSP Contribution', f"${record.rrsp:.2f}", '-'])

        if record.union_dues > 0:
            data.append(['Union Dues', f"${record.union_dues:.2f}", '-'])

        if record.garnishments > 0:
            data.append(['Garnishments', f"${record.garnishments:.2f}", '-'])

        # Total deductions row
        data.append([
            '<b>TOTAL DEDUCTIONS</b>',
            f"<b>${record.total_deductions:.2f}</b>",
            '-'
        ])

        table = Table(data, colWidths=[3.5*inch, 1.7*inch, 1.7*inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8e8e8')),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('LINEBELOW', (0, -1), (-1, -1), 1.5, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))

        return [heading, table, Spacer(1, 0.2 * inch)]

    def _build_summary_section(self, record: PayrollRecord) -> list:
        """Build net pay summary"""
        data = [
            ['Gross Earnings', f"${record.total_gross:.2f}"],
            ['Total Deductions', f"-${record.total_deductions:.2f}"],
            ['<b>NET PAY</b>', f"<b>${record.net_pay:.2f}</b>"],
        ]

        table = Table(data, colWidths=[4*inch, 2*inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('LINEABOVE', (0, 2), (-1, 2), 2, colors.black),
            ('LINEBELOW', (0, 2), (-1, 2), 2, colors.black),
            ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#f0f0f0')),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))

        return [Spacer(1, 0.2 * inch), table, Spacer(1, 0.3 * inch)]

    def _build_ytd_section(self, record: PayrollRecord) -> list:
        """Build YTD summary"""
        heading = Paragraph("<b>YEAR-TO-DATE SUMMARY</b>", self.heading_style)

        data = [
            ['Gross Earnings YTD:', f"${record.ytd_gross:.2f}"],
            ['CPP Contributions YTD:', f"${record.ytd_cpp:.2f}"],
            ['EI Premiums YTD:', f"${record.ytd_ei:.2f}"],
            ['Federal Tax YTD:', f"${record.ytd_federal_tax:.2f}"],
            ['Provincial Tax YTD:', f"${record.ytd_provincial_tax:.2f}"],
        ]

        table = Table(data, colWidths=[4*inch, 2*inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#666666')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))

        return [heading, table]

    def _build_vacation_section(self, record: PayrollRecord) -> list:
        """Build vacation tracking section (Ontario requirement)"""
        heading = Paragraph("<b>VACATION TRACKING</b>", self.heading_style)

        data = [
            ['Vacation Accrued This Period:', f"${record.vacation_accrued:.2f}"],
            ['Vacation Hours Taken:', f"{record.vacation_hours_taken:.1f} hours"],
        ]

        table = Table(data, colWidths=[4*inch, 2*inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#666666')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))

        return [heading, table]

    def _build_employer_contributions(self, record: PayrollRecord) -> list:
        """Build employer contributions section (BC requirement)"""
        heading = Paragraph("<b>EMPLOYER CONTRIBUTIONS</b>", self.heading_style)

        data = [
            ['CPP - Employer Portion:', f"${record.cpp_employer:.2f}"],
            ['EI - Employer Portion:', f"${record.ei_employer:.2f}"],
            ['Total Employer Contributions:', f"${record.total_employer_cost:.2f}"],
        ]

        table = Table(data, colWidths=[4*inch, 2*inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#666666')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))

        return [heading, table]

    def _build_footer(self) -> list:
        """Build paystub footer"""
        footer_style = ParagraphStyle(
            'Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#999999'),
            alignment=TA_CENTER
        )

        footer_text = Paragraph(
            "This is an official statement of earnings. Please retain for your records.<br/>"
            "For questions, contact your payroll department.",
            footer_style
        )

        return [Spacer(1, 0.5 * inch), footer_text]
```

VALIDATION:
Generate a test paystub and verify:
- All mandatory fields present
- Numbers align properly
- YTD totals accurate
- PDF renders correctly
```

---

## 📦 Task 3.2: DigitalOcean Spaces Storage (NEW)

### LLM Agent Prompt

```markdown
TASK: Create Paystub Storage Service for DigitalOcean Spaces

CONTEXT:
Use DigitalOcean Spaces for storing paystub PDFs, consistent with
the existing document storage pattern in the project.

FILE TO CREATE:
backend/app/services/payroll/paystub_storage.py

REFERENCE:
- backend/app/services/storage/do_spaces_service.py (existing pattern)
- backend/app/core/config.py (DO Spaces configuration)

REQUIREMENTS:

```python
"""
Paystub storage service using DigitalOcean Spaces.

Handles upload, retrieval, and pre-signed URL generation for
paystub PDFs.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any
from uuid import UUID

import boto3
from botocore.config import Config

from app.core.config import settings

logger = logging.getLogger(__name__)


class PaystubStorage:
    """
    Store and retrieve paystubs in DigitalOcean Spaces.

    Storage path pattern:
    {root_prefix}/{user_id}/{ledger_id}/payroll/paystubs/{year}/{employee_id}_{pay_date}.pdf

    Example:
    beanflow/user123/ledger456/payroll/paystubs/2025/emp789_2025-01-15.pdf
    """

    def __init__(self):
        """Initialize DO Spaces client."""
        self.bucket = settings.do_spaces_bucket
        self.root_prefix = settings.do_spaces_root_prefix or ""

        # Initialize S3-compatible client
        self.client = boto3.client(
            's3',
            endpoint_url=settings.do_spaces_endpoint,
            aws_access_key_id=settings.do_spaces_access_key,
            aws_secret_access_key=settings.do_spaces_secret_key,
            region_name=settings.do_spaces_region,
            config=Config(signature_version='s3v4')
        )

    def _build_storage_key(
        self,
        user_id: str,
        ledger_id: str,
        employee_id: UUID | str,
        pay_date: date
    ) -> str:
        """
        Build storage key for paystub.

        Args:
            user_id: User ID
            ledger_id: Ledger ID
            employee_id: Employee UUID
            pay_date: Pay date

        Returns:
            Storage key path
        """
        base = self.root_prefix.rstrip('/') if self.root_prefix else ""
        year = pay_date.year

        key = f"{user_id}/{ledger_id}/payroll/paystubs/{year}/{employee_id}_{pay_date.isoformat()}.pdf"

        if base:
            key = f"{base}/{key}"

        return key

    async def save_paystub(
        self,
        user_id: str,
        ledger_id: str,
        employee_id: UUID | str,
        pay_date: date,
        pdf_bytes: bytes
    ) -> str:
        """
        Upload paystub PDF to DigitalOcean Spaces.

        Args:
            user_id: User ID
            ledger_id: Ledger ID
            employee_id: Employee UUID
            pay_date: Pay date
            pdf_bytes: PDF file content as bytes

        Returns:
            Storage key for the uploaded file
        """
        storage_key = self._build_storage_key(
            user_id=user_id,
            ledger_id=ledger_id,
            employee_id=employee_id,
            pay_date=pay_date
        )

        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=storage_key,
                Body=pdf_bytes,
                ContentType='application/pdf',
                ContentDisposition=f'attachment; filename="{employee_id}_{pay_date.isoformat()}_paystub.pdf"'
            )

            logger.info(
                "Saved paystub to DO Spaces",
                extra={
                    "storage_key": storage_key,
                    "employee_id": str(employee_id),
                    "pay_date": pay_date.isoformat()
                }
            )

            return storage_key

        except Exception as e:
            logger.error(
                f"Failed to save paystub: {e}",
                extra={
                    "storage_key": storage_key,
                    "employee_id": str(employee_id)
                }
            )
            raise

    async def get_download_url(
        self,
        storage_key: str,
        expires_in: int = 900  # 15 minutes
    ) -> str:
        """
        Generate pre-signed URL for downloading paystub.

        Args:
            storage_key: Storage key of the paystub
            expires_in: URL expiration time in seconds (default 15 min)

        Returns:
            Pre-signed download URL
        """
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket,
                    'Key': storage_key
                },
                ExpiresIn=expires_in
            )

            return url

        except Exception as e:
            logger.error(
                f"Failed to generate download URL: {e}",
                extra={"storage_key": storage_key}
            )
            raise

    async def list_paystubs_for_employee(
        self,
        user_id: str,
        ledger_id: str,
        employee_id: UUID | str,
        year: int | None = None
    ) -> list[dict[str, Any]]:
        """
        List all paystubs for an employee.

        Args:
            user_id: User ID
            ledger_id: Ledger ID
            employee_id: Employee UUID
            year: Optional year filter

        Returns:
            List of paystub metadata:
            [{"storage_key": str, "pay_date": str, "size": int}, ...]
        """
        # Build prefix for listing
        base = self.root_prefix.rstrip('/') if self.root_prefix else ""
        prefix = f"{user_id}/{ledger_id}/payroll/paystubs/"

        if year:
            prefix = f"{prefix}{year}/"

        if base:
            prefix = f"{base}/{prefix}"

        try:
            response = self.client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=prefix
            )

            paystubs = []
            for obj in response.get('Contents', []):
                key = obj['Key']
                filename = key.split('/')[-1]

                # Filter by employee ID
                if filename.startswith(str(employee_id)):
                    # Extract pay date from filename
                    # Format: {employee_id}_{pay_date}.pdf
                    parts = filename.replace('.pdf', '').split('_')
                    if len(parts) >= 2:
                        pay_date_str = parts[-1]

                        paystubs.append({
                            'storage_key': key,
                            'pay_date': pay_date_str,
                            'size': obj['Size'],
                            'last_modified': obj['LastModified'].isoformat()
                        })

            # Sort by pay date descending
            paystubs.sort(key=lambda x: x['pay_date'], reverse=True)
            return paystubs

        except Exception as e:
            logger.error(
                f"Failed to list paystubs: {e}",
                extra={
                    "employee_id": str(employee_id),
                    "year": year
                }
            )
            return []

    async def delete_paystub(
        self,
        storage_key: str
    ) -> bool:
        """
        Delete a paystub from storage.

        Args:
            storage_key: Storage key of the paystub

        Returns:
            True if deleted successfully
        """
        try:
            self.client.delete_object(
                Bucket=self.bucket,
                Key=storage_key
            )

            logger.info(
                "Deleted paystub",
                extra={"storage_key": storage_key}
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to delete paystub: {e}",
                extra={"storage_key": storage_key}
            )
            return False

    async def paystub_exists(
        self,
        storage_key: str
    ) -> bool:
        """
        Check if paystub exists.

        Args:
            storage_key: Storage key to check

        Returns:
            True if exists
        """
        try:
            self.client.head_object(
                Bucket=self.bucket,
                Key=storage_key
            )
            return True
        except Exception:
            return False
```

USAGE EXAMPLE:
```python
from app.services.payroll.paystub_generator import PaystubGenerator
from app.services.payroll.paystub_storage import PaystubStorage

# Generate paystub
generator = PaystubGenerator()
pdf_bytes = generator.generate_paystub_bytes(
    employee_name="John Doe",
    employee_id=str(employee.id),
    sin_masked="***-***-789",
    province=Province.ON,
    employer_name="Acme Corp",
    employer_address="123 Main St, Toronto",
    period_start=date(2025, 1, 1),
    period_end=date(2025, 1, 15),
    pay_date=date(2025, 1, 17),
    record=payroll_record
)

# Upload to DO Spaces
storage = PaystubStorage()
storage_key = await storage.save_paystub(
    user_id=user_id,
    ledger_id=ledger_id,
    employee_id=employee.id,
    pay_date=date(2025, 1, 17),
    pdf_bytes=pdf_bytes
)

# Generate download URL
download_url = await storage.get_download_url(storage_key)
```
```

---

## 📦 Task 3.3: Integrate with Payroll Service

### LLM Agent Prompt

```markdown
TASK: Add Paystub Generation to Payroll Service

CONTEXT:
Integrate paystub generation and storage into the payroll approval workflow.
When a payroll run is approved, generate paystubs for all employees.

FILE TO MODIFY:
backend/app/services/payroll/payroll_service.py

ADD TO approve_payroll_run METHOD:

```python
from app.services.payroll.paystub_generator import PaystubGenerator
from app.services.payroll.paystub_storage import PaystubStorage

async def _generate_paystubs_for_run(
    self,
    user_id: str,
    ledger_id: str,
    run: PayrollRun,
    records: list[PayrollRecord],
    employees: dict[UUID, Employee],
    company_info: CompanyInfo
) -> None:
    """
    Generate and store paystubs for all employees in a payroll run.

    Args:
        user_id: User ID
        ledger_id: Ledger ID
        run: Payroll run
        records: List of payroll records
        employees: Employee lookup by ID
        company_info: Company information for employer section
    """
    generator = PaystubGenerator()
    storage = PaystubStorage()

    for record in records:
        employee = employees.get(record.employee_id)
        if not employee:
            logger.warning(f"Employee not found for record: {record.id}")
            continue

        try:
            # Generate PDF bytes
            pdf_bytes = generator.generate_paystub_bytes(
                employee_name=f"{employee.first_name} {employee.last_name}",
                employee_id=str(employee.id),
                sin_masked=employee.sin_masked,
                province=employee.province_of_employment,
                employer_name=company_info.name,
                employer_address=self._format_address(company_info),
                period_start=run.period_start,
                period_end=run.period_end,
                pay_date=run.pay_date,
                record=record
            )

            # Upload to DO Spaces
            storage_key = await storage.save_paystub(
                user_id=user_id,
                ledger_id=ledger_id,
                employee_id=employee.id,
                pay_date=run.pay_date,
                pdf_bytes=pdf_bytes
            )

            # Update record with storage key
            await self.record_repository.update_paystub_key(
                record_id=record.id,
                storage_key=storage_key
            )

            logger.info(
                "Generated paystub",
                extra={
                    "employee_id": str(employee.id),
                    "pay_date": run.pay_date.isoformat(),
                    "storage_key": storage_key
                }
            )

        except Exception as e:
            logger.error(
                f"Failed to generate paystub for employee {employee.id}: {e}",
                exc_info=True
            )
            # Continue with other employees - don't fail entire run

def _format_address(self, company_info: CompanyInfo) -> str:
    """Format company address for paystub."""
    parts = []
    if company_info.address_street:
        parts.append(company_info.address_street)
    if company_info.address_city:
        city_line = company_info.address_city
        if company_info.address_province:
            city_line += f", {company_info.address_province}"
        if company_info.address_postal_code:
            city_line += f" {company_info.address_postal_code}"
        parts.append(city_line)
    return ", ".join(parts) if parts else "Address not configured"
```

UPDATE approve_payroll_run TO CALL THE NEW METHOD:
```python
async def approve_payroll_run(self, ...):
    # ... existing validation and status checks ...

    # Generate paystubs
    await self._generate_paystubs_for_run(
        user_id=user_id,
        ledger_id=ledger_id,
        run=run,
        records=records,
        employees=employees_by_id,
        company_info=company_info
    )

    # ... continue with Beancount integration ...
```
```

---

## ✅ Validation Checklist

### PDF Output Quality
- [ ] All text is readable and properly formatted
- [ ] Tables align correctly
- [ ] No overlapping content
- [ ] Company logo (if added) renders clearly
- [ ] Page breaks correctly for multi-page paystubs

### Data Accuracy
- [ ] Gross earnings match PayrollRecord model
- [ ] All deductions itemized correctly
- [ ] Net pay = Total Gross - Total Deductions
- [ ] YTD totals accurate
- [ ] SIN masked (show last 3 digits only)

### Compliance
- [ ] All mandatory fields present
- [ ] Pay period dates clearly shown
- [ ] Employer contact info included
- [ ] Meets provincial requirements (Ontario vacation, BC employer costs)

### Storage
- [ ] PDFs upload to DigitalOcean Spaces
- [ ] Storage keys follow expected pattern
- [ ] Pre-signed URLs work (15 min expiry)
- [ ] Can list paystubs for employee
- [ ] Can filter by year

---

## 🚨 Common Issues

### Issue 1: ReportLab Import Error
**Problem**: `ModuleNotFoundError: No module named 'reportlab'`
**Solution**:
```bash
cd backend
uv add reportlab
uv sync
```

### Issue 2: Text Overflow
**Problem**: Employee name too long, breaks layout
**Solution**: Use truncation or smaller font for long names

### Issue 3: Decimal Formatting
**Problem**: Shows `$2000.0` instead of `$2000.00`
**Solution**: Always use f-string with :.2f format

### Issue 4: DO Spaces Connection Error
**Problem**: `EndpointConnectionError` when uploading
**Solution**: Verify DO Spaces credentials in `.env`:
```bash
DO_SPACES_ENDPOINT=https://nyc3.digitaloceanspaces.com
DO_SPACES_REGION=nyc3
DO_SPACES_ACCESS_KEY=your_key
DO_SPACES_SECRET_KEY=your_secret
DO_SPACES_BUCKET=your_bucket
```

### Issue 5: Pre-signed URL Expired
**Problem**: URL returns 403 after 15 minutes
**Solution**: Generate new URL for each download request (as designed)

---

**Next**: [Phase 4: API & Integration](./04_phase4_api_integration.md)
