"""
Tier 2: Income Level Coverage Tests

Tests low and high income scenarios for provinces with special rules.

Coverage:
- Low Income ($30k): Tests tax credits, reductions at lower brackets
- High Income ($120k+): Tests surtax, health premiums, CPP2

Provinces with special income-based rules:
- Ontario: Health premium, surtax thresholds
- BC: Tax reduction (Factor S) phases out
- Manitoba: Dynamic BPA adjustment
- Nova Scotia: Two-tier BPA, surtax
- Alberta: Flat rate comparison at different income levels
"""

from __future__ import annotations

import pytest

from .conftest import (
    assert_validations_pass,
    build_payroll_input,
    get_case_by_id,
    get_verified_case_ids,
    load_tier_cases,
    validate_all_components,
)

TIER = 2


class TestTier2LowIncome:
    """
    PDOC Validation: Low Income Tests ($30k annual)

    Tests scenarios where tax credits and reductions are maximized.
    Parameterized by tax_year and edition from conftest.py fixtures.
    """

    @pytest.fixture(autouse=True)
    def setup(self, payroll_engine, tax_year, edition):
        """Set up PayrollEngine and context for tests."""
        self.engine = payroll_engine
        self.tax_year = tax_year
        self.edition = edition

    @pytest.mark.parametrize(
        "case_id",
        [
            "ON_30K_BIWEEKLY",
            "BC_30K_BIWEEKLY",
            "MB_30K_BIWEEKLY",
            "NS_30K_BIWEEKLY",
        ],
    )
    def test_low_income(self, case_id: str):
        """
        Test low income calculation with maximum tax benefits.

        Low income scenarios test:
        - Full tax reduction benefits (BC)
        - Below health premium threshold (ON)
        - Maximum dynamic BPA (MB)
        - Higher BPA tier (NS)
        """
        case = get_case_by_id(TIER, case_id, self.tax_year, self.edition)
        if not case:
            pytest.skip(f"Test case {case_id} not found for {self.tax_year}/{self.edition}")

        if not case.is_verified:
            pytest.skip(f"Test case {case_id} not yet verified with PDOC")

        input_data = build_payroll_input(case)
        result = self.engine.calculate(input_data)

        validations = validate_all_components(result, case.pdoc_expected)
        assert_validations_pass(case_id, validations)


class TestTier2HighIncome:
    """
    PDOC Validation: High Income Tests ($120k+ annual)

    Tests scenarios with full surtax, health premiums, and CPP2.
    Parameterized by tax_year and edition from conftest.py fixtures.
    """

    @pytest.fixture(autouse=True)
    def setup(self, payroll_engine, tax_year, edition):
        """Set up PayrollEngine and context for tests."""
        self.engine = payroll_engine
        self.tax_year = tax_year
        self.edition = edition

    @pytest.mark.parametrize(
        "case_id",
        [
            "ON_120K_MONTHLY",
            "AB_120K_MONTHLY",
            "BC_120K_MONTHLY",
            "MB_120K_MONTHLY",
            "ON_150K_MONTHLY",
            "NS_120K_MONTHLY",
            "ON_200K_MONTHLY",
            "AB_200K_MONTHLY",
        ],
    )
    def test_high_income(self, case_id: str):
        """
        Test high income calculation with surtax and premiums.

        High income scenarios test:
        - Full Ontario surtax and health premium
        - CPP2 contributions (above YMPE)
        - Reduced dynamic BPA (MB)
        - No tax reduction (BC at high income)
        - Top tax bracket calculations
        """
        case = get_case_by_id(TIER, case_id, self.tax_year, self.edition)
        if not case:
            pytest.skip(f"Test case {case_id} not found for {self.tax_year}/{self.edition}")

        if not case.is_verified:
            pytest.skip(f"Test case {case_id} not yet verified with PDOC")

        input_data = build_payroll_input(case)
        result = self.engine.calculate(input_data)

        validations = validate_all_components(result, case.pdoc_expected)
        assert_validations_pass(case_id, validations)


class TestTier2DataIntegrity:
    """Tests to ensure Tier 2 fixture data is valid."""

    def test_has_low_and_high_income_cases(self):
        """Verify both low and high income cases exist."""
        cases = load_tier_cases(TIER)

        low_income = [c for c in cases if "30K" in c.id]
        high_income = [c for c in cases if "120K" in c.id or "150K" in c.id or "200K" in c.id]

        assert len(low_income) >= 4, f"Expected at least 4 low income cases, got {len(low_income)}"
        assert len(high_income) >= 6, f"Expected at least 6 high income cases, got {len(high_income)}"

    def test_verified_cases_count(self):
        """Report number of verified cases."""
        verified_ids = get_verified_case_ids(TIER)
        total = len(load_tier_cases(TIER))
        print(f"\nTier 2: {len(verified_ids)}/{total} cases verified")
        assert True
