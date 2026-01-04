"""
Tier 4: Special Conditions Tests

Tests for RRSP deductions, union dues, exemptions, and taxable benefits.

Coverage:
- RRSP: Tax reduction from RRSP contributions
- Union Dues: Tax credit for union dues
- Exemptions: CPP/EI/CPP2 exempt employees
- Taxable Benefits: Benefits added to taxable income
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
    validate_component,
)

TIER = 4


class TestTier4RRSP:
    """
    PDOC Validation: RRSP Deduction Tests

    RRSP contributions reduce taxable income.
    Uses dynamic test discovery based on fixture data.
    """

    TIER = 4
    CATEGORY = "rrsp"

    def test_rrsp_deduction(self, dynamic_case):
        """
        Test RRSP reduces taxable income and taxes.

        RRSP contributions:
        - Reduce taxable income for federal tax
        - Reduce taxable income for provincial tax
        - Do NOT affect CPP/EI contributions
        """
        year, edition, case_id = dynamic_case

        engine = PayrollEngine(year=year)
        case = get_case_by_id(TIER, case_id, year, edition)

        input_data = build_payroll_input(case)
        result = engine.calculate(input_data)

        validations = validate_all_components(result, case.pdoc_expected)
        assert_validations_pass(case_id, validations)


class TestTier4UnionDues:
    """
    PDOC Validation: Union Dues Tests

    Union dues affect tax calculation.
    Uses dynamic test discovery based on fixture data.
    """

    TIER = 4
    CATEGORY = "union_dues"

    def test_union_dues_credit(self, dynamic_case):
        """Test union dues provide tax credit."""
        year, edition, case_id = dynamic_case

        engine = PayrollEngine(year=year)
        case = get_case_by_id(TIER, case_id, year, edition)

        input_data = build_payroll_input(case)
        result = engine.calculate(input_data)

        validations = validate_all_components(result, case.pdoc_expected)
        assert_validations_pass(case_id, validations)


class TestTier4Exemptions:
    """
    PDOC Validation: Exemption Tests

    Tests for CPP, EI, and CPP2 exempt employees.
    Uses dynamic test discovery based on fixture data.
    """

    TIER = 4
    CATEGORY = "exemptions"

    def test_exemption(self, dynamic_case):
        """
        Test exemption scenarios.

        Exemption types:
        - CPP exempt: Zero CPP contribution
        - EI exempt: Zero EI contribution
        - CPP2 exempt: Zero CPP2 (additional) contribution
        """
        year, edition, case_id = dynamic_case

        engine = PayrollEngine(year=year)
        case = get_case_by_id(TIER, case_id, year, edition)

        input_data = build_payroll_input(case)
        result = engine.calculate(input_data)

        # Verify specific exemption if identifiable from case ID
        case_id_upper = case_id.upper()
        if "CPP_EXEMPT" in case_id_upper and "CPP2" not in case_id_upper:
            cpp_validation = validate_component(
                "CPP", result.cpp_total, Decimal("0.00"), VARIANCE_TOLERANCE
            )
            assert cpp_validation.passed, cpp_validation.message

        if "EI_EXEMPT" in case_id_upper:
            ei_validation = validate_component(
                "EI", result.ei_employee, Decimal("0.00"), VARIANCE_TOLERANCE
            )
            assert ei_validation.passed, ei_validation.message

        if "CPP2_EXEMPT" in case_id_upper:
            cpp2_validation = validate_component(
                "CPP2", result.cpp_additional, Decimal("0.00"), VARIANCE_TOLERANCE
            )
            assert cpp2_validation.passed, cpp2_validation.message

        # General validation
        validations = validate_all_components(result, case.pdoc_expected)
        assert_validations_pass(case_id, validations)


class TestTier4TaxableBenefits:
    """
    PDOC Validation: Taxable Benefits Tests

    Tests for taxable benefits added to income.
    Uses dynamic test discovery based on fixture data.
    """

    TIER = 4
    CATEGORY = "taxable_benefits"

    def test_taxable_benefits(self, dynamic_case):
        """
        Test taxable benefits increase taxable income.

        Taxable benefits:
        - Add to taxable income for tax purposes
        - May affect pensionable/insurable earnings
        - Interact with tax credits (BC tax reduction)
        """
        year, edition, case_id = dynamic_case

        engine = PayrollEngine(year=year)
        case = get_case_by_id(TIER, case_id, year, edition)

        input_data = build_payroll_input(case)
        result = engine.calculate(input_data)

        validations = validate_all_components(result, case.pdoc_expected)
        assert_validations_pass(case_id, validations)


class TestTier4PayFrequency:
    """
    PDOC Validation: Pay Frequency Tests

    Tests for different pay frequencies (weekly, semi-monthly, monthly).
    Uses dynamic test discovery based on fixture data.
    """

    TIER = 4
    CATEGORY = "pay_frequency"

    def test_pay_frequency(self, dynamic_case):
        """Test different pay frequency calculations."""
        year, edition, case_id = dynamic_case

        engine = PayrollEngine(year=year)
        case = get_case_by_id(TIER, case_id, year, edition)

        input_data = build_payroll_input(case)
        result = engine.calculate(input_data)

        validations = validate_all_components(result, case.pdoc_expected)
        assert_validations_pass(case_id, validations)


class TestTier4K5PCredit:
    """
    PDOC Validation: K5P Credit Tests (Alberta)

    Tests for Alberta's K5P supplemental credit.
    Uses dynamic test discovery based on fixture data.
    """

    TIER = 4
    CATEGORY = "k5p_credit"

    def test_k5p_credit(self, dynamic_case):
        """Test Alberta K5P credit calculation."""
        year, edition, case_id = dynamic_case

        engine = PayrollEngine(year=year)
        case = get_case_by_id(TIER, case_id, year, edition)

        input_data = build_payroll_input(case)
        result = engine.calculate(input_data)

        validations = validate_all_components(result, case.pdoc_expected)
        assert_validations_pass(case_id, validations)


class TestTier4Combined:
    """
    PDOC Validation: Combined Deductions Tests

    Tests for multiple deductions combined.
    Uses dynamic test discovery based on fixture data.
    """

    TIER = 4
    CATEGORY = "combined"

    def test_combined_deductions(self, dynamic_case):
        """Test combined deduction scenarios."""
        year, edition, case_id = dynamic_case

        engine = PayrollEngine(year=year)
        case = get_case_by_id(TIER, case_id, year, edition)

        input_data = build_payroll_input(case)
        result = engine.calculate(input_data)

        validations = validate_all_components(result, case.pdoc_expected)
        assert_validations_pass(case_id, validations)


class TestTier4DataIntegrity:
    """Tests to ensure Tier 4 fixture data is valid."""

    def test_has_special_condition_cases(self):
        """Verify special condition test cases exist."""
        cases = load_tier_cases(TIER)

        rrsp_cases = [c for c in cases if c.category == "rrsp"]
        union_cases = [c for c in cases if c.category == "union_dues"]
        [c for c in cases if c.category == "exemptions"]
        [c for c in cases if c.category == "taxable_benefits"]

        assert len(rrsp_cases) >= 1, f"Expected at least 1 RRSP case, got {len(rrsp_cases)}"
        assert len(union_cases) >= 1, f"Expected at least 1 union dues case, got {len(union_cases)}"

    def test_verified_cases_count(self):
        """Report number of verified cases."""
        verified_ids = get_verified_case_ids(TIER)
        total = len(load_tier_cases(TIER))
        print(f"\nTier 4: {len(verified_ids)}/{total} cases verified")
        assert True
