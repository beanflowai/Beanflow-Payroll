"""
Tests for paystub_generator.py module.

Tests the PaystubGenerator class which generates PDF paystubs using ReportLab.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from app.models.paystub import (
    BenefitLine,
    EarningLine,
    PaystubData,
    SickLeaveInfo,
    TaxLine,
    VacationInfo,
)
from app.services.payroll.paystub_generator import PaystubGenerator


class TestFormatCurrency:
    """Tests for _format_currency method."""

    @pytest.fixture
    def generator(self) -> PaystubGenerator:
        """Create a PaystubGenerator instance."""
        return PaystubGenerator()

    def test_positive_value(self, generator: PaystubGenerator):
        """Test formatting positive currency value."""
        result = generator._format_currency(Decimal("1234.56"))
        assert result == "1,234.56"

    def test_negative_value_with_sign(self, generator: PaystubGenerator):
        """Test formatting negative value with sign shown."""
        result = generator._format_currency(Decimal("-500.00"))
        assert result == "-500.00"

    def test_negative_value_without_sign(self, generator: PaystubGenerator):
        """Test formatting negative value without sign."""
        result = generator._format_currency(Decimal("-500.00"), show_negative=False)
        assert result == "500.00"

    def test_zero_value(self, generator: PaystubGenerator):
        """Test formatting zero value."""
        result = generator._format_currency(Decimal("0"))
        assert result == "0.00"

    def test_large_value_with_commas(self, generator: PaystubGenerator):
        """Test formatting large value with comma separators."""
        result = generator._format_currency(Decimal("1234567.89"))
        assert result == "1,234,567.89"

    def test_small_value(self, generator: PaystubGenerator):
        """Test formatting small value."""
        result = generator._format_currency(Decimal("0.01"))
        assert result == "0.01"


class TestDownloadLogo:
    """Tests for _download_logo method."""

    @pytest.fixture
    def generator(self) -> PaystubGenerator:
        """Create a PaystubGenerator instance."""
        return PaystubGenerator()

    def test_successful_download(self, generator: PaystubGenerator):
        """Test successful logo download."""
        mock_response = MagicMock()
        mock_response.content = b"fake_image_data"

        with patch("app.services.payroll.paystub_generator.httpx.Client") as mock_client:
            mock_context = MagicMock()
            mock_context.get.return_value = mock_response
            mock_client.return_value.__enter__ = MagicMock(return_value=mock_context)
            mock_client.return_value.__exit__ = MagicMock(return_value=False)

            result = generator._download_logo("https://example.com/logo.png")

            assert result is not None
            assert result.getvalue() == b"fake_image_data"

    def test_failed_download(self, generator: PaystubGenerator):
        """Test logo download failure returns None."""
        with patch("app.services.payroll.paystub_generator.httpx.Client") as mock_client:
            mock_context = MagicMock()
            mock_context.get.side_effect = Exception("Network error")
            mock_client.return_value.__enter__ = MagicMock(return_value=mock_context)
            mock_client.return_value.__exit__ = MagicMock(return_value=False)

            result = generator._download_logo("https://example.com/logo.png")

            assert result is None

    def test_http_error(self, generator: PaystubGenerator):
        """Test HTTP error returns None."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")

        with patch("app.services.payroll.paystub_generator.httpx.Client") as mock_client:
            mock_context = MagicMock()
            mock_context.get.return_value = mock_response
            mock_client.return_value.__enter__ = MagicMock(return_value=mock_context)
            mock_client.return_value.__exit__ = MagicMock(return_value=False)

            result = generator._download_logo("https://example.com/logo.png")

            assert result is None


class TestGeneratePaystubBytes:
    """Tests for generate_paystub_bytes method."""

    @pytest.fixture
    def generator(self) -> PaystubGenerator:
        """Create a PaystubGenerator instance."""
        return PaystubGenerator()

    @pytest.fixture
    def minimal_paystub_data(self) -> PaystubData:
        """Create minimal paystub data for testing."""
        return PaystubData(
            employeeName="John Doe",
            employeeAddress="123 Main St\nToronto, Ontario M5V 1A1",
            sinMasked="***-***-123",
            employerName="Acme Corp",
            employerAddress="456 Business Ave\nToronto, Ontario M5V 2B2",
            periodStart=date(2025, 1, 1),
            periodEnd=date(2025, 1, 15),
            payDate=date(2025, 1, 17),
            earnings=[
                EarningLine(
                    description="Regular Earnings",
                    qty=None,
                    rate=None,
                    current=Decimal("2000"),
                    ytd=Decimal("4000"),
                )
            ],
            totalEarnings=Decimal("2000"),
            ytdEarnings=Decimal("4000"),
            taxes=[
                TaxLine(description="CPP", current=Decimal("-100"), ytd=Decimal("-200")),
                TaxLine(description="EI", current=Decimal("-50"), ytd=Decimal("-100")),
                TaxLine(
                    description="Federal Tax", current=Decimal("-300"), ytd=Decimal("-600")
                ),
                TaxLine(
                    description="Provincial Tax",
                    current=Decimal("-150"),
                    ytd=Decimal("-300"),
                ),
            ],
            totalTaxes=Decimal("-600"),
            ytdTaxes=Decimal("-1200"),
            nonTaxableBenefits=[],
            taxableBenefits=[],
            benefitDeductions=[],
            totalBenefitDeductions=Decimal("0"),
            ytdBenefitDeductions=Decimal("0"),
            netPay=Decimal("1400"),
            ytdNetPay=Decimal("2800"),
        )

    def test_generates_pdf_bytes(
        self, generator: PaystubGenerator, minimal_paystub_data: PaystubData
    ):
        """Test that generate_paystub_bytes returns PDF bytes."""
        result = generator.generate_paystub_bytes(minimal_paystub_data)

        # Check that it returns bytes
        assert isinstance(result, bytes)
        # Check PDF magic bytes
        assert result.startswith(b"%PDF-")
        # Check it ends with PDF EOF marker
        assert b"%%EOF" in result

    def test_pdf_size_is_reasonable(
        self, generator: PaystubGenerator, minimal_paystub_data: PaystubData
    ):
        """Test that PDF has reasonable size."""
        result = generator.generate_paystub_bytes(minimal_paystub_data)

        # PDF should be at least 1KB for a valid paystub
        assert len(result) > 1000

    def test_pdf_contains_page_content(
        self, generator: PaystubGenerator, minimal_paystub_data: PaystubData
    ):
        """Test that PDF contains page content stream."""
        result = generator.generate_paystub_bytes(minimal_paystub_data)

        # Check for PDF content stream marker
        assert b"stream" in result
        assert b"endstream" in result

    def test_with_vacation_info(
        self, generator: PaystubGenerator, minimal_paystub_data: PaystubData
    ):
        """Test generating paystub with vacation info."""
        minimal_paystub_data.vacation = VacationInfo(
            earned=Decimal("100"),
            ytdUsed=Decimal("50"),
            available=Decimal("500"),
        )

        result = generator.generate_paystub_bytes(minimal_paystub_data)

        assert isinstance(result, bytes)
        assert result.startswith(b"%PDF-")

    def test_with_sick_leave_info(
        self, generator: PaystubGenerator, minimal_paystub_data: PaystubData
    ):
        """Test generating paystub with sick leave info."""
        minimal_paystub_data.sickLeave = SickLeaveInfo(
            paidDaysRemaining=Decimal("5"),
            unpaidDaysRemaining=Decimal("0"),
            daysUsedYtd=Decimal("2"),
        )

        result = generator.generate_paystub_bytes(minimal_paystub_data)

        assert isinstance(result, bytes)
        assert result.startswith(b"%PDF-")

    def test_with_benefits(
        self, generator: PaystubGenerator, minimal_paystub_data: PaystubData
    ):
        """Test generating paystub with benefits."""
        minimal_paystub_data.nonTaxableBenefits = [
            BenefitLine(
                description="Health - Employer",
                current=Decimal("100"),
                ytd=Decimal("200"),
            )
        ]
        minimal_paystub_data.taxableBenefits = [
            BenefitLine(
                description="Life Insurance - Employer",
                current=Decimal("50"),
                ytd=Decimal("100"),
            )
        ]
        minimal_paystub_data.benefitDeductions = [
            BenefitLine(
                description="Health - Employee",
                current=Decimal("-50"),
                ytd=Decimal("-100"),
            )
        ]
        minimal_paystub_data.totalBenefitDeductions = Decimal("-50")
        minimal_paystub_data.ytdBenefitDeductions = Decimal("-100")

        result = generator.generate_paystub_bytes(minimal_paystub_data)

        assert isinstance(result, bytes)
        assert result.startswith(b"%PDF-")

    def test_with_pay_rate(
        self, generator: PaystubGenerator, minimal_paystub_data: PaystubData
    ):
        """Test generating paystub with pay rate."""
        minimal_paystub_data.payRate = "$52,000.00/yr"

        result = generator.generate_paystub_bytes(minimal_paystub_data)

        assert isinstance(result, bytes)
        assert result.startswith(b"%PDF-")

    def test_with_occupation(
        self, generator: PaystubGenerator, minimal_paystub_data: PaystubData
    ):
        """Test generating paystub with occupation."""
        minimal_paystub_data.occupation = "Software Developer"

        result = generator.generate_paystub_bytes(minimal_paystub_data)

        assert isinstance(result, bytes)
        assert result.startswith(b"%PDF-")

    def test_with_logo_bytes(
        self, generator: PaystubGenerator, minimal_paystub_data: PaystubData
    ):
        """Test generating paystub with logo bytes."""
        from PIL import Image as PILImage

        # Create a valid PNG image using PIL
        img = PILImage.new("RGB", (100, 50), color=(255, 255, 255))
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        png_data = buffer.getvalue()

        minimal_paystub_data.logoBytes = png_data

        result = generator.generate_paystub_bytes(minimal_paystub_data)

        assert isinstance(result, bytes)
        assert result.startswith(b"%PDF-")

    def test_with_overtime_earnings(
        self, generator: PaystubGenerator, minimal_paystub_data: PaystubData
    ):
        """Test generating paystub with overtime earnings."""
        minimal_paystub_data.earnings.append(
            EarningLine(
                description="Overtime",
                qty=Decimal("10"),
                rate=Decimal("45"),
                current=Decimal("450"),
                ytd=Decimal("900"),
            )
        )
        minimal_paystub_data.totalEarnings = Decimal("2450")
        minimal_paystub_data.ytdEarnings = Decimal("4900")

        result = generator.generate_paystub_bytes(minimal_paystub_data)

        assert isinstance(result, bytes)
        assert result.startswith(b"%PDF-")

    def test_with_all_sections(self, generator: PaystubGenerator):
        """Test generating paystub with all optional sections."""
        data = PaystubData(
            employeeName="Jane Smith",
            employeeAddress="789 Oak Ave\nVancouver, British Columbia V6B 2W2",
            sinMasked="***-***-456",
            occupation="Accountant",
            employerName="Finance Inc",
            employerAddress="321 Corporate Dr\nVancouver, British Columbia V6B 3C3",
            periodStart=date(2025, 1, 16),
            periodEnd=date(2025, 1, 31),
            payDate=date(2025, 2, 1),
            payRate="$80,000.00/yr",
            earnings=[
                EarningLine(
                    description="Regular Earnings",
                    qty=None,
                    rate=None,
                    current=Decimal("3076.92"),
                    ytd=Decimal("6153.84"),
                ),
                EarningLine(
                    description="Holiday Pay",
                    qty=None,
                    rate=None,
                    current=Decimal("200"),
                    ytd=Decimal("200"),
                ),
            ],
            totalEarnings=Decimal("3276.92"),
            ytdEarnings=Decimal("6353.84"),
            taxes=[
                TaxLine(description="CPP", current=Decimal("-180"), ytd=Decimal("-360")),
                TaxLine(description="EI", current=Decimal("-55"), ytd=Decimal("-110")),
                TaxLine(
                    description="Federal Tax", current=Decimal("-500"), ytd=Decimal("-1000")
                ),
                TaxLine(
                    description="Provincial Tax",
                    current=Decimal("-200"),
                    ytd=Decimal("-400"),
                ),
            ],
            totalTaxes=Decimal("-935"),
            ytdTaxes=Decimal("-1870"),
            nonTaxableBenefits=[
                BenefitLine(
                    description="Health - Employer",
                    current=Decimal("150"),
                    ytd=Decimal("300"),
                ),
                BenefitLine(
                    description="Dental - Employer",
                    current=Decimal("75"),
                    ytd=Decimal("150"),
                ),
            ],
            taxableBenefits=[
                BenefitLine(
                    description="Life & AD&D - Employer",
                    current=Decimal("40"),
                    ytd=Decimal("80"),
                ),
            ],
            benefitDeductions=[
                BenefitLine(
                    description="Health - Employee",
                    current=Decimal("-75"),
                    ytd=Decimal("-150"),
                ),
                BenefitLine(
                    description="Dental - Employee",
                    current=Decimal("-35"),
                    ytd=Decimal("-70"),
                ),
            ],
            totalBenefitDeductions=Decimal("-110"),
            ytdBenefitDeductions=Decimal("-220"),
            netPay=Decimal("2231.92"),
            ytdNetPay=Decimal("4263.84"),
            vacation=VacationInfo(
                earned=Decimal("131.08"),
                ytdUsed=Decimal("0"),
                available=Decimal("1000"),
            ),
            sickLeave=SickLeaveInfo(
                paidDaysRemaining=Decimal("5"),
                unpaidDaysRemaining=Decimal("0"),
                daysUsedYtd=Decimal("0"),
            ),
        )

        result = generator.generate_paystub_bytes(data)

        assert isinstance(result, bytes)
        assert result.startswith(b"%PDF-")
        # Should be larger than minimal paystub
        assert len(result) > 1000


class TestBuildHeaderSection:
    """Tests for _build_header_section method."""

    @pytest.fixture
    def generator(self) -> PaystubGenerator:
        """Create a PaystubGenerator instance."""
        return PaystubGenerator()

    def test_header_without_logo(self, generator: PaystubGenerator):
        """Test building header without logo."""
        elements: list = []
        data = MagicMock()
        data.logoBytes = None
        data.logoUrl = None
        data.employerName = "Test Company"

        generator._build_header_section(elements, data)

        assert len(elements) == 1  # Header table added

    def test_header_with_logo_url(self, generator: PaystubGenerator):
        """Test building header with logo URL."""
        elements: list = []
        data = MagicMock()
        data.logoBytes = None
        data.logoUrl = "https://example.com/logo.png"
        data.employerName = "Test Company"

        with patch.object(generator, "_download_logo", return_value=None):
            generator._build_header_section(elements, data)

        assert len(elements) == 1  # Header table added


class TestBuildPayDetailsSection:
    """Tests for _build_pay_details_section method."""

    @pytest.fixture
    def generator(self) -> PaystubGenerator:
        """Create a PaystubGenerator instance."""
        return PaystubGenerator()

    def test_pay_details_with_all_fields(self, generator: PaystubGenerator):
        """Test building pay details with all fields."""
        elements: list = []
        data = MagicMock()
        data.payRate = "$50,000/yr"
        data.periodStart = date(2025, 1, 1)
        data.periodEnd = date(2025, 1, 15)
        data.payDate = date(2025, 1, 17)
        data.vacation = MagicMock()
        data.vacation.available = Decimal("500")

        generator._build_pay_details_section(elements, data)

        assert len(elements) == 1  # Details table added

    def test_pay_details_without_pay_rate(self, generator: PaystubGenerator):
        """Test building pay details without pay rate."""
        elements: list = []
        data = MagicMock()
        data.payRate = None
        data.periodStart = date(2025, 1, 1)
        data.periodEnd = date(2025, 1, 15)
        data.payDate = date(2025, 1, 17)
        data.vacation = None

        generator._build_pay_details_section(elements, data)

        assert len(elements) == 1  # Details table still added with period/date

    def test_pay_details_without_vacation(self, generator: PaystubGenerator):
        """Test building pay details without vacation info."""
        elements: list = []
        data = MagicMock()
        data.payRate = "$50,000/yr"
        data.periodStart = date(2025, 1, 1)
        data.periodEnd = date(2025, 1, 15)
        data.payDate = date(2025, 1, 17)
        data.vacation = None

        generator._build_pay_details_section(elements, data)

        assert len(elements) == 1


class TestBuildIncomeSection:
    """Tests for _build_income_section method."""

    @pytest.fixture
    def generator(self) -> PaystubGenerator:
        """Create a PaystubGenerator instance."""
        return PaystubGenerator()

    def test_income_section_with_single_earning(self, generator: PaystubGenerator):
        """Test building income section with single earning."""
        elements: list = []
        data = MagicMock()
        data.earnings = [
            MagicMock(
                description="Regular Earnings",
                qty=None,
                rate=None,
                current=Decimal("2000"),
                ytd=Decimal("4000"),
            )
        ]
        data.totalEarnings = Decimal("2000")
        data.ytdEarnings = Decimal("4000")

        generator._build_income_section(elements, data)

        assert len(elements) == 2  # Income table + gross pay table

    def test_income_section_with_multiple_earnings(self, generator: PaystubGenerator):
        """Test building income section with multiple earnings."""
        elements: list = []
        data = MagicMock()
        data.earnings = [
            MagicMock(
                description="Regular Earnings",
                qty=None,
                rate=None,
                current=Decimal("2000"),
                ytd=Decimal("4000"),
            ),
            MagicMock(
                description="Overtime",
                qty=Decimal("10"),
                rate=Decimal("45"),
                current=Decimal("450"),
                ytd=Decimal("900"),
            ),
        ]
        data.totalEarnings = Decimal("2450")
        data.ytdEarnings = Decimal("4900")

        generator._build_income_section(elements, data)

        assert len(elements) == 2


class TestBuildDeductionsSection:
    """Tests for _build_deductions_section method."""

    @pytest.fixture
    def generator(self) -> PaystubGenerator:
        """Create a PaystubGenerator instance."""
        return PaystubGenerator()

    def test_deductions_section(self, generator: PaystubGenerator):
        """Test building deductions section."""
        elements: list = []
        data = MagicMock()
        data.taxes = [
            MagicMock(description="CPP", current=Decimal("-100"), ytd=Decimal("-200")),
            MagicMock(description="EI", current=Decimal("-50"), ytd=Decimal("-100")),
        ]
        data.benefitDeductions = []
        data.totalTaxes = Decimal("-150")
        data.totalBenefitDeductions = Decimal("0")
        data.ytdTaxes = Decimal("-300")
        data.ytdBenefitDeductions = Decimal("0")

        generator._build_deductions_section(elements, data)

        assert len(elements) == 2  # Deductions table + totals table

    def test_deductions_section_with_benefits(self, generator: PaystubGenerator):
        """Test building deductions section with benefit deductions."""
        elements: list = []
        data = MagicMock()
        data.taxes = [
            MagicMock(description="CPP", current=Decimal("-100"), ytd=Decimal("-200")),
        ]
        data.benefitDeductions = [
            MagicMock(
                description="Health - Employee",
                current=Decimal("-50"),
                ytd=Decimal("-100"),
            )
        ]
        data.totalTaxes = Decimal("-100")
        data.totalBenefitDeductions = Decimal("-50")
        data.ytdTaxes = Decimal("-200")
        data.ytdBenefitDeductions = Decimal("-100")

        generator._build_deductions_section(elements, data)

        assert len(elements) == 2


class TestBuildNetPaySection:
    """Tests for _build_net_pay_section method."""

    @pytest.fixture
    def generator(self) -> PaystubGenerator:
        """Create a PaystubGenerator instance."""
        return PaystubGenerator()

    def test_net_pay_section(self, generator: PaystubGenerator):
        """Test building net pay section."""
        elements: list = []
        data = MagicMock()
        data.netPay = Decimal("2000")
        data.ytdNetPay = Decimal("4000")

        generator._build_net_pay_section(elements, data)

        assert len(elements) == 1  # Net pay table

    def test_net_pay_section_without_ytd(self, generator: PaystubGenerator):
        """Test building net pay section without YTD."""
        elements: list = []
        data = MagicMock()
        data.netPay = Decimal("2000")
        data.ytdNetPay = None

        generator._build_net_pay_section(elements, data)

        assert len(elements) == 1


class TestBuildEmployerContributionsSection:
    """Tests for _build_employer_contributions_section method."""

    @pytest.fixture
    def generator(self) -> PaystubGenerator:
        """Create a PaystubGenerator instance."""
        return PaystubGenerator()

    def test_employer_contributions_with_benefits(self, generator: PaystubGenerator):
        """Test building employer contributions with benefits."""
        elements: list = []
        data = MagicMock()
        data.nonTaxableBenefits = [
            MagicMock(
                description="Health - Employer",
                current=Decimal("100"),
                ytd=Decimal("200"),
            )
        ]
        data.taxableBenefits = [
            MagicMock(
                description="Life Insurance - Employer",
                current=Decimal("50"),
                ytd=Decimal("100"),
            )
        ]

        generator._build_employer_contributions_section(elements, data)

        assert len(elements) == 1

    def test_employer_contributions_without_benefits(self, generator: PaystubGenerator):
        """Test that no section is added without benefits."""
        elements: list = []
        data = MagicMock()
        data.nonTaxableBenefits = []
        data.taxableBenefits = []

        generator._build_employer_contributions_section(elements, data)

        assert len(elements) == 0


class TestBuildLeaveBalancesSection:
    """Tests for _build_leave_balances_section method."""

    @pytest.fixture
    def generator(self) -> PaystubGenerator:
        """Create a PaystubGenerator instance."""
        return PaystubGenerator()

    def test_leave_balances_with_vacation(self, generator: PaystubGenerator):
        """Test building leave balances with vacation."""
        elements: list = []
        data = MagicMock()
        data.vacation = MagicMock()
        data.vacation.earned = Decimal("100")
        data.vacation.ytdUsed = Decimal("50")
        data.vacation.available = Decimal("500")
        data.sickLeave = None

        generator._build_leave_balances_section(elements, data)

        assert len(elements) == 1

    def test_leave_balances_with_sick_leave(self, generator: PaystubGenerator):
        """Test building leave balances with sick leave."""
        elements: list = []
        data = MagicMock()
        data.vacation = None
        data.sickLeave = MagicMock()
        data.sickLeave.paidDaysRemaining = Decimal("5")
        data.sickLeave.daysUsedYtd = Decimal("2")

        generator._build_leave_balances_section(elements, data)

        assert len(elements) == 1

    def test_leave_balances_with_both(self, generator: PaystubGenerator):
        """Test building leave balances with both vacation and sick leave."""
        elements: list = []
        data = MagicMock()
        data.vacation = MagicMock()
        data.vacation.earned = Decimal("100")
        data.vacation.ytdUsed = None
        data.vacation.available = Decimal("500")
        data.sickLeave = MagicMock()
        data.sickLeave.paidDaysRemaining = Decimal("5")
        data.sickLeave.daysUsedYtd = Decimal("2")

        generator._build_leave_balances_section(elements, data)

        assert len(elements) == 1

    def test_leave_balances_without_either(self, generator: PaystubGenerator):
        """Test that no section is added without leave info."""
        elements: list = []
        data = MagicMock()
        data.vacation = None
        data.sickLeave = None

        generator._build_leave_balances_section(elements, data)

        assert len(elements) == 0


class TestCustomStyles:
    """Tests for custom styles initialization."""

    def test_styles_are_initialized(self):
        """Test that custom styles are properly initialized."""
        generator = PaystubGenerator()

        assert generator.styles is not None
        assert "SectionHeader" in generator.styles.byName
        assert "TableText" in generator.styles.byName
        assert "CompanyName" in generator.styles.byName
        assert "PayStubTitle" in generator.styles.byName
        assert "LabelStyle" in generator.styles.byName
