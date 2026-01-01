# Canadian Vacation Pay Standards by Province

This document provides a quick reference for vacation pay minimums across Canadian provinces and territories.

## Key Insight: Saskatchewan is Different

**Saskatchewan (SK)** has the highest minimum vacation entitlement in Canada:
- **New employees**: 5.77% (3 weeks) from day one
- **After 10 years**: 7.69% (4 weeks)

Most other provinces start at 4% (2 weeks).

## Summary Table

| Province | Initial Rate | Initial Weeks | Upgrade Threshold | Upgraded Rate | Upgraded Weeks |
|----------|--------------|---------------|-------------------|---------------|----------------|
| **SK** | **5.77%** | 3 | 10 years | **7.69%** | 4 |
| Federal | 4% | 2 | 5 years / 10 years | 6% / 8% | 3 / 4 |
| AB | 4% | 2 | 5 years | 6% | 3 |
| BC | 4% | 2 | 5 years | 6% | 3 |
| MB | 4% | 2 | 5 years | 6% | 3 |
| NB | 4% | 2 | 8 years | 6% | 3 |
| NL | 4% | 2 | 15 years | 6% | 3 |
| NS | 4% | 2 | 7 years | 6% | 3 |
| NT | 4% | 2 | None | 4% | 2 |
| NU | 4% | 2 | None | 4% | 2 |
| ON | 4% | 2 | 5 years | 6% | 3 |
| PE | 4% | 2 | 8 years | 6% | 3 |
| QC | 4% | 2 | 3 years | 6% | 3 |
| YT | 4% | 2 | None | 4% | 2 |

## Legal Principle

**Employers can offer more vacation than the minimum, but never less.**

If an employee's `vacation_rate_override` is set to `null`, the system automatically uses the provincial minimum based on:
1. Province of employment
2. Years of service (calculated from hire date)

If an employer wants to offer a higher rate, they set `vacation_rate_override` to that value. The system will validate that the override is >= the provincial minimum.

## Calculation Method

### Percentage-Based (Most Common)
Vacation pay = Gross Wages × Vacation Rate

### Saskatchewan's Unique Calculation
Saskatchewan calculates vacation as 3 weeks / 52 weeks = 5.77% (not 3/50 = 6%)

This means SK employees get slightly less than 3 full weeks' worth of pay, but they get it from day one instead of having to wait 5 years like in most provinces.

## Configuration Files

- `backend/config/vacation_pay/2025/provinces_jan.json` - 2025 rates
- `backend/config/vacation_pay/2026/provinces_jan.json` - 2026 rates
- `backend/config/vacation_pay/schemas/vacation_pay_schema.json` - Schema definition

## Implementation

The `VacationPayConfigLoader` class provides methods to:
- `get_minimum_rate(province, years_of_service)` - Get provincial minimum
- `get_effective_rate(province, years_of_service, override)` - Get effective rate considering override
- `calculate_years_of_service(hire_date)` - Calculate complete years of service

## Sources

- [Knit People - Vacation Pay Rates](https://www.knitpeople.com/payroll-legislations/vacation-pay-rates-and-entitlements)
- [Wagepoint - Vacation Pay in Canada](https://wagepoint.com/blog/vacation-pay-in-canada/)
- Saskatchewan Employment Act
- Canada Labour Code Part III, Division IV
- Provincial Employment Standards Acts
