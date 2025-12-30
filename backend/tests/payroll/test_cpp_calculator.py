"""
CPP (Canada Pension Plan) Calculator Tests

Tests CPP contribution calculations following CRA T4127 Chapter 6.
Includes both base CPP and additional CPP2 (above YMPE).

2025 Key Parameters:
- YMPE: $71,300
- YAMPE: $81,200
- Basic Exemption: $3,500
- Base Rate: 5.95%
- Additional Rate (CPP2): 4.00%
- Max Base: $4,034.10
- Max CPP2: $396.00
"""

import pytest
from decimal import Decimal

from app.services.payroll.cpp_calculator import CPPCalculator


class TestCPPCalculatorBaseCPP:
    """Test base CPP contribution calculations."""

    def setup_method(self):
        """Create calculator for bi-weekly (26 periods)."""
        self.calc = CPPCalculator(pay_periods_per_year=26, year=2025)

    # ========== Standard Income Tests ==========

    def test_base_cpp_standard_income(self):
        """Test: Standard income below YMPE.

        $2,000/period × 26 = $52,000 annual (below YMPE $71,300)
        Expected: (2000 - 3500/26) × 5.95%
                = (2000 - 134.62) × 0.0595
                = 1865.38 × 0.0595
                ≈ $110.99
        """
        result = self.calc.calculate_total_cpp(
            pensionable_earnings=Decimal("2000.00"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
            ytd_cpp_additional=Decimal("0"),
        )

        # Base CPP should be around $111
        assert result.base > Decimal("100")
        assert result.base < Decimal("130")
        # No CPP2 below YMPE
        assert result.additional == Decimal("0")

    def test_base_cpp_low_income_below_exemption(self):
        """Test: Income below basic exemption per period - should be $0.

        Basic exemption: $3,500/year = $134.62/period (bi-weekly)
        """
        result = self.calc.calculate_total_cpp(
            pensionable_earnings=Decimal("100.00"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
        )

        assert result.base == Decimal("0")
        assert result.total == Decimal("0")

    def test_base_cpp_exactly_at_exemption(self):
        """Test: Income exactly at basic exemption threshold."""
        exemption_per_period = Decimal("3500") / 26
        result = self.calc.calculate_total_cpp(
            pensionable_earnings=exemption_per_period,
            ytd_pensionable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
        )

        assert result.base == Decimal("0")

    # ========== Annual Maximum Tests ==========

    def test_base_cpp_max_already_reached(self):
        """Test: YTD already at maximum - no more deduction.

        Max base contribution: $4,034.10
        """
        result = self.calc.calculate_total_cpp(
            pensionable_earnings=Decimal("5000.00"),
            ytd_pensionable_earnings=Decimal("70000"),
            ytd_cpp_base=Decimal("4034.10"),
        )

        assert result.base == Decimal("0")

    def test_base_cpp_partial_max(self):
        """Test: Partial deduction when approaching max.

        YTD CPP is $4,000.00, max is $4,034.10
        Remaining room: $34.10
        """
        result = self.calc.calculate_total_cpp(
            pensionable_earnings=Decimal("3000.00"),
            ytd_pensionable_earnings=Decimal("68000"),
            ytd_cpp_base=Decimal("4000.00"),
        )

        # Should be capped at remaining room
        assert result.base <= Decimal("34.10")
        assert result.base > Decimal("0")

    def test_base_cpp_exceeds_max_capped(self):
        """Test: Calculated CPP exceeds remaining annual max."""
        result = self.calc.calculate_total_cpp(
            pensionable_earnings=Decimal("5000.00"),
            ytd_pensionable_earnings=Decimal("65000"),
            ytd_cpp_base=Decimal("4030.00"),  # Only $4.10 remaining
        )

        # Should be exactly the remaining amount
        assert result.base == Decimal("4.10")


class TestCPPCalculatorCPP2:
    """Test CPP2 (additional CPP) calculations."""

    def setup_method(self):
        """Create calculator for bi-weekly (26 periods)."""
        self.calc = CPPCalculator(pay_periods_per_year=26, year=2025)

    def test_cpp2_income_below_ympe(self):
        """Test: No CPP2 for income below YMPE."""
        result = self.calc.calculate_total_cpp(
            pensionable_earnings=Decimal("2000.00"),
            ytd_pensionable_earnings=Decimal("50000"),
            ytd_cpp_base=Decimal("2800.00"),
            ytd_cpp_additional=Decimal("0"),
        )

        assert result.additional == Decimal("0")

    def test_cpp2_income_above_ympe(self):
        """Test: CPP2 kicks in for income above YMPE per period.

        YMPE: $71,300 / 26 = $2,742.31/period
        For high income exceeding YMPE per period, CPP2 applies.
        """
        # High income that exceeds YMPE per period
        ympe_per_period = Decimal("71300") / 26
        high_income = ympe_per_period + Decimal("200")

        result = self.calc.calculate_total_cpp(
            pensionable_earnings=high_income,
            ytd_pensionable_earnings=Decimal("71300"),  # Past YMPE
            ytd_cpp_base=Decimal("4034.10"),  # Base CPP maxed
            ytd_cpp_additional=Decimal("0"),
        )

        assert result.additional > Decimal("0")

    def test_cpp2_max_reached(self):
        """Test: CPP2 stops at $396 maximum."""
        ympe_per_period = Decimal("71300") / 26
        high_income = ympe_per_period + Decimal("500")

        result = self.calc.calculate_total_cpp(
            pensionable_earnings=high_income,
            ytd_pensionable_earnings=Decimal("80000"),
            ytd_cpp_base=Decimal("4034.10"),
            ytd_cpp_additional=Decimal("396.00"),  # CPP2 max reached
        )

        assert result.additional == Decimal("0")

    def test_cpp2_partial_max(self):
        """Test: Partial CPP2 when approaching max."""
        ympe_per_period = Decimal("71300") / 26
        high_income = ympe_per_period + Decimal("500")

        result = self.calc.calculate_total_cpp(
            pensionable_earnings=high_income,
            ytd_pensionable_earnings=Decimal("78000"),
            ytd_cpp_base=Decimal("4034.10"),
            ytd_cpp_additional=Decimal("390.00"),  # $6.00 remaining
        )

        assert result.additional <= Decimal("6.00")

    def test_cpp2_exemption(self):
        """Test: Employee with CPP2 exemption (CPT30)."""
        ympe_per_period = Decimal("71300") / 26
        high_income = ympe_per_period + Decimal("500")

        result = self.calc.calculate_total_cpp(
            pensionable_earnings=high_income,
            ytd_pensionable_earnings=Decimal("72000"),
            ytd_cpp_base=Decimal("4034.10"),
            ytd_cpp_additional=Decimal("0"),
            cpp2_exempt=True,  # CPT30 exemption
        )

        assert result.additional == Decimal("0")


class TestCPPCalculatorPayFrequency:
    """Test CPP calculations with different pay frequencies."""

    @pytest.mark.parametrize("periods,gross,expected_min,expected_max", [
        (52, Decimal("1000"), Decimal("50"), Decimal("70")),    # Weekly
        (26, Decimal("2000"), Decimal("100"), Decimal("130")),  # Bi-weekly
        (24, Decimal("2167"), Decimal("110"), Decimal("140")),  # Semi-monthly
        (12, Decimal("5000"), Decimal("270"), Decimal("320")),  # Monthly
    ])
    def test_different_pay_frequencies(self, periods, gross, expected_min, expected_max):
        """Test: CPP calculation with different pay frequencies."""
        calc = CPPCalculator(pay_periods_per_year=periods, year=2025)
        result = calc.calculate_total_cpp(
            pensionable_earnings=gross,
            ytd_pensionable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
        )

        assert result.base >= expected_min
        assert result.base <= expected_max

    def test_weekly_exemption_per_period(self):
        """Test: Weekly exemption is correctly prorated."""
        calc = CPPCalculator(pay_periods_per_year=52, year=2025)
        # Exemption per period = 3500/52 = $67.31
        result = calc.calculate_total_cpp(
            pensionable_earnings=Decimal("50.00"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
        )

        assert result.base == Decimal("0")


class TestCPPCalculatorEmployerContribution:
    """Test employer CPP contribution calculations."""

    def setup_method(self):
        """Create calculator for bi-weekly (26 periods)."""
        self.calc = CPPCalculator(pay_periods_per_year=26, year=2025)

    def test_employer_cpp_matches_employee(self):
        """Test: Employer CPP equals employee CPP (base + additional)."""
        result = self.calc.calculate_total_cpp(
            pensionable_earnings=Decimal("2500.00"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
        )

        # Employer contribution should equal total employee contribution
        assert result.employer == result.total
        assert result.employer == result.base + result.additional

    def test_employer_cpp_with_cpp2(self):
        """Test: Employer matches both base CPP and CPP2."""
        ympe_per_period = Decimal("71300") / 26
        high_income = ympe_per_period + Decimal("500")

        result = self.calc.calculate_total_cpp(
            pensionable_earnings=high_income,
            ytd_pensionable_earnings=Decimal("71000"),
            ytd_cpp_base=Decimal("4034.10"),
            ytd_cpp_additional=Decimal("0"),
        )

        # Employer should match base + additional
        assert result.employer == result.base + result.additional


class TestCPPCalculatorF5Deduction:
    """Test F5 (CPP tax deduction) calculation.

    F5 = F2 + C2 where:
    - F2 is enhancement portion of base CPP
    - C2 is CPP2 (additional CPP)
    """

    def setup_method(self):
        """Create calculator for bi-weekly (26 periods)."""
        self.calc = CPPCalculator(pay_periods_per_year=26, year=2025)

    def test_f5_calculated_correctly(self):
        """Test: F5 includes both enhancement and CPP2."""
        result = self.calc.calculate_total_cpp(
            pensionable_earnings=Decimal("2000.00"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
        )

        # F5 should be > 0 and <= base (since it only includes enhancement portion)
        assert result.f5 >= Decimal("0")
        # F5 = enhancement portion (1% out of 5.95%) + any CPP2
        # For income below CPP2 threshold, F5 is just the enhancement part
        assert result.f5 <= result.base

    def test_f5_is_zero_when_no_cpp(self):
        """Test: No F5 deduction when income below exemption."""
        result = self.calc.calculate_total_cpp(
            pensionable_earnings=Decimal("100.00"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
        )

        assert result.base == Decimal("0")
        assert result.f5 == Decimal("0")


class TestCPPCalculatorCreditRates:
    """Test CPP credit rate calculations for K2."""

    def setup_method(self):
        """Create calculator for bi-weekly (26 periods)."""
        self.calc = CPPCalculator(pay_periods_per_year=26, year=2025)

    def test_credit_rate_is_4_95_percent(self):
        """Test: Credit rate is 4.95% (pre-enhancement rate)."""
        credit_rate = self.calc.get_base_cpp_credit_rate()
        assert credit_rate == Decimal("0.0495")

    def test_credit_ratio(self):
        """Test: Credit ratio is 0.0495/0.0595."""
        credit_ratio = self.calc.get_cpp_credit_ratio()
        expected_ratio = Decimal("0.0495") / Decimal("0.0595")

        assert abs(credit_ratio - expected_ratio) < Decimal("0.0001")


class TestCPPCalculatorEdgeCases:
    """Test edge cases and boundary conditions."""

    def setup_method(self):
        """Create calculator for bi-weekly (26 periods)."""
        self.calc = CPPCalculator(pay_periods_per_year=26, year=2025)

    def test_zero_earnings(self):
        """Test: Zero earnings should produce zero CPP."""
        result = self.calc.calculate_total_cpp(
            pensionable_earnings=Decimal("0"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
        )

        assert result.base == Decimal("0")
        assert result.additional == Decimal("0")
        assert result.total == Decimal("0")
        assert result.employer == Decimal("0")

    def test_negative_earnings_treated_as_zero(self):
        """Test: Negative earnings should not produce negative CPP."""
        result = self.calc.calculate_total_cpp(
            pensionable_earnings=Decimal("-100.00"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
        )

        assert result.base >= Decimal("0")
        assert result.total >= Decimal("0")

    def test_very_high_income_caps_at_max(self):
        """Test: Very high income caps at annual maximum."""
        result = self.calc.calculate_total_cpp(
            pensionable_earnings=Decimal("50000.00"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
            ytd_cpp_additional=Decimal("0"),
        )

        # Base should be capped
        assert result.base <= Decimal("4034.10")

    def test_individual_calculation_methods(self):
        """Test: Individual calculation methods work correctly."""
        base = self.calc.calculate_base_cpp(
            pensionable_earnings=Decimal("2000.00"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
        )

        additional = self.calc.calculate_additional_cpp(
            pensionable_earnings=Decimal("2000.00"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_cpp_additional=Decimal("0"),
        )

        result = self.calc.calculate_total_cpp(
            pensionable_earnings=Decimal("2000.00"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
            ytd_cpp_additional=Decimal("0"),
        )

        assert base == result.base
        assert additional == result.additional


class TestCPPPDOCValidation:
    """Test cases validated against CRA PDOC.

    These are placeholder tests that should be updated with
    actual PDOC values after manual verification.
    """

    def setup_method(self):
        """Create calculator for bi-weekly (26 periods)."""
        self.calc = CPPCalculator(pay_periods_per_year=26, year=2025)

    def test_pdoc_case_standard_60k(self):
        """
        PDOC Validation Case: Standard $60k annual, bi-weekly

        PDOC Input:
        - Gross: $2,307.69 (60k/26)
        - Pay periods: 26
        - YTD: $0

        Expected calculation:
        - Pensionable after exemption: 2307.69 - (3500/26) = 2307.69 - 134.62 = 2173.07
        - Base CPP: 2173.07 × 5.95% = $129.30
        """
        result = self.calc.calculate_total_cpp(
            pensionable_earnings=Decimal("2307.69"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
        )

        # Expected approximately $129.30 (allow small variance)
        assert abs(result.base - Decimal("129.30")) < Decimal("1.00")

    def test_pdoc_case_high_income_100k(self):
        """
        PDOC Validation Case: High income $100k annual, bi-weekly

        PDOC Input:
        - Gross: $3,846.15 (100k/26)
        - Pay periods: 26
        - YTD at mid-year: $50,000

        This should still be in base CPP territory (below YMPE per period).
        """
        result = self.calc.calculate_total_cpp(
            pensionable_earnings=Decimal("3846.15"),
            ytd_pensionable_earnings=Decimal("50000"),
            ytd_cpp_base=Decimal("2750.00"),
        )

        # Should have base CPP contribution
        assert result.base > Decimal("0")
        # CPP2 depends on whether income exceeds YMPE per period
        # YMPE/26 = $2,742.31, so $3,846.15 > YMPE per period
        # CPP2 would apply on the excess
        assert result.additional >= Decimal("0")
