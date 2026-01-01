# Ontario - Holiday Pay Official Reference

> **Status**: ✅ Verified
> **Last Verified**: 2025-12-31
> **Verified By**: Claude Code

## Official Sources

| Source | URL |
|--------|-----|
| Employment Standards | https://www.ontario.ca/document/your-guide-employment-standards-act-0 |
| Public Holidays Guide | https://www.ontario.ca/document/your-guide-employment-standards-act-0/public-holidays |
| Vacation Guide | https://www.ontario.ca/document/your-guide-employment-standards-act-0/vacation |

---

## Statutory Holidays (2025)

| Holiday | Date | Statutory? | Notes |
|---------|------|------------|-------|
| New Year's Day | Jan 1 (Wed) | Yes | |
| Family Day | Feb 17 (Mon) | Yes | 3rd Monday of February |
| Good Friday | Apr 18 (Fri) | Yes | |
| Victoria Day | May 19 (Mon) | Yes | Monday before May 25 |
| Canada Day | Jul 1 (Tue) | Yes | |
| Labour Day | Sep 1 (Mon) | Yes | 1st Monday of September |
| Thanksgiving | Oct 13 (Mon) | Yes | 2nd Monday of October |
| Remembrance Day | Nov 11 | **No** | Not a statutory holiday in Ontario |
| Christmas Day | Dec 25 (Thu) | Yes | |
| Boxing Day | Dec 26 (Fri) | Yes | |

**Total: 9 statutory holidays** (Remembrance Day is NOT included)

---

## Eligibility Rules

| Rule | Value | Notes |
|------|-------|-------|
| min_employment_days | 0 | No minimum employment period required |
| require_last_first_rule | Yes | Must work last scheduled day before AND first after holiday |
| "5 of 9" rule | No | Not applicable to Ontario |

### Details

- **No minimum tenure**: All employees qualify regardless of length of employment, hours worked, or employment type (full-time, part-time, contract)
- **Last/First Rule**: Employee must work their last regularly scheduled day before the holiday AND first regularly scheduled day after the holiday
- **Reasonable Cause Exception**: If employee has reasonable cause (circumstances beyond their control) for missing last/first day, they still qualify
- The "last" and "first" scheduled days need not be immediately adjacent to the holiday - they are based on the employee's regular work schedule

---

## Holiday Pay Formula

### Formula Type
- **Type**: 4_week_average
- **Lookback Period**: 4 weeks before the public holiday

### Calculation
```
Holiday Pay = (Regular wages in 4 weeks + Vacation pay payable in 4 weeks) / 20
```

### Includes
- [x] Regular wages
- [ ] Overtime (excluded)
- [x] Vacation pay (payable in the 4-week period)
- [ ] Previous holiday pay (excluded)
- [ ] Premium pay (excluded)
- [ ] Termination pay (excluded)

### Vacation Pay Inclusion Rules
| Vacation Pay Method | Include in Formula? |
|---------------------|---------------------|
| Paid before vacation or on payday of vacation week | Only if employee was on vacation during 4-week period |
| Paid with every paycheck | At least 4% (or higher if specified) of wages in 4-week period |
| Paid in lump sum on specific dates | Only if payment date falls within 4-week period |

---

## Regular vs Non-Regular Work Day

### Determining Regular Work Day
- Based on employee's regular work schedule
- Vacation periods, leaves, and layoffs modify which days count as "scheduled"
- If employer agrees to early departure, scheduled shift duration changes accordingly

### Pay Rules

| Scenario | Pay | Formula |
|----------|-----|---------|
| Regular Day + Not Worked | Holiday pay + day off | (4wk wages + vac pay) / 20 |
| Regular Day + Worked (Option A) | Regular wages + substitute day with holiday pay | Reg rate x hours + holiday pay on sub day |
| Regular Day + Worked (Option B) | Holiday pay + premium pay | (4wk/20) + (1.5 x reg rate x hours) |
| Non-Regular Day + Not Worked | Holiday pay OR substitute day | Employee choice (written agreement) |
| Non-Regular Day + Worked | Same as Regular Day + Worked | Option A or B |
| Partial work (no reasonable cause) | Premium pay only | 1.5 x reg rate x hours worked |
| Failed to work (no reasonable cause) | Nothing | $0 |

---

## Premium Rate

- **Rate**: 1.5x (time and a half)
- **Notes**:
  - Applies to all hours worked on the public holiday
  - Premium pay hours are NOT included when calculating overtime hours
  - This is important: if an employee works 8 hours on a holiday, those 8 hours don't count toward the 44-hour overtime threshold

---

## Vacation Pay

| Years of Service | Vacation Weeks | Vacation Pay Rate |
|------------------|----------------|-------------------|
| < 5 years | 2 weeks | 4% of gross wages |
| 5+ years | 3 weeks | 6% of gross wages |

### Notes
- Rate is based on gross wages earned in the vacation entitlement year (excluding vacation pay already paid)
- When employee reaches 5-year mark mid-year, the 6% rate applies to ALL earnings for that entitlement year
- Includes: regular earnings, commissions, work-related bonuses, overtime, public holiday pay
- Excludes: tips, discretionary bonuses, severance pay, benefit plan contributions

---

## Config Verification Checklist

Compare with `backend/config/holiday_pay/2025/provinces_jan.json`:

- [x] `formula_type` matches official - "4_week_average" ✅
- [x] `formula_params.lookback_weeks` = 4 ✅
- [x] `formula_params.divisor` = 20 ✅
- [x] `formula_params.include_vacation_pay` = true ✅
- [x] `formula_params.include_overtime` = false ✅
- [x] `eligibility.min_employment_days` = 0 ✅
- [x] `eligibility.require_last_first_rule` = true ✅
- [x] `premium_rate` = 1.5 ✅
- [ ] Regular/Non-regular day logic implemented (needs code review)
- [x] "5 of 9" rule implemented - N/A for Ontario

---

## Differences Found

| Field | Official | Current Config | Action Needed |
|-------|----------|----------------|---------------|
| - | - | - | No differences found - config matches official policy |

---

## References

1. Ontario Employment Standards Act, 2000 - Part X (Public Holidays)
2. https://www.ontario.ca/document/your-guide-employment-standards-act-0/public-holidays
3. https://www.ontario.ca/document/your-guide-employment-standards-act-0/vacation
4. https://canada-holidays.ca/provinces/ON/2025
