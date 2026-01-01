# Workers' Compensation Board (WCB) Reference

> **Status**: Reference Only (Not Config-Driven)
> **Last Updated**: 2026-01-01
> **Purpose**: Policy reference for future feature development

---

## Overview

Workers' Compensation Board (WCB) is a provincial/territorial insurance program that provides wage replacement and medical benefits to workers injured on the job.

### Key Policy Points

| Aspect | Detail |
|--------|--------|
| **Who Pays** | 100% Employer - Employees do NOT contribute |
| **Calculation** | Rate per $100 of payroll × Annual payroll |
| **Rate Factors** | Industry classification, safety record, claims history |
| **Mandatory** | Yes for most industries (some exemptions for low-risk) |
| **Filing Deadline** | Typically February 28 (varies by province) |

### Difference from CPP/EI

| Program | Employer Pays | Employee Pays |
|---------|--------------|---------------|
| CPP | Yes | Yes |
| EI | Yes (1.4× employee) | Yes |
| **WCB** | **Yes (100%)** | **No** |

---

## Provincial WCB Organizations

| Code | Province/Territory | Organization | Website |
|------|-------------------|--------------|---------|
| AB | Alberta | Workers' Compensation Board of Alberta | https://www.wcb.ab.ca |
| BC | British Columbia | WorkSafeBC | https://www.worksafebc.com |
| MB | Manitoba | Workers' Compensation Board of Manitoba | https://www.wcb.mb.ca |
| NB | New Brunswick | WorkSafeNB | https://www.worksafenb.ca |
| NL | Newfoundland & Labrador | WorkplaceNL | https://workplacenl.ca |
| NS | Nova Scotia | Workers' Compensation Board of Nova Scotia | https://www.wcb.ns.ca |
| ON | Ontario | Workplace Safety and Insurance Board (WSIB) | https://www.wsib.on.ca |
| PE | Prince Edward Island | Workers Compensation Board of PEI | https://www.wcb.pe.ca |
| QC | Quebec | CNESST | https://www.cnesst.gouv.qc.ca |
| SK | Saskatchewan | Saskatchewan Workers' Compensation Board | https://www.wcbsask.com |
| NT | Northwest Territories | WSCC (shared with NU) | https://www.wscc.nt.ca |
| NU | Nunavut | WSCC (shared with NT) | https://www.wscc.nt.ca |
| YT | Yukon | Yukon Workers' Compensation Health and Safety Board | https://www.wcb.yk.ca |

**National Association**: [AWCBC](https://awcbc.org) - Association of Workers' Compensation Boards of Canada

---

## 2025 Maximum Assessable Earnings

The maximum assessable earnings cap determines the maximum payroll amount per employee used to calculate WCB premiums.

| Province | 2025 Maximum | 2024 Maximum | Change |
|----------|-------------|--------------|--------|
| MB | $167,050 | $160,510 | +4.1% |
| BC | $121,500 | $116,700 | +4.1% |
| ON | $117,000 | $112,500 | +4.0% |
| NU | $113,900 | $110,600 | +3.0% |
| NT | $112,600 | $110,600 | +1.8% |
| AB | $106,400 | $104,600 | +1.7% |
| YT | $104,975 | $102,017 | +2.9% |
| SK | $104,531 | $99,945 | +4.6% |
| QC | $98,000 | $94,000 | +4.3% |
| NB | $84,200 | $76,900 | +9.5% |
| PE | $82,900 | $78,400 | +5.7% |
| NL | $79,345 | $76,955 | +3.1% |
| NS | $76,300 | $72,500 | +5.2% |

---

## Premium Rate Structure

### How Rates Are Determined

WCB premium rates are NOT uniform across provinces or companies. Each company's rate depends on:

1. **Industry Classification** - Higher risk industries (construction, mining) pay more
2. **Company Size** - Larger payrolls may qualify for experience rating
3. **Claims History** - Companies with more claims pay higher rates
4. **Safety Programs** - Good safety records can reduce rates

### Typical Rate Range

- **Low-risk** (office work): $0.20 - $0.50 per $100 payroll
- **Medium-risk** (retail, healthcare): $1.00 - $3.00 per $100 payroll
- **High-risk** (construction, logging): $5.00 - $15.00+ per $100 payroll

### Example Calculation

```
Company: Small retail store in Alberta
Industry Rate: $1.50 per $100 payroll
Annual Payroll: $500,000

WCB Premium = ($500,000 / $100) × $1.50 = $7,500/year
```

---

## Filing Deadlines by Province

| Province | Deadline | Notes |
|----------|----------|-------|
| AB | February 28 | |
| BC | Quarterly | Staggered deadlines |
| MB | February 28 | |
| NB | February 28 | |
| NL | February 28 | |
| NS | March 31 | |
| ON | March 31 | |
| PE | February 28 | |
| QC | March 15 | |
| SK | February 28 | |
| NT/NU | February 28 | |
| YT | February 28 | |

---

## Relation to Beanflow-Payroll System

### Current Implementation

- WCB rate field exists in **Pay Group** settings
- Used for **employer cost tracking**, not employee deductions
- Does NOT appear on employee pay stubs

### Why NOT in Pay Stub

WCB is an employer expense, similar to:
- Employer portion of EI (1.4× employee)
- Employer portion of CPP
- Employer health tax (in some provinces)

Employees never see or pay WCB directly.

### Future Feature Considerations

When implementing features like scheduling, time tracking, or leave management, WCB may be relevant for:

| Feature | WCB Relevance |
|---------|---------------|
| **Scheduling** | Overtime hours affect assessable payroll |
| **Time Tracking** | Total hours × wage = assessable earnings |
| **Leave Management** | Injury-related leave may trigger WCB claims |
| **Employer Reports** | Annual payroll reporting to WCB |
| **Cost Analysis** | WCB as part of total employer cost per employee |

---

## External Resources

### Official Sources
- [Canada.ca - Workers' Compensation](https://www.canada.ca/en/revenue-agency/services/tax/businesses/topics/payroll/payroll-deductions-contributions/special-payments/workers-compensation-claims.html)
- [AWCBC - Statistics & Data](https://awcbc.org/data-and-statistics/)
- [CANPAY - Provincial WCB Info](https://www.canpay.com/payroll-information/provincial-workers-compensation.html)

### Rate Information
- [WCB Alberta Premium Rates](https://www.wcb.ab.ca/insurance-and-premiums/how-premiums-are-set/)
- [WorkSafeBC Industry Rates](https://www.worksafebc.com/en/insurance/know-coverage-costs/industry-premium-rates)
- [WSIB Ontario Rate Framework](https://www.wsib.ca/en/businesses/premiums-and-coverage)

---

## Notes

- WCB rates are company-specific and cannot be automatically calculated by our system
- Maximum Assessable Earnings should be updated annually (typically announced in Q4)
- Some provinces (e.g., BC) have different names (WorkSafeBC) but serve the same function
