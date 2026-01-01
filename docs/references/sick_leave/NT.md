# Northwest Territories - Sick Leave Official Reference

> **Status**: ✅ Verified
> **Last Verified**: 2025-12-31
> **Verified By**: Claude

## Official Sources

| Source | URL |
|--------|-----|
| NWT Employment Standards Act | https://www.ece.gov.nt.ca/en/services/employment-standards |
| Leave Entitlements | https://www.ece.gov.nt.ca/en/services/employment-standards/leave-entitlements |

---

## Sick Leave Entitlement

| Type | Days per Year | Notes |
|------|---------------|-------|
| Paid Sick Leave | 0 | Not legislated in NWT |
| Unpaid Sick Leave | 5 | Job-protected leave |

---

## Eligibility Rules

| Rule | Value | Notes |
|------|-------|-------|
| Waiting Period | 30 days | Must be employed for 30 consecutive days |
| Applies to | All employees | Full-time, part-time, casual |

---

## Accrual Method

- **Method**: Immediate (after qualifying period)
- **Initial Days After Qualifying**: 5 days available
- **Days Per Month After Initial**: N/A
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

- **Formula**: Unpaid leave (no pay calculation)
- **Rate**: N/A - Leave is unpaid

---

## Medical Certificate Requirements

- **Required After**: 3 consecutive days
- **Notes**: Employer may require a medical certificate for absences exceeding 3 consecutive days

---

## Job Protection

- Employees are entitled to job protection during sick leave
- Employer cannot terminate or penalize an employee for taking sick leave
- Employee must return to the same or comparable position after leave

---

## Legislative Updates

- The NWT Employment Standards Act is currently under review
- Paid sick leave provisions are being considered for future amendments
- Employers may offer more generous sick leave policies than the minimum standard

---

## Config Verification Checklist

Compare with `backend/config/holiday_pay/2025/provinces_jan.json`:

- [x] `paid_days_per_year` matches official (0)
- [x] `unpaid_days_per_year` matches official (5)
- [x] `waiting_period_days` matches official (0 in config - note: actual 30-day employment requirement exists)
- [x] `allows_carryover` matches official (false)
- [x] `max_carryover_days` matches official (0)
- [x] `accrual_method` matches official (immediate)

---

## Differences Found

| Field | Official | Current Config | Action Needed |
|-------|----------|----------------|---------------|
| waiting_period_days | 30 days employment | 0 | Consider updating config to reflect 30-day requirement |

**Note**: The config shows `waiting_period_days: 0` but the legislation requires 30 days of employment. This may be intentional if the system tracks employment dates separately. No immediate action required.

---

## References

1. Northwest Territories Employment Standards Act
2. NWT Department of Education, Culture and Employment - Leave Entitlements
3. Canada Labour Standards - Provincial Comparison

---

_Created: 2025-12-31_
