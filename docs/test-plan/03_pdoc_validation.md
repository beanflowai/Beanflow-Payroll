# Phase 3: PDOC Validation

**Duration**: 2-3 days
**Priority**: P0 (Critical)
**Prerequisites**: Phase 1 & 2 tests passing

---

## Overview

**PDOC (Payroll Deductions Online Calculator)** is CRA's official tool for calculating payroll deductions. Validating our system against PDOC ensures compliance with Canadian tax regulations.

**PDOC URL**: https://www.canada.ca/en/revenue-agency/services/e-services/digital-services-businesses/payroll-deductions-online-calculator.html

---

## Validation Process

```
┌─────────────────────────────────────────────────────────────────────┐
│                      PDOC Validation Workflow                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   Step 1: Prepare Test Scenario                                      │
│   ┌─────────────────────────────────────────┐                        │
│   │ • Province: Ontario                     │                        │
│   │ • Gross Pay: $2,307.69                  │                        │
│   │ • Pay Frequency: Bi-weekly              │                        │
│   │ • TD1 Federal: $16,129                  │                        │
│   │ • TD1 Provincial: $12,747               │                        │
│   └─────────────────────────────────────────┘                        │
│                          │                                           │
│                          ▼                                           │
│   Step 2: Run in CRA PDOC                                            │
│   ┌─────────────────────────────────────────┐                        │
│   │ 1. Go to PDOC website                   │                        │
│   │ 2. Select "Salary" calculation          │                        │
│   │ 3. Enter all parameters                 │                        │
│   │ 4. Click "Calculate"                    │                        │
│   │ 5. Screenshot results                   │                        │
│   └─────────────────────────────────────────┘                        │
│                          │                                           │
│                          ▼                                           │
│   Step 3: Record Expected Values                                     │
│   ┌─────────────────────────────────────────┐                        │
│   │ PDOC Results:                           │                        │
│   │ • CPP: $119.23                          │                        │
│   │ • EI: $37.85                            │                        │
│   │ • Federal Tax: $220.15                  │                        │
│   │ • Provincial Tax: $89.87                │                        │
│   │ • Net Pay: $1,840.59                    │                        │
│   └─────────────────────────────────────────┘                        │
│                          │                                           │
│                          ▼                                           │
│   Step 4: Compare with Our System                                    │
│   ┌─────────────────────────────────────────┐                        │
│   │ Our System vs PDOC:                     │                        │
│   │ • CPP: $119.25 vs $119.23 = +$0.02 ✅   │                        │
│   │ • EI: $37.85 vs $37.85 = $0.00 ✅       │                        │
│   │ • Fed Tax: $220.00 vs $220.15 = -$0.15 ✅│                        │
│   │ • Prov Tax: $90.00 vs $89.87 = +$0.13 ✅ │                        │
│   │ All within $1 tolerance ✅              │                        │
│   └─────────────────────────────────────────┘                        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Test Scenarios

### Scenario 1: Ontario Standard (Baseline)

| Parameter | Value |
|-----------|-------|
| Province | Ontario (ON) |
| Gross Pay | $2,307.69 |
| Pay Frequency | Bi-weekly (26) |
| Pay Date | 2025-07-18 |
| Federal TD1 | $16,129.00 |
| Provincial TD1 | $12,747.00 |
| RRSP | $0 |
| YTD Gross | $0 |
| YTD CPP | $0 |
| YTD EI | $0 |

**PDOC Expected** (fill after running PDOC):
| Component | PDOC Value | Our Value | Variance | Status |
|-----------|------------|-----------|----------|--------|
| CPP | $_____ | | | |
| EI | $_____ | | | |
| Federal Tax | $_____ | | | |
| Provincial Tax | $_____ | | | |
| Net Pay | $_____ | | | |

---

### Scenario 2: Alberta High Income

| Parameter | Value |
|-----------|-------|
| Province | Alberta (AB) |
| Gross Pay | $10,000.00 |
| Pay Frequency | Monthly (12) |
| Pay Date | 2025-07-18 |
| Federal TD1 | $16,129.00 |
| Provincial TD1 | $22,323.00 |
| RRSP | $500.00 |
| YTD Gross | $60,000.00 |
| YTD CPP | $3,500.00 |
| YTD EI | $900.00 |

**PDOC Expected**:
| Component | PDOC Value | Our Value | Variance | Status |
|-----------|------------|-----------|----------|--------|
| CPP (base) | $_____ | | | |
| CPP2 | $_____ | | | |
| EI | $_____ | | | |
| Federal Tax | $_____ | | | |
| Provincial Tax | $_____ | | | |
| Net Pay | $_____ | | | |

---

### Scenario 3: Nova Scotia Low Income

| Parameter | Value |
|-----------|-------|
| Province | Nova Scotia (NS) |
| Gross Pay | $1,000.00 |
| Pay Frequency | Bi-weekly (26) |
| Pay Date | 2025-07-18 |
| Federal TD1 | $16,129.00 |
| Provincial TD1 | $11,744.00 |
| RRSP | $0 |
| YTD Gross | $0 |
| YTD CPP | $0 |
| YTD EI | $0 |

**PDOC Expected**:
| Component | PDOC Value | Our Value | Variance | Status |
|-----------|------------|-----------|----------|--------|
| CPP | $_____ | | | |
| EI | $_____ | | | |
| Federal Tax | $_____ | | | |
| Provincial Tax | $_____ | | | |
| Net Pay | $_____ | | | |

---

### Scenario 4: BC with Tax Reduction

| Parameter | Value |
|-----------|-------|
| Province | British Columbia (BC) |
| Gross Pay | $1,500.00 |
| Pay Frequency | Bi-weekly (26) |
| Pay Date | 2025-07-18 |
| Federal TD1 | $16,129.00 |
| Provincial TD1 | $12,932.00 |
| YTD Gross | $0 |

**PDOC Expected**:
| Component | PDOC Value | Our Value | Variance | Status |
|-----------|------------|-----------|----------|--------|
| CPP | $_____ | | | |
| EI | $_____ | | | |
| Federal Tax | $_____ | | | |
| Provincial Tax | $_____ | | | |
| Net Pay | $_____ | | | |

---

### Scenario 5: Manitoba Dynamic BPA

| Parameter | Value |
|-----------|-------|
| Province | Manitoba (MB) |
| Gross Pay | $2,500.00 |
| Pay Frequency | Bi-weekly (26) |
| Pay Date | 2025-07-18 |
| Federal TD1 | $16,129.00 |
| Provincial TD1 | $15,780.00 |
| YTD Gross | $0 |

**PDOC Expected**:
| Component | PDOC Value | Our Value | Variance | Status |
|-----------|------------|-----------|----------|--------|
| CPP | $_____ | | | |
| EI | $_____ | | | |
| Federal Tax | $_____ | | | |
| Provincial Tax | $_____ | | | |
| Net Pay | $_____ | | | |

---

### Scenario 6-12: Remaining Provinces

Create similar scenarios for:
- [ ] New Brunswick (NB)
- [ ] Newfoundland & Labrador (NL)
- [ ] Northwest Territories (NT)
- [ ] Nunavut (NU)
- [ ] Prince Edward Island (PE)
- [ ] Saskatchewan (SK)
- [ ] Yukon (YT)

---

## PDOC Data Collection Template

### How to Collect PDOC Data

1. **Navigate to PDOC**
   ```
   https://www.canada.ca/en/revenue-agency/services/e-services/digital-services-businesses/payroll-deductions-online-calculator.html
   ```

2. **Select Calculation Type**
   - Choose "Salary" for regular employees
   - Choose "Bonus" for bonus calculations

3. **Enter Parameters**
   - Province of employment
   - Pay period frequency
   - Gross salary per period
   - Federal TD1 claim
   - Provincial TD1 claim
   - Any additional amounts (RRSP, pension, etc.)

4. **Enter YTD Values** (if applicable)
   - YTD gross income
   - YTD CPP contributions
   - YTD EI premiums

5. **Calculate and Record**
   - Click "Calculate"
   - Screenshot the results page
   - Record values in the template below

### Data Recording Template

```json
// backend/tests/payroll/fixtures/pdoc_test_data.json

{
  "version": "2025-07",
  "collected_date": "2025-XX-XX",
  "pdoc_version": "T4127 121st Edition",

  "test_cases": [
    {
      "id": "ON_60K_BIWEEKLY",
      "description": "Ontario standard $60k annual, bi-weekly",
      "input": {
        "province": "ON",
        "gross_pay": "2307.69",
        "pay_frequency": "biweekly",
        "pay_periods": 26,
        "pay_date": "2025-07-18",
        "federal_claim": "16129.00",
        "provincial_claim": "12747.00",
        "rrsp": "0",
        "union_dues": "0",
        "ytd_gross": "0",
        "ytd_cpp": "0",
        "ytd_ei": "0"
      },
      "pdoc_expected": {
        "cpp": "119.23",
        "cpp2": "0.00",
        "ei": "37.85",
        "federal_tax": "220.15",
        "provincial_tax": "89.87",
        "total_deductions": "467.10",
        "net_pay": "1840.59"
      },
      "pdoc_screenshot": "screenshots/ON_60K_BIWEEKLY.png"
    },
    {
      "id": "AB_120K_MONTHLY",
      "description": "Alberta high income $120k annual, monthly",
      "input": {
        "province": "AB",
        "gross_pay": "10000.00",
        "pay_frequency": "monthly",
        "pay_periods": 12,
        "pay_date": "2025-07-18",
        "federal_claim": "16129.00",
        "provincial_claim": "22323.00",
        "rrsp": "500.00",
        "ytd_gross": "60000.00",
        "ytd_cpp": "3500.00",
        "ytd_ei": "900.00"
      },
      "pdoc_expected": {
        "cpp": "XXX.XX",
        "cpp2": "XXX.XX",
        "ei": "XXX.XX",
        "federal_tax": "XXXX.XX",
        "provincial_tax": "XXX.XX",
        "total_deductions": "XXXX.XX",
        "net_pay": "XXXX.XX"
      },
      "pdoc_screenshot": "screenshots/AB_120K_MONTHLY.png"
    }
  ]
}
```

---

## Automated PDOC Comparison Test

**File**: `backend/tests/payroll/test_pdoc_validation.py`

```python
# backend/tests/payroll/test_pdoc_validation.py

import pytest
import json
from decimal import Decimal
from pathlib import Path
from datetime import datetime

from app.services.payroll.payroll_engine import PayrollEngine, EmployeePayrollInput
from app.models.payroll import Province, PayFrequency


# Load PDOC test data
FIXTURES_DIR = Path(__file__).parent / "fixtures"
PDOC_DATA_FILE = FIXTURES_DIR / "pdoc_test_data.json"


def load_pdoc_test_cases():
    """Load PDOC validation test cases from JSON"""
    if not PDOC_DATA_FILE.exists():
        pytest.skip("PDOC test data not yet collected")

    with open(PDOC_DATA_FILE) as f:
        data = json.load(f)

    return data.get("test_cases", [])


class TestPDOCValidation:
    """Validate calculations against CRA PDOC"""

    VARIANCE_TOLERANCE = Decimal("1.00")  # $1 max variance

    def setup_method(self):
        self.engine = PayrollEngine(year=2025)

    @pytest.fixture
    def pdoc_cases(self):
        return load_pdoc_test_cases()

    def _parse_date(self, date_str: str):
        """Parse date string to date object"""
        return datetime.strptime(date_str, "%Y-%m-%d").date()

    def _get_pay_frequency(self, freq_str: str) -> PayFrequency:
        """Convert string to PayFrequency enum"""
        mapping = {
            "weekly": PayFrequency.WEEKLY,
            "biweekly": PayFrequency.BIWEEKLY,
            "semimonthly": PayFrequency.SEMIMONTHLY,
            "monthly": PayFrequency.MONTHLY,
        }
        return mapping.get(freq_str.lower(), PayFrequency.BIWEEKLY)

    def test_pdoc_case_ontario_standard(self):
        """
        PDOC Validation: Ontario $60k annual, bi-weekly

        Run this test AFTER collecting PDOC data
        """
        # Skip if no PDOC data
        if not PDOC_DATA_FILE.exists():
            pytest.skip("PDOC data not collected yet")

        with open(PDOC_DATA_FILE) as f:
            data = json.load(f)

        case = next(
            (c for c in data["test_cases"] if c["id"] == "ON_60K_BIWEEKLY"),
            None
        )
        if not case:
            pytest.skip("Test case ON_60K_BIWEEKLY not found")

        # Build input
        inp = case["input"]
        input_data = EmployeePayrollInput(
            employee_id="pdoc_test_on",
            province=Province.ON,
            pay_frequency=self._get_pay_frequency(inp["pay_frequency"]),
            pay_date=self._parse_date(inp["pay_date"]),
            regular_pay=Decimal(inp["gross_pay"]),
            federal_claim_amount=Decimal(inp["federal_claim"]),
            provincial_claim_amount=Decimal(inp["provincial_claim"]),
            rrsp_deduction=Decimal(inp.get("rrsp", "0")),
            union_dues=Decimal(inp.get("union_dues", "0")),
            ytd_gross=Decimal(inp["ytd_gross"]),
            ytd_cpp=Decimal(inp["ytd_cpp"]),
            ytd_ei=Decimal(inp["ytd_ei"]),
        )

        result = self.engine.calculate_payroll(input_data)

        # Compare with PDOC expected
        expected = case["pdoc_expected"]

        # CPP
        pdoc_cpp = Decimal(expected["cpp"])
        our_cpp = result.cpp_employee
        cpp_variance = abs(our_cpp - pdoc_cpp)
        assert cpp_variance <= self.VARIANCE_TOLERANCE, \
            f"CPP variance {cpp_variance} exceeds tolerance. Our: {our_cpp}, PDOC: {pdoc_cpp}"

        # EI
        pdoc_ei = Decimal(expected["ei"])
        our_ei = result.ei_employee
        ei_variance = abs(our_ei - pdoc_ei)
        assert ei_variance <= self.VARIANCE_TOLERANCE, \
            f"EI variance {ei_variance} exceeds tolerance. Our: {our_ei}, PDOC: {pdoc_ei}"

        # Federal Tax
        pdoc_fed = Decimal(expected["federal_tax"])
        our_fed = result.federal_tax
        fed_variance = abs(our_fed - pdoc_fed)
        assert fed_variance <= self.VARIANCE_TOLERANCE, \
            f"Federal tax variance {fed_variance} exceeds tolerance. Our: {our_fed}, PDOC: {pdoc_fed}"

        # Provincial Tax
        pdoc_prov = Decimal(expected["provincial_tax"])
        our_prov = result.provincial_tax
        prov_variance = abs(our_prov - pdoc_prov)
        assert prov_variance <= self.VARIANCE_TOLERANCE, \
            f"Provincial tax variance {prov_variance} exceeds tolerance. Our: {our_prov}, PDOC: {pdoc_prov}"

    @pytest.mark.parametrize("case_id", [
        "ON_60K_BIWEEKLY",
        "AB_120K_MONTHLY",
        "NS_LOW_INCOME",
        "BC_TAX_REDUCTION",
        "MB_DYNAMIC_BPA",
        # Add more as collected
    ])
    def test_pdoc_all_cases(self, case_id):
        """Parametrized test for all PDOC validation cases"""
        if not PDOC_DATA_FILE.exists():
            pytest.skip("PDOC data not collected yet")

        with open(PDOC_DATA_FILE) as f:
            data = json.load(f)

        case = next(
            (c for c in data["test_cases"] if c["id"] == case_id),
            None
        )
        if not case:
            pytest.skip(f"Test case {case_id} not found")

        # Run validation
        inp = case["input"]
        input_data = EmployeePayrollInput(
            employee_id=f"pdoc_{case_id.lower()}",
            province=Province[inp["province"]],
            pay_frequency=self._get_pay_frequency(inp["pay_frequency"]),
            pay_date=self._parse_date(inp["pay_date"]),
            regular_pay=Decimal(inp["gross_pay"]),
            federal_claim_amount=Decimal(inp["federal_claim"]),
            provincial_claim_amount=Decimal(inp["provincial_claim"]),
            rrsp_deduction=Decimal(inp.get("rrsp", "0")),
            ytd_gross=Decimal(inp["ytd_gross"]),
            ytd_cpp=Decimal(inp["ytd_cpp"]),
            ytd_ei=Decimal(inp["ytd_ei"]),
        )

        result = self.engine.calculate_payroll(input_data)
        expected = case["pdoc_expected"]

        # Validate all components
        validations = [
            ("CPP", result.cpp_employee, Decimal(expected["cpp"])),
            ("EI", result.ei_employee, Decimal(expected["ei"])),
            ("Federal Tax", result.federal_tax, Decimal(expected["federal_tax"])),
            ("Provincial Tax", result.provincial_tax, Decimal(expected["provincial_tax"])),
        ]

        failures = []
        for name, our_value, pdoc_value in validations:
            variance = abs(our_value - pdoc_value)
            if variance > self.VARIANCE_TOLERANCE:
                failures.append(
                    f"{name}: Our={our_value}, PDOC={pdoc_value}, Variance={variance}"
                )

        assert not failures, f"PDOC validation failed for {case_id}:\n" + "\n".join(failures)
```

---

## Validation Results Template

**File**: `backend/tests/pdoc_validation/validation_results.md`

```markdown
# PDOC Validation Results

**Date**: 2025-XX-XX
**PDOC Version**: T4127 121st Edition (July 2025)
**Validator**: [Your Name]

---

## Summary

| Metric | Result |
|--------|--------|
| Total Test Cases | XX |
| Passed | XX |
| Failed | 0 |
| Max Variance | $X.XX |

---

## Detailed Results

### Test Case 1: Ontario Standard ($60k, Bi-weekly)

**Input**:
- Gross Pay: $2,307.69
- Pay Frequency: Bi-weekly
- Federal TD1: $16,129.00
- Provincial TD1: $12,747.00

**Results**:
| Component | Our System | PDOC | Variance | Status |
|-----------|------------|------|----------|--------|
| CPP | $119.25 | $119.23 | $0.02 | ✅ PASS |
| EI | $37.85 | $37.85 | $0.00 | ✅ PASS |
| Federal Tax | $220.00 | $220.15 | $0.15 | ✅ PASS |
| Provincial Tax | $90.00 | $89.87 | $0.13 | ✅ PASS |
| **Net Pay** | **$1,840.59** | **$1,840.59** | **$0.00** | ✅ PASS |

**Evidence**: `screenshots/ON_60K_BIWEEKLY.png`

---

### Test Case 2: Alberta High Income ($120k, Monthly)

[Similar format]

---

## Issues Found

### Issue #1: [Description]
- **Severity**: [High/Medium/Low]
- **Component**: [CPP/EI/Tax]
- **Details**: [Description]
- **Resolution**: [How it was fixed]

---

## Sign-off

- [ ] All test cases validated
- [ ] Screenshots archived
- [ ] Issues documented and resolved
- [ ] Results reviewed and approved

**Approved by**: ________________
**Date**: ________________
```

---

## Evidence Collection

### Screenshot Guidelines

Store PDOC screenshots in:
```
backend/tests/pdoc_validation/screenshots/
├── ON_60K_BIWEEKLY.png
├── AB_120K_MONTHLY.png
├── NS_LOW_INCOME.png
└── ...
```

**Screenshot should include**:
1. PDOC input summary
2. Calculation results
3. Date/timestamp visible
4. Full browser window

---

## Execution Checklist

### Data Collection Phase

- [ ] Create `fixtures/pdoc_test_data.json`
- [ ] Collect PDOC data for Ontario standard case
- [ ] Collect PDOC data for Alberta high income case
- [ ] Collect PDOC data for Nova Scotia low income case
- [ ] Collect PDOC data for BC tax reduction case
- [ ] Collect PDOC data for Manitoba dynamic BPA case
- [ ] Collect data for remaining 7 provinces
- [ ] Screenshot all PDOC results

### Validation Phase

- [ ] Run `test_pdoc_validation.py`
- [ ] Verify all variances < $1
- [ ] Document any discrepancies
- [ ] Create `validation_results.md`
- [ ] Get sign-off

---

## Troubleshooting

### Common Variance Causes

| Issue | Cause | Solution |
|-------|-------|----------|
| CPP variance > $0.50 | Rounding method | Check `ROUND_HALF_UP` |
| Tax bracket wrong | Threshold error | Verify T4127 Table 8.1 |
| Provincial tax off | BPA calculation | Check dynamic BPA formula |
| EI not matching | Rate precision | Use 1.64% exactly |

### Debugging Steps

1. **Isolate the component** - Test CPP, EI, tax separately
2. **Check intermediate values** - Print Factor A, K1, K2, etc.
3. **Verify tax brackets** - Ensure correct bracket selection
4. **Compare formulas** - Match T4127 exactly

---

**Next**: [Phase 4: Test Matrix](./04_test_matrix.md)
