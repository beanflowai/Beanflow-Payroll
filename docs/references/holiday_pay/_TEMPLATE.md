# [Province Name] - Holiday Pay Official Reference

> **Status**: ⬜ Not Verified | ✅ Verified | ⚠️ Needs Update
> **Last Verified**: YYYY-MM-DD
> **Verified By**: [Name]

## Official Sources

| Source | URL |
|--------|-----|
| Employment Standards | |
| Holiday Pay Guide | |
| Official Calculator | |

---

## Statutory Holidays (2025)

| Holiday | Date | Statutory? | Notes |
|---------|------|------------|-------|
| New Year's Day | Jan 1 | | |
| Family Day | Feb 17 | | |
| Good Friday | Apr 18 | | |
| Victoria Day | May 19 | | |
| Canada Day | Jul 1 | | |
| Labour Day | Sep 1 | | |
| Thanksgiving | Oct 13 | | |
| Remembrance Day | Nov 11 | | |
| Christmas Day | Dec 25 | | |

---

## Eligibility Rules

| Rule | Value | Notes |
|------|-------|-------|
| min_employment_days | | |
| require_last_first_rule | | |
| "5 of 9" rule | | |

### Details

-

---

## Holiday Pay Formula

### Formula Type
- **Type**:
- **Lookback Period**:

### Calculation
```
Holiday Pay =
```

### Includes
- [ ] Regular wages
- [ ] Overtime
- [ ] Vacation pay
- [ ] Previous holiday pay

---

## Regular vs Non-Regular Work Day

### Determining Regular Work Day
-

### Pay Rules

| Scenario | Pay | Formula |
|----------|-----|---------|
| Regular Day + Not Worked | | |
| Regular Day + Worked | | |
| Non-Regular Day + Not Worked | | |
| Non-Regular Day + Worked | | |

---

## Premium Rate

- **Rate**:
- **Notes**:

---

## Vacation Pay

| Years of Service | Vacation Weeks | Vacation Pay Rate |
|------------------|----------------|-------------------|
| < 1 year | | |
| 1-4 years | | |
| 5+ years | | |

---

## Config Verification Checklist

Compare with `backend/config/holiday_pay/2025/provinces_jan.json`:

- [ ] `formula_type` matches official
- [ ] `formula_params` matches official
- [ ] `eligibility.min_employment_days` matches official
- [ ] `eligibility.require_last_first_rule` matches official
- [ ] `premium_rate` matches official
- [ ] Regular/Non-regular day logic implemented
- [ ] "5 of 9" rule implemented (if applicable)

---

## Differences Found

| Field | Official | Current Config | Action Needed |
|-------|----------|----------------|---------------|
| | | | |

---

## References

1.
