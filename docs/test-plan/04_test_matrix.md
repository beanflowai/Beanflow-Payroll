# Phase 4: Test Matrix

**Purpose**: Comprehensive reference of all test scenarios
**Priority**: P1 (Reference Document)

---

## Overview

This document provides a complete matrix of test scenarios covering all combinations of:
- 12 Provinces/Territories
- 4 Pay Frequencies
- Multiple Income Levels
- Special Conditions (exemptions, maximums, etc.)

---

## Test Dimensions

### Dimension 1: Provinces (12)

| Code | Province/Territory | Special Rules |
|------|-------------------|---------------|
| AB | Alberta | K5P supplemental credit |
| BC | British Columbia | Tax reduction (Factor S) |
| MB | Manitoba | Dynamic BPA |
| NB | New Brunswick | Standard |
| NL | Newfoundland & Labrador | Standard |
| NS | Nova Scotia | Dynamic BPA (two-tier) |
| NT | Northwest Territories | Standard |
| NU | Nunavut | Standard |
| ON | Ontario | Surtax + Health Premium |
| PE | Prince Edward Island | Mid-year BPA change |
| SK | Saskatchewan | Mid-year BPA change |
| YT | Yukon | Dynamic BPA (follows federal) |

### Dimension 2: Pay Frequencies (4)

| Frequency | Periods/Year | Typical Use Case |
|-----------|--------------|------------------|
| Weekly | 52 | Hourly workers |
| Bi-weekly | 26 | Most common |
| Semi-monthly | 24 | Some salaried |
| Monthly | 12 | Executives |

### Dimension 3: Income Levels (5)

| Level | Annual Income | Characteristics |
|-------|---------------|-----------------|
| Very Low | < $20,000 | Below tax threshold |
| Low | $20,000 - $45,000 | First tax bracket |
| Medium | $45,000 - $75,000 | Second tax bracket |
| High | $75,000 - $120,000 | Third bracket, CPP2 triggers |
| Very High | > $120,000 | Top brackets, all maxes |

### Dimension 4: Special Conditions (8)

| Condition | Description |
|-----------|-------------|
| Standard | No special conditions |
| CPP Exempt | Employee exempt from CPP |
| EI Exempt | Employee exempt from EI |
| CPP2 Exempt | Exempt from additional CPP |
| YTD Max CPP | CPP maximum already reached |
| YTD Max EI | EI maximum already reached |
| With RRSP | Has RRSP deduction |
| With Benefits | Has taxable benefits |

---

## Core Test Matrix

### Priority 1: Essential Tests (Must Pass)

| ID | Province | Income | Frequency | Condition | Notes |
|----|----------|--------|-----------|-----------|-------|
| E01 | ON | Medium | Bi-weekly | Standard | Baseline case |
| E02 | ON | High | Monthly | Standard | Surtax test |
| E03 | AB | Medium | Bi-weekly | Standard | K5P credit |
| E04 | BC | Low | Bi-weekly | Standard | Tax reduction |
| E05 | MB | Medium | Bi-weekly | Standard | Dynamic BPA |
| E06 | NS | Medium | Bi-weekly | Standard | Two-tier BPA |
| E07 | YT | Medium | Bi-weekly | Standard | Federal BPA |
| E08 | ON | High | Bi-weekly | YTD Max CPP | Max reached |
| E09 | ON | High | Bi-weekly | YTD Max EI | Max reached |
| E10 | ON | Very High | Monthly | Standard | CPP2 test |
| E11 | ON | Medium | Bi-weekly | CPP Exempt | Exemption |
| E12 | ON | Medium | Bi-weekly | EI Exempt | Exemption |

### Priority 2: Province Coverage (All 12)

| ID | Province | Income | Frequency | Notes |
|----|----------|--------|-----------|-------|
| P01 | AB | $65,000 | Bi-weekly | Alberta standard |
| P02 | BC | $65,000 | Bi-weekly | BC standard |
| P03 | MB | $65,000 | Bi-weekly | Manitoba standard |
| P04 | NB | $65,000 | Bi-weekly | New Brunswick |
| P05 | NL | $65,000 | Bi-weekly | Newfoundland |
| P06 | NS | $65,000 | Bi-weekly | Nova Scotia |
| P07 | NT | $65,000 | Bi-weekly | NWT |
| P08 | NU | $65,000 | Bi-weekly | Nunavut |
| P09 | ON | $65,000 | Bi-weekly | Ontario |
| P10 | PE | $65,000 | Bi-weekly | PEI |
| P11 | SK | $65,000 | Bi-weekly | Saskatchewan |
| P12 | YT | $65,000 | Bi-weekly | Yukon |

### Priority 3: Boundary Tests

| ID | Description | Value Tested | Expected Behavior |
|----|-------------|--------------|-------------------|
| B01 | Income at CPP exemption | $3,500/year | CPP = $0 |
| B02 | Income just above exemption | $4,000/year | CPP > $0 |
| B03 | Income at YMPE | $71,300 | No CPP2 |
| B04 | Income just above YMPE | $72,000 | CPP2 starts |
| B05 | Income at YAMPE | $81,200 | CPP2 at max |
| B06 | Income above YAMPE | $100,000 | CPP2 capped |
| B07 | Income at MIE | $65,700 | EI at max |
| B08 | YTD CPP at 99% max | $3,994 | Partial deduction |
| B09 | YTD EI at 99% max | $1,066 | Partial deduction |
| B10 | Zero income | $0 | All deductions $0 |

### Priority 4: Special Rules

| ID | Province | Rule | Test Scenario |
|----|----------|------|---------------|
| S01 | ON | Surtax 20% | Tax > $5,554 |
| S02 | ON | Surtax 36% | Tax > $7,108 |
| S03 | ON | Health Premium | Income > $20,000 |
| S04 | BC | Tax Reduction | Income < $24,000 |
| S05 | MB | Dynamic BPA Low | Income < $50,000 |
| S06 | MB | Dynamic BPA High | Income > $200,000 |
| S07 | NS | BPA Tier 1 | Income < threshold |
| S08 | NS | BPA Tier 2 | Income > threshold |
| S09 | YT | Federal BPA | Follows federal formula |
| S10 | AB | K5P Credit | All Alberta employees |

---

## Detailed Test Scenarios

### Scenario Matrix: Ontario

| Annual Income | Bi-weekly Gross | Expected CPP | Expected EI | Fed Tax | Prov Tax |
|---------------|-----------------|--------------|-------------|---------|----------|
| $30,000 | $1,153.85 | ~$58 | ~$19 | ~$50 | ~$25 |
| $45,000 | $1,730.77 | ~$90 | ~$28 | ~$130 | ~$55 |
| $60,000 | $2,307.69 | ~$119 | ~$38 | ~$220 | ~$90 |
| $80,000 | $3,076.92 | ~$155* | ~$50 | ~$380 | ~$150 |
| $100,000 | $3,846.15 | ~$155* | ~$41* | ~$560 | ~$230 |
| $150,000 | $5,769.23 | ~$155* | ~$0* | ~$1,100 | ~$500 |

*May hit annual maximums depending on YTD

### Scenario Matrix: Alberta (Low Tax)

| Annual Income | Monthly Gross | Expected CPP | Expected EI | Fed Tax | Prov Tax |
|---------------|---------------|--------------|-------------|---------|----------|
| $60,000 | $5,000 | ~$260 | ~$82 | ~$480 | ~$150 |
| $90,000 | $7,500 | ~$380 | ~$110 | ~$900 | ~$350 |
| $120,000 | $10,000 | ~$450* | ~$89* | ~$1,500 | ~$600 |

### Scenario Matrix: Manitoba (High Tax)

| Annual Income | Bi-weekly Gross | Expected CPP | Expected EI | Fed Tax | Prov Tax |
|---------------|-----------------|--------------|-------------|---------|----------|
| $60,000 | $2,307.69 | ~$119 | ~$38 | ~$220 | ~$180 |
| $80,000 | $3,076.92 | ~$155 | ~$50 | ~$380 | ~$280 |

---

## Test Data Templates

### Standard Employee Template

```json
{
  "employee_id": "test_001",
  "province": "ON",
  "pay_frequency": "biweekly",
  "pay_date": "2025-07-18",
  "regular_pay": "2307.69",
  "overtime_pay": "0",
  "bonus": "0",
  "federal_claim": "16129.00",
  "provincial_claim": "12747.00",
  "rrsp": "0",
  "union_dues": "0",
  "taxable_benefits": "0",
  "ytd_gross": "0",
  "ytd_cpp": "0",
  "ytd_ei": "0",
  "cpp_exempt": false,
  "ei_exempt": false,
  "cpp2_exempt": false
}
```

### High Income Employee Template

```json
{
  "employee_id": "test_high_001",
  "province": "AB",
  "pay_frequency": "monthly",
  "pay_date": "2025-07-18",
  "regular_pay": "10000.00",
  "bonus": "5000.00",
  "federal_claim": "16129.00",
  "provincial_claim": "22323.00",
  "rrsp": "1000.00",
  "ytd_gross": "60000.00",
  "ytd_cpp": "3500.00",
  "ytd_cpp2": "100.00",
  "ytd_ei": "900.00"
}
```

### Exempt Employee Template

```json
{
  "employee_id": "test_exempt_001",
  "province": "ON",
  "pay_frequency": "biweekly",
  "pay_date": "2025-07-18",
  "regular_pay": "2000.00",
  "federal_claim": "16129.00",
  "provincial_claim": "12747.00",
  "cpp_exempt": true,
  "ei_exempt": false
}
```

---

## Expected Results Reference

### 2025 CPP Reference Values

| Annual Income | Annual CPP (Base) | Annual CPP2 | Total |
|---------------|-------------------|-------------|-------|
| $30,000 | $1,577.25 | $0 | $1,577.25 |
| $50,000 | $2,766.75 | $0 | $2,766.75 |
| $71,300 | $4,034.10 | $0 | $4,034.10 |
| $81,200 | $4,034.10 | $396.00 | $4,430.10 |
| $100,000 | $4,034.10 | $396.00 | $4,430.10 |

### 2025 EI Reference Values

| Annual Income | Annual EI |
|---------------|-----------|
| $30,000 | $492.00 |
| $50,000 | $820.00 |
| $65,700 | $1,077.48 |
| $100,000 | $1,077.48 |

---

## Test Coverage Summary

### By Phase

| Phase | Tests | Coverage |
|-------|-------|----------|
| Unit Tests | ~30 | Calculator logic |
| Integration Tests | ~25 | Full payroll flow |
| PDOC Validation | ~12 | CRA compliance |
| Edge Cases | ~15 | Boundaries |
| **Total** | **~82** | |

### By Priority

| Priority | Count | Description |
|----------|-------|-------------|
| P0 - Critical | 12 | Must pass for release |
| P1 - High | 20 | Province coverage |
| P2 - Medium | 30 | Boundary conditions |
| P3 - Low | 20 | Edge cases |

### By Component

| Component | Unit | Integration | PDOC |
|-----------|------|-------------|------|
| CPP | 8 | 4 | 12 |
| EI | 6 | 3 | 12 |
| Federal Tax | 10 | 4 | 12 |
| Provincial Tax | 15 | 12 | 12 |
| Payroll Engine | - | 8 | - |

---

## Maintenance Notes

### When Tax Rates Change

1. Update `backend/config/tax_tables/{year}/` JSON files
2. Update expected values in this matrix
3. Re-run PDOC validation
4. Update test data fixtures

### When Adding New Province Rules

1. Add to Special Rules section
2. Create dedicated test cases
3. Add PDOC validation scenario
4. Update province coverage matrix

---

## Appendix: Provincial BPA 2025

| Province | BPA | Notes |
|----------|-----|-------|
| AB | $22,323 | Static |
| BC | $12,932 | Static |
| MB | $15,780 | Dynamic (reduces at high income) |
| NB | $13,396 | Static |
| NL | $11,067 | Static |
| NS | $11,744 / $8,744 | Two-tier based on income |
| NT | $17,842 | Static |
| NU | $19,274 | Static |
| ON | $12,747 | Static |
| PE | $14,250 → $15,050 | Mid-year change (Jul 1) |
| SK | $18,991 → $19,991 | Mid-year change (Jul 1) |
| YT | ~$16,129 | Follows federal BPA formula |

---

## Appendix: Federal Tax Brackets 2025 (Jul+)

| Bracket | Income Range | Rate | Constant K |
|---------|-------------|------|------------|
| 1 | $0 - $57,375 | 14.0% | $0 |
| 2 | $57,375 - $114,750 | 20.5% | $3,729 |
| 3 | $114,750 - $177,882 | 26.0% | $10,041 |
| 4 | $177,882 - $253,414 | 29.0% | $15,378 |
| 5 | > $253,414 | 33.0% | $25,515 |

---

**End of Test Matrix**
