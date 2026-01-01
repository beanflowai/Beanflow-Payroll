# Saskatchewan - Sick Leave Official Reference

> **Status**: ✅ Verified
> **Last Verified**: 2025-12-31
> **Verified By**: Claude

## Official Sources

| Source | URL |
|--------|-----|
| Saskatchewan Employment Act | https://www.saskatchewan.ca/business/employment-standards/leaves/sick-leave |
| Employment Standards Guide | https://pubsaskdev.blob.core.windows.net/pubsask-prod/76937/V14-EmploymentStandards.pdf |

---

## Important Note: Job Protection vs. Sick Leave

Saskatchewan's Employment Act does NOT provide statutory "sick leave" as a standalone entitlement. Instead, it provides **job protection for absence due to illness**. This is an important distinction:

- Employees are protected from termination when absent due to illness
- The leave is **unpaid** - there is no statutory requirement for employers to pay wages during illness absence
- The protection is framed as "job protection for illness absence" rather than "sick leave entitlement"

---

## Sick Leave Entitlement

| Type | Days per Year | Notes |
|------|---------------|-------|
| Paid Sick Leave | 0 | Not required by Saskatchewan Employment Act |
| Unpaid Job Protection (non-serious illness) | Up to 12 days | Job protection for absence due to illness |
| Unpaid Job Protection (serious illness) | Up to 12 weeks | For serious illness or injury |

---

## Eligibility Rules

| Rule | Value | Notes |
|------|-------|-------|
| Waiting Period | 13 weeks (91 days) | Must be employed for 13+ consecutive weeks |
| Applies to | All employees | Full-time, part-time, and casual workers covered by Employment Act |

---

## Accrual Method

- **Method**: immediate (upon meeting eligibility)
- **Initial Days After Qualifying**: N/A - job protection, not accrued leave
- **Days Per Month After Initial**: N/A
- **Maximum Days**: 12 days (non-serious) or 12 weeks (serious illness)

---

## Carryover Rules

| Rule | Value |
|------|-------|
| Allows Carryover | No |
| Max Carryover Days | 0 |
| Expiry | Calendar year basis |

---

## Pay Calculation

- **Formula**: N/A - Leave is unpaid
- **Rate**: $0 - No statutory pay requirement

Employees may be eligible for federal Employment Insurance (EI) Sickness Benefits if they meet EI eligibility requirements.

---

## Medical Certificate Requirements

- **Required After**: Employer may request a medical certificate
- **Notes**:
  - Employers can require medical documentation to verify the need for leave
  - **As of January 1, 2026**: Restrictions on when employers can require sick notes (see Upcoming Changes below)

---

## Upcoming Changes (January 1, 2026)

Saskatchewan has announced amendments to the Employment Act effective January 1, 2026:

| Change | Current | New (Jan 1, 2026) |
|--------|---------|-------------------|
| Long-term sick leave | 12 weeks | 27 weeks |
| Sick note restrictions | None | Employers restricted from requiring sick notes in certain circumstances |

---

## Job Protection Details

### Non-Serious Illness or Injury
- **Duration**: Up to 12 days per calendar year
- **Eligibility**: 13+ weeks of employment
- **Notice**: Employee should notify employer as soon as reasonably practicable

### Serious Illness or Injury
- **Duration**: Up to 12 weeks (extending to 27 weeks as of Jan 1, 2026)
- **Eligibility**: 13+ weeks of employment
- **Definition**: Illness or injury that requires significant medical attention or extended recovery

---

## Config Verification Checklist

Compare with `backend/config/sick_leave/2025/provinces_jan.json`:

- [x] `paid_days_per_year`: 0 - Correct (no paid sick leave in Saskatchewan)
- [ ] `unpaid_days_per_year`: 0 - **Should be 12** (12 days job protection for non-serious illness)
- [x] `waiting_period_days`: 0 - **Should be 91** (13 weeks = 91 days eligibility requirement)
- [x] `allows_carryover`: false - Correct
- [x] `max_carryover_days`: 0 - Correct
- [x] `accrual_method`: "immediate" - Correct
- [ ] `notes` - Should clarify this is job protection, not traditional sick leave

---

## Differences Found

| Field | Official | Current Config | Action Needed |
|-------|----------|----------------|---------------|
| `unpaid_days_per_year` | 12 days | 0 | Update to 12 (job-protected days for non-serious illness) |
| `waiting_period_days` | 91 days (13 weeks) | 0 | Update to 91 |
| `notes` | Job protection for illness absence | "No statutory sick leave in Saskatchewan" | Update to clarify distinction |

---

## Recommended Config Update

```json
"SK": {
  "paid_days_per_year": 0,
  "unpaid_days_per_year": 12,
  "waiting_period_days": 91,
  "allows_carryover": false,
  "max_carryover_days": 0,
  "accrual_method": "immediate",
  "notes": "No paid sick leave. 12 days/year job protection for non-serious illness; 12 weeks for serious illness. 13+ weeks employment required. Unpaid but job-protected. Jan 1, 2026: long-term leave extends to 27 weeks."
}
```

---

## References

1. Saskatchewan Employment Act, Part II, Division 6 - Leaves of Absence
2. Saskatchewan Employment Standards - Sick Leave: https://www.saskatchewan.ca/business/employment-standards/leaves/sick-leave
3. Government of Saskatchewan 2024 Budget Announcements (re: 2026 changes)
