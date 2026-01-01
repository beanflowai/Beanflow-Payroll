# Federal (Canada Labour Code) - Sick Leave Official Reference

> **Status**: ✅ Verified
> **Last Verified**: 2025-12-31
> **Verified By**: Claude

## Official Sources

| Source | URL |
|--------|-----|
| Canada Labour Code | https://laws-lois.justice.gc.ca/eng/acts/L-2/ |
| Medical Leave with Pay Guide | https://www.canada.ca/en/employment-social-development/programs/laws-regulations/labour/interpretations-policies/medical-leave-pay.html |
| ESDC - Leaves of Absence | https://www.canada.ca/en/services/jobs/workplace/federal-labour-standards/leaves.html |

---

## Sick Leave Entitlement

| Type | Days per Year | Notes |
|------|---------------|-------|
| Paid Sick Leave | 10 days | Effective December 1, 2022 |
| Unpaid Sick Leave | 0 days | Additional 17 weeks unpaid available for long-term illness |

---

## Eligibility Rules

| Rule | Value | Notes |
|------|-------|-------|
| Waiting Period | 30 days | Must complete 30 consecutive days of continuous employment |
| Applies to | All employees | Full-time, part-time, casual, and seasonal workers in federally regulated industries |

---

## Accrual Method

- **Method**: Monthly accrual with initial grant
- **Initial Days After Qualifying**: 3 days (granted after completing 30-day qualifying period)
- **Days Per Month After Initial**: 1 day per month of continuous employment
- **Maximum Days**: 10 days per calendar year

---

## Carryover Rules

| Rule | Value |
|------|-------|
| Allows Carryover | Yes |
| Max Carryover Days | 10 days |
| Expiry | Unused days carry over to next year up to maximum of 10 total |

---

## Pay Calculation

- **Formula**: Regular rate of wages x Normal hours of work
- **Rate**: Employee's regular rate of wages (what they would have earned if they had worked their normal hours that day)

---

## Medical Certificate Requirements

- **Required After**: 5 consecutive days
- **Notes**: Employer may request a medical certificate for absences of 5 or more consecutive days. Certificate must be from a qualified health practitioner.

---

## Config Verification Checklist

Compare with `backend/config/holiday_pay/2025/provinces_jan.json`:

- [x] `paid_days_per_year` matches official (10 days)
- [x] `unpaid_days_per_year` matches official (0 days)
- [x] `waiting_period_days` matches official (30 days)
- [x] `allows_carryover` matches official (true)
- [x] `max_carryover_days` matches official (10 days)
- [x] `accrual_method` matches official (monthly)
- [x] `initial_days_after_qualifying` matches official (3 days)
- [x] `days_per_month_after_initial` matches official (1 day)

---

## Differences Found

| Field | Official | Current Config | Action Needed |
|-------|----------|----------------|---------------|
| None | - | - | Config matches official requirements |

---

## Additional Notes

### Federally Regulated Industries

The Canada Labour Code applies to federally regulated private-sector employers, including:
- Banking
- Telecommunications
- Broadcasting
- Air transportation
- Rail and road transportation (inter-provincial)
- Shipping
- Crown corporations
- First Nations band councils

### Key Dates

- **December 1, 2022**: 10 days paid medical leave came into effect (previously 0 paid days)

### Related Leaves

Employees may also be entitled to:
- 17 weeks unpaid medical leave for serious illness/injury
- Personal leave (up to 5 days, first 3 paid after 3 months employment)

---

## References

1. Canada Labour Code, Part III, Division VII - Medical Leave with Pay
2. Employment and Social Development Canada - Medical leave with pay interpretations and policies
3. Bill C-3, An Act to amend the Criminal Code and the Canada Labour Code (2021)
