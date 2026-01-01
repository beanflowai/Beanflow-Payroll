# Alberta - Sick Leave Official Reference

> **Status**: ✅ Verified
> **Last Verified**: 2025-12-31
> **Verified By**: Claude

## Official Sources

| Source | URL |
|--------|-----|
| Employment Standards | https://www.alberta.ca/employment-standards |
| Personal and Family Responsibility Leave | https://www.alberta.ca/personal-family-responsibility-leave |
| Long-term Illness and Injury Leave | https://www.alberta.ca/long-term-illness-injury-leave |

---

## Sick Leave Entitlement

| Type | Days per Year | Notes |
|------|---------------|-------|
| Paid Sick Leave | 0 | Not legislated in Alberta |
| Unpaid Sick Leave (Personal and Family Responsibility Leave) | 5 | For personal illness/injury OR family care |
| Long-term Illness Leave | 16 weeks (unpaid) | Increasing to 27 weeks on Jan 1, 2026 |

**Important**: Alberta does NOT have statutory paid sick leave. The "Personal and Family Responsibility Leave" is a combined leave category that can be used for personal illness/injury, caring for ill family members, or addressing family emergencies.

---

## Eligibility Rules

| Rule | Value | Notes |
|------|-------|-------|
| Waiting Period | 90 days | Must be employed 90+ days to be eligible |
| Applies to | All employees | Full-time, part-time, casual |

---

## Accrual Method

- **Method**: immediate (after qualifying period)
- **Initial Days After Qualifying**: 5 days
- **Days Per Month After Initial**: N/A (annual entitlement)
- **Maximum Days**: 5 per calendar year

---

## Carryover Rules

| Rule | Value |
|------|-------|
| Allows Carryover | No |
| Max Carryover Days | 0 |
| Expiry | Unused days do not carry over to next year |

---

## Pay Calculation

- **Formula**: N/A (unpaid leave)
- **Rate**: $0 - No pay required for Personal and Family Responsibility Leave

---

## Medical Certificate Requirements

- **Required After**: Not specified in legislation
- **Notes**: Employer may request "reasonable verification" but cannot require a medical certificate for short absences

---

## Long-term Illness and Injury Leave

Alberta provides separate protection for longer absences:

| Current (2025) | Effective Jan 1, 2026 |
|----------------|----------------------|
| Up to 16 weeks unpaid | Up to 27 weeks unpaid |

Requirements:
- Employee must have worked for the same employer for at least 90 days
- Leave is job-protected but unpaid
- May run concurrently with short-term disability or EI sickness benefits

---

## Config Verification Checklist

Compare with `backend/config/holiday_pay/2025/provinces_jan.json`:

- [x] `paid_days_per_year` matches official (0 = correct)
- [ ] `unpaid_days_per_year` **DOES NOT MATCH** (config shows 0, should be 5)
- [ ] `waiting_period_days` **DOES NOT MATCH** (config shows 0, should be 90)
- [x] `allows_carryover` matches official (false = correct)
- [x] `max_carryover_days` matches official (0 = correct)
- [x] `accrual_method` matches official (immediate = correct)

---

## Differences Found

| Field | Official | Current Config | Action Needed |
|-------|----------|----------------|---------------|
| `unpaid_days_per_year` | 5 | 0 | Update to 5 |
| `waiting_period_days` | 90 | 0 | Update to 90 |
| `notes` | "Personal and Family Responsibility Leave - 5 days unpaid after 90 days employment" | "No statutory sick leave in Alberta" | Update to clarify unpaid leave exists |

**Note**: The current config note "No statutory sick leave" is technically accurate for PAID sick leave, but Alberta does have 5 days of unpaid "Personal and Family Responsibility Leave" that can be used for illness. The config should reflect this unpaid entitlement.

---

## References

1. Alberta Employment Standards - Personal and Family Responsibility Leave
2. Alberta Employment Standards - Long-term Illness and Injury Leave
3. Alberta Employment Standards Code, Part 2, Division 7.4
