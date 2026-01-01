# Newfoundland and Labrador - Holiday Pay Official Reference

> **Status**: ✅ Verified
> **Last Verified**: 2025-12-31
> **Verified By**: Claude Code

## Official Sources

| Source | URL |
|--------|-----|
| Labour Standards Act | https://assembly.nl.ca/legislation/sr/statutes/l02.htm |
| LSA Issues Overview | https://www.gov.nl.ca/ecc/labour/lsaissues/ |
| Government Holidays 2025 | https://www.gov.nl.ca/hcs/files/24-19-Government-Holidays-2025.pdf |

---

## Statutory Holidays (2025)

| Holiday | Date | Statutory? | Notes |
|---------|------|------------|-------|
| New Year's Day | Jan 1 (Wed) | Yes | |
| Good Friday | Apr 18 (Fri) | Yes | |
| Memorial Day | Jul 1 (Tue) | Yes | Same date as Canada Day, commemorates WWI Battle of Beaumont-Hamel |
| Labour Day | Sep 1 (Mon) | Yes | |
| Remembrance Day | Nov 11 (Tue) | Yes | |
| Christmas Day | Dec 25 (Thu) | Yes | |

**Total: 6 statutory holidays**

**NOT statutory holidays in NL:**
- Family Day (not observed)
- Victoria Day (not observed)
- Thanksgiving (not statutory - employers may give it off but not required)
- Boxing Day (not statutory)
- National Day for Truth and Reconciliation (federal employees only)

---

## Eligibility Rules

| Rule | Value | Notes |
|------|-------|-------|
| min_employment_days | 30 | Must be employed 30+ days before the holiday |
| require_last_first_rule | Yes | Must work last scheduled day before AND first after holiday |
| "5 of 9" rule | No | Not applicable |

### Details

Per Section 19(1) of the Labour Standards Act, an employee is NOT entitled to holiday pay if:
- The public holiday occurs within 30 days following the beginning of employment
- The employee fails to work the regular day before and after the holiday without just cause

---

## Holiday Pay Formula

### Formula Type
- **Type**: 3_week_average_hours
- **Lookback Period**: 3 weeks immediately preceding the holiday

### Calculation
```
Holiday Pay = Hourly Rate × Average Hours Worked Per Day (in preceding 3 weeks)
```

Per Section 15(3): "The wages to which an employee is entitled under subsection (2) shall be calculated by multiplying the employee's hourly rate of pay by the average number of hours worked in a day in the 3 weeks immediately preceding the holiday."

### Includes
- [x] Regular wages (hourly rate)
- [ ] Overtime
- [ ] Vacation pay
- [ ] Previous holiday pay

### Key Difference from Other Provinces
NL uses a **3-week lookback** (not 4 weeks) and calculates based on **average hours per day** multiplied by hourly rate, not total wages divided by days.

---

## Regular vs Non-Regular Work Day

### Pay Rules

| Scenario | Pay | Formula |
|----------|-----|---------|
| Holiday + Not Worked | Holiday pay | Hourly rate × avg daily hours (3 weeks) |
| Holiday + Worked | 2× wages OR substitute day | See options below |

### Options When Working on Holiday (Section 17)

Per Section 17(1), when an employee works on a public holiday, they receive one of:
1. **Double pay**: Twice the wages properly earned for that day
2. **Substitute day (30 days)**: One paid day off within 30 days at regular holiday rate
3. **Extra vacation**: One extra day added to annual vacation at regular holiday rate

---

## Premium Rate

- **Rate**: 2.0× (double time)
- **Notes**: Higher than most provinces which use 1.5× premium

---

## Vacation Pay

| Years of Service | Vacation Weeks | Vacation Pay Rate |
|------------------|----------------|-------------------|
| < 15 years | 2 weeks | 4% of total wages |
| 15+ years | 3 weeks | 6% of total wages |

### Eligibility (Section 8)
- Must work 90% of normal working hours in the 12-month period
- After 15 years continuous employment, entitled to enhanced rate

---

## Config Verification Checklist

Compare with `backend/config/holiday_pay/2025/provinces_jan.json`:

| Field | Official | Current Config | Match? |
|-------|----------|----------------|--------|
| formula_type | 3_week_average_hours | 30_day_average | ⚠️ MISMATCH |
| lookback_period | 3 weeks | 30 days | ⚠️ MISMATCH |
| method | hourly_rate × avg_hours | total_wages_div_days | ⚠️ MISMATCH |
| min_employment_days | 30 | 30 | ✅ |
| require_last_first_rule | true | false | ⚠️ MISMATCH |
| premium_rate | 2.0 | 1.5 | ⚠️ MISMATCH |

---

## Differences Found

| Field | Official | Current Config | Action Needed |
|-------|----------|----------------|---------------|
| formula_type | 3_week_average_hours | 30_day_average | Update to correct formula type |
| lookback | 3 weeks (21 days) | 30 days | Update to 21 days / 3 weeks |
| method | hourly_rate × avg_daily_hours | total_wages_div_days | Update calculation method |
| require_last_first_rule | true | false | Update to true |
| premium_rate | 2.0 | 1.5 | Update to 2.0 (double time) |

### Recommended Config Update

```json
"NL": {
  "province_code": "NL",
  "name": "Newfoundland and Labrador",
  "formula_type": "3_week_average_hours",
  "formula_params": {
    "lookback_weeks": 3,
    "method": "hourly_rate_x_avg_daily_hours",
    "include_overtime": false,
    "new_employee_fallback": "ineligible"
  },
  "eligibility": {
    "min_employment_days": 30,
    "require_last_first_rule": true,
    "notes": "30 days employment required, must work day before and after holiday"
  },
  "premium_rate": 2.0,
  "notes": "NL LSA s.15(3) - hourly rate × avg hours/day in 3 weeks. Premium is 2×."
}
```

---

## References

1. Newfoundland and Labrador Labour Standards Act, RSNL 1990, c L-2
2. https://assembly.nl.ca/legislation/sr/statutes/l02.htm
3. https://www.gov.nl.ca/ecc/labour/lsaissues/
4. https://canada-holidays.ca/provinces/NL
5. https://ebsource.ca/statutory-holidays-in-newfoundland-and-labrador/
