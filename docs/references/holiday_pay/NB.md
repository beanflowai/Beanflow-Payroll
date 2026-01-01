# New Brunswick - Holiday Pay Official Reference

> **Status**: ✅ Verified
> **Last Verified**: 2025-12-31
> **Verified By**: Claude Code

## Official Sources

| Source | URL |
|--------|-----|
| Paid Public Holidays & Vacation | https://www.gnb.ca/en/topic/jobs-workplaces/labour-market-workforce/employment-standards/holiday-vacation.html |
| Employment Standards | https://www.gnb.ca/en/topic/jobs-workplaces/labour-market-workforce/employment-standards.html |
| Employment Standards Act | https://www.canlii.org/en/nb/laws/stat/snb-1982-c-e-7.2/latest/snb-1982-c-e-7.2.html |

---

## Statutory Holidays (2025)

| Holiday | Date | Statutory? | Notes |
|---------|------|------------|-------|
| New Year's Day | Jan 1 (Wed) | ✓ | Paid public holiday |
| Family Day | Feb 17 (Mon) | ✓ | 3rd Monday in February |
| Good Friday | Apr 18 (Fri) | ✓ | Paid public holiday |
| Canada Day | Jul 1 (Tue) | ✓ | Paid public holiday |
| New Brunswick Day | Aug 4 (Mon) | ✓ | 1st Monday in August (NB unique) |
| Labour Day | Sep 1 (Mon) | ✓ | Paid public holiday |
| Remembrance Day | Nov 11 (Tue) | ✓ | Paid public holiday |
| Christmas Day | Dec 25 (Thu) | ✓ | Paid public holiday |

**NOT Paid Public Holidays (Prescribed Days of Rest only):**
- Victoria Day (May 19) - Day of rest, not paid
- Thanksgiving Day (Oct 13) - Day of rest, not paid
- Boxing Day (Dec 26) - Day of rest, not paid

---

## Eligibility Rules

| Rule | Value | Notes |
|------|-------|-------|
| min_employment_days | **90** | 90 calendar days (not workdays) in preceding 12 months |
| require_last_first_rule | **Yes** | Must work scheduled day before AND after holiday |
| "5 of 9" rule | **No** | Not applicable in NB |

### Details

Employees qualify for paid public holiday if ALL conditions met:
- Employed for at least 90 calendar days during the preceding 12 months
- Worked their regular scheduled day before AND after the holiday (unless valid reason)
- If agreeing to work the holiday, must report and work the shift (unless valid reason)

Employees are **ineligible** if:
- In a flexible scheduling arrangement where they control work days
- In a regulated exempt occupation
- Absent without valid reason on day before or after holiday

---

## Holiday Pay Formula

### Formula Type
- **Type**: `30_day_average` (for variable wage earners) or `regular_day_pay` (for fixed schedules)
- **Lookback Period**: 30 days preceding the holiday

### Calculation

**For fixed schedule employees:**
```
Holiday Pay = Regular Day's Pay
```

**For variable wage earners:**
```
Holiday Pay = Total Wages in 30 days ÷ Days Worked in 30 days
            = Average Daily Pay
```

### Alternative Employer Option
Employer may choose to pay **4% of gross wages** from first day of employment instead of calculating per-holiday pay. This is added to regular pay each period.

### Includes
- [x] Regular wages
- [ ] Overtime (not specified, assume excluded)
- [x] Vacation pay (included in gross wages for 4% option)
- [x] Previous holiday pay (included in gross wages for 4% option)

---

## Regular vs Non-Regular Work Day

### Determining Regular Work Day
- Based on employee's regular scheduled work pattern
- Not based on "5 of 9" rule (NB doesn't use this)

### Pay Rules

| Scenario | Pay | Formula |
|----------|-----|---------|
| Regular Day + Not Worked | Regular day's pay | Average daily pay |
| Regular Day + Worked | Regular day's pay + Premium | Avg daily pay + 1.5x × hours worked |
| Non-Regular Day (during vacation) | Regular day's pay OR day off in lieu | Employee choice |
| Holiday on Non-Working Day | Another paid working day off OR regular day's pay | If employee agrees |

---

## Premium Rate

- **Rate**: 1.5× (time and a half)
- **Notes**:
  - Premium is for hours worked on the holiday
  - Premium is **in addition to** regular day's pay
  - Total for working = Regular Day's Pay + 1.5× hours worked

---

## Vacation Pay

| Years of Service | Vacation Weeks | Vacation Pay Rate |
|------------------|----------------|-------------------|
| < 1 year | Pro-rated (1 day/month) | 4% of gross wages |
| 1-7 years | 2 weeks (max) | 4% of gross wages |
| 8+ years | 3 weeks | 6% of gross wages |

### Calculation Details
- **< 8 years**: Minimum of one day per calendar month worked OR two weeks annually, whichever is less
- **8+ years**: Minimum of 1.25 days per month worked OR three weeks annually

### When Vacation Pay Must Be Paid
- At least one day before vacation begins
- Upon termination: on next regular pay day

---

## Config Verification Checklist

Compare with `backend/config/holiday_pay/2025/provinces_jan.json`:

- [x] `formula_type` matches official - Correct: `30_day_average`
- [x] `formula_params.lookback_days` matches official - Correct: 30
- [x] `eligibility.min_employment_days` matches official - Correct: 90
- [ ] `eligibility.require_last_first_rule` matches official - **MISMATCH**: Config has `false`, should be `true`
- [x] `premium_rate` matches official - Correct: 1.5
- [ ] Alternative 4% option not in config

---

## Differences Found

| Field | Official | Current Config | Action Needed |
|-------|----------|----------------|---------------|
| require_last_first_rule | `true` | `false` | Change to `true` |
| Alternative option | 4% of gross wages | Not implemented | Consider adding as alternative formula |
| min_employment_days unit | 90 **calendar** days | 90 (unspecified) | Clarify in notes |

---

## Implementation Notes

### Key NB-Specific Logic

1. **90 Calendar Days**: Unlike some provinces, NB counts calendar days, not workdays, for the 90-day eligibility

2. **8 Holidays Only**: NB has only 8 paid public holidays. Victoria Day, Thanksgiving, and Boxing Day are "prescribed days of rest" but NOT paid

3. **New Brunswick Day**: Unique to NB - 1st Monday in August

4. **4% Alternative**: Employer can pay 4% of gross wages continuously instead of per-holiday calculation

5. **8-Year Vacation Threshold**: Unlike most provinces (5 years), NB uses 8 years for the 6%/3-week vacation threshold

---

## References

1. New Brunswick Employment Standards - Paid Public Holidays & Vacation: https://www.gnb.ca/en/topic/jobs-workplaces/labour-market-workforce/employment-standards/holiday-vacation.html
2. Employment Standards Act, SNB 1982, c E-7.2: https://www.canlii.org/en/nb/laws/stat/snb-1982-c-e-7.2/latest/snb-1982-c-e-7.2.html
