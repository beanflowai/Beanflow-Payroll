# Federal (Canada Labour Code) - Holiday Pay Official Reference

> **Status**: ✅ Verified
> **Last Verified**: 2025-12-31
> **Verified By**: Claude Code

## Official Sources

| Source | URL |
|--------|-----|
| General Holidays | https://www.canada.ca/en/employment-social-development/services/labour-standards/reports/holidays.html |
| Vacations & Holidays Overview | https://www.canada.ca/en/services/jobs/workplace/federal-labour-standards/vacations-holidays.html |
| Holiday Calculator | https://wages-salaires.service.canada.ca/en/gen_holiday/index.html |
| Vacation Pay Policy (IPG-012) | https://www.canada.ca/en/employment-social-development/programs/laws-regulations/labour/interpretations-policies/vacation-pay.html |

---

## Statutory Holidays (2025)

| Holiday | Date | Statutory? | Notes |
|---------|------|------------|-------|
| New Year's Day | Jan 1 (Wed) | Yes | |
| Good Friday | Apr 18 (Fri) | Yes | |
| Victoria Day | May 19 (Mon) | Yes | Monday before May 25 |
| Canada Day | Jul 1 (Tue) | Yes | |
| Labour Day | Sep 1 (Mon) | Yes | 1st Monday of September |
| National Day for Truth and Reconciliation | Sep 30 (Tue) | Yes | Added 2021 |
| Thanksgiving Day | Oct 13 (Mon) | Yes | 2nd Monday of October |
| Remembrance Day | Nov 11 (Tue) | Yes | Federal includes this |
| Christmas Day | Dec 25 (Thu) | Yes | |
| Boxing Day | Dec 26 (Fri) | Yes | |

**Total: 10 statutory holidays**

### Holiday Substitution Rules
If New Year's Day, Canada Day, National Day for Truth and Reconciliation, Remembrance Day, Christmas Day, or Boxing Day falls on a Saturday or Sunday that is a non-working day, the employee is entitled to a holiday with pay on the working day immediately preceding or following the general holiday.

---

## Eligibility Rules

| Rule | Value | Notes |
|------|-------|-------|
| min_employment_days | 0 | No minimum employment period specified |
| require_last_first_rule | No | Not explicitly required |
| "5 of 9" rule | No | Not applicable |

### Details

- **No minimum tenure**: All federally regulated employees are entitled to general holidays regardless of length of employment
- Part-time employees are entitled to the same 10 general holidays as full-time employees
- Holiday pay is adjusted proportionally for part-time employees

---

## Holiday Pay Formula

### Formula Type
- **Type**: 4_week_average
- **Lookback Period**: 4 weeks immediately before the week in which the holiday occurs

### Calculation
```
Holiday Pay = (Wages in 4 weeks, excluding overtime) / 20
```

For commission-based employees who have worked 12+ weeks continuously:
```
Holiday Pay = (Wages in 12 weeks, excluding overtime) / 60
```

### Includes
- [x] Regular wages
- [ ] Overtime (excluded)
- [ ] Vacation pay (not explicitly mentioned as included)
- [ ] Previous holiday pay (not explicitly mentioned)

---

## Regular vs Non-Regular Work Day

### Determining Regular Work Day
- Based on employee's regular work schedule
- If holiday falls on a non-working day (Saturday/Sunday), employee receives substitute day

### Pay Rules

| Scenario | Pay | Formula |
|----------|-----|---------|
| Regular Day + Not Worked | Holiday pay | (4wk wages) / 20 |
| Regular Day + Worked | 1.5x wages + holiday pay | (1.5 x rate x hours) + holiday pay |
| Non-Regular Day + Not Worked | Substitute day with holiday pay | Holiday pay on substitute day |
| Non-Regular Day + Worked | 1.5x wages + holiday pay | Same as Regular Day + Worked |

---

## Premium Rate

- **Rate**: 1.5x (time and a half) PLUS regular holiday pay
- **Notes**:
  - When required to work on a general holiday, employee receives:
    1. At least 1.5 times regular rate for hours worked, AND
    2. General holiday pay for that day
  - Total compensation = 1.5x wages for hours worked + standard holiday pay

---

## Vacation Pay

| Years of Service | Vacation Weeks | Vacation Pay Rate |
|------------------|----------------|-------------------|
| 1+ years | 2 weeks | 4% |
| 5+ years | 3 weeks | 6% |
| 10+ years | 4 weeks | 8% |

### Notes
- Vacation pay is calculated as a percentage of gross wages during the year of employment
- Employers must schedule vacation with at least 2 weeks notice
- Vacation must begin within 10 months of completing each employment year
- "Wages" includes all forms of remuneration for work performed, excluding tips and gratuities

---

## Config Verification Checklist

Compare with `backend/config/holiday_pay/2025/provinces_jan.json`:

- [x] `formula_type` = "4_week_average" ✅
- [x] `formula_params.lookback_weeks` = 4 ✅
- [x] `formula_params.divisor` = 20 ✅
- [x] `formula_params.include_overtime` = false ✅
- [x] `formula_params.include_vacation_pay` = false ✅
- [x] `eligibility.min_employment_days` = 0 ✅
- [x] `eligibility.require_last_first_rule` = false ✅
- [x] `premium_rate` = 1.5 ✅

---

## Differences Found

| Field | Official | Current Config | Action Needed |
|-------|----------|----------------|---------------|
| - | - | - | No differences - config updated 2025-12-31 |

---

## References

1. Canada Labour Code, Part III - Standard Hours, Wages, Vacations and Holidays
2. https://www.canada.ca/en/employment-social-development/services/labour-standards/reports/holidays.html
3. https://www.canada.ca/en/services/jobs/workplace/federal-labour-standards/vacations-holidays.html
4. https://www.canada.ca/en/employment-social-development/programs/laws-regulations/labour/interpretations-policies/vacation-pay.html
5. https://wages-salaires.service.canada.ca/en/gen_holiday/index.html
