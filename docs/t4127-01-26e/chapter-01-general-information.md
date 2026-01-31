# Chapter 1 – General Information

> Payroll Deductions Formulas - 122nd Edition
> Effective January 1, 2026

---

## 1.1 Overview

This chapter provides general information and procedures for calculating payroll deductions in Canada. It covers:

- Rounding procedures for mathematical calculations
- Pay period frequencies
- General calculation rules

---

## 1.2 Rounding Procedures

For all mathematical calculations in this guide, use the following rounding rules **except when we specify otherwise**.

### 1.2.1 For Income Tax Deductions

**Rule:** If the figure has three or more digits after the decimal point:

1. **Increase** the second digit after the decimal point by one if the third digit is **five or more**, and drop the third digit.
2. If the third digit is **less than five**, drop the third digit.

**Examples:**

| Calculation | Result |
|:------------|:-------|
| 123.4567 | 123.46 |
| 123.4549 | 123.45 |
| 123.4550 | 123.46 |
| 100.001 | 100.00 |
| 100.005 | 100.01 |

### 1.2.2 For Canada Pension Plan (CPP) Calculations

#### Basic Exemption

**Calculation:**
```
Basic Exemption per pay period = Annual Basic Exemption ÷ Number of pay periods
```

**Rounding Rule:**
- If the figure has three or more digits after the decimal point, **drop the third digit** (do not round up).

**Examples:**

| Pay Periods | Calculation | Unrounded | Rounded |
|:------------|:------------|:----------|:--------|
| 12 (monthly) | $3,500 ÷ 12 | 291.666... | 291.66 |
| 24 (semi-monthly) | $3,500 ÷ 24 | 145.833... | 145.83 |
| 26 (bi-weekly) | $3,500 ÷ 26 | 134.615... | 134.61 |
| 52 (weekly) | $3,500 ÷ 52 | 67.307... | 67.30 |

#### CPP Contributions

**Calculation:**
```
C = (I - BPE) × 0.0595
```

**Rounding Rule:**
- Use the same rounding rule as income tax deductions (round up if 3rd digit ≥ 5).

**Important Note:**
Rate ratios in formulas are part of the calculation and **should not be rounded**. Only the final contribution amount should be rounded.

**Example:**

For bi-weekly pay with gross income of $2,000:
```
BPE = 134.61
C = (2000 - 134.61) × 0.0595
C = 1865.39 × 0.0595
C = 110.990705 → 110.99
```

### 1.2.3 For Employment Insurance (EI) Premiums

**Rounding Rule:**
- Use the same rounding rule as income tax deductions (round up if 3rd digit ≥ 5).

**Example:**

For bi-weekly pay with gross income of $2,000:
```
EI = 2000 × 0.0163
EI = 32.60 → 32.60 (already has 2 decimal places)
```

### 1.2.4 For Tax Calculations

**General Rule:**
- All intermediate calculations should maintain at least 4 decimal places
- Only the final tax deduction amount should be rounded to 2 decimal places

---

## 1.3 Pay Period Frequencies

When using the formulas in this guide, you must know the number of pay periods in the year (**P**).

### Common Pay Period Frequencies

| Pay Frequency | Pay Periods (P) | Description |
|:--------------|:----------------|:------------|
| Annual | 1 | Once per year |
| Semi-annual | 2 | Twice per year |
| Quarterly | 4 | Four times per year |
| Monthly | 12 | 12 times per year |
| Semi-monthly | 24 | 24 times per year (e.g., 15th and end of month) |
| Bi-weekly | 26 | Every two weeks (52 weeks ÷ 2) |
| Weekly | 52 | Every week |
| Daily | 260 | Working days (52 weeks × 5 days) |

### Special Cases

#### 27 Pay Periods in a Year

In some years, bi-weekly payrolls may have **27 pay periods** instead of 26 due to calendar alignment.

**How to handle:**
- Use **P = 27** for that year
- Adjust all per-period calculations accordingly
- This occurs approximately every 11 years

#### Leap Years

For weekly and bi-weekly pay periods:
- A leap year adds one extra day (52 weeks + 1 day)
- This does **not** change the number of pay periods (P)
- Use standard P values (52 for weekly, 26 for bi-weekly)

---

## 1.4 Annualization Factors

When converting between pay period amounts and annual amounts, use the following factors:

### To Annualize (Multiply)

| Pay Frequency | Factor |
|:--------------|:-------|
| Weekly | × 52 |
| Bi-weekly | × 26 |
| Semi-monthly | × 24 |
| Monthly | × 12 |

### To Convert to Pay Period (Divide)

| Pay Frequency | Factor |
|:--------------|:-------|
| Weekly | ÷ 52 |
| Bi-weekly | ÷ 26 |
| Semi-monthly | ÷ 24 |
| Monthly | ÷ 12 |

---

## 1.5 Calculation Order

When calculating payroll deductions, follow this order:

1. **Calculate taxable income** (A)
2. **Calculate CPP contributions** (C)
3. **Calculate EI premiums** (EI)
4. **Calculate federal tax** (T1)
5. **Calculate provincial/territorial tax** (T2)
6. **Calculate total tax deduction** (T)

### Important Notes

- CPP contributions are **not tax-deductible** for income tax purposes
- EI premiums are **tax-deductible**
- RSP/RRSP contributions are **tax-deductible**
- Registered Pension Plan (RPP) contributions are **tax-deductible**

---

## 1.6 Maximum Contributions and Premiums

### Canada Pension Plan (CPP) - 2026

| Parameter | Amount |
|:----------|:-------|
| YMPE (Year's Maximum Pensionable Earnings) | $74,600 |
| Basic Exemption | $3,500 |
| YMCE (Year's Maximum Contributory Earnings) | $71,100 |
| Contribution Rate | 5.95% |
| Maximum Employee Contribution | $4,230.45 |
| Maximum Employer Contribution | $4,230.45 |

**Once an employee reaches the maximum contribution:**
- Stop deducting CPP contributions
- Continue calculating EI and tax deductions normally

### CPP2 (Additional CPP) - 2026

| Parameter | Amount |
|:----------|:-------|
| YAMPE (Year's Additional Maximum Pensionable Earnings) | $85,000 |
| CPP2 Rate | 4% |
| Maximum CPP2 Contribution | $416.00 |

**CPP2 contributions begin:**
- Only after year-to-date earnings exceed YMPE ($74,600)
- Only on earnings between YMPE and YAMPE ($74,600 to $85,000)

### Employment Insurance (EI) - 2026

| Parameter | Canada (except QC) | Quebec (QC) |
|:----------|:-------------------|:------------|
| Max Insurable Earnings | $68,900 | $68,900 |
| Employee Rate | 1.63% | 1.30% |
| Max Employee Premium | $1,123.07 | $895.70 |

**Once an employee reaches the maximum premium:**
- Stop deducting EI premiums
- Continue calculating CPP and tax deductions normally

---

## 1.7 Year-to-Date Tracking

For accurate calculation of maximum contributions, you must track:

### Year-to-Date (YTD) Amounts

| Amount | Description |
|:-------|:-------------|
| YTD Gross | Total gross earnings for the year |
| YTD CPP | Total CPP contributions for the year |
| YTD CPP2 | Total CPP2 contributions for the year |
| YTD EI | Total EI premiums for the year |
| YTD Tax | Total income tax deducted for the year |

### Tracking Maximums

**For CPP:**
```
If (YTD_CPP + Current_CPP) ≥ Max_CPP:
    CPP_Contribution = Max_CPP - YTD_CPP
    If CPP_Contribution < 0:
        CPP_Contribution = 0
```

**For EI:**
```
If (YTD_EI + Current_EI) ≥ Max_EI:
    EI_Premium = Max_EI - YTD_EI
    If EI_Premium < 0:
        EI_Premium = 0
```

**For CPP2:**
```
If YTD_Earnings > YMPE:
    CPP2_Earnings = Min(YTD_Earnings, YAMPE) - YMPE
    CPP2_Contribution = CPP2_Earnings × 0.04
    CPP2_Deduction = CPP2_Contribution - YTD_CPP2
    If CPP2_Deduction < 0:
        CPP2_Deduction = 0
```

---

## 1.8 Mid-Year Employment Changes

### New Employee During the Year

When an employee starts mid-year:
1. Determine the **remaining pay periods** in the year
2. Calculate deductions based on the **reduced number of pay periods**
3. Track YTD amounts normally

### Employee Leaves During the Year

When an employee leaves:
1. Final pay includes all outstanding amounts
2. Calculate deductions for the final pay period normally
3. Issue ROE (Record of Employment) for EI purposes

### Multiple Employers

**Important:** Each employer must calculate deductions independently:
- CPP maximums apply **per employer**
- EI maximums apply **per employer**
- Tax calculations are **per employer**
- Employees may contribute more than the annual maximum if they work for multiple employers

**Employee's Right to Refund:**
Employees can request a CPP/EI refund at year-end if total contributions exceed maximums.

---

## 1.9 Special Payment Types

### Bonuses and Retroactive Pay

Bonuses and retroactive pay increases are treated as **non-periodic income**:

**Method 1 - Tax at Source:**
```
Tax = Bonus × Marginal Tax Rate
```

**Method 2 - Aggregate Method:**
```
1. Add bonus to regular pay
2. Calculate tax on total
3. Subtract tax already paid on regular pay
4. Difference = Tax on bonus
```

### Commission Income

Commission-only income requires special calculations:
- Use **Option 1** or **Option 2** formulas
- Claim expenses against commission income
- CPP and EI calculated on gross commission

### Pension Income

Pension income has special tax treatment:
- May qualify for **pension income amount** tax credit
- Different CPP/EI rules (usually no CPP/EI on pension income)
- May be subject to withholding tax

### Tips and Gratuities

**Controlled Tips:**
- Reported by employer
- Subject to CPP, EI, and tax deductions

**Direct Tips:**
- Reported by employee
- Subject to CPP, EI, and tax deductions
- Employee must report to employer

---

## 1.10 Quebec Residents

Quebec residents have special considerations:

### Quebec Pension Plan (QPP)
- Different contribution rates (6.30% for 2026)
- Same YMPE as CPP
- Different maximums

### Quebec Provincial Tax
- Quebec has its own provincial tax system
- **Abattement** (16.5% federal tax abatement) applies
- Different tax brackets and rates

### Quebec Parental Insurance Plan (QPIP)
- Replaces EI for parental benefits in Quebec
- Lower EI premiums for Quebec residents
- QPIP premiums are separate

---

## 1.11 Prescribed Zones

Northern and prescribed zones have special tax considerations:

### Northern Residence Deductions

Employees living in prescribed zones may qualify for:
- **Housing deduction** (D)
- **Travel benefit deduction**
- **Board and lodging benefits** (U1)

### Prescribed Zone Zones

| Zone | Areas |
|:-----|:------|
| Zone 1 | Northwest Territories, Nunavut, Yukon |
| Zone 2 | Certain areas of BC, Alberta, Saskatchewan, Manitoba, Ontario, Quebec, Labrador |

---

*Continue to [Chapter 2 - Personal Tax Credits Returns](./chapter-02-td1-forms.md)*
