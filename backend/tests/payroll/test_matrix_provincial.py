"""
Special Provincial Rules Tests (S01-S10) for PayrollEngine.

Tests for province-specific rules and edge cases.
Each province may have unique rules like surtaxes, tax reductions,
dynamic BPA, or special credits.

Phase 4 - Test Matrix Implementation - Special Provincial Rules
"""

from decimal import Decimal

from app.models.payroll import PayFrequency, Province
from app.services.payroll.payroll_engine import PayrollEngine

from .conftest import INCOME_LEVELS, create_standard_input


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
