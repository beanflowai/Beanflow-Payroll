"""
Tests for Remittance API endpoints.

Tests for PD7A PDF generation endpoint.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api.v1.remittance import router, generate_pd7a_voucher
from app.models.remittance import PD7ARemittanceVoucher


# Sample data for testing
COMPANY_ID = UUID("12345678-1234-5678-1234-567812345678")
REMITTANCE_ID = UUID("87654321-4321-8765-4321-876543210987")
USER_ID = "user-123"


@pytest.fixture
def mock_current_user():
    """Create a mock current user."""
    user = MagicMock()
    user.id = USER_ID
    return user


@pytest.fixture
def sample_period():
    """Sample remittance period data from database."""
    return {
        "id": str(REMITTANCE_ID),
        "company_id": str(COMPANY_ID),
        "user_id": USER_ID,
        "period_start": "2025-01-01",
        "period_end": "2025-01-31",
        "due_date": "2025-02-15",
        "cpp_employee": "1000.00",
        "cpp_employer": "1000.00",
        "ei_employee": "500.00",
        "ei_employer": "700.00",
        "federal_tax": "3000.00",
        "provincial_tax": "1500.00",
        "total_amount": "7700.00",
        "status": "pending",
    }


@pytest.fixture
def sample_company():
    """Sample company data from database."""
    return {
        "company_name": "Test Company Inc.",
        "payroll_account_number": "123456789RP0001",
    }


class TestGeneratePD7AVoucher:
    """Tests for generate_pd7a_voucher endpoint."""

    @pytest.mark.asyncio
    async def test_returns_pdf_response(
        self, mock_current_user, sample_period, sample_company
    ):
        """Test that endpoint returns PDF response with correct headers."""
        with patch("app.api.v1.remittance.get_supabase_client") as mock_supabase, \
             patch("app.api.v1.remittance.PD7APDFGenerator") as mock_generator:

            # Setup supabase mock
            mock_client = MagicMock()
            mock_supabase.return_value = mock_client

            # Mock period query
            mock_period_result = MagicMock()
            mock_period_result.data = sample_period
            mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value = mock_period_result

            # Mock company query - need to handle different table calls
            mock_company_result = MagicMock()
            mock_company_result.data = sample_company

            # Configure table mock to return different results
            def table_side_effect(table_name):
                mock_table = MagicMock()
                if table_name == "remittance_periods":
                    mock_table.select.return_value.eq.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value = mock_period_result
                elif table_name == "companies":
                    mock_table.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value = mock_company_result
                return mock_table

            mock_client.table.side_effect = table_side_effect

            # Mock PDF generator
            mock_gen_instance = MagicMock()
            mock_gen_instance.generate_pdf.return_value = b"%PDF-1.4 test content"
            mock_generator.return_value = mock_gen_instance

            # Call endpoint
            response = await generate_pd7a_voucher(
                company_id=COMPANY_ID,
                remittance_id=REMITTANCE_ID,
                current_user=mock_current_user,
            )

            # Verify response
            assert response.media_type == "application/pdf"
            assert b"PDF" in response.body
            assert "Content-Disposition" in response.headers
            assert "PD7A_2025-01-01_2025-01-31.pdf" in response.headers["Content-Disposition"]

    @pytest.mark.asyncio
    async def test_returns_404_when_period_not_found(self, mock_current_user):
        """Test that 404 is returned when remittance period not found."""
        with patch("app.api.v1.remittance.get_supabase_client") as mock_supabase:
            mock_client = MagicMock()
            mock_supabase.return_value = mock_client

            # Mock period query to return None
            mock_period_result = MagicMock()
            mock_period_result.data = None
            mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value = mock_period_result

            with pytest.raises(HTTPException) as exc_info:
                await generate_pd7a_voucher(
                    company_id=COMPANY_ID,
                    remittance_id=REMITTANCE_ID,
                    current_user=mock_current_user,
                )

            assert exc_info.value.status_code == 404
            assert "Remittance period not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_returns_404_when_company_not_found(
        self, mock_current_user, sample_period
    ):
        """Test that 404 is returned when company not found."""
        with patch("app.api.v1.remittance.get_supabase_client") as mock_supabase:
            mock_client = MagicMock()
            mock_supabase.return_value = mock_client

            # Mock period query to return data
            mock_period_result = MagicMock()
            mock_period_result.data = sample_period

            # Mock company query to return None
            mock_company_result = MagicMock()
            mock_company_result.data = None

            def table_side_effect(table_name):
                mock_table = MagicMock()
                if table_name == "remittance_periods":
                    mock_table.select.return_value.eq.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value = mock_period_result
                elif table_name == "companies":
                    mock_table.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value = mock_company_result
                return mock_table

            mock_client.table.side_effect = table_side_effect

            with pytest.raises(HTTPException) as exc_info:
                await generate_pd7a_voucher(
                    company_id=COMPANY_ID,
                    remittance_id=REMITTANCE_ID,
                    current_user=mock_current_user,
                )

            assert exc_info.value.status_code == 404
            assert "Company not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_returns_500_on_unexpected_error(
        self, mock_current_user, sample_period, sample_company
    ):
        """Test that 500 is returned on unexpected errors."""
        with patch("app.api.v1.remittance.get_supabase_client") as mock_supabase, \
             patch("app.api.v1.remittance.PD7APDFGenerator") as mock_generator:

            mock_client = MagicMock()
            mock_supabase.return_value = mock_client

            # Mock period query
            mock_period_result = MagicMock()
            mock_period_result.data = sample_period

            mock_company_result = MagicMock()
            mock_company_result.data = sample_company

            def table_side_effect(table_name):
                mock_table = MagicMock()
                if table_name == "remittance_periods":
                    mock_table.select.return_value.eq.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value = mock_period_result
                elif table_name == "companies":
                    mock_table.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value = mock_company_result
                return mock_table

            mock_client.table.side_effect = table_side_effect

            # Mock PDF generator to raise exception
            mock_gen_instance = MagicMock()
            mock_gen_instance.generate_pdf.side_effect = Exception("PDF generation failed")
            mock_generator.return_value = mock_gen_instance

            with pytest.raises(HTTPException) as exc_info:
                await generate_pd7a_voucher(
                    company_id=COMPANY_ID,
                    remittance_id=REMITTANCE_ID,
                    current_user=mock_current_user,
                )

            assert exc_info.value.status_code == 500
            assert "Internal error generating PDF" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_builds_correct_voucher(
        self, mock_current_user, sample_period, sample_company
    ):
        """Test that PD7A voucher is built with correct data."""
        with patch("app.api.v1.remittance.get_supabase_client") as mock_supabase, \
             patch("app.api.v1.remittance.PD7APDFGenerator") as mock_generator:

            mock_client = MagicMock()
            mock_supabase.return_value = mock_client

            mock_period_result = MagicMock()
            mock_period_result.data = sample_period

            mock_company_result = MagicMock()
            mock_company_result.data = sample_company

            def table_side_effect(table_name):
                mock_table = MagicMock()
                if table_name == "remittance_periods":
                    mock_table.select.return_value.eq.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value = mock_period_result
                elif table_name == "companies":
                    mock_table.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value = mock_company_result
                return mock_table

            mock_client.table.side_effect = table_side_effect

            mock_gen_instance = MagicMock()
            mock_gen_instance.generate_pdf.return_value = b"%PDF-1.4"
            mock_generator.return_value = mock_gen_instance

            await generate_pd7a_voucher(
                company_id=COMPANY_ID,
                remittance_id=REMITTANCE_ID,
                current_user=mock_current_user,
            )

            # Verify the voucher passed to generate_pdf
            call_args = mock_gen_instance.generate_pdf.call_args
            voucher = call_args[0][0]

            assert voucher.employer_name == "Test Company Inc."
            assert voucher.payroll_account_number == "123456789RP0001"
            assert voucher.period_start == date(2025, 1, 1)
            assert voucher.period_end == date(2025, 1, 31)
            assert voucher.due_date == date(2025, 2, 15)
            assert voucher.line_10_cpp_employee == Decimal("1000.00")
            assert voucher.line_10_cpp_employer == Decimal("1000.00")
            assert voucher.line_10_ei_employee == Decimal("500.00")
            assert voucher.line_10_ei_employer == Decimal("700.00")
            # Income tax is federal + provincial
            assert voucher.line_10_income_tax == Decimal("4500.00")

    @pytest.mark.asyncio
    async def test_reraises_http_exceptions(self, mock_current_user):
        """Test that HTTPExceptions are re-raised as-is."""
        with patch("app.api.v1.remittance.get_supabase_client") as mock_supabase:
            mock_client = MagicMock()
            mock_supabase.return_value = mock_client

            # Make supabase raise an HTTPException-like scenario
            mock_period_result = MagicMock()
            mock_period_result.data = None
            mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value = mock_period_result

            with pytest.raises(HTTPException) as exc_info:
                await generate_pd7a_voucher(
                    company_id=COMPANY_ID,
                    remittance_id=REMITTANCE_ID,
                    current_user=mock_current_user,
                )

            # Should be 404 not 500
            assert exc_info.value.status_code == 404


class TestPD7ARemittanceVoucher:
    """Tests for PD7ARemittanceVoucher model."""

    def test_calculates_line_11_total_deductions(self):
        """Test that line_11_total_deductions is calculated correctly."""
        voucher = PD7ARemittanceVoucher(
            employer_name="Test Co",
            payroll_account_number="123456789RP0001",
            period_start=date(2025, 1, 1),
            period_end=date(2025, 1, 31),
            due_date=date(2025, 2, 15),
            line_10_cpp_employee=Decimal("1000"),
            line_10_cpp_employer=Decimal("1000"),
            line_10_ei_employee=Decimal("500"),
            line_10_ei_employer=Decimal("700"),
            line_10_income_tax=Decimal("3000"),
        )

        # Total = 1000 + 1000 + 500 + 700 + 3000 = 6200
        assert voucher.line_11_total_deductions == Decimal("6200.00")

    def test_calculates_line_13_total_due_with_previous_balance(self):
        """Test that line_13_total_due includes previous balance."""
        voucher = PD7ARemittanceVoucher(
            employer_name="Test Co",
            payroll_account_number="123456789RP0001",
            period_start=date(2025, 1, 1),
            period_end=date(2025, 1, 31),
            due_date=date(2025, 2, 15),
            line_10_cpp_employee=Decimal("1000"),
            line_10_cpp_employer=Decimal("1000"),
            line_10_ei_employee=Decimal("500"),
            line_10_ei_employer=Decimal("700"),
            line_10_income_tax=Decimal("3000"),
            line_12_previous_balance=Decimal("100"),
        )

        # Line 11 = 6200, Line 12 = 100, Line 13 = 6300
        assert voucher.line_11_total_deductions == Decimal("6200.00")
        assert voucher.line_13_total_due == Decimal("6300.00")
