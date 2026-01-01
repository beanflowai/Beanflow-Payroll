# Prince Edward Island - Holiday Pay Official Reference

> **Status**: ✅ Verified
> **Last Verified**: 2025-12-31
> **Verified By**: Claude Code

## Official Sources

| Source | URL |
|--------|-----|
| Employment Standards - Paid Holidays | https://www.princeedwardisland.ca/en/information/workforce-advanced-learning-and-population/paid-holidays |
| Employment Standards Act | https://www.princeedwardisland.ca/sites/default/files/legislation/e-06-2-employment_standards_act.pdf |
| Vacation and Vacation Pay | https://www.princeedwardisland.ca/en/information/workforce-advanced-learning-and-population/vacation-and-vacation-pay |
| CFIB Employment Standards Guide | https://www.cfib-fcei.ca/en/tools-resources/employment-standards/understanding-peis-employment-standards |

---

## Statutory Holidays (2025)

| Holiday | Date | Statutory? | Notes |
|---------|------|------------|-------|
| New Year's Day | Jan 1 | ✓ | |
| Islander Day | Feb 17 | ✓ | 2nd Monday in February (PEI unique) |
| Good Friday | Apr 18 | ✓ | |
| Canada Day | Jul 1 | ✓ | |
| Labour Day | Sep 1 | ✓ | |
| National Day for Truth and Reconciliation | Sep 30 | ✓ | Added as statutory holiday |
| Remembrance Day | Nov 11 | ✓ | |
| Christmas Day | Dec 25 | ✓ | |

**NOT Statutory in PEI (Optional):**
- Easter Monday
- Victoria Day
- Civic Holiday (August)
- Thanksgiving
- Boxing Day

**Total**: 8 statutory holidays

---

## Eligibility Rules

| Rule | Value | Notes |
|------|-------|-------|
| min_employment_days | **30** | Must be employed 30 calendar days before holiday |
| days_worked_in_period | **15** | Must earn wages on at least 15 of the 30 days |
| require_last_first_rule | **Yes** | Must work last shift before and first shift after holiday |

### Details

To qualify for paid holiday, an employee must meet ALL three criteria:
1. **Employment Duration**: Work for the same employer for at least 30 calendar days before the holiday
2. **Days Worked**: Earn wages on at least 15 of the 30 days before the holiday
3. **Shift Attendance**: Complete last regularly scheduled shift before the holiday AND first regularly scheduled shift after (unless employer requires absence)

### Exemptions
- Commissioned sales employees (if majority of income from commissions)
- Agricultural farm labourers
- Employers may voluntarily provide benefits to exempt employees

---

## Holiday Pay Formula

### Formula Type
- **Type**: `30_day_average` (average daily wage in lookback period)
- **Lookback Period**: 30 calendar days before the holiday

### Calculation

**For consistent wages/hours:**
```
Holiday Pay = Regular Daily Wage
```

**For fluctuating wages/hours:**
```
Holiday Pay = Total Wages Earned in 30 Days ÷ Days Worked in 30 Days
```

**Alternative formula for variable hours:**
```
Holiday Pay = (Hours worked in prior 3 weeks ÷ 15) × Hourly Rate
```

**Example**: Employee earning $1,485 over 22 days worked:
$1,485 ÷ 22 = **$67.50** holiday pay

### Includes
- [x] Regular wages
- [ ] Overtime (not specified, typically excluded)
- [x] Vacation pay (if taken during period)
- [x] Previous holiday pay (if in period)

---

## Regular vs Non-Regular Work Day

### Determining Regular Work Day
- Based on employee's normal scheduled work pattern
- For varying schedules, use average daily calculation

### Pay Rules

| Scenario | Pay | Formula |
|----------|-----|---------|
| Regular Day + Not Worked | Holiday Pay only | Average daily wage |
| Regular Day + Worked | Holiday Pay + Premium | Average daily wage + 1.5x hourly × hours worked |
| Non-Regular Day + Not Worked | Holiday Pay only | Average daily wage |
| Non-Regular Day + Worked | Holiday Pay + Premium | Average daily wage + 1.5x hourly × hours worked |

### Alternative for Working on Holiday
Employer may provide EITHER:
- Regular holiday pay + 1.5× premium for hours worked, OR
- Regular wages for hours worked + substitute paid day off before next vacation

---

## Premium Rate

- **Rate**: 1.5× (time and a half)
- **Notes**:
  - Premium is **in addition to** regular holiday pay
  - Total for working = Holiday Pay + 1.5× hours worked
  - OR substitute day off option available

---

## Vacation Pay

| Years of Service | Vacation Weeks | Vacation Pay Rate |
|------------------|----------------|-------------------|
| < 1 year | Pro-rated | 4% of gross wages |
| 1-7 years | 2 weeks | 4% of gross wages |
| 8+ years | 3 weeks | **6%** of gross wages |

### Additional Rules
- Vacation is considered earned wages
- Vacation must be taken within 4 months after entitlement year ends
- Seasonal workers: vacation pay may be included in hourly rate if documented

---

## Config Verification Checklist

Compare with `backend/config/holiday_pay/2025/provinces_jan.json`:

- [x] `formula_type` matches official - `30_day_average` ✓
- [x] `formula_params.lookback_days` matches official - 30 ✓
- [x] `formula_params.method` matches official - `total_wages_div_days` ✓
- [x] `eligibility.min_employment_days` matches official - 30 ✓
- [x] `eligibility.require_last_first_rule` matches official - true ✓
- [x] `eligibility.min_days_worked_in_period` matches official - 15 ✓
- [x] `premium_rate` matches official - 1.5 ✓

---

## Differences Found

| Field | Official | Current Config | Action Needed |
|-------|----------|----------------|---------------|
| All fields | Match | Match | None - config updated 2025-12-31 |

---

## References

1. PEI Employment Standards - Paid Holidays: https://www.princeedwardisland.ca/en/information/workforce-advanced-learning-and-population/paid-holidays
2. PEI Employment Standards Act: https://www.princeedwardisland.ca/sites/default/files/legislation/e-06-2-employment_standards_act.pdf
3. CFIB - Understanding PEI's Employment Standards: https://www.cfib-fcei.ca/en/tools-resources/employment-standards/understanding-peis-employment-standards
4. EBSource - Statutory Holidays in PEI: https://ebsource.ca/statutory-holidays-in-prince-edward-island/
