# Nova Scotia - Sick Leave Official Reference

> **Status**: ⚠️ Needs Update
> **Last Verified**: 2025-12-31
> **Verified By**: Claude

## Official Sources

| Source | URL |
|--------|-----|
| Employment Standards | https://novascotia.ca/lae/employmentrights/ |
| Labour Standards Code | https://www.novascotia.ca/just/regulations/regs/lstdcode.htm |

---

## Sick Leave Entitlement

| Type | Days per Year | Notes |
|------|---------------|-------|
| Paid Sick Leave | 0 days | No provincial requirement for paid sick leave |
| Unpaid Sick Leave | 5 days | Personal illness or injury (as of Jan 1, 2025) |
| Medical Appointments / Family Illness | 3 days | Additional unpaid days for appointments or caring for ill family |
| **Total Unpaid Leave** | **8 days** | Combined annual entitlement |

### Long-Term Sick Leave

| Type | Duration | Eligibility |
|------|----------|-------------|
| Serious Illness/Injury Leave | Up to 27 weeks | 3 months employment required |

**Note**: The 27-week unpaid leave for serious illness aligns with Employment Insurance (EI) sickness benefits eligibility.

---

## Eligibility Rules

| Rule | Value | Notes |
|------|-------|-------|
| Waiting Period (Standard Sick Leave) | 0 days | Eligible immediately upon employment |
| Waiting Period (Serious Illness Leave) | 90 days | 3 months employment required |
| Applies to | All employees | Full-time, part-time, casual |

---

## Accrual Method

- **Method**: Immediate
- **Initial Days After Qualifying**: 5 days (sick) + 3 days (medical/family) available immediately
- **Days Per Month After Initial**: N/A
- **Maximum Days**: 8 days unpaid per year

---

## Carryover Rules

| Rule | Value |
|------|-------|
| Allows Carryover | No |
| Max Carryover Days | 0 |
| Expiry | Unused days do not carry forward to next year |

---

## Pay Calculation

- **Formula**: N/A (unpaid leave)
- **Rate**: $0 (no paid sick leave requirement)

---

## Medical Certificate Requirements

- **Required After**: Employer may request medical certificate after 5 consecutive days
- **Notes**: Employer cannot require certificate for shorter absences unless pattern of abuse suspected

---

## Recent Legislative Changes (January 1, 2025)

The Nova Scotia Labour Standards Code was amended effective January 1, 2025:

| Previous | Current (2025) |
|----------|----------------|
| 3 unpaid sick days | 5 unpaid sick days |
| Plus 3 medical/family days | Plus 3 medical/family days (unchanged) |
| **Total: 6 days** | **Total: 8 days** |

---

## Pending Legislation

**Bill 31 - Paid Sick Days**:
- **Status**: Proposed (not yet passed as of Dec 2025)
- **Proposed Entitlement**: Up to 10 paid sick days per year
- **Action Required**: Monitor legislative progress

---

## Config Verification Checklist

Compare with `backend/config/holiday_pay/2025/provinces_jan.json`:

- [x] `paid_days_per_year` matches official (0 days - CORRECT)
- [ ] `unpaid_days_per_year` matches official - **MISMATCH** (config: 3, official: 5)
- [x] `waiting_period_days` matches official (0 days - CORRECT)
- [x] `allows_carryover` matches official (false - CORRECT)
- [x] `max_carryover_days` matches official (0 - CORRECT)
- [x] `accrual_method` matches official (immediate - CORRECT)

---

## Differences Found

| Field | Official (2025) | Current Config | Action Needed |
|-------|-----------------|----------------|---------------|
| `unpaid_days_per_year` | 5 | 3 | **UPDATE REQUIRED** - Change from 3 to 5 |
| `notes` | 5 unpaid days + 3 medical/family | "3 unpaid days" | Update to reflect 2025 changes |

### Recommended Config Update

```json
"NS": {
  "paid_days_per_year": 0,
  "unpaid_days_per_year": 5,
  "waiting_period_days": 0,
  "allows_carryover": false,
  "max_carryover_days": 0,
  "accrual_method": "immediate",
  "notes": "Nova Scotia Labour Standards Code - 5 unpaid sick days + 3 unpaid days for medical appointments/family illness (8 total). 27 weeks unpaid for serious illness (3 months employment required)."
}
```

---

## References

1. Nova Scotia Labour Standards Code, Section 60E - Sick Leave
2. Government of Nova Scotia Employment Standards - Leave provisions
3. Bill 31 - An Act to Amend Chapter 246 of the Revised Statutes, 1989, the Labour Standards Code (Paid Sick Days)
