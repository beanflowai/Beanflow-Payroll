"""
Edge cases and boundary condition tests for PayrollEngine.

Tests boundary conditions including:
- CPP at YMPE and YAMPE boundaries
- EI at MIE boundary
- Zero and minimal income
- Very high income
- Mid-year scenarios

Phase 2 - Integration Testing
"""

import pytest
from decimal import Decimal
from datetime import date

from app.services.payroll.payroll_engine import PayrollEngine, EmployeePayrollInput
from app.models.payroll import Province, PayFrequency


# 2025 Constants
CPP_YMPE = Decimal("71300.00")  # Year's Maximum Pensionable Earnings
CPP_YAMPE = Decimal("81200.00")  # Year's Additional Maximum Pensionable Earnings
CPP_BASIC_EXEMPTION = Decimal("3500.00")
CPP_MAX_BASE = Decimal("4034.10")  # Max base CPP contribution
CPP_MAX_ADDITIONAL = Decimal("396.00")  # Max CPP2 contribution
EI_MIE = Decimal("65700.00")  # Maximum Insurable Earnings
EI_MAX = Decimal("1077.48")  # Max EI contribution


class TestCPPBoundaryConditions:
    """Test CPP boundary conditions."""

    def setup_method(self):
        self.engine = PayrollEngine(year=2025)

    def test_cpp_at_ympe_boundary(self):
        """Test: Income exactly at YMPE boundary ($71,300)."""
        # YTD just below YMPE
        ytd_pensionable = Decimal("68557.69")  # 25 periods of ~$2742.31
        input_data = EmployeePayrollInput(
            employee_id="emp_ympe",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 12, 19),  # 26th period
            gross_regular=Decimal("2742.31"),  # $71,300 / 26
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            ytd_gross=ytd_pensionable,
            ytd_pensionable_earnings=ytd_pensionable,
            ytd_insurable_earnings=ytd_pensionable,
            ytd_cpp_base=Decimal("3879.00"),  # Base CPP almost at max
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("1000.00"),
        )

        result = self.engine.calculate(input_data)

        # Should have base CPP (remaining to max)
        assert result.cpp_base >= Decimal("0")
        # Total YTD should not exceed max
        assert result.new_ytd_cpp <= CPP_MAX_BASE + CPP_MAX_ADDITIONAL + Decimal("1")

    def test_cpp2_at_yampe_boundary(self):
        """Test: Income exactly at YAMPE boundary ($81,200)."""
        input_data = EmployeePayrollInput(
            employee_id="emp_yampe",
            province=Province.ON,
            pay_frequency=PayFrequency.MONTHLY,
            pay_date=date(2025, 12, 15),  # 12th period
            gross_regular=Decimal("6766.67"),  # $81,200 / 12
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            ytd_gross=Decimal("74433.33"),  # 11 months done
            ytd_pensionable_earnings=Decimal("74433.33"),
            ytd_insurable_earnings=Decimal("60091.67"),  # EI almost maxed
            ytd_cpp_base=Decimal("4034.10"),  # Base maxed
            ytd_cpp_additional=Decimal("360.00"),  # CPP2 almost maxed ($36 remaining)
            ytd_ei=Decimal("985.50"),
        )

        result = self.engine.calculate(input_data)

        # CPP2 should be partial (remaining to max)
        assert result.cpp_additional <= Decimal("36.00") + Decimal("0.01")
        assert result.cpp_base == Decimal("0")  # Base already maxed

    def test_cpp_partial_contribution_near_max(self):
        """Test: CPP contribution is partial when near annual max."""
        # YTD CPP just $50 below max
        input_data = EmployeePayrollInput(
            employee_id="emp_cpp_partial",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 11, 28),
            gross_regular=Decimal("3000.00"),
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            ytd_gross=Decimal("65000.00"),
            ytd_pensionable_earnings=Decimal("65000.00"),
            ytd_insurable_earnings=Decimal("65000.00"),
            ytd_cpp_base=Decimal("3984.10"),  # $50 below max
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("900.00"),
        )

        result = self.engine.calculate(input_data)

        # CPP should be exactly the remaining amount to max
        assert result.cpp_base == Decimal("50.00")

    def test_cpp_below_basic_exemption(self):
        """Test: No CPP when earnings below basic exemption per period."""
        # Basic exemption per period for biweekly: $3500 / 26 = $134.62
        input_data = EmployeePayrollInput(
            employee_id="emp_cpp_exempt",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            gross_regular=Decimal("130.00"),  # Below exemption
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            ytd_gross=Decimal("0"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result = self.engine.calculate(input_data)

        # No CPP contribution when below exemption
        assert result.cpp_base == Decimal("0")
        assert result.cpp_additional == Decimal("0")


class TestEIBoundaryConditions:
    """Test EI boundary conditions."""

    def setup_method(self):
        self.engine = PayrollEngine(year=2025)

    def test_ei_at_mie_boundary(self):
        """Test: Income exactly at MIE boundary ($65,700)."""
        input_data = EmployeePayrollInput(
            employee_id="emp_mie",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 12, 19),  # 26th period
            gross_regular=Decimal("2526.92"),  # $65,700 / 26
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            ytd_gross=Decimal("63173.08"),  # 25 periods
            ytd_pensionable_earnings=Decimal("63173.08"),
            ytd_insurable_earnings=Decimal("63173.08"),
            ytd_cpp_base=Decimal("3500.00"),
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("1036.04"),  # ~$41.44 remaining to max
        )

        result = self.engine.calculate(input_data)

        # EI should be partial (remaining to max)
        remaining_ei = EI_MAX - Decimal("1036.04")
        assert result.ei_employee <= remaining_ei + Decimal("0.01")

    def test_ei_partial_contribution_near_max(self):
        """Test: EI contribution is partial when near annual max."""
        # YTD EI just $20 below max
        input_data = EmployeePayrollInput(
            employee_id="emp_ei_partial",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 11, 28),
            gross_regular=Decimal("3000.00"),
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            ytd_gross=Decimal("60000.00"),
            ytd_pensionable_earnings=Decimal("60000.00"),
            ytd_insurable_earnings=Decimal("64000.00"),
            ytd_cpp_base=Decimal("3500.00"),
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("1057.48"),  # $20 below max
        )

        result = self.engine.calculate(input_data)

        # EI should be exactly the remaining amount to max
        assert result.ei_employee == Decimal("20.00")


class TestZeroAndMinimalIncome:
    """Test zero and minimal income scenarios."""

    def setup_method(self):
        self.engine = PayrollEngine(year=2025)

    def test_zero_income(self):
        """Test: Zero gross pay produces zero deductions."""
        input_data = EmployeePayrollInput(
            employee_id="emp_zero",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            gross_regular=Decimal("0"),
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
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

    def test_very_low_income_below_cpp_exemption(self):
        """Test: Income below CPP exemption has no CPP but may have EI."""
        input_data = EmployeePayrollInput(
            employee_id="emp_low",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            gross_regular=Decimal("100.00"),  # Below CPP exemption
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            ytd_gross=Decimal("0"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result = self.engine.calculate(input_data)

        # CPP should be zero (below exemption)
        assert result.cpp_base == Decimal("0")

        # EI still applies: $100 × 1.64% = $1.64
        assert result.ei_employee == Decimal("1.64")

        # Tax likely zero (income too low)
        assert result.federal_tax >= Decimal("0")

    def test_minimal_income_just_above_cpp_exemption(self):
        """Test: Income just above CPP exemption per period."""
        # Exemption per period for biweekly: $3500 / 26 = $134.62
        input_data = EmployeePayrollInput(
            employee_id="emp_minimal",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            gross_regular=Decimal("150.00"),  # Just above exemption
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            ytd_gross=Decimal("0"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result = self.engine.calculate(input_data)

        # CPP should be calculated on amount above exemption
        # ($150 - $134.62) × 5.95% = $0.92
        assert result.cpp_base > Decimal("0")
        assert result.cpp_base < Decimal("2")


class TestVeryHighIncome:
    """Test very high income scenarios."""

    def setup_method(self):
        self.engine = PayrollEngine(year=2025)

    def test_very_high_income_500k(self):
        """Test: Very high income ($500k annual)."""
        input_data = EmployeePayrollInput(
            employee_id="emp_executive",
            province=Province.ON,
            pay_frequency=PayFrequency.MONTHLY,
            pay_date=date(2025, 7, 18),
            gross_regular=Decimal("41666.67"),  # $500k annual
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            ytd_gross=Decimal("0"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result = self.engine.calculate(input_data)

        # Should be in highest tax brackets
        assert result.federal_tax > Decimal("10000")
        assert result.provincial_tax > Decimal("4000")
        assert result.net_pay > Decimal("0")

    def test_millionaire_income(self):
        """Test: Millionaire income ($1M annual)."""
        input_data = EmployeePayrollInput(
            employee_id="emp_millionaire",
            province=Province.ON,
            pay_frequency=PayFrequency.MONTHLY,
            pay_date=date(2025, 7, 18),
            gross_regular=Decimal("83333.33"),  # $1M annual
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            ytd_gross=Decimal("0"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result = self.engine.calculate(input_data)

        # Very high taxes in top brackets
        assert result.federal_tax > Decimal("20000")
        assert result.provincial_tax > Decimal("8000")

        # CPP maxes out quickly, but first month still has contributions
        assert result.cpp_base > Decimal("0")
        assert result.ei_employee > Decimal("0")


class TestMidYearScenarios:
    """Test mid-year employment scenarios."""

    def setup_method(self):
        self.engine = PayrollEngine(year=2025)

    def test_new_employee_mid_year(self):
        """Test: New employee starting mid-year with zero YTD."""
        input_data = EmployeePayrollInput(
            employee_id="emp_new",
            province=Province.BC,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 9, 15),
            gross_regular=Decimal("3000.00"),
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12932.00"),
            ytd_gross=Decimal("0"),  # First pay
            ytd_pensionable_earnings=Decimal("0"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result = self.engine.calculate(input_data)

        # Should calculate normally
        assert result.cpp_base > Decimal("0")
        assert result.ei_employee > Decimal("0")
        assert result.federal_tax > Decimal("0")

    def test_employee_with_prior_employer_ytd(self):
        """Test: Employee with YTD from prior employer."""
        input_data = EmployeePayrollInput(
            employee_id="emp_transfer",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            gross_regular=Decimal("2500.00"),
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            # YTD from prior employer
            ytd_gross=Decimal("40000.00"),
            ytd_pensionable_earnings=Decimal("40000.00"),
            ytd_insurable_earnings=Decimal("40000.00"),
            ytd_cpp_base=Decimal("2200.00"),
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("656.00"),
        )

        result = self.engine.calculate(input_data)

        # Should continue from YTD position
        new_ytd_cpp = Decimal("2200.00") + result.cpp_base + result.cpp_additional
        assert result.new_ytd_cpp == new_ytd_cpp

    def test_employee_maxed_at_prior_employer(self):
        """Test: Employee already maxed CPP/EI at prior employer."""
        input_data = EmployeePayrollInput(
            employee_id="emp_maxed",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 8, 15),
            gross_regular=Decimal("3000.00"),
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            # Already maxed at prior employer
            ytd_gross=Decimal("85000.00"),
            ytd_pensionable_earnings=Decimal("85000.00"),
            ytd_insurable_earnings=Decimal("70000.00"),
            ytd_cpp_base=Decimal("4034.10"),
            ytd_cpp_additional=Decimal("396.00"),
            ytd_ei=Decimal("1077.48"),
        )

        result = self.engine.calculate(input_data)

        # No additional CPP/EI deductions
        assert result.cpp_base == Decimal("0")
        assert result.cpp_additional == Decimal("0")
        assert result.ei_employee == Decimal("0")

        # But taxes still apply
        assert result.federal_tax > Decimal("0")
        assert result.provincial_tax > Decimal("0")


class TestLargeDeductions:
    """Test scenarios with large pre-tax deductions."""

    def setup_method(self):
        self.engine = PayrollEngine(year=2025)

    def test_large_rrsp_deduction(self):
        """Test: Large RRSP deduction (40% of gross)."""
        input_data = EmployeePayrollInput(
            employee_id="emp_rrsp",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            gross_regular=Decimal("5000.00"),
            rrsp_per_period=Decimal("2000.00"),  # 40% RRSP
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            ytd_gross=Decimal("0"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result = self.engine.calculate(input_data)

        # Tax should be significantly lower due to RRSP
        # But CPP/EI based on full gross
        assert result.cpp_base > Decimal("250")
        assert result.rrsp == Decimal("2000.00")

    def test_combined_rrsp_and_union_dues(self):
        """Test: Combined RRSP and union dues deductions."""
        input_data = EmployeePayrollInput(
            employee_id="emp_combined",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            gross_regular=Decimal("4000.00"),
            rrsp_per_period=Decimal("500.00"),
            union_dues_per_period=Decimal("100.00"),
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            ytd_gross=Decimal("0"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result = self.engine.calculate(input_data)

        # Both deductions should reduce taxable income
        assert result.rrsp == Decimal("500.00")
        assert result.union_dues == Decimal("100.00")

        # Net pay should reflect all deductions
        total_deductions = (
            result.cpp_total
            + result.ei_employee
            + result.federal_tax
            + result.provincial_tax
            + result.rrsp
            + result.union_dues
        )
        assert result.net_pay == result.total_gross - result.total_employee_deductions


class TestSpecialEarningsTypes:
    """Test various earnings types."""

    def setup_method(self):
        self.engine = PayrollEngine(year=2025)

    def test_holiday_pay(self):
        """Test: Holiday pay included in calculations."""
        input_data = EmployeePayrollInput(
            employee_id="emp_holiday",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            gross_regular=Decimal("2000.00"),
            holiday_pay=Decimal("200.00"),  # Stat holiday pay
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            ytd_gross=Decimal("0"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result = self.engine.calculate(input_data)

        # Total gross includes holiday pay
        assert result.total_gross == Decimal("2200.00")
        assert result.holiday_pay == Decimal("200.00")

    def test_vacation_pay(self):
        """Test: Vacation pay included in calculations."""
        input_data = EmployeePayrollInput(
            employee_id="emp_vacation",
            province=Province.BC,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            gross_regular=Decimal("2000.00"),
            vacation_pay=Decimal("80.00"),  # 4% vacation accrual
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12932.00"),
            ytd_gross=Decimal("0"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result = self.engine.calculate(input_data)

        # Total gross includes vacation pay
        assert result.total_gross == Decimal("2080.00")
        assert result.vacation_pay == Decimal("80.00")

    def test_all_earnings_types_combined(self):
        """Test: All earnings types combined."""
        input_data = EmployeePayrollInput(
            employee_id="emp_all_earnings",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            gross_regular=Decimal("2000.00"),
            gross_overtime=Decimal("300.00"),
            holiday_pay=Decimal("200.00"),
            holiday_premium_pay=Decimal("100.00"),
            vacation_pay=Decimal("80.00"),
            other_earnings=Decimal("50.00"),  # Bonus
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            ytd_gross=Decimal("0"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result = self.engine.calculate(input_data)

        # Total gross includes all earnings
        expected_gross = (
            Decimal("2000.00")  # regular
            + Decimal("300.00")  # overtime
            + Decimal("200.00")  # holiday
            + Decimal("100.00")  # holiday premium
            + Decimal("80.00")  # vacation
            + Decimal("50.00")  # other
        )
        assert result.total_gross == expected_gross


class TestPostTaxDeductions:
    """Test post-tax deductions."""

    def setup_method(self):
        self.engine = PayrollEngine(year=2025)

    def test_garnishments(self):
        """Test: Garnishments reduce net pay but not taxes."""
        input_no_garnish = EmployeePayrollInput(
            employee_id="emp_no_garnish",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            gross_regular=Decimal("2500.00"),
            garnishments=Decimal("0"),
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            ytd_gross=Decimal("0"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        input_with_garnish = EmployeePayrollInput(
            employee_id="emp_garnish",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            gross_regular=Decimal("2500.00"),
            garnishments=Decimal("300.00"),  # Court-ordered garnishment
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            ytd_gross=Decimal("0"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result_no_garnish = self.engine.calculate(input_no_garnish)
        result_with_garnish = self.engine.calculate(input_with_garnish)

        # Taxes should be the same (garnishments don't reduce taxable income)
        assert result_with_garnish.federal_tax == result_no_garnish.federal_tax
        assert result_with_garnish.provincial_tax == result_no_garnish.provincial_tax

        # Net pay should be reduced by garnishment
        expected_net_diff = result_no_garnish.net_pay - result_with_garnish.net_pay
        assert expected_net_diff == Decimal("300.00")

    def test_other_deductions(self):
        """Test: Other post-tax deductions."""
        input_data = EmployeePayrollInput(
            employee_id="emp_other_ded",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            gross_regular=Decimal("2500.00"),
            other_deductions=Decimal("50.00"),  # e.g., parking
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            ytd_gross=Decimal("0"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result = self.engine.calculate(input_data)

        assert result.other_deductions == Decimal("50.00")
        # Included in total employee deductions
        assert result.total_employee_deductions >= Decimal("50.00")


class TestRoundingAndPrecision:
    """Test rounding and decimal precision."""

    def setup_method(self):
        self.engine = PayrollEngine(year=2025)

    def test_results_rounded_to_cents(self):
        """Test: All monetary results are rounded to 2 decimal places."""
        input_data = EmployeePayrollInput(
            employee_id="emp_rounding",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            gross_regular=Decimal("2333.33"),  # Odd amount
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            ytd_gross=Decimal("0"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result = self.engine.calculate(input_data)

        # All results should have max 2 decimal places
        def count_decimal_places(value: Decimal) -> int:
            return max(0, -value.as_tuple().exponent)

        assert count_decimal_places(result.net_pay) <= 2
        assert count_decimal_places(result.total_employee_deductions) <= 2
        assert count_decimal_places(result.total_employer_costs) <= 2

    def test_fractional_cent_handling(self):
        """Test: Fractional cents are properly handled."""
        # Use an amount that would produce fractional cents
        input_data = EmployeePayrollInput(
            employee_id="emp_fractional",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            gross_regular=Decimal("1111.11"),
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            ytd_gross=Decimal("0"),
            ytd_pensionable_earnings=Decimal("0"),
            ytd_insurable_earnings=Decimal("0"),
            ytd_cpp_base=Decimal("0"),
            ytd_cpp_additional=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result = self.engine.calculate(input_data)

        # EI: $1111.11 × 1.64% = $18.22 (rounded)
        # Should be properly rounded, not truncated
        assert result.ei_employee == Decimal("18.22")
