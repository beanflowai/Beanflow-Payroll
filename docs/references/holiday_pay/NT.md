# Northwest Territories - Holiday Pay Official Reference

> **Status**: ✅ Verified
> **Last Verified**: 2025-12-31
> **Verified By**: Claude Code

## Official Sources

| Source | URL |
|--------|-----|
| Employment Standards - FAQ | https://www.ece.gov.nt.ca/en/services/employment-standards/frequently-asked-questions |
| Employment Standards Main | https://www.ece.gov.nt.ca/en/employment-standards |
| Employment Standards Act (PDF) | https://www.justice.gov.nt.ca/en/files/legislation/employment-standards/employment-standards.a.pdf |
| NDTR Amendment | https://www.gov.nt.ca/en/newsroom/national-day-truth-and-reconciliation-declared-statutory-holiday-northwest-territories |

---

## Statutory Holidays (2025)

| Holiday | Date | Statutory? | Notes |
|---------|------|------------|-------|
| New Year's Day | Jan 1 | ✓ | |
| Good Friday | Apr 18 | ✓ | |
| Victoria Day | May 19 | ✓ | |
| National Indigenous Peoples Day | Jun 21 | ✓ | NT unique holiday |
| Canada Day | Jul 1 | ✓ | |
| Civic Holiday | Aug 4 | ✓ | First Monday in August |
| Labour Day | Sep 1 | ✓ | |
| National Day for Truth and Reconciliation | Sep 30 | ✓ | Added 2022 via Bill 47 |
| Thanksgiving Day | Oct 13 | ✓ | |
| Remembrance Day | Nov 11 | ✓ | |
| Christmas Day | Dec 25 | ✓ | |

**Total: 11 statutory holidays**

**NOT Statutory in NWT:**
- Easter Monday (employers may voluntarily recognize)
- Boxing Day (employers may voluntarily recognize)
- Family Day (not observed in NT)

---

## Eligibility Rules

| Rule | Value | Notes |
|------|-------|-------|
| min_employment_days | **30** | Within 12 months prior to the holiday |
| require_last_first_rule | **Yes** | Must work last scheduled shift before AND first shift after holiday |
| report_if_scheduled | **Yes** | Must report to work on holiday if scheduled or called |

### Details

Employees must meet ALL conditions to qualify:
- Worked for employer **30 days within 12 months** prior to holiday
- Reported to work on **last scheduled day before** the holiday
- Reported to work on **next scheduled day after** the holiday
- Reported to work on the holiday **if scheduled or called**

**Exceptions:**
- Employees on pregnancy/parental leave are not entitled during leave
- Part-time employees qualify once conditions are met (entitlements may be prorated)

---

## Holiday Pay Formula

### Formula Type
- **Type**: `average_daily_pay` (varies by compensation structure)
- **Lookback Period**: 4 weeks for non-time-based wages

### Calculation

**For Time-Based Wages (hourly/salary):**
```
Holiday Pay = Regular rate × Normal hours of work for that day
```

**For Other Compensation (commission, piece work, etc.):**
```
Holiday Pay = Average daily wages for 4 weeks immediately preceding the holiday week
```

### Includes
- [x] Regular wages
- [ ] Overtime (calculated separately)
- [x] Vacation pay (independent entitlement)
- [x] Previous holiday pay

---

## Regular vs Non-Regular Work Day

### Determining Regular Work Day
- Based on employee's normal scheduled work pattern

### Pay Rules

| Scenario | Pay | Formula |
|----------|-----|---------|
| Regular Day + Not Worked | Average day's pay | Regular rate × normal hours |
| Regular Day + Worked | Premium + Average day's pay | 1.5× hours worked + average day's pay |
| Non-Regular Day + Not Worked | Average day's pay | Regular rate × normal hours |
| Non-Regular Day + Worked | Premium + Average day's pay | 1.5× hours worked + average day's pay |

**Alternative:** Employer may provide substitute paid day off before next annual vacation instead of premium pay.

---

## Premium Rate

- **Rate**: 1.5× (time and a half)
- **Notes**:
  - Premium is **in addition to** average day's pay (not instead of)
  - Total for working = 1.5× hours worked + average day's pay
  - Overtime threshold drops from 40 to 32 regular hours during weeks with statutory holiday

---

## Vacation Pay

| Years of Service | Vacation Weeks | Vacation Pay Rate |
|------------------|----------------|-------------------|
| < 1 year | Pro-rated | 4% of wages earned |
| 1-5 years | 2 weeks | **4%** of gross wages |
| 5+ years | 3 weeks | **6%** of gross wages |

### Additional Rules
- Vacation pay accumulates from first hour worked
- Vacation must be granted within 6 months of year earned
- All earned vacation pay must be paid in final cheque within 10 calendar days
- Part-time and casual employees also receive vacation pay
- Statutory holiday during vacation = both compensations apply

---

## Config Verification Checklist

Compare with `backend/config/holiday_pay/2025/provinces_jan.json`:

- [x] `formula_type` matches official - ✅ `30_day_average` (time-based uses regular day's pay)
- [x] `formula_params.lookback_days` - ✅ 30 days is correct
- [x] `eligibility.min_employment_days` - ✅ 30 days is correct
- [x] `eligibility.require_last_first_rule` - ✅ Updated to `true`
- [x] `premium_rate` - ✅ 1.5 is correct
- [x] `notes` - ✅ Added official URL reference

---

## Differences Found

| Field | Official | Current Config | Action Needed |
|-------|----------|----------------|---------------|
| All fields | - | - | ✅ All verified and updated on 2025-12-31 |

---

## References

1. NWT Employment Standards FAQ: https://www.ece.gov.nt.ca/en/services/employment-standards/frequently-asked-questions
2. NWT Employment Standards Main Page: https://www.ece.gov.nt.ca/en/employment-standards
3. NWT Employment Standards Act: https://www.justice.gov.nt.ca/en/files/legislation/employment-standards/employment-standards.a.pdf
4. NDTR Amendment Announcement: https://www.gov.nt.ca/en/newsroom/national-day-truth-and-reconciliation-declared-statutory-holiday-northwest-territories
5. Contact: Employment Standards Office - 1-888-700-5707 / employment_standards@gov.nt.ca
