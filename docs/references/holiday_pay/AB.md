# Alberta - Holiday Pay Official Reference

> **Status**: ✅ Verified
> **Last Verified**: 2025-12-31
> **Verified By**: Claude Code

## Official Sources

| Source | URL |
|--------|-----|
| General Holidays & Pay | https://www.alberta.ca/general-holidays-pay |
| Vacation Pay | https://www.alberta.ca/vacation-pay |
| Employment Standards | https://www.alberta.ca/employment-standards |

---

## Statutory Holidays (2025)

| Holiday | Date | Statutory? | Notes |
|---------|------|------------|-------|
| New Year's Day | Jan 1 (Wed) | ✓ | |
| Alberta Family Day | Feb 17 (Mon) | ✓ | 3rd Monday in February (AB unique) |
| Good Friday | Apr 18 (Fri) | ✓ | |
| Victoria Day | May 19 (Mon) | ✓ | |
| Canada Day | Jul 1 (Tue) | ✓ | Observed Jul 2 if Jul 1 is Sunday |
| Labour Day | Sep 1 (Mon) | ✓ | |
| Thanksgiving | Oct 13 (Mon) | ✓ | |
| Remembrance Day | Nov 11 (Tue) | ✓ | |
| Christmas Day | Dec 25 (Thu) | ✓ | |

**NOT Statutory in Alberta (Optional):**
- Easter Monday
- Heritage Day (1st Monday in August)
- National Day for Truth and Reconciliation (Sep 30)
- Boxing Day

---

## Eligibility Rules

| Rule | Value | Notes |
|------|-------|-------|
| min_employment_days | **30** | 30 workdays in the 12 months prior to the holiday |
| require_last_first_rule | **Yes** | Must not be absent without employer consent on last scheduled day before OR first scheduled day after |
| "5 of 9" rule | **Yes** | Alberta-specific rule for determining regular vs non-regular work days |

### Details

Employees qualify for general holiday pay if:
- The holiday falls on a regular work day, OR
- They work on the holiday (even if non-regular day)

Employees are **ineligible** if they:
- Worked fewer than 30 workdays in the 12 months prior to the holiday
- Were absent when required to work the holiday
- Were absent without employer consent on the last scheduled day before OR first scheduled day after the holiday

### Exemptions

Certain employees have no general holiday entitlements:
- Certain commissioned salespersons (auto, real estate, investments)
- Film/video production extras
- Camp counselors/instructors (charitable/non-profit)
- Direct selling salespersons (age 16+)
- Teachers

Construction workers and farm/ranch workers have modified rules.

---

## Holiday Pay Formula

### Formula Type
- **Type**: `4_week_average_daily` (average daily wage)
- **Lookback Period**: 4 weeks (employer chooses one option):
  - Option A: 4 weeks immediately preceding the holiday
  - Option B: 4 weeks ending on the last day of the preceding pay period

### Calculation
```
Average Daily Wage = Total Wages in 4-week period ÷ Days Worked in 4-week period
```

### Includes
- [x] Regular wages
- [ ] Overtime (explicitly excluded)
- [x] Vacation pay
- [x] Previous holiday pay

---

## Regular vs Non-Regular Work Day

### Determining Regular Work Day - The "5 of 9" Rule

**Alberta-specific rule**: A day is considered a "regular work day" if the employee worked on that day of the week at least **5 times in the previous 9 weeks**.

Example: If the holiday falls on a Monday, check if the employee worked 5 or more Mondays in the 9 weeks before the holiday.

### Pay Rules

| Scenario | Pay | Formula |
|----------|-----|---------|
| Regular Day + Not Worked | Average daily wage | ADW |
| Regular Day + Worked | Premium + Average daily wage | 1.5x × hours worked + ADW |
| Non-Regular Day + Not Worked | **No pay** | $0 |
| Non-Regular Day + Worked | Premium only | 1.5x × hours worked |

### Alternative Option (Regular Day + Worked)

Employer may offer instead:
- Regular wages for hours worked + future day off with average daily wage

---

## Premium Rate

- **Rate**: 1.5× (time and a half)
- **Notes**:
  - For Regular Day + Worked: Premium is **in addition to** average daily wage
  - For Non-Regular Day + Worked: Premium only, no additional ADW

---

## Vacation Pay

| Years of Service | Vacation Weeks | Vacation Pay Rate |
|------------------|----------------|-------------------|
| < 1 year | No statutory entitlement | N/A |
| 1-4 years | 2 weeks | 4% of yearly wages |
| 5+ years | 3 weeks | 6% of yearly wages |

### Calculation for Salaried Employees
```
Weekly Vacation Pay = Monthly Wage ÷ 4.3333
```

### Vacation Pay Excludes
- Overtime
- General holiday pay
- Termination pay
- Unearned bonuses
- Tips
- Allowances

---

## Config Verification Checklist

Compare with `backend/config/holiday_pay/2025/provinces_jan.json`:

- [x] `formula_type` matches official - Correct: `4_week_average_daily`
- [x] `formula_params.lookback_weeks` matches official - Correct: 4
- [x] `formula_params.method` matches official - Correct: `wages_div_days_worked`
- [x] `eligibility.min_employment_days` matches official - Correct: 30
- [x] `eligibility.require_last_first_rule` matches official - Correct: true
- [x] `premium_rate` matches official - Correct: 1.5
- [ ] "5 of 9" rule implementation needed
- [ ] Regular/Non-regular day pay logic needs verification

---

## Differences Found

| Field | Official | Current Config | Action Needed |
|-------|----------|----------------|---------------|
| min_employment_days | 30 workdays in **12 months** | 30 (no window specified) | Clarify 12-month window in notes |
| "5 of 9" rule | Required for AB | Not in config | Add to eligibility or formula_params |
| Non-regular day logic | No pay if not worked | Not explicit | Ensure calculator handles this |

---

## Implementation Notes

### Key Alberta-Specific Logic

1. **"5 of 9" Rule**: Must be implemented to determine if a day is "regular"
   ```
   is_regular_day(day_of_week) = count(worked_on_day_of_week in last 9 weeks) >= 5
   ```

2. **Non-Regular Day + Not Worked = $0**: Unlike some provinces, Alberta pays nothing if the holiday falls on a non-regular day and employee doesn't work.

3. **Lookback Period Options**: Employer can choose between two 4-week windows - this should be configurable.

---

## References

1. Alberta Employment Standards - General Holidays & Pay: https://www.alberta.ca/general-holidays-pay
2. Alberta Employment Standards - Vacation Pay: https://www.alberta.ca/vacation-pay
3. Employment Standards Code, RSA 2000, c E-9: https://www.qp.alberta.ca/documents/Acts/E09.pdf
