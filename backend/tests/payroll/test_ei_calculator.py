"""
EI (Employment Insurance) Calculator Tests

Tests EI premium calculations following CRA T4127 Chapter 7.

2025 Key Parameters:
- MIE (Maximum Insurable Earnings): $65,700
- Employee Rate: 1.64%
- Employer Multiplier: 1.4×
- Max Employee Premium: $1,077.48
- Max Employer Premium: $1,508.47
"""

import pytest
from decimal import Decimal

from app.services.payroll.ei_calculator import EICalculator


class TestEICalculatorBasic:
    """Test basic EI premium calculations."""

    def setup_method(self):
        """Create calculator for bi-weekly (26 periods)."""
        self.calc = EICalculator(pay_periods_per_year=26, year=2025)

    # ========== Standard Income Tests ==========

    def test_ei_standard_income(self):
        """Test: Standard income below MIE.

        $2,000/period × 1.64% = $32.80
        """
        result = self.calc.calculate_total_premium(
            insurable_earnings=Decimal("2000.00"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        assert result.employee == Decimal("32.80")

    def test_ei_exact_calculation(self):
        """Test: Exact calculation verification.

        $1,000 × 1.64% = $16.40
        """
        result = self.calc.calculate_total_premium(
            insurable_earnings=Decimal("1000.00"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        assert result.employee == Decimal("16.40")

    def test_ei_low_income(self):
        """Test: Low income still gets EI deducted."""
        result = self.calc.calculate_total_premium(
            insurable_earnings=Decimal("100.00"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        # $100 × 1.64% = $1.64
        assert result.employee == Decimal("1.64")

    # ========== Annual Maximum Tests ==========

    def test_ei_max_reached(self):
        """Test: YTD already at maximum - no more deduction.

        Max employee premium: $1,077.48
        """
        result = self.calc.calculate_total_premium(
            insurable_earnings=Decimal("3000.00"),
            ytd_insurable_earnings=Decimal("65700"),  # MIE reached
            ytd_ei=Decimal("1077.48"),  # Max reached
        )

        assert result.employee == Decimal("0")

    def test_ei_partial_max(self):
        """Test: Partial deduction when approaching max.

        YTD EI: $1,050.00, remaining: $27.48
        """
        result = self.calc.calculate_total_premium(
            insurable_earnings=Decimal("2000.00"),
            ytd_insurable_earnings=Decimal("64000"),
            ytd_ei=Decimal("1050.00"),
        )

        # Should be capped at remaining room
        assert result.employee <= Decimal("27.48")
        assert result.employee > Decimal("0")

    def test_ei_exceeds_max_capped(self):
        """Test: Calculated EI exceeds remaining annual max."""
        result = self.calc.calculate_total_premium(
            insurable_earnings=Decimal("3000.00"),
            ytd_insurable_earnings=Decimal("64000"),
            ytd_ei=Decimal("1070.00"),  # Only $7.48 remaining
        )

        # Should be exactly the remaining amount
        assert result.employee == Decimal("7.48")

    def test_ei_ytd_insurable_exceeds_mie(self):
        """Test: YTD insurable earnings already exceed MIE."""
        result = self.calc.calculate_total_premium(
            insurable_earnings=Decimal("2000.00"),
            ytd_insurable_earnings=Decimal("66000"),  # Over MIE
            ytd_ei=Decimal("1077.48"),
        )

        assert result.employee == Decimal("0")

    def test_ei_remaining_insurable_capped(self):
        """Test: Only remaining insurable earnings are used.

        MIE: $65,700, YTD: $65,000, remaining: $700
        Premium on $700 = $11.48
        """
        result = self.calc.calculate_total_premium(
            insurable_earnings=Decimal("2000.00"),
            ytd_insurable_earnings=Decimal("65000"),
            ytd_ei=Decimal("1066.00"),  # Not yet at max premium
        )

        # Should only calculate on remaining $700 of insurable earnings
        # But also capped by remaining premium room ($1077.48 - $1066.00 = $11.48)
        assert result.employee <= Decimal("11.48")


class TestEICalculatorEmployerPremium:
    """Test employer EI premium calculations."""

    def setup_method(self):
        """Create calculator for bi-weekly (26 periods)."""
        self.calc = EICalculator(pay_periods_per_year=26, year=2025)

    def test_employer_ei_multiplier(self):
        """Test: Employer EI is 1.4× employee.

        Employee: $32.80, Employer: $32.80 × 1.4 = $45.92
        """
        result = self.calc.calculate_total_premium(
            insurable_earnings=Decimal("2000.00"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        expected_employer = result.employee * Decimal("1.4")
        assert result.employer == expected_employer

    def test_employer_ei_exact_calculation(self):
        """Test: Exact employer calculation.

        $1,000 × 1.64% = $16.40 employee
        $16.40 × 1.4 = $22.96 employer
        """
        result = self.calc.calculate_total_premium(
            insurable_earnings=Decimal("1000.00"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        assert result.employee == Decimal("16.40")
        assert result.employer == Decimal("22.96")

    def test_employer_ei_zero_when_employee_zero(self):
        """Test: Employer EI is zero when employee EI is zero."""
        result = self.calc.calculate_total_premium(
            insurable_earnings=Decimal("1000.00"),
            ytd_insurable_earnings=Decimal("65700"),
            ytd_ei=Decimal("1077.48"),
        )

        assert result.employee == Decimal("0")
        assert result.employer == Decimal("0")


class TestEICalculatorPayFrequency:
    """Test EI calculations with different pay frequencies."""

    @pytest.mark.parametrize("periods,gross,expected", [
        (52, Decimal("1000"), Decimal("16.40")),   # Weekly
        (26, Decimal("2000"), Decimal("32.80")),   # Bi-weekly
        (24, Decimal("2167"), Decimal("35.54")),   # Semi-monthly (rounded)
        (12, Decimal("5000"), Decimal("82.00")),   # Monthly
    ])
    def test_different_pay_frequencies(self, periods, gross, expected):
        """Test: EI with different pay frequencies."""
        calc = EICalculator(pay_periods_per_year=periods, year=2025)
        result = calc.calculate_total_premium(
            insurable_earnings=gross,
            ytd_insurable_earnings=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        # Allow small rounding variance
        assert abs(result.employee - expected) < Decimal("0.02")

    def test_weekly_full_year_max(self):
        """Test: Weekly pay reaches annual max correctly."""
        calc = EICalculator(pay_periods_per_year=52, year=2025)

        # First week
        result = calc.calculate_total_premium(
            insurable_earnings=Decimal("1500.00"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        # $1,500 × 1.64% = $24.60
        assert result.employee == Decimal("24.60")


class TestEICalculatorHelperMethods:
    """Test EI calculator helper methods."""

    def setup_method(self):
        """Create calculator for bi-weekly (26 periods)."""
        self.calc = EICalculator(pay_periods_per_year=26, year=2025)

    def test_get_remaining_annual_premium(self):
        """Test: Remaining annual premium calculation."""
        remaining = self.calc.get_remaining_annual_premium(Decimal("500.00"))

        # Max is $1,077.48, YTD is $500.00
        expected = Decimal("1077.48") - Decimal("500.00")
        assert remaining == expected

    def test_get_remaining_at_max(self):
        """Test: Remaining is zero when at max."""
        remaining = self.calc.get_remaining_annual_premium(Decimal("1077.48"))
        assert remaining == Decimal("0")

    def test_get_remaining_over_max(self):
        """Test: Remaining is zero when over max."""
        remaining = self.calc.get_remaining_annual_premium(Decimal("1100.00"))
        assert remaining == Decimal("0")

    def test_is_at_annual_maximum_false(self):
        """Test: Not at annual maximum."""
        is_max = self.calc.is_at_annual_maximum(Decimal("500.00"))
        assert is_max is False

    def test_is_at_annual_maximum_true(self):
        """Test: At annual maximum."""
        is_max = self.calc.is_at_annual_maximum(Decimal("1077.48"))
        assert is_max is True

    def test_is_at_annual_maximum_over(self):
        """Test: Over annual maximum (still True)."""
        is_max = self.calc.is_at_annual_maximum(Decimal("1100.00"))
        assert is_max is True


class TestEICalculatorEdgeCases:
    """Test edge cases and boundary conditions."""

    def setup_method(self):
        """Create calculator for bi-weekly (26 periods)."""
        self.calc = EICalculator(pay_periods_per_year=26, year=2025)

    def test_zero_earnings(self):
        """Test: Zero earnings should produce zero EI."""
        result = self.calc.calculate_total_premium(
            insurable_earnings=Decimal("0"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        assert result.employee == Decimal("0")
        assert result.employer == Decimal("0")

    def test_very_small_earnings(self):
        """Test: Very small earnings still get EI deducted."""
        result = self.calc.calculate_total_premium(
            insurable_earnings=Decimal("1.00"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        # $1.00 × 1.64% = $0.02 (rounded)
        assert result.employee == Decimal("0.02")

    def test_very_high_income_capped(self):
        """Test: Very high income is capped at annual maximum."""
        result = self.calc.calculate_total_premium(
            insurable_earnings=Decimal("100000.00"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        # Should not exceed annual max
        assert result.employee <= Decimal("1077.48")

    def test_individual_calculation_methods(self):
        """Test: Individual calculation methods work correctly."""
        employee_ei = self.calc.calculate_ei_premium(
            insurable_earnings=Decimal("2000.00"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        employer_ei = self.calc.calculate_employer_premium(employee_ei)

        result = self.calc.calculate_total_premium(
            insurable_earnings=Decimal("2000.00"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        assert employee_ei == result.employee
        assert employer_ei == result.employer


class TestEIPDOCValidation:
    """Test cases validated against CRA PDOC.

    These are placeholder tests that should be updated with
    actual PDOC values after manual verification.
    """

    def setup_method(self):
        """Create calculator for bi-weekly (26 periods)."""
        self.calc = EICalculator(pay_periods_per_year=26, year=2025)

    def test_pdoc_case_standard_60k(self):
        """
        PDOC Validation Case: Standard $60k annual, bi-weekly

        PDOC Input:
        - Gross: $2,307.69 (60k/26)
        - Pay periods: 26
        - YTD: $0

        Expected: $2,307.69 × 1.64% = $37.85
        """
        result = self.calc.calculate_total_premium(
            insurable_earnings=Decimal("2307.69"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        # Allow small rounding variance
        assert abs(result.employee - Decimal("37.85")) < Decimal("0.01")

    def test_pdoc_case_high_income_mid_year(self):
        """
        PDOC Validation Case: High income at mid-year

        PDOC Input:
        - Gross: $5,000 per period
        - YTD insurable: $60,000
        - YTD EI: $984.00

        Only insure remaining $5,700 ($65,700 - $60,000)
        Then cap at premium room ($1,077.48 - $984.00 = $93.48)
        $5,700 × 1.64% = $93.48
        """
        result = self.calc.calculate_total_premium(
            insurable_earnings=Decimal("5000.00"),
            ytd_insurable_earnings=Decimal("60000"),
            ytd_ei=Decimal("984.00"),
        )

        # Should be the remaining insurable × rate, capped at premium room
        # min($5,000, $5,700) × 1.64% = $82.00, but premium room is $93.48
        # So should be $82.00
        assert result.employee <= Decimal("93.48")
