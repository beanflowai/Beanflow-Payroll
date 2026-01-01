# Manitoba - Holiday Pay Official Reference

> **Status**: ✅ Verified
> **Last Verified**: 2025-12-31
> **Verified By**: Claude Code

## Official Sources

| Source | URL |
|--------|-----|
| Employment Standards - General Holidays | https://www.gov.mb.ca/labour/standards/doc,gen-holidays-after-april-30-07,factsheet.html |
| Employment Standards - Vacations | https://www.gov.mb.ca/labour/standards/doc,vacations,factsheet.html |
| General Holidays Category | https://www.gov.mb.ca/labour/standards/category,generalholidays,factsheet.html |

---

## Statutory Holidays (2025)

| Holiday | Date | Statutory? | Notes |
|---------|------|------------|-------|
| New Year's Day | Jan 1 | ✓ | |
| Louis Riel Day | Feb 17 | ✓ | 3rd Monday in February (MB unique) |
| Good Friday | Apr 18 | ✓ | |
| Victoria Day | May 19 | ✓ | |
| Canada Day | Jul 1 | ✓ | |
| Labour Day | Sep 1 | ✓ | |
| Orange Shirt Day | Sep 30 | ✓ | National Day for Truth and Reconciliation |
| Thanksgiving | Oct 13 | ✓ | |
| Christmas Day | Dec 25 | ✓ | |

**NOT Statutory in Manitoba:**
- Easter Sunday
- Terry Fox Day
- Family Day (MB has Louis Riel Day instead)
- Boxing Day
- Remembrance Day

---

## Eligibility Rules

| Rule | Value | Notes |
|------|-------|-------|
| min_employment_days | **0** | No minimum - entitled from first day of employment |
| require_last_first_rule | Yes | Must not be absent without permission on last day before or first day after holiday |
| "5 of 9" rule | No | Not applicable in MB |

### Details

Employees receive general holiday pay **unless** they:
- Are scheduled to work but absent without employer permission
- Are absent without permission from their last scheduled workday before or first scheduled workday after the holiday
- Are election officials, enumerators, or temporary persons appointed under The Elections Act

**Key Point**: "The length of time employees work for an employer does not affect the requirement to pay general holiday pay."

---

## Holiday Pay Formula

### Formula Type
- **Type**: `5_percent_28_days` (percentage of wages in lookback period)
- **Lookback Period**: 4 weeks (28 days) immediately before the holiday

### Calculation

**For varying hours/wages (most common):**
```
Holiday Pay = 5% × Gross Wages in 4-week period before holiday
```

**For consistent schedules:**
```
Holiday Pay = 1 regular work day's pay
```

**Construction industry exception:**
```
Holiday Pay = 4% of gross earnings (typically paid per cheque)
```

### Includes
- [x] Regular wages
- [ ] Overtime (explicitly excluded)
- [x] Vacation pay
- [x] Previous holiday pay

---

## Regular vs Non-Regular Work Day

### Determining Regular Work Day
- Based on employee's normal scheduled work pattern
- For varying schedules, use average hours

### Pay Rules

| Scenario | Pay | Formula |
|----------|-----|---------|
| Regular Day + Not Worked | Holiday Pay only | 5% of 4-week wages |
| Regular Day + Worked | Holiday Pay + Premium | 5% of 4-week wages + 1.5x hourly rate × hours worked |
| Non-Regular Day + Not Worked | Holiday Pay only | 5% of 4-week wages |
| Non-Regular Day + Worked | Holiday Pay + Premium | 5% of 4-week wages + 1.5x hourly rate × hours worked |

---

## Premium Rate

- **Rate**: 1.5× (time and a half)
- **Notes**:
  - Premium is **in addition to** general holiday pay (not instead of)
  - Total for working = Holiday Pay + 1.5× hours worked

### Exceptions
Certain employers may pay regular wages if they provide another day off with general holiday pay within 30 days:
- Gas stations
- Hospitals
- Hotels
- Restaurants
- Amusement venues
- Continuously operating businesses
- Climate-controlled agricultural businesses
- Seasonal industries
- Domestic worker employers

---

## Vacation Pay

| Years of Service | Vacation Weeks | Vacation Pay Rate |
|------------------|----------------|-------------------|
| < 1 year | Pro-rated | 4% of wages earned |
| 1-4 years | 2 weeks | 4% of gross wages |
| 5+ years | 3 weeks | 6% of gross wages |

### Additional Rules
- Vacation must be taken within 10 months of being earned
- General holidays during vacation = extra vacation day + holiday pay
- On termination: vacation pay due within 10 working days

---

## Config Verification Checklist

Compare with `backend/config/holiday_pay/2025/provinces_jan.json`:

- [x] `formula_type` matches official - ✅ Updated to `5_percent_28_days`
- [x] `formula_params` matches official - ✅ Updated (28-day lookback, 5% percentage)
- [x] `eligibility.min_employment_days` matches official - ✅ Updated to `0`
- [x] `eligibility.require_last_first_rule` matches official - ✅ Updated to `true`
- [x] `premium_rate` matches official - ✅ Correct at 1.5
- [x] Construction industry exception - ✅ Added `construction_percentage: 0.04`
- [ ] "5 of 9" rule implemented (if applicable) - N/A for MB

---

## Differences Found

| Field | Official | Current Config | Action Needed |
|-------|----------|----------------|---------------|
| All fields | - | - | ✅ All verified and updated on 2025-12-31 |

---

## References

1. Manitoba Employment Standards - General Holidays: https://www.gov.mb.ca/labour/standards/doc,gen-holidays-after-april-30-07,factsheet.html
2. Manitoba Employment Standards - Vacations and Vacation Pay: https://www.gov.mb.ca/labour/standards/doc,vacations,factsheet.html
3. Manitoba Employment Standards Code: https://web2.gov.mb.ca/laws/statutes/ccsm/e110e.php
