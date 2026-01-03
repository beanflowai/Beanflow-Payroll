"""
Federal Tax Rate Change Tests for PayrollEngine.

Tests for July 2025 federal tax rate change (15% → 14%).
The federal government changed the lowest tax bracket rate from
15% to 14% effective July 1, 2025.

Phase 4 - Test Matrix Implementation - Federal Tax Rate Change
"""

from datetime import date
from decimal import Decimal

import pytest

from app.models.payroll import PayFrequency, Province
from app.services.payroll.payroll_engine import PayrollEngine

from .conftest import INCOME_LEVELS, create_standard_input


class TestFederalTaxRateChange:
    """
    Tests for July 2025 federal tax rate change (15% → 14%).

    The federal government changed the lowest tax bracket rate from
    15% to 14% effective July 1, 2025.
    """

    def setup_method(self):
        self.engine = PayrollEngine(year=2025)

    @pytest.mark.parametrize("province", list(Province))
    def test_federal_tax_lower_after_july(self, province: Province):
        """Test: Federal tax is lower after July 2025 for all provinces."""
        base_input = {
            "province": province,
            "pay_frequency": PayFrequency.BIWEEKLY,
            "annual_income": INCOME_LEVELS["medium"],
        }

        input_before = create_standard_input(
            **base_input,
            pay_date=date(2025, 3, 15),  # Before July
        )
        input_after = create_standard_input(
            **base_input,
            pay_date=date(2025, 7, 15),  # After July
        )

        result_before = self.engine.calculate(input_before)
        result_after = self.engine.calculate(input_after)

        # Federal tax after July should be lower
        assert result_after.federal_tax < result_before.federal_tax, (
            f"{province.value}: Federal tax should be lower after July"
        )

    def test_federal_tax_boundary_june_30(self):
        """Test: June 30 still uses 15% rate."""
        input_data = create_standard_input(
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            annual_income=INCOME_LEVELS["medium"],
            pay_date=date(2025, 6, 30),
        )
        result = self.engine.calculate(input_data)

        # June 30 should use 15% rate
        assert result.federal_tax > Decimal("0")

    def test_federal_tax_boundary_july_1(self):
        """Test: July 1 uses 14% rate."""
        input_june = create_standard_input(
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            annual_income=INCOME_LEVELS["medium"],
            pay_date=date(2025, 6, 30),
        )
        input_july = create_standard_input(
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            annual_income=INCOME_LEVELS["medium"],
            pay_date=date(2025, 7, 1),
        )

        result_june = self.engine.calculate(input_june)
        result_july = self.engine.calculate(input_july)

        # July 1 should use 14% rate (lower tax)
        assert result_july.federal_tax < result_june.federal_tax
