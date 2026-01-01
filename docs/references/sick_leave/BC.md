# British Columbia - Sick Leave Official Reference

> **Status**: ✅ Verified
> **Last Verified**: 2025-12-31
> **Verified By**: Claude

## Official Sources

| Source | URL |
|--------|-----|
| BC Employment Standards Act | https://www.bclaws.gov.bc.ca/civix/document/id/complete/statreg/00_96113_01 |
| BC Paid Sick Leave Guide | https://www2.gov.bc.ca/gov/content/employment-business/employment-standards-advice/paid-sick-leave |
| WorkSafeBC Information | https://www.worksafebc.com/ |

---

## Sick Leave Entitlement

| Type | Days per Year | Notes |
|------|---------------|-------|
| Paid Sick Leave | 5 days | Effective January 1, 2022 |
| Unpaid Sick Leave | 3 days | In addition to paid leave |

---

## Eligibility Rules

| Rule | Value | Notes |
|------|-------|-------|
| Waiting Period | 90 days | Days of employment before eligible for paid sick leave |
| Applies to | All employees | Full-time, part-time, casual; no minimum hours requirement |
| Unpaid Leave | Immediate | No waiting period for unpaid sick leave |

---

## Accrual Method

- **Method**: Immediate (full entitlement after qualifying period)
- **Initial Days After Qualifying**: 5 paid days available immediately after 90-day waiting period
- **Days Per Month After Initial**: N/A (not accrual-based)
- **Maximum Days**: 5 paid + 3 unpaid per year

---

## Carryover Rules

| Rule | Value |
|------|-------|
| Allows Carryover | No |
| Max Carryover Days | 0 |
| Expiry | End of calendar year (unused days do not carry over) |

---

## Pay Calculation

- **Formula**: Regular wages for the day
- **Rate**: Average day's pay (total wages earned in 30 calendar days before leave, divided by days worked)
- **Includes**: Regular wages; does not include overtime

---

## Medical Certificate Requirements

- **Required After**: Cannot require for first 2 absences of 5 days or less (as of November 2025)
- **Notes**:
  - New regulation effective November 2025 prohibits employers from requiring a sick note for the first two absences of 5 consecutive days or less in a calendar year
  - Employers may still require documentation for longer absences or after the first two qualifying absences
  - Employers cannot require employees to provide a reason for taking sick leave

---

## Config Verification Checklist

Compare with `backend/config/sick_leave/2025/provinces_jan.json`:

- [x] `paid_days_per_year` matches official (5 days)
- [x] `unpaid_days_per_year` matches official (3 days)
- [x] `waiting_period_days` matches official (90 days)
- [x] `allows_carryover` matches official (false)
- [x] `max_carryover_days` matches official (0)
- [x] `accrual_method` matches official (immediate)

---

## Differences Found

| Field | Official | Current Config | Action Needed |
|-------|----------|----------------|---------------|
| None | - | - | Config matches official requirements |

---

## Additional Notes

### Recent Changes (November 2025)
- Employers can no longer require a sick note for the first two absences of 5 consecutive days or less per calendar year
- This change aims to reduce burden on healthcare system and employees

### Key Points
- Sick leave is job-protected; employees cannot be fired or penalized for taking entitled sick leave
- Part-time employees receive the same number of days (not prorated)
- Sick leave can be used for personal illness, injury, or medical appointments
- Leave can also be used for caring for dependents' health needs

---

## References

1. BC Employment Standards Act, Part 6 - Leaves and Jury Duty
2. BC Government Paid Sick Leave Information Page
3. BC Employment Standards Branch - Sick Leave Factsheet
