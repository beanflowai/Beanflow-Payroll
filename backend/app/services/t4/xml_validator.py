"""
T4 XML Validator

Validates T4 XML structure and content before CRA submission.
Uses basic structure validation (not XSD schema validation).
"""

from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from xml.etree.ElementTree import Element, ParseError, fromstring

from app.models.t4 import T4ValidationError, T4ValidationResult, T4ValidationWarning
from app.utils.sin_validator import validate_sin_luhn


class T4XMLValidator:
    """
    Validate T4 XML structure and content.

    Performs basic structure validation without requiring XSD schema files.
    CRA will perform full validation upon upload - this catches obvious errors first.
    """

    # Validation error codes
    ERR_XML_PARSE = "XML_PARSE_ERROR"
    ERR_MISSING_ELEMENT = "MISSING_REQUIRED_ELEMENT"
    ERR_INVALID_BN = "INVALID_BUSINESS_NUMBER"
    ERR_INVALID_SIN = "INVALID_SIN"
    ERR_INVALID_AMOUNT = "INVALID_AMOUNT"
    ERR_INVALID_TAX_YEAR = "INVALID_TAX_YEAR"
    ERR_SLIP_COUNT_MISMATCH = "SLIP_COUNT_MISMATCH"

    WARN_TAX_YEAR = "UNEXPECTED_TAX_YEAR"
    WARN_AMOUNT_MISMATCH = "AMOUNT_MISMATCH"

    # CRA T4 XML namespace
    T4_NAMESPACE = "http://www.cra-arc.gc.ca/xmlns/t4"
    NS = {"t4": T4_NAMESPACE}

    # Required XML elements
    REQUIRED_ROOT_ELEMENTS = ["Transmitter", "T4"]
    REQUIRED_TRANSMITTER_ELEMENTS = ["TransmitterNumber", "TransmitterName"]
    REQUIRED_SUMMARY_ELEMENTS = [
        "BusinessNumber",
        "EmployerName",
        "TotalSlips",
        "TaxYear",
    ]

    def _find_element(self, parent: Element, tag: str) -> Element | None:
        """
        Find child element, handling both namespaced and non-namespaced XML.

        The T4 XML generator uses a default namespace, so elements are actually
        {http://www.cra-arc.gc.ca/xmlns/t4}ElementName. This helper tries both
        namespaced and non-namespaced lookup.

        Args:
            parent: Parent element to search in
            tag: Element tag name (without namespace)

        Returns:
            Found element or None
        """
        # Try with namespace first (for generated XML)
        elem = parent.find(f"t4:{tag}", self.NS)
        if elem is not None:
            return elem
        # Fallback to no namespace (for simple/test XML)
        return parent.find(tag)

    def _find_all_elements(self, parent: Element, tag: str) -> list[Element]:
        """
        Find all child elements with given tag, handling namespaces.

        Args:
            parent: Parent element to search in
            tag: Element tag name (without namespace)

        Returns:
            List of found elements
        """
        # Try with namespace first
        elems = parent.findall(f"t4:{tag}", self.NS)
        if elems:
            return elems
        # Fallback to no namespace
        return parent.findall(tag)

    def validate(self, xml_content: str) -> T4ValidationResult:
        """
        Validate T4 XML structure and content.

        Args:
            xml_content: XML string to validate

        Returns:
            T4ValidationResult with errors and warnings
        """
        errors: list[T4ValidationError] = []
        warnings: list[T4ValidationWarning] = []

        # 1. XML well-formed check
        try:
            root = fromstring(xml_content)
        except ParseError as e:
            errors.append(
                T4ValidationError(
                    code=self.ERR_XML_PARSE,
                    message=f"XML parsing failed: {str(e)}",
                    field="xml",
                )
            )
            return T4ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
            )

        # 2. Required root elements
        self._validate_required_elements(root, errors)

        # Get T4 section
        t4_elem = self._find_element(root, "T4")
        if t4_elem is None:
            # Already reported in required elements check
            return T4ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
            )

        # Get T4Summary section
        summary_elem = self._find_element(t4_elem, "T4Summary")
        if summary_elem is None:
            errors.append(
                T4ValidationError(
                    code=self.ERR_MISSING_ELEMENT,
                    message="Missing required element: T4/T4Summary",
                    field="T4Summary",
                )
            )
            return T4ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
            )

        # 3. Validate T4Summary required elements
        self._validate_summary_elements(summary_elem, errors)

        # 4. Validate Business Number format
        self._validate_business_number(summary_elem, errors)

        # 5. Validate Tax Year
        self._validate_tax_year(summary_elem, errors, warnings)

        # Get T4Slips section
        slips_elem = self._find_element(t4_elem, "T4Slips")
        if slips_elem is None:
            errors.append(
                T4ValidationError(
                    code=self.ERR_MISSING_ELEMENT,
                    message="Missing required element: T4/T4Slips",
                    field="T4Slips",
                )
            )
        else:
            # 6. Validate each T4 slip
            slips = self._find_all_elements(slips_elem, "T4Slip")
            for i, slip in enumerate(slips, start=1):
                self._validate_t4_slip(slip, i, errors)

            # 7. Validate slip count matches TotalSlips
            self._validate_slip_count(summary_elem, slips, errors)

            # 8. Validate summary totals match slip totals
            self._validate_totals(summary_elem, slips, warnings)

        return T4ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def _validate_required_elements(
        self,
        root: Element,
        errors: list[T4ValidationError],
    ) -> None:
        """Validate required root elements exist."""
        for elem_name in self.REQUIRED_ROOT_ELEMENTS:
            if self._find_element(root, elem_name) is None:
                errors.append(
                    T4ValidationError(
                        code=self.ERR_MISSING_ELEMENT,
                        message=f"Missing required element: {elem_name}",
                        field=elem_name,
                    )
                )

        # Validate Transmitter elements
        trans_elem = self._find_element(root, "Transmitter")
        if trans_elem is not None:
            for elem_name in self.REQUIRED_TRANSMITTER_ELEMENTS:
                if self._find_element(trans_elem, elem_name) is None:
                    errors.append(
                        T4ValidationError(
                            code=self.ERR_MISSING_ELEMENT,
                            message=f"Missing required element: Transmitter/{elem_name}",
                            field=f"Transmitter/{elem_name}",
                        )
                    )

    def _validate_summary_elements(
        self,
        summary_elem: Element,
        errors: list[T4ValidationError],
    ) -> None:
        """Validate T4Summary required elements."""
        for elem_name in self.REQUIRED_SUMMARY_ELEMENTS:
            elem = self._find_element(summary_elem, elem_name)
            if elem is None or not elem.text:
                errors.append(
                    T4ValidationError(
                        code=self.ERR_MISSING_ELEMENT,
                        message=f"Missing or empty required element: T4Summary/{elem_name}",
                        field=f"T4Summary/{elem_name}",
                    )
                )

    def _validate_business_number(
        self,
        summary_elem: Element,
        errors: list[T4ValidationError],
    ) -> None:
        """Validate Business Number format (9 digits)."""
        bn_elem = self._find_element(summary_elem, "BusinessNumber")
        if bn_elem is not None and bn_elem.text:
            bn = bn_elem.text.strip()
            if not re.match(r"^\d{9}$", bn):
                errors.append(
                    T4ValidationError(
                        code=self.ERR_INVALID_BN,
                        message=f"Invalid Business Number format: {bn}. Must be exactly 9 digits.",
                        field="T4Summary/BusinessNumber",
                    )
                )

    def _validate_tax_year(
        self,
        summary_elem: Element,
        errors: list[T4ValidationError],
        warnings: list[T4ValidationWarning],
    ) -> None:
        """Validate Tax Year is current or previous year."""
        year_elem = self._find_element(summary_elem, "TaxYear")
        if year_elem is not None and year_elem.text:
            try:
                tax_year = int(year_elem.text)
                current_year = datetime.now().year
                # Allow current year and previous year
                if tax_year not in [current_year, current_year - 1]:
                    warnings.append(
                        T4ValidationWarning(
                            code=self.WARN_TAX_YEAR,
                            message=f"Tax year {tax_year} is not current ({current_year}) or previous ({current_year - 1}) year",
                            field="T4Summary/TaxYear",
                        )
                    )
            except ValueError:
                errors.append(
                    T4ValidationError(
                        code=self.ERR_INVALID_TAX_YEAR,
                        message=f"Invalid TaxYear format: '{year_elem.text}' must be a valid year number",
                        field="T4Summary/TaxYear",
                    )
                )

    def _validate_t4_slip(
        self,
        slip_elem: Element,
        slip_num: int,
        errors: list[T4ValidationError],
    ) -> None:
        """Validate individual T4 slip."""
        slip_prefix = f"T4Slip[{slip_num}]"

        # Validate Employee section
        emp_elem = self._find_element(slip_elem, "Employee")
        if emp_elem is None:
            errors.append(
                T4ValidationError(
                    code=self.ERR_MISSING_ELEMENT,
                    message=f"Missing Employee element in {slip_prefix}",
                    field=f"{slip_prefix}/Employee",
                )
            )
        else:
            # Validate SIN
            sin_elem = self._find_element(emp_elem, "SIN")
            if sin_elem is None or not sin_elem.text:
                errors.append(
                    T4ValidationError(
                        code=self.ERR_MISSING_ELEMENT,
                        message=f"Missing SIN in {slip_prefix}",
                        field=f"{slip_prefix}/Employee/SIN",
                    )
                )
            else:
                sin = sin_elem.text.strip()
                if not re.match(r"^\d{9}$", sin):
                    errors.append(
                        T4ValidationError(
                            code=self.ERR_INVALID_SIN,
                            message=f"Invalid SIN format in {slip_prefix}: must be 9 digits",
                            field=f"{slip_prefix}/Employee/SIN",
                        )
                    )
                elif not validate_sin_luhn(sin):
                    errors.append(
                        T4ValidationError(
                            code=self.ERR_INVALID_SIN,
                            message=f"Invalid SIN in {slip_prefix}: failed Luhn validation",
                            field=f"{slip_prefix}/Employee/SIN",
                        )
                    )

            # Validate required employee fields
            for field_name in ["FirstName", "LastName"]:
                field_elem = self._find_element(emp_elem, field_name)
                if field_elem is None or not field_elem.text:
                    errors.append(
                        T4ValidationError(
                            code=self.ERR_MISSING_ELEMENT,
                            message=f"Missing {field_name} in {slip_prefix}",
                            field=f"{slip_prefix}/Employee/{field_name}",
                        )
                    )

        # Validate T4Amounts section
        amounts_elem = self._find_element(slip_elem, "T4Amounts")
        if amounts_elem is None:
            errors.append(
                T4ValidationError(
                    code=self.ERR_MISSING_ELEMENT,
                    message=f"Missing T4Amounts element in {slip_prefix}",
                    field=f"{slip_prefix}/T4Amounts",
                )
            )
        else:
            # Validate required amount boxes
            for box_name in ["Box14"]:  # Employment income is required
                self._validate_amount_box(
                    amounts_elem, box_name, slip_prefix, errors, required=True
                )

    def _validate_amount_box(
        self,
        amounts_elem: Element,
        box_name: str,
        slip_prefix: str,
        errors: list[T4ValidationError],
        required: bool = False,
    ) -> None:
        """Validate an amount box."""
        box_elem = self._find_element(amounts_elem, box_name)

        # Check if required box is missing or empty
        if box_elem is None or not box_elem.text:
            if required:
                errors.append(
                    T4ValidationError(
                        code=self.ERR_MISSING_ELEMENT,
                        message=f"Missing required {box_name} (Employment Income) in {slip_prefix}",
                        field=f"{slip_prefix}/T4Amounts/{box_name}",
                    )
                )
            return

        if box_elem is not None and box_elem.text:
            try:
                amount = int(box_elem.text)
                if amount < 0:
                    errors.append(
                        T4ValidationError(
                            code=self.ERR_INVALID_AMOUNT,
                            message=f"Negative amount in {slip_prefix}/{box_name}: {amount}",
                            field=f"{slip_prefix}/T4Amounts/{box_name}",
                        )
                    )
            except ValueError:
                errors.append(
                    T4ValidationError(
                        code=self.ERR_INVALID_AMOUNT,
                        message=f"Invalid amount format in {slip_prefix}/{box_name}: {box_elem.text}",
                        field=f"{slip_prefix}/T4Amounts/{box_name}",
                    )
                )

    def _validate_slip_count(
        self,
        summary_elem: Element,
        slips: list[Element],
        errors: list[T4ValidationError],
    ) -> None:
        """Validate TotalSlips matches actual slip count."""
        total_elem = self._find_element(summary_elem, "TotalSlips")
        if total_elem is not None and total_elem.text:
            try:
                declared_total = int(total_elem.text)
                actual_count = len(slips)
                if declared_total != actual_count:
                    errors.append(
                        T4ValidationError(
                            code=self.ERR_SLIP_COUNT_MISMATCH,
                            message=f"TotalSlips ({declared_total}) does not match actual slip count ({actual_count})",
                            field="T4Summary/TotalSlips",
                        )
                    )
            except ValueError:
                pass

    def _validate_totals(
        self,
        summary_elem: Element,
        slips: list[Element],
        warnings: list[T4ValidationWarning],
    ) -> None:
        """Validate summary totals match slip totals."""
        # Calculate totals from slips
        # Note: Box17 is CPP2/QPP2 contributions (second tier CPP, introduced 2024)
        slip_totals = {
            "employment_income": Decimal("0"),
            "cpp_contributions": Decimal("0"),
            "cpp2_contributions": Decimal("0"),
            "ei_premiums": Decimal("0"),
            "income_tax": Decimal("0"),
        }

        box_mapping = {
            "Box14": "employment_income",
            "Box16": "cpp_contributions",
            "Box17": "cpp2_contributions",  # CPP2/QPP2 second tier (2024+)
            "Box18": "ei_premiums",
            "Box22": "income_tax",
        }

        for slip in slips:
            amounts = self._find_element(slip, "T4Amounts")
            if amounts is not None:
                for box_name, total_key in box_mapping.items():
                    box_elem = self._find_element(amounts, box_name)
                    if box_elem is not None and box_elem.text:
                        try:
                            # Amounts are in cents
                            slip_totals[total_key] += Decimal(box_elem.text)
                        except (ValueError, TypeError, InvalidOperation):
                            pass

        # Compare with summary totals
        summary_mapping = {
            "TotalEmploymentIncome": "employment_income",
            "TotalCPPContributions": "cpp_contributions",
            "TotalCPP2Contributions": "cpp2_contributions",  # CPP2/QPP2 second tier (2024+)
            "TotalEIPremiums": "ei_premiums",
            "TotalIncomeTaxDeducted": "income_tax",
        }

        for summary_elem_name, total_key in summary_mapping.items():
            elem = self._find_element(summary_elem, summary_elem_name)
            if elem is not None and elem.text:
                try:
                    declared_total = Decimal(elem.text)
                    calculated_total = slip_totals[total_key]
                    if declared_total != calculated_total:
                        warnings.append(
                            T4ValidationWarning(
                                code=self.WARN_AMOUNT_MISMATCH,
                                message=f"{summary_elem_name} ({declared_total}) does not match sum of slips ({calculated_total})",
                                field=f"T4Summary/{summary_elem_name}",
                            )
                        )
                except (ValueError, TypeError, InvalidOperation):
                    pass
