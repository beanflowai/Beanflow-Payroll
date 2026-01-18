# Chapter 6 – Canada Pension Plan

> Payroll Deductions Formulas - 122nd Edition
> Effective January 1, 2026

---

## 6.1 Overview

The **Canada Pension Plan (CPP)** is a contributory, earnings-related social insurance program. It provides basic benefits when a contributor retires or becomes disabled.

### Key Points

- **Mandatory** for most employees and employers in Canada (except Quebec)
- **Employees aged 18-70** must contribute (with some exemptions)
- **Employers must match** employee contributions
- Quebec has its own **Quebec Pension Plan (QPP)** with similar rules

---

## 6.2 CPP Parameters for 2026

| Parameter | Value |
|:----------|:-------|
| **YMPE** (Year's Maximum Pensionable Earnings) | $74,600 |
| **Basic Exemption** | $3,500 |
| **YMCE** (Year's Maximum Contributory Earnings) | $71,100 |
| **Employee Contribution Rate** | 5.95% |
| **Employer Contribution Rate** | 5.95% |
| **Maximum Employee Contribution** | $4,230.45 |
| **Maximum Employer Contribution** | $4,230.45 |
| **YAMPE** (Year's Additional Maximum Pensionable Earnings) | $85,000 |
| **CPP2 Rate** | 4.00% |
| **Maximum CPP2 Contribution** | $416.00 |

---

## 6.3 Who Must Contribute?

### Employees Who Must Contribute

| Category | Age | Employment Status | Contribution Required |
|:---------|:-----|:------------------|:---------------------|
| **Regular employees** | 18-70 | Full-time, part-time, casual | Yes |
| **Commission employees** | 18-70 | Commission-based | Yes |
| **Seasonal workers** | 18-70 | Seasonal employment | Yes |
| **Directors** | 18-70 | Corporate directors | Yes (unless exempt) |

### Employees Exempt from CPP

| Category | Reason for Exemption |
|:---------|:---------------------|
| **Quebec residents** | Covered by QPP (Quebec Pension Plan) |
| **Employees under 18** | Age exemption |
| **Employees over 70** | Age exemption |
| **Indigenous peoples** | Working on reserve (specific conditions) |
| **Disabled CPP recipients** | Receiving CPP disability benefit |
| **Minimum wage earners** | Earning less than basic exemption per pay period |
| **Elected officials** | Certain provincial/municipal positions |
| **Members of religious orders** | Vow of poverty |

### Self-Employed Persons

Self-employed individuals must contribute **both employee and employer portions**:
- Total contribution rate: **11.9%** (5.95% + 5.95%)
- On earnings between basic exemption and YMPE

---

## 6.4 CPP Contribution Formula

### Basic CPP Contribution

**Formula:**
```
C = (I - BPE) × 0.0595
```

Where:
- **C** = CPP contribution for the pay period
- **I** = Gross remuneration for the pay period
- **BPE** = Basic exemption per pay period
- **0.0595** = CPP contribution rate (5.95%)

**Important:**
- If result is negative, set **C = $0**
- Apply maximum contribution limit ($4,230.45 annually)

### Basic Exemption Calculation

**Basic Exemption Per Pay Period:**
```
BPE = $3,500 ÷ P
```

Where:
- **BPE** = Basic exemption per pay period
- **P** = Number of pay periods in the year

**Rounding Rule:**
- If result has 3+ decimal places, **drop the third digit** (do not round up)

| Pay Frequency | BPE (Rounded) |
|:--------------|:--------------|
| Annual (P=1) | $3,500.00 |
| Semi-annual (P=2) | $1,750.00 |
| Quarterly (P=4) | $875.00 |
| Monthly (P=12) | $291.66 |
| Semi-monthly (P=24) | $145.83 |
| Bi-weekly (P=26) | $134.61 |
| Weekly (P=52) | $67.30 |
| Daily (P=260) | $13.46 |

---

## 6.5 CPP Contribution Examples

### Example 1: Monthly Pay

**Scenario:**
- Monthly pay (P = 12)
- Gross salary: $4,500 per month

**Calculation:**
```
BPE = $3,500 ÷ 12 = $291.666... → $291.66 (drop 3rd digit)

C = ($4,500 - $291.66) × 0.0595
C = $4,208.34 × 0.0595
C = $250.40 (rounded to 2 decimal places)
```

**Monthly CPP Contribution = $250.40**

### Example 2: Bi-weekly Pay

**Scenario:**
- Bi-weekly pay (P = 26)
- Gross salary: $2,000 per period

**Calculation:**
```
BPE = $3,500 ÷ 26 = $134.615... → $134.61 (drop 3rd digit)

C = ($2,000 - $134.61) × 0.0595
C = $1,865.39 × 0.0595
C = $110.99 (rounded to 2 decimal places)
```

**Bi-weekly CPP Contribution = $110.99**

### Example 3: Below Basic Exemption

**Scenario:**
- Weekly pay (P = 52)
- Gross salary: $50 per period

**Calculation:**
```
BPE = $3,500 ÷ 52 = $67.307... → $67.30 (drop 3rd digit)

C = ($50 - $67.30) × 0.0595
C = -$17.30 × 0.0595
C = -$1.03
```

Since negative: **C = $0**

**No CPP contribution required**

---

## 6.6 Maximum Contributions

### Tracking Year-to-Date (YTD) CPP

**Formula:**
```
If (YTD_C + C) > Max_CPP:
    C = Max_CPP - YTD_C
    If C < 0:
        C = $0
```

Where:
- **YTD_C** = Year-to-date CPP contributions
- **C** = Current period CPP contribution
- **Max_CPP** = Maximum annual contribution ($4,230.45)

### Example: Reaching Maximum

**Scenario:**
- Monthly pay (P = 12)
- Employee has contributed $4,000 YTD
- Current month's CPP calculation: $300

**Calculation:**
```
If ($4,000 + $300) > $4,230.45:
    C = $4,230.45 - $4,000
    C = $230.45
```

**Current month's CPP = $230.45**
**Future months: C = $0** (maximum reached)

---

## 6.7 CPP2 (Additional CPP) Contributions

### Overview

As of 2026, employees must contribute additional CPP (CPP2) on earnings **above the YMPE** but below the **YAMPE**.

### CPP2 Parameters

| Parameter | Value |
|:----------|:-------|
| **YAMPE** (Year's Additional Maximum Pensionable Earnings) | $85,000 |
| **CPP2 Rate** | 4.00% |
| **Maximum CPP2 Contribution** | $416.00 |
| **CPP2 Earnings Range** | $74,601 to $85,000 |

### CPP2 Contribution Formula

**Formula:**
```
C2 = (YTD_Earnings - YMPE) × 0.04
```

**Where:**
- **C2** = CPP2 contribution for the pay period
- **YTD_Earnings** = Year-to-date gross earnings
- **YMPE** = Year's Maximum Pensionable Earnings ($74,600)
- **0.04** = CPP2 contribution rate (4%)

**Constraints:**
- Only applies if **YTD_Earnings > YMPE**
- Maximum per year: **$416.00**
- Employer must match employee contributions

### CPP2 Contribution Example

**Scenario:**
- Bi-weekly pay (P = 26)
- YTD earnings (before this period): $74,000
- Current period gross: $2,000

**Calculation:**
```
New YTD_Earnings = $74,000 + $2,000 = $76,000

Since $76,000 > $74,600 (YMPE):
    C2 = ($76,000 - $74,600) × 0.04
    C2 = $1,400 × 0.04
    C2 = $56.00
```

**CPP2 Contribution = $56.00**

### CPP2 Maximum Tracking

**Formula:**
```
If (YTD_C2 + C2) > Max_CPP2:
    C2 = Max_CPP2 - YTD_C2
    If C2 < 0:
        C2 = $0
```

**Example:**
- YTD CPP2 contributions: $400
- Maximum: $416
- Current period calculation: $50

```
C2 = $416 - $400 = $16
```

**Current CPP2 = $16.00**
**Future periods: C2 = $0** (maximum reached)

---

## 6.8 CPP for Quebec Residents

### Quebec Pension Plan (QPP)

Quebec residents contribute to the **Quebec Pension Plan (QPP)** instead of CPP.

### QPP Parameters for 2026

| Parameter | QPP | CPP |
|:----------|:-----|:-----|
| **YMPE** | $74,600 | $74,600 |
| **Basic Exemption** | $3,500 | $3,500 |
| **YMCE** | $71,100 | $71,100 |
| **Employee Rate** | 6.30% | 5.95% |
| **Max Employee Contribution** | $4,479.30 | $4,230.45 |
| **YAMPE** | $85,000 | $85,000 |
| **QPP2 Rate** | 4.00% | 4.00% |
| **Max QPP2** | $416.00 | $416.00 |

### QPP Contribution Formula

```
C_QPP = (I - BPE) × 0.0630
```

Where:
- **C_QPP** = QPP contribution for the pay period
- **I** = Gross remuneration
- **BPE** = Basic exemption per pay period
- **0.0630** = QPP contribution rate (6.30%)

---

## 6.9 CPP Tax Credit

### Federal Tax Credit for CPP Contributions

Employees receive a federal tax credit for CPP contributions:

**Formula:**
```
K2_CPP = 0.14 × (P × C × (0.0495/0.0595))
```

Where:
- **K2_CPP** = CPP tax credit
- **0.14** = Federal tax credit rate
- **P** = Number of pay periods in the year
- **C** = CPP contributions for the pay period
- **0.0495/0.0595** = Ratio of employee-only to total contribution

**Maximum K2_CPP:**
```
K2_CPP_max = 0.14 × $3,519.45 × (PM/12)
```

Where **PM** = Number of months in the year (usually 12)

### Example

**Scenario:**
- Monthly pay (P = 12)
- Monthly CPP contribution: $250.40

**Calculation:**
```
K2_CPP = 0.14 × (12 × $250.40 × (0.0495/0.0595))
K2_CPP = 0.14 × ($3,004.80 × 0.8319)
K2_CPP = 0.14 × $2,500.00
K2_CPP = $350.00
```

**Annual CPP Tax Credit = $350.00**

---

## 6.10 CPP Reporting

### T4 Slip Reporting

On the T4 slip, report CPP contributions in:
- **Box 16**: Employee's CPP contributions
- **Box 17**: Employer's CPP contributions (should equal Box 16)

### T4 Summary

Report total CPP contributions for all employees:
- **Code 76**: Total employee CPP contributions
- **Code 77**: Total employer CPP contributions

---

## 6.11 Special Situations

### Employees Turning 18

When an employee turns 18:
- Start deducting CPP in the **first pay period after** their 18th birthday
- No CPP contributions before age 18

### Employees Turning 70

When an employee turns 70:
- Stop deducting CPP in the **first pay period after** the month they turn 70
- Example: Birthday in March, stop in April

### Employees Receiving CPP Disability

- Stop deducting CPP when employee starts receiving CPP disability benefits
- Employee must provide proof of disability benefits

### New Employees Starting Mid-Year

- Calculate CPP based on **remaining pay periods** in the year
- Maximum contribution is **not prorated** (still $4,230.45)
- Track YTD contributions to apply maximum correctly

---

## 6.12 Complete Calculation Example

### Scenario

- Employee: Ontario resident
- Start date: January 1, 2026
- Annual salary: $90,000
- Pay frequency: Monthly (P = 12)
- Monthly gross: $7,500

### Monthly CPP Calculation

**Step 1: Calculate Basic Exemption**
```
BPE = $3,500 ÷ 12 = $291.666... → $291.66
```

**Step 2: Calculate Monthly CPP**
```
C = ($7,500 - $291.66) × 0.0595
C = $7,208.34 × 0.0595
C = $428.90
```

**Step 3: Calculate Annual CPP**
```
Annual CPP = $428.90 × 12 = $5,146.80
```

**Step 4: Apply Maximum**
```
Maximum CPP = $4,230.45
Since $5,146.80 > $4,230.45:
    Actual CPP = $4,230.45
```

**Step 5: When to Stop Deducting**
```
Months until maximum reached:
$4,230.45 ÷ $428.90 = 9.86 months
```

**Result:**
- Deduct CPP for **9 full months** (January to September)
- **October**: Final CPP deduction
- **November and December**: **No CPP deduction**

---

*Continue to [Chapter 7 - Employment Insurance](./chapter-07-ei.md)*
