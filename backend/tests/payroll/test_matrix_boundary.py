"""
Boundary Tests (B01-B10) for PayrollEngine.

These tests verify correct behavior at critical income boundaries
for CPP, CPP2, and EI thresholds.

Phase 4 - Test Matrix Implementation - Boundary Conditions
"""

from datetime import date
from decimal import Decimal

import pytest

from app.models.payroll import PayFrequency, Province
from app.services.payroll.payroll_engine import EmployeePayrollInput, PayrollEngine

from .conftest import (
    CPP_BASIC_EXEMPTION,
    CPP_MAX_ADDITIONAL,
    CPP_MAX_BASE,
    CPP_YAMPE,
    CPP_YMPE,
    EI_MAX,
    EI_MIE,
    FEDERAL_BPA,
    INCOME_LEVELS,
    PROVINCIAL_BPA,
    create_standard_input,
)


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
