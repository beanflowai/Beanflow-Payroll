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

from app.services.payroll.payroll_engine import PayrollEngine

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
    Uses dynamic test discovery based on fixture data.
    """

    TIER = 2
    CATEGORY = "low_income"

    def test_low_income(self, dynamic_case):
        """
        Test low income calculation with maximum tax benefits.

        Low income scenarios test:
        - Full tax reduction benefits (BC)
        - Below health premium threshold (ON)
        - Maximum dynamic BPA (MB)
        - Higher BPA tier (NS)
        """
        year, edition, case_id = dynamic_case

        engine = PayrollEngine(year=year)
        case = get_case_by_id(TIER, case_id, year, edition)

        input_data = build_payroll_input(case)
        result = engine.calculate(input_data)

        validations = validate_all_components(result, case.pdoc_expected)
        assert_validations_pass(case_id, validations)


class TestTier2HighIncome:
    """
    PDOC Validation: High Income Tests ($120k+ annual)

    Tests scenarios with full surtax, health premiums, and CPP2.
    Uses dynamic test discovery based on fixture data.
    """

    TIER = 2
    CATEGORY = "high_income"

    def test_high_income(self, dynamic_case):
        """
        Test high income calculation with surtax and premiums.

        High income scenarios test:
        - Full Ontario surtax and health premium
        - CPP2 contributions (above YMPE)
        - Reduced dynamic BPA (MB)
        - No tax reduction (BC at high income)
        - Top tax bracket calculations
        """
        year, edition, case_id = dynamic_case

        engine = PayrollEngine(year=year)
        case = get_case_by_id(TIER, case_id, year, edition)

        input_data = build_payroll_input(case)
        result = engine.calculate(input_data)

        validations = validate_all_components(result, case.pdoc_expected)
        assert_validations_pass(case_id, validations)


class TestTier2DataIntegrity:
    """Tests to ensure Tier 2 fixture data is valid."""

    def test_has_low_and_high_income_cases(self):
        """Verify both low and high income cases exist."""
        cases = load_tier_cases(TIER)

        low_income = [c for c in cases if c.category == "low_income"]
        high_income = [c for c in cases if c.category == "high_income"]

        assert len(low_income) >= 4, f"Expected at least 4 low income cases, got {len(low_income)}"
        assert len(high_income) >= 6, f"Expected at least 6 high income cases, got {len(high_income)}"

    def test_verified_cases_count(self):
        """Report number of verified cases."""
        verified_ids = get_verified_case_ids(TIER)
        total = len(load_tier_cases(TIER))
        print(f"\nTier 2: {len(verified_ids)}/{total} cases verified")
        assert True
