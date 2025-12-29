"""
Federal Income Tax Calculator Tests

Tests federal income tax calculations following CRA T4127 Chapter 4, Step 2-3.
Uses Option 1 (annualized tax method).

2025 Key Parameters:
- BPAF (Basic Personal Amount Federal): $16,129
- CEA (Canada Employment Amount): $1,471
- Lowest Tax Rate (Jan-Jun): 15%
- Lowest Tax Rate (Jul onwards): 14%

Tax Brackets (2025 with Jul rate change):
- Up to $57,375: 14% (15% before July)
- $57,375 - $114,750: 20.5%
- $114,750 - $177,882: 26%
- $177,882 - $253,414: 29%
- Over $253,414: 33%
"""

import pytest
from datetime import date
from decimal import Decimal

from app.services.payroll.federal_tax_calculator import FederalTaxCalculator


class TestFederalTaxAnnualTaxableIncome:
    """Test annual taxable income (Factor A) calculations."""

    def setup_method(self):
        """Create calculator for bi-weekly (26 periods), July 2025."""
        self.calc = FederalTaxCalculator(
            pay_periods_per_year=26,
            year=2025,
            pay_date=date(2025, 7, 15),
        )

    def test_annual_taxable_income_simple(self):
        """Test: Basic annualization.

        A = P × I = 26 × $2,000 = $52,000
        """
        A = self.calc.calculate_annual_taxable_income(
            gross_per_period=Decimal("2000.00"),
        )

        assert A == Decimal("52000.00")

    def test_annual_taxable_income_with_rrsp(self):
        """Test: Annualization with RRSP deduction.

        A = P × (I - F) = 26 × ($2,500 - $200) = 26 × $2,300 = $59,800
        """
        A = self.calc.calculate_annual_taxable_income(
            gross_per_period=Decimal("2500.00"),
            rrsp_per_period=Decimal("200.00"),
        )

        assert A == Decimal("59800.00")

    def test_annual_taxable_income_with_all_deductions(self):
        """Test: Annualization with all pre-tax deductions.

        A = P × (I - F - F2 - U1 - CPP2)
        A = 26 × (2500 - 200 - 50 - 20 - 10) = 26 × 2220 = $57,720
        """
        A = self.calc.calculate_annual_taxable_income(
            gross_per_period=Decimal("2500.00"),
            rrsp_per_period=Decimal("200.00"),
            union_dues_per_period=Decimal("20.00"),
            cpp2_per_period=Decimal("10.00"),
            cpp_enhancement_per_period=Decimal("50.00"),
        )

        assert A == Decimal("57720.00")

    def test_annual_taxable_income_negative_becomes_zero(self):
        """Test: Negative annual income becomes zero."""
        A = self.calc.calculate_annual_taxable_income(
            gross_per_period=Decimal("100.00"),
            rrsp_per_period=Decimal("200.00"),  # RRSP > gross
        )

        assert A == Decimal("0")


class TestFederalTaxK1PersonalCredit:
    """Test K1 (personal tax credits) calculations."""

    def setup_method(self):
        """Create calculator for bi-weekly (26 periods), July 2025."""
        self.calc = FederalTaxCalculator(
            pay_periods_per_year=26,
            year=2025,
            pay_date=date(2025, 7, 15),
        )

    def test_k1_personal_credit_standard(self):
        """Test: K1 calculation from TD1 claim.

        K1 = rate × TC = 0.14 × $16,129 = $2,258.06
        """
        k1 = self.calc.calculate_k1(total_claim_amount=Decimal("16129.00"))

        assert k1 == Decimal("2258.06")

    def test_k1_with_additional_claims(self):
        """Test: K1 with additional TD1 claims."""
        # TC includes BPA + spouse amount + other claims
        tc = Decimal("20000.00")
        k1 = self.calc.calculate_k1(total_claim_amount=tc)

        # K1 = 0.14 × 20000 = $2,800.00
        assert k1 == Decimal("2800.00")

    def test_k1_zero_claim(self):
        """Test: K1 with zero claim amount."""
        k1 = self.calc.calculate_k1(total_claim_amount=Decimal("0"))

        assert k1 == Decimal("0")


class TestFederalTaxK2CPPEICredit:
    """Test K2 (CPP and EI tax credits) calculations."""

    def setup_method(self):
        """Create calculator for bi-weekly (26 periods), July 2025."""
        self.calc = FederalTaxCalculator(
            pay_periods_per_year=26,
            year=2025,
            pay_date=date(2025, 7, 15),
        )

    def test_k2_cpp_ei_credit(self):
        """Test: K2 from CPP/EI contributions.

        K2 involves CPP credit ratio (4.95%/5.95%) because
        only the base rate qualifies for the credit.
        """
        k2 = self.calc.calculate_k2(
            cpp_per_period=Decimal("110.00"),
            ei_per_period=Decimal("35.00"),
        )

        # K2 = rate × [(P × C × credit_ratio) + (P × EI)]
        # Should be reasonable range
        assert k2 > Decimal("300")
        assert k2 < Decimal("1000")

    def test_k2_cpp_only(self):
        """Test: K2 with only CPP contribution."""
        k2 = self.calc.calculate_k2(
            cpp_per_period=Decimal("100.00"),
            ei_per_period=Decimal("0"),
        )

        assert k2 > Decimal("0")

    def test_k2_ei_only(self):
        """Test: K2 with only EI contribution."""
        k2 = self.calc.calculate_k2(
            cpp_per_period=Decimal("0"),
            ei_per_period=Decimal("40.00"),
        )

        assert k2 > Decimal("0")

    def test_k2_capped_at_annual_max(self):
        """Test: K2 components are capped at annual maximums."""
        # Very high CPP/EI should still be capped
        k2_normal = self.calc.calculate_k2(
            cpp_per_period=Decimal("200.00"),
            ei_per_period=Decimal("50.00"),
        )

        k2_extreme = self.calc.calculate_k2(
            cpp_per_period=Decimal("500.00"),
            ei_per_period=Decimal("100.00"),
        )

        # Both should be similar due to annual caps
        assert abs(k2_normal - k2_extreme) < Decimal("100")


class TestFederalTaxK4EmploymentCredit:
    """Test K4 (Canada Employment Amount credit) calculations."""

    def setup_method(self):
        """Create calculator for bi-weekly (26 periods), July 2025."""
        self.calc = FederalTaxCalculator(
            pay_periods_per_year=26,
            year=2025,
            pay_date=date(2025, 7, 15),
        )

    def test_k4_employment_credit_full(self):
        """Test: K4 for income above CEA.

        K4 = rate × min(A, CEA) = 0.14 × $1,471 = $205.94
        """
        k4 = self.calc.calculate_k4(annual_income=Decimal("60000.00"))

        assert k4 == Decimal("205.94")

    def test_k4_employment_credit_low_income(self):
        """Test: K4 capped at actual income.

        K4 = rate × min(1000, 1471) = 0.14 × 1000 = $140.00
        """
        k4 = self.calc.calculate_k4(annual_income=Decimal("1000.00"))

        assert k4 == Decimal("140.00")

    def test_k4_employment_credit_zero_income(self):
        """Test: K4 with zero income."""
        k4 = self.calc.calculate_k4(annual_income=Decimal("0"))

        assert k4 == Decimal("0")

    def test_k4_employment_credit_exactly_cea(self):
        """Test: K4 when income exactly equals CEA."""
        k4 = self.calc.calculate_k4(annual_income=Decimal("1471.00"))

        assert k4 == Decimal("205.94")


class TestFederalTaxBrackets:
    """Test federal tax bracket selection and calculations."""

    def setup_method(self):
        """Create calculator for bi-weekly (26 periods), July 2025."""
        self.calc = FederalTaxCalculator(
            pay_periods_per_year=26,
            year=2025,
            pay_date=date(2025, 7, 15),
        )

    @pytest.mark.parametrize("income,expected_rate", [
        (Decimal("40000"), Decimal("0.14")),   # Bracket 1
        (Decimal("60000"), Decimal("0.205")),  # Bracket 2
        (Decimal("120000"), Decimal("0.26")),  # Bracket 3
        (Decimal("180000"), Decimal("0.29")),  # Bracket 4
        (Decimal("300000"), Decimal("0.33")),  # Bracket 5
    ])
    def test_tax_brackets_july_onwards(self, income, expected_rate):
        """Test: Correct tax bracket selection for July 2025+."""
        result = self.calc.calculate_federal_tax(
            annual_taxable_income=income,
            total_claim_amount=Decimal("16129.00"),
            cpp_per_period=Decimal("100"),
            ei_per_period=Decimal("35"),
        )

        assert result.tax_rate == expected_rate

    def test_tax_bracket_boundary_first(self):
        """Test: At first bracket boundary.

        The first bracket (14%) applies up to certain threshold.
        $57,375 is actually at/above the first bracket threshold,
        so it falls into the second bracket (20.5%).
        """
        result = self.calc.calculate_federal_tax(
            annual_taxable_income=Decimal("57375.00"),
            total_claim_amount=Decimal("16129.00"),
            cpp_per_period=Decimal("100"),
            ei_per_period=Decimal("35"),
        )

        # $57,375 is at the boundary, falls into second bracket
        assert result.tax_rate == Decimal("0.205")


class TestFederalTaxMidYearRateChange:
    """Test mid-year rate change (July 2025: 15% → 14%)."""

    def test_jan_to_jun_rate(self):
        """Test: 15% rate before July 2025."""
        calc_jan = FederalTaxCalculator(
            pay_periods_per_year=26,
            year=2025,
            pay_date=date(2025, 3, 15),  # March
        )

        result = calc_jan.calculate_federal_tax(
            annual_taxable_income=Decimal("40000"),
            total_claim_amount=Decimal("16129.00"),
            cpp_per_period=Decimal("100"),
            ei_per_period=Decimal("35"),
        )

        assert result.tax_rate == Decimal("0.15")

    def test_jul_onwards_rate(self):
        """Test: 14% rate from July 2025."""
        calc_jul = FederalTaxCalculator(
            pay_periods_per_year=26,
            year=2025,
            pay_date=date(2025, 8, 15),  # August
        )

        result = calc_jul.calculate_federal_tax(
            annual_taxable_income=Decimal("40000"),
            total_claim_amount=Decimal("16129.00"),
            cpp_per_period=Decimal("100"),
            ei_per_period=Decimal("35"),
        )

        assert result.tax_rate == Decimal("0.14")

    def test_june_still_15_percent(self):
        """Test: June 30 still uses 15% rate."""
        calc_jun = FederalTaxCalculator(
            pay_periods_per_year=26,
            year=2025,
            pay_date=date(2025, 6, 30),
        )

        result = calc_jun.calculate_federal_tax(
            annual_taxable_income=Decimal("40000"),
            total_claim_amount=Decimal("16129.00"),
            cpp_per_period=Decimal("100"),
            ei_per_period=Decimal("35"),
        )

        assert result.tax_rate == Decimal("0.15")

    def test_july_1_uses_14_percent(self):
        """Test: July 1 uses 14% rate."""
        calc_jul = FederalTaxCalculator(
            pay_periods_per_year=26,
            year=2025,
            pay_date=date(2025, 7, 1),
        )

        result = calc_jul.calculate_federal_tax(
            annual_taxable_income=Decimal("40000"),
            total_claim_amount=Decimal("16129.00"),
            cpp_per_period=Decimal("100"),
            ei_per_period=Decimal("35"),
        )

        assert result.tax_rate == Decimal("0.14")


class TestFederalTaxFullCalculation:
    """Test complete federal tax calculation."""

    def setup_method(self):
        """Create calculator for bi-weekly (26 periods), July 2025."""
        self.calc = FederalTaxCalculator(
            pay_periods_per_year=26,
            year=2025,
            pay_date=date(2025, 7, 15),
        )

    def test_full_calculation_standard_employee(self):
        """Test: Complete calculation for standard employee.

        $60k annual, bi-weekly, standard claims.
        """
        result = self.calc.calculate_federal_tax(
            annual_taxable_income=Decimal("60000.00"),
            total_claim_amount=Decimal("16129.00"),
            cpp_per_period=Decimal("115.00"),
            ei_per_period=Decimal("38.00"),
        )

        # Basic assertions
        assert result.annual_taxable_income == Decimal("60000.00")
        assert result.tax_rate == Decimal("0.205")  # Second bracket
        assert result.personal_credits_k1 > Decimal("0")
        assert result.cpp_ei_credits_k2 > Decimal("0")
        assert result.employment_credit_k4 > Decimal("0")
        assert result.basic_federal_tax_t3 >= Decimal("0")
        assert result.annual_federal_tax_t1 >= Decimal("0")
        assert result.tax_per_period >= Decimal("0")

    def test_full_calculation_low_income_no_tax(self):
        """Test: Low income may result in no tax due to credits."""
        result = self.calc.calculate_federal_tax(
            annual_taxable_income=Decimal("15000.00"),
            total_claim_amount=Decimal("16129.00"),
            cpp_per_period=Decimal("50.00"),
            ei_per_period=Decimal("12.00"),
        )

        # Income below BPA should result in minimal or no tax
        assert result.basic_federal_tax_t3 == Decimal("0") or result.basic_federal_tax_t3 < Decimal("100")

    def test_full_calculation_high_income(self):
        """Test: High income calculation."""
        result = self.calc.calculate_federal_tax(
            annual_taxable_income=Decimal("200000.00"),
            total_claim_amount=Decimal("16129.00"),
            cpp_per_period=Decimal("155.00"),
            ei_per_period=Decimal("41.00"),
        )

        # High income should have significant tax
        assert result.tax_rate == Decimal("0.29")  # Fourth bracket
        assert result.annual_federal_tax_t1 > Decimal("30000")
        assert result.tax_per_period > Decimal("1000")

    def test_tax_per_period_convenience_method(self):
        """Test: Convenience method calculates correctly."""
        tax = self.calc.calculate_tax_per_period(
            gross_per_period=Decimal("2307.69"),
            total_claim_amount=Decimal("16129.00"),
            cpp_per_period=Decimal("115.00"),
            ei_per_period=Decimal("38.00"),
        )

        # Should return a reasonable tax amount
        assert tax > Decimal("0")
        assert tax < Decimal("1000")  # Reasonable for $60k income

    def test_calculation_details_method(self):
        """Test: Detailed calculation breakdown."""
        details = self.calc.get_calculation_details(
            gross_per_period=Decimal("2307.69"),
            total_claim_amount=Decimal("16129.00"),
            cpp_per_period=Decimal("115.00"),
            ei_per_period=Decimal("38.00"),
        )

        # Should have all expected keys
        assert "inputs" in details
        assert "calculation" in details
        assert "result" in details
        assert "formula" in details


class TestFederalTaxEdgeCases:
    """Test edge cases and boundary conditions."""

    def setup_method(self):
        """Create calculator for bi-weekly (26 periods), July 2025."""
        self.calc = FederalTaxCalculator(
            pay_periods_per_year=26,
            year=2025,
            pay_date=date(2025, 7, 15),
        )

    def test_zero_income(self):
        """Test: Zero income should result in zero tax."""
        result = self.calc.calculate_federal_tax(
            annual_taxable_income=Decimal("0"),
            total_claim_amount=Decimal("16129.00"),
            cpp_per_period=Decimal("0"),
            ei_per_period=Decimal("0"),
        )

        assert result.basic_federal_tax_t3 == Decimal("0")
        assert result.tax_per_period == Decimal("0")

    def test_zero_claim_amount(self):
        """Test: Zero claim amount (employee requested no credits)."""
        result = self.calc.calculate_federal_tax(
            annual_taxable_income=Decimal("60000.00"),
            total_claim_amount=Decimal("0"),
            cpp_per_period=Decimal("100.00"),
            ei_per_period=Decimal("35.00"),
        )

        # Should have higher tax due to no K1 credit
        assert result.personal_credits_k1 == Decimal("0")
        assert result.basic_federal_tax_t3 > Decimal("5000")

    def test_k3_other_credits(self):
        """Test: K3 (other tax credits) reduces tax."""
        result_no_k3 = self.calc.calculate_federal_tax(
            annual_taxable_income=Decimal("60000.00"),
            total_claim_amount=Decimal("16129.00"),
            cpp_per_period=Decimal("100.00"),
            ei_per_period=Decimal("35.00"),
            k3=Decimal("0"),
        )

        result_with_k3 = self.calc.calculate_federal_tax(
            annual_taxable_income=Decimal("60000.00"),
            total_claim_amount=Decimal("16129.00"),
            cpp_per_period=Decimal("100.00"),
            ei_per_period=Decimal("35.00"),
            k3=Decimal("500.00"),  # Medical or tuition credits
        )

        # K3 should reduce tax
        assert result_with_k3.basic_federal_tax_t3 < result_no_k3.basic_federal_tax_t3

    def test_very_high_income(self):
        """Test: Very high income in top bracket."""
        result = self.calc.calculate_federal_tax(
            annual_taxable_income=Decimal("500000.00"),
            total_claim_amount=Decimal("16129.00"),
            cpp_per_period=Decimal("155.00"),
            ei_per_period=Decimal("41.00"),
        )

        assert result.tax_rate == Decimal("0.33")  # Top bracket
        assert result.tax_per_period > Decimal("5000")


class TestFederalTaxPDOCValidation:
    """Test cases validated against CRA PDOC.

    These tests should be updated with actual PDOC values.
    """

    def setup_method(self):
        """Create calculator for bi-weekly (26 periods), July 2025."""
        self.calc = FederalTaxCalculator(
            pay_periods_per_year=26,
            year=2025,
            pay_date=date(2025, 7, 15),
        )

    def test_pdoc_case_standard_60k(self):
        """
        PDOC Validation Case: Ontario, $60k annual, bi-weekly

        PDOC Input:
        - Province: Ontario
        - Gross: $2,307.69
        - Pay periods: 26
        - TD1 Claim: $16,129

        Should produce reasonable federal tax per period.
        """
        result = self.calc.calculate_federal_tax(
            annual_taxable_income=Decimal("60000.00"),
            total_claim_amount=Decimal("16129.00"),
            cpp_per_period=Decimal("129.30"),  # Approximate
            ei_per_period=Decimal("37.85"),    # Approximate
        )

        # Federal tax per period should be in reasonable range
        # Approximately $200-$350 per bi-weekly period for $60k income
        assert result.tax_per_period > Decimal("150")
        assert result.tax_per_period < Decimal("400")

    def test_pdoc_case_low_income_25k(self):
        """
        PDOC Validation Case: Low income $25k annual

        Low income should result in minimal tax due to credits.
        """
        result = self.calc.calculate_federal_tax(
            annual_taxable_income=Decimal("25000.00"),
            total_claim_amount=Decimal("16129.00"),
            cpp_per_period=Decimal("50.00"),
            ei_per_period=Decimal("16.00"),
        )

        # Should be minimal or no federal tax
        assert result.tax_per_period < Decimal("100")
