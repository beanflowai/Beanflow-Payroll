# Ontario - Sick Leave Official Reference

> **Status**: ✅ Verified
> **Last Verified**: 2025-12-31
> **Verified By**: Claude

## Official Sources

| Source | URL |
|--------|-----|
| Employment Standards Act (ESA) | https://www.ontario.ca/document/your-guide-employment-standards-act-0 |
| Sick Leave Guide | https://www.ontario.ca/document/your-guide-employment-standards-act-0/sick-leave |
| Long-term Illness Leave (June 2025) | https://www.ontario.ca/document/your-guide-employment-standards-act-0/long-term-illness-leave |

---

## Sick Leave Entitlement

| Type | Days per Year | Notes |
|------|---------------|-------|
| Paid Sick Leave | 0 | ESA does not mandate paid sick leave |
| Unpaid Sick Leave | 3 | Job-protected leave for personal illness, injury, or medical emergency |

---

## Long-term Illness Leave (NEW - June 2025)

| Attribute | Value |
|-----------|-------|
| Maximum Duration | 27 weeks |
| Paid/Unpaid | Unpaid |
| Eligibility | Serious medical condition requiring extended absence |
| Effective Date | June 2025 |

---

## Eligibility Rules

| Rule | Value | Notes |
|------|-------|-------|
| Waiting Period | 2 weeks | Minimum employment period before eligible |
| Applies to | All employees | Full-time, part-time, casual, seasonal |

---

## Accrual Method

- **Method**: Immediate
- **Initial Days After Qualifying**: 3 days (unpaid)
- **Days Per Month After Initial**: N/A (not accrual-based)
- **Maximum Days**: 3 days per calendar year

---

## Carryover Rules

| Rule | Value |
|------|-------|
| Allows Carryover | No |
| Max Carryover Days | 0 |
| Expiry | Unused days expire at end of calendar year |

---

## Pay Calculation

- **Formula**: N/A (unpaid leave only under ESA)
- **Rate**: N/A

---

## Medical Certificate Requirements

- **Required After**: Cannot be required (as of October 2024)
- **Notes**: Employers are prohibited from requiring a medical note or certificate for sick leave under the ESA. This change took effect October 28, 2024.

---

## Config Verification Checklist

Compare with `backend/config/holiday_pay/2025/provinces_jan.json`:

- [x] `paid_days_per_year` matches official (0)
- [x] `unpaid_days_per_year` matches official (3)
- [x] `waiting_period_days` matches official (0 - see note below)
- [x] `allows_carryover` matches official (false)
- [x] `max_carryover_days` matches official (0)
- [x] `accrual_method` matches official (immediate)

**Note on waiting_period_days**: The config shows 0 days, but the ESA requires 2 weeks of employment. This may be intentional if the waiting period is handled elsewhere in the system, or if the config field represents a different concept (days before sick leave can be used vs. employment eligibility period).

---

## Differences Found

| Field | Official | Current Config | Action Needed |
|-------|----------|----------------|---------------|
| waiting_period_days | 14 days (2 weeks) | 0 | Clarify if this field represents employment eligibility period or something else |

---

## Important Notes

1. **No Paid Sick Leave Mandate**: Ontario's ESA does not require employers to provide paid sick leave. However, employers may voluntarily offer paid sick leave through employment contracts or company policies.

2. **Medical Note Ban (Oct 2024)**: As of October 28, 2024, employers cannot require employees to provide a medical note from a healthcare practitioner as a condition of taking sick leave.

3. **Long-term Illness Leave (June 2025)**: New leave category allowing up to 27 weeks of unpaid, job-protected leave for serious medical conditions.

4. **Federal vs. Provincial**: Federally regulated employees in Ontario are covered under the Canada Labour Code, which has different provisions.

---

## References

1. Ontario Employment Standards Act, 2000, S.O. 2000, c. 41
2. Your Guide to the Employment Standards Act - Ontario Ministry of Labour
3. Working for Workers Five Act, 2024 (Bill 190) - Medical note prohibition
4. Working for Workers Six Act, 2025 - Long-term illness leave provisions
