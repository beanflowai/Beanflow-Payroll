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

TIER = 3


class TestTier3CPP2Calculations:
    """
    PDOC Validation: CPP2 (Second Additional CPP) Tests

    CPP2 applies to pensionable earnings between YMPE and YAMPE.
    Rate: 4% (employee portion)
    Uses dynamic test discovery based on fixture data.
    """

    TIER = 3
    CATEGORY = "cpp2"

    def test_cpp2_calculation(self, dynamic_case):
        """
        Test CPP2 calculation at various income levels.

        Verifies:
        - CPP2 starts above YMPE ($71,300)
        - CPP2 maxes at YAMPE ($81,200)
        - Correct CPP2 rate application
        """
        year, edition, case_id = dynamic_case

        engine = PayrollEngine(year=year)
        case = get_case_by_id(TIER, case_id, year, edition)

        input_data = build_payroll_input(case)
        result = engine.calculate(input_data)

        validations = validate_all_components(result, case.pdoc_expected)
        assert_validations_pass(case_id, validations)


class TestTier3EIBoundary:
    """
    PDOC Validation: EI Boundary Tests

    Tests EI at maximum insurable earnings threshold.
    Uses dynamic test discovery based on fixture data.
    """

    TIER = 3
    CATEGORY = "ei_boundary"

    def test_ei_at_mie_threshold(self, dynamic_case):
        """Test EI at Maximum Insurable Earnings threshold."""
        year, edition, case_id = dynamic_case

        engine = PayrollEngine(year=year)
        case = get_case_by_id(TIER, case_id, year, edition)

        input_data = build_payroll_input(case)
        result = engine.calculate(input_data)

        validations = validate_all_components(result, case.pdoc_expected)
        assert_validations_pass(case_id, validations)


class TestTier3YTDMaximums:
    """
    PDOC Validation: YTD Near Maximum Tests

    Tests partial CPP/EI deductions when YTD is near annual maximum.
    Uses dynamic test discovery based on fixture data.
    """

    TIER = 3
    CATEGORY = "ytd_max"

    def test_ytd_near_max(self, dynamic_case):
        """
        Test partial deductions when YTD is near maximum.

        Scenarios:
        - YTD CPP near $4,034.10 max
        - YTD EI near $1,077.48 max
        - All contributions maxed (zero deductions)
        """
        year, edition, case_id = dynamic_case

        engine = PayrollEngine(year=year)
        case = get_case_by_id(TIER, case_id, year, edition)

        input_data = build_payroll_input(case)
        result = engine.calculate(input_data)

        validations = validate_all_components(result, case.pdoc_expected)
        assert_validations_pass(case_id, validations)


class TestTier3K2EffectivePeriods:
    """
    PDOC Validation: K2 Effective Periods Tests

    Tests the K2 P-1 logic when CPP/EI reaches maximum in current period.
    When (ytd_cpp_base + cpp_per_period) >= max_cpp_credit, the K2 tax
    credit calculation uses P-1 periods instead of P periods.
    Uses dynamic test discovery based on fixture data.
    """

    TIER = 3
    CATEGORY = "k2_periods"

    def test_cpp_reaches_max_triggers_k2_logic(self, dynamic_case):
        """
        Test K2 P-1 logic when CPP reaches max in current period.

        This scenario:
        - YTD CPP base: $3,900 (near max of $4,034.10)
        - Current period CPP: $134.10 (exactly fills to max)
        - This triggers effective_periods = P - 1 for K2 calculation

        Note: Using slightly relaxed tolerance ($1.00) for tax components due to
        input parameter differences between PDOC collection and fixture values.
        """
        year, edition, case_id = dynamic_case

        engine = PayrollEngine(year=year)
        case = get_case_by_id(TIER, case_id, year, edition)

        input_data = build_payroll_input(case)
        result = engine.calculate(input_data)

        # Use relaxed tolerance for K2 test due to YTD input adjustments
        k2_tolerance = Decimal("1.00")

        # Validate all components match PDOC with relaxed tolerance for tax
        validations = validate_all_components(
            result, case.pdoc_expected, tolerance=k2_tolerance
        )
        assert_validations_pass(case_id, validations)

        # Specifically verify CPP reaches exactly the max (strict tolerance)
        if "cpp_total" in case.pdoc_expected:
            cpp_validation = validate_component(
                "CPP Base", result.cpp_base, Decimal(case.pdoc_expected["cpp_total"])
            )
            assert cpp_validation.passed, (
                f"CPP should be exactly {case.pdoc_expected['cpp_total']} to reach annual max"
            )


class TestTier3Exemptions:
    """
    PDOC Validation: CPP/EI Exemption Tests (Tier 3)

    Tests for CPP, EI, and CPP2 exempt employees in boundary scenarios.
    Uses dynamic test discovery based on fixture data.
    """

    TIER = 3
    CATEGORY = "exemptions"

    def test_exemption(self, dynamic_case):
        """Test exemption scenarios."""
        year, edition, case_id = dynamic_case

        engine = PayrollEngine(year=year)
        case = get_case_by_id(TIER, case_id, year, edition)

        input_data = build_payroll_input(case)
        result = engine.calculate(input_data)

        validations = validate_all_components(result, case.pdoc_expected)
        assert_validations_pass(case_id, validations)


class TestTier3DataIntegrity:
    """Tests to ensure Tier 3 fixture data is valid."""

    def test_has_boundary_test_cases(self):
        """Verify CPP/EI boundary test cases exist."""
        cases = load_tier_cases(TIER)

        cpp2_cases = [c for c in cases if c.category == "cpp2"]
        ei_boundary_cases = [c for c in cases if c.category == "ei_boundary"]
        ytd_cases = [c for c in cases if c.category == "ytd_max"]
        k2_cases = [c for c in cases if c.category == "k2_periods"]

        assert len(cpp2_cases) >= 2, f"Expected at least 2 CPP2 boundary cases, got {len(cpp2_cases)}"
        assert len(ei_boundary_cases) >= 1, f"Expected at least 1 EI boundary case, got {len(ei_boundary_cases)}"

    def test_verified_cases_count(self):
        """Report number of verified cases."""
        verified_ids = get_verified_case_ids(TIER)
        total = len(load_tier_cases(TIER))
        print(f"\nTier 3: {len(verified_ids)}/{total} cases verified")
        assert True
