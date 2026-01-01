# Nova Scotia - Holiday Pay Official Reference

> **Status**: ✅ Verified
> **Last Verified**: 2025-12-31
> **Verified By**: Claude Code

## Official Sources

| Source | URL |
|--------|-----|
| Holiday Pay | https://novascotia.ca/lae/employmentrights/holidaypay.asp |
| Holiday Chart | https://novascotia.ca/lae/employmentrights/holidaychart.asp |
| Vacation Time and Pay | https://novascotia.ca/lae/employmentrights/vacationleavepay.asp |
| Remembrance Day | https://novascotia.ca/lae/employmentrights/remembrance.asp |
| Truth and Reconciliation Day | https://novascotia.ca/lae/employmentrights/truth-and-reconciliation-day.asp |
| Labour Standards Code Guide | https://novascotia.ca/lae/employmentrights/docs/labourstandardscodeguide.pdf |

---

## Paid Holidays (2025)

| Holiday | Date | Paid Holiday? | Notes |
|---------|------|---------------|-------|
| New Year's Day | Wed, Jan 1 | ✓ | Labour Standards Code |
| Nova Scotia Heritage Day | Mon, Feb 17 | ✓ | 3rd Monday in February (NS unique) |
| Good Friday | Fri, Apr 18 | ✓ | Labour Standards Code |
| Easter Sunday | Sun, Apr 20 | ✗ | Retail closing day only |
| Victoria Day | May 19 | ✗ | Not a paid holiday in NS |
| Canada Day | Tue, Jul 1 | ✓ | Labour Standards Code |
| Natal Day | Aug 4 | ✗ | Not a paid holiday in NS |
| Labour Day | Mon, Sep 1 | ✓ | Labour Standards Code |
| Truth & Reconciliation Day | Tue, Sep 30 | ✗ | Public sector closes; not private sector paid holiday |
| Thanksgiving Day | Mon, Oct 13 | ✗ | Retail closing day only |
| Remembrance Day | Tue, Nov 11 | ⚠️ | Separate legislation - see below |
| Christmas Day | Thu, Dec 25 | ✓ | Labour Standards Code |
| Boxing Day | Fri, Dec 26 | ✗ | Retail closing day only |

**Total Labour Standards Code Paid Holidays: 6**

### Remembrance Day Special Rules

Remembrance Day is governed by the **Remembrance Day Act**, not the Labour Standards Code:
- Employees must **actually work** on Nov 11 to qualify for a paid day off (unlike other holidays)
- **No premium pay** (no time-and-a-half) required
- **Exempt industries**: Farming, fishing, aquaculture, Christmas tree operations, forestry, industrial undertakings
- Cannot substitute another day for November 11

---

## Eligibility Rules

| Rule | Value | Notes |
|------|-------|-------|
| min_employment_days | **Not specified** | No minimum employment days stated |
| min_days_entitled_to_pay | **15** | Must be entitled to receive pay for 15 of 30 days before holiday |
| require_last_first_rule | **Yes** | Must work last scheduled shift before AND first scheduled shift after |

### Details

To qualify for holiday pay, an employee must:
1. Be **entitled to receive pay** for at least **15 of the 30 calendar days** immediately before the holiday
2. Work their **last scheduled shift** before the holiday
3. Work their **first scheduled shift** after the holiday

**What counts as "entitled to receive pay":**
- Days actually worked
- Paid sick leave
- Paid training/courses
- Vacation time

**Important**: The phrase is "entitled to receive pay" NOT "days worked" - this is broader.

**Exception**: If an employer prohibits the employee from reporting on scheduled days, the employee still qualifies if they meet the 15-of-30 requirement.

---

## Holiday Pay Formula

### Formula Type
- **Type**: `30_day_average` (Average Day's Pay)
- **Lookback Period**: 30 calendar days immediately before the holiday

### Calculation

**For hourly/regular workers:**
```
Holiday Pay = Regular day's pay
```

**For variable hours:**
```
Holiday Pay = Average hours over 30-day period × hourly rate
```

**For commission-based:**
```
Holiday Pay = Total commissions in 30 days ÷ Days worked
Example: $2040 ÷ 17 days = $120 average day's pay
```

### When Holiday Falls on Day Off
- Employer must provide a different day off with pay
- Options: Working day immediately after holiday, working day after vacation, or mutually agreed day

---

## Regular vs Non-Regular Work Day

| Scenario | Pay |
|----------|-----|
| Holiday + NOT worked (regular day off) | One day's pay + substitute day off |
| Holiday + NOT worked (scheduled to work) | One regular day's pay |
| Holiday + WORKED | Regular/average day's pay + 1.5× for hours worked |

---

## Premium Rate

- **Rate**: 1.5× (time and a half)
- **Applies to**: Hours actually worked on the holiday
- **Plus**: Regular or average day's pay

**Exception for continuous operations:**
- Employer may pay straight time for hours worked
- Plus grant a different paid day off instead

---

## Vacation Pay

| Years of Service | Vacation Weeks | Vacation Pay Rate |
|------------------|----------------|-------------------|
| 0-7 years | 2 weeks | 4% of gross wages |
| 8+ years | 3 weeks | 6% of gross wages |

### Key Details
- Vacation pay increases to 6% at **start of 8th year** (after completing 7 years)
- Vacation time increases to 3 weeks at **start of 9th year** (after completing 8 years)
- Applies to: Full-time, part-time, casual, and seasonal workers
- Vacation must be taken within 10 months of being earned

### Exemptions
- Real estate/car salespeople
- Commissioned salespeople
- Domestic workers under 24 hours weekly

---

## Config Verification Checklist

Compare with `backend/config/holiday_pay/2025/provinces_jan.json`:

- [x] `formula_type` matches official - `30_day_average` is correct
- [x] `formula_params.lookback_days` matches official - 30 is correct
- [x] `formula_params.method` matches official - `total_wages_div_days` is correct
- [x] `premium_rate` matches official - 1.5 is correct
- [ ] `eligibility.require_last_first_rule` - **MISMATCH**: Config has `false`, should be `true`
- [ ] `eligibility.min_employment_days` - Config has `30`, but NS specifies `15 of 30 days entitled to pay` (different concept)

---

## Differences Found

| Field | Official | Current Config | Action Needed |
|-------|----------|----------------|---------------|
| eligibility.require_last_first_rule | `true` | `false` | Change to `true` |
| eligibility.min_employment_days | Not specified (uses 15/30 rule) | `30` | Consider renaming to `min_days_entitled_to_pay: 15` |
| eligibility.notes | "15 of 30 days entitled to pay + last/first rule" | "30 days of employment required" | Update notes |

---

## Special Notes for NS

1. **Only 6 standard paid holidays** - fewer than most provinces
2. **Remembrance Day** has completely separate rules under the Remembrance Day Act
3. **Victoria Day, Thanksgiving** are NOT paid holidays in NS
4. **Truth & Reconciliation Day** is NOT a paid holiday for private sector
5. **"Entitled to receive pay"** is broader than "days worked" - includes paid leave, vacation

---

## References

1. Nova Scotia Holiday Pay: https://novascotia.ca/lae/employmentrights/holidaypay.asp
2. Nova Scotia Holiday Chart: https://novascotia.ca/lae/employmentrights/holidaychart.asp
3. Nova Scotia Vacation Pay: https://novascotia.ca/lae/employmentrights/vacationleavepay.asp
4. Nova Scotia Remembrance Day: https://novascotia.ca/lae/employmentrights/remembrance.asp
5. Nova Scotia Labour Standards Code Guide: https://novascotia.ca/lae/employmentrights/docs/labourstandardscodeguide.pdf
