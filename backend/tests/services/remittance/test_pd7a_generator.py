"""
Tests for PD7A Remittance Voucher PDF Generator.

Tests the PD7APDFGenerator class which generates PD7A voucher PDFs.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.services.remittance.pd7a_generator import PD7APDFGenerator


class TestGeneratePDF:
    """Tests for generate_pdf method."""

    @pytest.fixture
    def generator(self) -> PD7APDFGenerator:
        """Create a PD7APDFGenerator instance."""
        return PD7APDFGenerator()

    @pytest.fixture
    def mock_voucher(self) -> MagicMock:
        """Create a mock PD7ARemittanceVoucher."""
        voucher = MagicMock()
        voucher.employer_name = "Acme Corp"
        voucher.payroll_account_number = "123456789RP0001"
        voucher.period_start = date(2025, 1, 1)
        voucher.period_end = date(2025, 1, 31)
        voucher.due_date = date(2025, 2, 15)
        voucher.line_10_cpp_employee = Decimal("5000.00")
        voucher.line_10_cpp_employer = Decimal("5000.00")
        voucher.line_10_ei_employee = Decimal("2000.00")
        voucher.line_10_ei_employer = Decimal("2800.00")
        voucher.line_10_income_tax = Decimal("15000.00")
        voucher.line_11_total_deductions = Decimal("29800.00")
        voucher.line_12_previous_balance = Decimal("0")
        voucher.line_13_total_due = Decimal("29800.00")
        return voucher

    def test_generates_pdf_bytes(
        self, generator: PD7APDFGenerator, mock_voucher: MagicMock
    ):
        """Test that generate_pdf returns PDF bytes."""
        result = generator.generate_pdf(mock_voucher)

        # Check that it returns bytes
        assert isinstance(result, bytes)
        # Check PDF magic bytes
        assert result.startswith(b"%PDF-")
        # Check it ends with PDF EOF marker
        assert b"%%EOF" in result

    def test_pdf_size_is_reasonable(
        self, generator: PD7APDFGenerator, mock_voucher: MagicMock
    ):
        """Test that PDF has reasonable size."""
        result = generator.generate_pdf(mock_voucher)

        # PDF should be at least 1KB for a valid PD7A
        assert len(result) > 1000

    def test_pdf_contains_page_content(
        self, generator: PD7APDFGenerator, mock_voucher: MagicMock
    ):
        """Test that PDF contains page content stream."""
        result = generator.generate_pdf(mock_voucher)

        assert b"stream" in result
        assert b"endstream" in result

    def test_pdf_with_previous_balance(
        self, generator: PD7APDFGenerator, mock_voucher: MagicMock
    ):
        """Test PDF generation with previous balance."""
        mock_voucher.line_12_previous_balance = Decimal("5000.00")
        mock_voucher.line_13_total_due = Decimal("34800.00")

        result = generator.generate_pdf(mock_voucher)

        assert isinstance(result, bytes)
        assert result.startswith(b"%PDF-")

    def test_pdf_with_large_amounts(
        self, generator: PD7APDFGenerator, mock_voucher: MagicMock
    ):
        """Test PDF generation with large amounts."""
        mock_voucher.line_10_cpp_employee = Decimal("125000.00")
        mock_voucher.line_10_cpp_employer = Decimal("125000.00")
        mock_voucher.line_10_ei_employee = Decimal("41000.00")
        mock_voucher.line_10_ei_employer = Decimal("57400.00")
        mock_voucher.line_10_income_tax = Decimal("500000.00")
        mock_voucher.line_11_total_deductions = Decimal("848400.00")
        mock_voucher.line_13_total_due = Decimal("848400.00")

        result = generator.generate_pdf(mock_voucher)

        assert isinstance(result, bytes)
        assert result.startswith(b"%PDF-")


class TestBuildEmployerSection:
    """Tests for _build_employer_section method."""

    @pytest.fixture
    def generator(self) -> PD7APDFGenerator:
        """Create a PD7APDFGenerator instance."""
        return PD7APDFGenerator()

    def test_employer_section(self, generator: PD7APDFGenerator):
        """Test building employer section."""
        voucher = MagicMock()
        voucher.employer_name = "Acme Corp"
        voucher.payroll_account_number = "123456789RP0001"

        result = generator._build_employer_section(voucher)

        assert len(result) == 1  # Single table


class TestBuildPeriodSection:
    """Tests for _build_period_section method."""

    @pytest.fixture
    def generator(self) -> PD7APDFGenerator:
        """Create a PD7APDFGenerator instance."""
        return PD7APDFGenerator()

    def test_period_section(self, generator: PD7APDFGenerator):
        """Test building period section."""
        voucher = MagicMock()
        voucher.period_start = date(2025, 1, 1)
        voucher.period_end = date(2025, 1, 31)
        voucher.due_date = date(2025, 2, 15)

        result = generator._build_period_section(voucher)

        assert len(result) == 1  # Single table


class TestBuildDeductionsTable:
    """Tests for _build_deductions_table method."""

    @pytest.fixture
    def generator(self) -> PD7APDFGenerator:
        """Create a PD7APDFGenerator instance."""
        return PD7APDFGenerator()

    def test_deductions_table(self, generator: PD7APDFGenerator):
        """Test building deductions table."""
        voucher = MagicMock()
        voucher.line_10_cpp_employee = Decimal("5000.00")
        voucher.line_10_cpp_employer = Decimal("5000.00")
        voucher.line_10_ei_employee = Decimal("2000.00")
        voucher.line_10_ei_employer = Decimal("2800.00")
        voucher.line_10_income_tax = Decimal("15000.00")

        result = generator._build_deductions_table(voucher)

        assert len(result) == 1  # Single table

    def test_deductions_table_with_zero_values(self, generator: PD7APDFGenerator):
        """Test deductions table with zero values."""
        voucher = MagicMock()
        voucher.line_10_cpp_employee = Decimal("0")
        voucher.line_10_cpp_employer = Decimal("0")
        voucher.line_10_ei_employee = Decimal("0")
        voucher.line_10_ei_employer = Decimal("0")
        voucher.line_10_income_tax = Decimal("0")

        result = generator._build_deductions_table(voucher)

        assert len(result) == 1


class TestBuildTotalTable:
    """Tests for _build_total_table method."""

    @pytest.fixture
    def generator(self) -> PD7APDFGenerator:
        """Create a PD7APDFGenerator instance."""
        return PD7APDFGenerator()

    def test_total_table_without_previous_balance(self, generator: PD7APDFGenerator):
        """Test building total table without previous balance."""
        voucher = MagicMock()
        voucher.line_11_total_deductions = Decimal("29800.00")
        voucher.line_12_previous_balance = Decimal("0")

        result = generator._build_total_table(voucher)

        # Should have just the total table
        assert len(result) == 1

    def test_total_table_with_previous_balance(self, generator: PD7APDFGenerator):
        """Test building total table with previous balance."""
        voucher = MagicMock()
        voucher.line_11_total_deductions = Decimal("29800.00")
        voucher.line_12_previous_balance = Decimal("5000.00")
        voucher.line_13_total_due = Decimal("34800.00")

        result = generator._build_total_table(voucher)

        # Should have total table, spacer, and balance table
        assert len(result) == 3


class TestBuildPaymentInstructions:
    """Tests for _build_payment_instructions method."""

    @pytest.fixture
    def generator(self) -> PD7APDFGenerator:
        """Create a PD7APDFGenerator instance."""
        return PD7APDFGenerator()

    def test_payment_instructions(self, generator: PD7APDFGenerator):
        """Test building payment instructions."""
        result = generator._build_payment_instructions()

        # Should return a Paragraph
        assert result is not None


class TestGeneratorInitialization:
    """Tests for PD7APDFGenerator initialization."""

    def test_styles_are_initialized(self):
        """Test that styles are properly initialized."""
        generator = PD7APDFGenerator()

        assert generator.styles is not None
        # Check that standard styles are available
        assert "Title" in generator.styles.byName
        assert "Normal" in generator.styles.byName
