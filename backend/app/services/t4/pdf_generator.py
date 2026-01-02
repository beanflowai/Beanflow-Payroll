"""
T4 PDF Generator

Generates T4 Statement of Remuneration Paid PDFs using ReportLab.
Follows CRA T4 form layout with employer/employee info and T4 boxes.
"""

from __future__ import annotations

from decimal import Decimal
from io import BytesIO
from typing import TYPE_CHECKING, Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

if TYPE_CHECKING:
    from app.models.t4 import T4SlipData, T4Summary


class T4PDFGenerator:
    """Generate T4 Statement of Remuneration Paid PDFs using ReportLab."""

    def __init__(self) -> None:
        """Initialize generator with styles."""
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self) -> None:
        """Set up custom paragraph styles for T4."""
        self.styles.add(
            ParagraphStyle(
                "T4Title",
                parent=self.styles["Normal"],
                fontSize=14,
                fontName="Helvetica-Bold",
                alignment=TA_CENTER,
                spaceAfter=6,
            )
        )
        self.styles.add(
            ParagraphStyle(
                "T4Subtitle",
                parent=self.styles["Normal"],
                fontSize=10,
                fontName="Helvetica",
                alignment=TA_CENTER,
                spaceAfter=12,
            )
        )
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
                "BoxLabel",
                parent=self.styles["Normal"],
                fontSize=8,
                fontName="Helvetica",
            )
        )
        self.styles.add(
            ParagraphStyle(
                "BoxValue",
                parent=self.styles["Normal"],
                fontSize=10,
                fontName="Helvetica-Bold",
                alignment=TA_RIGHT,
            )
        )

    def generate_t4_slip_pdf(self, slip: T4SlipData) -> bytes:
        """
        Generate a T4 slip PDF.

        Args:
            slip: T4SlipData containing all T4 information

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

        # Title
        self._build_title_section(elements, slip)
        elements.append(Spacer(1, 12))

        # Employer Information
        self._build_employer_section(elements, slip)
        elements.append(Spacer(1, 12))

        # Employee Information
        self._build_employee_section(elements, slip)
        elements.append(Spacer(1, 16))

        # T4 Boxes
        self._build_boxes_section(elements, slip)
        elements.append(Spacer(1, 16))

        # Province of Employment
        self._build_province_section(elements, slip)
        elements.append(Spacer(1, 24))

        # Footer
        self._build_footer_section(elements, slip)

        doc.build(elements)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    def _build_title_section(self, elements: list[Any], slip: T4SlipData) -> None:
        """Build the T4 title section."""
        title = Paragraph(
            "T4 - Statement of Remuneration Paid",
            self.styles["T4Title"]
        )
        elements.append(title)

        subtitle = Paragraph(
            f"Tax Year {slip.tax_year}",
            self.styles["T4Subtitle"]
        )
        elements.append(subtitle)

    def _build_employer_section(self, elements: list[Any], slip: T4SlipData) -> None:
        """Build employer information section."""
        elements.append(Paragraph("EMPLOYER", self.styles["SectionHeader"]))

        address_parts = [slip.employer_name]
        if slip.employer_address_line1:
            address_parts.append(slip.employer_address_line1)
        if slip.employer_city and slip.employer_province:
            address_parts.append(
                f"{slip.employer_city}, {slip.employer_province.value} "
                f"{slip.employer_postal_code or ''}"
            )

        data = [
            ["Name and Address:", "\n".join(address_parts)],
            ["Payroll Account Number:", slip.employer_account_number],
        ]

        table = Table(data, colWidths=[2 * inch, 5 * inch])
        table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(table)

    def _build_employee_section(self, elements: list[Any], slip: T4SlipData) -> None:
        """Build employee information section."""
        elements.append(Paragraph("EMPLOYEE", self.styles["SectionHeader"]))

        address_parts = [slip.employee_full_name]
        if slip.employee_address_line1:
            address_parts.append(slip.employee_address_line1)
        if slip.employee_city and slip.employee_province:
            address_parts.append(
                f"{slip.employee_city}, {slip.employee_province.value} "
                f"{slip.employee_postal_code or ''}"
            )

        data = [
            ["Name and Address:", "\n".join(address_parts)],
            ["Social Insurance Number:", slip.sin_formatted],
        ]

        table = Table(data, colWidths=[2 * inch, 5 * inch])
        table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(table)

    def _build_boxes_section(self, elements: list[Any], slip: T4SlipData) -> None:
        """Build the T4 boxes section with all income and deduction boxes."""
        elements.append(Paragraph("T4 BOXES", self.styles["SectionHeader"]))

        # Main T4 boxes in a structured layout
        box_data = [
            # Header row
            ["Box", "Description", "Amount"],
            # Income
            ["14", "Employment income", self._format_currency(slip.box_14_employment_income)],
            # Deductions
            ["16", "Employee's CPP contributions", self._format_currency(slip.box_16_cpp_contributions)],
            ["17", "Employee's CPP2 contributions", self._format_currency(slip.box_17_cpp2_contributions)],
            ["18", "Employee's EI premiums", self._format_currency(slip.box_18_ei_premiums)],
            ["22", "Income tax deducted", self._format_currency(slip.box_22_income_tax_deducted)],
            # Insurable/Pensionable earnings
            ["24", "EI insurable earnings", self._format_currency(slip.box_24_ei_insurable_earnings)],
            ["26", "CPP/QPP pensionable earnings", self._format_currency(slip.box_26_cpp_pensionable_earnings)],
        ]

        # Add optional boxes if they have values
        if slip.box_20_rpp_contributions:
            box_data.append(["20", "RPP contributions", self._format_currency(slip.box_20_rpp_contributions)])

        if slip.box_44_union_dues:
            box_data.append(["44", "Union dues", self._format_currency(slip.box_44_union_dues)])

        if slip.box_46_charitable_donations:
            box_data.append(["46", "Charitable donations", self._format_currency(slip.box_46_charitable_donations)])

        if slip.box_52_pension_adjustment:
            box_data.append(["52", "Pension adjustment", self._format_currency(slip.box_52_pension_adjustment)])

        table = Table(box_data, colWidths=[0.6 * inch, 4 * inch, 1.5 * inch])
        table.setStyle(TableStyle([
            # Header row
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#333333")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            # Data rows
            ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (1, 1), (1, -1), "Helvetica"),
            ("FONTNAME", (2, 1), (2, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 1), (-1, -1), 10),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("ALIGN", (2, 0), (2, -1), "RIGHT"),
            # Box 14 highlight (Employment income)
            ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#f0f0f0")),
            # Grid
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(table)

    def _build_province_section(self, elements: list[Any], slip: T4SlipData) -> None:
        """Build province of employment section."""
        data = [
            ["Province of Employment (Box 10):", slip.province_of_employment.value],
        ]

        # Add exemption flags if applicable
        exemptions = []
        if slip.cpp_exempt:
            exemptions.append("CPP Exempt")
        if slip.ei_exempt:
            exemptions.append("EI Exempt")

        if exemptions:
            data.append(["Exemptions:", ", ".join(exemptions)])

        table = Table(data, colWidths=[2.5 * inch, 4.5 * inch])
        table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(table)

    def _build_footer_section(self, elements: list[Any], slip: T4SlipData) -> None:
        """Build footer with instructions."""
        footer_text = (
            "This is your copy of the T4 - Statement of Remuneration Paid. "
            "Keep this slip with your tax records. You will need the information "
            "on this slip to complete your income tax return."
        )
        elements.append(Paragraph(footer_text, self.styles["Normal"]))

    def generate_t4_summary_pdf(
        self,
        summary: T4Summary,
        slips: list[T4SlipData] | None = None,
    ) -> bytes:
        """
        Generate a T4 Summary PDF.

        Args:
            summary: T4Summary data
            slips: Optional list of T4 slips for detailed breakdown

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

        # Title
        title = Paragraph(
            "T4 Summary - Statement of Remuneration Paid",
            self.styles["T4Title"]
        )
        elements.append(title)

        subtitle = Paragraph(
            f"Tax Year {summary.tax_year}",
            self.styles["T4Subtitle"]
        )
        elements.append(subtitle)
        elements.append(Spacer(1, 12))

        # Employer Information
        self._build_summary_employer_section(elements, summary)
        elements.append(Spacer(1, 16))

        # Summary Totals
        self._build_summary_totals_section(elements, summary)
        elements.append(Spacer(1, 16))

        # Employer Contributions
        self._build_employer_contributions_section(elements, summary)
        elements.append(Spacer(1, 16))

        # Total Remittance
        self._build_remittance_section(elements, summary)

        doc.build(elements)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    def _build_summary_employer_section(
        self,
        elements: list[Any],
        summary: T4Summary,
    ) -> None:
        """Build employer information for summary."""
        elements.append(Paragraph("EMPLOYER INFORMATION", self.styles["SectionHeader"]))

        address_parts = [summary.employer_name]
        if summary.employer_address_line1:
            address_parts.append(summary.employer_address_line1)
        if summary.employer_city and summary.employer_province:
            address_parts.append(
                f"{summary.employer_city}, {summary.employer_province.value} "
                f"{summary.employer_postal_code or ''}"
            )

        data = [
            ["Name and Address:", "\n".join(address_parts)],
            ["Payroll Account Number:", summary.employer_account_number],
            ["Number of T4 Slips:", str(summary.total_number_of_t4_slips)],
        ]

        table = Table(data, colWidths=[2.5 * inch, 4.5 * inch])
        table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(table)

    def _build_summary_totals_section(
        self,
        elements: list[Any],
        summary: T4Summary,
    ) -> None:
        """Build summary totals table."""
        elements.append(Paragraph("EMPLOYEE TOTALS", self.styles["SectionHeader"]))

        data = [
            ["Description", "Total"],
            ["Total Employment Income (Box 14)", self._format_currency(summary.total_employment_income)],
            ["Total CPP Contributions (Box 16)", self._format_currency(summary.total_cpp_contributions)],
            ["Total CPP2 Contributions (Box 17)", self._format_currency(summary.total_cpp2_contributions)],
            ["Total EI Premiums (Box 18)", self._format_currency(summary.total_ei_premiums)],
            ["Total Income Tax Deducted (Box 22)", self._format_currency(summary.total_income_tax_deducted)],
            ["Total Union Dues (Box 44)", self._format_currency(summary.total_union_dues)],
        ]

        table = Table(data, colWidths=[5 * inch, 2 * inch])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#333333")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (0, -1), "Helvetica"),
            ("FONTNAME", (1, 1), (1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(table)

    def _build_employer_contributions_section(
        self,
        elements: list[Any],
        summary: T4Summary,
    ) -> None:
        """Build employer contributions section."""
        elements.append(Paragraph("EMPLOYER CONTRIBUTIONS", self.styles["SectionHeader"]))

        data = [
            ["Description", "Total"],
            ["Employer CPP Contributions", self._format_currency(summary.total_cpp_employer)],
            ["Employer EI Premiums", self._format_currency(summary.total_ei_employer)],
            ["Total Employer Contributions", self._format_currency(summary.total_employer_contributions)],
        ]

        table = Table(data, colWidths=[5 * inch, 2 * inch])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#333333")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (0, -1), "Helvetica"),
            ("FONTNAME", (1, 1), (1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            # Highlight total row
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f0f0f0")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(table)

    def _build_remittance_section(
        self,
        elements: list[Any],
        summary: T4Summary,
    ) -> None:
        """Build total remittance section."""
        elements.append(Paragraph("TOTAL REMITTANCE REQUIRED", self.styles["SectionHeader"]))

        data = [
            ["Description", "Total"],
            ["Employee CPP + CPP2", self._format_currency(
                summary.total_cpp_contributions + summary.total_cpp2_contributions
            )],
            ["Employer CPP", self._format_currency(summary.total_cpp_employer)],
            ["Employee EI", self._format_currency(summary.total_ei_premiums)],
            ["Employer EI", self._format_currency(summary.total_ei_employer)],
            ["Income Tax Deducted", self._format_currency(summary.total_income_tax_deducted)],
            ["TOTAL REMITTANCE", self._format_currency(summary.total_remittance_required)],
        ]

        table = Table(data, colWidths=[5 * inch, 2 * inch])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#333333")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (0, -2), "Helvetica"),
            ("FONTNAME", (1, 1), (1, -1), "Helvetica-Bold"),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("FONTSIZE", (0, -1), (-1, -1), 12),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            # Highlight total row
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#4CAF50")),
            ("TEXTCOLOR", (0, -1), (-1, -1), colors.white),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(table)

    def _format_currency(self, value: Decimal | None) -> str:
        """Format decimal as currency string."""
        if value is None:
            return "$0.00"
        return f"${value:,.2f}"
