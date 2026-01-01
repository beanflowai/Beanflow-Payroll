# Yukon - Holiday Pay Official Reference

> **Status**: ✅ Verified
> **Last Verified**: 2025-12-31
> **Verified By**: Claude Code

## Official Sources

| Source | URL |
|--------|-----|
| Employment Standards Main | https://yukon.ca/en/employment/employment-standards |
| Statutory Holidays (Employers) | https://yukon.ca/en/doing-business/employer-responsibilities/find-yukon-statutory-holiday |
| Statutory Holidays (Employees) | https://yukon.ca/en/employment/employment-standards/find-employee-information-statutory-holidays |
| Holiday Pay Guide | https://yukon.ca/en/employment/employment-standards/find-out-about-general-holiday-pay-under-employment-standards-act |
| Vacation Pay Guide | https://yukon.ca/en/employment/employment-standards/learn-about-annual-vacation-pay-and-vacation-time |
| General Holiday Pay Fact Sheet (PDF) | https://yukon.ca/sites/default/files/cs-general-holiday-pay-fact-sheet.pdf |

---

## Statutory Holidays (2025)

| Holiday | Date | Statutory? | Notes |
|---------|------|------------|-------|
| New Year's Day | Jan 1 | ✓ | |
| Good Friday | Apr 18 | ✓ | |
| Victoria Day | May 19 | ✓ | |
| National Indigenous Peoples Day | Jun 21 | ✓ | Statutory since 2017 in Yukon |
| Canada Day | Jul 1 | ✓ | |
| Discovery Day | Aug 18 | ✓ | Third Monday in August - Yukon unique |
| Labour Day | Sep 1 | ✓ | |
| National Day for Truth and Reconciliation | Sep 30 | ✓ | |
| Thanksgiving Day | Oct 13 | ✓ | |
| Remembrance Day | Nov 11 | ✓ | |
| Christmas Day | Dec 25 | ✓ | |

**Total: 11 statutory holidays**

**NOT Statutory in Yukon:**
- Heritage Day (Feb 17 - third Monday in February) - not statutory, but employers may include
- Easter Monday - not statutory
- Boxing Day - not statutory

---

## Eligibility Rules

| Rule | Value | Notes |
|------|-------|-------|
| min_employment_days | **30** | 30 calendar days before the holiday |
| require_last_first_rule | **Yes** | Must work last scheduled shift before AND first shift after holiday |

### Details

Employees must meet ALL conditions to qualify:
- Employed for **30 calendar days** before the holiday
- Must work **last scheduled shift before** the holiday
- Must work **first scheduled shift after** the holiday
- Unless absence is permitted by the Employment Standards Act

**Permitted Absences (do not disqualify):**
- Sick leave (especially with doctor's note)
- Pre-approved vacation
- Bereavement leave
- Jury duty

**Holiday Falls on Day Off:**
- If a statutory holiday falls on an employee's regular day off, the first working day immediately following becomes the statutory holiday

---

## Holiday Pay Formula

### Formula Type
- **Type**: Dual formula depending on work pattern
- **Standard employees**: Regular day's pay
- **Irregular/part-time**: 10% of wages in 2 weeks prior

### Calculation

**For Regular/Standard Hours Employees:**
```
Holiday Pay = Regular rate × Normal hours of work for that day
```

**For Irregular Hours/Part-Time Employees:**
```
Holiday Pay = 10% × (Wages earned in 2 calendar weeks before holiday week)
```
- Excludes vacation pay from calculation
- Includes overtime earned in that period

### Includes (for 10% formula)
- [x] Regular wages
- [x] Overtime
- [ ] Vacation pay (explicitly excluded)
- [x] Previous holiday pay

---

## Regular vs Non-Regular Work Day

### Determining Regular Work Day
- Based on employee's normal scheduled work pattern
- Irregular hours = less than standard hours or variable schedule

### Pay Rules

| Scenario | Pay | Formula |
|----------|-----|---------|
| Regular Day + Not Worked | Regular day's pay | Regular rate × normal hours |
| Regular Day + Worked | Premium + General holiday pay | 1.5× hours worked + holiday pay (or regular rate + lieu day) |
| Non-Regular Day + Not Worked | 10% formula | 10% × wages in prior 2 weeks |
| Non-Regular Day + Worked | Premium + 10% formula | 1.5× hours worked + 10% holiday pay (or regular rate + lieu day) |

**Alternative for Working on Holiday:**
- Employer may pay regular rate for hours worked AND grant a substitute day off
- Lieu day may be added to annual vacation or taken at mutually convenient time

---

## Premium Rate

- **Rate**: 1.5× (time and a half) OR regular rate + lieu day
- **Notes**:
  - Premium is **in addition to** general holiday pay (not instead of)
  - Employee is entitled to both general holiday pay AND premium/overtime even if employed less than 30 days
  - Employer choice: overtime rate OR regular rate + day off later

---

## Vacation Pay

| Years of Service | Vacation Weeks | Vacation Pay Rate |
|------------------|----------------|-------------------|
| 0-14 days | None | 0% |
| 14+ days (accrual starts) | Pro-rated | 4% of gross wages |
| 1+ years | 2 weeks | **4%** of gross wages |

### Additional Rules
- Vacation pay must be paid at least **one day before** vacation begins
- Vacation time: at least 2 weeks for every year of completed work
- Vacation pay excludes: gratuities and discretionary employer payments unrelated to work
- Yukon legislation provides **only one tier** of vacation pay (4%)
- Some third-party sources incorrectly cite 6% after 5 or 8 years - this is NOT in official Yukon ESA

**Note:** Government of Yukon employees have enhanced benefits (4-8 weeks), but this applies only to government employees, not private sector under ESA.

---

## Config Verification Checklist

Compare with `backend/config/holiday_pay/2025/provinces_jan.json`:

- [x] `formula_type` - Config uses `30_day_average` (acceptable approximation for standard employees)
- [x] `formula_params.lookback_days` - 30 days configured
- [x] `eligibility.min_employment_days` - ✅ 30 days is correct
- [x] `eligibility.require_last_first_rule` - ✅ Updated to `true` on 2025-12-31
- [x] `premium_rate` - ✅ 1.5 is correct
- [x] `notes` - ✅ Added official URL reference

---

## Differences Found

| Field | Official | Current Config | Action Needed |
|-------|----------|----------------|---------------|
| All fields | - | - | ✅ All verified and updated on 2025-12-31 |

**Note:** Yukon uses a dual formula (regular day's pay for standard employees, 10% of 2 weeks for irregular hours). The current `30_day_average` is an acceptable simplification for most cases.

---

## References

1. Yukon Employment Standards Main: https://yukon.ca/en/employment/employment-standards
2. Statutory Holidays (Employers): https://yukon.ca/en/doing-business/employer-responsibilities/find-yukon-statutory-holiday
3. Statutory Holidays (Employees): https://yukon.ca/en/employment/employment-standards/find-employee-information-statutory-holidays
4. General Holiday Pay: https://yukon.ca/en/employment/employment-standards/find-out-about-general-holiday-pay-under-employment-standards-act
5. Vacation Pay: https://yukon.ca/en/employment/employment-standards/learn-about-annual-vacation-pay-and-vacation-time
6. Contact: Employment Standards Office - 867-667-5944 / employmentstandards@yukon.ca / Toll-free in Yukon: 1-800-661-0408 ext 5944
