# Prince Edward Island - Sick Leave Official Reference

> **Status**: ⚠️ Needs Update
> **Last Verified**: 2025-12-31
> **Verified By**: Claude

## Official Sources

| Source | URL |
|--------|-----|
| Employment Standards Act | https://www.princeedwardisland.ca/en/information/workforce-advanced-learning-and-population/employment-standards-act |
| Sick Leave Guide | https://www.princeedwardisland.ca/en/information/workforce-advanced-learning-and-population/sick-leave |

---

## Sick Leave Entitlement

### Paid Sick Leave (Effective October 1, 2024)

Paid sick leave is tenure-based and increases with length of employment:

| Employment Duration | Paid Sick Days per Year | Notes |
|---------------------|-------------------------|-------|
| After 12 months | 1 day | First tier |
| After 24 months | 2 days | Second tier |
| After 36 months | 3 days | Maximum entitlement |

### Unpaid Sick Leave

| Type | Days per Year | Notes |
|------|---------------|-------|
| Current (pre-Sept 2025) | 3 days | After 3 months employment |
| New ESA (Sept 2025) | 4 days | After 30 days employment |

### Long-Term Leave (New ESA - Sept 2025)

| Type | Duration | Notes |
|------|----------|-------|
| Long-term sick leave | Up to 27 weeks | New provision under updated ESA |

---

## Eligibility Rules

### Current Rules

| Rule | Value | Notes |
|------|-------|-------|
| Unpaid Leave Waiting Period | 3 months | Days of employment before eligible for unpaid leave |
| Paid Leave Waiting Period | 12 months | Before first paid day entitlement |
| Applies to | All employees | Full-time and part-time |

### New ESA Rules (Effective September 2025)

| Rule | Value | Notes |
|------|-------|-------|
| Unpaid Leave Waiting Period | 30 days | Reduced from 3 months |
| Applies to | All employees | Full-time and part-time |

---

## Accrual Method

- **Method**: Tenure-based (not standard accrual)
- **Initial Days After Qualifying**: 1 day (after 12 months)
- **Second Tier**: 2 days (after 24 months)
- **Maximum Days**: 3 days (after 36 months)

**Note**: PEI's paid sick leave is unique in that it is tied to total length of employment, not annual accrual. Employees unlock additional days as they reach employment milestones.

---

## Carryover Rules

| Rule | Value |
|------|-------|
| Allows Carryover | No |
| Max Carryover Days | 0 |
| Expiry | End of calendar year |

**Note**: Paid sick days are an annual entitlement and do not carry over.

---

## Pay Calculation

- **Formula**: Regular rate of pay for hours employee would have worked
- **Rate**: 100% of regular wages

---

## Medical Certificate Requirements

- **Required After**: 3 consecutive days
- **Notes**: Employer may require a medical certificate for absences exceeding 3 consecutive days

---

## Config Verification Checklist

Compare with `backend/config/sick_leave/2025/provinces_jan.json`:

- [ ] `paid_days_per_year` matches official - **MISMATCH**: Config shows 0, should be 1-3 based on tenure
- [x] `unpaid_days_per_year` matches official - Config shows 3 days (correct for pre-Sept 2025)
- [ ] `waiting_period_days` matches official - Config shows 0, should be 90 (3 months) or 365 for paid
- [x] `allows_carryover` matches official - Config shows false (correct)
- [x] `max_carryover_days` matches official - Config shows 0 (correct)
- [ ] `accrual_method` matches official - Config shows "immediate", should be "tenure_based" or similar

---

## Differences Found

| Field | Official | Current Config | Action Needed |
|-------|----------|----------------|---------------|
| `paid_days_per_year` | 1-3 days (tenure-based) | 0 | **Requires schema change** - PEI's model is tenure-based, not fixed annual |
| `waiting_period_days` | 90 days (unpaid), 365 days (paid) | 0 | Update to reflect actual waiting periods |
| `accrual_method` | tenure_based | immediate | Consider adding "tenure_based" accrual method |

---

## Implementation Considerations

### Complex Tenure-Based Model

PEI's paid sick leave model (effective Oct 1, 2024) is more complex than other provinces:

1. **Cannot be represented by simple `paid_days_per_year`**: The entitlement depends on how long the employee has been with the employer.

2. **Suggested Schema Enhancement**:
   ```json
   "PE": {
     "paid_days_tiers": [
       {"after_months": 12, "days": 1},
       {"after_months": 24, "days": 2},
       {"after_months": 36, "days": 3}
     ],
     "unpaid_days_per_year": 3,
     "unpaid_waiting_period_days": 90,
     "allows_carryover": false,
     "max_carryover_days": 0,
     "accrual_method": "tenure_based",
     "notes": "PEI Employment Standards Act - Paid sick leave tiered by tenure (Oct 2024)"
   }
   ```

3. **Upcoming Change (Sept 2025)**: The new ESA will change unpaid leave to 4 days after only 30 days of employment, plus introduce 27-week long-term leave.

---

## References

1. Prince Edward Island Employment Standards Act
2. PEI Workforce, Advanced Learning and Population - Sick Leave Information
3. Bill 102 - Amendments to Employment Standards Act (effective October 1, 2024)
4. Upcoming ESA amendments (effective September 2025)
