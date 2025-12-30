# Phase 3: PDOC Validation

**Priority**: P0 (Critical)
**Prerequisites**: Phase 1 & 2 tests passing

---

## Test Structure (Modular)

The PDOC validation tests are organized in a modular tier-based structure with edition separation:

```
backend/tests/payroll/pdoc/
├── conftest.py                      # Shared fixtures + utilities (~420 lines)
├── fixtures/
│   └── 2025/                        # Year-based fixture directory
│       ├── jan/                     # 120th Edition (Jan-Jun, 15% federal rate)
│       │   ├── tier1_province_coverage.json
│       │   ├── tier2_income_levels.json
│       │   ├── tier3_cpp_ei_boundary.json
│       │   ├── tier4_special_conditions.json
│       │   └── tier5_federal_rate_change.json
│       └── jul/                     # 121st Edition (Jul+, 14% federal rate)
│           ├── tier1_province_coverage.json  # 12 verified tests
│           ├── tier2_income_levels.json      # 12 verified tests
│           ├── tier3_cpp_ei_boundary.json    # 9 verified tests
│           ├── tier4_special_conditions.json # 8 verified tests
│           └── tier5_federal_rate_change.json # 4 verified tests
├── test_tier1_provinces.py           # Core 12省覆盖 (~133 lines)
├── test_tier2_income_levels.py       # 收入级别测试 (~147 lines)
├── test_tier3_cpp_ei.py              # CPP/EI边界 (~199 lines)
├── test_tier4_special.py             # 特殊条件 (~242 lines)
└── test_tier5_rate_change.py         # 联邦税率变更 (~201 lines)
```

### Edition Differences (2025)

| Field | Jan Edition (120th) | Jul Edition (121st) |
|-------|---------------------|---------------------|
| `pay_date` | `2025-01-17` ~ `2025-06-30` | `2025-07-01`+ |
| Federal Rate | 15% | 14% |
| SK provincial_claim | $18,991 | $19,991 |
| PE provincial_claim | $14,250 | $15,050 |

**Note**: CPP/EI rates are unchanged for the entire year.

### Running Tests

```bash
# Run all PDOC tests (default: jul edition)
pytest backend/tests/payroll/pdoc/

# Run specific tier
pytest backend/tests/payroll/pdoc/test_tier1_provinces.py

# Run only verified cases
pytest backend/tests/payroll/pdoc/ -k "verified"

# Run with verbose output
pytest backend/tests/payroll/pdoc/ -v

# Run both editions (when jan fixtures are verified)
# Modify conftest.py: edition fixture params=["jan", "jul"]
```

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

## Test Implementation

The PDOC validation tests are implemented in a modular tier-based structure. Each tier focuses on specific validation scenarios:

| Tier | File | Test Focus | Cases |
|------|------|------------|-------|
| Tier 1 | `test_tier1_provinces.py` | Core 12 province coverage | 12 |
| Tier 2 | `test_tier2_income_levels.py` | Low/high income levels | 12 |
| Tier 3 | `test_tier3_cpp_ei.py` | CPP2/EI boundary conditions | 8 |
| Tier 4 | `test_tier4_special.py` | RRSP, union dues, special cases | 8 |
| Tier 5 | `test_tier5_rate_change.py` | Federal rate change scenarios | 4 |

### Test Fixtures

Test data is stored in JSON fixtures under `pdoc/fixtures/<year>/<edition>/`:

```
fixtures/2025/
├── jan/   # 120th Edition - 15% federal rate (Jan-Jun 2025)
│   └── tier*.json
└── jul/   # 121st Edition - 14% federal rate (Jul+ 2025)
    └── tier*.json
```

**Edition Selection**:
- `jan`: 120th Edition, effective January-June 2025, federal lowest bracket rate is 15%
- `jul`: 121st Edition, effective July 2025 onwards, federal lowest bracket rate is 14%

**Jan Edition Status**: Fixtures created with structure; most cases marked `TO_BE_VERIFIED` pending PDOC validation. SK and PE have different provincial BPA values.

The year + edition directory structure allows testing against:
- Multiple tax years (2024, 2025, 2026, etc.)
- Mid-year rate changes (jan/jul editions)

### Variance Tolerance

All tests use a **$1.00 maximum variance** tolerance per component (CPP, EI, Federal Tax, Provincial Tax).

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

- [ ] Run `pytest backend/tests/payroll/pdoc/`
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
