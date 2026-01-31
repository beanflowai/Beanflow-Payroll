# Holiday Pay - Known Limitations & TODO

> Last updated: 2026-01-24
> Source: Codex Code Review Analysis

This document tracks known limitations and TODO items for the holiday pay calculation system.

---

## Deferred Items

### 1. NS Remembrance Day Special Rules

**Status**: Deferred
**Priority**: Low
**Source**: Codex Finding #7

**Description**:
NS Remembrance Day has special rules covered by a separate Remembrance Day Act and typically does not apply standard premium pay. Current implementation does not handle this special case.

**Action Required**:
- Research NS Labour Standards Code and Remembrance Day Act for specifics
- Add special handling in calculator if needed

**Reference**:
- Nova Scotia Remembrance Day Act
- Current config note: "Remembrance Day covered by separate Remembrance Day Act."

---

### 2. MB/AB Construction Industry Percentage

**Status**: Deferred
**Priority**: Low
**Source**: Codex Finding #8

**Description**:
Configuration has `construction_percentage: 0.04` (MB) and `construction_percentage: 0.036`, `incentive_pay_percentage: 0.042` (AB), but no code branch uses these parameters. These are alternative calculation methods for construction industry employees.

**Config Location**: `backend/config/holiday_pay/2026/provinces_jan.json`
- MB line 125: `"construction_percentage": 0.04`
- AB lines 74-75: `"construction_percentage": 0.036, "incentive_pay_percentage": 0.042`

**Action Required**:
- Add industry identification field to employee/pay_group model
- Implement formula routing based on industry type
- For AB: Also need to handle incentive pay employees (4.2%)

**Reference**:
- MB ESC: "Construction industry: 4%"
- AB ESC s.25: "Construction: 3.6%. Incentive pay employees: 4.2% of wages in 4 weeks."

---

## TODO Items

### 1. QC/Federal Commission Employee Formula (1/60)

**Status**: TODO
**Priority**: Medium
**Source**: Codex Finding #4

**Description**:
Commission employees in QC and Federal jurisdictions should use 1/60 of 12-week wages instead of 1/20 of 4-week wages. Config parameters exist but no routing logic implemented.

**Config Parameters**:
- QC (lines 100-101): `"commission_divisor": 60, "commission_lookback_weeks": 12`
- Federal (lines 334-335): `"commission_divisor": 60, "commission_lookback_weeks": 12`

**Implementation Notes**:
- `apply_commission()` formula already implemented in `formula_calculators.py:530-594`
- Need to add `compensation_type == "commission"` branch in calculator
- Defer until QC implementation is complete

**Config Notes**:
> "Commission employees: 1/60 of wages in 12 weeks (pending implementation, requires employee type identifier support)."

---

## Completed Items

_Items will be moved here after implementation_

---

## References

- [BC Employment Standards Act - Statutory Holidays](https://www2.gov.bc.ca/gov/content/employment-business/employment-standards-advice/employment-standards/statutory-holidays)
- [Alberta Employment Standards Code - General Holidays](https://www.alberta.ca/alberta-general-holidays)
- [Canada Labour Code Part III](https://laws-lois.justice.gc.ca/eng/acts/L-2/)
- [Nova Scotia Labour Standards Code](https://novascotia.ca/lae/employmentrights/)
- [Manitoba Employment Standards Code](https://www.gov.mb.ca/labour/standards/)
