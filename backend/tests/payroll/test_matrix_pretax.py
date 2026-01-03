"""
Pre-Tax Deduction Tests for PayrollEngine.

Tests for pre-tax deductions like RRSP.
Validates that RRSP reduces taxable income but not CPP/EI.

Phase 4 - Test Matrix Implementation - Pre-Tax Deductions
"""

from decimal import Decimal

import pytest

from app.models.payroll import PayFrequency, Province
from app.services.payroll.payroll_engine import PayrollEngine

from .conftest import INCOME_LEVELS, create_standard_input


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
