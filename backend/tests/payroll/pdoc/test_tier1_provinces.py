"""
Tier 1: Core Province Coverage Tests

Tests standard $60k annual, bi-weekly calculations for all 12 provinces/territories.
This tier establishes the baseline for all provincial tax calculations.

Coverage:
- Ontario (ON) - Surtax, Health Premium
- Alberta (AB) - Flat 10% rate, K5P credit
- British Columbia (BC) - Tax reduction (Factor S)
- Manitoba (MB) - Dynamic BPA
- Saskatchewan (SK) - Mid-year BPA change
- New Brunswick (NB) - Standard
- Newfoundland (NL) - Standard
- Nova Scotia (NS) - Two-tier BPA, Surtax
- Prince Edward Island (PE) - Mid-year BPA change
- Northwest Territories (NT) - Standard
- Nunavut (NU) - Standard
- Yukon (YT) - Federal BPA formula
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

TIER = 1


class TestTier1ProvinceCoverage:
    """
    PDOC Validation: Core Province Coverage

    Validates standard $60k annual, bi-weekly calculations for all provinces.
    Uses dynamic test discovery based on fixture data.
    """

    TIER = 1
    CATEGORY = "province_coverage"

    def test_province(self, dynamic_case):
        """
        Test standard $60k bi-weekly calculation for each province.

        Validates:
        - CPP total (base + enhancement)
        - EI employee contribution
        - Federal tax
        - Provincial tax
        - Net pay

        All within $0.05 tolerance.
        """
        year, edition, case_id = dynamic_case

        engine = PayrollEngine(year=year)
        case = get_case_by_id(TIER, case_id, year, edition)

        # Run calculation
        input_data = build_payroll_input(case)
        result = engine.calculate(input_data)

        # Validate all components
        validations = validate_all_components(result, case.pdoc_expected)
        assert_validations_pass(case_id, validations)


class TestTier1DataIntegrity:
    """Tests to ensure Tier 1 fixture data is valid and complete."""

    def test_fixture_has_all_provinces(self):
        """Verify all 12 provinces are in the fixture."""
        cases = load_tier_cases(TIER)
        provinces = {case.input["province"] for case in cases}

        expected_provinces = {
            "ON", "AB", "BC", "MB", "SK", "NB",
            "NL", "NS", "PE", "NT", "NU", "YT"
        }
        assert provinces == expected_provinces, (
            f"Missing provinces: {expected_provinces - provinces}"
        )

    def test_all_cases_have_required_fields(self):
        """Verify all test cases have required input fields."""
        cases = load_tier_cases(TIER)
        required_fields = [
            "province", "gross_pay", "pay_frequency", "pay_date",
            "federal_claim", "provincial_claim"
        ]

        for case in cases:
            for field in required_fields:
                assert field in case.input, (
                    f"Missing field '{field}' in case {case.id}"
                )

    def test_verified_cases_count(self):
        """Report number of verified cases."""
        verified_ids = get_verified_case_ids(TIER)
        total = len(load_tier_cases(TIER))
        print(f"\nTier 1: {len(verified_ids)}/{total} cases verified")
        # This test always passes, just reports status
        assert True
