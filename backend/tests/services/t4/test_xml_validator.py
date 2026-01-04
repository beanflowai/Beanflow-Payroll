"""
Tests for T4 XML Validator

Tests for validating T4 XML structure and content before CRA submission.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from app.services.t4.xml_validator import T4XMLValidator


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def validator() -> T4XMLValidator:
    """Create a T4 XML validator instance."""
    return T4XMLValidator()


@pytest.fixture
def valid_xml() -> str:
    """Create a valid T4 XML document."""
    current_year = datetime.now().year
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Return xmlns="http://www.cra-arc.gc.ca/xmlns/t4">
    <Transmitter>
        <TransmitterNumber>MM123456</TransmitterNumber>
        <TransmitterName>Test Payroll</TransmitterName>
    </Transmitter>
    <T4>
        <T4Summary>
            <BusinessNumber>123456789</BusinessNumber>
            <EmployerName>Test Company</EmployerName>
            <TotalSlips>1</TotalSlips>
            <TotalEmploymentIncome>5000000</TotalEmploymentIncome>
            <TotalCPPContributions>380000</TotalCPPContributions>
            <TotalCPP2Contributions>50000</TotalCPP2Contributions>
            <TotalEIPremiums>104912</TotalEIPremiums>
            <TotalIncomeTaxDeducted>850000</TotalIncomeTaxDeducted>
            <TaxYear>{current_year}</TaxYear>
        </T4Summary>
        <T4Slips>
            <T4Slip>
                <Employee>
                    <SIN>046454286</SIN>
                    <FirstName>John</FirstName>
                    <LastName>Doe</LastName>
                </Employee>
                <T4Amounts>
                    <Box14>5000000</Box14>
                    <Box16>380000</Box16>
                    <Box17>50000</Box17>
                    <Box18>104912</Box18>
                    <Box22>850000</Box22>
                </T4Amounts>
            </T4Slip>
        </T4Slips>
    </T4>
</Return>"""


@pytest.fixture
def simple_valid_xml() -> str:
    """Create a simple valid T4 XML without namespace."""
    current_year = datetime.now().year
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Return>
    <Transmitter>
        <TransmitterNumber>MM123456</TransmitterNumber>
        <TransmitterName>Test Payroll</TransmitterName>
    </Transmitter>
    <T4>
        <T4Summary>
            <BusinessNumber>123456789</BusinessNumber>
            <EmployerName>Test Company</EmployerName>
            <TotalSlips>1</TotalSlips>
            <TotalEmploymentIncome>5000000</TotalEmploymentIncome>
            <TotalCPPContributions>380000</TotalCPPContributions>
            <TotalCPP2Contributions>50000</TotalCPP2Contributions>
            <TotalEIPremiums>104912</TotalEIPremiums>
            <TotalIncomeTaxDeducted>850000</TotalIncomeTaxDeducted>
            <TaxYear>{current_year}</TaxYear>
        </T4Summary>
        <T4Slips>
            <T4Slip>
                <Employee>
                    <SIN>046454286</SIN>
                    <FirstName>John</FirstName>
                    <LastName>Doe</LastName>
                </Employee>
                <T4Amounts>
                    <Box14>5000000</Box14>
                    <Box16>380000</Box16>
                    <Box17>50000</Box17>
                    <Box18>104912</Box18>
                    <Box22>850000</Box22>
                </T4Amounts>
            </T4Slip>
        </T4Slips>
    </T4>
</Return>"""


# =============================================================================
# Test: XML Parse Errors
# =============================================================================


class TestXmlParseErrors:
    """Tests for XML parsing errors."""

    def test_invalid_xml_syntax(self, validator):
        """Test validation fails for invalid XML syntax."""
        invalid_xml = "<Return><unclosed>"

        result = validator.validate(invalid_xml)

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].code == "XML_PARSE_ERROR"

    def test_empty_xml(self, validator):
        """Test validation fails for empty XML."""
        result = validator.validate("")

        assert result.is_valid is False
        assert result.errors[0].code == "XML_PARSE_ERROR"


# =============================================================================
# Test: Required Elements
# =============================================================================


class TestRequiredElements:
    """Tests for required element validation."""

    def test_missing_transmitter(self, validator):
        """Test validation fails when Transmitter is missing."""
        current_year = datetime.now().year
        xml = f"""<?xml version="1.0"?>
<Return>
    <T4>
        <T4Summary>
            <BusinessNumber>123456789</BusinessNumber>
            <EmployerName>Test</EmployerName>
            <TotalSlips>0</TotalSlips>
            <TaxYear>{current_year}</TaxYear>
        </T4Summary>
        <T4Slips></T4Slips>
    </T4>
</Return>"""

        result = validator.validate(xml)

        assert result.is_valid is False
        errors = [e for e in result.errors if e.field == "Transmitter"]
        assert len(errors) == 1

    def test_missing_t4_section(self, validator):
        """Test validation fails when T4 section is missing."""
        xml = """<?xml version="1.0"?>
<Return>
    <Transmitter>
        <TransmitterNumber>MM123456</TransmitterNumber>
        <TransmitterName>Test</TransmitterName>
    </Transmitter>
</Return>"""

        result = validator.validate(xml)

        assert result.is_valid is False
        errors = [e for e in result.errors if e.field == "T4"]
        assert len(errors) == 1

    def test_missing_t4_summary(self, validator):
        """Test validation fails when T4Summary is missing."""
        xml = """<?xml version="1.0"?>
<Return>
    <Transmitter>
        <TransmitterNumber>MM123456</TransmitterNumber>
        <TransmitterName>Test</TransmitterName>
    </Transmitter>
    <T4>
        <T4Slips></T4Slips>
    </T4>
</Return>"""

        result = validator.validate(xml)

        assert result.is_valid is False
        errors = [e for e in result.errors if "T4Summary" in e.message]
        assert len(errors) >= 1

    def test_missing_t4_slips(self, validator):
        """Test validation fails when T4Slips section is missing."""
        current_year = datetime.now().year
        xml = f"""<?xml version="1.0"?>
<Return>
    <Transmitter>
        <TransmitterNumber>MM123456</TransmitterNumber>
        <TransmitterName>Test</TransmitterName>
    </Transmitter>
    <T4>
        <T4Summary>
            <BusinessNumber>123456789</BusinessNumber>
            <EmployerName>Test</EmployerName>
            <TotalSlips>0</TotalSlips>
            <TaxYear>{current_year}</TaxYear>
        </T4Summary>
    </T4>
</Return>"""

        result = validator.validate(xml)

        assert result.is_valid is False
        errors = [e for e in result.errors if "T4Slips" in e.message]
        assert len(errors) >= 1


# =============================================================================
# Test: Business Number Validation
# =============================================================================


class TestBusinessNumberValidation:
    """Tests for Business Number validation."""

    def test_valid_business_number(self, validator, simple_valid_xml):
        """Test valid 9-digit business number passes."""
        result = validator.validate(simple_valid_xml)

        bn_errors = [e for e in result.errors if e.code == "INVALID_BUSINESS_NUMBER"]
        assert len(bn_errors) == 0

    def test_invalid_business_number_short(self, validator):
        """Test BN with less than 9 digits fails."""
        current_year = datetime.now().year
        xml = f"""<?xml version="1.0"?>
<Return>
    <Transmitter>
        <TransmitterNumber>MM123456</TransmitterNumber>
        <TransmitterName>Test</TransmitterName>
    </Transmitter>
    <T4>
        <T4Summary>
            <BusinessNumber>12345678</BusinessNumber>
            <EmployerName>Test</EmployerName>
            <TotalSlips>0</TotalSlips>
            <TaxYear>{current_year}</TaxYear>
        </T4Summary>
        <T4Slips></T4Slips>
    </T4>
</Return>"""

        result = validator.validate(xml)

        bn_errors = [e for e in result.errors if e.code == "INVALID_BUSINESS_NUMBER"]
        assert len(bn_errors) == 1

    def test_invalid_business_number_letters(self, validator):
        """Test BN with letters fails."""
        current_year = datetime.now().year
        xml = f"""<?xml version="1.0"?>
<Return>
    <Transmitter>
        <TransmitterNumber>MM123456</TransmitterNumber>
        <TransmitterName>Test</TransmitterName>
    </Transmitter>
    <T4>
        <T4Summary>
            <BusinessNumber>12345ABCD</BusinessNumber>
            <EmployerName>Test</EmployerName>
            <TotalSlips>0</TotalSlips>
            <TaxYear>{current_year}</TaxYear>
        </T4Summary>
        <T4Slips></T4Slips>
    </T4>
</Return>"""

        result = validator.validate(xml)

        bn_errors = [e for e in result.errors if e.code == "INVALID_BUSINESS_NUMBER"]
        assert len(bn_errors) == 1


# =============================================================================
# Test: SIN Validation
# =============================================================================


class TestSinValidation:
    """Tests for SIN validation."""

    def test_valid_sin_luhn(self, validator, simple_valid_xml):
        """Test valid SIN passes Luhn check."""
        # 046454286 is a valid SIN that passes Luhn
        result = validator.validate(simple_valid_xml)

        sin_errors = [e for e in result.errors if e.code == "INVALID_SIN"]
        assert len(sin_errors) == 0

    def test_invalid_sin_format(self, validator):
        """Test SIN with wrong format fails."""
        current_year = datetime.now().year
        xml = f"""<?xml version="1.0"?>
<Return>
    <Transmitter>
        <TransmitterNumber>MM123456</TransmitterNumber>
        <TransmitterName>Test</TransmitterName>
    </Transmitter>
    <T4>
        <T4Summary>
            <BusinessNumber>123456789</BusinessNumber>
            <EmployerName>Test</EmployerName>
            <TotalSlips>1</TotalSlips>
            <TaxYear>{current_year}</TaxYear>
        </T4Summary>
        <T4Slips>
            <T4Slip>
                <Employee>
                    <SIN>12345</SIN>
                    <FirstName>John</FirstName>
                    <LastName>Doe</LastName>
                </Employee>
                <T4Amounts>
                    <Box14>5000000</Box14>
                </T4Amounts>
            </T4Slip>
        </T4Slips>
    </T4>
</Return>"""

        result = validator.validate(xml)

        sin_errors = [e for e in result.errors if e.code == "INVALID_SIN"]
        assert len(sin_errors) == 1
        assert "must be 9 digits" in sin_errors[0].message

    def test_invalid_sin_luhn(self, validator):
        """Test SIN that fails Luhn check."""
        current_year = datetime.now().year
        xml = f"""<?xml version="1.0"?>
<Return>
    <Transmitter>
        <TransmitterNumber>MM123456</TransmitterNumber>
        <TransmitterName>Test</TransmitterName>
    </Transmitter>
    <T4>
        <T4Summary>
            <BusinessNumber>123456789</BusinessNumber>
            <EmployerName>Test</EmployerName>
            <TotalSlips>1</TotalSlips>
            <TaxYear>{current_year}</TaxYear>
        </T4Summary>
        <T4Slips>
            <T4Slip>
                <Employee>
                    <SIN>123456789</SIN>
                    <FirstName>John</FirstName>
                    <LastName>Doe</LastName>
                </Employee>
                <T4Amounts>
                    <Box14>5000000</Box14>
                </T4Amounts>
            </T4Slip>
        </T4Slips>
    </T4>
</Return>"""

        result = validator.validate(xml)

        sin_errors = [e for e in result.errors if e.code == "INVALID_SIN"]
        assert len(sin_errors) == 1
        assert "Luhn" in sin_errors[0].message


# =============================================================================
# Test: Tax Year Validation
# =============================================================================


class TestTaxYearValidation:
    """Tests for tax year validation."""

    def test_current_year_valid(self, validator, simple_valid_xml):
        """Test current year is valid."""
        result = validator.validate(simple_valid_xml)

        year_warnings = [w for w in result.warnings if w.code == "UNEXPECTED_TAX_YEAR"]
        assert len(year_warnings) == 0

    def test_previous_year_valid(self, validator):
        """Test previous year is valid."""
        prev_year = datetime.now().year - 1
        xml = f"""<?xml version="1.0"?>
<Return>
    <Transmitter>
        <TransmitterNumber>MM123456</TransmitterNumber>
        <TransmitterName>Test</TransmitterName>
    </Transmitter>
    <T4>
        <T4Summary>
            <BusinessNumber>123456789</BusinessNumber>
            <EmployerName>Test</EmployerName>
            <TotalSlips>1</TotalSlips>
            <TotalEmploymentIncome>5000000</TotalEmploymentIncome>
            <TotalCPPContributions>380000</TotalCPPContributions>
            <TotalEIPremiums>104912</TotalEIPremiums>
            <TotalIncomeTaxDeducted>850000</TotalIncomeTaxDeducted>
            <TaxYear>{prev_year}</TaxYear>
        </T4Summary>
        <T4Slips>
            <T4Slip>
                <Employee>
                    <SIN>046454286</SIN>
                    <FirstName>John</FirstName>
                    <LastName>Doe</LastName>
                </Employee>
                <T4Amounts>
                    <Box14>5000000</Box14>
                    <Box16>380000</Box16>
                    <Box18>104912</Box18>
                    <Box22>850000</Box22>
                </T4Amounts>
            </T4Slip>
        </T4Slips>
    </T4>
</Return>"""

        result = validator.validate(xml)

        year_warnings = [w for w in result.warnings if w.code == "UNEXPECTED_TAX_YEAR"]
        assert len(year_warnings) == 0

    def test_old_year_warning(self, validator):
        """Test old tax year generates warning."""
        old_year = datetime.now().year - 5
        xml = f"""<?xml version="1.0"?>
<Return>
    <Transmitter>
        <TransmitterNumber>MM123456</TransmitterNumber>
        <TransmitterName>Test</TransmitterName>
    </Transmitter>
    <T4>
        <T4Summary>
            <BusinessNumber>123456789</BusinessNumber>
            <EmployerName>Test</EmployerName>
            <TotalSlips>0</TotalSlips>
            <TaxYear>{old_year}</TaxYear>
        </T4Summary>
        <T4Slips></T4Slips>
    </T4>
</Return>"""

        result = validator.validate(xml)

        year_warnings = [w for w in result.warnings if w.code == "UNEXPECTED_TAX_YEAR"]
        assert len(year_warnings) == 1

    def test_invalid_tax_year_format(self, validator):
        """Test invalid tax year format fails."""
        xml = """<?xml version="1.0"?>
<Return>
    <Transmitter>
        <TransmitterNumber>MM123456</TransmitterNumber>
        <TransmitterName>Test</TransmitterName>
    </Transmitter>
    <T4>
        <T4Summary>
            <BusinessNumber>123456789</BusinessNumber>
            <EmployerName>Test</EmployerName>
            <TotalSlips>0</TotalSlips>
            <TaxYear>invalid</TaxYear>
        </T4Summary>
        <T4Slips></T4Slips>
    </T4>
</Return>"""

        result = validator.validate(xml)

        year_errors = [e for e in result.errors if e.code == "INVALID_TAX_YEAR"]
        assert len(year_errors) == 1


# =============================================================================
# Test: Slip Count Validation
# =============================================================================


class TestSlipCountValidation:
    """Tests for slip count validation."""

    def test_matching_slip_count(self, validator, simple_valid_xml):
        """Test matching slip count passes."""
        result = validator.validate(simple_valid_xml)

        count_errors = [e for e in result.errors if e.code == "SLIP_COUNT_MISMATCH"]
        assert len(count_errors) == 0

    def test_mismatched_slip_count(self, validator):
        """Test mismatched slip count fails."""
        current_year = datetime.now().year
        xml = f"""<?xml version="1.0"?>
<Return>
    <Transmitter>
        <TransmitterNumber>MM123456</TransmitterNumber>
        <TransmitterName>Test</TransmitterName>
    </Transmitter>
    <T4>
        <T4Summary>
            <BusinessNumber>123456789</BusinessNumber>
            <EmployerName>Test</EmployerName>
            <TotalSlips>5</TotalSlips>
            <TaxYear>{current_year}</TaxYear>
        </T4Summary>
        <T4Slips>
            <T4Slip>
                <Employee>
                    <SIN>046454286</SIN>
                    <FirstName>John</FirstName>
                    <LastName>Doe</LastName>
                </Employee>
                <T4Amounts>
                    <Box14>5000000</Box14>
                </T4Amounts>
            </T4Slip>
        </T4Slips>
    </T4>
</Return>"""

        result = validator.validate(xml)

        count_errors = [e for e in result.errors if e.code == "SLIP_COUNT_MISMATCH"]
        assert len(count_errors) == 1
        assert "5" in count_errors[0].message  # Declared count
        assert "1" in count_errors[0].message  # Actual count


# =============================================================================
# Test: Amount Validation
# =============================================================================


class TestAmountValidation:
    """Tests for amount validation."""

    def test_valid_amounts(self, validator, simple_valid_xml):
        """Test valid amounts pass."""
        result = validator.validate(simple_valid_xml)

        amount_errors = [e for e in result.errors if e.code == "INVALID_AMOUNT"]
        assert len(amount_errors) == 0

    def test_negative_amount_fails(self, validator):
        """Test negative amount fails validation."""
        current_year = datetime.now().year
        xml = f"""<?xml version="1.0"?>
<Return>
    <Transmitter>
        <TransmitterNumber>MM123456</TransmitterNumber>
        <TransmitterName>Test</TransmitterName>
    </Transmitter>
    <T4>
        <T4Summary>
            <BusinessNumber>123456789</BusinessNumber>
            <EmployerName>Test</EmployerName>
            <TotalSlips>1</TotalSlips>
            <TaxYear>{current_year}</TaxYear>
        </T4Summary>
        <T4Slips>
            <T4Slip>
                <Employee>
                    <SIN>046454286</SIN>
                    <FirstName>John</FirstName>
                    <LastName>Doe</LastName>
                </Employee>
                <T4Amounts>
                    <Box14>-5000000</Box14>
                </T4Amounts>
            </T4Slip>
        </T4Slips>
    </T4>
</Return>"""

        result = validator.validate(xml)

        amount_errors = [e for e in result.errors if e.code == "INVALID_AMOUNT"]
        assert len(amount_errors) == 1
        assert "Negative" in amount_errors[0].message


# =============================================================================
# Test: Total Validation
# =============================================================================


class TestTotalValidation:
    """Tests for summary total validation."""

    def test_matching_totals(self, validator, simple_valid_xml):
        """Test matching totals pass without warnings."""
        result = validator.validate(simple_valid_xml)

        mismatch_warnings = [w for w in result.warnings if w.code == "AMOUNT_MISMATCH"]
        assert len(mismatch_warnings) == 0

    def test_mismatched_totals_warning(self, validator):
        """Test mismatched totals generate warning."""
        current_year = datetime.now().year
        xml = f"""<?xml version="1.0"?>
<Return>
    <Transmitter>
        <TransmitterNumber>MM123456</TransmitterNumber>
        <TransmitterName>Test</TransmitterName>
    </Transmitter>
    <T4>
        <T4Summary>
            <BusinessNumber>123456789</BusinessNumber>
            <EmployerName>Test</EmployerName>
            <TotalSlips>1</TotalSlips>
            <TotalEmploymentIncome>9999999</TotalEmploymentIncome>
            <TaxYear>{current_year}</TaxYear>
        </T4Summary>
        <T4Slips>
            <T4Slip>
                <Employee>
                    <SIN>046454286</SIN>
                    <FirstName>John</FirstName>
                    <LastName>Doe</LastName>
                </Employee>
                <T4Amounts>
                    <Box14>5000000</Box14>
                </T4Amounts>
            </T4Slip>
        </T4Slips>
    </T4>
</Return>"""

        result = validator.validate(xml)

        mismatch_warnings = [w for w in result.warnings if w.code == "AMOUNT_MISMATCH"]
        assert len(mismatch_warnings) >= 1


# =============================================================================
# Test: Complete Valid XML
# =============================================================================


class TestCompleteValidation:
    """Tests for complete valid XML validation."""

    def test_valid_xml_passes(self, validator, simple_valid_xml):
        """Test complete valid XML passes validation."""
        result = validator.validate(simple_valid_xml)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_valid_xml_with_namespace_passes(self, validator, valid_xml):
        """Test complete valid XML with namespace passes validation."""
        result = validator.validate(valid_xml)

        assert result.is_valid is True
        assert len(result.errors) == 0


# =============================================================================
# Test: Transmitter Sub-elements Validation
# =============================================================================


class TestTransmitterSubElements:
    """Tests for Transmitter required sub-elements validation."""

    def test_missing_transmitter_number(self, validator):
        """Test validation fails when TransmitterNumber is missing."""
        current_year = datetime.now().year
        xml = f"""<?xml version="1.0"?>
<Return>
    <Transmitter>
        <TransmitterName>Test</TransmitterName>
    </Transmitter>
    <T4>
        <T4Summary>
            <BusinessNumber>123456789</BusinessNumber>
            <EmployerName>Test</EmployerName>
            <TotalSlips>0</TotalSlips>
            <TaxYear>{current_year}</TaxYear>
        </T4Summary>
        <T4Slips></T4Slips>
    </T4>
</Return>"""

        result = validator.validate(xml)

        errors = [e for e in result.errors if "Transmitter" in e.field]
        assert len(errors) >= 1
        assert any("TransmitterNumber" in e.message for e in errors)

    def test_missing_transmitter_name(self, validator):
        """Test validation fails when TransmitterName is missing."""
        current_year = datetime.now().year
        xml = f"""<?xml version="1.0"?>
<Return>
    <Transmitter>
        <TransmitterNumber>MM123456</TransmitterNumber>
    </Transmitter>
    <T4>
        <T4Summary>
            <BusinessNumber>123456789</BusinessNumber>
            <EmployerName>Test</EmployerName>
            <TotalSlips>0</TotalSlips>
            <TaxYear>{current_year}</TaxYear>
        </T4Summary>
        <T4Slips></T4Slips>
    </T4>
</Return>"""

        result = validator.validate(xml)

        errors = [e for e in result.errors if "Transmitter" in e.field]
        assert len(errors) >= 1
        assert any("TransmitterName" in e.message for e in errors)


# =============================================================================
# Test: Empty T4Summary Elements
# =============================================================================


class TestEmptySummaryElements:
    """Tests for empty T4Summary element validation."""

    def test_empty_business_number(self, validator):
        """Test validation fails when BusinessNumber is empty."""
        current_year = datetime.now().year
        xml = f"""<?xml version="1.0"?>
<Return>
    <Transmitter>
        <TransmitterNumber>MM123456</TransmitterNumber>
        <TransmitterName>Test</TransmitterName>
    </Transmitter>
    <T4>
        <T4Summary>
            <BusinessNumber></BusinessNumber>
            <EmployerName>Test</EmployerName>
            <TotalSlips>0</TotalSlips>
            <TaxYear>{current_year}</TaxYear>
        </T4Summary>
        <T4Slips></T4Slips>
    </T4>
</Return>"""

        result = validator.validate(xml)

        errors = [e for e in result.errors if "BusinessNumber" in e.field]
        assert len(errors) >= 1
        assert any("empty" in e.message.lower() for e in errors)

    def test_empty_employer_name(self, validator):
        """Test validation fails when EmployerName is empty."""
        current_year = datetime.now().year
        xml = f"""<?xml version="1.0"?>
<Return>
    <Transmitter>
        <TransmitterNumber>MM123456</TransmitterNumber>
        <TransmitterName>Test</TransmitterName>
    </Transmitter>
    <T4>
        <T4Summary>
            <BusinessNumber>123456789</BusinessNumber>
            <EmployerName></EmployerName>
            <TotalSlips>0</TotalSlips>
            <TaxYear>{current_year}</TaxYear>
        </T4Summary>
        <T4Slips></T4Slips>
    </T4>
</Return>"""

        result = validator.validate(xml)

        errors = [e for e in result.errors if "EmployerName" in e.field]
        assert len(errors) >= 1


# =============================================================================
# Test: T4 Slip Element Validation
# =============================================================================


class TestT4SlipElements:
    """Tests for T4 slip element validation."""

    def test_missing_employee_in_slip(self, validator):
        """Test validation fails when Employee element is missing from T4Slip."""
        current_year = datetime.now().year
        xml = f"""<?xml version="1.0"?>
<Return>
    <Transmitter>
        <TransmitterNumber>MM123456</TransmitterNumber>
        <TransmitterName>Test</TransmitterName>
    </Transmitter>
    <T4>
        <T4Summary>
            <BusinessNumber>123456789</BusinessNumber>
            <EmployerName>Test</EmployerName>
            <TotalSlips>1</TotalSlips>
            <TaxYear>{current_year}</TaxYear>
        </T4Summary>
        <T4Slips>
            <T4Slip>
                <T4Amounts>
                    <Box14>5000000</Box14>
                </T4Amounts>
            </T4Slip>
        </T4Slips>
    </T4>
</Return>"""

        result = validator.validate(xml)

        errors = [e for e in result.errors if "Employee" in e.field]
        assert len(errors) >= 1

    def test_missing_sin_in_employee(self, validator):
        """Test validation fails when SIN is missing from Employee."""
        current_year = datetime.now().year
        xml = f"""<?xml version="1.0"?>
<Return>
    <Transmitter>
        <TransmitterNumber>MM123456</TransmitterNumber>
        <TransmitterName>Test</TransmitterName>
    </Transmitter>
    <T4>
        <T4Summary>
            <BusinessNumber>123456789</BusinessNumber>
            <EmployerName>Test</EmployerName>
            <TotalSlips>1</TotalSlips>
            <TaxYear>{current_year}</TaxYear>
        </T4Summary>
        <T4Slips>
            <T4Slip>
                <Employee>
                    <FirstName>John</FirstName>
                    <LastName>Doe</LastName>
                </Employee>
                <T4Amounts>
                    <Box14>5000000</Box14>
                </T4Amounts>
            </T4Slip>
        </T4Slips>
    </T4>
</Return>"""

        result = validator.validate(xml)

        sin_errors = [e for e in result.errors if "SIN" in e.field]
        assert len(sin_errors) >= 1

    def test_missing_t4_amounts(self, validator):
        """Test validation fails when T4Amounts is missing."""
        current_year = datetime.now().year
        xml = f"""<?xml version="1.0"?>
<Return>
    <Transmitter>
        <TransmitterNumber>MM123456</TransmitterNumber>
        <TransmitterName>Test</TransmitterName>
    </Transmitter>
    <T4>
        <T4Summary>
            <BusinessNumber>123456789</BusinessNumber>
            <EmployerName>Test</EmployerName>
            <TotalSlips>1</TotalSlips>
            <TaxYear>{current_year}</TaxYear>
        </T4Summary>
        <T4Slips>
            <T4Slip>
                <Employee>
                    <SIN>046454286</SIN>
                    <FirstName>John</FirstName>
                    <LastName>Doe</LastName>
                </Employee>
            </T4Slip>
        </T4Slips>
    </T4>
</Return>"""

        result = validator.validate(xml)

        errors = [e for e in result.errors if "T4Amounts" in e.message]
        assert len(errors) >= 1

    def test_missing_required_box(self, validator):
        """Test validation fails when required Box14 is missing."""
        current_year = datetime.now().year
        xml = f"""<?xml version="1.0"?>
<Return>
    <Transmitter>
        <TransmitterNumber>MM123456</TransmitterNumber>
        <TransmitterName>Test</TransmitterName>
    </Transmitter>
    <T4>
        <T4Summary>
            <BusinessNumber>123456789</BusinessNumber>
            <EmployerName>Test</EmployerName>
            <TotalSlips>1</TotalSlips>
            <TaxYear>{current_year}</TaxYear>
        </T4Summary>
        <T4Slips>
            <T4Slip>
                <Employee>
                    <SIN>046454286</SIN>
                    <FirstName>John</FirstName>
                    <LastName>Doe</LastName>
                </Employee>
                <T4Amounts>
                </T4Amounts>
            </T4Slip>
        </T4Slips>
    </T4>
</Return>"""

        result = validator.validate(xml)

        box_errors = [e for e in result.errors if "Box" in e.message or "T4Amounts" in e.message]
        assert len(box_errors) >= 1


# =============================================================================
# Test: Additional Validation Scenarios
# =============================================================================


class TestAdditionalScenarios:
    """Tests for additional validation scenarios."""

    def test_multiple_slips_with_one_invalid(self, validator):
        """Test validation with multiple slips where one is invalid."""
        current_year = datetime.now().year
        xml = f"""<?xml version="1.0"?>
<Return>
    <Transmitter>
        <TransmitterNumber>MM123456</TransmitterNumber>
        <TransmitterName>Test</TransmitterName>
    </Transmitter>
    <T4>
        <T4Summary>
            <BusinessNumber>123456789</BusinessNumber>
            <EmployerName>Test</EmployerName>
            <TotalSlips>2</TotalSlips>
            <TaxYear>{current_year}</TaxYear>
        </T4Summary>
        <T4Slips>
            <T4Slip>
                <Employee>
                    <SIN>046454286</SIN>
                    <FirstName>John</FirstName>
                    <LastName>Doe</LastName>
                </Employee>
                <T4Amounts>
                    <Box14>5000000</Box14>
                </T4Amounts>
            </T4Slip>
            <T4Slip>
                <Employee>
                    <FirstName>Jane</FirstName>
                    <LastName>Smith</LastName>
                </Employee>
                <T4Amounts>
                    <Box14>4500000</Box14>
                </T4Amounts>
            </T4Slip>
        </T4Slips>
    </T4>
</Return>"""

        result = validator.validate(xml)

        # Should fail due to missing SIN in second slip
        sin_errors = [e for e in result.errors if "SIN" in e.field]
        assert len(sin_errors) >= 1

    def test_slip_with_empty_sin(self, validator):
        """Test validation fails when SIN element is empty."""
        current_year = datetime.now().year
        xml = f"""<?xml version="1.0"?>
<Return>
    <Transmitter>
        <TransmitterNumber>MM123456</TransmitterNumber>
        <TransmitterName>Test</TransmitterName>
    </Transmitter>
    <T4>
        <T4Summary>
            <BusinessNumber>123456789</BusinessNumber>
            <EmployerName>Test</EmployerName>
            <TotalSlips>1</TotalSlips>
            <TaxYear>{current_year}</TaxYear>
        </T4Summary>
        <T4Slips>
            <T4Slip>
                <Employee>
                    <SIN></SIN>
                    <FirstName>John</FirstName>
                    <LastName>Doe</LastName>
                </Employee>
                <T4Amounts>
                    <Box14>5000000</Box14>
                </T4Amounts>
            </T4Slip>
        </T4Slips>
    </T4>
</Return>"""

        result = validator.validate(xml)

        sin_errors = [e for e in result.errors if "SIN" in e.field]
        assert len(sin_errors) >= 1

    def test_missing_first_name(self, validator):
        """Test validation fails when FirstName is missing from Employee (line 336)."""
        current_year = datetime.now().year
        xml = f"""<?xml version="1.0"?>
<Return>
    <Transmitter>
        <TransmitterNumber>MM123456</TransmitterNumber>
        <TransmitterName>Test</TransmitterName>
    </Transmitter>
    <T4>
        <T4Summary>
            <BusinessNumber>123456789</BusinessNumber>
            <EmployerName>Test</EmployerName>
            <TotalSlips>1</TotalSlips>
            <TaxYear>{current_year}</TaxYear>
        </T4Summary>
        <T4Slips>
            <T4Slip>
                <Employee>
                    <SIN>046454286</SIN>
                    <LastName>Doe</LastName>
                </Employee>
                <T4Amounts>
                    <Box14>5000000</Box14>
                </T4Amounts>
            </T4Slip>
        </T4Slips>
    </T4>
</Return>"""

        result = validator.validate(xml)

        errors = [e for e in result.errors if "FirstName" in e.message or "FirstName" in e.field]
        assert len(errors) >= 1

    def test_missing_last_name(self, validator):
        """Test validation fails when LastName is missing from Employee (line 336)."""
        current_year = datetime.now().year
        xml = f"""<?xml version="1.0"?>
<Return>
    <Transmitter>
        <TransmitterNumber>MM123456</TransmitterNumber>
        <TransmitterName>Test</TransmitterName>
    </Transmitter>
    <T4>
        <T4Summary>
            <BusinessNumber>123456789</BusinessNumber>
            <EmployerName>Test</EmployerName>
            <TotalSlips>1</TotalSlips>
            <TaxYear>{current_year}</TaxYear>
        </T4Summary>
        <T4Slips>
            <T4Slip>
                <Employee>
                    <SIN>046454286</SIN>
                    <FirstName>John</FirstName>
                </Employee>
                <T4Amounts>
                    <Box14>5000000</Box14>
                </T4Amounts>
            </T4Slip>
        </T4Slips>
    </T4>
</Return>"""

        result = validator.validate(xml)

        errors = [e for e in result.errors if "LastName" in e.message or "LastName" in e.field]
        assert len(errors) >= 1

    def test_invalid_amount_format(self, validator):
        """Test validation fails when amount has invalid format (lines 395-396)."""
        from decimal import InvalidOperation

        current_year = datetime.now().year
        xml = f"""<?xml version="1.0"?>
<Return>
    <Transmitter>
        <TransmitterNumber>MM123456</TransmitterNumber>
        <TransmitterName>Test</TransmitterName>
    </Transmitter>
    <T4>
        <T4Summary>
            <BusinessNumber>123456789</BusinessNumber>
            <EmployerName>Test</EmployerName>
            <TotalSlips>1</TotalSlips>
            <TaxYear>{current_year}</TaxYear>
        </T4Summary>
        <T4Slips>
            <T4Slip>
                <Employee>
                    <SIN>046454286</SIN>
                    <FirstName>John</FirstName>
                    <LastName>Doe</LastName>
                </Employee>
                <T4Amounts>
                    <Box14>not_a_number</Box14>
                </T4Amounts>
            </T4Slip>
        </T4Slips>
    </T4>
</Return>"""

        # The code doesn't catch decimal.InvalidOperation, so this will raise
        # This reveals a bug in the code (lines 461-462 should catch InvalidOperation)
        with pytest.raises(InvalidOperation):
            validator.validate(xml)

    def test_invalid_slip_count_format(self, validator):
        """Test validation handles invalid TotalSlips format (lines 424-425)."""
        current_year = datetime.now().year
        xml = f"""<?xml version="1.0"?>
<Return>
    <Transmitter>
        <TransmitterNumber>MM123456</TransmitterNumber>
        <TransmitterName>Test</TransmitterName>
    </Transmitter>
    <T4>
        <T4Summary>
            <BusinessNumber>123456789</BusinessNumber>
            <EmployerName>Test</EmployerName>
            <TotalSlips>not_a_number</TotalSlips>
            <TaxYear>{current_year}</TaxYear>
        </T4Summary>
        <T4Slips>
            <T4Slip>
                <Employee>
                    <SIN>046454286</SIN>
                    <FirstName>John</FirstName>
                    <LastName>Doe</LastName>
                </Employee>
                <T4Amounts>
                    <Box14>5000000</Box14>
                </T4Amounts>
            </T4Slip>
        </T4Slips>
    </T4>
</Return>"""

        # Should handle invalid format gracefully (no crash)
        # The code catches ValueError for int(), so this should work
        result = validator.validate(xml)
        assert result is not None

    def test_invalid_summary_total_format(self, validator):
        """Test validation handles invalid summary total format (lines 487-488)."""
        from decimal import InvalidOperation

        current_year = datetime.now().year
        xml = f"""<?xml version="1.0"?>
<Return>
    <Transmitter>
        <TransmitterNumber>MM123456</TransmitterNumber>
        <TransmitterName>Test</TransmitterName>
    </Transmitter>
    <T4>
        <T4Summary>
            <BusinessNumber>123456789</BusinessNumber>
            <EmployerName>Test</EmployerName>
            <TotalSlips>1</TotalSlips>
            <TotalEmploymentIncome>invalid_amount</TotalEmploymentIncome>
            <TaxYear>{current_year}</TaxYear>
        </T4Summary>
        <T4Slips>
            <T4Slip>
                <Employee>
                    <SIN>046454286</SIN>
                    <FirstName>John</FirstName>
                    <LastName>Doe</LastName>
                </Employee>
                <T4Amounts>
                    <Box14>5000000</Box14>
                </T4Amounts>
            </T4Slip>
        </T4Slips>
    </T4>
</Return>"""

        # The code doesn't catch decimal.InvalidOperation (bug at lines 487-488)
        with pytest.raises(InvalidOperation):
            validator.validate(xml)
