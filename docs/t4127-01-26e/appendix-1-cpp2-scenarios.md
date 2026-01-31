# Appendix 1: Example Scenarios for CPP2 Treatment

> Payroll Deductions Formulas - 122nd Edition
> Effective January 1, 2026

---

## A1.1 Overview

This appendix provides detailed examples of how **CPP2 (Additional CPP)** contributions are calculated in various employment situations. CPP2 contributions apply to earnings between the **YMPE** ($74,600) and **YAMPE** ($85,000).

### CPP2 Key Parameters

| Parameter | Value |
|:----------|:-------|
| **YMPE** (Year's Maximum Pensionable Earnings) | $74,600 |
| **YAMPE** (Year's Additional Maximum Pensionable Earnings) | $85,000 |
| **CPP2 Rate** | 4.00% |
| **Maximum CPP2 Contribution** | $416.00 |
| **CPP2 Earnings Range** | $74,601 to $85,000 ($10,400) |

---

## A1.2 CPP2 Formula

### Basic CPP2 Calculation

```
If YTD_Earnings > YMPE:
    CPP2_Range = Min(YTD_Earnings, YAMPE) - YMPE
    C2 = CPP2_Range × 0.04
    C2_Deduction = C2 - YTD_C2
    If C2_Deduction < 0:
        C2_Deduction = 0
```

Where:
- **YTD_Earnings** = Year-to-date gross earnings (including current period)
- **YMPE** = $74,600 (Year's Maximum Pensionable Earnings)
- **YAMPE** = $85,000 (Year's Additional Maximum Pensionable Earnings)
- **C2** = Total CPP2 contribution for the year to date
- **YTD_C2** = CPP2 contributions deducted in previous periods
- **C2_Deduction** = CPP2 contribution for the current pay period

---

## A1.3 Scenario 1: Single Employer - Regular Income

### Employee Profile

- **Employer:** ABC Company
- **Annual Salary:** $95,000
- **Pay Frequency:** Monthly (P = 12)
- **Start Date:** January 1, 2026

### Monthly Calculation

#### Before Reaching YMPE ($74,600)

**January to September (9 months):**
- Monthly gross: $7,916.67
- YTD earnings after September: $71,250

**October:**
- YTD earnings before October: $71,250
- October gross: $7,916.67
- New YTD earnings: $79,166.67

**Since $79,166.67 > $74,600 (YMPE):**
```
CPP2_Range = Min($79,166.67, $85,000) - $74,600
CPP2_Range = $79,166.67 - $74,600
CPP2_Range = $4,566.67

C2 = $4,566.67 × 0.04
C2 = $182.67
```

**October CPP2 Deduction: $182.67**

#### Continuing CPP2 Deductions

**November:**
- YTD earnings before November: $79,166.67
- November gross: $7,916.67
- New YTD earnings: $87,083.34

**Since $87,083.34 > $85,000 (YAMPE):**
```
CPP2_Range = Min($87,083.34, $85,000) - $74,600
CPP2_Range = $85,000 - $74,600
CPP2_Range = $10,400 (maximum range)

C2 = $10,400 × 0.04
C2 = $416.00 (maximum annual CPP2)

C2_Deduction = $416.00 - $182.67 (previous CPP2)
C2_Deduction = $233.33
```

**November CPP2 Deduction: $233.33**

#### After Reaching Maximum

**December:**
- YTD CPP2 already at maximum ($416.00)
```
C2_Deduction = $0 (maximum reached)
```

**December CPP2 Deduction: $0.00**

### Annual Summary

| Month | YTD Earnings | Monthly CPP | Monthly CPP2 | YTD CPP2 |
|:------|:-------------|:------------|:-------------|:---------|
| Jan-Sep | $71,250 | Various | $0.00 | $0.00 |
| Oct | $79,167 | $451.83 | $182.67 | $182.67 |
| Nov | $87,083 | $451.83 | $233.33 | $416.00 |
| Dec | $95,000 | $451.83 | $0.00 | $416.00 |

**Total 2026:**
- CPP: $4,230.45 (maximum)
- CPP2: $416.00 (maximum)

---

## A1.4 Scenario 2: Multiple Employers

### Employee Profile

- **Employer 1:** Company A (January to June)
- **Employer 2:** Company B (July to December)
- **Combined Annual Income:** $95,000
- **Company A Income:** $45,000
- **Company B Income:** $50,000
- **Pay Frequency:** Monthly

### Company A (January to June)

**YTD Earnings:** $45,000 (below YMPE)

```
CPP = ($45,000 - $1,750) × 0.0595 = $2,579.13
CPP2 = $0 (no earnings above YMPE)
```

### Company B (July to December)

**Monthly Gross:** $8,333.33

**July to November:**
- YTD earnings: $50,000 (below YMPE)
- No CPP2 deductions

**December:**
- YTD earnings for Company B: $50,000
- Total YTD earnings (both employers): $95,000

**Important:** Each employer calculates CPP independently!

**Company B Calculation:**
```
Since $50,000 < $74,600 (YMPE):
    CPP2 = $0
```

### Employee's Total CPP Contributions

| Employer | Annual Income | CPP Contribution | CPP2 Contribution |
|:---------|:--------------|:-----------------|:------------------|
| **Company A** | $45,000 | $2,579.13 | $0.00 |
| **Company B** | $50,000 | $2,852.58 | $0.00 |
| **Total** | $95,000 | $5,431.71 | $0.00 |

**Result:** Employee contributes **more than the maximum** because each employer applies maximum independently.

### Employee's Right to Refund

Employees can request a CPP refund at year-end if total contributions exceed maximums:
- Maximum CPP + CPP2: $4,230.45 + $416.00 = $4,646.45
- Actual paid: $5,431.71
- **Refund request:** $5,431.71 - $4,646.45 = **$785.26**

---

## A1.5 Scenario 3: Mid-Year Employment Change

### Employee Profile

- **Employer:** XYZ Company
- **Start Date:** July 1, 2026
- **Annual Salary:** $95,000 (prorated to $47,500 for 6 months)
- **Pay Frequency:** Monthly (P = 6 for this year)

### Monthly Calculation

**July to November (5 months):**
- Monthly gross: $7,916.67
- YTD earnings after November: $39,583.35

**December:**
- YTD earnings before December: $39,583.35
- December gross: $7,916.67
- New YTD earnings: $47,500

**Since $47,500 < $74,600 (YMPE):**
```
CPP = ($47,500 - $291.66) × 0.0595 = $2,800.83
CPP2 = $0
```

### Annual Summary

| Period | YTD Earnings | Monthly CPP | Monthly CPP2 | YTD CPP2 |
|:-------|:-------------|:------------|:-------------|:---------|
| Jul-Nov | $39,583 | Various | $0.00 | $0.00 |
| Dec | $47,500 | $466.81 | $0.00 | $0.00 |

**Total 2026:**
- CPP: $2,800.83 (below maximum)
- CPP2: $0.00 (did not reach YMPE)

**Note:** Maximum contributions are **not prorated** for mid-year starts. Employee will reach maximum in 2027 if earnings continue.

---

## A1.6 Scenario 4: Commission Income with Fluctuating Earnings

### Employee Profile

- **Employer:** Sales Company
- **Pay Frequency:** Monthly (P = 12)
- **Income Source:** Commission only
- **Annual Earnings:** $90,000

### Monthly Earnings and Calculations

| Month | Gross | YTD Gross | CPP | CPP2 | Notes |
|:------|:------|:----------|:-----|:-----|:------|
| Jan | $5,000 | $5,000 | $279.13 | $0.00 | Below YMPE |
| Feb | $6,000 | $11,000 | $342.58 | $0.00 | Below YMPE |
| Mar | $8,000 | $19,000 | $456.97 | $0.00 | Below YMPE |
| Apr | $10,000 | $29,000 | $571.35 | $0.00 | Below YMPE |
| May | $7,000 | $36,000 | $399.68 | $0.00 | Below YMPE |
| Jun | $9,000 | $45,000 | $514.06 | $0.00 | Below YMPE |
| Jul | $6,000 | $51,000 | $342.58 | $0.00 | Below YMPE |
| Aug | $8,000 | $59,000 | $456.97 | $0.00 | Below YMPE |
| Sep | $7,000 | $66,000 | $399.68 | $0.00 | Below YMPE |
| Oct | $9,000 | $75,000 | $514.06 | $16.00 | **Crosses YMPE** |
| Nov | $8,000 | $83,000 | $456.97 | $320.00 | Approaching YAMPE |
| Dec | $7,000 | $90,000 | $399.68 | $80.00 | **Reaches maximum** |

### Detailed October Calculation (Crosses YMPE)

**Before October:** YTD = $66,000
**October Gross:** $9,000
**New YTD:** $75,000

**CPP2 Calculation:**
```
CPP2_Range = Min($75,000, $85,000) - $74,600
CPP2_Range = $75,000 - $74,600
CPP2_Range = $400

C2 = $400 × 0.04
C2 = $16.00
```

**October CPP2 = $16.00**

### Detailed November Calculation

**Before November:** YTD = $75,000
**November Gross:** $8,000
**New YTD:** $83,000

**CPP2 Calculation:**
```
CPP2_Range = Min($83,000, $85,000) - $74,600
CPP2_Range = $83,000 - $74,600
CPP2_Range = $8,400

C2 = $8,400 × 0.04
C2 = $336.00

C2_Deduction = $336.00 - $16.00 (previous CPP2)
C2_Deduction = $320.00
```

**November CPP2 = $320.00**

### Detailed December Calculation (Reaches Maximum)

**Before December:** YTD = $83,000
**December Gross:** $7,000
**New YTD:** $90,000

**CPP2 Calculation:**
```
CPP2_Range = Min($90,000, $85,000) - $74,600
CPP2_Range = $85,000 - $74,600
CPP2_Range = $10,400 (maximum)

C2 = $10,400 × 0.04
C2 = $416.00 (maximum annual CPP2)

C2_Deduction = $416.00 - $336.00 (previous CPP2)
C2_Deduction = $80.00
```

**December CPP2 = $80.00**

**YTD CPP2 = $416.00 (maximum reached)**

### Annual Summary

| Category | Amount |
|:---------|:-------|
| **Total Earnings** | $90,000 |
| **Total CPP** | $4,230.45 (maximum) |
| **Total CPP2** | $416.00 (maximum) |
| **Combined Maximum Reached** | Yes (December) |

---

## A1.7 Scenario 5: Bonus Payment Above YMPE

### Employee Profile

- **Employer:** ABC Company
- **Annual Salary:** $70,000
- **Bonus:** $15,000 (paid in December)
- **Pay Frequency:** Monthly (P = 12)

### Regular Salary (January to November)

**Monthly Gross:** $5,833.33
**YTD Earnings (November):** $64,166.63

```
CPP = ($64,166.63 - $291.66) × 0.0595 = $3,789.71
CPP2 = $0 (below YMPE)
```

### December with Bonus

**Regular Pay:** $5,833.33
**Bonus:** $15,000
**Total December Pay:** $20,833.33

**New YTD Earnings:** $85,000 (exactly at YAMPE)

**CPP Calculation:**
```
Regular CPP = ($5,833.33 - $291.66) × 0.0595 = $329.37
YTD CPP before December = $3,789.71
New YTD CPP = $3,789.71 + $329.37 = $4,119.08

Bonus CPP = Min($20,833.33, $71,100) - $64,166.63 - $291.66
Bonus CPP = $6,641.71 × 0.0595 = $395.18

Total CPP = $4,119.08 + $395.18 = $4,514.26
Maximum CPP = $4,230.45
Final CPP = $4,230.45 (cap at maximum)
```

**December CPP Deduction:**
```
December CPP = $4,230.45 - $3,789.71 = $440.74
```

**CPP2 Calculation:**
```
New YTD Earnings = $85,000 (exactly at YAMPE)

CPP2_Range = Min($85,000, $85,000) - $74,600
CPP2_Range = $10,400

C2 = $10,400 × 0.04
C2 = $416.00 (maximum)
```

**December CPP2 = $416.00**

### Annual Summary

| Category | Amount |
|:---------|:-------|
| **Base Salary** | $70,000 |
| **Bonus** | $15,000 |
| **Total Earnings** | $85,000 |
| **Total CPP** | $4,230.45 (maximum) |
| **Total CPP2** | $416.00 (maximum) |

---

## A1.8 CPP2 Tracking Worksheet

### Year-to-Date Tracking Template

| Period | Gross Pay | YTD Gross | CPP This Period | YTD CPP | CPP2 This Period | YTD CPP2 | Notes |
|:-------|:----------|:----------|:----------------|:--------|:-----------------|:---------|:------|
| 1 | | | | | | | |
| 2 | | | | | | | |
| ... | | | | | | | |
| Total | | | | | | | |

### Maximum Reminders

**CPP Maximums:**
- YMPE: $74,600
- Maximum CPP: $4,230.45
- YAMPE: $85,000
- Maximum CPP2: $416.00

**When to Stop Deducting:**
- CPP: When YTD_CPP reaches $4,230.45
- CPP2: When YTD_CPP2 reaches $416.00

---

*Return to [Table of Contents](./table-of-contents.md) | [Main README](./README.md)*
