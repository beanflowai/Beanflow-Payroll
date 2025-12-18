---
name: payroll-domain
description: Canadian payroll domain knowledge - CPP, EI, federal/provincial tax calculations, vacation pay, statutory holidays, pay frequencies, ROE, T4
owner: Payroll Team
last_updated: 2025-12-18
triggers:
  - payroll calculations
  - CPP contribution
  - EI premium
  - tax calculations
  - federal tax
  - provincial tax
  - vacation pay
  - statutory holiday
  - pay frequency
  - ROE
  - T4
  - deductions
related_skills:
  - backend-development
  - frontend-development
agent_hints:
  token_budget_hint: "Load for payroll-specific business logic and calculations"
  write_scope: ["writes-backend", "writes-frontend"]
  plan_shape: ["Identify applicable tax rules", "Calculate deductions", "Validate against CRA guidelines"]
  approval_required_if: ["Tax calculation changes", "New deduction types"]
---

# Quick Reference Card
- When to use: Implementing payroll calculations, tax deductions, vacation pay, statutory holiday pay
- 3-step approach:
  1) Identify pay frequency and annualization factors
  2) Calculate statutory deductions (CPP, EI, federal/provincial tax)
  3) Apply vacation pay and other deductions
- How to verify: Cross-check with CRA payroll deduction tables; validate year-to-date accumulations

---

# Canadian Payroll Domain Knowledge

## Pay Frequencies

| Frequency | Periods/Year | Description |
|-----------|--------------|-------------|
| Weekly | 52 | Paid every week |
| Bi-weekly | 26 | Paid every two weeks |
| Semi-monthly | 24 | Paid twice per month (e.g., 1st and 15th) |
| Monthly | 12 | Paid once per month |

### Annualization Factor

To calculate annual amounts from periodic pay:
```
Annual Amount = Periodic Amount × Pay Periods Per Year
```

---

## CPP (Canada Pension Plan) Contributions - 2025

### Key Values (2025)

| Parameter | Value |
|-----------|-------|
| Maximum Pensionable Earnings (YMPE) | $71,300 |
| Basic Exemption (annual) | $3,500 |
| Employee Contribution Rate | 5.95% |
| Second Additional CPP Rate (CPP2) | 4.00% |
| YAMPE (Year's Additional Maximum) | $81,200 |

### Calculation Steps

1. **Calculate pensionable earnings** (gross pay minus non-pensionable items)
2. **Apply basic exemption** (prorated by pay period)
3. **Calculate contribution** up to maximum

```python
def calculate_cpp_contribution(
    pensionable_earnings: float,
    pay_periods: int,
    ytd_cpp: float,
    ytd_pensionable: float
) -> dict[str, float]:
    """Calculate CPP contribution for a pay period."""
    YMPE = 71300.0
    BASIC_EXEMPTION = 3500.0
    CPP_RATE = 0.0595
    MAX_CPP = (YMPE - BASIC_EXEMPTION) * CPP_RATE  # $4,034.10

    # Prorated basic exemption
    period_exemption = BASIC_EXEMPTION / pay_periods

    # Contributory earnings
    contributory = max(0, pensionable_earnings - period_exemption)

    # Calculate contribution
    contribution = contributory * CPP_RATE

    # Check against remaining room
    remaining_room = MAX_CPP - ytd_cpp
    contribution = min(contribution, remaining_room)

    return {
        "cppContribution": round(contribution, 2),
        "contributoryEarnings": round(contributory, 2)
    }
```

---

## EI (Employment Insurance) Premiums - 2025

### Key Values (2025)

| Parameter | Value |
|-----------|-------|
| Maximum Insurable Earnings (MIE) | $65,700 |
| Employee Premium Rate | 1.64% |
| Maximum Annual Premium | $1,077.48 |

### Calculation

```python
def calculate_ei_premium(
    insurable_earnings: float,
    ytd_ei: float
) -> dict[str, float]:
    """Calculate EI premium for a pay period."""
    MIE = 65700.0
    EI_RATE = 0.0164
    MAX_EI = MIE * EI_RATE  # $1,077.48

    # Calculate premium
    premium = insurable_earnings * EI_RATE

    # Check against remaining room
    remaining_room = MAX_EI - ytd_ei
    premium = min(premium, remaining_room)

    return {
        "eiPremium": round(premium, 2),
        "insurableEarnings": round(insurable_earnings, 2)
    }
```

---

## Federal Income Tax - 2025

### Tax Brackets (2025)

| Bracket | Income Range | Rate |
|---------|--------------|------|
| 1 | $0 - $57,375 | 15% |
| 2 | $57,375 - $114,750 | 20.5% |
| 3 | $114,750 - $177,882 | 26% |
| 4 | $177,882 - $253,414 | 29% |
| 5 | Over $253,414 | 33% |

### Basic Personal Amount (2025)

- Base amount: $16,129
- Higher income threshold: $177,882
- Reduced amount for high earners

### Calculation Method

1. **Annualize periodic income**
2. **Calculate annual tax using brackets**
3. **Apply tax credits**
4. **De-annualize to get periodic tax**

```python
def calculate_federal_tax(
    annualized_taxable_income: float,
    td1_claim: float = 16129.0  # Basic personal amount
) -> float:
    """Calculate federal tax on annualized income."""
    BRACKETS = [
        (57375, 0.15),
        (114750, 0.205),
        (177882, 0.26),
        (253414, 0.29),
        (float('inf'), 0.33)
    ]

    tax = 0.0
    prev_threshold = 0

    for threshold, rate in BRACKETS:
        if annualized_taxable_income <= prev_threshold:
            break
        taxable_in_bracket = min(
            annualized_taxable_income - prev_threshold,
            threshold - prev_threshold
        )
        tax += taxable_in_bracket * rate
        prev_threshold = threshold

    # Apply basic personal amount credit
    credit = td1_claim * 0.15
    tax = max(0, tax - credit)

    return round(tax, 2)
```

---

## Provincial Income Tax

### Ontario Tax Brackets (2025 Example)

| Bracket | Income Range | Rate |
|---------|--------------|------|
| 1 | $0 - $52,886 | 5.05% |
| 2 | $52,886 - $105,775 | 9.15% |
| 3 | $105,775 - $150,000 | 11.16% |
| 4 | $150,000 - $220,000 | 12.16% |
| 5 | Over $220,000 | 13.16% |

### British Columbia Tax Brackets (2025 Example)

| Bracket | Income Range | Rate |
|---------|--------------|------|
| 1 | $0 - $47,937 | 5.06% |
| 2 | $47,937 - $95,875 | 7.70% |
| 3 | $95,875 - $110,076 | 10.50% |
| 4 | $110,076 - $133,664 | 12.29% |
| 5 | $133,664 - $181,232 | 14.70% |
| 6 | Over $181,232 | 20.50% |

### Implementation Pattern

```python
def get_provincial_tax_calculator(province: str):
    """Get tax calculator for specific province."""
    calculators = {
        "ON": calculate_ontario_tax,
        "BC": calculate_bc_tax,
        "AB": calculate_alberta_tax,
        # Add other provinces...
    }
    return calculators.get(province)
```

---

## Vacation Pay

### Minimum Standards by Province

| Province | < 5 Years | 5+ Years |
|----------|-----------|----------|
| Ontario | 4% (2 weeks) | 6% (3 weeks) |
| British Columbia | 4% (2 weeks) | 6% (3 weeks) |
| Alberta | 4% (2 weeks) | 6% (3 weeks) |
| Federal | 4% (2 weeks) | 6% (3 weeks) |

### Calculation Methods

**Method 1: Percentage of Earnings**
```python
vacation_pay = gross_earnings * vacation_rate
```

**Method 2: Paid Time Off**
```python
# Calculate daily rate
daily_rate = annual_salary / working_days_per_year

# Vacation pay for days taken
vacation_pay = vacation_days_taken * daily_rate
```

### Accrual Tracking

```python
def calculate_vacation_accrual(
    gross_pay: float,
    vacation_rate: float,
    ytd_accrued: float,
    ytd_taken: float
) -> dict[str, float]:
    """Calculate vacation accrual for pay period."""
    accrual = gross_pay * vacation_rate
    new_ytd_accrued = ytd_accrued + accrual
    balance = new_ytd_accrued - ytd_taken

    return {
        "periodAccrual": round(accrual, 2),
        "ytdAccrued": round(new_ytd_accrued, 2),
        "ytdTaken": round(ytd_taken, 2),
        "balance": round(balance, 2)
    }
```

---

## Statutory Holidays

### Federal Statutory Holidays

| Holiday | Date |
|---------|------|
| New Year's Day | January 1 |
| Good Friday | Varies |
| Victoria Day | Monday before May 25 |
| Canada Day | July 1 |
| Labour Day | First Monday in September |
| National Day for Truth and Reconciliation | September 30 |
| Thanksgiving | Second Monday in October |
| Remembrance Day | November 11 |
| Christmas Day | December 25 |

### Statutory Holiday Pay Calculation

```python
def calculate_stat_holiday_pay(
    wages_earned_in_4_weeks: float,
    days_worked_in_4_weeks: int
) -> float:
    """Calculate statutory holiday pay (Ontario method)."""
    if days_worked_in_4_weeks == 0:
        return 0.0

    average_daily_wage = wages_earned_in_4_weeks / days_worked_in_4_weeks
    return round(average_daily_wage, 2)
```

---

## Payroll Run Data Structure

```python
class PayrollRunResult:
    """Complete payroll run result for an employee."""

    employeeId: str
    payDate: str
    payPeriodStart: str
    payPeriodEnd: str

    # Earnings
    regularHours: float
    regularPay: float
    overtimeHours: float
    overtimePay: float
    grossPay: float

    # Statutory Deductions
    cppContribution: float
    eiPremium: float
    federalTax: float
    provincialTax: float
    totalStatutoryDeductions: float

    # Other Deductions
    vacationPayAccrued: float
    otherDeductions: float
    totalDeductions: float

    # Net Pay
    netPay: float

    # Year-to-Date
    ytdGrossPay: float
    ytdCpp: float
    ytdEi: float
    ytdFederalTax: float
    ytdProvincialTax: float
    ytdNetPay: float
```

---

## ROE (Record of Employment)

### When to Issue ROE

- Employee separation (quit, terminated, laid off)
- Leave of absence (maternity, parental, sick)
- Reduction in hours

### Key Fields

| Block | Description |
|-------|-------------|
| 10 | First day worked |
| 11 | Last day paid |
| 12 | Final pay period end date |
| 15A | Total insurable hours |
| 15B | Total insurable earnings |
| 16 | Reason for issuing |
| 17 | Vacation pay (if applicable) |

### Reason Codes

| Code | Reason |
|------|--------|
| A | Shortage of work |
| D | Illness or injury |
| E | Quit |
| K | Other |
| M | Dismissal |
| N | Leave of absence |

---

## T4 (Statement of Remuneration Paid)

### Key Boxes

| Box | Description |
|-----|-------------|
| 14 | Employment income |
| 16 | CPP contributions |
| 18 | EI premiums |
| 22 | Income tax deducted |
| 24 | EI insurable earnings |
| 26 | CPP pensionable earnings |
| 44 | Union dues |
| 52 | Pension adjustment |

### Filing Requirements

- Due date: Last day of February
- Electronic filing required for more than 5 T4s
- Must match payroll records exactly

---

## Validation Checklist

When implementing payroll calculations:

- [ ] CPP contribution does not exceed annual maximum?
- [ ] EI premium does not exceed annual maximum?
- [ ] Basic exemption applied correctly (prorated by pay period)?
- [ ] Tax brackets applied correctly?
- [ ] Provincial tax using correct province's rates?
- [ ] Vacation pay calculated at correct rate?
- [ ] YTD accumulators updated correctly?
- [ ] Statutory holiday pay calculated correctly?

---

## Related Resources

### Project Documentation (Detailed)

| Document | Content |
|----------|---------|
| `docs/02_phase2_calculations.md` | CPP/EI/Federal/Provincial tax formulas (CRA T4127) |
| `docs/08_holidays_vacation.md` | All provincial holidays, vacation pay, sick leave |
| `docs/09_year_end_processing.md` | Year-end procedures, T4 generation |
| `docs/10_remittance_reporting.md` | CRA remittance schedules, reporting |
| `docs/11_roe_generation.md` | ROE generation rules and codes |
| `docs/12_garnishments_deductions.md` | Garnishments, child support, other deductions |

### Quick Reference Skills

- **Tax Rates 2025**: See `tax-rates-2025` skill (CPP/EI/tax bracket quick reference)
- **Vacation & Holidays**: See `vacation-holidays` skill (statutory holidays, vacation pay)

### CRA Official Resources

- **Payroll Deductions Online Calculator**: https://www.canada.ca/en/revenue-agency/services/e-services/e-services-businesses/payroll-deductions-online-calculator.html
- **T4032 Payroll Deductions Tables**: https://www.canada.ca/en/revenue-agency/services/forms-publications/payroll/t4032-payroll-deductions-tables.html
- **T4127 Payroll Deductions Formulas**: https://www.canada.ca/en/revenue-agency/services/forms-publications/payroll/t4127-payroll-deductions-formulas.html

### Related Skills

- **Backend Development**: See `backend-development` skill
- **Frontend Development**: See `frontend-development` skill
