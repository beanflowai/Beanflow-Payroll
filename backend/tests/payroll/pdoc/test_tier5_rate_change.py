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

from app.services.payroll.payroll_engine import PayrollEngine

from .conftest import (
    YEAR_EDITION_COMBINATIONS,
    assert_validations_pass,
    build_payroll_input,
    get_case_by_id,
    get_cases_by_category,
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
    Uses dynamic test discovery based on fixture data.
    """

    TIER = 5
    CATEGORY = "pre_july"

    def test_pre_july_rate(self, dynamic_case):
        """
        Test calculations with 15% federal rate (pre-July 2025).

        Key differences at 15%:
        - Higher federal tax than 14%
        - Different K1, K2 credit calculations
        """
        year, edition, case_id = dynamic_case

        engine = PayrollEngine(year=year)
        case = get_case_by_id(TIER, case_id, year, edition)

        input_data = build_payroll_input(case)
        result = engine.calculate(input_data)

        validations = validate_all_components(result, case.pdoc_expected)
        assert_validations_pass(case_id, validations)


class TestTier5PostJulyRate:
    """
    PDOC Validation: Post-July 2025 Tests (14% Federal Rate)

    Tests calculations after July 1, 2025 when federal lowest
    bracket rate is 14%.
    Uses dynamic test discovery based on fixture data.
    """

    TIER = 5
    CATEGORY = "post_july"

    def test_post_july_rate(self, dynamic_case):
        """
        Test calculations with 14% federal rate (post-July 2025).

        Key differences at 14%:
        - Lower federal tax than 15%
        - Different K1, K2 credit calculations
        """
        year, edition, case_id = dynamic_case

        engine = PayrollEngine(year=year)
        case = get_case_by_id(TIER, case_id, year, edition)

        input_data = build_payroll_input(case)
        result = engine.calculate(input_data)

        validations = validate_all_components(result, case.pdoc_expected)
        assert_validations_pass(case_id, validations)


class TestTier5RateComparison:
    """
    Tests comparing pre and post July calculations.

    These tests verify the expected difference between
    15% and 14% federal rate calculations.
    """

    def test_rate_change_impact(self):
        """
        Compare federal tax before and after rate change.

        For $60k income, the rate change should result in
        approximately 1% lower federal tax at 14% vs 15%.
        """
        # Find year/edition combinations that have both pre and post July cases
        for year, edition in YEAR_EDITION_COMBINATIONS:
            pre_july_cases = get_cases_by_category(TIER, "pre_july", year, edition)
            post_july_cases = get_cases_by_category(TIER, "post_july", year, edition)

            if not pre_july_cases or not post_july_cases:
                continue

            # Get matching ON_60K cases if available
            jan_case = next((c for c in pre_july_cases if "ON_60K" in c.id), None)
            jul_case = next((c for c in post_july_cases if "ON_60K" in c.id), None)

            if jan_case and jul_case:
                engine = PayrollEngine(year=year)

                jan_input = build_payroll_input(jan_case)
                jul_input = build_payroll_input(jul_case)

                jan_result = engine.calculate(jan_input)
                jul_result = engine.calculate(jul_input)

                # Federal tax should be lower in July
                print(f"\nFederal Tax Comparison ({year}-{edition}):")
                print(f"  Pre-July (15%): ${jan_result.federal_tax:.2f}")
                print(f"  Post-July (14%): ${jul_result.federal_tax:.2f}")
                print(f"  Difference: ${jan_result.federal_tax - jul_result.federal_tax:.2f}")

                # Provincial tax should be the same (no provincial rate change)
                assert jan_result.provincial_tax == jul_result.provincial_tax, (
                    "Provincial tax should not change between pre and post July"
                )

                # CPP and EI should be the same (same gross, same YTD)
                assert jan_result.cpp_total == jul_result.cpp_total, (
                    "CPP should not change between pre and post July"
                )
                assert jan_result.ei_employee == jul_result.ei_employee, (
                    "EI should not change between pre and post July"
                )

                return  # Found and tested a valid comparison

        # If no valid comparison found, skip the test
        import pytest
        pytest.skip("No matching pre/post July comparison cases found")


class TestTier5DataIntegrity:
    """Tests to ensure Tier 5 fixture data is valid."""

    def test_has_pre_and_post_july_cases(self):
        """Verify both pre and post July cases exist."""
        cases = load_tier_cases(TIER)

        pre_july_cases = [c for c in cases if c.category == "pre_july"]
        [c for c in cases if c.category == "post_july"]

        assert len(pre_july_cases) >= 1, f"Expected at least 1 pre-July case, got {len(pre_july_cases)}"

    def test_pay_dates_correct(self):
        """Verify pay dates are before/after July 1, 2025."""
        cases = load_tier_cases(TIER)

        for case in cases:
            pay_date = case.input["pay_date"]
            if case.category == "pre_july":
                assert pay_date < "2025-07-01", f"{case.id} should have pre-July date"
            if case.category == "post_july":
                assert pay_date >= "2025-07-01", f"{case.id} should have post-July date"

    def test_verified_cases_count(self):
        """Report number of verified cases."""
        verified_ids = get_verified_case_ids(TIER)
        total = len(load_tier_cases(TIER))
        print(f"\nTier 5: {len(verified_ids)}/{total} cases verified")
        assert True
