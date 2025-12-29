---
name: vacation-holidays
description: Quick reference for Canadian statutory holidays and vacation pay by province. For detailed calculations, see docs/08_holidays_vacation.md
owner: Payroll Team
last_updated: 2025-12-18
triggers:
  - statutory holidays
  - vacation pay
  - holiday pay
  - sick leave
  - provincial holidays
  - stat holiday
related_skills:
  - payroll-domain
  - tax-rates-2025
agent_hints:
  token_budget_hint: "Quick reference only - for detailed rules see docs/08_holidays_vacation.md"
  write_scope: ["reads"]
---

# Canadian Holidays & Vacation Pay - Quick Reference

> **Detailed Documentation**: `docs/08_holidays_vacation.md`

---

## Statutory Holidays by Province - 2025

| Holiday | AB | BC | MB | NB | NL | NS | NT | NU | ON | PE | SK | YT |
|---------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| New Year's (Jan 1) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Family Day (Feb 17) | ✓ | ✓ | MB¹ | ✓ | - | NS² | - | - | ✓ | PE³ | ✓ | - |
| Good Friday (Apr 18) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Victoria Day (May 19) | ✓ | ✓ | ✓ | ✓ | - | - | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Canada Day (Jul 1) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Civic Holiday (Aug 4) | ? | BC⁴ | - | - | - | - | ✓ | ✓ | - | - | ✓ | - |
| Labour Day (Sep 1) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Truth & Reconciliation (Sep 30) | ? | ✓ | ✓ | - | - | - | - | ✓ | - | ✓ | - | ✓ |
| Thanksgiving (Oct 13) | ✓ | ✓ | ✓ | ✓ | - | - | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Remembrance Day (Nov 11) | ✓ | ✓ | - | - | ✓ | - | ✓ | ✓ | - | ✓ | ✓ | ✓ |
| Christmas (Dec 25) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Boxing Day (Dec 26) | ? | - | - | - | - | - | - | - | ✓ | - | - | - |
| **Total Statutory** | 9 | 11 | 9 | 7 | 6 | 6 | 10 | 12 | 9 | 8 | 10 | 9 |

**Legend**: ✓ = Statutory, ? = Optional, - = Not a holiday
¹ Louis Riel Day, ² Heritage Day, ³ Islander Day, ⁴ BC Day

---

## 2025 Moveable Holiday Dates

| Holiday | 2025 | 2026 |
|---------|------|------|
| Family Day (3rd Mon Feb) | Feb 17 | Feb 16 |
| Good Friday | Apr 18 | Apr 3 |
| Easter Monday | Apr 21 | Apr 6 |
| Victoria Day (Mon before May 25) | May 19 | May 18 |
| Civic Holiday (1st Mon Aug) | Aug 4 | Aug 3 |
| Labour Day (1st Mon Sep) | Sep 1 | Sep 7 |
| Thanksgiving (2nd Mon Oct) | Oct 13 | Oct 12 |

---

## Holiday Pay Formulas by Province

### Ontario
```
Holiday Pay = (Wages + Vacation Pay in past 4 weeks) ÷ 20
```

### British Columbia
```
Hourly: Average Daily Hours × Hourly Rate
Salaried: Annual Salary ÷ Pay Periods ÷ Work Days per Period
```

### Alberta
```
Holiday Pay = (Wages in past 4 weeks) ÷ (Days worked in past 4 weeks)
OR if scheduled: Regular day's pay
```

### Manitoba / Saskatchewan
```
Holiday Pay = 5% of gross wages in 4-week period before holiday
```

> **Full formulas for all provinces**: `docs/08_holidays_vacation.md:124-350`

---

## Vacation Pay Rates

| Tenure | Standard Rate | Provinces with 8% |
|--------|---------------|-------------------|
| < 5 years | **4%** (2 weeks) | - |
| 5-10 years | **6%** (3 weeks) | - |
| 10+ years | 6% | SK (8% = 4 weeks) |

### Vacation Pay Calculation

```python
# Per-Period Method (paid each paycheck)
vacation_pay = gross_pay × vacation_rate

# Accrual Method (paid when vacation taken)
accrued = gross_wages_in_year × vacation_rate
daily_rate = accrued ÷ vacation_days_entitled
```

---

## Sick Leave by Province (2025)

| Province | Paid Days | Unpaid Days | Waiting Period | Carryover |
|----------|-----------|-------------|----------------|-----------|
| **BC** | 5 | 3 | 90 days | No |
| **ON** | 0 | 3 (IDEL) | None | No |
| **AB** | 0 | 0 | N/A | N/A |
| **MB** | 0 | 0 | N/A | N/A |
| **SK** | 0 | 0 | N/A | N/A |
| **Federal** | 10 | 0 | 30 days | Yes (max 10) |

### Part-Time Employee Rule
**Important**: Part-time employees are **NOT pro-rated** - they receive full entitlement.

### Sick Pay Calculation

**BC (Average Day's Pay)**:
```
Sick Pay = (Wages past 30 days) ÷ (Days worked past 30 days)
- Excludes overtime
- Includes vacation pay
```

**Federal (Variable Hours)**:
```
Sick Pay = Average daily earnings for last 20 days worked
- Excludes overtime
- Accrual: 3 days after 30-day period, +1 day/month (max 10)
```

> **Full details**: `docs/08_holidays_vacation.md:2476-2838`

---

## Quick Reference: Holiday Worked Premium

| Province | Premium |
|----------|---------|
| **Ontario** | Holiday pay + 1.5× for hours worked |
| **BC** | Holiday pay + 1.5× for first 12 hrs, 2× after |
| **Alberta** | Holiday pay + 1.5× for hours worked |
| **Most others** | Holiday pay + regular wages OR substitute day |

---

## Detailed Documentation Links

- **All Provincial Holiday Calendars**: `docs/08_holidays_vacation.md:56-102`
- **Holiday Pay Formulas by Province**: `docs/08_holidays_vacation.md:124-350`
- **Vacation Pay Accrual**: `docs/08_holidays_vacation.md:38-52`
- **Sick Leave Details**: `docs/08_holidays_vacation.md` (varies by province section)
- **Official Sources**:
  - Ontario: https://www.ontario.ca/document/your-guide-employment-standards-act-0/public-holidays
  - BC: https://www2.gov.bc.ca/gov/content/employment-business/employment-standards-advice/employment-standards/statutory-holidays
  - Federal: https://www.canada.ca/en/services/jobs/workplace/federal-labour-standards/holidays.html
