"""
Holiday Pay Validation Test Fixtures and Utilities

Shared fixtures and helper functions for Holiday Pay validation tests.
Similar structure to PDOC tests for consistency.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

# =============================================================================
# Constants
# =============================================================================

FIXTURES_BASE_DIR = Path(__file__).parent / "fixtures"
VARIANCE_TOLERANCE = Decimal("0.01")  # $0.01 max variance
DEFAULT_YEAR = 2025
VALID_PROVINCES = frozenset([
    "ON", "BC", "AB", "SK", "MB", "QC",
    "NB", "NS", "PE", "NL", "NT", "NU", "YT", "Federal"
])


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class HolidayPayTestCase:
    """Represents a single Holiday Pay test case."""

    id: str
    tier: int
    description: str
    status: str  # "VERIFIED", "PENDING"
    category: str
    input: dict[str, Any]
    expected: dict[str, Any]
    official_source: str
    verification_date: str | None = None
    notes: str = ""

    @property
    def is_verified(self) -> bool:
        """Check if test case has been verified with official calculator."""
        return self.status == "VERIFIED"

    @classmethod
    def from_dict(cls, data: dict) -> HolidayPayTestCase:
        """Create HolidayPayTestCase from dictionary."""
        return cls(
            id=data["id"],
            tier=data.get("tier", 1),
            description=data["description"],
            status=data.get("status", "PENDING"),
            category=data.get("category", "standard"),
            input=data["input"],
            expected=data["expected"],
            official_source=data.get("official_source", ""),
            verification_date=data.get("verification_date"),
            notes=data.get("notes", ""),
        )


@dataclass
class ValidationResult:
    """Result of a single component validation."""

    name: str
    our_value: Decimal
    expected_value: Decimal
    variance: Decimal
    passed: bool

    @property
    def message(self) -> str:
        """Format result as string."""
        status = "PASS" if self.passed else "FAIL"
        return (
            f"{self.name}: Our={self.our_value:.2f}, "
            f"Expected={self.expected_value:.2f}, Variance={self.variance:.2f} {status}"
        )


# =============================================================================
# Fixture Loading
# =============================================================================


def load_tier_fixture(tier: int, year: int = DEFAULT_YEAR) -> dict:
    """Load fixture data for a specific tier and year.

    Args:
        tier: Test tier (1-4)
        year: Tax year (default: 2025)

    Returns:
        Dictionary containing fixture data
    """
    tier_files = {
        1: "tier1_major_provinces.json",
        2: "tier2_atlantic.json",
        3: "tier3_territories.json",
        4: "tier4_edge_cases.json",
    }

    filename = tier_files.get(tier)
    if not filename:
        raise ValueError(f"Invalid tier: {tier}")

    filepath = FIXTURES_BASE_DIR / str(year) / filename
    if filepath.exists():
        with open(filepath) as f:
            return json.load(f)

    pytest.skip(f"Fixture file not found: {filepath}")


def load_tier_cases(tier: int, year: int = DEFAULT_YEAR) -> list[HolidayPayTestCase]:
    """Load all test cases for a specific tier and year."""
    data = load_tier_fixture(tier, year)
    return [HolidayPayTestCase.from_dict(case) for case in data.get("test_cases", [])]


def get_verified_cases(tier: int, year: int = DEFAULT_YEAR) -> list[HolidayPayTestCase]:
    """Get only verified test cases for a tier and year."""
    cases = load_tier_cases(tier, year)
    return [case for case in cases if case.is_verified]


def get_case_by_id(
    tier: int,
    case_id: str,
    year: int = DEFAULT_YEAR,
) -> HolidayPayTestCase | None:
    """Get a specific test case by ID."""
    cases = load_tier_cases(tier, year)
    return next((c for c in cases if c.id == case_id), None)


def get_cases_by_province(
    tier: int,
    province: str,
    year: int = DEFAULT_YEAR,
) -> list[HolidayPayTestCase]:
    """Get verified test cases filtered by province.

    Args:
        tier: Test tier (1-4)
        province: Province code (e.g., "SK", "ON")
        year: Tax year

    Returns:
        List of verified test cases for the province
    """
    cases = load_tier_cases(tier, year)
    return [
        c for c in cases
        if c.input.get("province") == province and c.is_verified
    ]


def get_cases_by_category(
    tier: int,
    category: str,
    year: int = DEFAULT_YEAR,
) -> list[HolidayPayTestCase]:
    """Get verified test cases filtered by category.

    Args:
        tier: Test tier (1-4)
        category: Category (e.g., "low_hours", "new_employee")
        year: Tax year

    Returns:
        List of verified test cases matching the category
    """
    cases = load_tier_cases(tier, year)
    return [c for c in cases if c.category == category and c.is_verified]


# =============================================================================
# Input Building
# =============================================================================


def build_employee_data(case: HolidayPayTestCase) -> dict[str, Any]:
    """Build employee data dict from test case input.

    Args:
        case: Test case with input data

    Returns:
        Employee dict suitable for HolidayPayCalculator
    """
    inp = case.input
    return {
        "id": f"test_{case.id.lower()}",
        "first_name": "Test",
        "last_name": case.id,
        "hourly_rate": inp.get("hourly_rate"),
        "salary": inp.get("salary"),
        "hire_date": inp.get("hire_date"),
    }


def build_historical_earnings(case: HolidayPayTestCase) -> dict[str, Decimal]:
    """Build historical earnings data from test case.

    Args:
        case: Test case with input data

    Returns:
        Dict with wages, vacation_pay, holiday_pay for lookback period
    """
    inp = case.input
    return {
        # SK formula (28-day lookback)
        "wages_past_28_days": Decimal(str(inp.get("wages_past_28_days", "0"))),
        "vacation_pay_past_28_days": Decimal(str(inp.get("vacation_pay_past_28_days", "0"))),
        "holiday_pay_past_28_days": Decimal(str(inp.get("holiday_pay_past_28_days", "0"))),
        "hours_worked_past_28_days": Decimal(str(inp.get("hours_worked_past_28_days", "0"))),
        # ON formula (4-week lookback)
        "wages_past_4_weeks": Decimal(str(inp.get("wages_past_4_weeks", "0"))),
        "vacation_pay_past_4_weeks": Decimal(str(inp.get("vacation_pay_past_4_weeks", "0"))),
        "days_worked_past_4_weeks": Decimal(str(inp.get("days_worked_past_4_weeks", "0"))),
        # BC/other formula (30-day lookback)
        "wages_past_30_days": Decimal(str(inp.get("wages_past_30_days", "0"))),
        "days_worked_past_30_days": Decimal(str(inp.get("days_worked_past_30_days", "0"))),
        # Current period (for new employee fallback)
        "current_period_gross": Decimal(str(inp.get("current_period_gross", "0"))),
    }


def build_premium_pay_data(case: HolidayPayTestCase) -> dict[str, Any]:
    """Build premium pay (worked on holiday) data from test case.

    Args:
        case: Test case with input data

    Returns:
        Dict with hours worked on holiday and calculated premium
    """
    inp = case.input
    hourly_rate = Decimal(str(inp.get("hourly_rate", "0")))
    hours_worked = Decimal(str(inp.get("hours_worked_on_holiday", "0")))
    premium_rate = Decimal("1.5")  # Standard premium rate

    return {
        "hours_worked_on_holiday": hours_worked,
        "hourly_rate": hourly_rate,
        "premium_rate": premium_rate,
        "calculated_premium": hours_worked * hourly_rate * premium_rate,
    }


def get_expected_values(case: HolidayPayTestCase) -> dict[str, Decimal]:
    """Extract expected values from test case.

    Args:
        case: Test case with expected data

    Returns:
        Dict with expected regular, premium, and total holiday pay
    """
    expected = case.expected
    return {
        "regular_holiday_pay": Decimal(str(expected.get("regular_holiday_pay", "0"))),
        "premium_holiday_pay": Decimal(str(expected.get("premium_holiday_pay", "0"))),
        "total_holiday_pay": Decimal(str(expected.get("total_holiday_pay", "0"))),
    }


# =============================================================================
# Validation Helpers
# =============================================================================


def validate_component(
    name: str,
    our_value: Decimal,
    expected_value: Decimal,
    tolerance: Decimal = VARIANCE_TOLERANCE,
) -> ValidationResult:
    """Validate a single component against expected value."""
    variance = abs(our_value - expected_value)
    passed = variance <= tolerance
    return ValidationResult(
        name=name,
        our_value=our_value,
        expected_value=expected_value,
        variance=variance,
        passed=passed,
    )


def validate_holiday_pay(
    result_pay: Decimal,
    expected: dict[str, Any],
    tolerance: Decimal = VARIANCE_TOLERANCE,
) -> list[ValidationResult]:
    """Validate holiday pay result against expected values.

    Args:
        result_pay: Calculated regular holiday pay
        expected: Dict with expected values
        tolerance: Max allowed variance

    Returns:
        List of validation results
    """
    validations = []

    if "regular_holiday_pay" in expected:
        validations.append(
            validate_component(
                "Regular Holiday Pay",
                result_pay,
                Decimal(str(expected["regular_holiday_pay"])),
                tolerance,
            )
        )

    return validations


def assert_validations_pass(
    case_id: str,
    validations: list[ValidationResult],
    print_results: bool = True,
) -> None:
    """Assert all validations pass, with optional result printing."""
    if print_results:
        print(f"\n--- {case_id} Validation ---")
        for v in validations:
            print(f"  {v.message}")

    failures = [v for v in validations if not v.passed]
    if failures:
        failure_messages = [v.message for v in failures]
        raise AssertionError(
            f"Holiday Pay validation failed for {case_id}:\n" + "\n".join(failure_messages)
        )


# =============================================================================
# Pytest Fixtures
# =============================================================================


@pytest.fixture
def tier1_cases():
    """Load Tier 1 (major provinces) test cases."""
    return load_tier_cases(1)


@pytest.fixture
def tier2_cases():
    """Load Tier 2 (Atlantic) test cases."""
    return load_tier_cases(2)


@pytest.fixture
def tier3_cases():
    """Load Tier 3 (territories) test cases."""
    return load_tier_cases(3)


@pytest.fixture
def tier4_cases():
    """Load Tier 4 (edge cases) test cases."""
    return load_tier_cases(4)


# =============================================================================
# Dynamic Test Parametrization
# =============================================================================


# Year combinations to test
YEAR_COMBINATIONS = [2025]


def pytest_generate_tests(metafunc):
    """Dynamically generate test parameters based on fixture data.

    Test classes should define:
        TIER: int - The tier number (1-4)
        PROVINCE: str - The province code (e.g., "SK")

    And use `dynamic_case` as a fixture parameter.
    """
    if "dynamic_case" not in metafunc.fixturenames:
        return

    cls = metafunc.cls
    if cls is None or not hasattr(cls, "TIER") or not hasattr(cls, "PROVINCE"):
        return

    tier = cls.TIER
    province = cls.PROVINCE

    params = []
    ids = []

    for year in YEAR_COMBINATIONS:
        try:
            cases = get_cases_by_province(tier, province, year)
            for case in cases:
                params.append((year, case.id))
                ids.append(f"{year}-{case.id}")
        except Exception:
            continue

    if params:
        metafunc.parametrize("dynamic_case", params, ids=ids)
    else:
        metafunc.parametrize(
            "dynamic_case",
            [pytest.param(None, marks=pytest.mark.skip(
                reason=f"No cases for tier={tier}, province={province}"
            ))],
            ids=["no_cases"],
        )
