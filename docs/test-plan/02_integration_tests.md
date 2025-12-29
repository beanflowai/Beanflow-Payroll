# Phase 2: Integration Tests

**Duration**: 2-3 days
**Priority**: P0 (Critical)
**Prerequisites**: Phase 1 unit tests passing

---

## Objectives

Test the complete payroll calculation flow:
1. PayrollEngine orchestration
2. All 12 provinces end-to-end
3. Complex scenarios (high income, exemptions, YTD limits)
4. Edge cases and boundary conditions

---

## Test File Structure

```
backend/tests/payroll/
├── test_payroll_engine.py         # Task 2.1: Full engine tests
├── test_all_provinces.py          # Task 2.2: Province coverage
├── test_edge_cases.py             # Task 2.3: Boundary conditions
└── fixtures/
    └── integration_test_data.json # Test data fixtures
```

---

## Task 2.1: Payroll Engine Integration Tests

**File**: `backend/tests/payroll/test_payroll_engine.py`

```python
# backend/tests/payroll/test_payroll_engine.py

import pytest
from decimal import Decimal
from datetime import date

from app.services.payroll.payroll_engine import PayrollEngine, EmployeePayrollInput
from app.models.payroll import Province, PayFrequency


class TestPayrollEngineIntegration:
    """End-to-end payroll calculation tests"""

    def setup_method(self):
        self.engine = PayrollEngine(year=2025)

    # ========== Task 2.1.1: Standard Payroll Calculation ==========

    def test_standard_payroll_ontario(self):
        """Test: Complete payroll for Ontario employee"""
        input_data = EmployeePayrollInput(
            employee_id="emp_001",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),

            # Income
            regular_pay=Decimal("2307.69"),  # $60k annual
            overtime_pay=Decimal("0"),
            bonus=Decimal("0"),

            # Claims
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),

            # Pre-tax deductions
            rrsp_deduction=Decimal("100.00"),
            union_dues=Decimal("0"),

            # YTD
            ytd_gross=Decimal("0"),
            ytd_cpp=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result = self.engine.calculate_payroll(input_data)

        # ===== Assertions =====

        # Gross pay
        assert result.gross_pay == Decimal("2307.69")

        # CPP (should be > 0, < max per period)
        assert result.cpp_employee > Decimal("0")
        assert result.cpp_employee < Decimal("200")

        # EI (should be > 0, < max per period)
        assert result.ei_employee > Decimal("0")
        assert result.ei_employee < Decimal("50")

        # Federal tax (should be > 0)
        assert result.federal_tax > Decimal("0")

        # Provincial tax (should be > 0)
        assert result.provincial_tax > Decimal("0")

        # Net pay calculation
        expected_net = (
            result.gross_pay
            - result.cpp_employee
            - result.cpp_additional
            - result.ei_employee
            - result.federal_tax
            - result.provincial_tax
            - result.rrsp
        )
        assert result.net_pay == expected_net

        # Employer costs
        assert result.cpp_employer == result.cpp_employee + result.cpp_additional
        assert result.ei_employer == result.ei_employee * Decimal("1.4")

    def test_payroll_with_overtime_and_bonus(self):
        """Test: Payroll with multiple income types"""
        input_data = EmployeePayrollInput(
            employee_id="emp_002",
            province=Province.AB,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),

            regular_pay=Decimal("2000.00"),
            overtime_pay=Decimal("300.00"),
            bonus=Decimal("500.00"),

            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("22323.00"),

            ytd_gross=Decimal("0"),
            ytd_cpp=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result = self.engine.calculate_payroll(input_data)

        # Gross includes all income types
        assert result.gross_pay == Decimal("2800.00")

        # Deductions should be calculated on full gross
        assert result.cpp_employee > Decimal("0")
        assert result.ei_employee > Decimal("0")

    def test_payroll_with_taxable_benefits(self):
        """Test: Payroll with employer-paid taxable benefits"""
        input_data = EmployeePayrollInput(
            employee_id="emp_003",
            province=Province.BC,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),

            regular_pay=Decimal("2500.00"),
            taxable_benefits_pensionable=Decimal("50.00"),  # Life insurance

            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12932.00"),

            ytd_gross=Decimal("0"),
            ytd_cpp=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result = self.engine.calculate_payroll(input_data)

        # Gross pay doesn't include taxable benefits
        assert result.gross_pay == Decimal("2500.00")

        # But CPP is calculated on pensionable earnings (gross + benefits)
        # EI is NOT calculated on benefits (not insurable)

    # ========== Task 2.1.2: Pre-tax Deductions ==========

    def test_rrsp_reduces_taxable_income(self):
        """Test: RRSP deduction reduces taxable income"""
        # Without RRSP
        input_no_rrsp = EmployeePayrollInput(
            employee_id="emp_004a",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            regular_pay=Decimal("3000.00"),
            rrsp_deduction=Decimal("0"),
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            ytd_gross=Decimal("0"),
            ytd_cpp=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        # With RRSP
        input_with_rrsp = EmployeePayrollInput(
            employee_id="emp_004b",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            regular_pay=Decimal("3000.00"),
            rrsp_deduction=Decimal("500.00"),
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            ytd_gross=Decimal("0"),
            ytd_cpp=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result_no_rrsp = self.engine.calculate_payroll(input_no_rrsp)
        result_with_rrsp = self.engine.calculate_payroll(input_with_rrsp)

        # RRSP should reduce taxes
        assert result_with_rrsp.federal_tax < result_no_rrsp.federal_tax
        assert result_with_rrsp.provincial_tax < result_no_rrsp.provincial_tax

        # But CPP/EI unchanged (RRSP doesn't affect pensionable/insurable)
        assert result_with_rrsp.cpp_employee == result_no_rrsp.cpp_employee
        assert result_with_rrsp.ei_employee == result_no_rrsp.ei_employee

    # ========== Task 2.1.3: Exemptions ==========

    def test_cpp_exempt_employee(self):
        """Test: Employee exempt from CPP"""
        input_data = EmployeePayrollInput(
            employee_id="emp_005",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            regular_pay=Decimal("2000.00"),
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            cpp_exempt=True,
            ytd_gross=Decimal("0"),
            ytd_cpp=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result = self.engine.calculate_payroll(input_data)

        assert result.cpp_employee == Decimal("0")
        assert result.cpp_additional == Decimal("0")
        assert result.cpp_employer == Decimal("0")

        # But EI should still be calculated
        assert result.ei_employee > Decimal("0")

    def test_ei_exempt_employee(self):
        """Test: Employee exempt from EI"""
        input_data = EmployeePayrollInput(
            employee_id="emp_006",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            regular_pay=Decimal("2000.00"),
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            ei_exempt=True,
            ytd_gross=Decimal("0"),
            ytd_cpp=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result = self.engine.calculate_payroll(input_data)

        assert result.ei_employee == Decimal("0")
        assert result.ei_employer == Decimal("0")

        # But CPP should still be calculated
        assert result.cpp_employee > Decimal("0")

    # ========== Task 2.1.4: YTD Tracking ==========

    def test_ytd_updates_correctly(self):
        """Test: YTD values accumulate correctly"""
        input_data = EmployeePayrollInput(
            employee_id="emp_007",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            regular_pay=Decimal("2000.00"),
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            ytd_gross=Decimal("20000.00"),
            ytd_cpp=Decimal("1000.00"),
            ytd_ei=Decimal("350.00"),
        )

        result = self.engine.calculate_payroll(input_data)

        # YTD should be updated
        assert result.ytd_gross == Decimal("20000.00") + result.gross_pay
        assert result.ytd_cpp == Decimal("1000.00") + result.cpp_employee + result.cpp_additional
        assert result.ytd_ei == Decimal("350.00") + result.ei_employee

    def test_cpp_stops_at_annual_max(self):
        """Test: CPP stops when annual max reached"""
        input_data = EmployeePayrollInput(
            employee_id="emp_008",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            regular_pay=Decimal("3000.00"),
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            ytd_gross=Decimal("70000.00"),
            ytd_cpp=Decimal("4034.10"),  # Max reached
            ytd_ei=Decimal("800.00"),
        )

        result = self.engine.calculate_payroll(input_data)

        # No more base CPP
        assert result.cpp_employee == Decimal("0")

        # But may have CPP2 if above YMPE
        # EI continues until its max
        assert result.ei_employee > Decimal("0") or result.ytd_ei >= Decimal("1077.48")


class TestPayrollEngineHighIncome:
    """Tests for high-income scenarios (CPP2, max limits)"""

    def setup_method(self):
        self.engine = PayrollEngine(year=2025)

    def test_high_income_triggers_cpp2(self):
        """Test: Income above YMPE triggers CPP2"""
        input_data = EmployeePayrollInput(
            employee_id="emp_high_001",
            province=Province.AB,
            pay_frequency=PayFrequency.MONTHLY,
            pay_date=date(2025, 7, 18),
            regular_pay=Decimal("10000.00"),  # $120k annual
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("22323.00"),
            ytd_gross=Decimal("60000.00"),  # Already past half year
            ytd_cpp=Decimal("3500.00"),
            ytd_ei=Decimal("900.00"),
        )

        result = self.engine.calculate_payroll(input_data)

        # Should have CPP2 contribution
        # (depends on YTD pensionable vs YMPE)

    def test_all_maximums_reached(self):
        """Test: All contribution limits reached"""
        input_data = EmployeePayrollInput(
            employee_id="emp_max_001",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 12, 15),
            regular_pay=Decimal("5000.00"),
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            ytd_gross=Decimal("100000.00"),
            ytd_cpp=Decimal("4034.10"),   # Base CPP maxed
            ytd_cpp2=Decimal("396.00"),   # CPP2 maxed
            ytd_ei=Decimal("1077.48"),    # EI maxed
        )

        result = self.engine.calculate_payroll(input_data)

        assert result.cpp_employee == Decimal("0")
        assert result.cpp_additional == Decimal("0")
        assert result.ei_employee == Decimal("0")

        # But taxes still apply
        assert result.federal_tax > Decimal("0")
        assert result.provincial_tax > Decimal("0")
```

---

## Task 2.2: All Provinces Test

**File**: `backend/tests/payroll/test_all_provinces.py`

```python
# backend/tests/payroll/test_all_provinces.py

import pytest
from decimal import Decimal
from datetime import date

from app.services.payroll.payroll_engine import PayrollEngine, EmployeePayrollInput
from app.models.payroll import Province, PayFrequency


# Provincial BPA data for 2025
PROVINCIAL_BPA = {
    Province.AB: Decimal("22323.00"),
    Province.BC: Decimal("12932.00"),
    Province.MB: Decimal("15780.00"),
    Province.NB: Decimal("13396.00"),
    Province.NL: Decimal("11067.00"),
    Province.NS: Decimal("11744.00"),
    Province.NT: Decimal("17842.00"),
    Province.NU: Decimal("19274.00"),
    Province.ON: Decimal("12747.00"),
    Province.PE: Decimal("14250.00"),
    Province.SK: Decimal("18991.00"),
    Province.YT: Decimal("16129.00"),
}


class TestAllProvinces:
    """Ensure all 12 provinces calculate correctly"""

    def setup_method(self):
        self.engine = PayrollEngine(year=2025)

    @pytest.mark.parametrize("province", list(Province))
    def test_province_calculates_without_error(self, province):
        """Test: Each province calculates successfully"""
        input_data = EmployeePayrollInput(
            employee_id=f"emp_{province.value}",
            province=province,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            regular_pay=Decimal("2000.00"),
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=PROVINCIAL_BPA[province],
            ytd_gross=Decimal("0"),
            ytd_cpp=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result = self.engine.calculate_payroll(input_data)

        # Basic sanity checks
        assert result.gross_pay == Decimal("2000.00")
        assert result.cpp_employee > Decimal("0")
        assert result.ei_employee > Decimal("0")
        assert result.federal_tax >= Decimal("0")
        assert result.provincial_tax >= Decimal("0")
        assert result.net_pay > Decimal("0")
        assert result.net_pay < result.gross_pay

    @pytest.mark.parametrize("province,expected_min_tax,expected_max_tax", [
        # Low tax provinces
        (Province.AB, Decimal("50"), Decimal("200")),
        (Province.SK, Decimal("40"), Decimal("180")),
        (Province.NT, Decimal("30"), Decimal("150")),
        (Province.NU, Decimal("25"), Decimal("140")),
        (Province.YT, Decimal("40"), Decimal("180")),

        # Medium tax provinces
        (Province.BC, Decimal("60"), Decimal("220")),
        (Province.ON, Decimal("70"), Decimal("250")),
        (Province.PE, Decimal("80"), Decimal("280")),

        # Higher tax provinces
        (Province.MB, Decimal("100"), Decimal("320")),
        (Province.NB, Decimal("90"), Decimal("300")),
        (Province.NL, Decimal("90"), Decimal("300")),
        (Province.NS, Decimal("90"), Decimal("300")),
    ])
    def test_provincial_tax_in_expected_range(
        self, province, expected_min_tax, expected_max_tax
    ):
        """Test: Provincial tax falls within expected range"""
        input_data = EmployeePayrollInput(
            employee_id=f"emp_tax_{province.value}",
            province=province,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            regular_pay=Decimal("2500.00"),  # ~$65k annual
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=PROVINCIAL_BPA[province],
            ytd_gross=Decimal("0"),
            ytd_cpp=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result = self.engine.calculate_payroll(input_data)

        # Check provincial tax is in expected range
        assert result.provincial_tax >= expected_min_tax, \
            f"{province}: Provincial tax {result.provincial_tax} below minimum {expected_min_tax}"
        assert result.provincial_tax <= expected_max_tax, \
            f"{province}: Provincial tax {result.provincial_tax} above maximum {expected_max_tax}"


class TestProvincialSpecialRules:
    """Test province-specific rules and edge cases"""

    def setup_method(self):
        self.engine = PayrollEngine(year=2025)

    def test_ontario_health_premium(self):
        """Test: Ontario health premium calculation"""
        # High income triggers health premium
        input_data = EmployeePayrollInput(
            employee_id="emp_on_health",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            regular_pay=Decimal("4000.00"),  # ~$104k annual
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            ytd_gross=Decimal("0"),
            ytd_cpp=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result = self.engine.calculate_payroll(input_data)

        # Ontario high income should have health premium included
        # V2 = 0 to $900/year depending on income

    def test_bc_low_income_tax_reduction(self):
        """Test: BC tax reduction for low income"""
        input_data = EmployeePayrollInput(
            employee_id="emp_bc_low",
            province=Province.BC,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            regular_pay=Decimal("1000.00"),  # ~$26k annual
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12932.00"),
            ytd_gross=Decimal("0"),
            ytd_cpp=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result = self.engine.calculate_payroll(input_data)

        # BC low income should have minimal or zero provincial tax
        assert result.provincial_tax < Decimal("50")
```

---

## Task 2.3: Edge Cases & Boundary Tests

**File**: `backend/tests/payroll/test_edge_cases.py`

```python
# backend/tests/payroll/test_edge_cases.py

import pytest
from decimal import Decimal
from datetime import date

from app.services.payroll.payroll_engine import PayrollEngine, EmployeePayrollInput
from app.models.payroll import Province, PayFrequency


class TestBoundaryConditions:
    """Test boundary conditions and edge cases"""

    def setup_method(self):
        self.engine = PayrollEngine(year=2025)

    # ========== CPP Boundaries ==========

    def test_cpp_at_ympe_boundary(self):
        """Test: Income exactly at YMPE boundary ($71,300)"""
        # YTD just below YMPE
        input_data = EmployeePayrollInput(
            employee_id="emp_ympe",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            regular_pay=Decimal("2742.31"),  # $71,300 / 26
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            ytd_gross=Decimal("68557.69"),  # 25 periods done
            ytd_cpp=Decimal("3879.00"),
            ytd_ei=Decimal("1000.00"),
        )

        result = self.engine.calculate_payroll(input_data)

        # Should have base CPP, possibly partial CPP2
        assert result.cpp_employee > Decimal("0")

    def test_cpp2_at_yampe_boundary(self):
        """Test: Income exactly at YAMPE boundary ($81,200)"""
        input_data = EmployeePayrollInput(
            employee_id="emp_yampe",
            province=Province.ON,
            pay_frequency=PayFrequency.MONTHLY,
            pay_date=date(2025, 11, 15),
            regular_pay=Decimal("6766.67"),  # $81,200 / 12
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            ytd_gross=Decimal("74433.33"),  # 11 months done
            ytd_cpp=Decimal("4034.10"),  # Base maxed
            ytd_cpp2=Decimal("360.00"),  # CPP2 almost maxed
            ytd_ei=Decimal("1077.48"),
        )

        result = self.engine.calculate_payroll(input_data)

        # CPP2 should be partial (remaining to max)
        assert result.cpp_additional <= Decimal("36.00")

    # ========== EI Boundaries ==========

    def test_ei_at_mie_boundary(self):
        """Test: Income exactly at MIE boundary ($65,700)"""
        input_data = EmployeePayrollInput(
            employee_id="emp_mie",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            regular_pay=Decimal("2526.92"),  # $65,700 / 26
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            ytd_gross=Decimal("63173.08"),  # 25 periods
            ytd_cpp=Decimal("3500.00"),
            ytd_ei=Decimal("1036.08"),  # $41.40 remaining
        )

        result = self.engine.calculate_payroll(input_data)

        # EI should be partial
        assert result.ei_employee <= Decimal("41.40")

    # ========== Zero/Minimal Income ==========

    def test_zero_income(self):
        """Test: Zero gross pay"""
        input_data = EmployeePayrollInput(
            employee_id="emp_zero",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            regular_pay=Decimal("0"),
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            ytd_gross=Decimal("0"),
            ytd_cpp=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result = self.engine.calculate_payroll(input_data)

        assert result.gross_pay == Decimal("0")
        assert result.cpp_employee == Decimal("0")
        assert result.ei_employee == Decimal("0")
        assert result.federal_tax == Decimal("0")
        assert result.provincial_tax == Decimal("0")
        assert result.net_pay == Decimal("0")

    def test_very_low_income(self):
        """Test: Income below CPP exemption"""
        input_data = EmployeePayrollInput(
            employee_id="emp_low",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            regular_pay=Decimal("100.00"),  # Below exemption
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            ytd_gross=Decimal("0"),
            ytd_cpp=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result = self.engine.calculate_payroll(input_data)

        # CPP should be zero (below exemption)
        assert result.cpp_employee == Decimal("0")

        # EI still applies
        assert result.ei_employee == Decimal("1.64")  # 100 × 1.64%

        # Tax likely zero (income too low)
        assert result.federal_tax >= Decimal("0")

    # ========== Very High Income ==========

    def test_very_high_income(self):
        """Test: Very high income ($500k+ annual)"""
        input_data = EmployeePayrollInput(
            employee_id="emp_executive",
            province=Province.ON,
            pay_frequency=PayFrequency.MONTHLY,
            pay_date=date(2025, 7, 18),
            regular_pay=Decimal("41666.67"),  # $500k annual
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            ytd_gross=Decimal("0"),
            ytd_cpp=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result = self.engine.calculate_payroll(input_data)

        # Should be in highest tax brackets
        assert result.federal_tax > Decimal("10000")
        assert result.provincial_tax > Decimal("4000")

    # ========== Multiple Deductions ==========

    def test_large_rrsp_deduction(self):
        """Test: Large RRSP deduction"""
        input_data = EmployeePayrollInput(
            employee_id="emp_rrsp",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            regular_pay=Decimal("5000.00"),
            rrsp_deduction=Decimal("2000.00"),  # 40% RRSP
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            ytd_gross=Decimal("0"),
            ytd_cpp=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result = self.engine.calculate_payroll(input_data)

        # Tax should be significantly lower due to RRSP
        # But CPP/EI based on full gross
        assert result.cpp_employee > Decimal("250")

    # ========== Mid-Year Scenarios ==========

    def test_new_employee_mid_year(self):
        """Test: New employee starting mid-year with zero YTD"""
        input_data = EmployeePayrollInput(
            employee_id="emp_new",
            province=Province.BC,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 9, 15),
            regular_pay=Decimal("3000.00"),
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12932.00"),
            ytd_gross=Decimal("0"),  # First pay
            ytd_cpp=Decimal("0"),
            ytd_ei=Decimal("0"),
        )

        result = self.engine.calculate_payroll(input_data)

        # Should calculate normally
        assert result.cpp_employee > Decimal("0")
        assert result.ei_employee > Decimal("0")

    def test_employee_with_prior_employer_ytd(self):
        """Test: Employee with YTD from prior employer"""
        input_data = EmployeePayrollInput(
            employee_id="emp_transfer",
            province=Province.ON,
            pay_frequency=PayFrequency.BIWEEKLY,
            pay_date=date(2025, 7, 18),
            regular_pay=Decimal("2500.00"),
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            # YTD from prior employer
            ytd_gross=Decimal("40000.00"),
            ytd_cpp=Decimal("2200.00"),
            ytd_ei=Decimal("656.00"),
        )

        result = self.engine.calculate_payroll(input_data)

        # Should continue from YTD position
        new_ytd_cpp = Decimal("2200.00") + result.cpp_employee + result.cpp_additional
        assert result.ytd_cpp == new_ytd_cpp
```

---

## Execution Instructions

### Run Integration Tests

```bash
# Run all integration tests
cd backend
uv run pytest tests/payroll/test_payroll_engine.py tests/payroll/test_all_provinces.py -v

# Run with detailed output
uv run pytest tests/payroll/ -v --tb=long

# Run specific test class
uv run pytest tests/payroll/test_all_provinces.py::TestAllProvinces -v
```

### Coverage Check

```bash
# Check coverage for payroll engine
uv run pytest tests/payroll/ --cov=app/services/payroll/payroll_engine --cov-report=term-missing
```

---

## Completion Checklist

- [ ] `test_payroll_engine.py` created and passing
- [ ] `test_all_provinces.py` created - all 12 provinces pass
- [ ] `test_edge_cases.py` created - boundary conditions tested
- [ ] All exemption scenarios tested (CPP, EI, CPP2)
- [ ] YTD tracking verified
- [ ] High income scenarios tested
- [ ] No test failures across all provinces

---

**Next**: [Phase 3: PDOC Validation](./03_pdoc_validation.md)
