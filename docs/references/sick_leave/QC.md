# Quebec - Sick Leave Official Reference

> **Status**: ✅ Verified
> **Last Verified**: 2025-12-31
> **Verified By**: Claude

## Official Sources

| Source | URL |
|--------|-----|
| CNESST - Act Respecting Labour Standards | https://www.cnesst.gouv.qc.ca/en/working-conditions/leave/personal-leave |
| Quebec Labour Standards | https://www.quebec.ca/en/employment/labour-standards |

---

## Sick Leave Entitlement

| Type | Days per Year | Notes |
|------|---------------|-------|
| Paid Sick Leave | 2 days | Part of broader personal leave category (10 days total) |
| Unpaid Sick Leave | Up to 26 weeks | For illness, organ/tissue donation, accident, domestic/sexual violence |

---

## Eligibility Rules

| Rule | Value | Notes |
|------|-------|-------|
| Waiting Period | 90 days (3 months) | Must complete 3 months of continuous service |
| Applies to | All employees | Full-time, part-time, temporary, seasonal |

---

## Accrual Method

- **Method**: Immediate (after qualifying period)
- **Initial Days After Qualifying**: 2 paid days available immediately
- **Days Per Month After Initial**: N/A (not monthly accrual)
- **Maximum Days**: 2 paid days per calendar year

---

## Carryover Rules

| Rule | Value |
|------|-------|
| Allows Carryover | No |
| Max Carryover Days | 0 |
| Expiry | End of calendar year |

---

## Pay Calculation

- **Formula**: 1/20th of wages earned in the 4 complete weeks of pay preceding the leave
- **Rate**: Daily rate = (4 weeks wages) / 20
- **Includes**: Regular wages, tips, commissions
- **Excludes**: Overtime pay

**Example**: If employee earned $4,000 in the 4 weeks before absence, daily rate = $4,000 / 20 = $200

---

## Medical Certificate Requirements

- **Required After**: 3 days (as of January 2025)
- **Notes**:
  - Employer cannot require documentation for absences of 3 consecutive days or less
  - For longer absences, employer may request reasonable documentation
  - This change took effect January 1, 2025

---

## Extended Leave for Illness

Quebec provides additional unpaid leave protections:

| Leave Type | Duration | Eligibility |
|------------|----------|-------------|
| Illness or Accident | Up to 26 weeks over 12 months | After 3 months service |
| Organ/Tissue Donation | Up to 26 weeks over 12 months | After 3 months service |

---

## Personal Leave Context

In Quebec, sick leave is part of a broader "personal leave" category:

| Leave Type | Paid Days | Unpaid Days | Total |
|------------|-----------|-------------|-------|
| Illness | 2 | 8 | 10 |
| Family obligations | (shared) | (shared) | (shared) |

Note: The 2 paid days and 8 unpaid days (10 total) can be used for various personal reasons including illness, family obligations, and other personal matters.

---

## Config Verification Checklist

Compare with `backend/config/holiday_pay/2025/provinces_jan.json`:

- [x] `paid_days_per_year`: 2 - Matches official
- [ ] `unpaid_days_per_year`: 0 - **NEEDS UPDATE** - Should reflect unpaid personal leave days
- [x] `waiting_period_days`: 90 - Matches official (3 months)
- [x] `allows_carryover`: false - Matches official
- [x] `max_carryover_days`: 0 - Matches official
- [x] `accrual_method`: immediate - Matches official

---

## Differences Found

| Field | Official | Current Config | Action Needed |
|-------|----------|----------------|---------------|
| `unpaid_days_per_year` | 8 days (personal leave) or 26 weeks (extended illness) | 0 | Consider updating - depends on how system models unpaid leave |

**Note on Unpaid Days**: The current config shows 0 unpaid days. Quebec allows:
1. **8 additional unpaid personal leave days** (part of 10-day personal leave total)
2. **Up to 26 weeks unpaid leave** for serious illness/injury

The appropriate config value depends on system design:
- If tracking personal leave category: `unpaid_days_per_year: 8`
- If only tracking short-term sick leave: `unpaid_days_per_year: 0` may be acceptable
- Extended illness leave (26 weeks) is typically handled separately

---

## References

1. CNESST - Personal Leave: https://www.cnesst.gouv.qc.ca/en/working-conditions/leave/personal-leave
2. Act Respecting Labour Standards (R.S.Q., c. N-1.1), Sections 79.7 to 79.16
3. Bill 176 (2018) - Amendments to Labour Standards
4. Bill 68 (2024) - Medical certificate restrictions effective January 2025
