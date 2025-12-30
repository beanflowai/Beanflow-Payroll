"""
PDOC Validation Test Fixtures and Utilities

Shared fixtures and helper functions for all PDOC validation tests.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from app.models.payroll import PayFrequency, Province
from app.services.payroll.payroll_engine import EmployeePayrollInput, PayrollEngine


# =============================================================================
# Constants
# =============================================================================

FIXTURES_BASE_DIR = Path(__file__).parent / "fixtures"
VARIANCE_TOLERANCE = Decimal("0.05")  # $0.05 max variance per component
DEFAULT_TAX_YEAR = 2025  # Default tax year for tests
DEFAULT_EDITION = "jul"  # Default edition (121st Edition, Jul+, 14% federal rate)
VALID_EDITIONS = frozenset(["jan", "jul"])  # Valid editions for tax year


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class PDOCTestCase:
    """Represents a single PDOC test case."""

    id: str
    tier: int
    description: str
    status: str
    input: dict[str, Any]
    pdoc_expected: dict[str, str]
    notes: str = ""

    @property
    def is_verified(self) -> bool:
        """Check if test case has been verified with PDOC."""
        return self.pdoc_expected.get("federal_tax") != "TO_BE_VERIFIED"

    @classmethod
    def from_dict(cls, data: dict) -> PDOCTestCase:
        """Create PDOCTestCase from dictionary."""
        return cls(
            id=data["id"],
            tier=data.get("tier", 1),
            description=data["description"],
            status=data.get("status", "PENDING"),
            input=data["input"],
            pdoc_expected=data["pdoc_expected"],
            notes=data.get("notes", ""),
        )


@dataclass
class ValidationResult:
    """Result of a single component validation."""

    name: str
    our_value: Decimal
    pdoc_value: Decimal
    variance: Decimal
    passed: bool

    @property
    def message(self) -> str:
        """Format result as string."""
        status = "PASS" if self.passed else "FAIL"
        return (
            f"{self.name}: Our={self.our_value:.2f}, "
            f"PDOC={self.pdoc_value:.2f}, Variance={self.variance:.2f} {status}"
        )


# =============================================================================
# Fixture Loading
# =============================================================================


def load_tier_fixture(
    tier: int,
    year: int = DEFAULT_TAX_YEAR,
    edition: str | None = None,
) -> dict:
    """Load fixture data for a specific tier, year, and edition.

    Args:
        tier: Test tier (1-5)
        year: Tax year (default: 2025)
        edition: Tax edition ("jan" for 120th/15%, "jul" for 121st/14%)
                 Defaults to DEFAULT_EDITION if not specified.

    Returns:
        Dictionary containing fixture data
    """
    tier_files = {
        1: "tier1_province_coverage.json",
        2: "tier2_income_levels.json",
        3: "tier3_cpp_ei_boundary.json",
        4: "tier4_special_conditions.json",
        5: "tier5_federal_rate_change.json",
    }

    filename = tier_files.get(tier)
    if not filename:
        raise ValueError(f"Invalid tier: {tier}")

    effective_edition = edition or DEFAULT_EDITION

    # Validate edition
    if effective_edition not in VALID_EDITIONS:
        raise ValueError(
            f"Invalid edition: {effective_edition}. Must be one of {VALID_EDITIONS}"
        )

    # Primary path: year/edition/filename
    filepath = FIXTURES_BASE_DIR / str(year) / effective_edition / filename
    if filepath.exists():
        with open(filepath) as f:
            return json.load(f)

    # Fallback path: year/filename (for backward compatibility during migration)
    fallback_path = FIXTURES_BASE_DIR / str(year) / filename
    if fallback_path.exists():
        with open(fallback_path) as f:
            return json.load(f)

    pytest.skip(f"Fixture file not found: {filepath}")


def load_tier_cases(
    tier: int,
    year: int = DEFAULT_TAX_YEAR,
    edition: str | None = None,
) -> list[PDOCTestCase]:
    """Load all test cases for a specific tier, year, and edition."""
    data = load_tier_fixture(tier, year, edition)
    return [PDOCTestCase.from_dict(case) for case in data.get("test_cases", [])]


def get_verified_cases(
    tier: int,
    year: int = DEFAULT_TAX_YEAR,
    edition: str | None = None,
) -> list[PDOCTestCase]:
    """Get only verified test cases for a tier, year, and edition."""
    cases = load_tier_cases(tier, year, edition)
    return [case for case in cases if case.is_verified]


def get_case_by_id(
    tier: int,
    case_id: str,
    year: int = DEFAULT_TAX_YEAR,
    edition: str | None = None,
) -> PDOCTestCase | None:
    """Get a specific test case by ID."""
    cases = load_tier_cases(tier, year, edition)
    return next((c for c in cases if c.id == case_id), None)


def get_all_case_ids(
    tier: int,
    year: int = DEFAULT_TAX_YEAR,
    edition: str | None = None,
) -> list[str]:
    """Get all case IDs for a tier, year, and edition."""
    cases = load_tier_cases(tier, year, edition)
    return [c.id for c in cases]


def get_verified_case_ids(
    tier: int,
    year: int = DEFAULT_TAX_YEAR,
    edition: str | None = None,
) -> list[str]:
    """Get only verified case IDs for a tier, year, and edition."""
    cases = get_verified_cases(tier, year, edition)
    return [c.id for c in cases]


# =============================================================================
# Input Building
# =============================================================================


def parse_date(date_str: str) -> datetime:
    """Parse date string to date object."""
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def get_pay_frequency(freq_str: str) -> PayFrequency:
    """Convert string to PayFrequency enum."""
    mapping = {
        "weekly": PayFrequency.WEEKLY,
        "biweekly": PayFrequency.BIWEEKLY,
        "semimonthly": PayFrequency.SEMI_MONTHLY,
        "monthly": PayFrequency.MONTHLY,
    }
    return mapping.get(freq_str.lower(), PayFrequency.BIWEEKLY)


def build_payroll_input(case: PDOCTestCase) -> EmployeePayrollInput:
    """Build EmployeePayrollInput from test case."""
    inp = case.input

    # Parse pensionable_months if provided (for prorated CPP max)
    pensionable_months = None
    if "pensionable_months" in inp:
        pensionable_months = int(inp["pensionable_months"])

    # Parse taxable benefits (used for both pensionable and insurable)
    taxable_benefits = Decimal(inp.get("taxable_benefits", "0"))

    return EmployeePayrollInput(
        employee_id=f"pdoc_{case.id.lower()}",
        province=Province[inp["province"]],
        pay_frequency=get_pay_frequency(inp["pay_frequency"]),
        pay_date=parse_date(inp["pay_date"]),
        gross_regular=Decimal(inp["gross_pay"]),
        federal_claim_amount=Decimal(inp["federal_claim"]),
        provincial_claim_amount=Decimal(inp["provincial_claim"]),
        rrsp_per_period=Decimal(inp.get("rrsp", "0")),
        union_dues_per_period=Decimal(inp.get("union_dues", "0")),
        ytd_gross=Decimal(inp.get("ytd_gross", "0")),
        ytd_pensionable_earnings=Decimal(inp.get("ytd_pensionable_earnings", "0")),
        ytd_insurable_earnings=Decimal(inp.get("ytd_insurable_earnings", "0")),
        ytd_cpp_base=Decimal(inp.get("ytd_cpp_base", "0")),
        ytd_cpp_additional=Decimal(inp.get("ytd_cpp_additional", "0")),
        ytd_ei=Decimal(inp.get("ytd_ei", "0")),
        pensionable_months=pensionable_months,
        # Exemption flags
        is_cpp_exempt=inp.get("cpp_exempt", False),
        is_ei_exempt=inp.get("ei_exempt", False),
        cpp2_exempt=inp.get("cpp2_exempt", False),
        # Taxable benefits (pensionable and insurable)
        taxable_benefits_pensionable=taxable_benefits,
        taxable_benefits_insurable=taxable_benefits,
    )


# =============================================================================
# Validation Helpers
# =============================================================================


def validate_component(
    name: str,
    our_value: Decimal,
    pdoc_value: Decimal,
    tolerance: Decimal = VARIANCE_TOLERANCE,
) -> ValidationResult:
    """Validate a single component against PDOC expected value."""
    variance = abs(our_value - pdoc_value)
    passed = variance <= tolerance
    return ValidationResult(
        name=name,
        our_value=our_value,
        pdoc_value=pdoc_value,
        variance=variance,
        passed=passed,
    )


def validate_all_components(
    result,
    expected: dict[str, str],
    tolerance: Decimal = VARIANCE_TOLERANCE,
) -> list[ValidationResult]:
    """Validate all standard components."""
    validations = []

    # CPP - PDOC shows base CPP and CPP2 separately
    if "cpp_total" in expected:
        if "cpp2" in expected:
            # PDOC lists CPP (base) and CPP2 separately
            # cpp_total in fixture = base CPP only
            validations.append(
                validate_component(
                    "CPP Base", result.cpp_base, Decimal(expected["cpp_total"]), tolerance
                )
            )
            validations.append(
                validate_component(
                    "CPP2", result.cpp_additional, Decimal(expected["cpp2"]), tolerance
                )
            )
        else:
            # No separate CPP2 - compare total
            validations.append(
                validate_component(
                    "CPP", result.cpp_total, Decimal(expected["cpp_total"]), tolerance
                )
            )

    # EI
    if "ei" in expected:
        validations.append(
            validate_component(
                "EI", result.ei_employee, Decimal(expected["ei"]), tolerance
            )
        )

    # Federal Tax
    if "federal_tax" in expected:
        validations.append(
            validate_component(
                "Federal Tax",
                result.federal_tax,
                Decimal(expected["federal_tax"]),
                tolerance,
            )
        )

    # Provincial Tax
    if "provincial_tax" in expected:
        validations.append(
            validate_component(
                "Provincial Tax",
                result.provincial_tax,
                Decimal(expected["provincial_tax"]),
                tolerance,
            )
        )

    # Net Pay
    if "net_pay" in expected:
        validations.append(
            validate_component(
                "Net Pay", result.net_pay, Decimal(expected["net_pay"]), tolerance
            )
        )

    return validations


def assert_validations_pass(
    case_id: str, validations: list[ValidationResult], print_results: bool = True
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
            f"PDOC validation failed for {case_id}:\n" + "\n".join(failure_messages)
        )


# =============================================================================
# Pytest Fixtures
# =============================================================================


@pytest.fixture(params=[2025, 2026])  # Multi-year testing
def tax_year(request):
    """Parameterized tax year fixture for multi-year testing."""
    return request.param


@pytest.fixture(params=["jan", "jul"])  # Both editions for multi-edition testing
def edition(request):
    """Parameterized edition fixture for multi-edition testing.

    Editions for 2025:
        jan: 120th Edition (Jan-Jun 2025, 15% federal rate)
        jul: 121st Edition (Jul+ 2025, 14% federal rate)

    Editions for 2026:
        jan: 122nd Edition (January 2026, 14% federal rate)
        jul: TBD (expected mid-2026)
    """
    return request.param


@pytest.fixture
def payroll_engine(tax_year):
    """Create PayrollEngine instance for tests with parameterized year."""
    return PayrollEngine(year=tax_year)


@pytest.fixture
def tier1_cases(tax_year, edition):
    """Load Tier 1 test cases for the current tax year and edition."""
    return load_tier_cases(1, tax_year, edition)


@pytest.fixture
def tier2_cases(tax_year, edition):
    """Load Tier 2 test cases for the current tax year and edition."""
    return load_tier_cases(2, tax_year, edition)


@pytest.fixture
def tier3_cases(tax_year, edition):
    """Load Tier 3 test cases for the current tax year and edition."""
    return load_tier_cases(3, tax_year, edition)


@pytest.fixture
def tier4_cases(tax_year, edition):
    """Load Tier 4 test cases for the current tax year and edition."""
    return load_tier_cases(4, tax_year, edition)


@pytest.fixture
def tier5_cases(tax_year, edition):
    """Load Tier 5 test cases for the current tax year and edition."""
    return load_tier_cases(5, tax_year, edition)
