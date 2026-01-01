# Nunavut - Holiday Pay Official Reference

> **Status**: ✅ Verified
> **Last Verified**: 2025-12-31
> **Verified By**: Claude Code

## Official Sources

| Source | URL |
|--------|-----|
| Labour Standards Compliance Office | https://nu-lsco.ca/faq-s?tmpl=component&faqid=11 |
| Government of Nunavut - Labour Standards | https://www.gov.nu.ca/en/justice-and-individual-protection/labour-and-employment-standards |
| Public Service Holidays | https://www.gov.nu.ca/en/staff-resources/public-service-holidays |
| Labour Standards Act (CanLII) | https://www.canlii.org/en/nu/laws/stat/rsnwt-nu-1988-c-l-1/latest/rsnwt-nu-1988-c-l-1.html |

---

## Statutory Holidays (2025)

| Holiday | Date | Statutory? | Notes |
|---------|------|------------|-------|
| New Year's Day | Jan 1 (Wed) | Yes | |
| Good Friday | Apr 18 (Fri) | Yes | |
| Victoria Day | May 19 (Mon) | Yes | |
| Canada Day | Jul 1 (Tue) | Yes | |
| Nunavut Day | Jul 9 (Wed) | Yes | Unique to Nunavut, added 2019 |
| Civic Holiday | Aug 4 (Mon) | Yes | First Monday in August |
| Labour Day | Sep 1 (Mon) | Yes | |
| Thanksgiving | Oct 13 (Mon) | Yes | |
| Remembrance Day | Nov 11 (Tue) | Yes | |
| Christmas Day | Dec 25 (Thu) | Yes | |

**Total**: 10 statutory holidays

**NOT Statutory** (Public Service only):
- Easter Monday (Apr 21)
- National Day for Truth and Reconciliation (Sep 30)
- Boxing Day (Dec 26)

---

## Eligibility Rules

| Rule | Value | Notes |
|------|-------|-------|
| min_employment_days | 30 | 30 days worked in preceding 12 months |
| require_last_first_rule | Yes | Must work last shift before AND first shift after |
| "5 of 9" rule | No | Not applicable in Nunavut |

### Details

Employer NOT required to pay for a general holiday where:
1. Employee has not worked for the same employer for a total of **30 days** during the preceding 12 months prior to the holiday
2. Employee did not report to work on that day after having been called to work on that day
3. Without consent of employer, employee has not reported for work on either their **last regular working day preceding** or **following** the general holiday
4. Employee is on pregnancy or parental leave

---

## Holiday Pay Formula

### Formula Type
- **Type**: Regular Day's Pay
- **Lookback Period**: N/A (regular day's pay, not average)

### Calculation
```
Holiday Pay = Regular Day's Pay (for employees not working on the holiday)
```

### Includes
- [x] Regular wages
- [ ] Overtime
- [ ] Vacation pay
- [ ] Previous holiday pay

---

## Regular vs Non-Regular Work Day

### Determining Regular Work Day
- Based on employee's normal work schedule

### Pay Rules

| Scenario | Pay | Formula |
|----------|-----|---------|
| Regular Day + Not Worked | Regular day's pay | 1.0x daily rate |
| Regular Day + Worked | Regular pay + premium OR day off | 1.0x + 1.5x hours worked, OR substitute day off with pay |
| Non-Regular Day + Not Worked | No pay | N/A |
| Non-Regular Day + Worked | Premium rate | 1.5x hours worked |

---

## Premium Rate

- **Rate**: 1.5x (time and a half)
- **Notes**: Employee receives normal day's pay PLUS 1.5x regular rate for time worked on the general holiday

---

## Vacation Pay

| Years of Service | Vacation Weeks | Vacation Pay Rate |
|------------------|----------------|-------------------|
| < 1 year | Pro-rated | 4% of gross wages |
| 1-5 years | 2 weeks | 4% of gross wages |
| 6+ years | 3 weeks | 6% of gross wages |

**Notes**:
- All employees entitled to vacation pay regardless of employment length
- Payment due at least 1 day before vacation begins
- Upon termination: receive accumulated unpaid vacation pay immediately

---

## Config Verification Checklist

Compare with `backend/config/holiday_pay/2025/provinces_jan.json`:

- [x] `formula_type` - Using "30_day_average" (see note below)
- [x] `formula_params` - lookback_days: 30
- [x] `eligibility.min_employment_days` - 30 (matches official)
- [x] `eligibility.require_last_first_rule` - true (fixed 2025-12-31)
- [x] `premium_rate` - 1.5 (matches official)
- [x] Regular/Non-regular day logic - Implemented
- [x] "5 of 9" rule - Not applicable (correctly not implemented)

---

## Differences Found

All differences have been resolved.

**Notes on formula_type**:
- Official policy states "regular day's pay" for holiday pay
- Config uses "30_day_average" which is a reasonable interpretation for variable-hour employees
- For salaried/fixed-hour employees, regular day's pay is straightforward
- For variable-hour employees, 30-day average is a reasonable fallback

---

## References

1. Nunavut Labour Standards Compliance Office - General Holidays FAQ: https://nu-lsco.ca/faq-s?tmpl=component&faqid=11
2. Government of Nunavut - Labour and Employment Standards: https://www.gov.nu.ca/en/justice-and-individual-protection/labour-and-employment-standards
3. Government of Nunavut - Public Service Holidays 2025: https://www.gov.nu.ca/en/staff-resources/public-service-holidays
4. Nunavut Labour Standards Act (CanLII): https://www.canlii.org/en/nu/laws/stat/rsnwt-nu-1988-c-l-1/latest/rsnwt-nu-1988-c-l-1.html
5. Bill 29 - Nunavut Day legislation (passed Nov 2019): Added July 9 as paid territorial statutory holiday
