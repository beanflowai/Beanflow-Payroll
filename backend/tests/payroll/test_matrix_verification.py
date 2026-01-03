"""
Deduction Calculation Verification Tests for PayrollEngine.

Verification tests for specific deduction calculations.
These tests verify the mathematical accuracy of deductions.

Phase 4 - Test Matrix Implementation - Deduction Calculation Verification
"""

from decimal import Decimal

import pytest

from app.models.payroll import PayFrequency, Province
from app.services.payroll.payroll_engine import PayrollEngine

from .conftest import INCOME_LEVELS, create_standard_input


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
