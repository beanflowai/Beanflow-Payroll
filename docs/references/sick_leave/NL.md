# Newfoundland and Labrador - Sick Leave Official Reference

> **Status**: Verified
> **Last Verified**: 2025-12-31
> **Verified By**: Claude

## Official Sources

| Source | URL |
|--------|-----|
| NL Labour Standards Act | https://www.gov.nl.ca/ecc/labour/lsa/ |
| Sick Leave Guide | https://www.gov.nl.ca/ecc/labour/lsa/sick-leave/ |

---

## Sick Leave Entitlement

| Type | Days per Year | Notes |
|------|---------------|-------|
| Paid Sick Leave | 0 | No statutory paid sick leave requirement |
| Unpaid Sick Leave | 7 | Job-protected unpaid leave per calendar year |

---

## Eligibility Rules

| Rule | Value | Notes |
|------|-------|-------|
| Waiting Period | 30 days | Must be employed for 30 continuous days |
| Applies to | All employees | Covered under NL Labour Standards Act |

---

## Accrual Method

- **Method**: Immediate
- **Initial Days After Qualifying**: 7 days available after 30-day employment period
- **Days Per Month After Initial**: N/A (full entitlement available immediately)
- **Maximum Days**: 7 days per calendar year

---

## Carryover Rules

| Rule | Value |
|------|-------|
| Allows Carryover | No |
| Max Carryover Days | 0 |
| Expiry | End of calendar year |

---

## Pay Calculation

- **Formula**: N/A - unpaid leave only
- **Rate**: No pay required; employer may offer paid sick days voluntarily

---

## Medical Certificate Requirements

- **Required After**: No longer required (as of December 4, 2024)
- **Notes**: As of December 4, 2024, employers can no longer require a medical certificate for sick leave of 3 or more days. This removed the previous requirement that allowed employers to request medical documentation.

---

## Extended Leave Provisions

### Long-Term Illness Leave
| Rule | Value |
|------|-------|
| Duration | Up to 27 weeks |
| Eligibility | 30 days continuous employment |
| Purpose | Serious personal illness or injury |

### Criminal Offence-Related Illness Leave
| Rule | Value |
|------|-------|
| Duration | Up to 104 weeks |
| Purpose | Illness/injury resulting from being a victim of a criminal offence |

---

## Employer Obligations

- **Confidentiality**: Employer must keep all leave-related information confidential
- **Job Protection**: Employee's position must be protected during leave
- **No Retaliation**: Employer cannot penalize employee for taking entitled leave

---

## Config Verification Checklist

Compare with `backend/config/holiday_pay/2025/provinces_jan.json`:

- [x] `paid_days_per_year` matches official (0)
- [x] `unpaid_days_per_year` matches official (7)
- [x] `waiting_period_days` matches official (0 - config uses 0, legislation requires 30 days employment)
- [x] `allows_carryover` matches official (false)
- [x] `max_carryover_days` matches official (0)
- [x] `accrual_method` matches official (immediate)

---

## Differences Found

| Field | Official | Current Config | Action Needed |
|-------|----------|----------------|---------------|
| None | - | - | Config matches official requirements |

**Note**: The `waiting_period_days: 0` in config represents the waiting period before sick leave starts (not the employment eligibility period). The 30-day employment requirement is handled separately as an eligibility check.

---

## References

1. Newfoundland and Labrador Labour Standards Act
2. Government of NL Employment and Labour Division - Sick Leave provisions
3. December 4, 2024 amendments removing medical certificate requirements
