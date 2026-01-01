# Manitoba - Sick Leave Official Reference

> **Status**: ⚠️ Needs Update
> **Last Verified**: 2025-12-31
> **Verified By**: Claude

## Official Sources

| Source | URL |
|--------|-----|
| Employment Standards Code | https://web2.gov.mb.ca/laws/statutes/ccsm/e110.php |
| Family Leave Guide | https://www.gov.mb.ca/labour/standards/doc,family-leave,factsheet.html |
| Long-Term Sick Leave (Bill 9) | https://www.gov.mb.ca/labour/standards/doc,leave-serious-illness-injury,factsheet.html |

---

## Summary

Manitoba does **not** have dedicated statutory sick leave. However, employees can use **Family Leave** for personal illness or health reasons. This is an important distinction from provinces with explicit sick leave provisions.

---

## Sick Leave Entitlement

| Type | Days per Year | Notes |
|------|---------------|-------|
| Paid Sick Leave | 0 | Not legislated in Manitoba |
| Unpaid Sick Leave (via Family Leave) | 3 | Family Leave can be used for personal health reasons |
| Long-Term Leave (Serious Illness/Injury) | 27 weeks | Extended from 17 weeks by Bill 9 |

---

## Family Leave (Used for Sick Leave)

Manitoba's **Family Leave** provision allows employees to take unpaid time off for:
- Personal illness or injury
- Health needs
- Family responsibilities (care for sick family members)
- Urgent matters relating to education of a child

**Key Details**:
- **3 days per year** unpaid
- No waiting period (eligible immediately upon employment)
- Employer cannot require medical certificate for these 3 days
- Can be taken in partial days

---

## Long-Term Sick Leave (Serious Illness or Injury)

| Rule | Value | Notes |
|------|-------|-------|
| Maximum Duration | 27 weeks | Extended from 17 weeks by Bill 9 (2023) |
| Employment Requirement | 90 days | Must be employed at least 90 days |
| Pay Type | Unpaid | No statutory pay requirement |
| Job Protection | Yes | Employer must reinstate to same or comparable position |

---

## Eligibility Rules

| Rule | Value | Notes |
|------|-------|-------|
| Family Leave (3 days) | No waiting period | Available immediately |
| Long-Term Leave | 90 days employment | Required for 27-week leave |
| Applies to | All employees | Full-time, part-time, casual |

---

## Accrual Method

- **Method**: Immediate (per calendar year)
- **Initial Days After Qualifying**: 3 days (Family Leave)
- **Days Per Month After Initial**: N/A
- **Maximum Days**: 3 days per year (short-term), 27 weeks (long-term)

---

## Carryover Rules

| Rule | Value |
|------|-------|
| Allows Carryover | No |
| Max Carryover Days | 0 |
| Expiry | End of calendar year |

---

## Pay Calculation

- **Formula**: N/A (unpaid leave)
- **Rate**: $0 - No statutory requirement for paid sick leave

---

## Medical Certificate Requirements

- **Family Leave (3 days)**: Employer cannot require a medical certificate
- **Long-Term Leave (27 weeks)**: Medical certificate may be required

---

## Config Verification Checklist

Compare with `backend/config/holiday_pay/2025/provinces_jan.json`:

- [x] `paid_days_per_year` matches official (0 - correct)
- [ ] `unpaid_days_per_year` does NOT match - **should be 3** (via Family Leave)
- [x] `waiting_period_days` matches official (0 - correct for Family Leave)
- [x] `allows_carryover` matches official (false - correct)
- [x] `max_carryover_days` matches official (0 - correct)
- [x] `accrual_method` matches official (immediate - correct)

---

## Differences Found

| Field | Official | Current Config | Action Needed |
|-------|----------|----------------|---------------|
| `unpaid_days_per_year` | 3 (via Family Leave) | 0 | Update to 3 |
| `notes` | Should clarify Family Leave usage | "No statutory paid sick leave in Manitoba" | Update to explain Family Leave |

### Recommended Config Update

```json
"MB": {
  "paid_days_per_year": 0,
  "unpaid_days_per_year": 3,
  "waiting_period_days": 0,
  "allows_carryover": false,
  "max_carryover_days": 0,
  "accrual_method": "immediate",
  "notes": "No statutory paid sick leave. 3 days unpaid Family Leave can be used for personal illness. Long-term: 27 weeks unpaid (90 days employment required)."
}
```

---

## Key Distinctions

1. **No "Sick Leave" per se**: Manitoba uses "Family Leave" which covers personal health
2. **Bill 9 (2023)**: Extended long-term leave from 17 to 27 weeks
3. **Family Leave is broad**: Covers illness, family care, and education matters
4. **No medical certificate**: Cannot be required for the 3 days of Family Leave

---

## References

1. Manitoba Employment Standards Code, Part 4 - Leaves of Absence
2. Manitoba Labour - Family Leave Fact Sheet
3. Bill 9 - The Employment Standards Code Amendment Act (Long-term Leave)
4. Manitoba Labour - Leave for Serious Illness or Injury Fact Sheet
