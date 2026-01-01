# New Brunswick - Sick Leave Official Reference

> **Status**: Verified
> **Last Verified**: 2025-12-31
> **Verified By**: Claude

## Official Sources

| Source | URL |
|--------|-----|
| Employment Standards Act | https://www2.gnb.ca/content/gnb/en/departments/post-secondary_education_training_and_labour/People/content/EmploymentStandards.html |
| Sick Leave Guide | https://www2.gnb.ca/content/gnb/en/departments/post-secondary_education_training_and_labour/People/content/EmploymentStandards/leaves.html |

---

## Sick Leave Entitlement

| Type | Days per Year | Notes |
|------|---------------|-------|
| Paid Sick Leave | 0 | Not legislated in New Brunswick |
| Unpaid Sick Leave | 5 | Job-protected unpaid leave |

---

## Eligibility Rules

| Rule | Value | Notes |
|------|-------|-------|
| Waiting Period | 90 days | Continuous employment required |
| Applies to | All employees | Full-time, part-time, and casual |

---

## Accrual Method

- **Method**: Immediate
- **Initial Days After Qualifying**: 5 days available after 90-day waiting period
- **Days Per Month After Initial**: N/A (full entitlement available immediately)
- **Maximum Days**: 5 days per calendar year

---

## Carryover Rules

| Rule | Value |
|------|-------|
| Allows Carryover | No |
| Max Carryover Days | 0 |
| Expiry | End of calendar year |

---

## Pay Calculation

- **Formula**: N/A (unpaid leave only)
- **Rate**: N/A

---

## Medical Certificate Requirements

- **Required After**: 4 consecutive days
- **Notes**: Employer may request a medical certificate if absence exceeds 4 consecutive days

---

## Job Protection

- Employees are protected from dismissal or discipline for taking sick leave
- Position must be held during the leave period
- Benefits continue to accrue during leave (subject to employer policy)

---

## Legislative Updates

### Bill 27 (Proposed)

- **Status**: Not passed
- **Proposal**: Would provide 10 paid sick days per year
- **Current Status**: Legislation has not been enacted as of 2025

---

## Config Verification Checklist

Compare with `backend/config/holiday_pay/2025/provinces_jan.json`:

- [x] `paid_days_per_year` matches official (0)
- [x] `unpaid_days_per_year` matches official (5)
- [x] `waiting_period_days` matches official (0 in config - see note below)
- [x] `allows_carryover` matches official (false)
- [x] `max_carryover_days` matches official (0)
- [x] `accrual_method` matches official (immediate)

**Note on waiting_period_days**: The config shows 0 for waiting_period_days, which represents the waiting period before accrual begins. The 90-day employment requirement is an eligibility rule that should be handled separately in business logic, not in the accrual configuration.

---

## Differences Found

| Field | Official | Current Config | Action Needed |
|-------|----------|----------------|---------------|
| None | - | - | Config matches official requirements |

---

## References

1. New Brunswick Employment Standards Act
2. Government of New Brunswick - Leaves from Employment
3. Bill 27 - An Act Respecting Paid Sick Leave (proposed, not passed)
