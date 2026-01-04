"""
YTD Scenario Tests for PayrollEngine.

Tests for Year-to-Date accumulation scenarios.
Validates correct behavior at different points during the year.

Phase 4 - Test Matrix Implementation - YTD Scenarios
"""

from datetime import date
from decimal import Decimal

from app.models.payroll import PayFrequency, Province
from app.services.payroll.payroll_engine import PayrollEngine

from .conftest import (
    CPP_MAX_ADDITIONAL,
    CPP_MAX_BASE,
    EI_MAX,
    INCOME_LEVELS,
    create_standard_input,
)


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
