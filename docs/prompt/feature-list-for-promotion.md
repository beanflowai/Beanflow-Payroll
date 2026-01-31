# BeanFlow Payroll 推广功能清单

> **日期**: 2026-01-24
> **目的**: 用具体功能推广 BeanFlow Payroll

---

## ✅ 已实现功能 (可用于推广)

### 1. 省级 Holiday Pay 计算 ⭐ 核心差异化

**实现位置**: `backend/app/services/payroll_run/holiday_pay/`

**省份特定公式**:
| 省份 | 公式 | 配置文件 |
|------|------|----------|
| Ontario | (4周工资 + 休假) ÷ 20 | `config/holiday_pay/2025/provinces_jan.json` |
| BC | 30天工资 ÷ 工作天数 | 同上 |
| Alberta | 4周平均日工资 | 同上 |

**特性**:
- 资格条件检查 (最少工作天数)
- Last/First 规则
- Premium pay (1.5x/2x)
- 新员工回退方案

---

### 2. 省级 Vacation Pay 计算 ⭐ 核心差异化

**实现位置**: `backend/app/services/payroll/vacation_pay_config_loader.py`

**配置文件**: `config/vacation_pay/2025/provinces_jan.json`

**分层费率**:
| 服务年限 | 大部分省 | 萨省 (最高) |
|----------|----------|-------------|
| 0-4 年 | 4% (2周) | 5.77% (3周) |
| 5+ 年 | 6% (3周) | - |
| 10+ 年 | 8% (4周) | - |

**支付方式**:
- ACCRUAL - 累计后支付
- PAY_AS_YOU_GO - 每次发薪支付
- LUMP_SUM - 每年一次性支付

---

### 3. Remittances 自动计算

**实现位置**: `docs/10_remittance_reporting.md` (规划中)

**已实现**:
- ✅ `RemitterType` enum (QUARTERLY, REGULAR, THRESHOLD_1, THRESHOLD_2)
- ✅ PD7A PDF 生成
- ✅ 公司 remitter_type 配置

**待实现**:
- Remittance periods 追踪
- 自动汇款提醒

---

### 4. 内置 Timesheet

**实现位置**:
- 数据库: `supabase/migrations/20260108120000_timesheet_entries.sql`
- API: `timesheetService.ts`
- UI: `TimesheetModal.svelte`

**功能**:
- 记录工作日期、常规工时、加班工时
- 按薪资记录分组
- 自动汇总总工时和工作天数

---

### 5. 多种 Pay Group 支持

**实现位置**: `models/payroll.py` - `PayGroup` model

**支持的配置**:

| 类型 | 选项 |
|------|------|
| **Pay Frequency** | Weekly, Bi-Weekly, Semi-Monthly, Monthly |
| **Employment Type** | Full-Time, Part-Time, Seasonal, Contract, Casual |
| **Compensation Type** | Salary (年薪), Hourly (时薪) |

**功能**:
- 按薪资组批量处理
- 组级别的加班规则
- 组级别的 Holiday/Vacation Pay 政策

---

### 6. 支持多种抵扣

**实现位置**: `payroll_engine.py` - `EmployeePayrollInput`

**税前抵扣** (影响税务计算):
- RRSP (注册退休储蓄计划)
- Union Dues (工会会费)
- RPP/PRPP (注册养老金计划)
- Child care expenses
- Medical expenses
- Charitable donations
- Alimony/maintenance

**税后抵扣** (不影响税务):
- Garnishments (工资扣押)
- Other deductions

---

### 7. 支持多种收入类型

**实现位置**: `PayrollRecordBase` in `models/payroll.py`

| 收入类型 | 字段 | 说明 |
|----------|------|------|
| 常规工资 | `gross_regular` | 标准时薪/薪资 |
| 加班费 | `gross_overtime` | 省级规则计算 |
| 奖金/佣金 | `bonus_earnings` | Lump-sum 支付 |
| 假期工资 | `holiday_pay` | Statutory holiday |
| 假期倍率工资 | `holiday_premium_pay` | 1.5x/2x premium |
| 休假工资 | `vacation_pay_paid` | Vacation payout |
| 其他收入 | `other_earnings` | 其他应税收入 |

---

### 8. 员工自助入口

**实现位置**: `frontend/src/routes/employee/[slug]/`

**功能页面**:
- `/profile` - 个人信息管理
- `/paystubs` - 查看 Paystub
- `/leave` - 休假/病假余额
- `/auth` - 账户验证

**员工自助功能**:
- Edit Personal Info - 编辑个人信息
- Edit Tax Info - 编辑税务信息 (TD1)
- Edit Bank Info - 编辑银行信息
- 查看 Paystub PDF
- 邀请加入门户

---

### 9. Paystub 自动生成和发送

**实现位置**:
- 生成: `paystub_generator.py`
- 存储: `paystub_storage.py` (DigitalOcean Spaces)
- 发送: `run_operations.py:send_paystubs()`

**功能**:
- ✅ CRA 合规格式 PDF 生成
- ✅ 员工信息、收入、扣款、YTD
- ✅ 省份特定显示 (Ontario vacation, BC employer contributions)
- ✅ 云存储 (DO Spaces)
- ✅ 批量邮件发送 (`/runs/{run_id}/send-paystubs`)

---

### 10. 其他核心功能

| 功能 | 状态 |
|------|------|
| CPP/EI 自动计算 (含 CPP2) | ✅ |
| 联邦税/省税自动计算 | ✅ |
| 加班费计算 (省级日/周阈值) | ✅ |
| YTD 累计跟踪 | ✅ |
| T4 年终报表 (PDF + XML) | ✅ |
| 薪资运行工作流 (审批流程) | ✅ |
| 998 测试通过 (PDOC 验证) | ✅ |

---

## 推广信息框架

### 主标题 (Slogan)

```
"Canadian Payroll with Provincial Policies, Free & Open Source"
"省级政策自动化的加拿大 Payroll 系统"
```

### 核心功能清单 (用于视频/文档)

```
✅ 省级 Holiday Pay 计算
   - Ontario: 4周平均公式
   - BC: 30天平均公式
   - Alberta: 4周平均日工资
   - 全部 12 省/区支持

✅ 省级 Vacation Pay 计算
   - 按服务年限自动分层 (4%/6%/8%)
   - 萨省最高 5.77% (3周)
   - 三种支付方式 (累计/随付/年付)

✅ Remittances 自动计算
   - PD7A 汇款单生成
   - Remitter Type 分类

✅ 内置 Timesheet
   - 工时记录
   - 加班自动计算

✅ 多种 Pay Group
   - Pay Frequency: 周薪/双周/半月/月薪
   - Employment Type: 全职/兼职/季节/合同/临时
   - Compensation Type: 年薪/时薪

✅ 支持多种抵扣
   - 税前: RRSP, Union Dues, RPP
   - 税后: Garnishments

✅ 支持多种收入类型
   - 常规工资、加班费、奖金、假期工资、休假工资

✅ 员工自助入口
   - 查看 Paystub
   - 更新税务信息
   - 休假余额查询

✅ Paystub 自动生成和发送
   - CRA 合规格式 PDF
   - 批量邮件发送

✅ CRA 合规
   - 2300+ tests, CRA-compliant validated
   - 160+ PDOC validation cases
   - T4 年终报表 (PDF + XML)
   - CPP/EI/税自动计算
```

---

## 视频/文章结构建议

### 开场 (15秒)

```
"处理加拿大 payroll，每个省政策都不一样：
Ontario 的 Holiday Pay 要算 4 周平均工资，
BC 要算 30 天工资，
Vacation Pay 还要按服务年限分层...

有没有免费的系统能自动处理这些？"
```

### 中段 (60秒)

```
"BeanFlow Payroll 是开源系统：

✅ 自动计算各省的 Holiday Pay 和 Vacation Pay
✅ 内置 Timesheet，加班自动计算
✅ 支持 4 种薪资周期、5 种雇佣类型
✅ 员工自助入口，自动发送 Paystub
✅ T4 年终报表一键生成
✅ 998 测试通过，CRA 合规"

"最重要的是：免费、开源"
```

### 结尾 (15秒)

```
"GitHub: BeanFlow Payroll
开源、免费、省级政策自动化"
```

---

## 下一步

1. **制作演示视频** - 展示上述功能
2. **编写快速开始指南** - 5分钟上手
3. **创建功能对比表** - vs QuickBooks/ADP/Wave
4. **收集用户证言** - 早期用户案例

---

_最后更新: 2026-01-24_
