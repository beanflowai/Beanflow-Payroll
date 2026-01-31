# Chapter 5 – Option 2 – Tax Formulas Based on Cumulative Averaging

> Payroll Deductions Formulas - 122nd Edition
> Effective January 1, 2026

---

## 5.1 Overview

**Option 2** uses cumulative averaging to calculate income tax deductions. This method tracks year-to-date (YTD) income and deductions to provide more accurate tax withholding, especially for employees with variable income.

### When to Use Option 2

Use **Option 2 (Cumulative Averaging)** for:
- Commission-based income
- Irregular pay periods
- Variable income amounts
- Employees with multiple jobs
- When more accurate tax withholding is needed
- Bonus and retroactive pay calculations

### Advantages of Option 2

- More accurate tax withholding throughout the year
- Reduces year-end tax surprises
- Better handles variable income
- Accounts for YTD contributions automatically

### Disadvantages of Option 2

- More complex calculations
- Requires tracking YTD amounts
- May result in fluctuating deductions

---

## 5.2 Key Concepts

### Year-to-Date (YTD) Tracking

Option 2 requires tracking the following YTD amounts:

| YTD Amount | Description |
|:-----------|:-------------|
| **YTD_I** | Year-to-date gross remuneration |
| **YTD_F** | Year-to-date pension contributions |
| **YTD_F1** | Year-to-date union dues |
| **YTD_T** | Year-to-date tax deductions |
| **YTD_C** | Year-to-date CPP contributions |
| **YTD_EI** | Year-to-date EI premiums |
| **YTD_A** | Year-to-date taxable income |

### Cumulative Method

The cumulative method calculates:
1. **Cumulative taxable income** for the year to date
2. **Cumulative tax** that should have been deducted
3. **Tax already deducted** in previous periods
4. **Current period tax** = Cumulative tax - Tax already deducted

---

## 5.3 Option 2 Formulas

### 5.3.1 Step 1 – Calculate Cumulative Taxable Income

**Cumulative Taxable Income (A_cumulative):**

```
A_cumulative = (YTD_I + I) - (YTD_F + F) - (YTD_F1 + F1) - HD
```

Where:
- **A_cumulative** = Cumulative annual taxable income
- **YTD_I** = Year-to-date gross remuneration (before this period)
- **I** = Gross remuneration for the current pay period
- **YTD_F** = Year-to-date pension contributions (before this period)
- **F** = Pension contributions for the current pay period
- **YTD_F1** = Year-to-date union dues (before this period)
- **F1** = Union dues for the current pay period
- **HD** = Annual value of housing and board benefits

---

### 5.3.2 Step 2 – Calculate Cumulative Tax

**Cumulative Federal Tax (T1_cumulative):**

```
T3_cumulative = (R × A_cumulative) - K - K1 - K2_cumulative - K3 - K4
T1_cumulative = T3_cumulative - (P × LCF)
```

**Where:**
- **T3_cumulative** = Cumulative basic federal tax
- **R** = Federal tax rate (based on cumulative taxable income)
- **A_cumulative** = Cumulative annual taxable income
- **K** = Federal constant
- **K1** = Federal non-refundable personal tax credit
- **K2_cumulative** = CPP and EI credits on cumulative contributions
- **K3** = Canada Employment Amount credit
- **K4** = Other federal tax credits
- **LCF** = Labour-sponsored funds tax credit

---

### 5.3.3 Step 3 – Calculate Current Period Tax

**Current Period Federal Tax (T1_current):**

```
T1_current = T1_cumulative - YTD_T1
```

Where:
- **T1_current** = Federal tax for the current pay period
- **T1_cumulative** = Cumulative federal tax to date
- **YTD_T1** = Federal tax deducted in previous periods

**If T1_current is negative, set T1_current = $0**

---

### 5.3.4 Provincial/Territorial Tax

Similar calculations apply for provincial/territorial tax:

```
T2_current = T2_cumulative - YTD_T2
```

Where:
- **T2_current** = Provincial/territorial tax for the current pay period
- **T2_cumulative** = Cumulative provincial/territorial tax to date
- **YTD_T2** = Provincial/territorial tax deducted in previous periods

---

### 5.3.5 Total Pay Period Tax

```
T = T1_current + T2_current + L
```

Where:
- **T** = Total tax deduction for the pay period
- **T1_current** = Current period federal tax
- **T2_current** = Current period provincial/territorial tax
- **L** = Other deductions for the pay period

---

## 5.4 Calculation Example

### Scenario
- Employee: Ontario resident
- Pay frequency: Bi-weekly (P = 26)
- Commission-based income
- 5 pay periods completed so far

### Pay Period History

| Period | Gross (I) | RSP (F) | YTD_I | YTD_F | YTD_T1 | YTD_T2 |
|:-------|:----------|:--------|:------|:------|:-------|-------|
| 1 | $1,500 | $100 | $1,500 | $100 | $280 | $140 |
| 2 | $3,000 | $200 | $4,500 | $300 | $560 | $280 |
| 3 | $2,000 | $150 | $6,500 | $450 | $840 | $420 |
| 4 | $4,000 | $400 | $10,500 | $850 | $1,120 | $560 |
| 5 | $2,500 | $250 | $13,000 | $1,100 | $1,400 | $700 |

### Current Period (Period 6)
- Gross (I) = $5,000
- RSP (F) = $500

### Step 1: Calculate Cumulative Taxable Income

```
A_cumulative = (YTD_I + I) - (YTD_F + F) - F1 - HD
A_cumulative = ($13,000 + $5,000) - ($1,100 + $500) - $0 - $0
A_cumulative = $18,000 - $1,600
A_cumulative = $16,400
```

**Annualize for bi-weekly:**
```
A_annualized = $16,400 × (26/6)
A_annualized = $16,400 × 4.333
A_annualized = $71,067
```

### Step 2: Calculate Cumulative Federal Tax

**Determine Tax Bracket:**
- A_annualized = $71,067 falls in 2nd bracket ($58,523 to $117,045)
- R = 0.2050
- K = $3,804

**Tax Credits:**
```
K1 = $2,303.28 (basic personal)
K2 = $374.95 (CPP/EI)
K3 = $200.62 (CEA)
```

**Calculate T3_cumulative:**
```
T3_cumulative = (0.2050 × $71,067) - $3,804 - $2,303.28 - $374.95 - $200.62
T3_cumulative = $14,569 - $6,682.85
T3_cumulative = $7,886.15
```

**De-annualize for 6 periods:**
```
T1_cumulative = $7,886.15 / (26/6)
T1_cumulative = $7,886.15 / 4.333
T1_cumulative = $1,819.52
```

### Step 3: Calculate Current Period Tax

```
T1_current = T1_cumulative - YTD_T1
T1_current = $1,819.52 - $1,400
T1_current = $419.52
```

### Step 4: Provincial Tax (Ontario)

**Determine Tax Bracket:**
- A_annualized = $71,067 falls in 2nd bracket ($53,891 to $107,785)
- PR = 0.0915
- KP = $2,210

**Calculate T4_cumulative:**
```
T4_cumulative = (0.0915 × $71,067) - $2,210 - $619.90
T4_cumulative = $6,503 - $2,829.90
T4_cumulative = $3,673.10
```

**De-annualize for 6 periods:**
```
T2_cumulative = $3,673.10 / 4.333
T2_cumulative = $847.51
```

**Current Period:**
```
T2_current = $847.51 - $700
T2_current = $147.51
```

### Step 5: Total Pay Period Tax

```
T = T1_current + T2_current
T = $419.52 + $147.51
T = $567.03
```

### Results Summary

| Tax Type | Cumulative | YTD Deducted | Current Period |
|:---------|:-----------|:-------------|:---------------|
| Federal | $1,819.52 | $1,400.00 | $419.52 |
| Ontario | $847.51 | $700.00 | $147.51 |
| **Total** | **$2,667.03** | **$2,100.00** | **$567.03** |

---

## 5.5 Bonus and Retroactive Pay Calculations

### Method 1 – Bonus Taxed Separately

Calculate tax on bonus alone:

```
T_bonus = [(R_bonus × B) - K_bonus] / P_bonus
```

Where:
- **T_bonus** = Tax on bonus
- **R_bonus** = Marginal tax rate
- **B** = Bonus amount
- **K_bonus** = Applicable credits
- **P_bonus** = Number of bonus periods (usually 1)

### Method 2 – Aggregate Method (Cumulative)

Add bonus to cumulative income:

```
A_cumulative_with_bonus = A_cumulative + B
T_cumulative_with_bonus = Calculate tax on A_cumulative_with_bonus
T_bonus = T_cumulative_with_bonus - T_cumulative_already_paid
```

### Example: Aggregate Bonus Calculation

**Scenario:**
- YTD taxable income (before bonus): $40,000
- YTD tax deducted (before bonus): $5,000
- Bonus amount: $10,000
- Pay periods remaining: 12

**Step 1: Calculate Cumulative with Bonus**
```
A_cumulative_with_bonus = $40,000 + $10,000 = $50,000
```

**Step 2: Calculate Tax on $50,000**
- 2nd bracket: R = 0.2050, K = $3,804

```
T_cumulative_with_bonus = (0.2050 × $50,000) - $3,804 - $2,303.28 - $374.95 - $200.62
T_cumulative_with_bonus = $10,250 - $6,682.85
T_cumulative_with_bonus = $3,567.15
```

**Step 3: Calculate Tax on Bonus**
```
T_bonus = $3,567.15 - $5,000
T_bonus = -$1,432.85
```

Since negative, set to $0:
```
T_bonus = $0
```

**Note:** In this case, no additional tax is needed on the bonus because the employee has already overpaid tax.

---

## 5.6 Multiple Employment Income

### Employees with Multiple Jobs

When an employee has multiple jobs, each employer calculates tax independently:

**Employer 1:**
```
T1 = Calculate tax on income from Employer 1 only
```

**Employer 2:**
```
T2 = Calculate tax on income from Employer 2 only
```

**Result:**
- Total tax deducted may be **less than** actual tax liability
- Employee may owe tax at year-end
- Employee can request additional tax withholding using Form TD1

### Requesting Additional Tax Withholding

Employee can complete section of TD1 to have additional tax deducted:

```
Additional_tax_per_period = Specified amount
T_total = T_calculated + Additional_tax_per_period
```

---

## 5.7 Year-End Adjustments

### Final Pay Period of Year

In the final pay period:
1. Calculate all cumulative amounts for the entire year
2. Compare to actual tax liability
3. Adjust if necessary (though typically minor)

### Reconciliation

At year-end, compare:
- **Total tax deducted** (YTD_T)
- **Actual tax liability** (from T4 slip)

**If under-deducted:**
- Employee owes tax on personal tax return
- No employer penalty (assuming correct calculations)

**If over-deducted:**
- Employee receives refund on personal tax return

---

## 5.8 Comparison: Option 1 vs Option 2

| Feature | Option 1 | Option 2 |
|:--------|:---------|:---------|
| **Calculation Basis** | Current pay only | Cumulative year-to-date |
| **Accuracy** | Good for consistent income | Better for variable income |
| **Complexity** | Simpler | More complex |
| **YTD Tracking** | Not required | Required |
| **Best For** | Regular salaried employees | Commission, irregular pay |
| **Tax Withholding** | May over/under withhold | More accurate |

---

*Continue to [Chapter 6 - Canada Pension Plan](./chapter-06-cpp.md)*
