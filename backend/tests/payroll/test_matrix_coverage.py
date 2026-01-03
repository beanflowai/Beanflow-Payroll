"""
Full Matrix Coverage Tests for PayrollEngine.

Tests all 12 provinces × 4 pay frequencies × 5 income levels = 240 combinations.

Phase 4 - Test Matrix Implementation - Full Matrix Coverage
"""

from decimal import Decimal

import pytest

from app.models.payroll import PayFrequency, Province
from app.services.payroll.payroll_engine import PayrollEngine

from .conftest import INCOME_LEVELS, create_standard_input


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
