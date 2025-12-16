# Phase 5: Testing & Validation

**Duration**: 1.5 weeks
**Complexity**: Medium
**Prerequisites**: Phase 1-4 completed

---

## 🎯 Objectives

Ensure payroll calculations are accurate and compliant with CRA standards.

### Deliverables
1. ✅ Unit tests for all calculators
2. ✅ Integration tests for payroll engine
3. ✅ Validation against CRA PDOC
4. ✅ Test data for all 12 provinces
5. ✅ Manual test plan

---

## 📦 Task 5.1: Unit Tests

### LLM Agent Prompt

```markdown
TASK: Create Unit Tests for Payroll Calculators

FILE TO CREATE:
backend/tests/payroll/test_cpp_calculator.py

REQUIREMENTS:

Write pytest tests for CPP calculator.

```python
import pytest
from decimal import Decimal
from app.services.payroll.cpp_calculator import CPPCalculator

class TestCPPCalculator:
    """Test CPP contribution calculations"""

    def setup_method(self):
        self.calc = CPPCalculator(pay_periods_per_year=26)  # Bi-weekly

    def test_base_cpp_low_income(self):
        """Test CPP for income below YMPE"""
        # $2000/period × 26 = $52,000 annual (below YMPE of $71,200)
        base_cpp, additional_cpp, total = self.calc.calculate_total_cpp(
            pensionable_earnings=Decimal("2000.00")
        )

        # Expected: (2000 - 3500/26) × 0.0595 = (2000 - 134.62) × 0.0595
        expected_base = round((Decimal("2000") - Decimal("3500")/26) * Decimal("0.0595"), 2)

        assert base_cpp == expected_base
        assert additional_cpp == Decimal("0")  # No CPP2 below YMPE
        assert total == base_cpp

    def test_cpp_above_ympe(self):
        """Test CPP for high income (above YMPE, has CPP2)"""
        # $3500/period × 26 = $91,000 annual (above YMPE)
        base_cpp, additional_cpp, total = self.calc.calculate_total_cpp(
            pensionable_earnings=Decimal("3500.00")
        )

        assert base_cpp > Decimal("0")
        assert additional_cpp > Decimal("0")  # Should have CPP2
        assert total == base_cpp + additional_cpp

    def test_cpp_max_contribution(self):
        """Test CPP stops at annual maximum"""
        # Simulate employee who already paid max CPP
        ytd_cpp = Decimal("3356.10")  # Max base CPP

        base_cpp, _, _ = self.calc.calculate_total_cpp(
            pensionable_earnings=Decimal("5000.00"),
            ytd_cpp=ytd_cpp
        )

        assert base_cpp == Decimal("0")  # No more CPP

    def test_employer_contribution_matches_employee(self):
        """Employer CPP = Employee CPP"""
        employee_cpp = Decimal("100.50")
        employer_cpp = self.calc.get_employer_contribution(employee_cpp)

        assert employer_cpp == employee_cpp

    @pytest.mark.parametrize("pay_periods,gross,expected_min", [
        (52, Decimal("1000"), Decimal("40")),    # Weekly
        (26, Decimal("2000"), Decimal("80")),    # Bi-weekly
        (12, Decimal("5000"), Decimal("200")),   # Monthly
    ])
    def test_different_pay_frequencies(self, pay_periods, gross, expected_min):
        """Test CPP with different pay frequencies"""
        calc = CPPCalculator(pay_periods_per_year=pay_periods)
        base_cpp, _, _ = calc.calculate_total_cpp(gross)

        assert base_cpp >= expected_min
```

FILE TO CREATE:
backend/tests/payroll/test_federal_tax_calculator.py

```python
import pytest
from decimal import Decimal
from app.services.payroll.federal_tax_calculator import FederalTaxCalculator

class TestFederalTaxCalculator:
    """Test federal income tax calculations"""

    def setup_method(self):
        self.calc = FederalTaxCalculator(pay_periods_per_year=26)

    def test_annual_taxable_income(self):
        """Test annual income calculation"""
        A = self.calc.calculate_annual_taxable_income(
            gross_per_period=Decimal("2000.00"),
            rrsp_per_period=Decimal("100.00"),
            union_dues_per_period=Decimal("50.00")
        )

        # A = 26 × (2000 - 100 - 50) = 26 × 1850 = 48,100
        assert A == Decimal("48100.00")

    def test_k1_personal_credits(self):
        """Test K1 calculation"""
        tc = Decimal("16129.00")  # Federal BPA for 2025
        k1 = self.calc.calculate_k1(tc)

        # K1 = 0.14 × 16129 = 2258.06
        assert k1 == Decimal("2258.06")

    def test_k2_cpp_ei_credits(self):
        """Test K2 CPP/EI credit calculation"""
        k2 = self.calc.calculate_k2(
            cpp_per_period=Decimal("100.00"),
            ei_per_period=Decimal("34.00")
        )

        # K2 = 0.14 × [(26 × 100 × 0.0495/0.0595) + (26 × 34)]
        # K2 = 0.14 × [2162.18 + 884]
        # K2 = 0.14 × 3046.18 = 426.47
        assert k2 > Decimal("400")
        assert k2 < Decimal("450")

    def test_k4_employment_credit(self):
        """Test K4 Canada Employment Amount credit"""
        # For income above CEA
        k4 = self.calc.calculate_k4(Decimal("50000.00"))
        assert k4 == Decimal("0.14") * Decimal("1471.00")

        # For low income (below CEA)
        k4_low = self.calc.calculate_k4(Decimal("1000.00"))
        assert k4_low == Decimal("0.14") * Decimal("1000.00")

    def test_federal_tax_calculation_low_bracket(self):
        """Test federal tax for low income (first bracket)"""
        result = self.calc.calculate_federal_tax(
            annual_taxable_income=Decimal("40000.00"),
            total_claim_amount=Decimal("16129.00"),
            cpp_per_period=Decimal("80.00"),
            ei_per_period=Decimal("30.00")
        )

        assert result["tax_rate"] == Decimal("0.1400")  # Lowest bracket
        assert result["annual_federal_tax_t1"] >= Decimal("0")

    def test_federal_tax_calculation_second_bracket(self):
        """Test federal tax for income in second bracket"""
        result = self.calc.calculate_federal_tax(
            annual_taxable_income=Decimal("70000.00"),
            total_claim_amount=Decimal("16129.00"),
            cpp_per_period=Decimal("120.00"),
            ei_per_period=Decimal("40.00")
        )

        assert result["tax_rate"] == Decimal("0.2050")  # Second bracket
        assert result["constant_k"] == Decimal("3729")
```

FILE TO CREATE:
backend/tests/payroll/test_provincial_tax_calculator.py

```python
import pytest
from decimal import Decimal
from app.services.payroll.provincial_tax_calculator import ProvincialTaxCalculator

class TestProvincialTaxCalculator:
    """Test provincial tax calculations"""

    @pytest.mark.parametrize("province,income,expected_min_tax", [
        ("ON", Decimal("50000"), Decimal("1000")),
        ("AB", Decimal("50000"), Decimal("800")),
        ("BC", Decimal("50000"), Decimal("900")),
        ("MB", Decimal("50000"), Decimal("2000")),
    ])
    def test_different_provinces(self, province, income, expected_min_tax):
        """Test tax calculations for different provinces"""
        calc = ProvincialTaxCalculator(province, pay_periods_per_year=26)

        result = calc.calculate_provincial_tax(
            annual_taxable_income=income,
            total_claim_amount=calc.get_basic_personal_amount(income),
            cpp_per_period=Decimal("100"),
            ei_per_period=Decimal("34")
        )

        assert result["annual_provincial_tax_t2"] >= expected_min_tax

    def test_alberta_k5p_credit(self):
        """Test Alberta supplemental tax credit (K5P)"""
        calc = ProvincialTaxCalculator("AB", pay_periods_per_year=26)

        result = calc.calculate_provincial_tax(
            annual_taxable_income=Decimal("80000"),
            total_claim_amount=Decimal("22323.00"),
            cpp_per_period=Decimal("120"),
            ei_per_period=Decimal("40")
        )

        # K5P should be calculated for Alberta
        assert result["supplemental_credit_k5p"] >= Decimal("0")

    def test_manitoba_dynamic_bpa(self):
        """Test Manitoba dynamic BPA formula"""
        calc = ProvincialTaxCalculator("MB", pay_periods_per_year=26)

        # Low income - full BPA
        bpa_low = calc.get_basic_personal_amount(
            annual_income=Decimal("50000"),
            net_income=Decimal("50000")
        )
        assert bpa_low == Decimal("15591.00")

        # High income - reduced BPA
        bpa_high = calc.get_basic_personal_amount(
            annual_income=Decimal("300000"),
            net_income=Decimal("300000")
        )
        assert bpa_high < Decimal("15591.00")

    def test_nova_scotia_dynamic_bpa(self):
        """Test Nova Scotia dynamic BPA formula"""
        calc = ProvincialTaxCalculator("NS", pay_periods_per_year=26)

        # Below threshold
        bpa_low = calc.get_basic_personal_amount(Decimal("20000"))
        assert bpa_low == Decimal("11744.00")

        # Above threshold
        bpa_high = calc.get_basic_personal_amount(Decimal("80000"))
        assert bpa_high == Decimal("14744.00")
```

RUN TESTS:
```bash
cd backend
uv run pytest tests/payroll/ -v
```
```

---

## 📦 Task 5.2: Integration Tests

### LLM Agent Prompt

```markdown
TASK: Create End-to-End Integration Tests

FILE TO CREATE:
backend/tests/payroll/test_payroll_engine_integration.py

REQUIREMENTS:

Test complete payroll calculation for realistic scenarios.

```python
import pytest
from decimal import Decimal
from app.services.payroll.payroll_engine import PayrollEngine
from app.models.payroll import (
    PayrollCalculationRequest,
    Province,
    PayPeriodFrequency
)

class TestPayrollEngineIntegration:
    """Integration tests for complete payroll calculation"""

    def setup_method(self):
        self.engine = PayrollEngine()

    def test_ontario_employee_bi_weekly(self):
        """Test complete payroll for Ontario employee, bi-weekly"""
        request = PayrollCalculationRequest(
            employee_id="emp_001",
            province=Province.ON,
            pay_frequency=PayPeriodFrequency.BIWEEKLY,
            gross_pay=Decimal("2307.69"),  # $60k annual / 26
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12747.00"),
            rrsp_deduction=Decimal("100.00"),
            union_dues=Decimal("0"),
            ytd_gross=Decimal("0"),
            ytd_cpp=Decimal("0"),
            ytd_ei=Decimal("0")
        )

        result = self.engine.calculate_payroll(request)

        # Validate result structure
        assert result.gross_pay == Decimal("2307.69")
        assert result.cpp_employee > Decimal("0")
        assert result.ei_employee > Decimal("0")
        assert result.federal_tax > Decimal("0")
        assert result.provincial_tax > Decimal("0")

        # Validate calculations
        total_deductions = (
            result.cpp_employee + result.cpp_additional + result.ei_employee +
            result.federal_tax + result.provincial_tax + result.rrsp
        )
        assert result.total_employee_deductions == total_deductions
        assert result.net_pay == result.gross_pay - total_deductions

        # Validate employer costs
        assert result.cpp_employer == result.cpp_employee + result.cpp_additional
        assert result.ei_employer > result.ei_employee  # 1.4x

    def test_alberta_high_income_monthly(self):
        """Test Alberta employee with high income, monthly pay"""
        request = PayrollCalculationRequest(
            employee_id="emp_002",
            province=Province.AB,
            pay_frequency=PayPeriodFrequency.MONTHLY,
            gross_pay=Decimal("10000.00"),  # $120k annual / 12
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("22323.00"),
            ytd_gross=Decimal("0"),
            ytd_cpp=Decimal("0"),
            ytd_ei=Decimal("0")
        )

        result = self.engine.calculate_payroll(request)

        # High income should have CPP2
        assert result.cpp_additional > Decimal("0")

        # Alberta should have K5P credit applied
        assert result.provincial_tax < Decimal("1500")  # Rough check

    def test_ytd_maximums_reached(self):
        """Test employee who reached CPP/EI maximums"""
        request = PayrollCalculationRequest(
            employee_id="emp_003",
            province=Province.BC,
            pay_frequency=PayPeriodFrequency.BIWEEKLY,
            gross_pay=Decimal("3000.00"),
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal("12932.00"),
            ytd_gross=Decimal("72000.00"),  # Already above YMPE
            ytd_cpp=Decimal("3356.10"),     # Max CPP reached
            ytd_ei=Decimal("1077.48")       # Max EI reached
        )

        result = self.engine.calculate_payroll(request)

        # Should not deduct more CPP/EI
        assert result.cpp_employee == Decimal("0")
        assert result.ei_employee == Decimal("0")

        # But should still have CPP2
        assert result.cpp_additional >= Decimal("0")

    @pytest.mark.parametrize("province", [
        Province.AB, Province.BC, Province.MB, Province.NB,
        Province.NL, Province.NS, Province.NT, Province.NU,
        Province.ON, Province.PE, Province.SK, Province.YT
    ])
    def test_all_provinces_smoke_test(self, province):
        """Smoke test: ensure all provinces calculate without errors"""
        # Get appropriate BPA for province
        bpa_map = {
            Province.AB: "22323.00",
            Province.BC: "12932.00",
            Province.MB: "15591.00",
            Province.NB: "13396.00",
            Province.NL: "11067.00",
            Province.NS: "11744.00",
            Province.NT: "17842.00",
            Province.NU: "19274.00",
            Province.ON: "12747.00",
            Province.PE: "15050.00",
            Province.SK: "19991.00",
            Province.YT: "16129.00"
        }

        request = PayrollCalculationRequest(
            employee_id=f"emp_{province}",
            province=province,
            pay_frequency=PayPeriodFrequency.BIWEEKLY,
            gross_pay=Decimal("2000.00"),
            federal_claim_amount=Decimal("16129.00"),
            provincial_claim_amount=Decimal(bpa_map[province]),
            ytd_gross=Decimal("0"),
            ytd_cpp=Decimal("0"),
            ytd_ei=Decimal("0")
        )

        result = self.engine.calculate_payroll(request)

        # Basic validation
        assert result.gross_pay == Decimal("2000.00")
        assert result.net_pay > Decimal("1000")  # Should have reasonable net pay
        assert result.net_pay < result.gross_pay
```

RUN INTEGRATION TESTS:
```bash
uv run pytest tests/payroll/test_payroll_engine_integration.py -v --cov=app/services/payroll
```
```

---

## 📦 Task 5.3: CRA PDOC Validation

### Manual Validation Against CRA Calculator

```markdown
TASK: Validate Calculations Against CRA PDOC

REFERENCE: https://www.canada.ca/en/revenue-agency/services/e-services/digital-services-businesses/payroll-deductions-online-calculator.html

PROCEDURE:

1. Test Cases to Validate:

   Test Case 1: Ontario, Bi-weekly, $60k annual
   - Gross per period: $2,307.69
   - Federal claim: $16,129
   - Provincial claim: $12,747
   - Pay periods: 26

   Expected (from PDOC):
   - CPP: ~$119
   - EI: ~$39
   - Federal Tax: ~$220
   - Provincial Tax: ~$90
   - Net Pay: ~$1,840

   Test Case 2: Alberta, Monthly, $120k annual
   - Gross per period: $10,000
   - Federal claim: $16,129
   - Provincial claim: $22,323
   - Pay periods: 12

   Expected:
   - CPP: ~$535 (includes CPP2)
   - EI: ~$170 (but capped)
   - Federal Tax: ~$1,500
   - Provincial Tax: ~$650

   Test Case 3: Low income, Nova Scotia
   - Gross per period: $1,000
   - Federal claim: $16,129
   - Provincial claim: $11,744
   - Pay periods: 26

   Expected:
   - CPP: ~$45
   - EI: ~$17
   - Federal Tax: ~$0 (below threshold)
   - Provincial Tax: ~$0

2. Validation Steps:

   a) For each test case:
      - Run calculation in your system
      - Run same inputs in CRA PDOC
      - Compare results

   b) Acceptable variance: ±$1 (due to rounding)

   c) If difference > $1:
      - Review tax bracket selection
      - Check K1/K2 credit calculations
      - Verify CPP/EI rates and maximums

3. Document Results:

   Create file: backend/tests/payroll/pdoc_validation_results.md

   ```markdown
   # PDOC Validation Results

   Date: 2025-01-XX
   PDOC Version: [version from PDOC site]

   ## Test Case 1: Ontario Bi-weekly
   | Component | Our System | PDOC | Difference | Status |
   |-----------|------------|------|------------|--------|
   | CPP       | $119.23    | $119 | $0.23      | ✅ PASS |
   | EI        | $39.23     | $39  | $0.23      | ✅ PASS |
   | Fed Tax   | $220.15    | $220 | $0.15      | ✅ PASS |
   | Prov Tax  | $89.87     | $90  | $0.13      | ✅ PASS |
   | Net Pay   | $1839.21   | $1839| $0.21      | ✅ PASS |

   ## Test Case 2: Alberta Monthly
   [Same format]

   ## Summary
   - Total tests: 3
   - Passed: 3
   - Failed: 0
   - Max variance: $0.50
   ```
```

---

## 📦 Task 5.4: Manual Test Plan

### LLM Agent Prompt

```markdown
TASK: Create Manual Testing Plan

FILE TO CREATE:
docs/planning/payroll/manual_test_plan.md

CONTENT:

# Payroll System - Manual Test Plan

## Pre-Test Setup
1. Backend server running: `cd backend && uv run uvicorn app.main:app --reload`
2. Frontend server running: `cd frontend && npm run dev`
3. Test user logged in
4. Test ledger created

---

## Test 1: Employee Management

### 1.1 Add Employee
**Steps:**
1. Navigate to `/payroll/employees`
2. Click "Add Employee" button
3. Fill form:
   - First Name: "John"
   - Last Name: "Doe"
   - SIN: "123-456-789"
   - Province: "Ontario"
   - Annual Salary: "60000.00"
   - Pay Frequency: "Bi-weekly"
   - Hire Date: "2025-01-01"
4. Click "Add Employee"

**Expected:**
- Employee appears in list
- SIN masked as "***-***-789"
- No errors in console

**Actual:** [Fill during test]
**Status:** [ ] Pass [ ] Fail

### 1.2 Edit Employee
[Similar format]

### 1.3 View Employee List
[Similar format]

---

## Test 2: Payroll Calculation

### 2.1 Calculate Single Payroll
**Steps:**
1. Use API endpoint or create UI
2. Submit payroll calculation request:
   ```json
   {
     "employee_id": "emp_001",
     "province": "ON",
     "gross_pay": "2307.69",
     ...
   }
   ```
3. Verify response

**Expected:**
- All deductions calculated
- Net pay = Gross - Deductions
- CPP employer matches employee
- EI employer = 1.4x employee

**Actual:** [Fill during test]
**Status:** [ ] Pass [ ] Fail

### 2.2 Test YTD Maximums
**Steps:**
1. Set YTD CPP to $3,356.10
2. Set YTD EI to $1,077.48
3. Calculate payroll

**Expected:**
- CPP employee = $0
- EI employee = $0
- Taxes still calculated

---

## Test 3: Paystub Generation

### 3.1 Generate PDF Paystub
**Steps:**
1. Complete a payroll calculation
2. Click "Generate Paystub"
3. Download PDF

**Expected:**
- PDF opens without errors
- All fields populated correctly
- Numbers formatted with 2 decimals
- YTD totals shown

**Checks:**
- [ ] Employee name correct
- [ ] Pay period dates correct
- [ ] All deductions listed
- [ ] Net pay matches calculation
- [ ] Company info displayed

---

## Test 4: Multi-Province Validation

### 4.1 Test Each Province
**For each province (AB, BC, MB, NB, NL, NS, NT, NU, ON, PE, SK, YT):**

**Steps:**
1. Create employee in province
2. Calculate payroll with $2,000 gross
3. Verify provincial tax calculated

**Expected:**
- No errors for any province
- Provincial tax > $0
- Tax rates match Table 8.1

**Results:**
- [ ] AB: $____
- [ ] BC: $____
- [ ] MB: $____
[etc.]

---

## Test 5: Beancount Integration

### 5.1 Transaction Generation
**Steps:**
1. Complete payroll calculation
2. Generate Beancount transaction
3. Append to ledger file
4. Open ledger in Fava

**Expected:**
- Transaction format correct
- All accounts exist
- Transaction balances
- Appears in Fava

**Checks:**
- [ ] Expenses:Payroll:Salaries correct
- [ ] Liabilities:Payroll:* correct
- [ ] Assets:Bank:Checking correct
- [ ] Metadata included

---

## Test Summary

**Date:** _______
**Tester:** _______

| Test | Status | Notes |
|------|--------|-------|
| 1.1  |        |       |
| 1.2  |        |       |
| ... |        |       |

**Overall Status:** [ ] PASS [ ] FAIL

**Issues Found:**
1.
2.
```

---

## ✅ Phase 5 Completion Checklist

- [ ] Unit tests written for all calculators
- [ ] Integration tests pass for all provinces
- [ ] PDOC validation completed (variance < $1)
- [ ] Manual test plan executed
- [ ] All tests documented
- [ ] Coverage > 80% for payroll services
- [ ] No critical bugs remaining

---

## 📊 Final Validation

After all tests pass, run full validation:

```bash
# Backend tests
cd backend
uv run pytest tests/payroll/ -v --cov=app/services/payroll --cov-report=html

# Quality checks
bash scripts/quality-check-backend.sh

# Frontend validation
cd frontend
npm run test
npm run check
```

---

**Congratulations! 🎉**

Your Canadian payroll system is complete and validated!

**Next Steps:**
- Deploy to production
- Monitor first real payroll runs
- Gather user feedback
- Plan Phase 2 features (T4, ROE, etc.)
