"""
Tier 6: TD1 Form Field Tests

Tests for TD1 form fields that affect tax calculations:
- Employer RRSP contributions (affects EI insurability)
- Retroactive payments
- Prescribed zone deductions (Northern living allowance)
- Alimony/maintenance payments (court-ordered)
- Tax-exempt reserve income with pensionable election
- Other annual deductions (child care, medical, charitable)
- RPP/PRPP contributions

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


class TestTier6PrescribedZone:
    """
    PDOC Validation: Prescribed Zone Deduction Tests

    Prescribed zone deductions for Northern/Island residents.
    Uses dynamic test discovery based on fixture data.
    """

    TIER = 6
    CATEGORY = "prescribed_zone"

    def test_prescribed_zone(self, dynamic_case):
        """
        Test prescribed zone deductions.

        Prescribed zone deductions:
        - Additional tax credit for Northern/Island residents
        - Reduce federal tax payable
        - Vary by zone (prescribed vs intermediate)
        """
        year, edition, case_id = dynamic_case

        engine = PayrollEngine(year=year)
        case = get_case_by_id(TIER, case_id, year, edition)

        input_data = build_payroll_input(case)
        result = engine.calculate(input_data)

        validations = validate_all_components(result, case.pdoc_expected)
        assert_validations_pass(case_id, validations)


class TestTier6Alimony:
    """
    PDOC Validation: Alimony/Maintenance Payment Tests

    Court-ordered alimony or maintenance payments.
    Uses dynamic test discovery based on fixture data.
    """

    TIER = 6
    CATEGORY = "alimony"

    def test_alimony(self, dynamic_case):
        """
        Test court-ordered alimony payments.

        Alimony payments:
        - Tax-deductible for the payer
        - Reduce taxable income
        - Must be court-ordered or written agreement
        """
        year, edition, case_id = dynamic_case

        engine = PayrollEngine(year=year)
        case = get_case_by_id(TIER, case_id, year, edition)

        input_data = build_payroll_input(case)
        result = engine.calculate(input_data)

        validations = validate_all_components(result, case.pdoc_expected)
        assert_validations_pass(case_id, validations)


class TestTier6ReserveIncome:
    """
    PDOC Validation: Tax-Exempt Reserve Income Tests

    Tax-exempt reserve income (military/RCMP) with pensionable election.
    Uses dynamic test discovery based on fixture data.
    """

    TIER = 6
    CATEGORY = "reserve_income"

    def test_reserve_income(self, dynamic_case):
        """
        Test tax-exempt reserve income.

        Reserve income:
        - Exempt from income tax (military/RCMP)
        - May be elected as pensionable for CPP
        - Affects CPP calculation if elected
        """
        year, edition, case_id = dynamic_case

        engine = PayrollEngine(year=year)
        case = get_case_by_id(TIER, case_id, year, edition)

        input_data = build_payroll_input(case)
        result = engine.calculate(input_data)

        validations = validate_all_components(result, case.pdoc_expected)
        assert_validations_pass(case_id, validations)


class TestTier6AnnualDeductions:
    """
    PDOC Validation: Other Annual Deductions Tests

    Child care, medical expenses, charitable donations.
    Uses dynamic test discovery based on fixture data.
    """

    TIER = 6
    CATEGORY = "annual_deductions"

    def test_annual_deductions(self, dynamic_case):
        """
        Test other annual deductions.

        Annual deductions:
        - Child care expenses
        - Medical expenses
        - Charitable donations
        - Claimed annually on TD1 form
        """
        year, edition, case_id = dynamic_case

        engine = PayrollEngine(year=year)
        case = get_case_by_id(TIER, case_id, year, edition)

        input_data = build_payroll_input(case)
        result = engine.calculate(input_data)

        validations = validate_all_components(result, case.pdoc_expected)
        assert_validations_pass(case_id, validations)


class TestTier6RppPrpp:
    """
    PDOC Validation: RPP/PRPP Contribution Tests

    Registered Pension Plan (RPP) and Pooled Registered Pension Plan (PRPP).
    Uses dynamic test discovery based on fixture data.
    """

    TIER = 6
    CATEGORY = "rpp_prpp"

    def test_rpp_prpp(self, dynamic_case):
        """
        Test RPP/PRPP contributions.

        RPP/PRPP contributions:
        - Deducted at source like RRSP
        - Reduce taxable income
        - Similar tax treatment to RRSP
        """
        year, edition, case_id = dynamic_case

        engine = PayrollEngine(year=year)
        case = get_case_by_id(TIER, case_id, year, edition)

        input_data = build_payroll_input(case)
        result = engine.calculate(input_data)

        validations = validate_all_components(result, case.pdoc_expected)
        assert_validations_pass(case_id, validations)


class TestTier6DataIntegrity:
    """Tests to ensure Tier 6 fixture data is valid."""

    def test_has_td1_field_cases(self):
        """Verify TD1 form field test cases exist."""
        # Tier 6 uses split fixtures by category - load each category separately
        from .conftest import load_tier6_category_fixture, TIER6_CATEGORIES

        # Collect all cases from all Tier 6 categories
        all_cases = []
        for category in TIER6_CATEGORIES:
            fixture_data = load_tier6_category_fixture(category, 2026, "jan")
            category_cases = [
                PDOCTestCase.from_dict(case)
                for case in fixture_data.get("test_cases", [])
            ]
            all_cases.extend(category_cases)

        employer_rrsp_cases = [c for c in all_cases if c.category == "employer_rrsp"]
        retroactive_cases = [c for c in all_cases if c.category == "retroactive_pay"]
        prescribed_zone_cases = [c for c in all_cases if c.category == "prescribed_zone"]
        alimony_cases = [c for c in all_cases if c.category == "alimony"]
        reserve_income_cases = [c for c in all_cases if c.category == "reserve_income"]
        annual_deductions_cases = [c for c in all_cases if c.category == "annual_deductions"]
        rpp_prpp_cases = [c for c in all_cases if c.category == "rpp_prpp"]

        # Verify all categories have test cases
        assert len(employer_rrsp_cases) >= 1, f"Expected at least 1 employer RRSP case, got {len(employer_rrsp_cases)}"
        assert len(retroactive_cases) >= 1, f"Expected at least 1 retroactive pay case, got {len(retroactive_cases)}"
        assert len(prescribed_zone_cases) >= 1, f"Expected at least 1 prescribed zone case, got {len(prescribed_zone_cases)}"
        assert len(alimony_cases) >= 1, f"Expected at least 1 alimony case, got {len(alimony_cases)}"
        assert len(reserve_income_cases) >= 1, f"Expected at least 1 reserve income case, got {len(reserve_income_cases)}"
        assert len(annual_deductions_cases) >= 1, f"Expected at least 1 annual deductions case, got {len(annual_deductions_cases)}"
        assert len(rpp_prpp_cases) >= 1, f"Expected at least 1 RPP/PRPP case, got {len(rpp_prpp_cases)}"

    def test_verified_cases_count(self):
        """Report number of verified cases."""
        # Tier 6 uses split fixtures - collect from all categories
        from .conftest import load_tier6_category_fixture, TIER6_CATEGORIES

        all_cases = []
        verified_count = 0
        for category in TIER6_CATEGORIES:
            fixture_data = load_tier6_category_fixture(category, 2026, "jan")
            category_cases = [
                PDOCTestCase.from_dict(case)
                for case in fixture_data.get("test_cases", [])
            ]
            all_cases.extend(category_cases)
            verified_count += sum(1 for c in category_cases if c.is_verified)

        total = len(all_cases)
        print(f"\nTier 6 (2026-jan): {verified_count}/{total} cases verified")
        assert True
