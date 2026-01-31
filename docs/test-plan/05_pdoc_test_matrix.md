# Phase 5: PDOC Validation Test Matrix

**Purpose**: Comprehensive PDOC validation covering all provinces and scenarios
**Priority**: P0 (Critical - CRA Compliance)
**Status**: Planning

---

## Overview

This document defines the complete PDOC (Payroll Deductions Online Calculator) validation test matrix. Each test case will be collected from CRA's official PDOC tool and used to validate BeanFlow Payroll calculations.

**PDOC URL**: https://www.canada.ca/en/revenue-agency/services/e-services/digital-services-businesses/payroll-deductions-online-calculator.html

**Tolerance**: $0.05 per component (CPP, EI, Federal Tax, Provincial Tax, Net Pay)

---

## Test Matrix Design Principles

### Coverage Strategy

1. **Province Coverage**: All 12 provinces/territories (excluding Quebec)
2. **Pay Frequency**: Focus on bi-weekly (most common), with monthly for high-income
3. **Income Levels**: 3 levels per province (low, medium, high)
4. **Special Rules**: Province-specific rules must be explicitly tested
5. **Date Sensitivity**: Pre-July and post-July 2025 federal rate change

### Test Case Naming Convention

```
{PROVINCE}_{INCOME_LEVEL}_{FREQUENCY}_{SPECIAL}
```

Examples:
- `ON_60K_BIWEEKLY` - Ontario, $60k, bi-weekly, standard
- `AB_120K_MONTHLY_RRSP` - Alberta, $120k, monthly, with RRSP
- `ON_150K_MONTHLY_YTD` - Ontario, $150k, monthly, with YTD near max

---

## Complete Test Matrix

### Tier 1: Core Province Coverage (12 tests)

Each province with $60k annual income, bi-weekly, standard conditions.

| ID | Province | Annual | Gross/Period | Federal Claim | Prov Claim | Special Rule Tested |
|----|----------|--------|--------------|---------------|------------|---------------------|
| ON_60K_BIWEEKLY | Ontario | $60,000 | $2,307.69 | $16,129 | $12,747 | Surtax, Health Premium |
| AB_60K_BIWEEKLY | Alberta | $60,000 | $2,307.69 | $16,129 | $22,323 | Flat 10%, K5P Credit |
| BC_60K_BIWEEKLY | BC | $60,000 | $2,307.69 | $16,129 | $12,932 | Tax Reduction (S) |
| MB_60K_BIWEEKLY | Manitoba | $60,000 | $2,307.69 | $16,129 | $15,780 | Dynamic BPA |
| SK_60K_BIWEEKLY | Saskatchewan | $60,000 | $2,307.69 | $16,129 | $18,991 | Mid-year BPA change |
| NB_60K_BIWEEKLY | New Brunswick | $60,000 | $2,307.69 | $16,129 | $13,396 | Standard |
| NL_60K_BIWEEKLY | Newfoundland | $60,000 | $2,307.69 | $16,129 | $11,067 | Standard |
| NS_60K_BIWEEKLY | Nova Scotia | $60,000 | $2,307.69 | $16,129 | $11,744 | Two-tier BPA, Surtax |
| PE_60K_BIWEEKLY | PEI | $60,000 | $2,307.69 | $16,129 | $14,250 | Mid-year BPA change |
| NT_60K_BIWEEKLY | NWT | $60,000 | $2,307.69 | $16,129 | $17,842 | Standard |
| NU_60K_BIWEEKLY | Nunavut | $60,000 | $2,307.69 | $16,129 | $19,274 | Standard |
| YT_60K_BIWEEKLY | Yukon | $60,000 | $2,307.69 | $16,129 | $16,129 | Federal BPA formula |

### Tier 2: Income Level Coverage (12 tests)

Test low and high income for provinces with special rules.

#### Low Income Tests ($30k)

| ID | Province | Annual | Gross/Period | Notes |
|----|----------|--------|--------------|-------|
| ON_30K_BIWEEKLY | Ontario | $30,000 | $1,153.85 | Below health premium threshold |
| BC_30K_BIWEEKLY | BC | $30,000 | $1,153.85 | Tax reduction (Factor S) active |
| MB_30K_BIWEEKLY | Manitoba | $30,000 | $1,153.85 | Full dynamic BPA benefit |
| NS_30K_BIWEEKLY | Nova Scotia | $30,000 | $1,153.85 | Higher BPA tier |

#### High Income Tests ($120k+)

| ID | Province | Annual | Gross/Period | Notes |
|----|----------|--------|--------------|-------|
| ON_120K_MONTHLY | Ontario | $120,000 | $10,000.00 | Full surtax, health premium |
| AB_120K_MONTHLY | Alberta | $120,000 | $10,000.00 | Flat rate, high BPA benefit |
| BC_120K_MONTHLY | BC | $120,000 | $10,000.00 | No tax reduction |
| MB_120K_MONTHLY | Manitoba | $120,000 | $10,000.00 | Reduced dynamic BPA |
| ON_150K_MONTHLY | Ontario | $150,000 | $12,500.00 | Maximum surtax bracket |
| NS_120K_MONTHLY | Nova Scotia | $120,000 | $10,000.00 | Lower BPA tier, surtax |
| ON_200K_MONTHLY | Ontario | $200,000 | $16,666.67 | Top tax bracket |
| AB_200K_MONTHLY | Alberta | $200,000 | $16,666.67 | Flat rate comparison |

### Tier 3: CPP/EI Boundary Tests (8 tests)

| ID | Province | Annual | Scenario | Expected Behavior |
|----|----------|--------|----------|-------------------|
| ON_72K_BIWEEKLY | Ontario | $72,000 | Just above YMPE | CPP2 starts |
| ON_82K_BIWEEKLY | Ontario | $82,000 | Above YAMPE | CPP2 at ceiling |
| ON_66K_BIWEEKLY | Ontario | $66,000 | At EI MIE | EI at maximum rate |
| ON_80K_YTD_CPP | Ontario | $80,000 | YTD CPP near max | Partial CPP deduction |
| ON_70K_YTD_EI | Ontario | $70,000 | YTD EI near max | Partial EI deduction |
| ON_100K_MAXED | Ontario | $100,000 | All YTD maxed | Zero CPP/EI |
| AB_85K_CPP2 | Alberta | $85,000 | CPP2 range | Verify CPP2 calculation |
| BC_90K_CPP2 | BC | $90,000 | CPP2 + tax reduction | Combined rules |

### Tier 4: Special Conditions (11 tests)

| ID | Province | Annual | Special Condition | Notes |
|----|----------|--------|-------------------|-------|
| ON_60K_RRSP | Ontario | $60,000 | RRSP $500/period | Tax reduction from RRSP |
| ON_60K_UNION | Ontario | $60,000 | Union dues $50/period | Tax credit |
| AB_80K_RRSP | Alberta | $80,000 | RRSP $1000/period | High RRSP deduction |
| ON_60K_CPP_EXEMPT | Ontario | $60,000 | CPP exempt | No CPP contribution |
| ON_60K_EI_EXEMPT | Ontario | $60,000 | EI exempt | No EI contribution |
| ON_100K_CPP2_EXEMPT | Ontario | $100,000 | CPP2 exempt | No additional CPP |
| ON_60K_BENEFITS | Ontario | $60,000 | Taxable benefits $100 | Benefits taxability |
| BC_40K_BENEFITS | BC | $40,000 | Taxable benefits + low income | Combined with tax reduction |
| **ON_BONUS_10K** | Ontario | $60,000 YTD + $10K bonus | Bonus $10,000 | Marginal rate method validation |
| **BC_BONUS_60K** | BC | $76,333 YTD + $60K bonus | Bonus $60,000 | High-value bonus edge case |
| **AB_BONUS_5K** | Alberta | $50,000 YTD + $5K bonus | Bonus $5,000 | Small bonus scenario |

### Tier 5: Federal Tax Rate Change (4 tests)

| ID | Province | Pay Date | Federal Rate | Notes |
|----|----------|----------|--------------|-------|
| ON_60K_JAN | Ontario | 2025-01-17 | 15% | Pre-July rate |
| ON_60K_JUN | Ontario | 2025-06-27 | 15% | Last day at 15% |
| ON_60K_JUL | Ontario | 2025-07-11 | 14% | First day at 14% |
| AB_60K_JAN | Alberta | 2025-01-17 | 15% | Pre-July comparison |

---

## Data Collection Template

For each test case, collect from PDOC:

```json
{
  "id": "PROVINCE_INCOME_FREQ",
  "description": "Description of test case",
  "collected_date": "YYYY-MM-DD",
  "pdoc_version": "T4127 - Version YYYY-MM-DD",
  "input": {
    "province": "XX",
    "gross_pay": "0.00",
    "pay_frequency": "biweekly|monthly|weekly|semimonthly",
    "pay_periods": 26,
    "pay_date": "YYYY-MM-DD",
    "federal_claim": "16129.00",
    "provincial_claim": "0.00",
    "rrsp": "0",
    "union_dues": "0",
    "ytd_gross": "0",
    "ytd_pensionable_earnings": "0",
    "ytd_insurable_earnings": "0",
    "ytd_cpp_base": "0",
    "ytd_cpp_additional": "0",
    "ytd_ei": "0"
  },
  "pdoc_expected": {
    "cpp_total": "0.00",
    "cpp_enhancement_f2": "0.00",
    "cpp2": "0.00",
    "ei": "0.00",
    "federal_tax": "0.00",
    "provincial_tax": "0.00",
    "total_deductions": "0.00",
    "net_pay": "0.00",
    "taxable_income_per_period": "0.00",
    "pensionable_earnings": "0.00",
    "insurable_earnings": "0.00"
  },
  "notes": "Any special observations"
}
```

---

## Collection Priority

### Phase 5A - Critical (12 tests) - **Immediate**
- All Tier 1 tests (12 provinces × $60k bi-weekly)
- Establishes baseline for all provinces

### Phase 5B - High Priority (12 tests)
- Tier 2 income level tests
- Validates tax bracket calculations

### Phase 5C - Medium Priority (8 tests)
- Tier 3 CPP/EI boundary tests
- Validates contribution maximums

### Phase 5D - Standard Priority (15 tests)
- Tier 4 special conditions (11) + Tier 5 rate change (4)
- Validates edge cases and bonus taxation

---

## Automation Plan (Claude in Chrome)

### PDOC Navigation Steps

1. Navigate to PDOC: `https://www.canada.ca/en/revenue-agency/services/e-services/digital-services-businesses/payroll-deductions-online-calculator.html`
2. Select "Payroll Deductions Online Calculator"
3. Enter calculation parameters:
   - Province
   - Pay date
   - Pay frequency
   - Gross pay
   - Federal/Provincial claims
   - YTD values (if applicable)
4. Click "Calculate"
5. Extract results:
   - CPP deductions
   - EI deductions
   - Federal tax
   - Provincial tax
   - Net pay

### Data Extraction Fields

From PDOC results page, extract:
- "CPP deductions" → `cpp_total`
- "CPP additional contribution (F2)" → `cpp_enhancement_f2`
- "Second additional CPP contributions (CPP2)" → `cpp2`
- "EI premiums" → `ei`
- "Federal tax" → `federal_tax`
- "Provincial tax" → `provincial_tax`
- "Total deductions" → `total_deductions`
- "Net pay" → `net_pay`

---

## Success Criteria

| Metric | Target |
|--------|--------|
| Total test cases | 47 |
| Province coverage | 12/12 (100%) |
| Maximum variance | $0.05 per component |
| CPP/EI exact match | 100% |
| Tax variance | < $0.05 |
| Bonus scenarios | 3 (ON, BC, AB) |

---

## Timeline

| Phase | Tests | Status |
|-------|-------|--------|
| Phase 5A | 12 | Pending |
| Phase 5B | 12 | Pending |
| Phase 5C | 8 | Pending |
| Phase 5D | 15 | Pending |
| **Total** | **47** | |

---

**End of PDOC Test Matrix**
