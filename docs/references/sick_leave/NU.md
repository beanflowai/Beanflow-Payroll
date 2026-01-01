# Nunavut - Sick Leave Official Reference

> **Status**: ⚠️ Needs Update
> **Last Verified**: 2025-12-31
> **Verified By**: Claude

## Official Sources

| Source | URL |
|--------|-----|
| Nunavut Labour Standards Act | https://www.nunavutlegislation.ca/en/consolidated-law/labour-standards-act |
| Labour Standards Compliance Office | https://www.gov.nu.ca/family-services/information/labour-standards |

---

## Sick Leave Entitlement

| Type | Days per Year | Notes |
|------|---------------|-------|
| Paid Sick Leave | 0 days | Not legislated in Nunavut |
| Unpaid Sick Leave | 3 days | For employee's own illness or family member illness |

---

## Eligibility Rules

| Rule | Value | Notes |
|------|-------|-------|
| Waiting Period | 3 months | Consecutive employment required |
| Applies to | All employees | Covered under Labour Standards Act |

---

## Accrual Method

- **Method**: immediate
- **Initial Days After Qualifying**: 3 unpaid days available after 3 months
- **Days Per Month After Initial**: N/A
- **Maximum Days**: 3 unpaid days per year

---

## Carryover Rules

| Rule | Value |
|------|-------|
| Allows Carryover | No |
| Max Carryover Days | 0 |
| Expiry | End of year |

---

## Pay Calculation

- **Formula**: Unpaid leave only - no pay calculation required
- **Rate**: N/A

---

## Medical Certificate Requirements

- **Required After**: Employer may request after 3+ consecutive days
- **Notes**: At employer's discretion

---

## Related Leave Provisions

### Compassionate Care Leave

| Aspect | Value |
|--------|-------|
| Duration | Up to 8 weeks unpaid |
| Purpose | Care for gravely ill family member |
| Employment Protection | Yes |

---

## Oversight Authority

**Labour Standards Compliance Office** (Department of Family Services)
- Oversees enforcement of Nunavut Labour Standards Act
- Handles complaints and inquiries

---

## Config Verification Checklist

Compare with `backend/config/holiday_pay/2025/provinces_jan.json`:

- [x] `paid_days_per_year` matches official (0)
- [ ] `unpaid_days_per_year` - **MISMATCH**: Official is 3, config shows 5
- [x] `waiting_period_days` - Official requires 3 months, config shows 0 (needs review)
- [x] `allows_carryover` matches official (false)
- [x] `max_carryover_days` matches official (0)
- [x] `accrual_method` matches official (immediate)

---

## Differences Found

| Field | Official | Current Config | Action Needed |
|-------|----------|----------------|---------------|
| `unpaid_days_per_year` | 3 | 5 | **Update to 3** |
| `waiting_period_days` | 90 (3 months) | 0 | **Update to 90** |
| `notes` | 3 unpaid days | "5 unpaid days" | **Update notes** |

---

## References

1. Nunavut Labour Standards Act - https://www.nunavutlegislation.ca/en/consolidated-law/labour-standards-act
2. Government of Nunavut - Labour Standards - https://www.gov.nu.ca/family-services/information/labour-standards
3. Canada Labour Code (for comparison with federal standards)

---

## Notes

- Nunavut follows territorial labour standards separate from federal jurisdiction
- The territory has minimal paid leave requirements compared to other Canadian jurisdictions
- Employers may offer more generous sick leave policies than the statutory minimum
- Sick leave can be used for employee's own illness or to care for ill family members
