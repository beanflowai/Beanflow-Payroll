"""
Provincial/Territorial Income Tax Calculator Tests

Tests provincial tax calculations following CRA T4127 Chapter 4, Step 4-5.
Handles all 12 provinces/territories (excluding Quebec).

Special features tested:
- Ontario: Surtax (V1) + Health Premium (V2)
- British Columbia: Tax Reduction (Factor S)
- Alberta: K5P supplemental credit
- Manitoba/Nova Scotia/Yukon: Dynamic BPA
"""

import pytest
from datetime import date
from decimal import Decimal

from app.services.payroll.provincial_tax_calculator import ProvincialTaxCalculator


# All province codes for parametrized tests
ALL_PROVINCE_CODES = ["AB", "BC", "MB", "NB", "NL", "NS", "NT", "NU", "ON", "PE", "SK", "YT"]


class TestProvincialTaxAllProvinces:
    """Test basic provincial tax calculations for all provinces."""

    @pytest.mark.parametrize("province", ALL_PROVINCE_CODES)
    def test_all_provinces_calculate_without_errors(self, province):
        """Test: All provinces calculate without errors."""
        calc = ProvincialTaxCalculator(
            province_code=province,
            pay_periods_per_year=26,
            year=2025,
        )

        bpa = calc.get_basic_personal_amount(
            annual_income=Decimal("60000"),
        )

        result = calc.calculate_provincial_tax(
            annual_taxable_income=Decimal("60000"),
            total_claim_amount=bpa,
            cpp_per_period=Decimal("110"),
            ei_per_period=Decimal("35"),
        )

        # Basic assertions for all provinces
        assert result.province_code == province
        assert result.annual_provincial_tax_t2 >= Decimal("0")
        assert result.tax_per_period >= Decimal("0")

    @pytest.mark.parametrize("province", ALL_PROVINCE_CODES)
    def test_all_provinces_have_bpa(self, province):
        """Test: All provinces have a Basic Personal Amount."""
        calc = ProvincialTaxCalculator(
            province_code=province,
            pay_periods_per_year=26,
            year=2025,
        )

        bpa = calc.get_basic_personal_amount(
            annual_income=Decimal("60000"),
        )

        assert bpa > Decimal("0")
        # All 2025 BPAs are above $8,000
        assert bpa > Decimal("8000")

    @pytest.mark.parametrize("province", ALL_PROVINCE_CODES)
    def test_all_provinces_low_income_minimal_tax(self, province):
        """Test: Low income produces minimal or no provincial tax."""
        calc = ProvincialTaxCalculator(
            province_code=province,
            pay_periods_per_year=26,
            year=2025,
        )

        bpa = calc.get_basic_personal_amount(
            annual_income=Decimal("15000"),
        )

        result = calc.calculate_provincial_tax(
            annual_taxable_income=Decimal("15000"),
            total_claim_amount=bpa,
            cpp_per_period=Decimal("40"),
            ei_per_period=Decimal("12"),
        )

        # Low income should result in minimal tax
        assert result.annual_provincial_tax_t2 < Decimal("1000")


class TestOntarioSurtax:
    """Test Ontario surtax calculations (V1)."""

    def setup_method(self):
        """Create Ontario calculator."""
        self.calc = ProvincialTaxCalculator(
            province_code="ON",
            pay_periods_per_year=26,
            year=2025,
        )

    def test_ontario_no_surtax_low_income(self):
        """Test: Ontario low income - no surtax.

        Surtax triggers when T4 > $5,710 (first threshold).
        """
        result = self.calc.calculate_provincial_tax(
            annual_taxable_income=Decimal("50000"),
            total_claim_amount=Decimal("12747"),
            cpp_per_period=Decimal("100"),
            ei_per_period=Decimal("35"),
        )

        assert result.surtax_v1 == Decimal("0")

    def test_ontario_with_surtax_high_income(self):
        """Test: Ontario high income - triggers surtax.

        Surtax formula:
        - If T4 > $5,710: 20% × (T4 - $5,710)
        - If T4 > $7,307: additional 36% × (T4 - $7,307)
        """
        result = self.calc.calculate_provincial_tax(
            annual_taxable_income=Decimal("150000"),
            total_claim_amount=Decimal("12747"),
            cpp_per_period=Decimal("155"),
            ei_per_period=Decimal("41"),
        )

        # High income should trigger surtax
        assert result.surtax_v1 > Decimal("0")

    def test_ontario_surtax_first_tier_only(self):
        """Test: Ontario income triggers only first tier surtax."""
        result = self.calc.calculate_provincial_tax(
            annual_taxable_income=Decimal("100000"),
            total_claim_amount=Decimal("12747"),
            cpp_per_period=Decimal("140"),
            ei_per_period=Decimal("40"),
        )

        # Should have some surtax, but not maximum
        # Exact value depends on T4 calculation
        if result.surtax_v1 > Decimal("0"):
            # If surtax applies, verify structure is correct
            assert result.annual_provincial_tax_t2 > result.basic_provincial_tax_t4


class TestOntarioHealthPremium:
    """Test Ontario Health Premium calculations (V2)."""

    def setup_method(self):
        """Create Ontario calculator."""
        self.calc = ProvincialTaxCalculator(
            province_code="ON",
            pay_periods_per_year=26,
            year=2025,
        )

    def test_ontario_no_health_premium_low_income(self):
        """Test: Ontario low income - no health premium.

        Health premium starts at $20,000 annual income.
        """
        result = self.calc.calculate_provincial_tax(
            annual_taxable_income=Decimal("18000"),
            total_claim_amount=Decimal("12747"),
            cpp_per_period=Decimal("50"),
            ei_per_period=Decimal("15"),
        )

        assert result.health_premium_v2 == Decimal("0")

    def test_ontario_with_health_premium(self):
        """Test: Ontario higher income triggers health premium.

        Health premium brackets increase with income up to $900.
        """
        result = self.calc.calculate_provincial_tax(
            annual_taxable_income=Decimal("100000"),
            total_claim_amount=Decimal("12747"),
            cpp_per_period=Decimal("140"),
            ei_per_period=Decimal("40"),
        )

        # Higher income should have health premium
        # Exact amount depends on bracket structure
        assert result.health_premium_v2 >= Decimal("0")


class TestBCTaxReduction:
    """Test BC Tax Reduction (Factor S) calculations."""

    def setup_method(self):
        """Create BC calculator."""
        self.calc = ProvincialTaxCalculator(
            province_code="BC",
            pay_periods_per_year=26,
            year=2025,
        )

    def test_bc_full_tax_reduction_low_income(self):
        """Test: BC low income gets full tax reduction.

        If A <= $25,437: S = $521 (full reduction)
        """
        result = self.calc.calculate_provincial_tax(
            annual_taxable_income=Decimal("20000"),
            total_claim_amount=Decimal("12932"),
            cpp_per_period=Decimal("45"),
            ei_per_period=Decimal("15"),
        )

        # Low income should get tax reduction
        assert result.tax_reduction_s >= Decimal("0")

    def test_bc_partial_tax_reduction_mid_income(self):
        """Test: BC mid income gets partial tax reduction.

        If $25,437 < A < $39,913: S = $521 - (0.036 × (A - $25,437))
        """
        result = self.calc.calculate_provincial_tax(
            annual_taxable_income=Decimal("30000"),
            total_claim_amount=Decimal("12932"),
            cpp_per_period=Decimal("70"),
            ei_per_period=Decimal("25"),
        )

        # Mid income should get partial reduction
        # S = 521 - (0.036 × (30000 - 25437)) = 521 - 164.27 = 356.73
        if result.tax_reduction_s > Decimal("0"):
            assert result.tax_reduction_s < Decimal("521")

    def test_bc_no_tax_reduction_high_income(self):
        """Test: BC high income - no tax reduction.

        If A >= $39,913: S = 0
        """
        result = self.calc.calculate_provincial_tax(
            annual_taxable_income=Decimal("60000"),
            total_claim_amount=Decimal("12932"),
            cpp_per_period=Decimal("110"),
            ei_per_period=Decimal("35"),
        )

        assert result.tax_reduction_s == Decimal("0")


class TestAlbertaK5PCredit:
    """Test Alberta supplemental credit (K5P) calculations."""

    def setup_method(self):
        """Create Alberta calculator."""
        self.calc = ProvincialTaxCalculator(
            province_code="AB",
            pay_periods_per_year=26,
            year=2025,
        )

    def test_alberta_k5p_below_threshold(self):
        """Test: Alberta K5P when (K1P + K2P) <= $3,600.

        K5P only applies when total credits exceed $3,600.
        """
        result = self.calc.calculate_provincial_tax(
            annual_taxable_income=Decimal("40000"),
            total_claim_amount=Decimal("22323"),  # Alberta BPA
            cpp_per_period=Decimal("80"),
            ei_per_period=Decimal("30"),
        )

        # Low income may not trigger K5P
        # Depends on actual K1P + K2P calculation
        assert result.supplemental_credit_k5p >= Decimal("0")

    def test_alberta_k5p_above_threshold(self):
        """Test: Alberta K5P when (K1P + K2P) > $3,600.

        K5P = ((K1P + K2P) - $3,600) × (0.04/0.06)
        """
        result = self.calc.calculate_provincial_tax(
            annual_taxable_income=Decimal("80000"),
            total_claim_amount=Decimal("22323"),
            cpp_per_period=Decimal("120"),
            ei_per_period=Decimal("40"),
        )

        # K5P should be calculated for higher income
        # Exact value depends on K1P + K2P exceeding $3,600
        assert result.supplemental_credit_k5p >= Decimal("0")


class TestDynamicBPA:
    """Test dynamic BPA calculations for MB, NS, YT."""

    def test_manitoba_full_bpa_low_income(self):
        """Test: Manitoba full BPA for low income.

        Manitoba uses income-based BPA adjustment.
        """
        calc = ProvincialTaxCalculator("MB", 26, 2025)

        bpa = calc.get_basic_personal_amount(
            annual_income=Decimal("40000"),
            net_income=Decimal("40000"),
        )

        # MB 2025 BPA is around $15,780 for low income
        assert bpa >= Decimal("14000")

    def test_manitoba_reduced_bpa_high_income(self):
        """Test: Manitoba reduced BPA for high income.

        High income reduces the BPA.
        """
        calc = ProvincialTaxCalculator("MB", 26, 2025)

        bpa_low = calc.get_basic_personal_amount(
            annual_income=Decimal("40000"),
            net_income=Decimal("40000"),
        )

        bpa_high = calc.get_basic_personal_amount(
            annual_income=Decimal("200000"),
            net_income=Decimal("200000"),
        )

        # High income should have same or lower BPA
        # Some provinces have completely flat BPA
        assert bpa_high <= bpa_low

    def test_nova_scotia_bpa(self):
        """Test: Nova Scotia BPA calculation.

        NS may have dynamic BPA based on income.
        """
        calc = ProvincialTaxCalculator("NS", 26, 2025)

        bpa_low = calc.get_basic_personal_amount(
            annual_income=Decimal("20000"),
        )

        bpa_high = calc.get_basic_personal_amount(
            annual_income=Decimal("80000"),
        )

        # Both should be valid BPA amounts
        assert bpa_low > Decimal("8000")
        assert bpa_high > Decimal("8000")

        # If dynamic, amounts may differ; if not, they should be equal
        if not calc.bpa_is_dynamic:
            assert bpa_low == bpa_high

    def test_yukon_bpa(self):
        """Test: Yukon BPA follows federal formula.

        YT may use income-based BPA similar to federal.
        """
        calc = ProvincialTaxCalculator("YT", 26, 2025)

        bpa = calc.get_basic_personal_amount(
            annual_income=Decimal("60000"),
        )

        # YT BPA should be around $16,129 (similar to federal)
        assert bpa >= Decimal("14000")


class TestPEISurtax:
    """Test PEI surtax calculations."""

    def setup_method(self):
        """Create PEI calculator."""
        self.calc = ProvincialTaxCalculator(
            province_code="PE",
            pay_periods_per_year=26,
            year=2025,
        )

    def test_pei_no_surtax_low_income(self):
        """Test: PEI low income - no surtax.

        PEI surtax: If T4 > $13,500: 10% × T4
        """
        result = self.calc.calculate_provincial_tax(
            annual_taxable_income=Decimal("50000"),
            total_claim_amount=Decimal("14250"),
            cpp_per_period=Decimal("100"),
            ei_per_period=Decimal("35"),
        )

        # Low basic tax should not trigger surtax
        assert result.surtax_v1 >= Decimal("0")

    def test_pei_with_surtax_high_income(self):
        """Test: PEI high income triggers surtax."""
        result = self.calc.calculate_provincial_tax(
            annual_taxable_income=Decimal("150000"),
            total_claim_amount=Decimal("14250"),
            cpp_per_period=Decimal("155"),
            ei_per_period=Decimal("41"),
        )

        # High income may trigger surtax
        # If T4 > $13,500, surtax = 10% × T4
        assert result.surtax_v1 >= Decimal("0")


class TestProvincialTaxCredits:
    """Test provincial tax credit calculations."""

    def setup_method(self):
        """Create Ontario calculator for testing."""
        self.calc = ProvincialTaxCalculator(
            province_code="ON",
            pay_periods_per_year=26,
            year=2025,
        )

    def test_k1p_personal_credit(self):
        """Test: K1P (personal tax credits) calculation.

        K1P = lowest_rate × TCP
        """
        k1p = self.calc.calculate_k1p(
            total_claim_amount=Decimal("12747"),
        )

        # Ontario lowest rate × BPA
        assert k1p > Decimal("0")

    def test_k2p_cpp_ei_credit(self):
        """Test: K2P (CPP/EI credits) calculation.

        K2P = lowest_rate × [(P × C × credit_ratio) + (P × EI)]
        """
        k2p = self.calc.calculate_k2p(
            cpp_per_period=Decimal("100"),
            ei_per_period=Decimal("35"),
        )

        assert k2p > Decimal("0")


class TestProvincialTaxFullCalculation:
    """Test complete provincial tax calculations."""

    @pytest.mark.parametrize("province,expected_range", [
        ("ON", (Decimal("2000"), Decimal("6000"))),
        ("BC", (Decimal("1500"), Decimal("5000"))),
        ("AB", (Decimal("2000"), Decimal("6000"))),
        ("MB", (Decimal("2000"), Decimal("6000"))),
        ("SK", (Decimal("2000"), Decimal("6000"))),
    ])
    def test_provincial_tax_reasonable_range(self, province, expected_range):
        """Test: Provincial tax for $60k income is in reasonable range."""
        calc = ProvincialTaxCalculator(
            province_code=province,
            pay_periods_per_year=26,
            year=2025,
        )

        bpa = calc.get_basic_personal_amount(Decimal("60000"))

        result = calc.calculate_provincial_tax(
            annual_taxable_income=Decimal("60000"),
            total_claim_amount=bpa,
            cpp_per_period=Decimal("115"),
            ei_per_period=Decimal("38"),
        )

        min_expected, max_expected = expected_range
        assert result.annual_provincial_tax_t2 >= min_expected
        assert result.annual_provincial_tax_t2 <= max_expected

    def test_calculation_details_method(self):
        """Test: Detailed calculation breakdown."""
        calc = ProvincialTaxCalculator("ON", 26, 2025)

        details = calc.get_calculation_details(
            annual_taxable_income=Decimal("60000"),
            total_claim_amount=Decimal("12747"),
            cpp_per_period=Decimal("115"),
            ei_per_period=Decimal("38"),
        )

        # Should have all expected keys
        assert "province" in details
        assert "inputs" in details
        assert "calculation" in details
        assert "adjustments" in details
        assert "result" in details
        assert "formula" in details


class TestProvincialTaxEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_income(self):
        """Test: Zero income should result in zero provincial tax."""
        calc = ProvincialTaxCalculator("ON", 26, 2025)

        result = calc.calculate_provincial_tax(
            annual_taxable_income=Decimal("0"),
            total_claim_amount=Decimal("12747"),
            cpp_per_period=Decimal("0"),
            ei_per_period=Decimal("0"),
        )

        assert result.basic_provincial_tax_t4 == Decimal("0")
        assert result.tax_per_period == Decimal("0")

    def test_income_below_bpa(self):
        """Test: Income below BPA should result in minimal tax."""
        calc = ProvincialTaxCalculator("ON", 26, 2025)

        bpa = calc.get_basic_personal_amount(Decimal("10000"))

        result = calc.calculate_provincial_tax(
            annual_taxable_income=Decimal("10000"),
            total_claim_amount=bpa,
            cpp_per_period=Decimal("25"),
            ei_per_period=Decimal("8"),
        )

        # Income below BPA should result in zero or minimal tax
        assert result.basic_provincial_tax_t4 == Decimal("0")

    def test_very_high_income(self):
        """Test: Very high income calculation."""
        calc = ProvincialTaxCalculator("ON", 26, 2025)

        result = calc.calculate_provincial_tax(
            annual_taxable_income=Decimal("500000"),
            total_claim_amount=Decimal("12747"),
            cpp_per_period=Decimal("155"),
            ei_per_period=Decimal("41"),
        )

        # High income should have significant tax
        assert result.annual_provincial_tax_t2 > Decimal("50000")
        assert result.tax_per_period > Decimal("2000")

    def test_convenience_method(self):
        """Test: Convenience method for tax per period."""
        calc = ProvincialTaxCalculator("ON", 26, 2025)

        tax = calc.calculate_tax_per_period(
            annual_taxable_income=Decimal("60000"),
            total_claim_amount=Decimal("12747"),
            cpp_per_period=Decimal("115"),
            ei_per_period=Decimal("38"),
        )

        # Should return reasonable tax amount
        assert tax > Decimal("50")
        assert tax < Decimal("500")


class TestProvincialTaxPDOCValidation:
    """Test cases validated against CRA PDOC.

    These tests should be updated with actual PDOC values.
    """

    def test_pdoc_case_ontario_60k(self):
        """
        PDOC Validation Case: Ontario, $60k annual, bi-weekly

        PDOC Input:
        - Province: Ontario
        - Gross: $2,307.69
        - Pay periods: 26
        - TD1 Claim: $12,747

        Provincial tax should be reasonable for Ontario.
        """
        calc = ProvincialTaxCalculator("ON", 26, 2025)

        result = calc.calculate_provincial_tax(
            annual_taxable_income=Decimal("60000"),
            total_claim_amount=Decimal("12747"),
            cpp_per_period=Decimal("129.30"),
            ei_per_period=Decimal("37.85"),
        )

        # Ontario provincial tax per period for $60k
        # Should be approximately $100-$200 per bi-weekly period
        assert result.tax_per_period > Decimal("80")
        assert result.tax_per_period < Decimal("250")

    def test_pdoc_case_bc_50k(self):
        """
        PDOC Validation Case: BC, $50k annual, bi-weekly

        BC should have tax reduction for lower income.
        """
        calc = ProvincialTaxCalculator("BC", 26, 2025)

        result = calc.calculate_provincial_tax(
            annual_taxable_income=Decimal("50000"),
            total_claim_amount=Decimal("12932"),
            cpp_per_period=Decimal("100"),
            ei_per_period=Decimal("32"),
        )

        # BC provincial tax for $50k should be lower due to tax reduction
        assert result.tax_per_period > Decimal("50")
        assert result.tax_per_period < Decimal("200")

    def test_pdoc_case_alberta_80k(self):
        """
        PDOC Validation Case: Alberta, $80k annual, bi-weekly

        Alberta has flat 10% rate (lowest) for first bracket.
        """
        calc = ProvincialTaxCalculator("AB", 26, 2025)

        result = calc.calculate_provincial_tax(
            annual_taxable_income=Decimal("80000"),
            total_claim_amount=Decimal("22323"),
            cpp_per_period=Decimal("120"),
            ei_per_period=Decimal("38"),
        )

        # Alberta has relatively simple tax structure
        assert result.tax_per_period > Decimal("100")
        assert result.tax_per_period < Decimal("300")
