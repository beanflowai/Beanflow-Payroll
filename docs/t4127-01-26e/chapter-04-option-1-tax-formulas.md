# Chapter 4 – Option 1 – Tax Formulas

> Payroll Deductions Formulas - 122nd Edition
> Effective January 1, 2026

---

## 4.1 Overview

**Option 1** is the standard method for calculating income tax deductions for regular payroll. This method calculates tax based on the current pay period's income, annualized to determine the appropriate tax rate and bracket.

### When to Use Option 1

- Regular payroll with consistent pay periods
- Salaried employees with predictable income
- Hourly employees with regular hours
- Most standard employment situations

### When to Use Option 2 Instead

Use **Option 2 (Cumulative Averaging)** for:
- Commission-based income
- Irregular pay periods
- Variable income amounts
- When more accurate tax withholding is needed

---

## 4.2 Step 1 – Calculate Annual Taxable Income (A)

### 4.2.1 Regular Pay (Salary and Hourly)

For employees paid a regular salary or hourly wage:

```
A = [P × (I - F - F2 - F5A - U1)] - HD - F1
```

Where:
- **A** = Annual taxable income
- **P** = Number of pay periods in the year
- **I** = Gross remuneration for the pay period
- **F** = RPP/RRSP/PRPP/RCA contributions for the pay period
- **F2** = RPP/RRSP/PRPP/RCA deductions from bonuses or retroactive pay
- **F5A** = Annual alimony or maintenance payments
- **U1** = Annual value of board and lodging benefits (for prescribed zones)
- **HD** = Annual value of housing and board benefits (for prescribed zones)
- **F1** = Union dues for the year

#### Example Calculation

**Scenario:**
- Bi-weekly pay (P = 26)
- Gross pay per period (I) = $2,000
- RSP contribution per period (F) = $100
- Union dues annual (F1) = $500
- No other deductions

**Calculation:**
```
A = [26 × ($2,000 - $100)] - $500
A = [26 × $1,900] - $500
A = $49,400 - $500
A = $48,900
```

**Annual Taxable Income (A) = $48,900**

---

### 4.2.2 Commission Only

For employees paid solely on commission:

```
A = I1 - F* - F2* - F5A - U1* - HD - F1 - E
```

Where:
- **A** = Annual taxable income
- **I1** = Annual gross commission income
- **F*** = Annual RPP/RRSP/PRPP/RCA contributions
- **F2*** = Annual RPP/RRSP/PRPP/RCA deductions from bonuses or retroactive pay
- **F5A** = Annual alimony or maintenance payments
- **U1*** = Annual value of board and lodging benefits (for prescribed zones, commission)
- **HD** = Annual value of housing and board benefits (for prescribed zones)
- **F1** = Union dues for the year
- **E** = Allowable deductions for commission income (expenses)

#### Example Calculation

**Scenario:**
- Annual commission income (I1) = $75,000
- Annual RSP contribution (F*) = $5,000
- Business expenses (E) = $8,000
- Union dues (F1) = $500

**Calculation:**
```
A = $75,000 - $5,000 - $8,000 - $500
A = $61,500
```

**Annual Taxable Income (A) = $61,500**

---

## 4.3 Step 2 – Calculate Basic Federal Tax (T3)

### 4.3.1 Basic Federal Tax Formula

```
T3 = (R × A) - K - K1 - K2* - K3 - K4
```

Where:
- **T3** = Annual basic federal tax
- **R** = Federal tax rate (based on tax bracket)
- **A** = Annual taxable income (from Step 1)
- **K** = Federal constant (tax overcharge adjustment)
- **K1** = Federal non-refundable personal tax credit
- **K2*** = CPP and EI federal tax credits
- **K3** = Canada Employment Amount credit
- **K4** = Other federal tax credits

**Important:** If T3 is negative, set T3 = $0

---

### 4.3.2 Federal Tax Rates and Brackets (2026)

| Bracket | Income Range (A) | Rate (R) | Constant (K) |
|:-------|:-----------------|:---------|:-------------|
| **1st** | $0 to $58,523 | 0.1400 | $0 |
| **2nd** | $58,523 to $117,045 | 0.2050 | $3,804 |
| **3rd** | $117,045 to $181,440 | 0.2600 | $10,241 |
| **4th** | $181,440 to $258,482 | 0.2900 | $15,685 |
| **5th** | Over $258,482 | 0.3300 | $26,024 |

---

### 4.3.3 Federal Tax Credits

#### K1 – Basic Personal Credit

```
K1 = 0.14 × TC
```

Where:
- **TC** = Total federal claim amount (from TD1 form)

**Maximum K1** (using 2026 BPAF):
```
K1_max = 0.14 × $16,452 = $2,303.28
```

#### K2 – CPP and EI Credits

```
K2 = K2_CPP + K2_EI
```

**CPP Credit:**
```
K2_CPP = 0.14 × (P × C × (0.0495/0.0595))
Maximum K2_CPP = 0.14 × $3,519.45 × (PM/12)
```

Where:
- **P** = Number of pay periods in the year
- **C** = CPP contributions for the pay period
- **PM** = Number of months in the year (usually 12)

**EI Credit:**
```
K2_EI = 0.14 × (P × EI)
Maximum K2_EI = 0.14 × $1,123.07
```

Where:
- **EI** = EI premiums for the pay period

#### K3 – Canada Employment Amount Credit

```
K3 = 0.14 × Lesser of (A) or (CEA)
```

Where:
- **A** = Annual taxable income
- **CEA** = Canada Employment Amount ($1,433 for 2026)

**Example:**
- If A = $75,000 (greater than CEA):
```
K3 = 0.14 × $1,433 = $200.62
```

- If A = $1,000 (less than CEA):
```
K3 = 0.14 × $1,000 = $140.00
```

#### K4 – Other Federal Tax Credits

```
K4 = Lesser of (0.14 × A*) or (0.14 × CEA)
```

---

### 4.3.4 Example T3 Calculation

**Scenario:**
- Annual taxable income (A) = $75,000
- Total federal claim (TC) = $16,452 (basic personal only)
- Bi-weekly pay (P = 26)
- CPP contribution per period (C) = $84.70
- EI premium per period (EI) = $32.60
- Months employed (PM) = 12

**Step 1: Determine Tax Bracket**
- A = $75,000 falls in 2nd bracket ($58,523 to $117,045)
- R = 0.2050
- K = $3,804

**Step 2: Calculate Tax Credits**

**K1 (Basic Personal):**
```
K1 = 0.14 × $16,452 = $2,303.28
```

**K2_CPP (CPP Credit):**
```
K2_CPP = 0.14 × (26 × $84.70 × (0.0495/0.0595))
K2_CPP = 0.14 × (26 × $84.70 × 0.8319)
K2_CPP = 0.14 × $1,830.62
K2_CPP = $256.29
```

**K2_EI (EI Credit):**
```
K2_EI = 0.14 × (26 × $32.60)
K2_EI = 0.14 × $847.60
K2_EI = $118.66
```

**K2 Total:**
```
K2 = $256.29 + $118.66 = $374.95
```

**K3 (CEA):**
```
K3 = 0.14 × $1,433 = $200.62
```

**Step 3: Calculate T3**
```
T3 = (0.2050 × $75,000) - $3,804 - $2,303.28 - $374.95 - $200.62
T3 = $15,375 - $3,804 - $2,303.28 - $374.95 - $200.62
T3 = $15,375 - $6,682.85
T3 = $8,692.15
```

**Annual Basic Federal Tax (T3) = $8,692.15**

---

## 4.4 Step 3 – Calculate Annual Federal Tax Payable (T1)

### 4.4.1 Standard Formula (Outside Quebec)

```
T1 = T3 - (P × LCF)
```

Where:
- **T1** = Annual federal tax payable
- **T3** = Annual basic federal tax (from Step 2)
- **P** = Number of pay periods in the year
- **LCF** = Labour-sponsored funds tax credit per pay period

**If no LCF:**
```
T1 = T3
```

---

### 4.4.2 Quebec Residents

For Quebec residents, the federal tax is reduced by the **abattement** (16.5%):

```
T1 = [(T3 - (P × LCF)) - (0.165 × T3)]
T1 = (T3 × 0.835) - (P × LCF)
```

**Example (Quebec Resident):**
```
T3 = $8,692.15
LCF = $0

T1 = [($8,692.15 - $0) - (0.165 × $8,692.15)]
T1 = $8,692.15 - $1,434.20
T1 = $7,257.95
```

**Annual Federal Tax Payable (T1) = $7,257.95**

---

## 4.5 Step 4 – Calculate Provincial or Territorial Tax

### 4.5.1 Basic Provincial/Territorial Tax (T4)

```
T4 = (PR × A) - KP - KP1 - KP2 - KP3
```

Where:
- **T4** = Annual basic provincial/territorial tax
- **PR** = Provincial/territorial tax rate
- **A** = Annual taxable income
- **KP** = Provincial constant
- **KP1** = Provincial basic personal credit
- **KP2** = Other provincial tax credits
- **KP3** = Additional provincial credits

**If T4 is negative, set T4 = $0**

---

### 4.5.2 Provincial Tax Rates and Brackets (2026)

#### Ontario

| Bracket | Income Range (A) | Rate (PR) | Constant (KP) |
|:-------|:-----------------|:----------|:--------------|
| **1st** | $0 to $53,891 | 0.0505 | $0 |
| **2nd** | $53,891 to $107,785 | 0.0915 | $2,210 |
| **3rd** | $107,785 to $150,000 | 0.1116 | $4,376 |
| **4th** | $150,000 to $220,000 | 0.1216 | $5,876 |
| **5th** | Over $220,000 | 0.1316 | $8,076 |

#### British Columbia

| Bracket | Income Range (A) | Rate (PR) | Constant (KP) |
|:-------|:-----------------|:----------|:--------------|
| **1st** | $0 to $47,937 | 0.0506 | $0 |
| **2nd** | $47,937 to $95,875 | 0.0770 | $1,278 |
| **3rd** | $95,875 to $110,076 | 0.1050 | $3,964 |
| **4th** | $110,076 to $133,664 | 0.1229 | $5,934 |
| **5th** | $133,664 to $181,882 | 0.1470 | $9,298 |
| **6th** | $181,882 to $259,244 | 0.1680 | $13,111 |
| **7th** | Over $259,244 | 0.2050 | $22,713 |

#### Alberta

| Bracket | Income Range (A) | Rate (PR) | Constant (KP) |
|:-------|:-----------------|:----------|:--------------|
| **1st** | $0 to $148,269 | 0.1000 | $0 |
| **2nd** | $148,269 to $177,922 | 0.1200 | $2,965 |
| **3rd** | $177,922 to $237,230 | 0.1300 | $4,744 |
| **4th** | $237,230 to $355,845 | 0.1400 | $7,117 |
| **5th** | Over $355,845 | 0.1500 | $10,676 |

*See Chapter 8 for complete provincial/territorial tax tables*

---

### 4.5.3 Example T4 Calculation (Ontario)

**Scenario:**
- Annual taxable income (A) = $75,000
- Total Ontario claim (TC) = $12,989 (basic personal only)

**Step 1: Determine Tax Bracket**
- A = $75,000 falls in 2nd bracket ($53,891 to $107,785)
- PR = 0.0915
- KP = $2,210

**Step 2: Calculate Provincial Credits**

**KP1 (Basic Personal):**
```
KP1 = 0.05 × $12,989 = $619.90
```

**Step 3: Calculate T4**
```
T4 = (0.0915 × $75,000) - $2,210 - $619.90
T4 = $6,862.50 - $2,210 - $619.90
T4 = $4,032.60
```

**Annual Basic Ontario Tax (T4) = $4,032.60**

---

## 4.6 Step 5 – Calculate Annual Provincial Tax Payable (T2)

### 4.6.1 Standard Formula

```
T2 = T4 - (Provincial tax credits)
```

**Example (Ontario):**
```
T2 = $4,032.60 - $0 (no additional credits)
T2 = $4,032.60
```

**Annual Ontario Tax Payable (T2) = $4,032.60**

---

## 4.7 Step 6 – Calculate Pay Period Tax Deduction (T)

### 4.7.1 Standard Formula

```
T = [(T1 + T2) / P] + L
```

Where:
- **T** = Total tax deduction for the pay period
- **T1** = Annual federal tax payable
- **T2** = Annual provincial/territorial tax payable
- **P** = Number of pay periods in the year
- **L** = Other deductions for the pay period

### 4.7.2 Example Calculation

**Scenario:**
- Annual federal tax payable (T1) = $8,692.15
- Annual Ontario tax payable (T2) = $4,032.60
- Bi-weekly pay (P = 26)
- Other deductions (L) = $0

**Calculation:**
```
T = [($8,692.15 + $4,032.60) / 26] + $0
T = [$12,724.75 / 26]
T = $489.41
```

**Pay Period Tax Deduction (T) = $489.41**

---

## 4.8 Complete Calculation Example

### Scenario
- Employee: Ontario resident
- Pay frequency: Bi-weekly (P = 26)
- Gross pay per period: $2,500
- RSP contribution per period: $150
- Union dues (annual): $600

### Step-by-Step Calculation

**Step 1: Annual Taxable Income (A)**
```
A = [26 × ($2,500 - $150)] - $600
A = [26 × $2,350] - $600
A = $61,100 - $600
A = $60,500
```

**Step 2: Federal Tax**
- Bracket: 2nd ($58,523 to $117,045)
- R = 0.2050, K = $3,804

```
T3 = (0.2050 × $60,500) - $3,804 - $2,303.28 - $374.95 - $200.62
T3 = $12,402.50 - $6,682.85
T3 = $5,719.65

T1 = $5,719.65
```

**Step 3: Ontario Tax**
- Bracket: 2nd ($53,891 to $107,785)
- PR = 0.0915, KP = $2,210

```
T4 = (0.0915 × $60,500) - $2,210 - $619.90
T4 = $5,535.75 - $2,829.90
T4 = $2,705.85

T2 = $2,705.85
```

**Step 4: Pay Period Tax**
```
T = [($5,719.65 + $2,705.85) / 26]
T = [$8,425.50 / 26]
T = $324.06
```

### Final Results

| Deduction | Annual | Per Pay Period |
|:----------|:-------|:---------------|
| Federal Tax (T1) | $5,719.65 | $219.99 |
| Ontario Tax (T2) | $2,705.85 | $104.07 |
| **Total Tax (T)** | **$8,425.50** | **$324.06** |

---

*Continue to [Chapter 5 - Option 2 Cumulative Averaging](./chapter-05-option-2-cumulative-averaging.md)*
