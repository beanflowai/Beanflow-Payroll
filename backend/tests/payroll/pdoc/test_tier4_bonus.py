"""
Tier 4: Bonus Taxation Tests

Tests for bonus payment taxation using CRA T4127 marginal rate method.
Validates that bonuses are correctly taxed using the formula:
Bonus Tax = Tax(YTD + Bonus) - Tax(YTD)

Coverage:
- Standard bonus scenarios (ON $10K, AB $5K)
- High-value bonus edge cases (BC $60K)
- Bonus tax split by income vs bonus
- CPP/EI deductions on bonus payments

Reference: CRA T4127 Payroll Deductions Formulas (122nd Edition, January 2026)
"""

from __future__ import annotations

from decimal import Decimal

from app.services.payroll.payroll_engine import PayrollEngine

from .conftest import (
    VARIANCE_TOLERANCE,
    assert_validations_pass,
    build_payroll_input,
    get_case_by_id,
    get_verified_case_ids,
    load_tier_cases,
    validate_all_components,
)

TIER = 4


class TestTier4Bonus:
    """
    PDOC Validation: Bonus Taxation Tests

    Tests bonus payment taxation using CRA T4127 marginal rate method.
    Uses dynamic test discovery based on fixture data.
    """

    TIER = 4
    CATEGORY = "bonus"

    def test_bonus_taxation(self, dynamic_case):
        """
        Test bonus taxation using marginal rate method.

        Bonus taxation:
        - Uses marginal rate method: Tax(YTD + Bonus) - Tax(YTD)
        - Separates income tax from bonus tax
        - Validates both components independently
        - CPP/EI calculated on bonus amounts
        """
        year, edition, case_id = dynamic_case

        engine = PayrollEngine(year=year)
        case = get_case_by_id(TIER, case_id, year, edition)

        input_data = build_payroll_input(case)
        result = engine.calculate(input_data)

        validations = validate_all_components(result, case.pdoc_expected)
        assert_validations_pass(case_id, validations)


class TestTier4BonusDataIntegrity:
    """Tests to ensure Tier 4 bonus fixture data is valid."""

    def test_has_bonus_cases(self):
        """Verify bonus test cases exist."""
        # Note: tier4_bonus.json is a separate fixture file
        # We need to load it directly since it's not in tier4_special_conditions.json
        import json

        from pathlib import Path

        fixtures_dir = Path(__file__).parent / "fixtures"
        bonus_cases_found = False

        # Check all year/edition combinations for tier4_bonus.json
        for year in [2025, 2026]:
            for edition in ["jan", "jul"]:
                fixture_path = fixtures_dir / str(year) / edition / "tier4_bonus.json"
                if fixture_path.exists():
                    with open(fixture_path) as f:
                        data = json.load(f)
                        test_cases = data.get("test_cases", [])
                        if test_cases:
                            bonus_cases_found = True
                            bonus_count = len([c for c in test_cases if c.get("category") == "bonus"])
                            print(f"\nTier 4 Bonus: Found {bonus_count} bonus cases in {year}-{edition}")

        assert bonus_cases_found, "No tier4_bonus.json fixture files found"

    def test_bonus_cases_structure(self):
        """Verify bonus test cases have required structure."""
        import json

        from pathlib import Path

        fixtures_dir = Path(__file__).parent / "fixtures"

        # Check 2026-jan tier4_bonus.json structure
        fixture_path = fixtures_dir / "2026" / "jan" / "tier4_bonus.json"
        if fixture_path.exists():
            with open(fixture_path) as f:
                data = json.load(f)
                test_cases = data.get("test_cases", [])

            for case in test_cases:
                # Verify input has bonus_amount
                assert "bonus_amount" in case["input"], f"Case {case['id']} missing bonus_amount"
                assert "salary_per_period" in case["input"], f"Case {case['id']} missing salary_per_period"

                # Verify expected has bonus tax breakdown
                expected = case["pdoc_expected"]
                assert "bonus_federal_tax" in expected, f"Case {case['id']} missing bonus_federal_tax"
                assert "bonus_provincial_tax" in expected, f"Case {case['id']} missing bonus_provincial_tax"
                assert "bonus_total_tax" in expected, f"Case {case['id']} missing bonus_total_tax"

                # Verify income tax breakdown
                assert "income_federal_tax" in expected, f"Case {case['id']} missing income_federal_tax"
                assert "income_provincial_tax" in expected, f"Case {case['id']} missing income_provincial_tax"

        assert True
