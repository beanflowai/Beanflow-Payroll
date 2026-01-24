"""
Tier 6: TD1 Form Field Tests

Tests for TD1 form fields that affect tax calculations:
- Employer RRSP contributions (affects EI insurability) - PENDING implementation
- Retroactive payments - VERIFIED

These tests validate the payroll engine against CRA PDOC calculations for
TD1 form scenarios not covered in earlier tiers.
"""

from __future__ import annotations

from app.services.payroll.payroll_engine import PayrollEngine

from .conftest import (
    PDOCTestCase,
    VARIANCE_TOLERANCE,
    assert_validations_pass,
    build_payroll_input,
    get_case_by_id,
    get_verified_case_ids,
    load_tier_cases,
    validate_all_components,
    validate_component,
)

TIER = 6


class TestTier6EmployerRRSP:
    """
    PDOC Validation: Employer RRSP Contribution Tests

    Employer RRSP contributions affect EI insurability:
    - Withdrawal-restricted RRSP: NOT EI insurable
    - Non-restricted RRSP: May be EI insurable

    Uses dynamic test discovery based on fixture data.
    """

    TIER = 6
    CATEGORY = "employer_rrsp"

    def test_employer_rrsp(self, dynamic_case):
        """
        Test employer RRSP contributions affect EI insurability.

        Employer RRSP contributions:
        - May affect EI insurable earnings depending on withdrawal restrictions
        - Do NOT affect CPP contributions
        - Do NOT directly affect tax calculation (employee benefit)
        """
        year, edition, case_id = dynamic_case

        engine = PayrollEngine(year=year)
        case = get_case_by_id(TIER, case_id, year, edition)

        input_data = build_payroll_input(case)
        result = engine.calculate(input_data)

        validations = validate_all_components(result, case.pdoc_expected)
        assert_validations_pass(case_id, validations)


class TestTier6RetroactivePay:
    """
    PDOC Validation: Retroactive Payment Tests

    Retroactive payments spread over multiple pay periods.
    Uses dynamic test discovery based on fixture data.
    """

    TIER = 6
    CATEGORY = "retroactive_pay"

    def test_retroactive_pay(self, dynamic_case):
        """
        Test retroactive payment calculations.

        Retroactive payments:
        - Spread over multiple pay periods for tax calculation
        - Affect tax withholding differently than regular pay
        - May require special handling for CPP/EI maximum tracking
        """
        year, edition, case_id = dynamic_case

        engine = PayrollEngine(year=year)
        case = get_case_by_id(TIER, case_id, year, edition)

        input_data = build_payroll_input(case)
        result = engine.calculate(input_data)

        validations = validate_all_components(result, case.pdoc_expected)
        assert_validations_pass(case_id, validations)


class TestTier6DataIntegrity:
    """Tests to ensure Tier 6 fixture data is valid.

    Note: Tier 6 fixtures are collected incrementally per category.
    This test reports on available fixtures rather than requiring all.
    """

    def test_has_td1_field_cases(self):
        """Report which TD1 form field test cases exist.

        This is a reporting test - it prints the status of each category
        rather than failing when fixtures are missing.
        """
        from .conftest import load_tier6_category_fixture, TIER6_CATEGORIES

        # Collect all cases from all Tier 6 categories
        category_counts = {}
        for category in TIER6_CATEGORIES:
            fixture_data = load_tier6_category_fixture(category, 2026, "jan")
            if fixture_data:
                cases = fixture_data.get("test_cases", [])
                category_counts[category] = len(cases)
            else:
                category_counts[category] = 0

        # Print summary
        print("\n--- Tier 6 TD1 Field Fixtures (2026-jan) ---")
        available = 0
        for category, count in category_counts.items():
            status = f"{count} case(s)" if count > 0 else "PENDING"
            print(f"  {category}: {status}")
            if count > 0:
                available += 1

        print(f"\n  Total: {available}/{len(TIER6_CATEGORIES)} categories have fixtures")

        # Only assert that at least one category has cases
        total_cases = sum(category_counts.values())
        assert total_cases >= 1, "Expected at least 1 Tier 6 test case across all categories"

    def test_verified_cases_count(self):
        """Report number of verified cases."""
        from .conftest import load_tier6_category_fixture, TIER6_CATEGORIES

        all_cases = []
        verified_count = 0
        for category in TIER6_CATEGORIES:
            fixture_data = load_tier6_category_fixture(category, 2026, "jan")
            if fixture_data:
                category_cases = [
                    PDOCTestCase.from_dict(case)
                    for case in fixture_data.get("test_cases", [])
                ]
                all_cases.extend(category_cases)
                verified_count += sum(1 for c in category_cases if c.is_verified)

        total = len(all_cases)
        print(f"\nTier 6 (2026-jan): {verified_count}/{total} cases verified")
        # This is a reporting test, always passes
        assert True
