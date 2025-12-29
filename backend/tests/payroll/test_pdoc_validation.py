"""
PDOC Validation Tests - Phase 3

Validates BeanFlow Payroll calculations against CRA's Payroll Deductions
Online Calculator (PDOC) to ensure compliance with Canadian tax regulations.

Reference: CRA T4127 Payroll Deductions Formulas (121st Edition)
PDOC URL: https://www.canada.ca/en/revenue-agency/services/e-services/digital-services-businesses/payroll-deductions-online-calculator.html
"""

from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest

from app.models.payroll import PayFrequency, Province
from app.services.payroll.payroll_engine import EmployeePayrollInput, PayrollEngine


# Load PDOC test data
FIXTURES_DIR = Path(__file__).parent / "fixtures"
PDOC_DATA_FILE = FIXTURES_DIR / "pdoc_test_data.json"


def load_pdoc_test_cases() -> list[dict]:
    """Load PDOC validation test cases from JSON."""
    if not PDOC_DATA_FILE.exists():
        pytest.skip("PDOC test data file not found")

    with open(PDOC_DATA_FILE) as f:
        data = json.load(f)

    return data.get("test_cases", [])


def get_verified_cases() -> list[dict]:
    """Get only test cases that have been verified with PDOC."""
    cases = load_pdoc_test_cases()
    return [
        case for case in cases
        if case["pdoc_expected"].get("federal_tax") != "TO_BE_VERIFIED"
    ]


class TestPDOCValidation:
    """
    Validate BeanFlow calculations against CRA PDOC.

    Tolerance: $0.05 per component (strict tolerance for high accuracy)

    Test cases are loaded from fixtures/pdoc_test_data.json which contains
    actual values collected from PDOC.

    Note: Actual variance is typically $0.00-$0.02, so $0.05 provides
    reasonable buffer while catching any significant calculation errors.
    """

    VARIANCE_TOLERANCE = Decimal("0.05")  # $0.05 max variance per component

    def setup_method(self):
        """Initialize PayrollEngine for tests."""
        self.engine = PayrollEngine(year=2025)

    def _parse_date(self, date_str: str):
        """Parse date string to date object."""
        return datetime.strptime(date_str, "%Y-%m-%d").date()

    def _get_pay_frequency(self, freq_str: str) -> PayFrequency:
        """Convert string to PayFrequency enum."""
        mapping = {
            "weekly": PayFrequency.WEEKLY,
            "biweekly": PayFrequency.BIWEEKLY,
            "semimonthly": PayFrequency.SEMI_MONTHLY,
            "monthly": PayFrequency.MONTHLY,
        }
        return mapping.get(freq_str.lower(), PayFrequency.BIWEEKLY)

    def _build_input(self, case: dict) -> EmployeePayrollInput:
        """Build EmployeePayrollInput from test case data."""
        inp = case["input"]
        return EmployeePayrollInput(
            employee_id=f"pdoc_{case['id'].lower()}",
            province=Province[inp["province"]],
            pay_frequency=self._get_pay_frequency(inp["pay_frequency"]),
            pay_date=self._parse_date(inp["pay_date"]),
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
        )

    def _assert_within_tolerance(
        self, name: str, our_value: Decimal, pdoc_value: Decimal
    ) -> tuple[bool, str]:
        """Check if our value is within tolerance of PDOC value."""
        variance = abs(our_value - pdoc_value)
        passed = variance <= self.VARIANCE_TOLERANCE
        message = (
            f"{name}: Our={our_value:.2f}, PDOC={pdoc_value:.2f}, "
            f"Variance={variance:.2f} {'PASS' if passed else 'FAIL'}"
        )
        return passed, message

    # =========================================================================
    # Verified Test Cases
    # =========================================================================

    def test_ontario_60k_biweekly(self):
        """
        PDOC Validation: Ontario $60k annual, bi-weekly, YTD=$0

        This is the primary validation case with verified PDOC data.
        Pay date: 2025-07-18 (post July 1, federal rate 14%)

        Expected from PDOC:
        - CPP: $129.30
        - EI: $37.85
        - Federal Tax: $210.07
        - Provincial Tax: $116.76
        - Net Pay: $1,813.71
        """
        cases = load_pdoc_test_cases()
        case = next((c for c in cases if c["id"] == "ON_60K_BIWEEKLY"), None)
        if not case:
            pytest.skip("Test case ON_60K_BIWEEKLY not found in fixtures")

        expected = case["pdoc_expected"]
        if expected.get("federal_tax") == "TO_BE_VERIFIED":
            pytest.skip("Test case ON_60K_BIWEEKLY not yet verified with PDOC")

        # Run calculation
        input_data = self._build_input(case)
        result = self.engine.calculate(input_data)

        # Collect all validations
        validations = []
        failures = []

        # CPP total (base + enhancement)
        pdoc_cpp = Decimal(expected["cpp_total"])
        passed, msg = self._assert_within_tolerance("CPP", result.cpp_total, pdoc_cpp)
        validations.append(msg)
        if not passed:
            failures.append(msg)

        # EI
        pdoc_ei = Decimal(expected["ei"])
        passed, msg = self._assert_within_tolerance("EI", result.ei_employee, pdoc_ei)
        validations.append(msg)
        if not passed:
            failures.append(msg)

        # Federal Tax
        pdoc_fed = Decimal(expected["federal_tax"])
        passed, msg = self._assert_within_tolerance(
            "Federal Tax", result.federal_tax, pdoc_fed
        )
        validations.append(msg)
        if not passed:
            failures.append(msg)

        # Provincial Tax
        pdoc_prov = Decimal(expected["provincial_tax"])
        passed, msg = self._assert_within_tolerance(
            "Provincial Tax", result.provincial_tax, pdoc_prov
        )
        validations.append(msg)
        if not passed:
            failures.append(msg)

        # Net Pay
        pdoc_net = Decimal(expected["net_pay"])
        passed, msg = self._assert_within_tolerance("Net Pay", result.net_pay, pdoc_net)
        validations.append(msg)
        if not passed:
            failures.append(msg)

        # Print all validation results for visibility
        print("\n" + "=" * 60)
        print(f"PDOC Validation: {case['id']}")
        print(f"Description: {case['description']}")
        print("=" * 60)
        for v in validations:
            print(f"  {v}")
        print("=" * 60)

        # Assert no failures
        assert not failures, (
            f"PDOC validation failed for {case['id']}:\n" + "\n".join(failures)
        )

    # =========================================================================
    # Parametrized Tests for All Verified Cases
    # =========================================================================

    @pytest.mark.parametrize(
        "case_id",
        [
            "ON_60K_BIWEEKLY",
            # Add more case IDs as they are verified:
            # "ON_60K_BIWEEKLY_JAN",
            # "AB_120K_MONTHLY",
            # "BC_39K_BIWEEKLY",
            # "NS_26K_BIWEEKLY",
        ],
    )
    def test_pdoc_case(self, case_id: str):
        """
        Parametrized PDOC validation for all verified cases.

        Each case compares:
        - CPP total (base + enhancement)
        - EI employee contribution
        - Federal tax
        - Provincial tax
        - Net pay

        All within $1.00 tolerance.
        """
        cases = load_pdoc_test_cases()
        case = next((c for c in cases if c["id"] == case_id), None)

        if not case:
            pytest.skip(f"Test case {case_id} not found in fixtures")

        expected = case["pdoc_expected"]
        if expected.get("federal_tax") == "TO_BE_VERIFIED":
            pytest.skip(f"Test case {case_id} not yet verified with PDOC")

        # Run calculation
        input_data = self._build_input(case)
        result = self.engine.calculate(input_data)

        # Validate all components
        validations = [
            ("CPP", result.cpp_total, Decimal(expected["cpp_total"])),
            ("EI", result.ei_employee, Decimal(expected["ei"])),
            ("Federal Tax", result.federal_tax, Decimal(expected["federal_tax"])),
            ("Provincial Tax", result.provincial_tax, Decimal(expected["provincial_tax"])),
            ("Net Pay", result.net_pay, Decimal(expected["net_pay"])),
        ]

        failures = []
        print(f"\n--- {case_id} Validation ---")
        for name, our_value, pdoc_value in validations:
            passed, message = self._assert_within_tolerance(name, our_value, pdoc_value)
            print(f"  {message}")
            if not passed:
                failures.append(message)

        assert not failures, (
            f"PDOC validation failed for {case_id}:\n" + "\n".join(failures)
        )

    # =========================================================================
    # Detailed Component Tests
    # =========================================================================

    def test_cpp_breakdown_ontario_60k(self):
        """
        Test CPP calculation breakdown for Ontario $60k case.

        PDOC shows:
        - CPP deductions: $129.30 (total)
        - CPP additional contribution (F2): $21.73 (for tax deduction)
        - CPP2: $0.00 (not applicable, below YAMPE)

        Our calculation:
        - Pensionable earnings: $2,307.69
        - Basic exemption per period: $3,500/26 = $134.62
        - Pensionable above exemption: $2,173.07
        - CPP at 5.95%: $2,173.07 * 0.0595 = $129.30
        - F2 (enhancement at 1%): $2,173.07 * 0.01 = $21.73
        """
        cases = load_pdoc_test_cases()
        case = next((c for c in cases if c["id"] == "ON_60K_BIWEEKLY"), None)
        if not case:
            pytest.skip("Test case not found")

        expected = case["pdoc_expected"]
        if expected.get("cpp_total") == "TO_BE_VERIFIED":
            pytest.skip("Test case not verified")

        input_data = self._build_input(case)
        result = self.engine.calculate(input_data)

        # CPP total should match
        pdoc_cpp_total = Decimal(expected["cpp_total"])
        assert abs(result.cpp_total - pdoc_cpp_total) <= self.VARIANCE_TOLERANCE, (
            f"CPP total mismatch: Our={result.cpp_total}, PDOC={pdoc_cpp_total}"
        )

        # CPP2 should be 0 (below YAMPE)
        pdoc_cpp2 = Decimal(expected.get("cpp2", "0"))
        assert result.cpp_additional == pdoc_cpp2, (
            f"CPP2 mismatch: Our={result.cpp_additional}, PDOC={pdoc_cpp2}"
        )

        # Verify calculation details
        details = result.calculation_details.get("cpp", {})
        print(f"\nCPP Breakdown:")
        print(f"  Pensionable earnings: {details.get('pensionable_earnings')}")
        print(f"  Base CPP: {details.get('base')}")
        print(f"  Enhancement (F2): {details.get('enhancement')}")
        print(f"  Additional (CPP2): {details.get('additional')}")
        print(f"  Total CPP: {details.get('total')}")

    def test_ei_calculation_ontario_60k(self):
        """
        Test EI calculation for Ontario $60k case.

        PDOC shows: EI = $37.85

        Our calculation:
        - Insurable earnings: $2,307.69
        - EI rate: 1.64%
        - EI: $2,307.69 * 0.0164 = $37.85
        """
        cases = load_pdoc_test_cases()
        case = next((c for c in cases if c["id"] == "ON_60K_BIWEEKLY"), None)
        if not case:
            pytest.skip("Test case not found")

        expected = case["pdoc_expected"]
        if expected.get("ei") == "TO_BE_VERIFIED":
            pytest.skip("Test case not verified")

        input_data = self._build_input(case)
        result = self.engine.calculate(input_data)

        pdoc_ei = Decimal(expected["ei"])
        assert abs(result.ei_employee - pdoc_ei) <= self.VARIANCE_TOLERANCE, (
            f"EI mismatch: Our={result.ei_employee}, PDOC={pdoc_ei}"
        )

    def test_federal_tax_ontario_60k(self):
        """
        Test federal tax calculation for Ontario $60k case.

        Pay date: 2025-07-18 (post July 1, federal rate is 14%)

        PDOC shows:
        - Taxable income for pay period: $2,285.96
        - Federal tax: $210.07

        Tax reduction from gross:
        - Gross: $2,307.69
        - CPP enhancement (F2): $21.73
        - Taxable: $2,307.69 - $21.73 = $2,285.96
        """
        cases = load_pdoc_test_cases()
        case = next((c for c in cases if c["id"] == "ON_60K_BIWEEKLY"), None)
        if not case:
            pytest.skip("Test case not found")

        expected = case["pdoc_expected"]
        if expected.get("federal_tax") == "TO_BE_VERIFIED":
            pytest.skip("Test case not verified")

        input_data = self._build_input(case)
        result = self.engine.calculate(input_data)

        pdoc_fed = Decimal(expected["federal_tax"])
        variance = abs(result.federal_tax - pdoc_fed)

        print(f"\nFederal Tax Breakdown:")
        details = result.calculation_details.get("federal_tax", {})
        print(f"  Annual taxable income: {details.get('annual_taxable_income')}")
        print(f"  Tax rate: {details.get('tax_rate')}")
        print(f"  K1 (personal credits): {details.get('K1_personal_credits')}")
        print(f"  K2 (CPP/EI credits): {details.get('K2_cpp_ei_credits')}")
        print(f"  T3 (basic federal tax): {details.get('T3_basic_tax')}")
        print(f"  T1 (annual federal tax): {details.get('T1_annual_tax')}")
        print(f"  Tax per period: {details.get('tax_per_period')}")
        print(f"  PDOC expected: {pdoc_fed}")
        print(f"  Variance: {variance}")

        assert variance <= self.VARIANCE_TOLERANCE, (
            f"Federal tax variance {variance} exceeds tolerance. "
            f"Our: {result.federal_tax}, PDOC: {pdoc_fed}"
        )

    def test_provincial_tax_ontario_60k(self):
        """
        Test provincial tax calculation for Ontario $60k case.

        PDOC shows: Provincial tax = $116.76
        """
        cases = load_pdoc_test_cases()
        case = next((c for c in cases if c["id"] == "ON_60K_BIWEEKLY"), None)
        if not case:
            pytest.skip("Test case not found")

        expected = case["pdoc_expected"]
        if expected.get("provincial_tax") == "TO_BE_VERIFIED":
            pytest.skip("Test case not verified")

        input_data = self._build_input(case)
        result = self.engine.calculate(input_data)

        pdoc_prov = Decimal(expected["provincial_tax"])
        variance = abs(result.provincial_tax - pdoc_prov)

        print(f"\nProvincial Tax Breakdown:")
        details = result.calculation_details.get("provincial_tax", {})
        print(f"  Province: {details.get('province')}")
        print(f"  Annual taxable income: {details.get('annual_taxable_income')}")
        print(f"  Tax rate: {details.get('tax_rate')}")
        print(f"  K1P (personal credits): {details.get('K1P_personal_credits')}")
        print(f"  K2P (CPP/EI credits): {details.get('K2P_cpp_ei_credits')}")
        print(f"  T4 (basic provincial tax): {details.get('T4_basic_tax')}")
        print(f"  V1 (surtax): {details.get('V1_surtax')}")
        print(f"  V2 (health premium): {details.get('V2_health_premium')}")
        print(f"  S (tax reduction): {details.get('S_tax_reduction')}")
        print(f"  T2 (annual provincial tax): {details.get('T2_annual_tax')}")
        print(f"  Tax per period: {details.get('tax_per_period')}")
        print(f"  PDOC expected: {pdoc_prov}")
        print(f"  Variance: {variance}")

        assert variance <= self.VARIANCE_TOLERANCE, (
            f"Provincial tax variance {variance} exceeds tolerance. "
            f"Our: {result.provincial_tax}, PDOC: {pdoc_prov}"
        )


class TestPDOCDataIntegrity:
    """Tests to ensure PDOC fixture data is valid and complete."""

    def test_fixture_file_exists(self):
        """Verify PDOC test data file exists."""
        assert PDOC_DATA_FILE.exists(), f"Missing fixture file: {PDOC_DATA_FILE}"

    def test_fixture_file_valid_json(self):
        """Verify fixture file is valid JSON."""
        with open(PDOC_DATA_FILE) as f:
            data = json.load(f)
        assert "test_cases" in data
        assert len(data["test_cases"]) > 0

    def test_verified_cases_exist(self):
        """Verify at least one PDOC-verified case exists."""
        verified = get_verified_cases()
        assert len(verified) > 0, "No verified PDOC test cases found"

    def test_required_fields_present(self):
        """Verify all test cases have required fields."""
        cases = load_pdoc_test_cases()
        required_input = [
            "province", "gross_pay", "pay_frequency", "pay_date",
            "federal_claim", "provincial_claim"
        ]
        required_expected = ["cpp_total", "ei", "federal_tax", "provincial_tax"]

        for case in cases:
            for field in required_input:
                assert field in case["input"], (
                    f"Missing input field '{field}' in case {case['id']}"
                )
            for field in required_expected:
                assert field in case["pdoc_expected"], (
                    f"Missing expected field '{field}' in case {case['id']}"
                )
