---
name: tax-rates-2025
description: Quick reference for 2025 Canadian payroll tax rates - CPP, EI, federal tax brackets, provincial tax rates. For detailed calculations, see docs/02_phase2_calculations.md
owner: Payroll Team
last_updated: 2025-12-18
triggers:
  - 2025 tax rates
  - CPP rates
  - EI rates
  - federal tax brackets
  - provincial tax rates
  - tax quick reference
related_skills:
  - payroll-domain
  - backend-development
agent_hints:
  token_budget_hint: "Quick reference only - for detailed formulas see docs/02_phase2_calculations.md"
  write_scope: ["reads"]
---

# 2025 Canadian Payroll Tax Rates - Quick Reference

> **Source**: CRA T4127 121st Edition (July 2025)
> **Detailed Formulas**: `docs/02_phase2_calculations.md`

---

## CPP (Canada Pension Plan) - 2025

| Parameter | Value |
|-----------|-------|
| **Basic Exemption (annual)** | $3,500 |
| **YMPE** (Year's Max Pensionable Earnings) | $71,300 |
| **YAMPE** (Additional Maximum) | $81,200 |
| **Base CPP Rate** | 5.95% |
| **CPP2 Rate** (above YMPE) | 4.00% |
| **Max Base CPP Contribution** | $4,034.10 |
| **Max CPP2 Contribution** | $396.00 |
| **Total Max Employee CPP** | $4,430.10 |

```python
# Quick formula
base_cpp = 0.0595 × (earnings - (3500 / pay_periods))
cpp2 = 0.04 × (earnings_above_YMPE)  # Only on $71,300 - $81,200 range
```

---

## EI (Employment Insurance) - 2025

| Parameter | Value |
|-----------|-------|
| **MIE** (Max Insurable Earnings) | $65,700 |
| **Employee Rate** | 1.64% |
| **Employer Rate** | 2.296% (1.4× employee) |
| **Max Employee Premium** | $1,077.48 |
| **Max Employer Premium** | $1,508.47 |

```python
# Quick formula
ei_premium = insurable_earnings × 0.0164
employer_ei = employee_ei × 1.4
```

---

## Federal Tax Brackets - 2025

| Bracket | Income Range | Rate | Constant K |
|---------|--------------|------|------------|
| 1 | $0 - $57,375 | 15.0% | $0 |
| 2 | $57,375 - $114,750 | 20.5% | $3,155 |
| 3 | $114,750 - $177,882 | 26.0% | $9,468 |
| 4 | $177,882 - $253,414 | 29.0% | $14,804 |
| 5 | Over $253,414 | 33.0% | $24,940 |

| Credit | Amount |
|--------|--------|
| **Basic Personal Amount** | $16,129 |
| **Canada Employment Amount (CEA)** | $1,471 |

```python
# Quick formula
T3 = (Rate × Annual_Income) - K - K1 - K2 - K4
# K1 = 0.15 × TD1_claim_amount
# K2 = 0.15 × (CPP_credit + EI_credit)
# K4 = 0.15 × min(Annual_Income, CEA)
```

---

## Provincial Tax Rates - 2025 (Top Rate Summary)

| Province | Lowest Rate | Top Rate | Top Bracket Start |
|----------|-------------|----------|-------------------|
| **AB** | 10.00% | 15.00% | $355,845 |
| **BC** | 5.06% | 20.50% | $252,752 |
| **MB** | 10.80% | 17.40% | $100,000 |
| **NB** | 9.40% | 19.50% | $185,064 |
| **NL** | 8.70% | 21.80% | $1,103,478 |
| **NS** | 8.79% | 21.00% | $150,000 |
| **NT** | 5.90% | 14.05% | $164,525 |
| **NU** | 4.00% | 11.50% | $173,205 |
| **ON** | 5.05% | 13.16% | $220,000 |
| **PE** | 9.65% | 18.75% | $140,000 |
| **SK** | 10.50% | 14.50% | $148,734 |
| **YT** | 6.40% | 15.00% | $500,000 |

### Special Provincial Rules

| Province | Special Tax |
|----------|-------------|
| **Ontario** | Surtax (20%/36%) + Health Premium ($0-$900) |
| **BC** | Tax Reduction (up to $562 for low income) |
| **Alberta** | K5P Supplemental Credit |

---

## Pay Period Factors

| Frequency | Periods/Year | Factor |
|-----------|--------------|--------|
| Weekly | 52 | ÷52 |
| Bi-weekly | 26 | ÷26 |
| Semi-monthly | 24 | ÷24 |
| Monthly | 12 | ÷12 |

---

## Quick Calculation Example (Bi-weekly, $60K/year, Ontario)

```
Gross per period: $2,307.69 ($60,000 ÷ 26)

CPP: $130.08 [(2307.69 - 134.62) × 0.0595]
EI:  $37.85  [2307.69 × 0.0164]
Federal Tax: ~$215 (varies by TD1)
Provincial Tax: ~$95 (varies by TD1)
─────────────────────
Approx. Deductions: ~$478
Net Pay: ~$1,830
```

---

## Detailed Documentation Links

- **CPP/EI/Tax Formulas**: `docs/02_phase2_calculations.md`
- **Ontario Surtax/Health Premium**: `docs/02_phase2_calculations.md:806-814`
- **BC Tax Reduction**: `docs/02_phase2_calculations.md:816-823`
- **All Provincial Brackets**: `docs/02_phase2_calculations.md:643-866`
- **CRA Official**: https://www.canada.ca/en/revenue-agency/services/forms-publications/payroll/t4127-payroll-deductions-formulas.html
