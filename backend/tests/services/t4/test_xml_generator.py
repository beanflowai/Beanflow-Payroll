"""
Tests for T4 XML Generator

Tests for generating CRA T619 XML format for T4 electronic filing.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from app.models.payroll import Province
from app.models.t4 import T4SlipData, T4Status, T4Summary
from app.services.t4.xml_generator import T4XMLGenerator


# =============================================================================
# Test Constants
# =============================================================================

TEST_USER_ID = "test-user-id-12345"
TEST_COMPANY_ID = str(uuid4())
TEST_EMPLOYEE_ID = str(uuid4())
TEST_TAX_YEAR = 2025


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def generator() -> T4XMLGenerator:
    """Create a T4 XML generator instance."""
    return T4XMLGenerator(
        transmitter_number="MM123456",
        transmitter_name="Test Payroll Software",
    )


@pytest.fixture
def sample_slip() -> T4SlipData:
    """Create a sample T4 slip."""
    return T4SlipData(
        employee_id=UUID(TEST_EMPLOYEE_ID),
        tax_year=TEST_TAX_YEAR,
        sin="123456789",
        employee_first_name="John",
        employee_last_name="Doe",
        employee_address_line1="123 Employee St",
        employee_city="Toronto",
        employee_province=Province.ON,
        employee_postal_code="M4K 2A1",
        employer_name="Test Company Inc.",
        employer_account_number="123456789RP0001",
        employer_address_line1="456 Company Ave",
        employer_city="Toronto",
        employer_province=Province.ON,
        employer_postal_code="M5V 1A1",
        box_14_employment_income=Decimal("50000.00"),
        box_16_cpp_contributions=Decimal("3800.00"),
        box_17_cpp2_contributions=Decimal("500.00"),
        box_18_ei_premiums=Decimal("1049.12"),
        box_22_income_tax_deducted=Decimal("8500.00"),
        box_24_ei_insurable_earnings=Decimal("50000.00"),
        box_26_cpp_pensionable_earnings=Decimal("50000.00"),
        box_44_union_dues=Decimal("500.00"),
        province_of_employment=Province.ON,
        cpp_exempt=False,
        ei_exempt=False,
    )


@pytest.fixture
def sample_summary() -> T4Summary:
    """Create a sample T4 summary."""
    return T4Summary(
        company_id=UUID(TEST_COMPANY_ID),
        user_id=TEST_USER_ID,
        tax_year=TEST_TAX_YEAR,
        employer_name="Test Company Inc.",
        employer_account_number="123456789RP0001",
        employer_address_line1="456 Company Ave",
        employer_city="Toronto",
        employer_province=Province.ON,
        employer_postal_code="M5V 1A1",
        total_number_of_t4_slips=2,
        total_employment_income=Decimal("100000.00"),
        total_cpp_contributions=Decimal("7600.00"),
        total_cpp2_contributions=Decimal("1000.00"),
        total_ei_premiums=Decimal("2098.24"),
        total_income_tax_deducted=Decimal("17000.00"),
        total_union_dues=Decimal("1000.00"),
        total_cpp_employer=Decimal("7600.00"),
        total_ei_employer=Decimal("2937.54"),
        status=T4Status.GENERATED,
    )


# =============================================================================
# Test: Initialization
# =============================================================================


class TestXMLGeneratorInit:
    """Tests for XML generator initialization."""

    def test_default_transmitter_info(self):
        """Test default transmitter information."""
        generator = T4XMLGenerator()

        assert generator.transmitter_number == "MM000000"
        assert generator.transmitter_name == "Beanflow Payroll"

    def test_custom_transmitter_info(self):
        """Test custom transmitter information."""
        generator = T4XMLGenerator(
            transmitter_number="MM123456",
            transmitter_name="Custom Payroll",
        )

        assert generator.transmitter_number == "MM123456"
        assert generator.transmitter_name == "Custom Payroll"


# =============================================================================
# Test: _format_amount
# =============================================================================


class TestFormatAmount:
    """Tests for amount formatting."""

    def test_format_whole_number(self, generator):
        """Test formatting whole numbers."""
        result = generator._format_amount(Decimal("100.00"))
        assert result == "10000"

    def test_format_with_cents(self, generator):
        """Test formatting numbers with cents."""
        result = generator._format_amount(Decimal("123.45"))
        assert result == "12345"

    def test_format_zero(self, generator):
        """Test formatting zero."""
        result = generator._format_amount(Decimal("0"))
        assert result == "0"

    def test_format_none(self, generator):
        """Test formatting None returns '0'."""
        result = generator._format_amount(None)
        assert result == "0"

    def test_format_large_amount(self, generator):
        """Test formatting large amounts."""
        result = generator._format_amount(Decimal("1000000.00"))
        assert result == "100000000"


# =============================================================================
# Test: generate_xml
# =============================================================================


class TestGenerateXml:
    """Tests for XML generation."""

    def test_generate_xml_basic_structure(self, generator, sample_summary, sample_slip):
        """Test basic XML structure is correct."""
        xml = generator.generate_xml(sample_summary, [sample_slip])

        assert '<?xml version="1.0"' in xml
        assert "<Return" in xml
        assert "</Return>" in xml
        assert "<Transmitter>" in xml
        assert "<T4>" in xml
        assert "<T4Summary>" in xml
        assert "<T4Slips>" in xml

    def test_generate_xml_includes_transmitter(self, generator, sample_summary, sample_slip):
        """Test XML includes transmitter information."""
        xml = generator.generate_xml(sample_summary, [sample_slip])

        assert "<TransmitterNumber>MM123456</TransmitterNumber>" in xml
        assert "<TransmitterName>Test Payroll Software</TransmitterName>" in xml
        assert "<TransmitterType>3</TransmitterType>" in xml

    def test_generate_xml_includes_summary(self, generator, sample_summary, sample_slip):
        """Test XML includes summary data."""
        xml = generator.generate_xml(sample_summary, [sample_slip])

        assert "<BusinessNumber>123456789</BusinessNumber>" in xml
        assert "<EmployerName>Test Company Inc.</EmployerName>" in xml
        assert "<TotalSlips>2</TotalSlips>" in xml
        assert f"<TaxYear>{TEST_TAX_YEAR}</TaxYear>" in xml

    def test_generate_xml_includes_slip(self, generator, sample_summary, sample_slip):
        """Test XML includes slip data."""
        xml = generator.generate_xml(sample_summary, [sample_slip])

        assert "<T4Slip>" in xml
        assert "<SIN>123456789</SIN>" in xml
        assert "<FirstName>John</FirstName>" in xml
        assert "<LastName>Doe</LastName>" in xml
        assert "<Box10>ON</Box10>" in xml  # Province of employment
        assert "<Box14>5000000</Box14>" in xml  # Employment income in cents

    def test_generate_xml_multiple_slips(self, generator, sample_summary, sample_slip):
        """Test XML with multiple slips."""
        slip2 = T4SlipData(
            employee_id=UUID(str(uuid4())),
            tax_year=TEST_TAX_YEAR,
            sin="987654321",
            employee_first_name="Jane",
            employee_last_name="Smith",
            employer_name="Test Company Inc.",
            employer_account_number="123456789RP0001",
            box_14_employment_income=Decimal("60000.00"),
            box_16_cpp_contributions=Decimal("4200.00"),
            box_18_ei_premiums=Decimal("1200.00"),
            box_22_income_tax_deducted=Decimal("10000.00"),
            box_24_ei_insurable_earnings=Decimal("60000.00"),
            box_26_cpp_pensionable_earnings=Decimal("60000.00"),
            province_of_employment=Province.BC,
        )

        xml = generator.generate_xml(sample_summary, [sample_slip, slip2])

        # Should have two slip sections
        assert xml.count("<T4Slip>") == 2
        assert "<SIN>123456789</SIN>" in xml
        assert "<SIN>987654321</SIN>" in xml
        assert "<FirstName>John</FirstName>" in xml
        assert "<FirstName>Jane</FirstName>" in xml

    def test_generate_xml_optional_fields(self, generator, sample_summary, sample_slip):
        """Test XML includes optional fields when present."""
        # The sample slip has union dues
        xml = generator.generate_xml(sample_summary, [sample_slip])

        assert "<Box44>50000</Box44>" in xml  # Union dues in cents

    def test_generate_xml_exemptions(self, generator, sample_summary):
        """Test XML includes exemption flags."""
        exempt_slip = T4SlipData(
            employee_id=UUID(str(uuid4())),
            tax_year=TEST_TAX_YEAR,
            sin="111222333",
            employee_first_name="Test",
            employee_last_name="Exempt",
            employer_name="Test Company Inc.",
            employer_account_number="123456789RP0001",
            box_14_employment_income=Decimal("10000.00"),
            box_16_cpp_contributions=Decimal("0"),
            box_18_ei_premiums=Decimal("0"),
            box_22_income_tax_deducted=Decimal("1000.00"),
            box_24_ei_insurable_earnings=Decimal("0"),
            box_26_cpp_pensionable_earnings=Decimal("0"),
            province_of_employment=Province.ON,
            cpp_exempt=True,
            ei_exempt=True,
        )

        xml = generator.generate_xml(sample_summary, [exempt_slip])

        assert "<CPPExempt>Y</CPPExempt>" in xml
        assert "<EIExempt>Y</EIExempt>" in xml

    def test_generate_xml_postal_code_no_space(self, generator, sample_summary, sample_slip):
        """Test postal codes are formatted without spaces."""
        xml = generator.generate_xml(sample_summary, [sample_slip])

        # M5V 1A1 should become M5V1A1
        assert "M5V1A1" in xml or "M4K2A1" in xml

    def test_generate_xml_cpp2_only_when_positive(self, generator, sample_summary):
        """Test CPP2 box only appears when positive."""
        slip_no_cpp2 = T4SlipData(
            employee_id=UUID(str(uuid4())),
            tax_year=TEST_TAX_YEAR,
            sin="111222333",
            employee_first_name="Test",
            employee_last_name="NoCPP2",
            employer_name="Test Company Inc.",
            employer_account_number="123456789RP0001",
            box_14_employment_income=Decimal("50000.00"),
            box_16_cpp_contributions=Decimal("3800.00"),
            box_17_cpp2_contributions=Decimal("0"),  # No CPP2
            box_18_ei_premiums=Decimal("1000.00"),
            box_22_income_tax_deducted=Decimal("8000.00"),
            box_24_ei_insurable_earnings=Decimal("50000.00"),
            box_26_cpp_pensionable_earnings=Decimal("50000.00"),
            province_of_employment=Province.ON,
        )

        xml = generator.generate_xml(sample_summary, [slip_no_cpp2])

        # Box17 should not appear when CPP2 is 0
        assert "<Box17>" not in xml


# =============================================================================
# Test: generate_xml_filename
# =============================================================================


class TestGenerateXmlFilename:
    """Tests for XML filename generation."""

    def test_generate_filename(self, generator, sample_summary):
        """Test filename generation."""
        filename = generator.generate_xml_filename(sample_summary)

        assert filename == f"T4_123456789RP0001_{TEST_TAX_YEAR}.xml"

    def test_generate_filename_removes_spaces(self, generator):
        """Test filename removes spaces from account number."""
        summary = T4Summary(
            company_id=UUID(TEST_COMPANY_ID),
            user_id=TEST_USER_ID,
            tax_year=TEST_TAX_YEAR,
            employer_name="Test",
            employer_account_number="123 456 789RP0001",  # With spaces
            status=T4Status.GENERATED,
        )

        filename = generator.generate_xml_filename(summary)

        assert filename == f"T4_123456789RP0001_{TEST_TAX_YEAR}.xml"


# =============================================================================
# Test: _prettify
# =============================================================================


class TestPrettify:
    """Tests for XML prettification."""

    def test_prettify_adds_declaration(self, generator):
        """Test prettify adds XML declaration."""
        simple_xml = "<root><child>test</child></root>"
        result = generator._prettify(simple_xml)

        assert '<?xml version="1.0"' in result
        assert "encoding=" in result

    def test_prettify_indents(self, generator):
        """Test prettify adds indentation."""
        simple_xml = "<root><child>test</child></root>"
        result = generator._prettify(simple_xml)

        # Should have newlines and indentation
        assert "\n" in result


# =============================================================================
# Test: Optional Fields Coverage
# =============================================================================


class TestOptionalFields:
    """Tests for optional T4 fields (lines 173, 202, 219, 223)."""

    def test_slip_with_address_line_2(self, generator):
        """Test slip with address line 2 (line 173)."""
        slip = T4SlipData(
            employee_id=UUID(TEST_EMPLOYEE_ID),
            tax_year=TEST_TAX_YEAR,
            sin="123456789",
            employee_first_name="John",
            employee_last_name="Doe",
            employee_address_line1="123 Employee St",
            employee_address_line2="Apt 4B",  # Optional field
            employee_city="Toronto",
            employee_province=Province.ON,
            employee_postal_code="M4K 2A1",
            employer_name="Test Company Inc.",
            employer_account_number="123456789RP0001",
            employer_address_line1="456 Company Ave",
            employer_city="Toronto",
            employer_province=Province.ON,
            employer_postal_code="M5V 1A1",
            box_14_employment_income=Decimal("50000.00"),
            box_16_cpp_contributions=Decimal("3800.00"),
            box_18_ei_premiums=Decimal("1049.12"),
            box_22_income_tax_deducted=Decimal("8500.00"),
            box_24_ei_insurable_earnings=Decimal("50000.00"),
            box_26_cpp_pensionable_earnings=Decimal("50000.00"),
            province_of_employment=Province.ON,
            cpp_exempt=False,
            ei_exempt=False,
        )

        summary = T4Summary(
            company_id=UUID(TEST_COMPANY_ID),
            user_id=TEST_USER_ID,
            tax_year=TEST_TAX_YEAR,
            employer_name="Test Company Inc.",
            employer_account_number="123456789RP0001",
            employer_address_line1="456 Company Ave",
            employer_city="Toronto",
            employer_province=Province.ON,
            employer_postal_code="M5V 1A1",
            total_number_of_t4_slips=1,
            total_employment_income=Decimal("50000.00"),
            total_cpp_contributions=Decimal("3800.00"),
            total_ei_premiums=Decimal("1049.12"),
            total_income_tax_deducted=Decimal("8500.00"),
            total_cpp_employer=Decimal("3800.00"),
            total_ei_employer=Decimal("1463.77"),
            status=T4Status.GENERATED,
        )

        xml_output = generator.generate_xml(summary, [slip])

        # Verify Address2 is in the XML
        assert "Apt 4B" in xml_output

    def test_slip_with_rpp_contributions(self, generator):
        """Test slip with RPP contributions - Box 20 (line 202)."""
        slip = T4SlipData(
            employee_id=UUID(TEST_EMPLOYEE_ID),
            tax_year=TEST_TAX_YEAR,
            sin="123456789",
            employee_first_name="John",
            employee_last_name="Doe",
            employee_address_line1="123 Employee St",
            employee_city="Toronto",
            employee_province=Province.ON,
            employee_postal_code="M4K 2A1",
            employer_name="Test Company Inc.",
            employer_account_number="123456789RP0001",
            employer_address_line1="456 Company Ave",
            employer_city="Toronto",
            employer_province=Province.ON,
            employer_postal_code="M5V 1A1",
            box_14_employment_income=Decimal("50000.00"),
            box_16_cpp_contributions=Decimal("3800.00"),
            box_18_ei_premiums=Decimal("1049.12"),
            box_20_rpp_contributions=Decimal("2000.00"),  # Optional field
            box_22_income_tax_deducted=Decimal("8500.00"),
            box_24_ei_insurable_earnings=Decimal("50000.00"),
            box_26_cpp_pensionable_earnings=Decimal("50000.00"),
            province_of_employment=Province.ON,
            cpp_exempt=False,
            ei_exempt=False,
        )

        summary = T4Summary(
            company_id=UUID(TEST_COMPANY_ID),
            user_id=TEST_USER_ID,
            tax_year=TEST_TAX_YEAR,
            employer_name="Test Company Inc.",
            employer_account_number="123456789RP0001",
            employer_address_line1="456 Company Ave",
            employer_city="Toronto",
            employer_province=Province.ON,
            employer_postal_code="M5V 1A1",
            total_number_of_t4_slips=1,
            total_employment_income=Decimal("50000.00"),
            total_cpp_contributions=Decimal("3800.00"),
            total_ei_premiums=Decimal("1049.12"),
            total_income_tax_deducted=Decimal("8500.00"),
            total_cpp_employer=Decimal("3800.00"),
            total_ei_employer=Decimal("1463.77"),
            status=T4Status.GENERATED,
        )

        xml_output = generator.generate_xml(summary, [slip])

        # Verify Box20 is in the XML (amount in cents: 2000.00 -> 200000)
        assert "<Box20>200000</Box20>" in xml_output

    def test_slip_with_charitable_donations(self, generator):
        """Test slip with charitable donations - Box 46 (line 219)."""
        slip = T4SlipData(
            employee_id=UUID(TEST_EMPLOYEE_ID),
            tax_year=TEST_TAX_YEAR,
            sin="123456789",
            employee_first_name="John",
            employee_last_name="Doe",
            employee_address_line1="123 Employee St",
            employee_city="Toronto",
            employee_province=Province.ON,
            employee_postal_code="M4K 2A1",
            employer_name="Test Company Inc.",
            employer_account_number="123456789RP0001",
            employer_address_line1="456 Company Ave",
            employer_city="Toronto",
            employer_province=Province.ON,
            employer_postal_code="M5V 1A1",
            box_14_employment_income=Decimal("50000.00"),
            box_16_cpp_contributions=Decimal("3800.00"),
            box_18_ei_premiums=Decimal("1049.12"),
            box_22_income_tax_deducted=Decimal("8500.00"),
            box_24_ei_insurable_earnings=Decimal("50000.00"),
            box_26_cpp_pensionable_earnings=Decimal("50000.00"),
            box_46_charitable_donations=Decimal("500.00"),  # Optional field
            province_of_employment=Province.ON,
            cpp_exempt=False,
            ei_exempt=False,
        )

        summary = T4Summary(
            company_id=UUID(TEST_COMPANY_ID),
            user_id=TEST_USER_ID,
            tax_year=TEST_TAX_YEAR,
            employer_name="Test Company Inc.",
            employer_account_number="123456789RP0001",
            employer_address_line1="456 Company Ave",
            employer_city="Toronto",
            employer_province=Province.ON,
            employer_postal_code="M5V 1A1",
            total_number_of_t4_slips=1,
            total_employment_income=Decimal("50000.00"),
            total_cpp_contributions=Decimal("3800.00"),
            total_ei_premiums=Decimal("1049.12"),
            total_income_tax_deducted=Decimal("8500.00"),
            total_cpp_employer=Decimal("3800.00"),
            total_ei_employer=Decimal("1463.77"),
            status=T4Status.GENERATED,
        )

        xml_output = generator.generate_xml(summary, [slip])

        # Verify Box46 is in the XML (amount in cents: 500.00 -> 50000)
        assert "<Box46>50000</Box46>" in xml_output

    def test_slip_with_pension_adjustment(self, generator):
        """Test slip with pension adjustment - Box 52 (line 223)."""
        slip = T4SlipData(
            employee_id=UUID(TEST_EMPLOYEE_ID),
            tax_year=TEST_TAX_YEAR,
            sin="123456789",
            employee_first_name="John",
            employee_last_name="Doe",
            employee_address_line1="123 Employee St",
            employee_city="Toronto",
            employee_province=Province.ON,
            employee_postal_code="M4K 2A1",
            employer_name="Test Company Inc.",
            employer_account_number="123456789RP0001",
            employer_address_line1="456 Company Ave",
            employer_city="Toronto",
            employer_province=Province.ON,
            employer_postal_code="M5V 1A1",
            box_14_employment_income=Decimal("50000.00"),
            box_16_cpp_contributions=Decimal("3800.00"),
            box_18_ei_premiums=Decimal("1049.12"),
            box_22_income_tax_deducted=Decimal("8500.00"),
            box_24_ei_insurable_earnings=Decimal("50000.00"),
            box_26_cpp_pensionable_earnings=Decimal("50000.00"),
            box_52_pension_adjustment=Decimal("1500.00"),  # Optional field
            province_of_employment=Province.ON,
            cpp_exempt=False,
            ei_exempt=False,
        )

        summary = T4Summary(
            company_id=UUID(TEST_COMPANY_ID),
            user_id=TEST_USER_ID,
            tax_year=TEST_TAX_YEAR,
            employer_name="Test Company Inc.",
            employer_account_number="123456789RP0001",
            employer_address_line1="456 Company Ave",
            employer_city="Toronto",
            employer_province=Province.ON,
            employer_postal_code="M5V 1A1",
            total_number_of_t4_slips=1,
            total_employment_income=Decimal("50000.00"),
            total_cpp_contributions=Decimal("3800.00"),
            total_ei_premiums=Decimal("1049.12"),
            total_income_tax_deducted=Decimal("8500.00"),
            total_cpp_employer=Decimal("3800.00"),
            total_ei_employer=Decimal("1463.77"),
            status=T4Status.GENERATED,
        )

        xml_output = generator.generate_xml(summary, [slip])

        # Verify Box52 is in the XML (amount in cents: 1500.00 -> 150000)
        assert "<Box52>150000</Box52>" in xml_output
