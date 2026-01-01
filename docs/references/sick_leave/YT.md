# Yukon - Sick Leave Official Reference

> **Status**: ✅ Verified
> **Last Verified**: 2025-12-31
> **Verified By**: Claude

## Official Sources

| Source | URL |
|--------|-----|
| Employment Standards Act | https://yukon.ca/en/employment-standards |
| Paid Sick Leave Rebate Program | https://yukon.ca/en/paid-sick-leave-rebate |

---

## Sick Leave Entitlement

| Type | Days per Year | Notes |
|------|---------------|-------|
| Paid Sick Leave | 0 | Not legislated in Yukon |
| Unpaid Sick Leave | 0 | No specific statutory provision |

---

## Eligibility Rules

| Rule | Value | Notes |
|------|-------|-------|
| Waiting Period | N/A | No statutory sick leave |
| Applies to | N/A | No statutory sick leave |

---

## Accrual Method

- **Method**: N/A (no statutory sick leave)
- **Initial Days After Qualifying**: N/A
- **Days Per Month After Initial**: N/A
- **Maximum Days**: N/A

---

## Carryover Rules

| Rule | Value |
|------|-------|
| Allows Carryover | N/A |
| Max Carryover Days | N/A |
| Expiry | N/A |

---

## Pay Calculation

- **Formula**: N/A (no statutory paid sick leave)
- **Rate**: N/A

---

## Medical Certificate Requirements

- **Required After**: N/A
- **Notes**: No statutory requirement as there is no statutory sick leave

---

## Voluntary Paid Sick Leave Rebate Program

Yukon Government offers a **voluntary** Paid Sick Leave Rebate Program to encourage employers to provide paid sick leave. This is NOT a statutory requirement.

### Program Details

| Feature | Value |
|---------|-------|
| Maximum Hours | Up to 40 hours per employee per program year |
| Employee Eligibility | 90 days of employment |
| Maximum Wage | $36.71/hour (employees earning more are not covered) |
| Program Extended To | March 31, 2026 |
| Employer Participation | Voluntary |

### Important Notes

- This program reimburses employers who voluntarily provide paid sick leave
- It does NOT create a statutory right to sick leave for employees
- Employers are not required to participate
- Employees have no legal entitlement to sick leave under this program

---

## Config Verification Checklist

Compare with `backend/config/holiday_pay/2025/provinces_jan.json`:

- [x] `paid_days_per_year` matches official (0 - no statutory sick leave)
- [x] `unpaid_days_per_year` matches official (0 - no specific provision)
- [x] `waiting_period_days` matches official (0 - N/A)
- [x] `allows_carryover` matches official (false - N/A)
- [x] `max_carryover_days` matches official (0 - N/A)
- [x] `accrual_method` matches official (immediate - default value)

---

## Differences Found

| Field | Official | Current Config | Action Needed |
|-------|----------|----------------|---------------|
| None | - | - | Config is correct |

---

## References

1. Yukon Employment Standards Act - https://yukon.ca/en/employment-standards
2. Yukon Paid Sick Leave Rebate Program - https://yukon.ca/en/paid-sick-leave-rebate
3. Yukon Government Press Release on Program Extension - https://yukon.ca/en/news/paid-sick-leave-rebate-program-extended
