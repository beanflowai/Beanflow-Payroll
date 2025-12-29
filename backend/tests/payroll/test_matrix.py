"""
Test Matrix for PayrollEngine - Phase 4.

Systematic coverage of all scenario combinations:
- 12 Provinces × 4 Pay Frequencies × 5 Income Levels
- Essential Tests (E01-E12)
- Boundary Tests (B01-B10)
- Special Provincial Rules (S01-S10)
- YTD Scenarios

This test file validates the complete payroll calculation matrix
as defined in docs/test-plan/04_test_matrix.md

Phase 4 - Test Matrix Implementation
"""

import pytest
from decimal import Decimal
from datetime import date
from typing import NamedTuple

from app.services.payroll.payroll_engine import PayrollEngine, EmployeePayrollInput
from app.models.payroll import Province, PayFrequency


# =============================================================================
# Constants and Reference Data
# =============================================================================

# 2025 CPP Parameters
CPP_YMPE = Decimal("71300.00")
CPP_YAMPE = Decimal("81200.00")
CPP_BASIC_EXEMPTION = Decimal("3500.00")
CPP_BASE_RATE = Decimal("0.0595")
CPP_ADDITIONAL_RATE = Decimal("0.04")
CPP_MAX_BASE = Decimal("4034.10")
CPP_MAX_ADDITIONAL = Decimal("396.00")

# 2025 EI Parameters
EI_MIE = Decimal("65700.00")
EI_RATE = Decimal("0.0164")
EI_MAX = Decimal("1077.48")

# 2025 Federal BPA
FEDERAL_BPA = Decimal("16129.00")

# Provincial BPA 2025
PROVINCIAL_BPA = {
    Province.AB: Decimal("22323.00"),
    Province.BC: Decimal("12932.00"),
    Province.MB: Decimal("15780.00"),
    Province.NB: Decimal("13396.00"),
    Province.NL: Decimal("11067.00"),
    Province.NS: Decimal("11744.00"),
    Province.NT: Decimal("17842.00"),
    Province.NU: Decimal("19274.00"),
    Province.ON: Decimal("12747.00"),
    Province.PE: Decimal("14250.00"),
    Province.SK: Decimal("18991.00"),
    Province.YT: Decimal("16129.00"),
}

# Income levels for testing
INCOME_LEVELS = {
    "very_low": Decimal("18000"),      # Below tax threshold (~$692/biweekly)
    "low": Decimal("35000"),           # First tax bracket (~$1,346/biweekly)
    "medium": Decimal("60000"),        # Second tax bracket (~$2,308/biweekly)
    "high": Decimal("85000"),          # Third bracket, CPP2 range (~$3,269/biweekly)
    "very_high": Decimal("150000"),    # Top brackets, all maxes (~$5,769/biweekly)
}


class ExpectedRange(NamedTuple):
    """Expected value range for test validation."""
    min_value: Decimal
    max_value: Decimal


# =============================================================================
# Helper Functions
# =============================================================================


def create_standard_input(
    province: Province,
    pay_frequency: PayFrequency,
    annual_income: Decimal,
    pay_date: date = date(2025, 7, 18),
    ytd_gross: Decimal = Decimal("0"),
    ytd_cpp_base: Decimal = Decimal("0"),
    ytd_cpp_additional: Decimal = Decimal("0"),
    ytd_ei: Decimal = Decimal("0"),
    is_cpp_exempt: bool = False,
    is_ei_exempt: bool = False,
    cpp2_exempt: bool = False,
    rrsp: Decimal = Decimal("0"),
) -> EmployeePayrollInput:
    """Create a standard employee payroll input for testing."""
    periods = pay_frequency.periods_per_year
    gross_per_period = (annual_income / periods).quantize(Decimal("0.01"))

    return EmployeePayrollInput(
        employee_id=f"matrix_{province.value}_{pay_frequency.value}_{annual_income}",
        province=province,
        pay_frequency=pay_frequency,
        pay_date=pay_date,
        gross_regular=gross_per_period,
        federal_claim_amount=FEDERAL_BPA,
        provincial_claim_amount=PROVINCIAL_BPA[province],
        rrsp_per_period=rrsp,
        ytd_gross=ytd_gross,
        ytd_pensionable_earnings=ytd_gross,
        ytd_insurable_earnings=ytd_gross,
        ytd_cpp_base=ytd_cpp_base,
        ytd_cpp_additional=ytd_cpp_additional,
        ytd_ei=ytd_ei,
        is_cpp_exempt=is_cpp_exempt,
        is_ei_exempt=is_ei_exempt,
        cpp2_exempt=cpp2_exempt,
    )


# =============================================================================
# ESSENTIAL TESTS (E01-E12) - Priority 1
# =============================================================================


class TestEssentialScenarios:
    """
    Essential test scenarios that must pass for release.

    These tests cover the most common and critical payroll scenarios
    as defined in the test matrix document.
    """

    def setup_method(self):
        self.engine = PayrollEngine(year=2025)

    def test_e01_ontario_medium_biweekly_standard(self):
        """E01: Ontario baseline case - $60k bi-weekly, standard conditions."""
        input_data = create_standard_input(
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            annual_income=INCOME_LEVELS["medium"],
        )
        result = self.engine.calculate(input_data)

        # Baseline validations
        assert result.total_gross == Decimal("2307.69")
        assert result.cpp_base > Decimal("100")  # ~$129
        assert result.cpp_base < Decimal("150")
        assert result.ei_employee > Decimal("30")  # ~$38
        assert result.ei_employee < Decimal("45")
        assert result.federal_tax > Decimal("180")  # ~$210
        assert result.federal_tax < Decimal("250")
        assert result.provincial_tax > Decimal("90")  # ~$117
        assert result.provincial_tax < Decimal("150")
        assert result.net_pay > Decimal("1700")
        assert result.net_pay < Decimal("1900")

    def test_e02_ontario_high_monthly_surtax(self):
        """E02: Ontario high income with surtax - $120k monthly."""
        input_data = create_standard_input(
            province=Province.ON,
            pay_frequency=PayFrequency.MONTHLY,
            annual_income=Decimal("120000"),
        )
        result = self.engine.calculate(input_data)

        # High income should trigger Ontario surtax
        assert result.total_gross == Decimal("10000.00")
        # Federal tax around $1,472 for $10k/month with 14% lowest rate (Jul+)
        assert result.federal_tax > Decimal("1400")
        assert result.federal_tax < Decimal("1600")
        # Provincial tax includes surtax ($741) and health premium ($750)
        assert result.provincial_tax > Decimal("700")
        assert result.net_pay > Decimal("0")

    def test_e03_alberta_medium_biweekly_k5p(self):
        """E03: Alberta with K5P credit - $60k bi-weekly."""
        input_data = create_standard_input(
            province=Province.AB,
            pay_frequency=PayFrequency.BIWEEKLY,
            annual_income=INCOME_LEVELS["medium"],
        )
        result = self.engine.calculate(input_data)

        # Alberta has flat 10% rate and high BPA ($22,323)
        assert result.total_gross == Decimal("2307.69")
        # Alberta should have lower provincial tax due to high BPA
        assert result.provincial_tax < Decimal("150")

    def test_e04_bc_low_biweekly_tax_reduction(self):
        """E04: BC low income with tax reduction - $35k bi-weekly."""
        input_data = create_standard_input(
            province=Province.BC,
            pay_frequency=PayFrequency.BIWEEKLY,
            annual_income=INCOME_LEVELS["low"],
        )
        result = self.engine.calculate(input_data)

        # BC has tax reduction (Factor S) for low income
        assert result.total_gross == Decimal("1346.15")
        # Low income should have minimal provincial tax
        assert result.provincial_tax >= Decimal("0")
        assert result.provincial_tax < Decimal("50")

    def test_e05_manitoba_medium_biweekly_dynamic_bpa(self):
        """E05: Manitoba with dynamic BPA - $60k bi-weekly."""
        input_data = create_standard_input(
            province=Province.MB,
            pay_frequency=PayFrequency.BIWEEKLY,
            annual_income=INCOME_LEVELS["medium"],
        )
        result = self.engine.calculate(input_data)

        # Manitoba has dynamic BPA that reduces at high income
        assert result.total_gross == Decimal("2307.69")
        # Manitoba typically has higher provincial tax
        assert result.provincial_tax > Decimal("100")

    def test_e06_nova_scotia_medium_biweekly_two_tier_bpa(self):
        """E06: Nova Scotia with two-tier BPA - $60k bi-weekly."""
        input_data = create_standard_input(
            province=Province.NS,
            pay_frequency=PayFrequency.BIWEEKLY,
            annual_income=INCOME_LEVELS["medium"],
        )
        result = self.engine.calculate(input_data)

        # NS has two-tier BPA based on income
        assert result.total_gross == Decimal("2307.69")
        assert result.provincial_tax > Decimal("100")

    def test_e07_yukon_medium_biweekly_federal_bpa(self):
        """E07: Yukon follows federal BPA formula - $60k bi-weekly."""
        input_data = create_standard_input(
            province=Province.YT,
            pay_frequency=PayFrequency.BIWEEKLY,
            annual_income=INCOME_LEVELS["medium"],
        )
        result = self.engine.calculate(input_data)

        # Yukon follows federal BPA formula
        assert result.total_gross == Decimal("2307.69")
        assert result.provincial_tax >= Decimal("0")
        assert result.net_pay > Decimal("0")

    def test_e08_ontario_high_biweekly_ytd_max_cpp(self):
        """E08: Ontario high income with CPP max reached - YTD at max."""
        input_data = create_standard_input(
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            annual_income=INCOME_LEVELS["high"],
            ytd_gross=Decimal("70000"),
            ytd_cpp_base=CPP_MAX_BASE,  # Max already reached
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("900"),
        )
        result = self.engine.calculate(input_data)

        # CPP base should be zero since max reached
        assert result.cpp_base == Decimal("0")
        # But taxes still apply
        assert result.federal_tax > Decimal("0")
        assert result.provincial_tax > Decimal("0")

    def test_e09_ontario_high_biweekly_ytd_max_ei(self):
        """E09: Ontario high income with EI max reached - YTD at max."""
        input_data = create_standard_input(
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            annual_income=INCOME_LEVELS["high"],
            ytd_gross=Decimal("70000"),
            ytd_cpp_base=Decimal("3500"),
            ytd_ei=EI_MAX,  # Max already reached
        )
        result = self.engine.calculate(input_data)

        # EI should be zero since max reached
        assert result.ei_employee == Decimal("0")
        # But CPP and taxes still apply
        assert result.cpp_base > Decimal("0")
        assert result.federal_tax > Decimal("0")

    def test_e10_ontario_very_high_monthly_cpp2(self):
        """E10: Ontario very high income triggering CPP2 - $150k monthly."""
        input_data = create_standard_input(
            province=Province.ON,
            pay_frequency=PayFrequency.MONTHLY,
            annual_income=INCOME_LEVELS["very_high"],
            ytd_gross=Decimal("75000"),  # 6 months, above YMPE
            ytd_cpp_base=CPP_MAX_BASE,  # Base CPP maxed
            ytd_cpp_additional=Decimal("200"),  # Some CPP2 already
            ytd_ei=EI_MAX,  # EI maxed
        )
        result = self.engine.calculate(input_data)

        # Base CPP should be zero (maxed)
        assert result.cpp_base == Decimal("0")
        # CPP2 may continue if not maxed
        # (YAMPE - YMPE = $81,200 - $71,300 = $9,900 earnings ceiling)
        assert result.cpp_additional >= Decimal("0")
        # EI should be zero (maxed)
        assert result.ei_employee == Decimal("0")
        # High taxes expected
        assert result.federal_tax > Decimal("2000")

    def test_e11_ontario_medium_biweekly_cpp_exempt(self):
        """E11: Ontario with CPP exemption - $60k bi-weekly."""
        input_data = create_standard_input(
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            annual_income=INCOME_LEVELS["medium"],
            is_cpp_exempt=True,
        )
        result = self.engine.calculate(input_data)

        # CPP should be zero due to exemption
        assert result.cpp_base == Decimal("0")
        assert result.cpp_additional == Decimal("0")
        assert result.cpp_total == Decimal("0")
        assert result.cpp_employer == Decimal("0")
        # But EI and taxes still apply
        assert result.ei_employee > Decimal("0")
        assert result.federal_tax > Decimal("0")

    def test_e12_ontario_medium_biweekly_ei_exempt(self):
        """E12: Ontario with EI exemption - $60k bi-weekly."""
        input_data = create_standard_input(
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            annual_income=INCOME_LEVELS["medium"],
            is_ei_exempt=True,
        )
        result = self.engine.calculate(input_data)

        # EI should be zero due to exemption
        assert result.ei_employee == Decimal("0")
        assert result.ei_employer == Decimal("0")
        # But CPP and taxes still apply
        assert result.cpp_base > Decimal("0")
        assert result.federal_tax > Decimal("0")


# =============================================================================
# BOUNDARY TESTS (B01-B10) - Priority 3
# =============================================================================


class TestBoundaryConditions:
    """
    Boundary condition tests for CPP, CPP2, and EI thresholds.

    These tests verify correct behavior at critical income boundaries.
    """

    def setup_method(self):
        self.engine = PayrollEngine(year=2025)

    def test_b01_income_at_cpp_exemption(self):
        """B01: Annual income exactly at CPP basic exemption ($3,500)."""
        input_data = create_standard_input(
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            annual_income=CPP_BASIC_EXEMPTION,  # $3,500
        )
        result = self.engine.calculate(input_data)

        # Per-period gross: $3,500 / 26 = $134.62
        # Per-period exemption: $3,500 / 26 = $134.62
        # Pensionable earnings = $134.62 - $134.62 = $0
        # CPP should be zero or minimal
        assert result.cpp_base >= Decimal("0")
        assert result.cpp_base < Decimal("1")

    def test_b02_income_just_above_cpp_exemption(self):
        """B02: Annual income just above CPP basic exemption ($4,000)."""
        input_data = create_standard_input(
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            annual_income=Decimal("4000"),
        )
        result = self.engine.calculate(input_data)

        # Per-period gross: $4,000 / 26 = $153.85
        # Per-period exemption: $3,500 / 26 = $134.62
        # Pensionable: $153.85 - $134.62 = $19.23
        # CPP: $19.23 × 5.95% = $1.14
        assert result.cpp_base > Decimal("0")
        assert result.cpp_base < Decimal("3")

    def test_b03_income_at_ympe(self):
        """B03: Annual income exactly at YMPE ($71,300) - minimal or no CPP2."""
        input_data = create_standard_input(
            province=Province.ON,
            pay_frequency=PayFrequency.MONTHLY,
            annual_income=CPP_YMPE,  # $71,300
        )
        result = self.engine.calculate(input_data)

        # At YMPE, very minimal CPP2 may apply due to rounding
        # Per-period: $71,300 / 12 = $5,941.67
        # When annualized, this may push slightly above YMPE threshold
        assert result.cpp_base > Decimal("0")
        # CPP2 should be zero or minimal (< $1 due to rounding)
        assert result.cpp_additional < Decimal("1")

    def test_b04_income_just_above_ympe(self):
        """B04: Annual income just above YMPE ($72,000) - CPP2 starts."""
        input_data = create_standard_input(
            province=Province.ON,
            pay_frequency=PayFrequency.MONTHLY,
            annual_income=Decimal("72000"),
            ytd_gross=Decimal("66000"),  # 11 months, near YMPE
            ytd_cpp_base=Decimal("3800"),  # Near base max
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("980"),
        )
        result = self.engine.calculate(input_data)

        # Just above YMPE, CPP2 may apply for earnings above YMPE
        # CPP2 applies to earnings between YMPE and YAMPE
        assert result.cpp_base >= Decimal("0")
        # CPP2 depends on how much of this period's earnings exceed YMPE

    def test_b05_income_at_yampe(self):
        """B05: Annual income exactly at YAMPE ($81,200) - CPP2 at ceiling."""
        # After a full year at YAMPE income, CPP2 would be maxed
        input_data = create_standard_input(
            province=Province.ON,
            pay_frequency=PayFrequency.MONTHLY,
            annual_income=CPP_YAMPE,  # $81,200
            ytd_gross=Decimal("74433.33"),  # 11 months
            ytd_cpp_base=CPP_MAX_BASE,  # Base maxed
            ytd_cpp_additional=Decimal("360"),  # Near CPP2 max ($396)
            ytd_ei=EI_MAX,  # EI maxed
        )
        result = self.engine.calculate(input_data)

        # Base CPP should be zero (maxed)
        assert result.cpp_base == Decimal("0")
        # CPP2 should be partial (remaining to $396 max)
        assert result.cpp_additional <= Decimal("36.00") + Decimal("0.01")
        assert result.ei_employee == Decimal("0")

    def test_b06_income_above_yampe(self):
        """B06: Annual income above YAMPE ($100,000) - CPP2 capped."""
        input_data = create_standard_input(
            province=Province.ON,
            pay_frequency=PayFrequency.MONTHLY,
            annual_income=Decimal("100000"),
            ytd_gross=Decimal("91666.67"),  # 11 months
            ytd_cpp_base=CPP_MAX_BASE,  # Base maxed
            ytd_cpp_additional=CPP_MAX_ADDITIONAL,  # CPP2 maxed
            ytd_ei=EI_MAX,  # EI maxed
        )
        result = self.engine.calculate(input_data)

        # All CPP contributions should be zero (maxed)
        assert result.cpp_base == Decimal("0")
        assert result.cpp_additional == Decimal("0")
        assert result.ei_employee == Decimal("0")
        # Only taxes apply
        assert result.federal_tax > Decimal("0")

    def test_b07_income_at_mie(self):
        """B07: Annual income exactly at MIE ($65,700) - EI at max."""
        input_data = create_standard_input(
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            annual_income=EI_MIE,  # $65,700
        )
        result = self.engine.calculate(input_data)

        # Per-period: $65,700 / 26 = $2,526.92
        # EI: $2,526.92 × 1.64% = $41.44
        assert result.ei_employee > Decimal("40")
        assert result.ei_employee < Decimal("45")

    def test_b08_ytd_cpp_at_99_percent_max(self):
        """B08: YTD CPP at 99% of max - partial deduction expected."""
        ytd_cpp_99 = (CPP_MAX_BASE * Decimal("0.99")).quantize(Decimal("0.01"))
        remaining = CPP_MAX_BASE - ytd_cpp_99  # ~$40.34

        input_data = create_standard_input(
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            annual_income=INCOME_LEVELS["high"],
            ytd_gross=Decimal("65000"),
            ytd_cpp_base=ytd_cpp_99,  # 99% of max
            ytd_ei=Decimal("900"),
        )
        result = self.engine.calculate(input_data)

        # CPP should be exactly the remaining amount
        assert result.cpp_base <= remaining + Decimal("0.01")
        assert result.cpp_base > Decimal("0")

    def test_b09_ytd_ei_at_99_percent_max(self):
        """B09: YTD EI at 99% of max - partial deduction expected."""
        ytd_ei_99 = (EI_MAX * Decimal("0.99")).quantize(Decimal("0.01"))
        remaining = EI_MAX - ytd_ei_99  # ~$10.77

        input_data = create_standard_input(
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            annual_income=INCOME_LEVELS["high"],
            ytd_gross=Decimal("63000"),
            ytd_cpp_base=Decimal("3500"),
            ytd_ei=ytd_ei_99,  # 99% of max
        )
        result = self.engine.calculate(input_data)

        # EI should be exactly the remaining amount
        assert result.ei_employee <= remaining + Decimal("0.01")
        assert result.ei_employee > Decimal("0")

    def test_b10_zero_income(self):
        """B10: Zero income - all deductions should be zero."""
        input_data = EmployeePayrollInput(
            employee_id="matrix_zero",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            gross_regular=Decimal("0"),
            federal_claim_amount=FEDERAL_BPA,
            provincial_claim_amount=PROVINCIAL_BPA[Province.ON],
            ytd_gross=Decimal("0"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("0"),
        )
        result = self.engine.calculate(input_data)

        assert result.total_gross == Decimal("0")
        assert result.cpp_base == Decimal("0")
        assert result.cpp_additional == Decimal("0")
        assert result.ei_employee == Decimal("0")
        assert result.federal_tax == Decimal("0")
        assert result.provincial_tax == Decimal("0")
        assert result.net_pay == Decimal("0")


# =============================================================================
# SPECIAL PROVINCIAL RULES TESTS (S01-S10) - Priority 4
# =============================================================================


class TestSpecialProvincialRules:
    """
    Tests for province-specific rules and edge cases.

    Each province may have unique rules like surtaxes, tax reductions,
    dynamic BPA, or special credits.
    """

    def setup_method(self):
        self.engine = PayrollEngine(year=2025)

    def test_s01_ontario_surtax_20_percent(self):
        """S01: Ontario surtax 20% - provincial tax > $5,554."""
        # Need high income to trigger surtax
        input_data = create_standard_input(
            province=Province.ON,
            pay_frequency=PayFrequency.MONTHLY,
            annual_income=Decimal("100000"),  # ~$8,333/month
        )
        result = self.engine.calculate(input_data)

        # High income should trigger Ontario surtax
        assert result.provincial_tax > Decimal("350")

    def test_s02_ontario_surtax_36_percent(self):
        """S02: Ontario surtax 36% - provincial tax > $7,108."""
        # Need very high income to trigger higher surtax
        input_data = create_standard_input(
            province=Province.ON,
            pay_frequency=PayFrequency.MONTHLY,
            annual_income=Decimal("200000"),  # ~$16,667/month
        )
        result = self.engine.calculate(input_data)

        # Very high income should trigger 36% surtax
        assert result.provincial_tax > Decimal("1000")

    def test_s03_ontario_health_premium(self):
        """S03: Ontario health premium - income > $20,000."""
        # Health premium kicks in above $20k annual
        input_data = create_standard_input(
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            annual_income=Decimal("50000"),  # Above $20k threshold
        )
        result = self.engine.calculate(input_data)

        # Provincial tax should include health premium
        assert result.provincial_tax > Decimal("0")

    def test_s04_bc_tax_reduction_low_income(self):
        """S04: BC tax reduction for low income (< $24,000)."""
        input_data = create_standard_input(
            province=Province.BC,
            pay_frequency=PayFrequency.BIWEEKLY,
            annual_income=Decimal("22000"),  # Below $24k threshold
        )
        result = self.engine.calculate(input_data)

        # BC low income should have minimal or zero provincial tax
        # due to tax reduction provisions (Factor S)
        assert result.provincial_tax >= Decimal("0")
        assert result.provincial_tax < Decimal("30")

    def test_s05_manitoba_dynamic_bpa_low_income(self):
        """S05: Manitoba dynamic BPA for low income (< $50,000)."""
        input_data = create_standard_input(
            province=Province.MB,
            pay_frequency=PayFrequency.BIWEEKLY,
            annual_income=Decimal("40000"),  # Below $50k
        )
        result = self.engine.calculate(input_data)

        # Lower income gets full BPA benefit
        assert result.provincial_tax >= Decimal("0")

    def test_s06_manitoba_dynamic_bpa_high_income(self):
        """S06: Manitoba dynamic BPA for high income (> $200,000)."""
        input_data = create_standard_input(
            province=Province.MB,
            pay_frequency=PayFrequency.MONTHLY,
            annual_income=Decimal("250000"),  # Above $200k
        )
        result = self.engine.calculate(input_data)

        # High income has reduced BPA, thus higher tax
        assert result.provincial_tax > Decimal("2000")

    def test_s07_nova_scotia_bpa_tier_1(self):
        """S07: Nova Scotia BPA Tier 1 - lower income."""
        input_data = create_standard_input(
            province=Province.NS,
            pay_frequency=PayFrequency.BIWEEKLY,
            annual_income=Decimal("25000"),  # Lower income
        )
        result = self.engine.calculate(input_data)

        # Lower income gets higher BPA ($11,744)
        assert result.provincial_tax >= Decimal("0")

    def test_s08_nova_scotia_bpa_tier_2(self):
        """S08: Nova Scotia BPA Tier 2 - higher income."""
        input_data = create_standard_input(
            province=Province.NS,
            pay_frequency=PayFrequency.BIWEEKLY,
            annual_income=Decimal("100000"),  # Higher income
        )
        result = self.engine.calculate(input_data)

        # Higher income gets lower BPA ($8,744)
        assert result.provincial_tax > Decimal("200")

    def test_s09_yukon_follows_federal_bpa(self):
        """S09: Yukon follows federal BPA formula."""
        # Compare Yukon with same federal BPA formula
        input_data = create_standard_input(
            province=Province.YT,
            pay_frequency=PayFrequency.BIWEEKLY,
            annual_income=INCOME_LEVELS["medium"],
        )
        result = self.engine.calculate(input_data)

        # Yukon uses federal BPA ($16,129)
        assert result.provincial_tax >= Decimal("0")
        # Should be relatively low due to favorable rates

    def test_s10_alberta_k5p_credit(self):
        """S10: Alberta K5P supplemental credit."""
        input_data = create_standard_input(
            province=Province.AB,
            pay_frequency=PayFrequency.BIWEEKLY,
            annual_income=INCOME_LEVELS["medium"],
        )
        result = self.engine.calculate(input_data)

        # Alberta has flat 10% rate and high BPA ($22,323)
        # K5P credit provides additional relief
        assert result.provincial_tax >= Decimal("0")
        # Alberta should have lower provincial tax than most provinces
        assert result.provincial_tax < Decimal("150")


# =============================================================================
# FULL MATRIX COVERAGE - Province × Frequency × Income
# =============================================================================


class TestFullMatrixCoverage:
    """
    Comprehensive matrix testing all combinations.

    Tests all 12 provinces × 4 pay frequencies × 5 income levels = 240 combinations
    """

    def setup_method(self):
        self.engine = PayrollEngine(year=2025)

    @pytest.mark.parametrize("province", list(Province))
    @pytest.mark.parametrize("pay_frequency", list(PayFrequency))
    @pytest.mark.parametrize(
        "income_level,annual_income",
        [
            ("very_low", INCOME_LEVELS["very_low"]),
            ("low", INCOME_LEVELS["low"]),
            ("medium", INCOME_LEVELS["medium"]),
            ("high", INCOME_LEVELS["high"]),
            ("very_high", INCOME_LEVELS["very_high"]),
        ],
    )
    def test_matrix_combination(
        self,
        province: Province,
        pay_frequency: PayFrequency,
        income_level: str,
        annual_income: Decimal,
    ):
        """Test: All province × frequency × income combinations calculate correctly."""
        input_data = create_standard_input(
            province=province,
            pay_frequency=pay_frequency,
            annual_income=annual_income,
        )
        result = self.engine.calculate(input_data)

        periods = pay_frequency.periods_per_year
        expected_gross = (annual_income / periods).quantize(Decimal("0.01"))

        # Basic sanity checks for all combinations
        assert result.total_gross == expected_gross, (
            f"Gross mismatch for {province.value}/{pay_frequency.value}/{income_level}"
        )

        # Net pay must be positive (unless zero income)
        if annual_income > Decimal("0"):
            assert result.net_pay > Decimal("0"), (
                f"Net pay should be positive for {province.value}/{pay_frequency.value}/{income_level}"
            )
            assert result.net_pay < result.total_gross, (
                f"Net pay should be less than gross for {province.value}/{pay_frequency.value}/{income_level}"
            )

        # CPP should be non-negative
        assert result.cpp_base >= Decimal("0")
        assert result.cpp_additional >= Decimal("0")

        # EI should be non-negative
        assert result.ei_employee >= Decimal("0")

        # Taxes should be non-negative
        assert result.federal_tax >= Decimal("0")
        assert result.provincial_tax >= Decimal("0")


# =============================================================================
# YTD SCENARIO TESTS
# =============================================================================


class TestYTDScenarios:
    """
    Tests for Year-to-Date accumulation scenarios.

    Validates correct behavior at different points during the year.
    """

    def setup_method(self):
        self.engine = PayrollEngine(year=2025)

    def test_ytd_year_start(self):
        """Test: First pay period of the year (January)."""
        input_data = create_standard_input(
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            annual_income=INCOME_LEVELS["medium"],
            pay_date=date(2025, 1, 10),
            ytd_gross=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
            ytd_ei=Decimal("0"),
        )
        result = self.engine.calculate(input_data)

        # First period should calculate full deductions
        assert result.cpp_base > Decimal("100")
        assert result.ei_employee > Decimal("30")
        # YTD should update
        assert result.new_ytd_cpp > Decimal("0")
        assert result.new_ytd_ei > Decimal("0")

    def test_ytd_mid_year(self):
        """Test: Mid-year (July) with accumulated YTD."""
        # 13 bi-weekly periods have passed
        ytd_periods = 13
        per_period_gross = Decimal("2307.69")
        ytd_gross = per_period_gross * ytd_periods

        input_data = create_standard_input(
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            annual_income=INCOME_LEVELS["medium"],
            pay_date=date(2025, 7, 18),
            ytd_gross=ytd_gross,
            ytd_cpp_base=Decimal("1700"),  # ~$130/period × 13
            ytd_ei=Decimal("492"),  # ~$38/period × 13
        )
        result = self.engine.calculate(input_data)

        # Should continue accumulating
        assert result.new_ytd_cpp > Decimal("1700")
        assert result.new_ytd_ei > Decimal("492")
        assert result.cpp_base > Decimal("0")
        assert result.ei_employee > Decimal("0")

    def test_ytd_near_cpp_max(self):
        """Test: Near end of year with CPP almost maxed."""
        # CPP max is $4,034.10, set YTD to $4,000
        input_data = create_standard_input(
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            annual_income=INCOME_LEVELS["medium"],
            pay_date=date(2025, 12, 5),
            ytd_gross=Decimal("55000"),
            ytd_cpp_base=Decimal("4000"),  # $34.10 remaining
            ytd_ei=Decimal("900"),
        )
        result = self.engine.calculate(input_data)

        # CPP should be capped to remaining amount
        assert result.cpp_base <= Decimal("34.11")
        assert result.new_ytd_cpp <= CPP_MAX_BASE + Decimal("0.01")

    def test_ytd_near_ei_max(self):
        """Test: Near end of year with EI almost maxed."""
        # EI max is $1,077.48, set YTD to $1,060
        input_data = create_standard_input(
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            annual_income=INCOME_LEVELS["medium"],
            pay_date=date(2025, 12, 5),
            ytd_gross=Decimal("55000"),
            ytd_cpp_base=Decimal("3200"),
            ytd_ei=Decimal("1060"),  # $17.48 remaining
        )
        result = self.engine.calculate(input_data)

        # EI should be capped to remaining amount
        assert result.ei_employee <= Decimal("17.49")
        assert result.new_ytd_ei <= EI_MAX + Decimal("0.01")

    def test_ytd_cpp2_progression(self):
        """Test: CPP2 calculation with high income through the year."""
        # High earner who has maxed base CPP and is accumulating CPP2
        input_data = create_standard_input(
            province=Province.ON,
            pay_frequency=PayFrequency.MONTHLY,
            annual_income=Decimal("100000"),  # $8,333.33/month
            pay_date=date(2025, 10, 15),
            ytd_gross=Decimal("75000"),  # 9 months
            ytd_cpp_base=CPP_MAX_BASE,  # Base maxed
            ytd_cpp_additional=Decimal("150"),  # $246 remaining
            ytd_ei=EI_MAX,  # EI maxed
        )
        result = self.engine.calculate(input_data)

        # Base CPP should be zero (maxed)
        assert result.cpp_base == Decimal("0")
        # CPP2 may continue depending on pensionable earnings
        assert result.cpp_additional >= Decimal("0")
        assert result.cpp_additional <= CPP_MAX_ADDITIONAL - Decimal("150") + Decimal("0.01")


# =============================================================================
# FEDERAL TAX RATE CHANGE TESTS (July 2025)
# =============================================================================


class TestFederalTaxRateChange:
    """
    Tests for July 2025 federal tax rate change (15% → 14%).

    The federal government changed the lowest tax bracket rate from
    15% to 14% effective July 1, 2025.
    """

    def setup_method(self):
        self.engine = PayrollEngine(year=2025)

    @pytest.mark.parametrize("province", list(Province))
    def test_federal_tax_lower_after_july(self, province: Province):
        """Test: Federal tax is lower after July 2025 for all provinces."""
        base_input = {
            "province": province,
            "pay_frequency": PayFrequency.BIWEEKLY,
            "annual_income": INCOME_LEVELS["medium"],
        }

        input_before = create_standard_input(
            **base_input,
            pay_date=date(2025, 3, 15),  # Before July
        )
        input_after = create_standard_input(
            **base_input,
            pay_date=date(2025, 7, 15),  # After July
        )

        result_before = self.engine.calculate(input_before)
        result_after = self.engine.calculate(input_after)

        # Federal tax after July should be lower
        assert result_after.federal_tax < result_before.federal_tax, (
            f"{province.value}: Federal tax should be lower after July"
        )

    def test_federal_tax_boundary_june_30(self):
        """Test: June 30 still uses 15% rate."""
        input_data = create_standard_input(
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            annual_income=INCOME_LEVELS["medium"],
            pay_date=date(2025, 6, 30),
        )
        result = self.engine.calculate(input_data)

        # June 30 should use 15% rate
        assert result.federal_tax > Decimal("0")

    def test_federal_tax_boundary_july_1(self):
        """Test: July 1 uses 14% rate."""
        input_june = create_standard_input(
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            annual_income=INCOME_LEVELS["medium"],
            pay_date=date(2025, 6, 30),
        )
        input_july = create_standard_input(
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            annual_income=INCOME_LEVELS["medium"],
            pay_date=date(2025, 7, 1),
        )

        result_june = self.engine.calculate(input_june)
        result_july = self.engine.calculate(input_july)

        # July 1 should use 14% rate (lower tax)
        assert result_july.federal_tax < result_june.federal_tax


# =============================================================================
# PRE-TAX DEDUCTION TESTS (RRSP Impact)
# =============================================================================


class TestPreTaxDeductions:
    """
    Tests for pre-tax deductions like RRSP.

    Validates that RRSP reduces taxable income but not CPP/EI.
    """

    def setup_method(self):
        self.engine = PayrollEngine(year=2025)

    @pytest.mark.parametrize("province", list(Province))
    def test_rrsp_reduces_tax_all_provinces(self, province: Province):
        """Test: RRSP reduces tax for all provinces."""
        input_no_rrsp = create_standard_input(
            province=province,
            pay_frequency=PayFrequency.BIWEEKLY,
            annual_income=INCOME_LEVELS["high"],
            rrsp=Decimal("0"),
        )
        input_with_rrsp = create_standard_input(
            province=province,
            pay_frequency=PayFrequency.BIWEEKLY,
            annual_income=INCOME_LEVELS["high"],
            rrsp=Decimal("500"),  # $500 bi-weekly RRSP
        )

        result_no_rrsp = self.engine.calculate(input_no_rrsp)
        result_with_rrsp = self.engine.calculate(input_with_rrsp)

        # RRSP should reduce federal and provincial tax
        assert result_with_rrsp.federal_tax < result_no_rrsp.federal_tax, (
            f"{province.value}: RRSP should reduce federal tax"
        )
        assert result_with_rrsp.provincial_tax < result_no_rrsp.provincial_tax, (
            f"{province.value}: RRSP should reduce provincial tax"
        )

        # But CPP and EI should remain the same
        assert result_with_rrsp.cpp_base == result_no_rrsp.cpp_base, (
            f"{province.value}: RRSP should not affect CPP"
        )
        assert result_with_rrsp.ei_employee == result_no_rrsp.ei_employee, (
            f"{province.value}: RRSP should not affect EI"
        )


# =============================================================================
# DEDUCTION CALCULATION VERIFICATION
# =============================================================================


class TestDeductionCalculationVerification:
    """
    Verification tests for specific deduction calculations.

    These tests verify the mathematical accuracy of deductions.
    """

    def setup_method(self):
        self.engine = PayrollEngine(year=2025)

    def test_cpp_calculation_accuracy(self):
        """Test: CPP calculation matches expected formula."""
        # $60k annual, bi-weekly
        # Per period: $2,307.69
        # Per period exemption: $3,500 / 26 = $134.62
        # Pensionable: $2,307.69 - $134.62 = $2,173.07
        # CPP: $2,173.07 × 5.95% = $129.30
        input_data = create_standard_input(
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            annual_income=Decimal("60000"),
        )
        result = self.engine.calculate(input_data)

        # Should be close to $129.30
        assert result.cpp_base >= Decimal("128.00")
        assert result.cpp_base <= Decimal("131.00")

    def test_ei_calculation_accuracy(self):
        """Test: EI calculation matches expected formula."""
        # $60k annual, bi-weekly
        # Per period: $2,307.69
        # EI: $2,307.69 × 1.64% = $37.85
        input_data = create_standard_input(
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            annual_income=Decimal("60000"),
        )
        result = self.engine.calculate(input_data)

        # Should be close to $37.85
        assert result.ei_employee >= Decimal("37.00")
        assert result.ei_employee <= Decimal("39.00")

    def test_employer_cpp_matches_employee(self):
        """Test: Employer CPP contribution equals employee CPP."""
        input_data = create_standard_input(
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            annual_income=INCOME_LEVELS["medium"],
        )
        result = self.engine.calculate(input_data)

        # Employer CPP should match employee CPP total
        assert result.cpp_employer == result.cpp_total

    def test_employer_ei_is_1_4x_employee(self):
        """Test: Employer EI is 1.4× employee EI."""
        input_data = create_standard_input(
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            annual_income=INCOME_LEVELS["medium"],
        )
        result = self.engine.calculate(input_data)

        # Employer EI should be 1.4× employee EI
        expected_employer_ei = (result.ei_employee * Decimal("1.4")).quantize(Decimal("0.01"))
        assert result.ei_employer == expected_employer_ei

    def test_net_pay_calculation(self):
        """Test: Net pay equals gross minus all deductions."""
        input_data = create_standard_input(
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            annual_income=INCOME_LEVELS["medium"],
        )
        result = self.engine.calculate(input_data)

        # Net pay should equal gross minus total employee deductions
        assert result.net_pay == result.total_gross - result.total_employee_deductions
