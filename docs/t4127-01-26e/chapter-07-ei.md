# Chapter 7 – Employment Insurance

> Payroll Deductions Formulas - 122nd Edition
> Effective January 1, 2026

---

## 7.1 Overview

**Employment Insurance (EI)** provides temporary financial assistance to unemployed Canadians while they look for work or upgrade their skills. It also provides special benefits for sickness, maternity, parental, and caregiving leave.

### Key Points

- **Mandatory** for most employees in Canada (with some exemptions)
- **Employees** pay EI premiums (employer portion is 1.4× employee rate)
- **Quebec** has its own system (QPIP) for parental benefits
- Premiums are calculated on **insurable earnings** up to a maximum

---

## 7.2 EI Parameters for 2026

### Canada (except Quebec)

| Parameter | Value |
|:----------|:-------|
| **Max Insurable Earnings (MIE)** | $68,900 |
| **Employee Premium Rate** | 1.63% |
| **Employer Premium Rate** | 2.28% (1.4 × employee rate) |
| **Maximum Employee Premium** | $1,123.07 |
| **Maximum Employer Premium** | $1,572.30 |

### Quebec

| Parameter | Value |
|:----------|:-------|
| **Max Insurable Earnings (MIE)** | $68,900 |
| **Employee Premium Rate** | 1.30% |
| **Employer Premium Rate** | 1.82% (1.4 × employee rate) |
| **Maximum Employee Premium** | $895.70 |
| **Maximum Employer Premium** | $1,253.98 |

**Note:** Quebec residents have lower EI premiums because they pay into the **Quebec Parental Insurance Plan (QPIP)** instead of EI for parental benefits.

---

## 7.3 Who Must Pay EI Premiums?

### Employees Who Must Pay

| Category | Employment Type | EI Required |
|:---------|:---------------|:------------|
| **Full-time employees** | Regular employment | Yes |
| **Part-time employees** | Part-time employment | Yes |
| **Seasonal workers** | Seasonal employment | Yes |
| **Commission employees** | Commission-based | Yes |
| **Casual workers** | Casual employment | Yes |

### Employees Exempt from EI

| Category | Reason for Exemption |
|:---------|:---------------------|
| **Self-employed** | Not employees (unless opting in) |
| **Family members** | Working for spouse/parent's business (closely held) |
| **Indigenous peoples** | Working on reserve (specific conditions) |
| **Elected officials** | Certain political positions |
| **Apprentices** | Some provinces (exemption varies) |
| **Certain religious groups** | Religious objections |
| **Retirement on pension** | Returning to work after retirement |
| **International workers** | Certain work permit categories |
| **Owner-operators** | Working in their own business |
| **Quebec residents** | For parental benefits (pay QPIP instead) |

---

## 7.4 EI Premium Formula

### Employee EI Premium

**Formula:**
```
EI = I × EI_Rate
```

Where:
- **EI** = EI premium for the pay period
- **I** = Gross remuneration for the pay period
- **EI_Rate** = Employee premium rate (1.63% for Canada, 1.30% for Quebec)

**Constraints:**
- Apply maximum annual premium limit
- Only on **insurable earnings** (most employment income is insurable)

### Employer EI Premium

**Formula:**
```
EI_Employer = EI × 1.4
```

Where:
- **EI_Employer** = Employer EI premium for the pay period
- **EI** = Employee EI premium
- **1.4** = Employer multiplier

---

## 7.5 EI Premium Examples

### Example 1: Monthly Pay (Canada)

**Scenario:**
- Monthly pay
- Gross salary: $4,500 per month
- Employee rate: 1.63%

**Calculation:**
```
EI = $4,500 × 0.0163
EI = $73.35
```

**Monthly Employee Premium = $73.35**
**Monthly Employer Premium = $73.35 × 1.4 = $102.69**

### Example 2: Bi-weekly Pay (Canada)

**Scenario:**
- Bi-weekly pay
- Gross salary: $2,000 per period
- Employee rate: 1.63%

**Calculation:**
```
EI = $2,000 × 0.0163
EI = $32.60
```

**Bi-weekly Employee Premium = $32.60**
**Bi-weekly Employer Premium = $32.60 × 1.4 = $45.64**

### Example 3: Monthly Pay (Quebec)

**Scenario:**
- Monthly pay
- Gross salary: $4,500 per month
- Quebec resident
- Employee rate: 1.30%

**Calculation:**
```
EI = $4,500 × 0.0130
EI = $58.50
```

**Monthly Employee Premium = $58.50**
**Monthly Employer Premium = $58.50 × 1.4 = $81.90**

---

## 7.6 Maximum Premiums

### Tracking Year-to-Date (YTD) EI

**Formula:**
```
If (YTD_EI + EI) > Max_EI:
    EI = Max_EI - YTD_EI
    If EI < 0:
        EI = $0
```

Where:
- **YTD_EI** = Year-to-date EI premiums
- **EI** = Current period EI premium
- **Max_EI** = Maximum annual premium ($1,123.07 for Canada, $895.70 for Quebec)

### Example: Reaching Maximum (Canada)

**Scenario:**
- Monthly pay
- Employee has contributed $1,000 YTD
- Current month's EI calculation: $100

**Calculation:**
```
If ($1,000 + $100) > $1,123.07:
    EI = $1,123.07 - $1,000
    EI = $123.07
```

**Current month's EI = $123.07**
**Future months: EI = $0** (maximum reached)

---

## 7.7 Insurable Earnings

### What Are Insurable Earnings?

Most employment income is insurable, including:

| Income Type | Insurable? |
|:------------|:-----------|
| Regular wages/salary | Yes |
| Overtime pay | Yes |
| Bonuses | Yes |
| Commissions | Yes |
| Vacation pay | Yes |
| Tips (controlled) | Yes |
| Tips (direct) | Yes |
| Shift premiums | Yes |
| Hazard pay | Yes |
| Statutory holiday pay | Yes |
| Sick pay (regular) | Yes |

### Non-Insurable Earnings

The following are **NOT insurable**:

| Income Type | Not Insurable |
|:------------|:--------------|
| Pension income | No |
| Retiring allowances | No |
| Severance pay | No |
| Lump-sum death benefits | No |
 | Workers' compensation benefits | No |
| Disability benefits (long-term) | No |
| Salary deferrals (RRSP) | No |
| Stock options | No |
| Director fees | No (unless in employment) |

---

## 7.8 EI Tax Credit

### Federal Tax Credit for EI Premiums

Employees receive a federal tax credit for EI premiums:

**Formula:**
```
K2_EI = 0.14 × (P × EI)
```

Where:
- **K2_EI** = EI tax credit
- **0.14** = Federal tax credit rate
- **P** = Number of pay periods in the year
- **EI** = EI premiums for the pay period

**Maximum K2_EI:**
```
K2_EI_max = 0.14 × Max_EI
```

For Canada:
```
K2_EI_max = 0.14 × $1,123.07 = $157.23
```

For Quebec:
```
K2_EI_max = 0.14 × $895.70 = $125.40
```

### Example

**Scenario:**
- Monthly pay (P = 12)
- Monthly EI premium: $73.35 (Canada)

**Calculation:**
```
K2_EI = 0.14 × (12 × $73.35)
K2_EI = 0.14 × $880.20
K2_EI = $123.23
```

**Annual EI Tax Credit = $123.23**

---

## 7.9 Employer EI Reductions

### Reduced Employer Rate

Some employers qualify for a reduced EI premium rate:

### Eligibility

Employers may qualify if they:
- Have a **wage-loss replacement plan** for short-term disability
- Provide **sick leave benefits** that are at least as generous as EI

### Reduction Amount

For 2026, the maximum reduction is:
- **Maximum reduction**: Up to **$1,243.15** per employee annually

### Calculation

**Standard Employer Premium:**
```
EI_Employer_Standard = EI × 1.4
```

**Reduced Employer Premium:**
```
EI_Employer_Reduced = EI_Employer_Standard - Reduction
```

---

## 7.10 EI for Quebec Residents (QPIP)

### Quebec Parental Insurance Plan

Quebec residents do not pay EI premiums for parental benefits. Instead, they pay into the **Quebec Parental Insurance Plan (QPIP)**.

### QPIP Parameters

| Parameter | Value |
|:----------|:-------|
| **Max Insurable Earnings** | $94,000 |
| **Employee Premium Rate** | 0.494% |
| **Employer Premium Rate** | 0.692% (1.4 × employee rate) |
| **Maximum Employee Premium** | $464.36 |
| **Maximum Employer Premium** | $650.10 |

### Total Premiums for Quebec Residents

**EI Regular (maternity, sickness, etc.):**
```
EI = I × 0.0130
Max = $895.70
```

**QPIP (parental benefits):**
```
QPIP = I × 0.00494
Max = $464.36
```

**Total Employee Premium:**
```
Total = EI + QPIP
Total_Max = $895.70 + $464.36 = $1,360.06
```

---

## 7.11 EI Reporting

### T4 Slip Reporting

On the T4 slip, report EI premiums in:
- **Box 18**: Employee's EI premiums
- **Box 19**: Employer's EI premiums (should be approximately 1.4 × Box 18, or less if reduction applies)

### T4 Summary

Report total EI premiums for all employees:
- **Code 52**: Total employee EI premiums
- **Code 53**: Total employer EI premiums

---

## 7.12 Complete Calculation Example

### Scenario

- Employee: Ontario resident (not Quebec)
- Start date: January 1, 2026
- Annual salary: $75,000
- Pay frequency: Monthly (P = 12)
- Monthly gross: $6,250

### Monthly EI Calculation

**Step 1: Calculate Monthly EI**
```
EI = $6,250 × 0.0163
EI = $101.88
```

**Step 2: Calculate Employer EI**
```
EI_Employer = $101.88 × 1.4
EI_Employer = $142.63
```

**Step 3: Calculate Annual EI**
```
Annual EI_Employee = $101.88 × 12 = $1,222.56
Annual EI_Employer = $142.63 × 12 = $1,711.56
```

**Step 4: Apply Maximum**
```
Maximum Employee EI = $1,123.07
Since $1,222.56 > $1,123.07:
    Actual Employee EI = $1,123.07
```

**Step 5: When to Stop Deducting**
```
Months until maximum reached:
$1,123.07 ÷ $101.88 = 11.02 months
```

**Result:**
- Deduct EI for **11 full months** (January to November)
- **December**: Partial EI deduction
- Total employee EI: $1,123.07
- Total employer EI: $1,123.07 × 1.4 = $1,572.30

---

## 7.13 Special Situations

### New Employees Starting Mid-Year

- Calculate EI based on **remaining pay periods**
- Maximum premium is **not prorated** (still $1,123.07 for Canada)
- Track YTD premiums to apply maximum correctly

### Employees Leaving Mid-Year

- Calculate EI up to last day of work
- Issue ROE (Record of Employment)
- Employee may continue EI benefits if eligible

### Multiple Employers

**Important:** Each employer calculates EI independently:
- EI maximums apply **per employer**
- Employees may pay more than the maximum if working for multiple employers
- Employees cannot request refund for excess EI premiums

### Rehired Employees

- If rehired in same calendar year, continue YTD tracking
- If rehired in new calendar year, start fresh

---

## 7.14 EI Benefits Overview

### Regular Benefits

- **Available to**: Employees who lose their job through no fault of their own
- **Duration**: Based on hours worked and regional unemployment rate
- **Amount**: 55% of average insurable earnings (max cap applies)

### Special Benefits

| Benefit Type | Duration | Amount |
|:-------------|:---------|:-------|
| **Maternity** | Up to 15 weeks | 55% of earnings |
| **Parental (Standard)** | Up to 35 weeks | 55% of earnings |
| **Parental (Extended)** | Up to 61 weeks | 33% of earnings |
| **Sickness** | Up to 15 weeks | 55% of earnings |
| **Compassionate Care** | Up to 26 weeks | 55% of earnings |
| **Parents of Critically Ill Children** | Up to 35 weeks | 55% of earnings |

---

*Continue to [Chapter 8 - Rates and Amounts](./chapter-08-rates-amounts.md)*
