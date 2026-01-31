# Chapter 2 – Personal Tax Credits Returns (Form TD1)

> Payroll Deductions Formulas - 122nd Edition
> Effective January 1, 2026

---

## 2.1 Overview

Form TD1, **Personal Tax Credits Return**, is used to determine the employee's total claim amount for federal and provincial/territorial tax purposes.

**Key Points:**
- Employees must complete a federal TD1 form
- Employees may also need to complete a provincial/territorial TD1 form
- If a current year TD1 has not been provided, update at the beginning of each year
- Two methods for updating: **Indexing** or **Claim Codes**

---

## 2.2 Form TD1 Components

### Federal TD1 Form

The federal TD1 form includes the following personal tax credits:

| Credit Code | Credit Type | 2026 Basic Amount |
|:------------|:------------|:------------------|
| **1** | Basic Personal Amount | $16,452* |
| **2** | Spousal Amount | $16,452* |
| **3** | Amount for Eligible Dependent | $16,452* |
| **4** | Age Amount (65+) | $8,221 |
| **5** | Pension Income Amount | $2,204 |
| **6** | CPP/QPP Contributions | See calculation |
| **7** | EI Premiums | See calculation |
| **8** | Canada Employment Amount | $1,433 |
| **9** | Disability Amount | $9,418 |
| **10** | Education Amount | $5,000 (full-time) / $2,500 (part-time) |
| **11** | Tuition Fees | Actual amount |
| **12** | Medical Expenses | Actual amount |
| **13** | Caregiver Amount | Various |

*Subject to income phase-out rules

### Provincial/Territorial TD1 Forms

Each province and territory has its own TD1 form with province-specific credits.

---

## 2.3 Total Claim Amounts

### Total Federal Claim (TC)

The Total Federal Claim (TC) is the sum of all federal personal tax credits claimed on the TD1 form.

```
TC = Sum of all federal credit amounts claimed
```

### Total Provincial/Territorial Claim (TCP)

The Total Provincial/Territorial Claim (TCP) is the sum of all provincial/territorial personal tax credits claimed.

```
TCP = Sum of all provincial/territorial credit amounts claimed
```

---

## 2.4 Updating TD1 Claims

When a current year TD1 has not been provided, update at the beginning of each year using one of two methods:

### Option 1 – Indexing of Personal Amounts

This method adjusts the claim amount for inflation using the indexing factor.

#### Calculation Steps

| Step | Description | Formula |
|:-----|:------------|:--------|
| **1** | Enter the total claim amount reported on Form TD1 | **TC_prev** |
| **2** | Minus: Non-indexed amounts (pension income, tuition, education) | **Non-indexed** |
| **3** | Amount subject to annual indexing | **(1) - (2)** |
| **4** | Enter the indexing factor | **IF** |
| **5** | Multiply (3) by (4) (rounded to nearest dollar) | **(3) × IF** |
| **6** | Enter non-indexed amounts (from step 2) | **Non-indexed** |
| **7** | Revised TC or TCP = (5) + (6) | **TC_new** |

#### 2026 Indexing Factors

| Jurisdiction | Indexing Factor (IF) |
|:-------------|:---------------------|
| Federal | 1.027 |
| Alberta | 1.020 |
| British Columbia | 1.040 |
| Manitoba | **No indexing** |
| New Brunswick | 1.031 |
| Newfoundland and Labrador | 1.020 |
| Northwest Territories | 1.024 |
| Nova Scotia | 1.030 |
| Nunavut | 1.024 |
| Ontario | 1.030 |
| Prince Edward Island | 1.024 |
| Saskatchewan | 1.022 |
| Yukon | 1.030 |

#### Non-Indexed Amounts

The following amounts are **NOT indexed**:
- Pension income amount
- Tuition fees
- Education amount
- Medical expenses
- Disability amount
- Caregiver amount

#### Example Calculation

**Scenario:**
- Previous year TC: $25,000
- Non-indexed amounts (tuition): $5,000
- Federal indexing factor: 1.027

**Calculation:**
```
1. TC_prev = $25,000
2. Non-indexed = $5,000
3. Indexed base = $25,000 - $5,000 = $20,000
4. IF = 1.027
5. Indexed amount = $20,000 × 1.027 = $20,540 (rounded)
6. Non-indexed = $5,000
7. TC_new = $20,540 + $5,000 = $25,540
```

**Revised TC = $25,540**

---

### Option 2 – Claim Codes

This method uses pre-calculated claim codes based on the total claim amount.

#### Federal Claim Codes (2026)

| Claim Code | Total Claim Amount Range |
|:-----------|:-------------------------|
| **0** | No claim amount |
| **1** | $0 to $12,935.00 |
| **2** | $12,935.01 to $16,452.00 |
| **3** | $16,452.01 to $20,357.00 |
| **4** | $20,357.01 to $24,262.00 |
| **5** | $24,262.01 to $28,167.00 |
| **6** | $28,167.01 to $32,072.00 |
| **7** | $32,072.01 to $35,977.00 |
| **8** | $35,977.01 to $39,882.00 |
| **9** | $39,882.01 to $43,787.00 |
| **10** | $43,787.01 and over |

#### Using Claim Codes in Calculations

When using claim codes:
1. Look up the corresponding claim amount for the employee's claim code
2. Use this amount as **TC** in tax calculations
3. Claim codes simplify payroll processing by avoiding individual calculations

---

## 2.5 Basic Personal Amount Formulas

### Federal Basic Personal Amount (BPAF) - 2026

The Federal Basic Personal Amount is subject to a phase-out based on net income.

#### Formula

| Net Income (NI*) | BPAF Amount |
|:-----------------|:------------|
| NI* ≤ $181,440 | **$16,452** |
| $181,440 < NI* < $258,482 | $16,452 - [(NI* - $181,440) × ($1,623 / $77,042)] |
| NI* ≥ $258,482 | **$14,829** |

*(NI* = A + HD, where A = Annual taxable income, HD = Annual value of housing and board benefits)*

#### Example Calculations

**Example 1:**
- Net Income (NI*) = $150,000
- Since $150,000 ≤ $181,440: **BPAF = $16,452**

**Example 2:**
- Net Income (NI*) = $200,000
- Since $181,440 < $200,000 < $258,482:
```
BPAF = $16,452 - [(($200,000 - $181,440) × $1,623) / $77,042]
BPAF = $16,452 - [($18,560 × $1,623) / $77,042]
BPAF = $16,452 - $391
BPAF = $16,061
```

**Example 3:**
- Net Income (NI*) = $300,000
- Since $300,000 ≥ $258,482: **BPAF = $14,829**

---

### Manitoba Basic Personal Amount (BPAMB) - 2026

**Important:** Manitoba does not index the Basic Personal Amount for 2025 and subsequent years.

#### Formula

| Net Income (NI*) | BPAMB Amount |
|:-----------------|:-------------|
| NI* ≤ $200,000 | **$15,780** |
| $200,000 < NI* < $400,000 | $15,780 - [(NI* - $200,000) × ($15,780 / $200,000)] |
| NI* ≥ $400,000 | **$0** |

#### Example Calculations

**Example 1:**
- Net Income (NI*) = $150,000
- Since $150,000 ≤ $200,000: **BPAMB = $15,780**

**Example 2:**
- Net Income (NI*) = $250,000
- Since $200,000 < $250,000 < $400,000:
```
BPAMB = $15,780 - [(($250,000 - $200,000) × $15,780) / $200,000]
BPAMB = $15,780 - [($50,000 × $15,780) / $200,000]
BPAMB = $15,780 - $3,945
BPAMB = $11,835
```

**Example 3:**
- Net Income (NI*) = $500,000
- Since $500,000 ≥ $400,000: **BPAMB = $0**

---

### Ontario Basic Personal Amount (BPAON) - 2026

#### Formula

| Net Income (NI) | BPAON Amount |
|:---------------|:-------------|
| NI ≤ $247,882 | **$12,989** |
| NI > $247,882 | $12,989 - [(NI - $247,882) × ($12,989 / $250,000)] |

#### Example Calculations

**Example 1:**
- Net Income (NI) = $200,000
- Since $200,000 ≤ $247,882: **BPAON = $12,989**

**Example 2:**
- Net Income (NI) = $300,000
- Since $300,000 > $247,882:
```
BPAON = $12,989 - [(($300,000 - $247,882) × $12,989) / $250,000]
BPAON = $12,989 - [($52,118 × $12,989) / $250,000]
BPAON = $12,989 - $2,585
BPAON = $9,813
```

---

### Nova Scotia Basic Personal Amount (BPANS) - 2026

**Important:** For 2026, the BPANS formula should be removed for all employees as it is now set at the maximum regardless of taxable income.

#### Fixed Amount
```
BPANS = $11,932 (for all employees)
```

---

## 2.6 Other Personal Tax Credits

### Canada Employment Amount (CEA) - 2026

| Jurisdiction | Amount | Income Limit |
|:-------------|:-------|:-------------|
| Federal | $1,433 | Phase-out starts at: |
|  |  | Alberta: $50,000 |
|  |  | British Columbia: $50,000 |
|  |  | Manitoba: No phase-out |
|  |  | Ontario: $50,000 |
|  |  | Saskatchewan: No phase-out |

#### Federal CEA Formula

```
CEA = $1,433 - [(Employment Income - $50,000) × 0.03]
Minimum CEA = $0
```

**Example:**
- Employment Income = $75,000
```
CEA = $1,433 - [(($75,000 - $50,000) × 0.03]
CEA = $1,433 - $750
CEA = $683
```

---

### Age Amount

For employees aged 65 or older on December 31 of the taxation year.

| Jurisdiction | Amount | Income Threshold |
|:-------------|:-------|:-----------------|
| Federal | $8,221 | Phase-out starts at $40,725 |
|  |  | Fully phased out at $95,259 |

#### Federal Age Amount Formula

```
If Net Income ≤ $40,725:
    Age Amount = $8,221
If $40,725 < Net Income < $95,259:
    Age Amount = $8,221 - [(Net Income - $40,725) × 0.15]
If Net Income ≥ $95,259:
    Age Amount = $0
```

---

### Pension Income Amount

For recipients of pension, superannuation, or annuity payments.

| Jurisdiction | Maximum Amount |
|:-------------|:---------------|
| Federal | $2,204 |

#### Eligible Pension Income

- Life annuity payments from a pension plan
- Superannuation payments
- RRSP annuity payments
- RRIF payments (after age 65)

---

## 2.7 CPP and EI Tax Credits

Employees receive tax credits for CPP and EI contributions.

### CPP Tax Credit (K2_CPP)

```
K2_CPP = 0.14 × (P × C × (0.0495/0.0595))
Maximum K2_CPP = 0.14 × $3,519.45 × (PM/12)
```

Where:
- **P** = Number of pay periods in the year
- **C** = CPP contributions for the pay period
- **PM** = Number of months in the year (usually 12)

### EI Tax Credit (K2_EI)

```
K2_EI = 0.14 × (P × EI)
Maximum K2_EI = 0.14 × $1,123.07
```

Where:
- **EI** = EI premiums for the pay period

---

## 2.8 TD1 Form Processing Rules

### New Employees

1. Employee must complete TD1 forms within **3 days** of starting employment
2. If no TD1 is provided:
   - Assume **no claim amounts** (claim code 0)
   - Deduct tax at maximum rate
3. When TD1 is received, adjust future deductions

### Updating TD1

Employees should submit a new TD1 when:
- Personal circumstances change (marriage, children, etc.)
- They want to change their claim amounts
- They move to a different province/territory

### Multiple Employers

- Employees must complete a TD1 for **each employer**
- Basic personal amount can be claimed in full for each employer
- Other credits may need to be prorated

---

*Continue to [Chapter 3 - Glossary](./chapter-03-glossary.md)*
