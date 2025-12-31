"""
PD7A Remittance Voucher PDF Generator

Generates PD7A Statement of Account for Current Source Deductions.
"""

from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING, Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

if TYPE_CHECKING:
    from app.models.remittance import PD7ARemittanceVoucher


class PD7APDFGenerator:
    """Generate PD7A Remittance Voucher PDF using ReportLab."""

    def __init__(self) -> None:
        self.styles = getSampleStyleSheet()

    def generate_pdf(self, voucher: PD7ARemittanceVoucher) -> bytes:
        """
        Generate PD7A PDF.

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
            self.styles["Title"]
        )
        story.append(title)
        story.append(Spacer(1, 12))

        # Employer Information
        story.extend(self._build_employer_section(voucher))
        story.append(Spacer(1, 18))

        # Period Information
        story.extend(self._build_period_section(voucher))
        story.append(Spacer(1, 24))

        # Deductions Table
        story.extend(self._build_deductions_table(voucher))
        story.append(Spacer(1, 12))

        # Total Table
        story.extend(self._build_total_table(voucher))
        story.append(Spacer(1, 36))

        # Payment Instructions
        story.append(self._build_payment_instructions())

        # Build PDF
        doc.build(story)

        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes

    def _build_employer_section(
        self,
        voucher: PD7ARemittanceVoucher
    ) -> list[Any]:
        """Build employer information section."""
        data = [
            ["Employer Name:", voucher.employer_name],
            ["Payroll Account Number:", voucher.payroll_account_number]
        ]
        table = Table(data, colWidths=[2.5 * inch, 4 * inch])
        table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 11),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0)
        ]))
        return [table]

    def _build_period_section(
        self,
        voucher: PD7ARemittanceVoucher
    ) -> list[Any]:
        """Build period information section."""
        period_str = (
            f"{voucher.period_start.strftime('%B %d, %Y')} to "
            f"{voucher.period_end.strftime('%B %d, %Y')}"
        )
        data = [
            ["Remittance Period:", period_str],
            ["Due Date:", voucher.due_date.strftime("%B %d, %Y")]
        ]
        table = Table(data, colWidths=[2.5 * inch, 4 * inch])
        table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 11),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0)
        ]))
        return [table]

    def _build_deductions_table(
        self,
        voucher: PD7ARemittanceVoucher
    ) -> list[Any]:
        """Build Line 10 deductions table."""
        data = [
            ["Line 10: Current Source Deductions", ""],
            ["CPP - Employee Contributions", f"${voucher.line_10_cpp_employee:,.2f}"],
            ["CPP - Employer Contributions", f"${voucher.line_10_cpp_employer:,.2f}"],
            ["EI - Employee Premiums", f"${voucher.line_10_ei_employee:,.2f}"],
            ["EI - Employer Premiums", f"${voucher.line_10_ei_employer:,.2f}"],
            ["Income Tax (Federal + Provincial)", f"${voucher.line_10_income_tax:,.2f}"]
        ]

        table = Table(data, colWidths=[4.5 * inch, 2 * inch])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#333333")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 11),
            ("ALIGN", (1, 1), (1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6)
        ]))
        return [table]

    def _build_total_table(
        self,
        voucher: PD7ARemittanceVoucher
    ) -> list[Any]:
        """Build Line 11-13 total tables."""
        tables = []

        # Line 11: Total
        total_data = [[
            "Line 11: Total Current Source Deductions",
            f"${voucher.line_11_total_deductions:,.2f}"
        ]]
        total_table = Table(total_data, colWidths=[4.5 * inch, 2 * inch])
        total_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0f0f0")),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 12),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8)
        ]))
        tables.append(total_table)

        # Line 12 & 13 (if previous balance exists)
        if voucher.line_12_previous_balance > 0:
            tables.append(Spacer(1, 12))
            balance_data = [
                [
                    "Line 12: Previous Balance Owing",
                    f"${voucher.line_12_previous_balance:,.2f}"
                ],
                [
                    "Line 13: Total Amount Due",
                    f"${voucher.line_13_total_due:,.2f}"
                ]
            ]
            balance_table = Table(balance_data, colWidths=[4.5 * inch, 2 * inch])
            balance_table.setStyle(TableStyle([
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica"),
                ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 12),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#ffcccc")),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6)
            ]))
            tables.append(balance_table)

        return tables

    def _build_payment_instructions(self) -> Paragraph:
        """Build payment instructions section."""
        return Paragraph(
            "<b>Payment Instructions:</b><br/><br/>"
            "1. Pay online through CRA My Business Account (recommended)<br/>"
            "2. Pre-authorized debit through CRA<br/>"
            "3. Wire transfer to CRA account<br/>"
            "4. Mail cheque with this voucher to:<br/>"
            "&nbsp;&nbsp;&nbsp;&nbsp;Sudbury Tax Centre<br/>"
            "&nbsp;&nbsp;&nbsp;&nbsp;1050 Notre Dame Avenue<br/>"
            "&nbsp;&nbsp;&nbsp;&nbsp;Sudbury ON P3A 5C1",
            self.styles["Normal"]
        )
