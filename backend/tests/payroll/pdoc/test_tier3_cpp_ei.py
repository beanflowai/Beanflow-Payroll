"""
Tier 3: CPP/EI Boundary Tests

Tests CPP and EI contribution maximums and CPP2 calculations.

2025 Limits:
- YMPE (CPP base ceiling): $71,300
- YAMPE (CPP2 ceiling): $81,200
- EI MIE (Maximum Insurable Earnings): $65,700
- CPP base max contribution: $4,034.10
- CPP2 max contribution: $396.00
- EI max contribution: $1,077.48

Coverage:
- CPP2 start: Just above YMPE ($71,300)
- CPP2 ceiling: Above YAMPE ($81,200)
- EI maximum: At EI MIE threshold
- YTD near max: Partial deductions
- All maxed: Zero CPP/EI deductions
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

TIER = 3


class TestTier3CPP2Calculations:
    """
    PDOC Validation: CPP2 (Second Additional CPP) Tests

    CPP2 applies to pensionable earnings between YMPE and YAMPE.
    Rate: 4% (employee portion)
    """

    @pytest.fixture(autouse=True)
    def setup(self, payroll_engine):
        """Set up PayrollEngine for tests."""
        self.engine = payroll_engine

    @pytest.mark.parametrize(
        "case_id",
        [
            "ON_72K_BIWEEKLY",  # Just above YMPE, CPP2 starts
            "ON_82K_BIWEEKLY",  # Above YAMPE, CPP2 at ceiling
            "AB_85K_CPP2",      # Alberta CPP2 verification
            "BC_90K_CPP2_TAX_REDUCTION",  # CPP2 + BC tax reduction
        ],
    )
    def test_cpp2_calculation(self, case_id: str):
        """
        Test CPP2 calculation at various income levels.

        Verifies:
        - CPP2 starts above YMPE ($71,300)
        - CPP2 maxes at YAMPE ($81,200)
        - Correct CPP2 rate application
        """
        case = get_case_by_id(TIER, case_id)
        if not case:
            pytest.skip(f"Test case {case_id} not found in fixtures")

        if not case.is_verified:
            pytest.skip(f"Test case {case_id} not yet verified with PDOC")

        input_data = build_payroll_input(case)
        result = self.engine.calculate(input_data)

        validations = validate_all_components(result, case.pdoc_expected)
        assert_validations_pass(case_id, validations)


class TestTier3EIBoundary:
    """
    PDOC Validation: EI Boundary Tests

    Tests EI at maximum insurable earnings threshold.
    """

    @pytest.fixture(autouse=True)
    def setup(self, payroll_engine):
        """Set up PayrollEngine for tests."""
        self.engine = payroll_engine

    def test_ei_at_mie_threshold(self):
        """Test EI at Maximum Insurable Earnings threshold."""
        case = get_case_by_id(TIER, "ON_66K_BIWEEKLY")
        if not case:
            pytest.skip("Test case ON_66K_BIWEEKLY not found")

        if not case.is_verified:
            pytest.skip("Test case not yet verified with PDOC")

        input_data = build_payroll_input(case)
        result = self.engine.calculate(input_data)

        validations = validate_all_components(result, case.pdoc_expected)
        assert_validations_pass("ON_66K_BIWEEKLY", validations)


class TestTier3YTDMaximums:
    """
    PDOC Validation: YTD Near Maximum Tests

    Tests partial CPP/EI deductions when YTD is near annual maximum.
    """

    @pytest.fixture(autouse=True)
    def setup(self, payroll_engine):
        """Set up PayrollEngine for tests."""
        self.engine = payroll_engine

    @pytest.mark.parametrize(
        "case_id",
        [
            "ON_80K_YTD_CPP_NEAR_MAX",
            "ON_70K_YTD_EI_NEAR_MAX",
        ],
    )
    def test_ytd_near_max(self, case_id: str):
        """
        Test partial deductions when YTD is near maximum.

        Scenarios:
        - YTD CPP near $4,034.10 max
        - YTD EI near $1,077.48 max
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

    def test_all_contributions_maxed(self):
        """Test zero CPP/EI when all contributions are maxed."""
        case = get_case_by_id(TIER, "ON_100K_ALL_MAXED")
        if not case:
            pytest.skip("Test case ON_100K_ALL_MAXED not found")

        if not case.is_verified:
            pytest.skip("Test case not yet verified with PDOC")

        input_data = build_payroll_input(case)
        result = self.engine.calculate(input_data)

        # CPP and EI should be zero when maxed
        cpp_validation = validate_component(
            "CPP", result.cpp_total, Decimal("0.00"), VARIANCE_TOLERANCE
        )
        ei_validation = validate_component(
            "EI", result.ei_employee, Decimal("0.00"), VARIANCE_TOLERANCE
        )

        assert cpp_validation.passed, cpp_validation.message
        assert ei_validation.passed, ei_validation.message


class TestTier3DataIntegrity:
    """Tests to ensure Tier 3 fixture data is valid."""

    def test_has_boundary_test_cases(self):
        """Verify CPP/EI boundary test cases exist."""
        cases = load_tier_cases(TIER)

        cpp2_cases = [c for c in cases if "CPP2" in c.id or "72K" in c.id or "82K" in c.id]
        ytd_cases = [c for c in cases if "YTD" in c.id]
        maxed_cases = [c for c in cases if "MAXED" in c.id]

        assert len(cpp2_cases) >= 3, "Expected at least 3 CPP2 boundary cases"
        assert len(ytd_cases) >= 2, "Expected at least 2 YTD cases"
        assert len(maxed_cases) >= 1, "Expected at least 1 all-maxed case"

    def test_verified_cases_count(self):
        """Report number of verified cases."""
        verified_ids = get_verified_case_ids(TIER)
        total = len(load_tier_cases(TIER))
        print(f"\nTier 3: {len(verified_ids)}/{total} cases verified")
        assert True
