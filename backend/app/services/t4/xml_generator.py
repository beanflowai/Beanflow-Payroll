"""
T4 XML Generator

Generates T619 XML format for CRA electronic filing.
This is the standard XML format for submitting T4 slips to CRA.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement, tostring

if TYPE_CHECKING:
    from app.models.t4 import T4SlipData, T4Summary


class T4XMLGenerator:
    """
    Generate CRA T619 XML for T4 electronic filing.

    The T619 format is the standard for submitting T4 information
    returns to CRA electronically.
    """

    # CRA T619 schema version
    SCHEMA_VERSION = "1.4"

    # XML namespaces
    T4_NAMESPACE = "http://www.cra-arc.gc.ca/xmlns/t4"
    SDTE_NAMESPACE = "http://www.cra-arc.gc.ca/xmlns/sdte"

    def __init__(
        self,
        transmitter_number: str | None = None,
        transmitter_name: str | None = None,
    ):
        """
        Initialize XML generator.

        Args:
            transmitter_number: CRA transmitter number (MM000000)
            transmitter_name: Transmitter company name
        """
        self.transmitter_number = transmitter_number or "MM000000"
        self.transmitter_name = transmitter_name or "Beanflow Payroll"

    def generate_xml(
        self,
        summary: T4Summary,
        slips: list[T4SlipData],
    ) -> str:
        """
        Generate complete T619 XML for T4 submission.

        Args:
            summary: T4Summary data
            slips: List of T4SlipData for all employees

        Returns:
            XML string
        """
        # Create root element with namespaces
        root = Element("Return")
        root.set("xmlns", self.T4_NAMESPACE)
        root.set("xmlns:sdte", self.SDTE_NAMESPACE)
        root.set("version", self.SCHEMA_VERSION)

        # Add Transmitter info
        self._add_transmitter(root)

        # Add T4 section
        t4_element = SubElement(root, "T4")

        # Add T4 Summary
        self._add_t4_summary(t4_element, summary)

        # Add T4 Slips
        slips_element = SubElement(t4_element, "T4Slips")
        for i, slip in enumerate(slips, start=1):
            self._add_t4_slip(slips_element, slip, i)

        # Convert to pretty-printed string
        xml_string = tostring(root, encoding="unicode")
        return self._prettify(xml_string)

    def _add_transmitter(self, parent: Element) -> None:
        """Add Transmitter section."""
        trans = SubElement(parent, "Transmitter")

        SubElement(trans, "TransmitterNumber").text = self.transmitter_number
        SubElement(trans, "TransmitterType").text = "3"  # Software
        SubElement(trans, "TransmitterName").text = self.transmitter_name

        # Contact info
        contact = SubElement(trans, "TransmitterContact")
        SubElement(contact, "ContactName").text = "Payroll Administrator"
        SubElement(contact, "ContactPhone").text = "000-000-0000"

    def _add_t4_summary(self, parent: Element, summary: T4Summary) -> None:
        """Add T4 Summary section."""
        sum_elem = SubElement(parent, "T4Summary")

        # Business number (first 9 digits of payroll account)
        bn = summary.employer_account_number[:9] if summary.employer_account_number else ""
        SubElement(sum_elem, "BusinessNumber").text = bn

        # Employer info
        SubElement(sum_elem, "EmployerName").text = summary.employer_name

        if summary.employer_address_line1:
            SubElement(sum_elem, "EmployerAddress1").text = summary.employer_address_line1
        if summary.employer_city:
            SubElement(sum_elem, "EmployerCity").text = summary.employer_city
        if summary.employer_province:
            SubElement(sum_elem, "EmployerProvince").text = summary.employer_province.value
        if summary.employer_postal_code:
            SubElement(sum_elem, "EmployerPostalCode").text = summary.employer_postal_code.replace(" ", "")

        # Summary totals
        SubElement(sum_elem, "TotalSlips").text = str(summary.total_number_of_t4_slips)

        # Box totals
        SubElement(sum_elem, "TotalEmploymentIncome").text = self._format_amount(
            summary.total_employment_income
        )
        SubElement(sum_elem, "TotalCPPContributions").text = self._format_amount(
            summary.total_cpp_contributions
        )
        SubElement(sum_elem, "TotalCPP2Contributions").text = self._format_amount(
            summary.total_cpp2_contributions
        )
        SubElement(sum_elem, "TotalEIPremiums").text = self._format_amount(
            summary.total_ei_premiums
        )
        SubElement(sum_elem, "TotalIncomeTaxDeducted").text = self._format_amount(
            summary.total_income_tax_deducted
        )

        # Employer contributions
        SubElement(sum_elem, "EmployerCPPContributions").text = self._format_amount(
            summary.total_cpp_employer
        )
        SubElement(sum_elem, "EmployerEIPremiums").text = self._format_amount(
            summary.total_ei_employer
        )

        # Total remittance
        SubElement(sum_elem, "TotalRemittanceRequired").text = self._format_amount(
            summary.total_remittance_required
        )

        # Tax year
        SubElement(sum_elem, "TaxYear").text = str(summary.tax_year)

    def _add_t4_slip(self, parent: Element, slip: T4SlipData, slip_num: int) -> None:
        """Add individual T4 slip."""
        slip_elem = SubElement(parent, "T4Slip")

        # Slip number
        SubElement(slip_elem, "SlipNumber").text = str(slip_num)

        # Employee info
        emp = SubElement(slip_elem, "Employee")
        SubElement(emp, "SIN").text = slip.sin
        SubElement(emp, "FirstName").text = slip.employee_first_name
        SubElement(emp, "LastName").text = slip.employee_last_name

        if slip.employee_address_line1:
            SubElement(emp, "Address1").text = slip.employee_address_line1
        if slip.employee_address_line2:
            SubElement(emp, "Address2").text = slip.employee_address_line2
        if slip.employee_city:
            SubElement(emp, "City").text = slip.employee_city
        if slip.employee_province:
            SubElement(emp, "Province").text = slip.employee_province.value
        if slip.employee_postal_code:
            SubElement(emp, "PostalCode").text = slip.employee_postal_code.replace(" ", "")

        # T4 Boxes
        boxes = SubElement(slip_elem, "T4Amounts")

        # Box 10 - Province of employment
        SubElement(boxes, "Box10").text = slip.province_of_employment.value

        # Box 14 - Employment income
        SubElement(boxes, "Box14").text = self._format_amount(slip.box_14_employment_income)

        # Box 16 - CPP contributions
        SubElement(boxes, "Box16").text = self._format_amount(slip.box_16_cpp_contributions)

        # Box 17 - CPP2 contributions
        if slip.box_17_cpp2_contributions > 0:
            SubElement(boxes, "Box17").text = self._format_amount(slip.box_17_cpp2_contributions)

        # Box 18 - EI premiums
        SubElement(boxes, "Box18").text = self._format_amount(slip.box_18_ei_premiums)

        # Box 20 - RPP contributions
        if slip.box_20_rpp_contributions:
            SubElement(boxes, "Box20").text = self._format_amount(slip.box_20_rpp_contributions)

        # Box 22 - Income tax deducted
        SubElement(boxes, "Box22").text = self._format_amount(slip.box_22_income_tax_deducted)

        # Box 24 - EI insurable earnings
        SubElement(boxes, "Box24").text = self._format_amount(slip.box_24_ei_insurable_earnings)

        # Box 26 - CPP pensionable earnings
        SubElement(boxes, "Box26").text = self._format_amount(slip.box_26_cpp_pensionable_earnings)

        # Box 44 - Union dues
        if slip.box_44_union_dues:
            SubElement(boxes, "Box44").text = self._format_amount(slip.box_44_union_dues)

        # Box 46 - Charitable donations
        if slip.box_46_charitable_donations:
            SubElement(boxes, "Box46").text = self._format_amount(slip.box_46_charitable_donations)

        # Box 52 - Pension adjustment
        if slip.box_52_pension_adjustment:
            SubElement(boxes, "Box52").text = self._format_amount(slip.box_52_pension_adjustment)

        # Exemption flags
        if slip.cpp_exempt:
            SubElement(boxes, "CPPExempt").text = "Y"
        if slip.ei_exempt:
            SubElement(boxes, "EIExempt").text = "Y"

    def _format_amount(self, value: Decimal | None) -> str:
        """
        Format decimal amount for XML.

        CRA requires amounts as cents (no decimal point).
        """
        if value is None:
            return "0"
        # Convert to cents (multiply by 100)
        cents = int(value * 100)
        return str(cents)

    def _prettify(self, xml_string: str) -> str:
        """Pretty print XML string."""
        # Add XML declaration
        dom = minidom.parseString(xml_string)
        return dom.toprettyxml(indent="  ", encoding="UTF-8").decode("UTF-8")

    def generate_xml_filename(self, summary: T4Summary) -> str:
        """
        Generate standard filename for T4 XML file.

        Args:
            summary: T4Summary data

        Returns:
            Filename like "T4_123456789RP0001_2025.xml"
        """
        account = summary.employer_account_number.replace(" ", "")
        return f"T4_{account}_{summary.tax_year}.xml"
