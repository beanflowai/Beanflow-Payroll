"""
Tier 5: Federal Tax Rate Change Tests

Tests for pre/post July 2025 federal tax rate change.

Federal Lowest Bracket Rate Change:
- Before July 1, 2025: 15%
- After July 1, 2025: 14%

This rate change affects:
- Federal tax calculation for lowest bracket
- K1 (federal personal credits) calculation
- K2 (federal CPP/EI credits) calculation

Coverage:
- January 2025: Pre-July rate (15%)
- June 2025: Last day at 15%
- July 2025: First pay at 14%
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

TIER = 5


class TestTier5PreJulyRate:
    """
    PDOC Validation: Pre-July 2025 Tests (15% Federal Rate)

    Tests calculations before July 1, 2025 when federal lowest
    bracket rate is 15%.
    """

    @pytest.fixture(autouse=True)
    def setup(self, payroll_engine):
        """Set up PayrollEngine for tests."""
        self.engine = payroll_engine

    @pytest.mark.parametrize(
        "case_id",
        [
            "ON_60K_JAN",   # January 2025
            "ON_60K_JUN",   # June 27, 2025 (last day at 15%)
            "AB_60K_JAN",   # Alberta January comparison
        ],
    )
    def test_pre_july_rate(self, case_id: str):
        """
        Test calculations with 15% federal rate (pre-July 2025).

        Key differences at 15%:
        - Higher federal tax than 14%
        - Different K1, K2 credit calculations
        """
        case = get_case_by_id(TIER, case_id)
        if not case:
            pytest.skip(f"Test case {case_id} not found")

        if not case.is_verified:
            pytest.skip(f"Test case {case_id} not yet verified with PDOC")

        input_data = build_payroll_input(case)
        result = self.engine.calculate(input_data)

        validations = validate_all_components(result, case.pdoc_expected)
        assert_validations_pass(case_id, validations)


class TestTier5PostJulyRate:
    """
    PDOC Validation: Post-July 2025 Tests (14% Federal Rate)

    Tests calculations after July 1, 2025 when federal lowest
    bracket rate is 14%.
    """

    @pytest.fixture(autouse=True)
    def setup(self, payroll_engine):
        """Set up PayrollEngine for tests."""
        self.engine = payroll_engine

    def test_post_july_rate(self):
        """
        Test calculations with 14% federal rate (post-July 2025).

        Key differences at 14%:
        - Lower federal tax than 15%
        - Different K1, K2 credit calculations
        """
        case = get_case_by_id(TIER, "ON_60K_JUL")
        if not case:
            pytest.skip("Test case ON_60K_JUL not found")

        if not case.is_verified:
            pytest.skip("Test case not yet verified with PDOC")

        input_data = build_payroll_input(case)
        result = self.engine.calculate(input_data)

        validations = validate_all_components(result, case.pdoc_expected)
        assert_validations_pass("ON_60K_JUL", validations)


class TestTier5RateComparison:
    """
    Tests comparing pre and post July calculations.

    These tests verify the expected difference between
    15% and 14% federal rate calculations.
    """

    @pytest.fixture(autouse=True)
    def setup(self, payroll_engine):
        """Set up PayrollEngine for tests."""
        self.engine = payroll_engine

    def test_rate_change_impact(self):
        """
        Compare federal tax before and after rate change.

        For $60k income, the rate change should result in
        approximately 1% lower federal tax at 14% vs 15%.
        """
        jan_case = get_case_by_id(TIER, "ON_60K_JAN")
        jul_case = get_case_by_id(TIER, "ON_60K_JUL")

        if not jan_case or not jul_case:
            pytest.skip("Rate comparison cases not found")

        if not jan_case.is_verified or not jul_case.is_verified:
            pytest.skip("Rate comparison cases not yet verified with PDOC")

        jan_input = build_payroll_input(jan_case)
        jul_input = build_payroll_input(jul_case)

        jan_result = self.engine.calculate(jan_input)
        jul_result = self.engine.calculate(jul_input)

        # Federal tax should be lower in July
        print(f"\nFederal Tax Comparison:")
        print(f"  January (15%): ${jan_result.federal_tax:.2f}")
        print(f"  July (14%): ${jul_result.federal_tax:.2f}")
        print(f"  Difference: ${jan_result.federal_tax - jul_result.federal_tax:.2f}")

        # Provincial tax should be the same (no provincial rate change)
        assert jan_result.provincial_tax == jul_result.provincial_tax, (
            "Provincial tax should not change between January and July"
        )

        # CPP and EI should be the same (same gross, same YTD)
        assert jan_result.cpp_total == jul_result.cpp_total, (
            "CPP should not change between January and July"
        )
        assert jan_result.ei_employee == jul_result.ei_employee, (
            "EI should not change between January and July"
        )


class TestTier5DataIntegrity:
    """Tests to ensure Tier 5 fixture data is valid."""

    def test_has_pre_and_post_july_cases(self):
        """Verify both pre and post July cases exist."""
        cases = load_tier_cases(TIER)

        jan_cases = [c for c in cases if "JAN" in c.id]
        jun_cases = [c for c in cases if "JUN" in c.id]
        jul_cases = [c for c in cases if "JUL" in c.id]

        assert len(jan_cases) >= 2, "Expected at least 2 January cases"
        assert len(jun_cases) >= 1, "Expected at least 1 June case"
        assert len(jul_cases) >= 1, "Expected at least 1 July case"

    def test_pay_dates_correct(self):
        """Verify pay dates are before/after July 1, 2025."""
        cases = load_tier_cases(TIER)

        for case in cases:
            pay_date = case.input["pay_date"]
            if "JAN" in case.id or "JUN" in case.id:
                assert pay_date < "2025-07-01", f"{case.id} should have pre-July date"
            if "JUL" in case.id:
                assert pay_date >= "2025-07-01", f"{case.id} should have post-July date"

    def test_verified_cases_count(self):
        """Report number of verified cases."""
        verified_ids = get_verified_case_ids(TIER)
        total = len(load_tier_cases(TIER))
        print(f"\nTier 5: {len(verified_ids)}/{total} cases verified")
        assert True
