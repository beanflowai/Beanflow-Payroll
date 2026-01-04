"""
Essential Tests (E01-E12) for PayrollEngine.

These tests cover the most common and critical payroll scenarios
as defined in the test matrix document.

Phase 4 - Test Matrix Implementation - Essential Scenarios
"""

from decimal import Decimal

from app.models.payroll import PayFrequency, Province
from app.services.payroll.payroll_engine import PayrollEngine

from .conftest import (
    CPP_MAX_BASE,
    EI_MAX,
    INCOME_LEVELS,
    create_standard_input,
)


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
