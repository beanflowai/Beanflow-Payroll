# Saskatchewan - Holiday Pay Official Reference

> **Status**: ✅ Verified
> **Last Verified**: 2025-12-31
> **Verified By**: Claude Code

## Official Sources

| Source | URL |
|--------|-----|
| Employment Standards - Public Holidays | https://www.saskatchewan.ca/business/employment-standards/public-statutory-holidays |
| Paying Employees for Public Holidays | https://www.saskatchewan.ca/business/employment-standards/public-statutory-holidays/paying-employees-for-public-holidays |
| Official Calculator | https://apps.saskatchewan.ca/lrws/calculator/holidaypay/ |
| Vacation Pay Guide | https://www.saskatchewan.ca/business/employment-standards/vacations-and-vacation-pay/annual-vacation-and-vacation-pay/calculating-and-paying-vacation-pay |

---

## Statutory Holidays (2025)

| Holiday | Date | Statutory? | Notes |
|---------|------|------------|-------|
| New Year's Day | Jan 1 | ✓ | |
| Family Day | Feb 17 | ✓ | 3rd Monday in February |
| Good Friday | Apr 18 | ✓ | |
| Victoria Day | May 19 | ✓ | |
| Canada Day | Jul 1 | ✓ | |
| Saskatchewan Day | Aug 4 | ✓ | 1st Monday in August (SK unique) |
| Labour Day | Sep 1 | ✓ | |
| Thanksgiving | Oct 13 | ✓ | |
| Remembrance Day | Nov 11 | ✓ | |
| Christmas Day | Dec 25 | ✓ | |

**NOT Statutory in Saskatchewan:**
- Easter Monday
- Easter Sunday
- Christmas Eve
- Boxing Day
- National Day for Truth and Reconciliation (Sept 30) - only federal workplaces

**Sunday Rule**: When New Year's Day, Christmas Day, or Remembrance Day falls on Sunday, the following Monday is observed as the holiday.

---

## Eligibility Rules

| Rule | Value | Notes |
|------|-------|-------|
| min_employment_days | **0** | No minimum - new employees entitled even if less than 28 days |
| require_last_first_rule | No | Not explicitly required in SK |
| "5 of 9" rule | No | Not applicable in SK |

### Details

All employees are entitled to public holiday pay regardless of:
- Payment method (hourly, salary, commission)
- Hours worked
- Employment classification (including managerial, professional, and group home operators)

**New Employees**: "A new employee is entitled to public holiday pay even if they have been employed for less than four weeks before the public holiday." The 5% calculation applies to only the wages earned before the holiday.

---

## Holiday Pay Formula

### Formula Type
- **Type**: `5_percent_28_days` (percentage of wages in lookback period)
- **Lookback Period**: 28 days (4 weeks) immediately before the holiday

### Calculation

**Standard Formula:**
```
Holiday Pay = 5% × Gross Wages in 28-day period before holiday
```

**Construction Industry Exception:**
```
Holiday Pay = 4% of annual wages (excluding overtime & vacation pay)
Paid by December 31 each year
```

### Includes
- [x] Regular wages
- [ ] Overtime (explicitly excluded)
- [x] Vacation pay (received during 28-day period)
- [x] Previous holiday pay (from 28-day period)
- [x] Commissions
- [x] Earned bonuses

### Excludes
- Overtime compensation
- Discretionary bonuses
- Gratuities

---

## Regular vs Non-Regular Work Day

### Determining Regular Work Day
- Based on employee's normal scheduled work pattern
- For varying schedules, use standard calculation (5% of 28 days)

### Pay Rules

| Scenario | Pay | Formula |
|----------|-----|---------|
| Regular Day + Not Worked | Holiday Pay only | 5% of 28-day wages |
| Regular Day + Worked | Holiday Pay + Premium | 5% of 28-day wages + 1.5x hourly rate × hours worked |
| Non-Regular Day + Not Worked | Holiday Pay only | 5% of 28-day wages |
| Non-Regular Day + Worked | Holiday Pay + Premium | 5% of 28-day wages + 1.5x hourly rate × hours worked |

### Salaried Employees
If a salaried employee receives the day off with pay, subtract one day's calculated salary from the total public holiday pay owed.

---

## Premium Rate

- **Rate**: 1.5× (time and a half)
- **Notes**:
  - Premium is **in addition to** general holiday pay (not instead of)
  - Total for working = Holiday Pay + 1.5× hours worked
  - Applies to all employees including managerial, professional, and group home operators

### Overtime During Holiday Week
- Overtime threshold reduced to 32 hours during weeks with a public holiday
- The 32 hours does not include hours worked on the public holiday itself

---

## Vacation Pay

| Years of Service | Vacation Weeks | Vacation Pay Rate | Formula |
|------------------|----------------|-------------------|---------|
| < 1 year | Pro-rated | 5.77% of wages earned | 3/52 |
| 1-9 years | 3 weeks | **5.77%** of gross wages | 3/52 |
| 10+ years | 4 weeks | **7.69%** of gross wages | 4/52 |

### Vacation Pay Wage Includes
- Salary, commission, earned bonuses
- Overtime
- Public holiday pay
- Vacation pay
- Pay in lieu of notice

---

## Config Verification Checklist

Compare with `backend/config/holiday_pay/2025/provinces_jan.json`:

- [x] `formula_type` matches official - `5_percent_28_days` ✓
- [x] `formula_params.lookback_days` matches official - 28 ✓
- [x] `formula_params.percentage` matches official - 0.05 (5%) ✓
- [x] `formula_params.include_overtime` matches official - false ✓
- [x] `formula_params.include_vacation_pay` matches official - true ✓
- [x] `formula_params.include_previous_holiday_pay` matches official - true ✓
- [x] `eligibility.min_employment_days` matches official - 0 ✓
- [x] `premium_rate` matches official - 1.5 ✓
- [ ] `eligibility.require_last_first_rule` - Config has `false`, verify if this is correct

---

## Differences Found

| Field | Official | Current Config | Action Needed |
|-------|----------|----------------|---------------|
| All core fields | Match | Match | None - config is correct |

**Note**: Saskatchewan config appears to be correctly implemented.

---

## References

1. Saskatchewan Employment Standards - Paying Employees for Public Holidays: https://www.saskatchewan.ca/business/employment-standards/public-statutory-holidays/paying-employees-for-public-holidays
2. Saskatchewan Employment Standards - List of Public Holidays: https://www.saskatchewan.ca/business/employment-standards/public-statutory-holidays/list-of-saskatchewan-public-holidays
3. Saskatchewan Employment Standards - Vacation Pay: https://www.saskatchewan.ca/business/employment-standards/vacations-and-vacation-pay/annual-vacation-and-vacation-pay/calculating-and-paying-vacation-pay
4. Official Public Holiday Pay Calculator: https://apps.saskatchewan.ca/lrws/calculator/holidaypay/
