# 2025 Tax Tables Update Log

## Summary

| Item | Status |
|------|--------|
| **Update Period** | 2025-12-29 to 2025-12-30 |
| **T4127 Editions** | 120th (Jan) + 121st (Jul) |
| **PDOC Validated** | Yes (44 test cases) |
| **Updated By** | claude-code |

---

## Configuration Files Updated

### cpp_ei.json

| Field | Initial Value | Corrected Value | Date Fixed |
|-------|---------------|-----------------|------------|
| YMPE | $71,200 | $71,300 | 2025-12-29 |
| YAMPE | $76,000 | $81,200 | 2025-12-29 |
| CPP2 Additional Rate | 1% | 4% | 2025-12-29 |

**Notes**: The initial configuration had outdated values from early 2025 estimates. Corrected to match T4127 121st Edition (July 2025).

### federal_jan.json

- Edition: 120th (January 2025)
- Effective: 2025-01-01 to 2025-06-30
- Federal lowest rate: 15%
- No corrections needed

### federal_jul.json

- Edition: 121st (July 2025)
- Effective: 2025-07-01 onwards
- Federal lowest rate: 14% (reduced from 15%)
- Bracket constants recalculated
- No corrections needed

### provinces_jan.json

- Edition: 120th (January 2025)
- All 12 provinces configured
- No corrections needed

### provinces_jul.json

- Edition: 121st (July 2025)
- Key changes from January:
  - Saskatchewan BPA: $18,991 → $19,991
  - PEI BPA: $14,250 → $15,050
  - `has_k4p` field added for all provinces
  - Quebec `cea` field added

---

## Validation Results

### PDOC Test Suite

| Tier | Test Cases | Status | Date |
|------|------------|--------|------|
| Tier 1 (Provinces) | 12 | ✅ Pass | 2025-12-29 |
| Tier 2 (Income) | 12 | ✅ Pass | 2025-12-29 |
| Tier 3 (CPP/EI) | 8 | ✅ Pass | 2025-12-29 |
| Tier 4 (Special) | 8 | ✅ Pass | 2025-12-29 |
| Tier 5 (Rate change) | 4 | ✅ Pass | 2025-12-29 |

**Total**: 44/44 test cases passed

### Tolerance

- Maximum variance: $0.05 per component
- All calculations within tolerance

---

## Issues Discovered and Fixed

### Issue 1: CPP2 Rate Incorrect

**Problem**: Configuration showed CPP2 rate as 1%, but T4127 121st Edition specifies 4%.

**Root Cause**: Initial configuration was based on 2024 estimates before final 2025 rates were published.

**Fix**: Updated `additional_rate` from `0.01` to `0.04` in cpp_ei.json.

**Impact**: CPP2 contributions for high-income earners ($71,300+) were significantly underestimated.

### Issue 2: YAMPE Outdated

**Problem**: YAMPE was set to $76,000 instead of $81,200.

**Root Cause**: Same as Issue 1 - early estimates.

**Fix**: Updated `yampe` from `76000.00` to `81200.00`.

**Impact**: CPP2 maximum contribution ceiling was incorrect.

### Issue 3: Documentation Out of Sync

**Problem**: `docs/02_phase2_calculations.md` and `docs/implementation_checklist.md` had outdated CPP2 rate and YAMPE values.

**Fix**: Updated both documentation files to match corrected configuration.

---

## Metadata Added

All configuration files now include `_metadata` field with:

- Source document references (T4127 edition, URL)
- Access dates for audit trail
- PDOC validation status and date
- Change history from previous version
- Last update timestamp and author

---

## Recommendations for 2026

1. **Early verification**: Validate 2026 configuration against PDOC as soon as CRA releases 122nd Edition
2. **Missing files**: Create `federal_jul.json` and `provinces_jul.json` when July 2026 edition is released
3. **Schema validation**: Implement JSON Schema validation to catch structural errors automatically
4. **CI integration**: Add PDOC tests to CI/CD pipeline for automated validation

---

## Sign-off

**Reviewed by**: _____________
**Date**: _____________
