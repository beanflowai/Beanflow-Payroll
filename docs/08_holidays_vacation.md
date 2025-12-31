# Phase 8: Holidays & Vacation Pay

**Complexity**: Medium
**Prerequisites**: Phase 1 (Data Layer), Phase 2 (Calculations), Phase 6 (Configuration)

---

## 🎯 Objectives

Implement comprehensive holiday and vacation pay functionality for Canadian payroll across 12 provinces/territories (excluding Quebec).

### Deliverables Status

| Deliverable | Status | Notes |
|-------------|--------|-------|
| Statutory holiday calendars for all provinces (2025-2027) | ✅ 完成 | `statutory_holidays` 表已创建，2025-2027 数据已填充 |
| Holiday pay calculation by province-specific rules | ✅ 完成 | `HolidayPayCalculator` 实现 ON/BC/AB 省级公式 |
| Vacation pay accrual and tracking system | ⚠️ 部分 | 有字段和类型，Years of Service 自动计算待完成 |
| Configuration-driven holiday management | ✅ 完成 | 数据库存储，前端从 Supabase 查询 |
| Integration with payroll calculator | ✅ 完成 | `HolidayPayCalculator` 集成到 `run_operations.py` |
| UI enhancements for holiday indicators | ✅ 完成 | HolidayAlert, HolidayWorkModal（含数据持久化） |

---

## 📊 Current Implementation Status

### ✅ 已完成 (Frontend UI)

| 组件 | 文件路径 | 功能 |
|------|----------|------|
| HolidayAlert | `frontend/src/lib/components/payroll/HolidayAlert.svelte` | 显示pay period内的节假日提醒 |
| HolidayWorkModal | `frontend/src/lib/components/payroll/HolidayWorkModal.svelte` | 录入员工在节假日工作的小时数（含数据持久化） |
| PayGroupStatutorySection | `frontend/src/lib/components/company/pay-group-detail/PayGroupStatutorySection.svelte` | 配置statutory deduction exemptions |

### ✅ 已完成 (Types & Models)

- **Frontend**: `Holiday`, `HolidayWorkEntry`, `VacationPayoutEntry` in `payroll.ts`
- **Frontend**: `VacationRatePreset`, `VacationConfig` in `employee.ts`
- **Backend**: `EmployeePayrollInput.holiday_pay`, `holiday_premium_pay` in `payroll.py`
- **Database**: `payroll_records` 表有 `holiday_pay`, `holiday_premium_pay`, `vacation_accrued` 字段

### ✅ 已完成 (Database & Integration)

| 功能 | 文件路径 | 说明 |
|------|----------|------|
| `statutory_holidays` 表 | `backend/supabase/migrations/20251231220000_create_statutory_holidays.sql` | 包含 2025-2026 数据 |
| 2027 节假日数据 | `backend/supabase/migrations/20251231230000_add_2027_statutory_holidays.sql` | 2027 年数据 |
| 前端节假日查询 | `frontend/src/lib/services/payroll/pay-groups.ts:224-244` | 从 Supabase 查询 |
| Holiday Pay 计算修复 | `backend/app/services/payroll_run/run_operations.py:230` | 使用 `GrossCalculator.calculate_hourly_rate()` |
| HolidayWorkModal 数据持久化 | `frontend/src/lib/components/payroll/HolidayWorkModal.svelte` | 从 `inputData` 读取已保存数据 |
| Draft/Non-Draft 视图区分 | `frontend/src/routes/(app)/payroll/run/[periodEnd]/+page.svelte` | 非 Draft 隐藏 Manage 按钮 |

### ⚠️ 待完成

1. ~~**省级 Holiday Pay 计算公式**~~ - ✅ 已完成 (`HolidayPayCalculator`)
2. ~~**Holiday Pay 资格检查**~~ - ✅ 已完成（30天雇佣规则）
3. **Years of Service 自动计算** - 4%→6% 自动切换（Phase 3）

---

## 📚 Background: Canadian Employment Standards

### Statutory Holidays Overview

- **Federal (Common)**: New Year's Day, Good Friday, Canada Day, Labour Day, Christmas Day
- **Provincial Variations**: Family Day, Victoria Day, Thanksgiving, Remembrance Day
- **Unique Provincial**: Nunavut Day, Islander Day, Heritage Day, Memorial Day (NL)

### Vacation Pay Overview

| Years of Service | Vacation Pay Rate | Applicable To |
|------------------|-------------------|---------------|
| 0 - 4 years | 4% | All provinces |
| 5 - 9 years | 6% | All provinces |
| 10+ years | 8% | Federal only |

**Custom Rates**: Saskatchewan uses 5.77% (3 weeks) for 1-9 years

---

## 📅 Task 8.1: Statutory Holiday Database

### Provincial Statutory Holiday Matrix (2025)

| Holiday | AB | BC | MB | NB | NL | NS | NT | NU | ON | PE | SK | YT |
|---------|----|----|----|----|----|----|----|----|----|----|----|----|
| **New Year's Day** (Jan 1) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Family Day** (Feb 17) | ✅ | ✅ | ⚪ | ✅ | ⚪ | ⚪ | ⚪ | ⚪ | ✅ | ⚪ | ✅ | ⚪ |
| **Louis Riel Day** (Feb 17) | ⚪ | ⚪ | ✅ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ |
| **Islander Day** (Feb 17) | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ✅ | ⚪ | ⚪ |
| **Heritage Day (NS)** (Feb 17) | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ✅ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ |
| **Good Friday** (Apr 18) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Easter Monday** (Apr 21) | 🟡 | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ✅ | ⚪ | ⚪ | ⚪ | ⚪ |
| **Victoria Day** (May 19) | ✅ | ✅ | ✅ | ✅ | ⚪ | ⚪ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Canada Day** (Jul 1) | ✅ | ✅ | ✅ | ✅ | ✅* | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Nunavut Day** (Jul 9) | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ✅ | ⚪ | ⚪ | ⚪ | ⚪ |
| **Civic Holiday** (Aug 4) | 🟡 | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ✅ | ✅ | ⚪ | ⚪ | ✅ | ⚪ |
| **BC Day** (Aug 4) | ⚪ | ✅ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ |
| **Labour Day** (Sep 1) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Truth & Reconciliation** (Sep 30) | 🟡 | ✅ | ✅ | ⚪ | ⚪ | ⚪ | ⚪ | ✅ | ⚪ | ✅ | ⚪ | ✅ |
| **Thanksgiving** (Oct 13) | ✅ | ✅ | ✅ | ✅ | ⚪ | ⚪ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Remembrance Day** (Nov 11) | ✅ | ✅ | ⚪ | ⚪ | ✅ | ⚪ | ✅ | ✅ | ⚪ | ✅ | ✅ | ✅ |
| **Christmas Day** (Dec 25) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Boxing Day** (Dec 26) | 🟡 | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ✅ | ⚪ | ⚪ | ⚪ |
| **Total Statutory** | **9** | **11** | **9** | **7** | **6** | **6** | **10** | **12** | **9** | **8** | **10** | **9** |

**Legend:** ✅ = Statutory (mandatory) | 🟡 = Optional | ⚪ = Not a holiday | \* = NL calls Canada Day "Memorial Day"

### Moveable Holidays (2025-2026)

| Holiday | 2025 | 2026 | Calculation Rule |
|---------|------|------|------------------|
| Good Friday | Apr 18 | Apr 3 | Easter Sunday - 2 days |
| Easter Monday | Apr 21 | Apr 6 | Easter Sunday + 1 day |
| Victoria Day | May 19 | May 18 | Last Monday before May 25 |
| Family Day | Feb 17 | Feb 16 | 3rd Monday in February |
| BC Day/Civic Holiday | Aug 4 | Aug 3 | 1st Monday in August |
| Labour Day | Sep 1 | Sep 7 | 1st Monday in September |
| Thanksgiving | Oct 13 | Oct 12 | 2nd Monday in October |

### Database Schema (✅ 已完成)

```sql
-- 文件: backend/supabase/migrations/20251231220000_create_statutory_holidays.sql
CREATE TABLE statutory_holidays (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  province TEXT NOT NULL,           -- 'ON', 'BC', 'AB', etc.
  holiday_date DATE NOT NULL,
  name TEXT NOT NULL,
  name_fr TEXT,                     -- French name (optional)
  year INTEGER NOT NULL,
  is_statutory BOOLEAN DEFAULT TRUE,  -- TRUE = mandatory, FALSE = optional
  calculation_rule TEXT,            -- For moveable holidays
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(province, holiday_date)
);

CREATE INDEX idx_holidays_province_year ON statutory_holidays(province, year);
CREATE INDEX idx_holidays_date_range ON statutory_holidays(holiday_date);
CREATE INDEX idx_holidays_province_date ON statutory_holidays(province, holiday_date, is_statutory);
```

**数据**: 2025-2027 年各省节假日数据已填充（12 省份 × 3 年）

### Frontend Integration (✅ 已完成)

`frontend/src/lib/services/payroll/pay-groups.ts:224-244`:

```typescript
// 从 Supabase 查询 pay period 内的节假日
const { data: holidayData, error: holidayError } = await supabase
  .from('statutory_holidays')
  .select('holiday_date, name, province')
  .gte('holiday_date', periodStartStr)
  .lte('holiday_date', periodEndStr)
  .in('province', Array.from(provinces))
  .eq('is_statutory', true);
```

---

## 💰 Task 8.2: Holiday Pay Calculation

### Provincial Holiday Pay Formulas

| Province | Formula | Description |
|----------|---------|-------------|
| **Ontario** | `(Total wages in past 4 weeks + vacation pay) ÷ 20` | 4周平均日薪 |
| **BC** | Hourly: `avg_daily_hours × hourly_rate`<br>Salaried: `annual_salary ÷ pay_periods ÷ work_days` | 平均日薪 |
| **Alberta** | `earnings_in_pay_period ÷ days_in_pay_period` | 前期日均 |
| **Other** | 多数使用 BC 或 ON 的变体 | - |

### Holiday Pay Eligibility Rules

**Common Requirements:**
- Employed for 30+ days before the holiday
- Worked last scheduled shift before holiday
- Worked first scheduled shift after holiday
- Not absent without permission on either shift

**Exceptions:** Medical leave, authorized vacation, employer-granted leave

### Worked Holiday Premium Pay

If employee works on statutory holiday:
- **Regular holiday pay** (automatic) + **Premium pay for hours worked**
- Premium rates: 1.5× (Ontario, BC, most provinces)

**Example (Ontario):**
- Employee works 8 hours on Christmas at $25/hour
- Regular holiday pay (from formula): $200
- Premium pay: 8 × $25 × 1.5 = $300
- **Total: $500**

### Implementation Approach

**简单查询 (Supabase Client):**
- 查询 pay period 内的节假日列表
- 查询员工的 holiday work hours

**复杂计算 (Backend API):**
- 省级 holiday pay 计算（需要历史工资数据）
- Holiday pay eligibility 检查

---

## 🏖️ Task 8.3: Vacation Pay Calculation

### Vacation Pay Methods

| Method | Description | Balance Tracking | Common Use |
|--------|-------------|------------------|------------|
| **Accrual** | 累积但不立即发放，休假时支付 | ✅ Required | Most industries |
| **Pay-As-You-Go** | 每期发放 4%/6% 到工资 | ❌ Not needed | Construction, seasonal |
| **Lump Sum** | 年底一次性发放 | ✅ Required | Rare |

### Accrual Method Flow

1. Calculate gross earnings (regular + overtime)
2. Accrue vacation pay = gross × vacation_rate (4% or 6%)
3. Update vacation balance += vacation_accrued
4. Calculate deductions on gross earnings ONLY
5. Net pay = gross - deductions

When employee takes vacation:
- Pay out from balance: vacation_hours × hourly_rate
- Deduct from vacation_balance

### Pay-As-You-Go Method Flow

1. Calculate gross earnings (regular + overtime)
2. Calculate vacation pay = gross × vacation_rate
3. Add vacation to gross: total_gross = gross + vacation_pay
4. Calculate deductions on total_gross (including vacation)
5. Net pay = total_gross - deductions

**Important:** No balance tracking needed for pay-as-you-go

### Years of Service Calculation

```
Years of Service = (calculation_date - hire_date).days / 365.25
```

**Rate Transition at 5-Year Mark:**
- < 5 years: 4%
- ≥ 5 years: 6%
- ≥ 10 years (Federal only): 8%

### Vacation Year-End Rules

| Policy | Description | Implementation |
|--------|-------------|----------------|
| **Carry-Over** | Balance rolls to next year | Default, no action |
| **Use-It-Or-Lose-It** | Unused balance forfeited | Zero balance on Jan 1 |
| **Payout** | Cash out unused balance | Payout before year-end |

---

## 🏥 Task 8.7: Sick Leave System

### Provincial Sick Leave Entitlements (2025)

| Province | Paid Days | Unpaid Days | Waiting Period | Carryover |
|----------|-----------|-------------|----------------|-----------|
| **BC** | 5 | 3 | 90 days | No |
| **ON** | 0 | 3 (IDEL) | None | No |
| **AB** | 0 | 0 | N/A | N/A |
| **Federal** | 10 | 0 | 30 days | Yes (max 10) |

**Key Rule:** Part-time employees are NOT pro-rated - they receive full entitlement.

### BC Sick Leave

**Average Day's Pay Formula:**
- Total wages in past 30 calendar days ÷ number of days actually worked
- EXCLUDES overtime pay
- INCLUDES vacation pay

**Rules:**
- Taking even 1 hour off = 1 full day of entitlement used
- Resets on January 1 each year
- No payout on termination

### Federal Sick Leave

**Accrual:**
- 3 days after 30-day qualifying period
- +1 day at start of each subsequent month
- Maximum 10 days per year
- Unused days carry to next year (max 10 total)

---

## 🚀 Implementation Roadmap

### Phase 1: 恢复节假日显示 (Priority: P0) ✅ 已完成

**Goal:** 让节假日在 Payroll Run 页面正常显示

| Step | Task | Status | Files |
|------|------|--------|-------|
| 1.1 | 创建 `statutory_holidays` 表 | ✅ | `backend/supabase/migrations/20251231220000_create_statutory_holidays.sql` |
| 1.2 | 填充 2025-2027 节假日数据 | ✅ | 同上 + `20251231230000_add_2027_statutory_holidays.sql` |
| 1.3 | 前端查询节假日 | ✅ | `frontend/src/lib/services/payroll/pay-groups.ts:224-244` |
| 1.4 | HolidayAlert 显示 | ✅ | `HolidayAlert.svelte` |
| 1.5 | HolidayWorkModal 数据持久化 | ✅ | `HolidayWorkModal.svelte` 从 `inputData` 读取 |
| 1.6 | Holiday Pay 计算修复 (Salaried) | ✅ | `run_operations.py:230` 使用 `GrossCalculator.calculate_hourly_rate()` |
| 1.7 | 非 Draft 隐藏 Manage 按钮 | ✅ | `+page.svelte` |

### Phase 2: Holiday Pay 计算 (Priority: P1) ✅ 完成

**实现概述：HolidayPayCalculator 完整实现省级公式**

```python
# holiday_pay_calculator.py - HolidayPayCalculator
# 支持 Regular Holiday Pay (Hourly only) + Premium Pay (all employees)
holiday_result = self.holiday_calculator.calculate_holiday_pay(
    employee=employee,
    province=province_code,
    pay_frequency=pay_frequency_str,
    period_start=period_start_obj,
    period_end=period_end_obj,
    holidays_in_period=employee_holidays,
    holiday_work_entries=input_data.get("holidayWorkEntries") or [],
    current_period_gross=gross_regular + gross_overtime,
    current_run_id=str(run_id),
)
```

| Step | Task | Status | Files |
|------|------|--------|-------|
| 2.1 | 省级 Holiday Pay 公式 (ON/BC/AB) | ✅ 完成 | `holiday_pay_calculator.py` |
| 2.2 | Holiday Pay 资格检查 (30天规则) | ✅ 完成 | `_is_eligible_for_holiday_pay()` |
| 2.3 | 集成 HolidayWorkModal 数据 | ✅ 完成 | `run_operations.py` |
| 2.4 | Holiday Premium 1.5x 计算 | ✅ 完成 | `_calculate_premium_pay()` |
| 2.5 | 完整数据流 | ✅ 完成 | Modal → API → input_data → HolidayPayCalculator → 返回 |

**省级公式实现：**

| 省份 | 公式 | 实现状态 |
|------|------|----------|
| Ontario | `(过去4周工资 + vacation pay) ÷ 20` | ✅ `_calculate_ontario_daily_pay()` |
| BC | `8h × hourly_rate` | ✅ `_calculate_bc_daily_pay()` |
| Alberta | `当期收入 ÷ 当期工作天数` | ✅ `_calculate_alberta_daily_pay()` |
| Other | 使用 BC 公式作为默认 | ✅ fallback to BC |

**资格检查规则：**
- ✅ 雇佣满 30 天以上 (简单版本)
- ⏭️ 节假日前最后一个班次出勤 (跳过 - 复杂度过高)
- ⏭️ 节假日后第一个班次出勤 (跳过 - 复杂度过高)

**测试覆盖：**
- `tests/payroll/test_holiday_pay_calculator.py` - 26 个测试用例

### Phase 3: Vacation Accrual 完善 (Priority: P1)

| Step | Task | Status | Files |
|------|------|--------|-------|
| 3.1 | Years of Service 自动计算 | ❌ TODO | `ytd_calculator.py` |
| 3.2 | Pay-As-You-Go 方式支持 | ✅ 完成 | `run_operations.py:157-160` |
| 3.3 | Vacation Balance 更新 | ✅ 完成 | `run_operations.py:854-922` (approve 时更新+验证) |

### Phase 4: Sick Leave (Priority: P2)

| Step | Task | Status | Files |
|------|------|--------|-------|
| 4.1 | BC/Federal sick leave 计算 | ✅ 完成 | `sick_leave_service.py`, `sick_leave_config_loader.py`, `sick_leave.py` (API) |
| 4.2 | UI for sick leave balance | ⚠️ 部分 | Employee Portal 使用 mock 数据，Paystub 简化显示 |

#### Step 4.1 已完成内容:
- **SickLeaveService** (465行): BC 30天平均日薪、Federal 20天平均日薪、月度累积、eligibility 检查、year-end carryover
- **Config Loader**: JSON 配置文件支持 (14省份)，mid-year version 支持
- **API Endpoints**: `GET /sick-leave/configs`, `GET /sick-leave/configs/{province}`, `GET /employees/{id}/sick-leave/{year}`
- **Database**: `sick_leave_configs`, `employee_sick_leave_balances`, `sick_leave_usage_history` 表 + RLS
- **Tests**: `test_sick_leave_service.py` (641行) + `test_sick_leave.py` (API测试)
- **Frontend**: `sickLeaveService.ts` (API调用+缓存), `sick-leave.ts` (类型定义)

#### Step 4.2 待完成:
- `/employee/leave` 页面需要从 mock 数据改为调用 `sickLeaveService.getEmployeeSickLeaveBalance()`
- Paystub `_build_sick_leave()` 应从 `employee_sick_leave_balances` 表获取完整数据
- 考虑添加 Admin/HR 视图管理员工 sick leave balance

---

## 📚 References

- Ontario ESA: https://www.ontario.ca/document/your-guide-employment-standards-act-0/public-holidays
- BC Employment Standards: https://www2.gov.bc.ca/gov/content/employment-business/employment-standards-advice/employment-standards/statutory-holidays
- BC Sick Leave: https://www2.gov.bc.ca/gov/content/employment-business/employment-standards-advice/paid-sick-leave
- Federal Sick Leave: https://www.canada.ca/en/employment-social-development/programs/laws-regulations/labour/interpretations-policies/medical-leave-pay.html
- CRA T4 Guide: https://www.canada.ca/en/revenue-agency/services/forms-publications/publications/rc4120.html

---

**Related Documents:**
- [Phase 1: Data Layer](./01_phase1_data_layer.md)
- [Phase 2: Calculations](./02_phase2_calculations.md)
- [Phase 6: Configuration Architecture](./06_configuration_architecture.md)
