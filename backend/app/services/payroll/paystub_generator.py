"""Paystub PDF generator using ReportLab."""

from decimal import Decimal
from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.models.paystub import PaystubData


class PaystubGenerator:
    """Generate PDF paystubs using ReportLab.

    Layout matches the reference image (Test/Haifeng-paystub.png):
    - Header with employee info and pay period
    - Earnings table
    - Non-taxable Company Items (employer contributions)
    - Taxes section
    - Adjustments to Net Pay (employee deductions)
    - Net Pay
    - Vacation section
    - Taxable Company Items (employer life insurance)
    - Footer with company address
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
                fontSize=9,
                fontName="Helvetica-Bold",
                spaceAfter=2,
            )
        )
        self.styles.add(
            ParagraphStyle(
                "TableText",
                parent=self.styles["Normal"],
                fontSize=8,
                fontName="Helvetica",
            )
        )
        self.styles.add(
            ParagraphStyle(
                "CompanyName",
                parent=self.styles["Normal"],
                fontSize=10,
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

        # Build all sections
        self._build_memo_section(elements, data)
        elements.append(Spacer(1, 12))
        self._build_header_section(elements, data)
        elements.append(Spacer(1, 8))
        self._build_earnings_and_benefits_section(elements, data)
        elements.append(Spacer(1, 6))
        self._build_taxes_section(elements, data)
        elements.append(Spacer(1, 6))
        self._build_adjustments_section(elements, data)
        elements.append(Spacer(1, 6))
        self._build_net_pay_section(elements, data)
        elements.append(Spacer(1, 6))
        self._build_vacation_section(elements, data)
        elements.append(Spacer(1, 6))
        self._build_taxable_benefits_section(elements, data)
        elements.append(Spacer(1, 12))
        self._build_footer_section(elements, data)

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

    def _build_memo_section(self, elements: list[Any], data: PaystubData) -> None:
        """Build MEMO section with employee name and pay period."""
        # Employee name and address at top
        elements.append(Paragraph(data.employeeName, self.styles["Normal"]))
        if data.employeeAddress:
            for line in data.employeeAddress.split("\n"):
                elements.append(Paragraph(line, self.styles["Normal"]))

        elements.append(Spacer(1, 8))

        # MEMO line
        period_str = f"{data.periodStart.strftime('%m/%d/%Y')} - {data.periodEnd.strftime('%m/%d/%Y')}"
        memo_text = data.memo or f"Pay Period: {period_str}"
        memo_table = Table(
            [["MEMO", memo_text]],
            colWidths=[0.6 * inch, 5 * inch],
        )
        memo_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        elements.append(memo_table)

    def _build_header_section(self, elements: list[Any], data: PaystubData) -> None:
        """Build header with employee info and pay period details."""
        # Two-column header: Employee info | Occupation/Period/Date
        period_str = f"{data.periodStart.strftime('%m/%d/%Y')} - {data.periodEnd.strftime('%m/%d/%Y')}"
        pay_date_str = data.payDate.strftime("%m/%d/%Y")

        # Build address string
        address_lines = data.employeeAddress.split("\n") if data.employeeAddress else []
        employee_info = f"<b>Employee</b><br/>{data.employeeName}"
        if address_lines:
            employee_info += "<br/>" + "<br/>".join(address_lines)

        occupation_info = f"<b>Occupation</b><br/>{data.occupation or ''}"
        period_info = f"<b>Pay Period:</b> {period_str}<br/><b>Cheque Date:</b> {pay_date_str}"

        header_data = [
            [
                Paragraph(employee_info, self.styles["TableText"]),
                Paragraph(occupation_info, self.styles["TableText"]),
            ],
            [
                "",
                Paragraph(period_info, self.styles["TableText"]),
            ],
        ]

        header_table = Table(header_data, colWidths=[3.5 * inch, 3.5 * inch])
        header_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LINEBELOW", (0, -1), (-1, -1), 0.5, colors.black),
                ]
            )
        )
        elements.append(header_table)

    def _build_earnings_and_benefits_section(self, elements: list[Any], data: PaystubData) -> None:
        """Build earnings table and non-taxable benefits side by side."""
        # Left side: Earnings
        earnings_header = ["Earnings and Hours", "Qty", "Rate", "Current", "YTD Amount"]
        earnings_rows = [earnings_header]

        for earning in data.earnings:
            earnings_rows.append(
                [
                    earning.description,
                    earning.qty or "",
                    self._format_currency(earning.rate) if earning.rate else "",
                    self._format_currency(earning.current),
                    self._format_currency(earning.ytd),
                ]
            )

        # Add total row if multiple earnings
        if len(data.earnings) > 1:
            earnings_rows.append(
                [
                    "",
                    "",
                    "",
                    self._format_currency(data.totalEarnings),
                    self._format_currency(data.ytdEarnings),
                ]
            )

        # Right side: Non-taxable Company Items
        benefits_header = ["Non-taxable Company Items", "Current", "YTD Amount"]
        benefits_rows = [benefits_header]

        for benefit in data.nonTaxableBenefits:
            benefits_rows.append(
                [
                    benefit.description,
                    self._format_currency(benefit.current),
                    self._format_currency(benefit.ytd),
                ]
            )

        # Create side-by-side tables
        earnings_table = Table(
            earnings_rows, colWidths=[1.5 * inch, 0.6 * inch, 0.6 * inch, 0.8 * inch, 0.9 * inch]
        )
        earnings_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
                    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )

        if data.nonTaxableBenefits:
            benefits_table = Table(benefits_rows, colWidths=[1.8 * inch, 0.8 * inch, 0.9 * inch])
            benefits_table.setStyle(
                TableStyle(
                    [
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 8),
                        ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
                        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                        ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ]
                )
            )

            # Combine into side-by-side layout
            combined_table = Table(
                [[earnings_table, benefits_table]], colWidths=[4.5 * inch, 3.5 * inch]
            )
            combined_table.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ]
                )
            )
            elements.append(combined_table)
        else:
            elements.append(earnings_table)

    def _build_taxes_section(self, elements: list[Any], data: PaystubData) -> None:
        """Build taxes deduction section."""
        if not data.taxes:
            return

        tax_header = ["Taxes", "Current", "YTD Amount"]
        tax_rows = [tax_header]

        for tax in data.taxes:
            tax_rows.append(
                [
                    tax.description,
                    self._format_currency(tax.current),
                    self._format_currency(tax.ytd),
                ]
            )

        # Add total row
        tax_rows.append(
            [
                "",
                self._format_currency(data.totalTaxes),
                self._format_currency(data.ytdTaxes),
            ]
        )

        tax_table = Table(tax_rows, colWidths=[2.5 * inch, 0.9 * inch, 0.9 * inch])
        tax_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
                    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        elements.append(tax_table)

    def _build_adjustments_section(self, elements: list[Any], data: PaystubData) -> None:
        """Build adjustments to net pay section (employee benefit deductions)."""
        if not data.benefitDeductions:
            return

        adj_header = ["Adjustments to Net Pay", "Current", "YTD Amount"]
        adj_rows = [adj_header]

        for deduction in data.benefitDeductions:
            adj_rows.append(
                [
                    deduction.description,
                    self._format_currency(deduction.current),
                    self._format_currency(deduction.ytd),
                ]
            )

        # Add total row
        adj_rows.append(
            [
                "",
                self._format_currency(data.totalBenefitDeductions),
                self._format_currency(data.ytdBenefitDeductions),
            ]
        )

        adj_table = Table(adj_rows, colWidths=[2.5 * inch, 0.9 * inch, 0.9 * inch])
        adj_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
                    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        elements.append(adj_table)

    def _build_net_pay_section(self, elements: list[Any], data: PaystubData) -> None:
        """Build net pay section."""
        net_pay_data = [
            [
                "Net Pay",
                self._format_currency(data.netPay),
                self._format_currency(data.ytdNetPay) if data.ytdNetPay is not None else "",
            ]
        ]

        net_pay_table = Table(net_pay_data, colWidths=[2.5 * inch, 0.9 * inch, 0.9 * inch])
        net_pay_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LINEABOVE", (0, 0), (-1, 0), 0.5, colors.black),
                    ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        elements.append(net_pay_table)

    def _build_vacation_section(self, elements: list[Any], data: PaystubData) -> None:
        """Build vacation/sick hours section."""
        if not data.vacation:
            return

        vac_header = ["Sick Hours and Vacation Pay", "Earned", "YTD Used", "Available"]
        vac_data = [
            vac_header,
            [
                "Vacation ($)",
                self._format_currency(data.vacation.earned),
                self._format_currency(data.vacation.ytdUsed)
                if data.vacation.ytdUsed is not None
                else "",
                self._format_currency(data.vacation.available),
            ],
        ]

        vac_table = Table(vac_data, colWidths=[2 * inch, 0.8 * inch, 0.8 * inch, 0.9 * inch])
        vac_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
                    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        elements.append(vac_table)

    def _build_taxable_benefits_section(self, elements: list[Any], data: PaystubData) -> None:
        """Build taxable company items section (employer-paid life insurance)."""
        if not data.taxableBenefits:
            return

        taxable_header = ["Taxable Company Items", "Current", "YTD Amount"]
        taxable_rows = [taxable_header]

        for benefit in data.taxableBenefits:
            taxable_rows.append(
                [
                    benefit.description,
                    self._format_currency(benefit.current),
                    self._format_currency(benefit.ytd),
                ]
            )

        taxable_table = Table(taxable_rows, colWidths=[2.5 * inch, 0.9 * inch, 0.9 * inch])
        taxable_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
                    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        elements.append(taxable_table)

    def _build_footer_section(self, elements: list[Any], data: PaystubData) -> None:
        """Build footer with company name and address."""
        elements.append(Paragraph(data.employerName, self.styles["CompanyName"]))
        elements.append(Paragraph(data.employerAddress, self.styles["Normal"]))
