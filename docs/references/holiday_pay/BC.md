# British Columbia - Holiday Pay Official Reference

> **Status**: ✅ Verified
> **Last Verified**: 2025-12-31
> **Verified By**: Claude Code

## Official Sources

| Source | URL |
|--------|-----|
| Statutory Holidays Overview | https://www2.gov.bc.ca/gov/content/employment-business/employment-standards-advice/employment-standards/statutory-holidays |
| Calculate Holiday Pay | https://www2.gov.bc.ca/gov/content/employment-business/employment-standards-advice/employment-standards/statutory-holidays/calculate-statutory-holiday-pay |
| Eligibility Requirements | https://www2.gov.bc.ca/gov/content/employment-business/employment-standards-advice/employment-standards/statutory-holidays/qualify-for-statutory-holiday-pay |
| ESA Section 44 - Entitlement | https://www2.gov.bc.ca/gov/content/employment-business/employment-standards-advice/employment-standards/forms-resources/igm/esa-part-5-section-44 |
| ESA Section 45 - Pay Formula | https://www2.gov.bc.ca/gov/content/employment-business/employment-standards-advice/employment-standards/forms-resources/igm/esa-part-5-section-45 |
| ESA Section 46 - Working on Holiday | https://www2.gov.bc.ca/gov/content/employment-business/employment-standards-advice/employment-standards/forms-resources/igm/esa-part-5-section-46 |
| Annual Vacation | https://www2.gov.bc.ca/gov/content/employment-business/employment-standards-advice/employment-standards/time-off/vacation |

---

## Statutory Holidays (2025)

| Holiday | Date | Statutory? | Notes |
|---------|------|------------|-------|
| New Year's Day | Wed, Jan 1 | ✓ | |
| Family Day | Mon, Feb 17 | ✓ | 3rd Monday in February |
| Good Friday | Fri, Apr 18 | ✓ | |
| Easter Sunday | Sun, Apr 20 | ✗ | NOT a statutory holiday in BC |
| Easter Monday | Mon, Apr 21 | ✗ | NOT a statutory holiday in BC |
| Victoria Day | Mon, May 19 | ✓ | |
| Canada Day | Tue, Jul 1 | ✓ | |
| B.C. Day | Mon, Aug 4 | ✓ | 1st Monday in August (BC unique) |
| Labour Day | Mon, Sep 1 | ✓ | |
| National Day for Truth and Reconciliation | Tue, Sep 30 | ✓ | Added 2021 |
| Thanksgiving Day | Mon, Oct 13 | ✓ | |
| Remembrance Day | Tue, Nov 11 | ✓ | |
| Christmas Day | Thu, Dec 25 | ✓ | |
| Boxing Day | Fri, Dec 26 | ✗ | NOT a statutory holiday in BC |

**Total Statutory Holidays: 11**

---

## Eligibility Rules

| Rule | Value | Notes |
|------|-------|-------|
| min_employment_days | **30** | Must be employed for 30 calendar days before holiday |
| min_days_worked_in_period | **15** | Must have worked or earned wages on 15 of 30 days before holiday |
| require_last_first_rule | **No** | BC explicitly does NOT use this rule |
| "5 of 9" rule | No | Not applicable in BC |

### Details

To qualify for statutory holiday pay, an employee must:
1. Have been employed for at least **30 calendar days** before the statutory holiday
2. Have **worked or earned wages** on at least **15 of the 30 days** before the holiday

**What counts as "worked or earned wages":**
- Days actually worked
- Paid vacation days
- Other paid statutory holidays
- Paid sick days (ESA-mandated)

**Important Clarification**: BC does NOT use the "day before/day after" rule. The official website explicitly states: "Some people think employees only need to work the day before and the day after to qualify for statutory holiday pay. This isn't the case in B.C."

### Excluded Employees

The following employee categories are excluded from statutory holiday pay:
- Managers (Section 36)
- Fishers (Section 37)
- Farm workers (Section 34.1)
- Commission sales workers (Section 37.14)
- High technology professionals (Section 37.8)
- Silviculture workers receiving 4.4% in lieu (Section 37.9)

---

## Holiday Pay Formula

### Formula Type
- **Type**: `30_day_average` (Average Day's Pay)
- **Lookback Period**: 30 calendar days immediately before the statutory holiday

### Calculation
```
Holiday Pay = Total Wages ÷ Days Worked
```

Where:
- **Total Wages** = All wages earned in the 30 calendar days before the holiday
- **Days Worked** = Number of days worked or earned wages in that 30-day period

### Includes
- [x] Regular wages and salary
- [x] Commission
- [x] Statutory holiday pay (from previous holidays)
- [x] Paid vacation pay
- [x] Paid sick days (ESA-mandated)
- [ ] Overtime - **explicitly excluded**

---

## Regular vs Non-Regular Work Day

### Determining Regular Work Day
BC does not distinguish between "regular" and "non-regular" days for eligibility purposes. The key factor is whether the employee meets the 30-day employment and 15-of-30 days worked requirements.

### Pay Rules

| Scenario | Pay | Formula |
|----------|-----|---------|
| Stat falls on scheduled day off | Average Day's Pay | Total Wages ÷ Days Worked |
| Stat is regular work day + NOT worked | Average Day's Pay | Total Wages ÷ Days Worked |
| Stat is regular work day + WORKED | Premium + Average Day's Pay | 1.5× rate × hours (up to 12) + 2× rate × hours (over 12) + Average Day's Pay |
| Employee does NOT qualify | Regular wages only | No stat holiday pay |

---

## Premium Rate

- **Rate (first 12 hours)**: 1.5× (time and a half)
- **Rate (over 12 hours)**: 2.0× (double time)
- **Additional**: Average Day's Pay is **always added** when working on a stat holiday

### Example Calculation

Employee earns $20/hr and works 10 hours on a statutory holiday:
- Average Day's Pay (from 30-day calc): $160.00
- Work compensation: 10 hours × $30/hour (1.5×) = $300.00
- **Total: $460.00**

### Shift Rules
- Shifts starting on a statutory holiday qualify for premium rates regardless of when they end
- Shifts starting the day before (and crossing midnight) do NOT qualify for statutory holiday rates

---

## Vacation Pay

| Years of Service | Vacation Weeks | Vacation Pay Rate |
|------------------|----------------|-------------------|
| 0-5 calendar days | 0 | 0% (not entitled) |
| 5 days - 1 year | Accruing | 4% of wages earned |
| 1-5 years | 2 weeks minimum | 4% of wages earned |
| 5+ years | 3 weeks minimum | 6% of wages earned |

### Additional Rules
- Vacation must be taken within 12 months of being earned
- Vacation pay must be paid at least 7 days before vacation starts (unless employee agrees in writing to receive it on regular pay cheques)
- Scheduled in blocks of 1 week or longer unless employee requests shorter periods
- Employees cannot forgo vacation time and receive only compensation instead

---

## Config Verification Checklist

Compare with `backend/config/holiday_pay/2025/provinces_jan.json`:

- [x] `formula_type` matches official - `30_day_average` is correct
- [x] `formula_params.lookback_days` matches official - 30 is correct
- [x] `formula_params.method` matches official - `total_wages_div_days` is correct
- [x] `formula_params.include_overtime` matches official - `false` is correct
- [x] `eligibility.min_employment_days` matches official - 30 is correct
- [x] `eligibility.require_last_first_rule` matches official - `false` is correct
- [x] `premium_rate` matches official - 1.5 is correct (for first 12 hours)
- [ ] Double-time after 12 hours - Not in config, may need separate field
- [ ] "15 of 30 days worked" eligibility rule - Not explicitly in config

---

## Differences Found

| Field | Official | Current Config | Action Needed |
|-------|----------|----------------|---------------|
| eligibility.min_days_worked | 15 (of 30 days before holiday) | Not present | Consider adding `min_days_worked_in_period: 15` |
| premium_rate_overtime | 2.0 (after 12 hours) | Not present | Consider adding `premium_rate_over_12h: 2.0` |

---

## References

1. BC Employment Standards - Statutory Holidays: https://www2.gov.bc.ca/gov/content/employment-business/employment-standards-advice/employment-standards/statutory-holidays
2. BC ESA Section 44 (Entitlement): https://www2.gov.bc.ca/gov/content/employment-business/employment-standards-advice/employment-standards/forms-resources/igm/esa-part-5-section-44
3. BC ESA Section 45 (Pay Formula): https://www2.gov.bc.ca/gov/content/employment-business/employment-standards-advice/employment-standards/forms-resources/igm/esa-part-5-section-45
4. BC ESA Section 46 (Working on Holiday): https://www2.gov.bc.ca/gov/content/employment-business/employment-standards-advice/employment-standards/forms-resources/igm/esa-part-5-section-46
5. BC Employment Standards - Annual Vacation: https://www2.gov.bc.ca/gov/content/employment-business/employment-standards-advice/employment-standards/time-off/vacation
