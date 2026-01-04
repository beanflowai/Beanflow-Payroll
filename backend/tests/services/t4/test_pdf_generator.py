"""
Tests for T4 PDF generator.

Tests the T4PDFGenerator class which generates T4 slip and summary PDFs.
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.services.t4.pdf_generator import T4PDFGenerator


class TestFormatCurrency:
    """Tests for _format_currency method."""

    @pytest.fixture
    def generator(self) -> T4PDFGenerator:
        """Create a T4PDFGenerator instance."""
        return T4PDFGenerator()

    def test_positive_value(self, generator: T4PDFGenerator):
        """Test formatting positive currency value."""
        result = generator._format_currency(Decimal("1234.56"))
        assert result == "$1,234.56"

    def test_none_value(self, generator: T4PDFGenerator):
        """Test formatting None value."""
        result = generator._format_currency(None)
        assert result == "$0.00"

    def test_zero_value(self, generator: T4PDFGenerator):
        """Test formatting zero value."""
        result = generator._format_currency(Decimal("0"))
        assert result == "$0.00"

    def test_large_value_with_commas(self, generator: T4PDFGenerator):
        """Test formatting large value with comma separators."""
        result = generator._format_currency(Decimal("75000.00"))
        assert result == "$75,000.00"

    def test_small_value(self, generator: T4PDFGenerator):
        """Test formatting small value."""
        result = generator._format_currency(Decimal("0.01"))
        assert result == "$0.01"


class TestGenerateT4SlipPDF:
    """Tests for generate_t4_slip_pdf method."""

    @pytest.fixture
    def generator(self) -> T4PDFGenerator:
        """Create a T4PDFGenerator instance."""
        return T4PDFGenerator()

    @pytest.fixture
    def mock_t4_slip(self) -> MagicMock:
        """Create a mock T4SlipData."""
        slip = MagicMock()
        slip.tax_year = 2025
        slip.employer_name = "Acme Corp"
        slip.employer_address_line1 = "123 Business St"
        slip.employer_city = "Toronto"
        slip.employer_province = MagicMock()
        slip.employer_province.value = "ON"
        slip.employer_postal_code = "M5V 1A1"
        slip.employer_account_number = "123456789RP0001"
        slip.employee_full_name = "John Doe"
        slip.employee_address_line1 = "456 Main Ave"
        slip.employee_city = "Toronto"
        slip.employee_province = MagicMock()
        slip.employee_province.value = "ON"
        slip.employee_postal_code = "M5V 2B2"
        slip.sin_formatted = "***-***-123"
        slip.province_of_employment = MagicMock()
        slip.province_of_employment.value = "ON"
        slip.box_14_employment_income = Decimal("75000")
        slip.box_16_cpp_contributions = Decimal("3754.45")
        slip.box_17_cpp2_contributions = Decimal("0")
        slip.box_18_ei_premiums = Decimal("1077.48")
        slip.box_22_income_tax_deducted = Decimal("15000")
        slip.box_24_ei_insurable_earnings = Decimal("65700")
        slip.box_26_cpp_pensionable_earnings = Decimal("71300")
        slip.box_20_rpp_contributions = None
        slip.box_44_union_dues = None
        slip.box_46_charitable_donations = None
        slip.box_52_pension_adjustment = None
        slip.cpp_exempt = False
        slip.ei_exempt = False
        return slip

    def test_generates_pdf_bytes(
        self, generator: T4PDFGenerator, mock_t4_slip: MagicMock
    ):
        """Test that generate_t4_slip_pdf returns PDF bytes."""
        result = generator.generate_t4_slip_pdf(mock_t4_slip)

        # Check that it returns bytes
        assert isinstance(result, bytes)
        # Check PDF magic bytes
        assert result.startswith(b"%PDF-")
        # Check it ends with PDF EOF marker
        assert b"%%EOF" in result

    def test_pdf_size_is_reasonable(
        self, generator: T4PDFGenerator, mock_t4_slip: MagicMock
    ):
        """Test that PDF has reasonable size."""
        result = generator.generate_t4_slip_pdf(mock_t4_slip)

        # PDF should be at least 1KB for a valid T4 slip
        assert len(result) > 1000

    def test_pdf_with_optional_boxes(
        self, generator: T4PDFGenerator, mock_t4_slip: MagicMock
    ):
        """Test PDF generation with optional boxes filled."""
        mock_t4_slip.box_20_rpp_contributions = Decimal("5000")
        mock_t4_slip.box_44_union_dues = Decimal("500")
        mock_t4_slip.box_46_charitable_donations = Decimal("200")
        mock_t4_slip.box_52_pension_adjustment = Decimal("8000")

        result = generator.generate_t4_slip_pdf(mock_t4_slip)

        assert isinstance(result, bytes)
        assert result.startswith(b"%PDF-")

    def test_pdf_with_exemptions(
        self, generator: T4PDFGenerator, mock_t4_slip: MagicMock
    ):
        """Test PDF generation with CPP/EI exemptions."""
        mock_t4_slip.cpp_exempt = True
        mock_t4_slip.ei_exempt = True

        result = generator.generate_t4_slip_pdf(mock_t4_slip)

        assert isinstance(result, bytes)
        assert result.startswith(b"%PDF-")

    def test_pdf_with_cpp2_contributions(
        self, generator: T4PDFGenerator, mock_t4_slip: MagicMock
    ):
        """Test PDF generation with CPP2 contributions."""
        mock_t4_slip.box_17_cpp2_contributions = Decimal("396")

        result = generator.generate_t4_slip_pdf(mock_t4_slip)

        assert isinstance(result, bytes)
        assert result.startswith(b"%PDF-")

    def test_pdf_without_address_details(
        self, generator: T4PDFGenerator, mock_t4_slip: MagicMock
    ):
        """Test PDF generation with minimal address info."""
        mock_t4_slip.employer_address_line1 = None
        mock_t4_slip.employer_city = None
        mock_t4_slip.employee_address_line1 = None
        mock_t4_slip.employee_city = None

        result = generator.generate_t4_slip_pdf(mock_t4_slip)

        assert isinstance(result, bytes)
        assert result.startswith(b"%PDF-")


class TestGenerateT4SummaryPDF:
    """Tests for generate_t4_summary_pdf method."""

    @pytest.fixture
    def generator(self) -> T4PDFGenerator:
        """Create a T4PDFGenerator instance."""
        return T4PDFGenerator()

    @pytest.fixture
    def mock_t4_summary(self) -> MagicMock:
        """Create a mock T4Summary."""
        summary = MagicMock()
        summary.tax_year = 2025
        summary.employer_name = "Acme Corp"
        summary.employer_address_line1 = "123 Business St"
        summary.employer_city = "Toronto"
        summary.employer_province = MagicMock()
        summary.employer_province.value = "ON"
        summary.employer_postal_code = "M5V 1A1"
        summary.employer_account_number = "123456789RP0001"
        summary.total_number_of_t4_slips = 50
        summary.total_employment_income = Decimal("2500000")
        summary.total_cpp_contributions = Decimal("125000")
        summary.total_cpp2_contributions = Decimal("10000")
        summary.total_ei_premiums = Decimal("41000")
        summary.total_income_tax_deducted = Decimal("500000")
        summary.total_union_dues = Decimal("12000")
        summary.total_cpp_employer = Decimal("125000")
        summary.total_ei_employer = Decimal("57400")
        summary.total_employer_contributions = Decimal("182400")
        summary.total_remittance_required = Decimal("858400")
        return summary

    def test_generates_pdf_bytes(
        self, generator: T4PDFGenerator, mock_t4_summary: MagicMock
    ):
        """Test that generate_t4_summary_pdf returns PDF bytes."""
        result = generator.generate_t4_summary_pdf(mock_t4_summary)

        # Check that it returns bytes
        assert isinstance(result, bytes)
        # Check PDF magic bytes
        assert result.startswith(b"%PDF-")
        # Check it ends with PDF EOF marker
        assert b"%%EOF" in result

    def test_pdf_size_is_reasonable(
        self, generator: T4PDFGenerator, mock_t4_summary: MagicMock
    ):
        """Test that PDF has reasonable size."""
        result = generator.generate_t4_summary_pdf(mock_t4_summary)

        # PDF should be at least 1KB for a valid T4 summary
        assert len(result) > 1000

    def test_pdf_contains_page_content(
        self, generator: T4PDFGenerator, mock_t4_summary: MagicMock
    ):
        """Test that PDF contains page content stream."""
        result = generator.generate_t4_summary_pdf(mock_t4_summary)

        assert b"stream" in result
        assert b"endstream" in result

    def test_pdf_with_slips_parameter(
        self, generator: T4PDFGenerator, mock_t4_summary: MagicMock
    ):
        """Test PDF generation with slips parameter."""
        mock_slips = [MagicMock(), MagicMock()]

        result = generator.generate_t4_summary_pdf(mock_t4_summary, slips=mock_slips)

        assert isinstance(result, bytes)
        assert result.startswith(b"%PDF-")


class TestBuildTitleSection:
    """Tests for _build_title_section method."""

    @pytest.fixture
    def generator(self) -> T4PDFGenerator:
        """Create a T4PDFGenerator instance."""
        return T4PDFGenerator()

    def test_title_section(self, generator: T4PDFGenerator):
        """Test building title section."""
        elements: list = []
        slip = MagicMock()
        slip.tax_year = 2025

        generator._build_title_section(elements, slip)

        assert len(elements) == 2  # Title + subtitle


class TestBuildEmployerSection:
    """Tests for _build_employer_section method."""

    @pytest.fixture
    def generator(self) -> T4PDFGenerator:
        """Create a T4PDFGenerator instance."""
        return T4PDFGenerator()

    def test_employer_section_with_full_address(self, generator: T4PDFGenerator):
        """Test building employer section with full address."""
        elements: list = []
        slip = MagicMock()
        slip.employer_name = "Acme Corp"
        slip.employer_address_line1 = "123 Business St"
        slip.employer_city = "Toronto"
        slip.employer_province = MagicMock()
        slip.employer_province.value = "ON"
        slip.employer_postal_code = "M5V 1A1"
        slip.employer_account_number = "123456789RP0001"

        generator._build_employer_section(elements, slip)

        # Should have section header and table
        assert len(elements) == 2

    def test_employer_section_minimal(self, generator: T4PDFGenerator):
        """Test building employer section with minimal info."""
        elements: list = []
        slip = MagicMock()
        slip.employer_name = "Acme Corp"
        slip.employer_address_line1 = None
        slip.employer_city = None
        slip.employer_province = None
        slip.employer_postal_code = None
        slip.employer_account_number = "123456789RP0001"

        generator._build_employer_section(elements, slip)

        assert len(elements) == 2


class TestBuildEmployeeSection:
    """Tests for _build_employee_section method."""

    @pytest.fixture
    def generator(self) -> T4PDFGenerator:
        """Create a T4PDFGenerator instance."""
        return T4PDFGenerator()

    def test_employee_section_with_full_address(self, generator: T4PDFGenerator):
        """Test building employee section with full address."""
        elements: list = []
        slip = MagicMock()
        slip.employee_full_name = "John Doe"
        slip.employee_address_line1 = "456 Main Ave"
        slip.employee_city = "Toronto"
        slip.employee_province = MagicMock()
        slip.employee_province.value = "ON"
        slip.employee_postal_code = "M5V 2B2"
        slip.sin_formatted = "***-***-123"

        generator._build_employee_section(elements, slip)

        assert len(elements) == 2

    def test_employee_section_minimal(self, generator: T4PDFGenerator):
        """Test building employee section with minimal info."""
        elements: list = []
        slip = MagicMock()
        slip.employee_full_name = "John Doe"
        slip.employee_address_line1 = None
        slip.employee_city = None
        slip.employee_province = None
        slip.employee_postal_code = None
        slip.sin_formatted = "***-***-123"

        generator._build_employee_section(elements, slip)

        assert len(elements) == 2


class TestBuildBoxesSection:
    """Tests for _build_boxes_section method."""

    @pytest.fixture
    def generator(self) -> T4PDFGenerator:
        """Create a T4PDFGenerator instance."""
        return T4PDFGenerator()

    def test_boxes_section_with_required_boxes(self, generator: T4PDFGenerator):
        """Test building boxes section with required boxes only."""
        elements: list = []
        slip = MagicMock()
        slip.box_14_employment_income = Decimal("75000")
        slip.box_16_cpp_contributions = Decimal("3754.45")
        slip.box_17_cpp2_contributions = Decimal("0")
        slip.box_18_ei_premiums = Decimal("1077.48")
        slip.box_22_income_tax_deducted = Decimal("15000")
        slip.box_24_ei_insurable_earnings = Decimal("65700")
        slip.box_26_cpp_pensionable_earnings = Decimal("71300")
        slip.box_20_rpp_contributions = None
        slip.box_44_union_dues = None
        slip.box_46_charitable_donations = None
        slip.box_52_pension_adjustment = None

        generator._build_boxes_section(elements, slip)

        # Should have section header and table
        assert len(elements) == 2

    def test_boxes_section_with_optional_boxes(self, generator: T4PDFGenerator):
        """Test building boxes section with optional boxes."""
        elements: list = []
        slip = MagicMock()
        slip.box_14_employment_income = Decimal("75000")
        slip.box_16_cpp_contributions = Decimal("3754.45")
        slip.box_17_cpp2_contributions = Decimal("396")
        slip.box_18_ei_premiums = Decimal("1077.48")
        slip.box_22_income_tax_deducted = Decimal("15000")
        slip.box_24_ei_insurable_earnings = Decimal("65700")
        slip.box_26_cpp_pensionable_earnings = Decimal("71300")
        slip.box_20_rpp_contributions = Decimal("5000")
        slip.box_44_union_dues = Decimal("500")
        slip.box_46_charitable_donations = Decimal("200")
        slip.box_52_pension_adjustment = Decimal("8000")

        generator._build_boxes_section(elements, slip)

        assert len(elements) == 2


class TestBuildProvinceSection:
    """Tests for _build_province_section method."""

    @pytest.fixture
    def generator(self) -> T4PDFGenerator:
        """Create a T4PDFGenerator instance."""
        return T4PDFGenerator()

    def test_province_section_no_exemptions(self, generator: T4PDFGenerator):
        """Test building province section without exemptions."""
        elements: list = []
        slip = MagicMock()
        slip.province_of_employment = MagicMock()
        slip.province_of_employment.value = "ON"
        slip.cpp_exempt = False
        slip.ei_exempt = False

        generator._build_province_section(elements, slip)

        assert len(elements) == 1

    def test_province_section_with_cpp_exemption(self, generator: T4PDFGenerator):
        """Test building province section with CPP exemption."""
        elements: list = []
        slip = MagicMock()
        slip.province_of_employment = MagicMock()
        slip.province_of_employment.value = "ON"
        slip.cpp_exempt = True
        slip.ei_exempt = False

        generator._build_province_section(elements, slip)

        assert len(elements) == 1

    def test_province_section_with_both_exemptions(self, generator: T4PDFGenerator):
        """Test building province section with both exemptions."""
        elements: list = []
        slip = MagicMock()
        slip.province_of_employment = MagicMock()
        slip.province_of_employment.value = "ON"
        slip.cpp_exempt = True
        slip.ei_exempt = True

        generator._build_province_section(elements, slip)

        assert len(elements) == 1


class TestBuildFooterSection:
    """Tests for _build_footer_section method."""

    @pytest.fixture
    def generator(self) -> T4PDFGenerator:
        """Create a T4PDFGenerator instance."""
        return T4PDFGenerator()

    def test_footer_section(self, generator: T4PDFGenerator):
        """Test building footer section."""
        elements: list = []
        slip = MagicMock()

        generator._build_footer_section(elements, slip)

        assert len(elements) == 1


class TestBuildSummaryEmployerSection:
    """Tests for _build_summary_employer_section method."""

    @pytest.fixture
    def generator(self) -> T4PDFGenerator:
        """Create a T4PDFGenerator instance."""
        return T4PDFGenerator()

    def test_summary_employer_section(self, generator: T4PDFGenerator):
        """Test building summary employer section."""
        elements: list = []
        summary = MagicMock()
        summary.employer_name = "Acme Corp"
        summary.employer_address_line1 = "123 Business St"
        summary.employer_city = "Toronto"
        summary.employer_province = MagicMock()
        summary.employer_province.value = "ON"
        summary.employer_postal_code = "M5V 1A1"
        summary.employer_account_number = "123456789RP0001"
        summary.total_number_of_t4_slips = 50

        generator._build_summary_employer_section(elements, summary)

        assert len(elements) == 2


class TestBuildSummaryTotalsSection:
    """Tests for _build_summary_totals_section method."""

    @pytest.fixture
    def generator(self) -> T4PDFGenerator:
        """Create a T4PDFGenerator instance."""
        return T4PDFGenerator()

    def test_summary_totals_section(self, generator: T4PDFGenerator):
        """Test building summary totals section."""
        elements: list = []
        summary = MagicMock()
        summary.total_employment_income = Decimal("2500000")
        summary.total_cpp_contributions = Decimal("125000")
        summary.total_cpp2_contributions = Decimal("10000")
        summary.total_ei_premiums = Decimal("41000")
        summary.total_income_tax_deducted = Decimal("500000")
        summary.total_union_dues = Decimal("12000")

        generator._build_summary_totals_section(elements, summary)

        assert len(elements) == 2


class TestBuildEmployerContributionsSection:
    """Tests for _build_employer_contributions_section method."""

    @pytest.fixture
    def generator(self) -> T4PDFGenerator:
        """Create a T4PDFGenerator instance."""
        return T4PDFGenerator()

    def test_employer_contributions_section(self, generator: T4PDFGenerator):
        """Test building employer contributions section."""
        elements: list = []
        summary = MagicMock()
        summary.total_cpp_employer = Decimal("125000")
        summary.total_ei_employer = Decimal("57400")
        summary.total_employer_contributions = Decimal("182400")

        generator._build_employer_contributions_section(elements, summary)

        assert len(elements) == 2


class TestBuildRemittanceSection:
    """Tests for _build_remittance_section method."""

    @pytest.fixture
    def generator(self) -> T4PDFGenerator:
        """Create a T4PDFGenerator instance."""
        return T4PDFGenerator()

    def test_remittance_section(self, generator: T4PDFGenerator):
        """Test building remittance section."""
        elements: list = []
        summary = MagicMock()
        summary.total_cpp_contributions = Decimal("125000")
        summary.total_cpp2_contributions = Decimal("10000")
        summary.total_cpp_employer = Decimal("125000")
        summary.total_ei_premiums = Decimal("41000")
        summary.total_ei_employer = Decimal("57400")
        summary.total_income_tax_deducted = Decimal("500000")
        summary.total_remittance_required = Decimal("858400")

        generator._build_remittance_section(elements, summary)

        assert len(elements) == 2


class TestCustomStyles:
    """Tests for custom styles initialization."""

    def test_styles_are_initialized(self):
        """Test that custom styles are properly initialized."""
        generator = T4PDFGenerator()

        assert generator.styles is not None
        assert "T4Title" in generator.styles.byName
        assert "T4Subtitle" in generator.styles.byName
        assert "SectionHeader" in generator.styles.byName
        assert "BoxLabel" in generator.styles.byName
        assert "BoxValue" in generator.styles.byName
