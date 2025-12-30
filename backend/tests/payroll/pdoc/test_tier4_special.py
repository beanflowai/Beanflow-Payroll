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

import pytest

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
    """

    @pytest.fixture(autouse=True)
    def setup(self, payroll_engine):
        """Set up PayrollEngine for tests."""
        self.engine = payroll_engine

    @pytest.mark.parametrize(
        "case_id",
        [
            "ON_60K_RRSP",   # Standard RRSP $500/period
            "AB_80K_RRSP",   # High RRSP $1000/period
        ],
    )
    def test_rrsp_deduction(self, case_id: str):
        """
        Test RRSP reduces taxable income and taxes.

        RRSP contributions:
        - Reduce taxable income for federal tax
        - Reduce taxable income for provincial tax
        - Do NOT affect CPP/EI contributions
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


class TestTier4UnionDues:
    """
    PDOC Validation: Union Dues Tests

    Union dues affect tax calculation.
    """

    @pytest.fixture(autouse=True)
    def setup(self, payroll_engine):
        """Set up PayrollEngine for tests."""
        self.engine = payroll_engine

    def test_union_dues_credit(self):
        """Test union dues provide tax credit."""
        case = get_case_by_id(TIER, "ON_60K_UNION")
        if not case:
            pytest.skip("Test case ON_60K_UNION not found")

        if not case.is_verified:
            pytest.skip("Test case not yet verified with PDOC")

        input_data = build_payroll_input(case)
        result = self.engine.calculate(input_data)

        validations = validate_all_components(result, case.pdoc_expected)
        assert_validations_pass("ON_60K_UNION", validations)


class TestTier4Exemptions:
    """
    PDOC Validation: Exemption Tests

    Tests for CPP, EI, and CPP2 exempt employees.
    """

    @pytest.fixture(autouse=True)
    def setup(self, payroll_engine):
        """Set up PayrollEngine for tests."""
        self.engine = payroll_engine

    def test_cpp_exempt(self):
        """Test CPP exempt employee has zero CPP contribution."""
        case = get_case_by_id(TIER, "ON_60K_CPP_EXEMPT")
        if not case:
            pytest.skip("Test case ON_60K_CPP_EXEMPT not found")

        if not case.is_verified:
            pytest.skip("Test case not yet verified with PDOC")

        input_data = build_payroll_input(case)
        result = self.engine.calculate(input_data)

        # CPP should be zero
        cpp_validation = validate_component(
            "CPP", result.cpp_total, Decimal("0.00"), VARIANCE_TOLERANCE
        )
        assert cpp_validation.passed, cpp_validation.message

        # Other validations
        validations = validate_all_components(result, case.pdoc_expected)
        assert_validations_pass("ON_60K_CPP_EXEMPT", validations)

    def test_ei_exempt(self):
        """Test EI exempt employee has zero EI contribution."""
        case = get_case_by_id(TIER, "ON_60K_EI_EXEMPT")
        if not case:
            pytest.skip("Test case ON_60K_EI_EXEMPT not found")

        if not case.is_verified:
            pytest.skip("Test case not yet verified with PDOC")

        input_data = build_payroll_input(case)
        result = self.engine.calculate(input_data)

        # EI should be zero
        ei_validation = validate_component(
            "EI", result.ei_employee, Decimal("0.00"), VARIANCE_TOLERANCE
        )
        assert ei_validation.passed, ei_validation.message

        # Other validations
        validations = validate_all_components(result, case.pdoc_expected)
        assert_validations_pass("ON_60K_EI_EXEMPT", validations)

    def test_cpp2_exempt(self):
        """Test CPP2 exempt employee has zero CPP2 contribution."""
        case = get_case_by_id(TIER, "ON_100K_CPP2_EXEMPT")
        if not case:
            pytest.skip("Test case ON_100K_CPP2_EXEMPT not found")

        if not case.is_verified:
            pytest.skip("Test case not yet verified with PDOC")

        input_data = build_payroll_input(case)
        result = self.engine.calculate(input_data)

        # CPP2 (additional) should be zero, but base CPP should still apply
        cpp2_validation = validate_component(
            "CPP2", result.cpp_additional, Decimal("0.00"), VARIANCE_TOLERANCE
        )
        assert cpp2_validation.passed, cpp2_validation.message


class TestTier4TaxableBenefits:
    """
    PDOC Validation: Taxable Benefits Tests

    Tests for taxable benefits added to income.
    """

    @pytest.fixture(autouse=True)
    def setup(self, payroll_engine):
        """Set up PayrollEngine for tests."""
        self.engine = payroll_engine

    @pytest.mark.parametrize(
        "case_id",
        [
            "ON_60K_BENEFITS",   # Standard taxable benefits
            "BC_40K_BENEFITS",   # Benefits + BC tax reduction
        ],
    )
    def test_taxable_benefits(self, case_id: str):
        """
        Test taxable benefits increase taxable income.

        Taxable benefits:
        - Add to taxable income for tax purposes
        - May affect pensionable/insurable earnings
        - Interact with tax credits (BC tax reduction)
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


class TestTier4DataIntegrity:
    """Tests to ensure Tier 4 fixture data is valid."""

    def test_has_special_condition_cases(self):
        """Verify special condition test cases exist."""
        cases = load_tier_cases(TIER)

        rrsp_cases = [c for c in cases if "RRSP" in c.id]
        union_cases = [c for c in cases if "UNION" in c.id]
        exempt_cases = [c for c in cases if "EXEMPT" in c.id]
        benefits_cases = [c for c in cases if "BENEFITS" in c.id]

        assert len(rrsp_cases) >= 2, "Expected at least 2 RRSP cases"
        assert len(union_cases) >= 1, "Expected at least 1 union dues case"
        assert len(exempt_cases) >= 3, "Expected at least 3 exemption cases"
        assert len(benefits_cases) >= 2, "Expected at least 2 taxable benefits cases"

    def test_verified_cases_count(self):
        """Report number of verified cases."""
        verified_ids = get_verified_case_ids(TIER)
        total = len(load_tier_cases(TIER))
        print(f"\nTier 4: {len(verified_ids)}/{total} cases verified")
        assert True
