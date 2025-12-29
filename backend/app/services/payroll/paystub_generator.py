"""Paystub PDF generator using ReportLab.

Layout follows the Avalon reference template with:
- Header: Company logo/name on left, "PAY STUB" title on right
- Employer/Employee info in two columns
- Pay details section with rate, period, date, accrued vacation
- INCOME section with gross pay
- DEDUCTIONS section (taxes + benefit deductions)
- NET PAY row
- Optional: Employer Contributions, Vacation Details
"""

import logging
from decimal import Decimal
from io import BytesIO
from typing import Any

import httpx
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.models.paystub import PaystubData

logger = logging.getLogger(__name__)


class PaystubGenerator:
    """Generate PDF paystubs using ReportLab.

    Layout follows the Avalon reference template:
    - Header with company logo and PAY STUB title
    - Employer/Employee info columns
    - Pay details (rate, period, date, accrued vacation)
    - INCOME table with GROSS PAY total
    - DEDUCTIONS table with totals
    - NET PAY row
    - Optional: Employer Contributions, Vacation Details
    """

    def __init__(self) -> None:
        """Initialize generator with styles."""
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self) -> None:
        """Set up custom paragraph styles."""
        self.styles.add(
            ParagraphStyle(
                "SectionHeader",
                parent=self.styles["Normal"],
                fontSize=10,
                fontName="Helvetica-Bold",
                spaceAfter=4,
            )
        )
        self.styles.add(
            ParagraphStyle(
                "TableText",
                parent=self.styles["Normal"],
                fontSize=9,
                fontName="Helvetica",
            )
        )
        self.styles.add(
            ParagraphStyle(
                "CompanyName",
                parent=self.styles["Normal"],
                fontSize=12,
                fontName="Helvetica-Bold",
            )
        )
        self.styles.add(
            ParagraphStyle(
                "PayStubTitle",
                parent=self.styles["Normal"],
                fontSize=16,
                fontName="Helvetica-Bold",
            )
        )
        self.styles.add(
            ParagraphStyle(
                "LabelStyle",
                parent=self.styles["Normal"],
                fontSize=9,
                fontName="Helvetica-Bold",
            )
        )

    def generate_paystub_bytes(self, data: PaystubData) -> bytes:
        """Generate paystub PDF and return as bytes.

        Args:
            data: PaystubData containing all paystub information

        Returns:
            PDF file contents as bytes
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.5 * inch,
            leftMargin=0.5 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
        )

        elements: list[Any] = []

        # Build all sections in order
        self._build_header_section(elements, data)
        elements.append(Spacer(1, 16))
        self._build_employer_employee_section(elements, data)
        elements.append(Spacer(1, 12))
        self._build_pay_details_section(elements, data)
        elements.append(Spacer(1, 16))
        self._build_income_section(elements, data)
        elements.append(Spacer(1, 12))
        self._build_deductions_section(elements, data)
        elements.append(Spacer(1, 8))
        self._build_net_pay_section(elements, data)

        # Optional sections
        if data.nonTaxableBenefits or data.taxableBenefits:
            elements.append(Spacer(1, 12))
            self._build_employer_contributions_section(elements, data)

        if data.vacation or data.sickLeave:
            elements.append(Spacer(1, 12))
            self._build_leave_balances_section(elements, data)

        doc.build(elements)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    def _format_currency(self, value: Decimal, show_negative: bool = True) -> str:
        """Format decimal as currency string.

        Args:
            value: Decimal value to format
            show_negative: If True, show minus sign for negative values

        Returns:
            Formatted string like "1,234.56" or "-1,234.56"
        """
        if value < 0 and show_negative:
            return f"-{abs(value):,.2f}"
        return f"{abs(value):,.2f}"

    def _download_logo(self, url: str) -> BytesIO | None:
        """Download logo image from URL.

        Args:
            url: URL to the logo image

        Returns:
            BytesIO buffer containing the image, or None if download fails
        """
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url)
                response.raise_for_status()
                return BytesIO(response.content)
        except Exception as e:
            logger.warning("Failed to download logo from %s: %s", url, e)
            return None

    def _build_header_section(self, elements: list[Any], data: PaystubData) -> None:
        """Build header with company logo/name on left and PAY STUB title on right."""
        # Build left side content (logo or company name)
        left_content: list[Any] = []

        # Use pre-downloaded logo bytes if available, otherwise download from URL
        logo_buffer: BytesIO | None = None
        if data.logoBytes:
            logo_buffer = BytesIO(data.logoBytes)
        elif data.logoUrl:
            logo_buffer = self._download_logo(data.logoUrl)

        if logo_buffer:
            try:
                # Get actual image dimensions and scale proportionally
                logo_buffer.seek(0)
                pil_img = PILImage.open(logo_buffer)
                orig_width_px, orig_height_px = pil_img.size

                # Get DPI from image metadata (default to 72 if not specified)
                dpi_info = pil_img.info.get("dpi", (72, 72))
                dpi_x = dpi_info[0] if isinstance(dpi_info, tuple) else 72
                dpi_y = dpi_info[1] if isinstance(dpi_info, tuple) else 72

                # Validate DPI values - prevent division by zero
                if not dpi_x or dpi_x <= 0:
                    dpi_x = 72
                if not dpi_y or dpi_y <= 0:
                    dpi_y = 72

                # Convert pixel dimensions to points (72 points per inch)
                # points = pixels * 72 / dpi
                orig_width_pts = orig_width_px * 72 / dpi_x
                orig_height_pts = orig_height_px * 72 / dpi_y

                # Scale to fit within max bounds while preserving aspect ratio
                max_width = 2 * inch
                max_height = 1 * inch
                scale = min(max_width / orig_width_pts, max_height / orig_height_pts)
                final_width = orig_width_pts * scale
                final_height = orig_height_pts * scale

                logo_buffer.seek(0)
                img = Image(logo_buffer, width=final_width, height=final_height)
                img.hAlign = "LEFT"
                left_content.append(img)
            except Exception as e:
                logger.warning("Failed to render logo: %s", e)
                # Fallback to company name
                left_content.append(
                    Paragraph(f"<b>{data.employerName}</b>", self.styles["CompanyName"])
                )
        else:
            # No logo available, use company name
            left_content.append(
                Paragraph(f"<b>{data.employerName}</b>", self.styles["CompanyName"])
            )

        # Build right side content (PAY STUB title) - right-aligned
        paystub_title_style = ParagraphStyle(
            "PayStubTitleRight",
            parent=self.styles["PayStubTitle"],
            alignment=TA_RIGHT,
        )
        right_content = [Paragraph("<b>PAY STUB</b>", paystub_title_style)]

        # Create header table with logo/company on left, title on right
        header_row = [left_content, right_content]
        header_table = Table(
            [header_row],
            colWidths=[5 * inch, 2.5 * inch],
        )
        header_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (0, 0), (0, 0), "LEFT"),
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ]
            )
        )
        elements.append(header_table)

    def _build_employer_employee_section(
        self, elements: list[Any], data: PaystubData
    ) -> None:
        """Build employer/employee info in two columns."""
        # Create right-aligned style for employee info
        employee_label_style = ParagraphStyle(
            "EmployeeLabelRight",
            parent=self.styles["LabelStyle"],
            alignment=TA_RIGHT,
        )
        employee_text_style = ParagraphStyle(
            "EmployeeTextRight",
            parent=self.styles["TableText"],
            alignment=TA_RIGHT,
        )

        # Left column: Employer info (left-aligned)
        employer_lines = [
            Paragraph("<b>EMPLOYER NAME/ADDRESS:</b>", self.styles["LabelStyle"]),
            Paragraph(data.employerName, self.styles["TableText"]),
        ]
        if data.employerAddress:
            for line in data.employerAddress.split("\n"):
                employer_lines.append(Paragraph(line, self.styles["TableText"]))

        # Right column: Employee info (right-aligned)
        employee_lines = [
            Paragraph("<b>EMPLOYEE NAME/ADDRESS:</b>", employee_label_style),
            Paragraph(data.employeeName, employee_text_style),
        ]
        if data.employeeAddress:
            for line in data.employeeAddress.split("\n"):
                employee_lines.append(Paragraph(line, employee_text_style))

        # Create two-column table (4" + 3.5" = 7.5" total width)
        info_table = Table(
            [[employer_lines, employee_lines]],
            colWidths=[4 * inch, 3.5 * inch],
        )
        info_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (0, 0), (0, 0), "LEFT"),
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ]
            )
        )
        elements.append(info_table)

    def _build_pay_details_section(self, elements: list[Any], data: PaystubData) -> None:
        """Build pay details section with rate, period, date, accrued vacation."""
        details_rows: list[list[str]] = []

        # Pay Rate (if available)
        if data.payRate:
            details_rows.append(["Pay Rate:", data.payRate])

        # Pay Period (Cycle)
        period_str = f"{data.periodStart.strftime('%Y-%m-%d')} - {data.periodEnd.strftime('%Y-%m-%d')}"
        details_rows.append(["Pay Period:", period_str])

        # Pay Date
        pay_date_str = data.payDate.strftime("%Y-%m-%d")
        details_rows.append(["Pay Date:", pay_date_str])

        # Accrued Vacation (if available)
        if data.vacation and data.vacation.available > 0:
            details_rows.append(
                ["Accrued Vacation:", f"${self._format_currency(data.vacation.available)}"]
            )

        if not details_rows:
            return

        details_table = Table(
            details_rows,
            colWidths=[1.5 * inch, 3 * inch],
            hAlign="LEFT",  # Align table to left edge of page
        )
        details_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),  # Left-align cell content
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        elements.append(details_table)

    def _build_income_section(self, elements: list[Any], data: PaystubData) -> None:
        """Build INCOME section with earnings and GROSS PAY total."""
        # Header row
        income_header = ["INCOME", "CURRENT HOURS", "CURRENT AMOUNT", "YEAR-TO-DATE"]
        income_rows = [income_header]

        # Earnings rows
        for earning in data.earnings:
            # For salaried employees, show "-" in hours column
            hours_display = earning.qty if earning.qty else "-"

            income_rows.append(
                [
                    earning.description,
                    hours_display,
                    self._format_currency(earning.current),
                    self._format_currency(earning.ytd),
                ]
            )

        # GROSS PAY row
        gross_pay_row = [
            "GROSS PAY",
            "",
            self._format_currency(data.totalEarnings),
            self._format_currency(data.ytdEarnings),
        ]

        income_table = Table(
            income_rows,
            colWidths=[3 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch],  # 7.5" total
        )
        income_table.setStyle(
            TableStyle(
                [
                    # Header styling
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
                    # Data alignment
                    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        elements.append(income_table)

        # GROSS PAY row as separate table with top border
        gross_table = Table(
            [gross_pay_row],
            colWidths=[3 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch],  # 7.5" total
        )
        gross_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("LINEABOVE", (0, 0), (-1, 0), 0.5, colors.black),
                    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        elements.append(gross_table)

    def _build_deductions_section(self, elements: list[Any], data: PaystubData) -> None:
        """Build DEDUCTIONS section combining taxes and benefit deductions."""
        # Header row
        deduction_header = ["DEDUCTIONS", "CURRENT AMOUNT", "YEAR-TO-DATE"]
        deduction_rows = [deduction_header]

        # Tax lines (with renamed descriptions for clarity)
        tax_name_map = {
            "CPP": "Federal Employee CPP",
            "EI": "Federal Employee EI",
            "Federal Tax": "Federal Income Tax",
            "Provincial Tax": "Provincial Income Tax",
        }

        for tax in data.taxes:
            display_name = tax_name_map.get(tax.description, tax.description)
            deduction_rows.append(
                [
                    display_name,
                    self._format_currency(abs(tax.current)),
                    self._format_currency(abs(tax.ytd)),
                ]
            )

        # Benefit deduction lines (employee portions)
        for deduction in data.benefitDeductions:
            # Remove "- Employee" suffix for cleaner display
            display_name = deduction.description.replace(" - Employee", "")
            deduction_rows.append(
                [
                    display_name,
                    self._format_currency(abs(deduction.current)),
                    self._format_currency(abs(deduction.ytd)),
                ]
            )

        # Calculate total deductions
        total_current = abs(data.totalTaxes) + abs(data.totalBenefitDeductions)
        total_ytd = abs(data.ytdTaxes) + abs(data.ytdBenefitDeductions)

        deduction_table = Table(
            deduction_rows,
            colWidths=[4.5 * inch, 1.5 * inch, 1.5 * inch],  # 7.5" total
        )
        deduction_table.setStyle(
            TableStyle(
                [
                    # Header styling
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
                    # Data alignment
                    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        elements.append(deduction_table)

        # DEDUCTION TOTALS row as separate table with top border
        totals_row = [
            "DEDUCTION TOTALS",
            self._format_currency(total_current),
            self._format_currency(total_ytd),
        ]
        totals_table = Table(
            [totals_row],
            colWidths=[4.5 * inch, 1.5 * inch, 1.5 * inch],  # 7.5" total
        )
        totals_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("LINEABOVE", (0, 0), (-1, 0), 0.5, colors.black),
                    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        elements.append(totals_table)

    def _build_net_pay_section(self, elements: list[Any], data: PaystubData) -> None:
        """Build NET PAY row."""
        net_pay_row = [
            "NET PAY",
            self._format_currency(data.netPay),
            self._format_currency(data.ytdNetPay) if data.ytdNetPay is not None else "",
        ]

        net_pay_table = Table(
            [net_pay_row],
            colWidths=[4.5 * inch, 1.5 * inch, 1.5 * inch],  # 7.5" total
        )
        net_pay_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        elements.append(net_pay_table)

    def _build_employer_contributions_section(
        self, elements: list[Any], data: PaystubData
    ) -> None:
        """Build optional Employer Contributions section (non-taxable + taxable benefits)."""
        if not data.nonTaxableBenefits and not data.taxableBenefits:
            return

        # Header row - with TAXABLE column
        contrib_header = ["EMPLOYER CONTRIBUTIONS", "TAXABLE", "CURRENT AMOUNT", "YEAR-TO-DATE"]
        contrib_rows = [contrib_header]

        # Non-taxable benefits
        for benefit in data.nonTaxableBenefits:
            display_name = benefit.description.replace(" - Employer", "")
            contrib_rows.append(
                [
                    display_name,
                    "No",
                    self._format_currency(benefit.current),
                    self._format_currency(benefit.ytd),
                ]
            )

        # Taxable benefits
        for benefit in data.taxableBenefits:
            display_name = benefit.description.replace(" - Employer", "")
            contrib_rows.append(
                [
                    display_name,
                    "Yes",
                    self._format_currency(benefit.current),
                    self._format_currency(benefit.ytd),
                ]
            )

        contrib_table = Table(
            contrib_rows,
            colWidths=[3 * inch, 1 * inch, 1.5 * inch, 2 * inch],  # 7.5" total
        )
        contrib_table.setStyle(
            TableStyle(
                [
                    # Header styling
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
                    # Data alignment
                    ("ALIGN", (1, 0), (1, -1), "CENTER"),  # TAXABLE column centered
                    ("ALIGN", (2, 0), (-1, -1), "RIGHT"),  # Amount columns right-aligned
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        elements.append(contrib_table)

    def _build_leave_balances_section(
        self, elements: list[Any], data: PaystubData
    ) -> None:
        """Build leave balances section (Vacation + Sick Leave)."""
        if not data.vacation and not data.sickLeave:
            return

        header = ["LEAVE BALANCES", "EARNED", "YTD USED", "AVAILABLE"]
        rows = [header]

        # Add vacation row if available
        if data.vacation:
            rows.append([
                "Vacation ($)",
                self._format_currency(data.vacation.earned),
                self._format_currency(data.vacation.ytdUsed)
                if data.vacation.ytdUsed is not None
                else "0.00",
                self._format_currency(data.vacation.available),
            ])

        # Add sick leave row if available
        if data.sickLeave:
            rows.append([
                "Sick Leave (days)",
                "-",  # Sick leave doesn't show "earned"
                f"{data.sickLeave.daysUsedYtd:.1f}",
                f"{data.sickLeave.paidDaysRemaining:.1f}",
            ])

        leave_table = Table(
            rows,
            colWidths=[3 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch],  # 7.5" total
        )
        leave_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
                    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        elements.append(leave_table)
