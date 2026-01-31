# Canadian Payroll Implementation - Master Checklist

**Project**: BeanFlow Payroll (Standalone Product)
**Scope**: All provinces/territories except Quebec
**Timeline**: 8-10 weeks

> **Last Updated**: 2026-01-02
> **Architecture Version**: v3.4 (T4 + Remittance 实现完成)

---

## 🚀 Standalone Product Architecture

BeanFlow Payroll is a **standalone product** with its own frontend:

| Aspect | Details |
|--------|---------|
| **Domain** | `payroll.beanflow.com` |
| **Frontend** | Separate SvelteKit app (`payroll-frontend/`) |
| **Backend** | Shared FastAPI with `/payroll/` route prefix |
| **Auth** | Shared Google OAuth with BeanFlow Bookkeeping |
| **Database** | Shared Supabase, separate tables |

See `14_standalone_architecture.md` for detailed setup.

---

## 🔄 Architecture Updates

This checklist has been updated to reflect standalone product architecture:

| Component | Previous Plan | Current Architecture |
|-----------|--------------|---------------------|
| **Product Model** | Module in BeanFlow | **Standalone Product** |
| **Frontend** | Embedded in `/payroll/` route | **Separate SvelteKit app** |
| **Domain** | Same as main app | **`payroll.beanflow.com`** |
| **Database** | Firestore | **Supabase (PostgreSQL)** |
| **File Storage** | Google Drive | **DigitalOcean Spaces** |
| **API Pattern** | Direct service | **Repository-Service-API** |
| **Multi-tenancy** | Basic | **RLS + user_id** |

---

## 📋 Overall Progress Tracker

| Phase | Status | Start Date | End Date | Notes |
|-------|--------|------------|----------|-------|
| **Phase 0: Frontend Setup** | ✅ Completed | 2025-12-16 | 2025-12-18 | Auth + 基础布局 + 导航 |
| Phase 1: Data Layer | ✅ Completed | 2025-12-16 | 2025-12-20 | 税表、模型、服务层全部完成 |
| Phase 2: Calculations | ✅ Completed | 2025-12-20 | 2025-12-26 | CPP/EI/Federal/Provincial + Engine 全部完成 |
| Phase 3: Paystub | ✅ Completed | 2025-12-28 | 2025-12-29 | PDF Generator + Data Builder + DO Spaces Storage |
| Phase 4: API & Integration | ✅ Completed | 2025-12-16 | 2026-01-02 | API + Service + Frontend UI 全部完成 |
| Phase 5: Testing | ✅ Completed | 2025-12-29 | 2025-12-31 | **2300+ tests, CRA-compliant validated** - 160+ PDOC validation cases |
| Phase 6: Year-End | ✅ ~95% Done | 2025-12-31 | 2026-01-02 | T4 完整实现 (Models/PDF/XML/API/UI) |
| Phase 7: Compliance | 🔄 ~70% Done | 2025-12-31 | 2026-01-02 | Remittance 完整实现，ROE 未开始 |
| Phase 8: Gov Submission (Future) | ⬜ Not Started | | | Enterprise auto-submission (WAC/ROE Web) |

**Status Legend**: ⬜ Not Started | 🔄 In Progress | ✅ Completed | ⚠️ Blocked

---

## 🏗️ Architecture Update (2025-12-16)

采用**混合架构**：简单 CRUD 直连 Supabase，复杂计算走 FastAPI。

详见 [00_architecture_overview.md](./00_architecture_overview.md)

### 额外实现 (超出原计划)

以下内容已实现但未在原 checklist 中列出：

#### Phase 1 额外实现
- ✅ **companies 表** - 公司信息、CRA 汇款配置
- ✅ **pay_groups 表** - 薪资组政策模板
- ✅ **Company/PayGroup Pydantic models** - 后端模型
- ✅ **company.ts / pay-group.ts** - 前端类型
- ✅ **companyService.ts / payGroupService.ts** - 前端服务
- ✅ **payroll/ 服务模块重构** (2025-12-18) - 将 payrollService.ts (1155行) 拆分为模块化结构:
  - `payroll/index.ts` - 统一导出
  - `payroll/types.ts` - 类型定义
  - `payroll/helpers.ts` - 工具函数
  - `payroll/dashboard.ts` - 仪表板/状态检查
  - `payroll/payroll-runs.ts` - 薪资运行 CRUD
  - `payroll/pay-groups.ts` - 薪资组查询
  - `payroll/calculation.ts` - 薪资计算 (调用后端 API)
- ✅ **2026 税表配置** (2025-12-26) - 提前配置下一年税表:
  - `backend/config/tax_tables/2026/cpp_ei.json`
  - `backend/config/tax_tables/2026/federal_jan.json`
  - `backend/config/tax_tables/2026/provinces.json`

#### Phase 3 额外实现 (2025-12-28 ~ 2025-12-29)
- ✅ **paystub_generator.py** - PDF Paystub 生成器:
  - ReportLab PDF generation
  - 员工信息、收入、扣款、YTD 汇总
  - 省份特定显示 (Ontario vacation, BC employer contributions)
- ✅ **paystub_data_builder.py** - Paystub 数据构建器:
  - 从 PayrollRecord 构建 PaystubData
  - 收入/扣款行项目格式化
  - YTD 累计计算
- ✅ **paystub_storage.py** - DO Spaces 存储:
  - `save_paystub()` - 上传到 DigitalOcean Spaces
  - `get_download_url()` - Pre-signed URL (15 min)
  - `list_paystubs_for_employee()`
  - `delete_paystub()` / `paystub_exists()`

#### Phase 4 额外实现 (部分完成)
- ✅ **payroll_run_service.py** (2025-12-27) - Payroll run 生命周期管理:
  - `_get_prior_ytd_for_employees()` - 查询历史 YTD
  - Record updates in draft state
  - Recalculation of payroll deductions
  - Status transitions (draft -> pending_approval)
- ✅ **api/v1/payroll.py** (2025-12-26) - 薪资计算 REST API:
  - `EmployeeCalculationRequest` / `CalculationResponse` models
  - `BatchCalculationRequest` model
  - POST `/payroll/calculate` endpoint
  - Full earnings/deductions/YTD support

#### Sick Leave 功能 (2025-12-29 新增)
- ✅ **sick_leave_service.py** - 病假计算服务:
  - `SickLeaveService` class
  - `SickLeaveConfig` / `SickLeaveBalance` models
  - `calculate_sick_pay()` - 病假工资计算
  - `calculate_average_day_pay()` - 平均日薪计算
  - `DEFAULT_SICK_LEAVE_CONFIGS` - 各省默认配置
- ✅ **sick_leave_config_loader.py** - 病假配置加载器:
  - `get_sick_leave_config()` - 获取省份配置
  - `get_provinces_with_paid_sick_leave()` - 有带薪病假的省份
  - `get_provinces_with_sick_leave_carryover()` - 支持病假结转的省份
- ✅ **sick-leave.ts** - 前端类型定义
- ✅ **migration** - 数据库迁移 (待应用)

#### T4 年终报表完整实现 (2025-12-31 ~ 2026-01-02 新增)
- ✅ **backend/app/models/t4.py** - T4 数据模型:
  - `T4SlipData` - 所有 CRA T4 boxes (14, 16, 17, 18, 20, 22, 24, 26, 44, 46, 52)
  - `T4SlipRecord` - 数据库记录，含状态跟踪、PDF 存储、amendment 支持
  - `T4Summary` - 雇主汇总数据
  - `T4Status` enum - draft, generated, amended, filed
- ✅ **backend/app/services/t4/** - T4 服务模块:
  - `aggregation_service.py` - 从已批准的 payroll runs 聚合年度数据
  - `pdf_generator.py` - 生成专业 T4 PDF (ReportLab)
  - `xml_generator.py` - 生成 CRA T619 XML 格式 (v1.4)
  - `storage_service.py` - DO Spaces 存储
- ✅ **backend/app/api/v1/t4.py** - 完整 REST API
- ✅ **frontend/src/lib/types/t4.ts** - TypeScript 类型
- ✅ **frontend/src/lib/services/t4Service.ts** - 前端服务
- ✅ **frontend/src/routes/(app)/reports/t4/+page.svelte** - T4 UI 页面
- ✅ **20260101100000_add_t4_tables.sql** - 数据库迁移

#### Remittance 完整实现 (2025-12-31 ~ 2026-01-02 新增)
- ✅ **backend/app/models/remittance.py** - Remittance 模型:
  - `PaymentMethod` enum (5 种支付方式)
  - `PD7ARemittanceVoucher` 模型，含计算字段
- ✅ **backend/app/services/remittance/** - Remittance 服务模块:
  - `period_service.py` - 自动创建/聚合 remittance periods
  - `period_calculator.py` - 期间边界和到期日计算
  - `pd7a_generator.py` - PD7A Statement of Account PDF
- ✅ **backend/app/api/v1/remittance.py** - PD7A 下载 API
- ✅ **frontend/src/lib/types/remittance.ts** - 前端类型
- ✅ **frontend/src/lib/services/remittanceService.ts** - 前端服务
- ✅ **frontend/src/routes/(app)/remittance/+page.svelte** - Remittance UI 页面:
  - Year selector, Upcoming Remittance card (overdue/due soon states)
  - Summary cards (YTD, Completed, On-Time Rate, Pending)
  - Remittance History table with expandable rows
  - MarkAsPaidModal component, PD7A PDF download
- ✅ **20251231240000_create_remittance_periods.sql** - 数据库迁移

---

## Phase 0: Standalone Frontend Setup (1 week)

### Task 0.1: Create Payroll Frontend Project

- [ ] **Task 0.1.1**: Initialize SvelteKit project
  - [ ] Create `payroll-frontend/` directory
  - [ ] Run `npm create svelte@latest .`
  - [ ] Choose: Skeleton project, TypeScript, ESLint, Prettier
  - [ ] Install dependencies: `npm install`

- [ ] **Task 0.1.2**: Configure Tailwind CSS
  - [ ] Install: `npm install -D tailwindcss postcss autoprefixer`
  - [ ] Run: `npx tailwindcss init -p`
  - [ ] Configure `tailwind.config.js` to extend shared config
  - [ ] Import design system in `app.css`

- [ ] **Task 0.1.3**: Set up shared resources
  - [ ] Create symlinks to shared design system
  - [ ] Create symlinks to shared base components
  - [ ] Create symlinks to shared icons
  - [ ] Test that shared styles work

### Task 0.2: Create Base Layout

- [ ] **Task 0.2.1**: Create root layout
  - [ ] Create `src/routes/+layout.svelte`
  - [ ] Create `src/routes/+layout.ts`
  - [ ] Import design system CSS

- [ ] **Task 0.2.2**: Create app shell layout
  - [ ] Create `src/lib/components/layout/AppShell.svelte`
  - [ ] Create `src/lib/components/layout/Sidebar.svelte`
  - [ ] Create `src/lib/components/layout/Header.svelte`
  - [ ] Create navigation items config

- [ ] **Task 0.2.3**: Create authenticated layout
  - [ ] Create `src/routes/(app)/+layout.svelte`
  - [ ] Create `src/routes/(app)/+layout.ts` (auth guard)

### Task 0.3: Implement Authentication

- [ ] **Task 0.3.1**: Set up Supabase client
  - [ ] Install: `npm install @supabase/supabase-js`
  - [ ] Create `src/lib/api/supabase.ts`
  - [ ] Configure environment variables

- [ ] **Task 0.3.2**: Create auth pages
  - [ ] Create `src/routes/(auth)/login/+page.svelte`
  - [ ] Create `src/routes/(auth)/callback/+page.svelte`
  - [ ] Implement Google OAuth flow

- [ ] **Task 0.3.3**: Create auth store
  - [ ] Create `src/lib/stores/auth.ts`
  - [ ] Implement session management
  - [ ] Add auth guard logic

### Task 0.4: Create Basic Routes

- [ ] **Task 0.4.1**: Create placeholder pages
  - [ ] Create `src/routes/(app)/dashboard/+page.svelte`
  - [ ] Create `src/routes/(app)/employees/+page.svelte`
  - [ ] Create `src/routes/(app)/payroll/+page.svelte`
  - [ ] Create `src/routes/(app)/reports/+page.svelte`
  - [ ] Create `src/routes/(app)/settings/+page.svelte`

- [ ] **Task 0.4.2**: Create API client
  - [ ] Create `src/lib/api/client.ts`
  - [ ] Configure base URL and auth headers
  - [ ] Create error handling utilities

### Task 0.5: Backend CORS Update

- [ ] **Task 0.5.1**: Update CORS configuration
  - [ ] Add `payroll.beanflow.com` to allowed origins
  - [ ] Add `localhost:5174` for development
  - [ ] Test cross-origin requests

- [ ] **Task 0.5.2**: Add feature flags
  - [ ] Add `has_payroll_access` column to users table
  - [ ] Create migration for feature flag
  - [ ] Test feature flag in auth flow

**Validation (Phase 0)**:
- [ ] Payroll frontend runs on port 5174
- [ ] Shared design system styles apply correctly
- [ ] Google OAuth login works
- [ ] Auth guard redirects unauthenticated users
- [ ] Navigation between pages works
- [ ] API client can reach backend

---

## Phase 1: Data Layer & Tax Tables (2 weeks)

### Week 1: Supabase Database Schema (NEW)

- [x] **Task 1.0.1**: Create Supabase migration for payroll tables ✅
  - [x] Create migration file: `backend/supabase/migrations/20251216_create_payroll_tables.sql`
  - [x] Create `employees` table:
    - [x] Basic fields (id, user_id, ledger_id, names)
    - [x] SIN encrypted storage
    - [x] Employment details (province, pay_frequency)
    - [x] TD1 claim amounts
    - [x] Exemption flags (cpp, ei, cpp2)
    - [x] Vacation config (JSONB)
    - [x] Timestamps
    - [x] Indexes (user_ledger, province, active)
  - [x] Create `payroll_runs` table:
    - [x] Period info (start, end, pay_date)
    - [x] Status enum (draft, calculating, pending_approval, approved, paid)
    - [x] Summary totals (all deduction types)
    - [x] Beancount transaction IDs array
    - [x] Approval tracking
    - [x] Timestamps
  - [x] Create `payroll_records` table:
    - [x] Foreign keys (payroll_run_id, employee_id)
    - [x] Earnings fields
    - [x] Deduction fields
    - [x] Generated columns (total_gross, total_deductions, net_pay)
    - [x] YTD snapshot fields
    - [x] Vacation tracking
    - [x] Paystub storage key
  - [x] Add RLS policies for all tables
  - [x] Add updated_at triggers

- [ ] **Task 1.0.2**: Apply and verify migration
  - [ ] Run `supabase db push` or `supabase migration up`
  - [ ] Verify tables exist in database
  - [ ] Verify RLS is enabled
  - [ ] Verify generated columns work

### Week 1: Data Access Layer

> **架构决策 (2025-12-16)**: 采用混合架构，简单 CRUD 使用前端直连 Supabase，
> 复杂逻辑使用 FastAPI。因此 Backend Repository 层改为前端 Service 层。

- [x] **Task 1.1.1**: Create Employee Service (前端) ✅ ~~Repository~~
  - [x] Create `frontend/src/lib/services/employeeService.ts`:
    - [x] `createEmployee()` - Insert with multi-tenancy
    - [x] `getEmployee()` - Single fetch
    - [x] `listEmployees()` - With filters (active, province)
    - [x] `updateEmployee()` - Partial update
    - [x] `terminateEmployee()` - Soft delete
    - [x] `getEmployeeCount()` - Count query

- [x] **Task 1.1.2**: Create Company Service (前端) ✅ (额外)
  - [x] Create `frontend/src/lib/services/companyService.ts`:
    - [x] `createCompany()`
    - [x] `getCompany()`
    - [x] `listCompanies()`
    - [x] `updateCompany()`
    - [x] `deleteCompany()`

- [x] **Task 1.1.3**: Create Pay Group Service (前端) ✅ (额外)
  - [x] Create `frontend/src/lib/services/payGroupService.ts`:
    - [x] `createPayGroup()`
    - [x] `getPayGroup()`
    - [x] `listPayGroups()`
    - [x] `updatePayGroup()`
    - [x] `deletePayGroup()`
    - [x] `getMatchingPayGroups()`

### Week 2: Tax Tables

> **实现说明**: 采用 JSON 配置 + Python 加载器分离架构，更易于年度更新维护。

- [x] **Task 1.2.1**: Create Tax Tables (JSON + Python 分离架构) ✅
  - [x] Create `backend/config/tax_tables/2025/federal.json`:
    - [x] BPAF = $16,129
    - [x] CEA = $1,471
    - [x] 5 brackets from T4127 Table 8.1
  - [x] Create `backend/config/tax_tables/2025/cpp_ei.json`:
    - [x] YMPE = $71,300
    - [x] YAMPE = $81,200
    - [x] Basic exemption = $3,500
    - [x] Rate = 5.95%
    - [x] Additional rate = 4%
    - [x] MIE = $65,700 (2025 实际值)
    - [x] Employee rate = 1.64% (2025 实际值)
    - [x] Employer multiplier = 1.4x
  - [x] Create `backend/config/tax_tables/2025/provinces.json`:
    - [x] AB (Alberta) - 6 brackets
    - [x] BC (British Columbia) - 7 brackets
    - [x] MB (Manitoba) - 3 brackets + dynamic BPA
    - [x] NB (New Brunswick) - 4 brackets
    - [x] NL (Newfoundland) - 8 brackets
    - [x] NS (Nova Scotia) - 5 brackets + dynamic BPA
    - [x] NT (Northwest Territories) - 4 brackets
    - [x] NU (Nunavut) - 4 brackets
    - [x] ON (Ontario) - 5 brackets + surtax/health premium
    - [x] PE (Prince Edward Island) - 5 brackets
    - [x] SK (Saskatchewan) - 3 brackets
    - [x] YT (Yukon) - 5 brackets + dynamic BPA
  - [x] Create `backend/app/services/payroll/tax_tables.py`:
    - [x] `load_federal_config()`
    - [x] `load_cpp_config()` / `load_ei_config()`
    - [x] `load_province_config()` / `load_all_provinces()`
    - [x] `find_tax_bracket()`
    - [x] `calculate_dynamic_bpa()` (MB, NS, YT)
    - [x] `validate_tax_tables()`

### Week 2: Data Models

- [x] **Task 1.3.1**: Create `backend/app/models/payroll.py` ✅
  - [x] Create Province enum (12 values, exclude QC)
  - [x] Create PayFrequency enum with `periods_per_year` property
  - [x] Create PayrollRunStatus enum
  - [x] Create EmploymentType enum (full_time, part_time, contract, casual)
  - [x] Create VacationPayoutMethod enum
  - [x] Create VacationConfig model
  - [x] Create Employee models (Base, Create, Update, Response)
  - [x] Create PayrollRun models (Base, Create, Response)
  - [x] Create PayrollRecord model
  - [x] Create PayrollCalculationRequest model
  - [x] Create PayrollCalculationResult model
  - [x] (额外) Create Company models (Base, Create, Update)
  - [x] (额外) Create PayGroup models + policy sub-models

- [x] **Task 1.3.2**: Create Frontend TypeScript Types ✅ (提前完成)
  - [x] Create `frontend/src/lib/types/employee.ts`
  - [x] Create `frontend/src/lib/types/payroll.ts`
  - [x] Create `frontend/src/lib/types/company.ts`
  - [x] Create `frontend/src/lib/types/pay-group.ts`

**Validation:**
- [ ] Migration applies without errors
- [ ] RLS policies working
- [x] Frontend services work (manual test)
- [x] All 12 provinces in config
- [x] Tax tables validate on import
- [x] Pydantic models pass type checking

---

## Phase 2: Core Calculation Engine (3 weeks) ✅ COMPLETED

### Week 3: CPP & EI Calculators

- [x] **Task 2.1.1**: Create `backend/app/services/payroll/cpp_calculator.py` ✅
  - [x] Create CPPCalculator class
  - [x] Implement `calculate_base_cpp()`:
    - [x] Apply $3,500 basic exemption
    - [x] Calculate at 5.95% rate
    - [x] Check annual maximum ($4,034.10)
    - [x] Handle YTD tracking
  - [x] Implement `calculate_additional_cpp()` (CPP2):
    - [x] Only for income above YMPE ($71,300)
    - [x] Calculate at 4% rate
    - [x] Up to YAMPE ($81,200)
    - [x] Max CPP2: $396.00
  - [x] Implement `get_employer_contribution()` (equals employee)
  - [x] (额外) CPP Enhancement F2 calculation (1% deductible from taxable income)
  - [x] (额外) CPP2 exemption support (CPT30 form)

- [x] **Task 2.1.2**: Create `backend/app/services/payroll/ei_calculator.py` ✅
  - [x] Create EICalculator class
  - [x] Implement `calculate_ei_premium()`:
    - [x] Apply 1.64% rate (2025)
    - [x] Check MIE limit ($65,700)
    - [x] Check maximum premium ($1,077.48)
    - [x] Handle YTD tracking
  - [x] Implement `get_employer_premium()` (1.4x employee = $1,508.47 max)

### Week 4-5: Tax Calculators

- [x] **Task 2.2.1**: Create `backend/app/services/payroll/federal_tax_calculator.py` ✅
  - [x] Create FederalTaxCalculator class
  - [x] Implement `calculate_annual_taxable_income()` (Factor A)
  - [x] Implement tax credit calculations:
    - [x] K1: Personal tax credit (based on TD1)
    - [x] K2: CPP/EI tax credit (uses 4.95% rate)
    - [x] K4: Canada Employment Amount credit
  - [x] Implement `calculate_federal_tax()` using T4127 formula: T3 = (R × A) - K - K1 - K2 - K3 - K4
  - [x] (额外) Support 2025-07-01 federal rate change (15% → 14%)
  - [x] (额外) CPP2 and CPP Enhancement (F2) deductions from taxable income

- [x] **Task 2.2.2**: Create `backend/app/services/payroll/provincial_tax_calculator.py` ✅
  - [x] Create ProvincialTaxCalculator class
  - [x] Implement `get_basic_personal_amount()` (static + dynamic for MB, NS, YT)
  - [x] Implement provincial credit calculations (K1P, K2P)
  - [x] Implement `calculate_provincial_tax()` for all 12 provinces
  - [x] Handle Ontario surtax (V1: 20%, 36%) + health premium (V2: up to $900)
  - [x] Handle BC tax reduction (Factor S: $521 base)
  - [x] Handle Alberta K5P supplementary credit

### Week 5: Payroll Engine

- [x] **Task 2.3.1**: Create `backend/app/services/payroll/payroll_engine.py` ✅
  - [x] Create PayrollEngine class
  - [x] Implement `calculate_payroll()`:
    - [x] Orchestrate all calculators (CPP → EI → Federal Tax → Provincial Tax)
    - [x] Handle exemptions (CPP, EI, CPP2)
    - [x] Calculate net pay
    - [x] Build PayrollCalculationResult object
  - [x] (额外) EmployeePayrollInput model with full earnings/deductions support
  - [x] (额外) Taxable benefits support
  - [x] (额外) Pre-tax deductions (RRSP, union dues)
  - [x] (额外) Post-tax deductions (garnishments)
  - [x] (额外) YTD tracking and updates
  - [x] (额外) Employer costs calculation
  - [x] (额外) Calculator caching for performance

**Validation:**
- [ ] CPP matches PDOC for test cases (待测试)
- [ ] EI matches PDOC for test cases (待测试)
- [ ] Federal tax matches PDOC (待测试)
- [ ] Provincial tax matches for all 12 provinces (待测试)
- [x] Payroll engine produces correct totals (代码完成，待 PDOC 验证)

---

## Phase 3: Paystub Generation (1.5 weeks) ✅ COMPLETED

### Week 6: PDF Generation & Storage

- [x] **Task 3.1.1**: Add dependencies ✅
  - [x] Run `uv add reportlab`
  - [x] Run `uv sync`

- [x] **Task 3.1.2**: Create `backend/app/services/payroll/paystub_generator.py` ✅
  - [x] Create PaystubGenerator class
  - [x] Implement `generate_paystub_bytes()`:
    - [x] Header section (employer name)
    - [x] Employee info section
    - [x] Earnings table
    - [x] Deductions table
    - [x] Summary (net pay)
    - [x] YTD totals
    - [x] Vacation section (Ontario)
    - [x] Employer contributions (BC)
    - [x] Footer
  - [x] Implement `generate_paystub_file()` (optional)

- [x] **Task 3.1.3**: Create `backend/app/services/payroll/paystub_storage.py` ✅
  - [x] Create PaystubStorage class (DO Spaces)
  - [x] Implement `_build_storage_key()` - Path pattern
  - [x] Implement `save_paystub()` - Upload to DO Spaces
  - [x] Implement `get_download_url()` - Pre-signed URL (15 min)
  - [x] Implement `list_paystubs_for_employee()`
  - [x] Implement `delete_paystub()`
  - [x] Implement `paystub_exists()`

- [x] **Task 3.1.4**: Create `backend/app/services/payroll/paystub_data_builder.py` ✅ (额外)
  - [x] Create PaystubDataBuilder class
  - [x] Implement `build_from_record()` - 从 PayrollRecord 构建数据
  - [x] Implement earnings/deductions line items formatting
  - [x] Implement YTD calculations

**Validation:**
- [x] PDF generates without errors
- [x] All mandatory fields present
- [x] Numbers formatted correctly ($X,XXX.XX)
- [x] SIN masked (***-***-XXX)
- [x] Upload to DO Spaces works
- [x] Pre-signed URLs work
- [x] Can list paystubs by employee/year

---

## Phase 4: API & Integration (2 weeks) ✅ ~95% COMPLETED

> **架构说明**: 根据混合架构决策，Employee CRUD 使用前端直连 Supabase，
> 复杂的薪资计算和 Payroll Run 管理使用后端 API。

### Week 7: Service Layer

- [x] **Task 4.0.1**: Create `backend/app/services/payroll/__init__.py` ✅
  - [x] Export PayrollEngine, EmployeePayrollInput, PayrollCalculationResult
  - [x] Export all calculator classes
  - [x] Export tax_tables functions

- [x] **Task 4.0.2**: Employee CRUD ✅ (前端直连 Supabase)
  - [x] `frontend/src/lib/services/employeeService.ts`:
    - [x] `listEmployees()` - 列出员工 (带分页/筛选)
    - [x] `getEmployee()` - 获取单个员工
    - [x] `createEmployee()` - 创建员工
    - [x] `updateEmployee()` - 更新员工
    - [x] `terminateEmployee()` - 终止员工 (软删除)
    - [x] `getEmployeeCount()` - 统计数量
    - [x] `maskSin()` - SIN 掩码显示

- [x] **Task 4.0.3**: Create `backend/app/services/payroll_run_service.py` ✅ (1389行)
  - [x] Create PayrollRunService class
  - [x] Implement `get_run()` - 获取单个 run
  - [x] Implement `get_run_records()` - 获取 run 的所有记录
  - [x] Implement `create_or_get_run()` - 创建或获取 draft run
  - [x] Implement `update_record()` - 更新 draft 记录的 input_data
  - [x] Implement `recalculate_run()` - 重新计算整个 run
  - [x] Implement `finalize_run()` - draft → pending_approval
  - [x] Implement `sync_employees()` - 同步新员工到 run
  - [x] Implement `add_employee_to_run()` - 添加单个员工
  - [x] Implement `remove_employee_from_run()` - 移除员工
  - [x] Implement `delete_run()` - 删除 draft run
  - [x] Implement `_get_prior_ytd_for_employees()` - 历史 YTD 查询
  - [x] Implement `_calculate_taxable_benefits()` - 应税福利计算
  - [x] Implement `_calculate_benefits_deduction()` - 员工福利扣款
  - [x] Implement `_calculate_gross_from_input()` - 从 input_data 计算工资
  - [x] Implement `approve_payroll_run()` - 批准 run ✅ (runs.py:536, run_operations.py:477)
  - [x] Implement `get_remittance_summary()` - 汇款摘要 ✅ (通过 RemittancePeriodService 实现)

### Week 7: Backend API

- [x] **Task 4.1.1**: Create `backend/app/api/v1/payroll.py` ✅ (1027行)
  - [x] Create request/response models (camelCase):
    - [x] EmployeeCalculationRequest / CalculationResponse
    - [x] BatchCalculationRequest / BatchCalculationResponse
    - [x] PayrollRunResponse / PayrollRecordResponse
    - [x] UpdatePayrollRecordRequest (含 LeaveEntry, HolidayWork, Adjustment, Overrides)
    - [x] CreateOrGetRunRequest / CreateOrGetRunResponse
    - [x] SyncEmployeesResponse / AddEmployeeRequest / RemoveEmployeeResponse
  - [x] ~~Employee endpoints~~ (N/A - 使用前端 employeeService.ts 直连 Supabase)
  - [x] Payroll calculation endpoints:
    - [x] POST `/payroll/calculate` - 单员工计算 ✅
    - [x] POST `/payroll/calculate/batch` - 批量计算 ✅
    - [x] GET `/payroll/tax-config/{province}` - 省份税务配置 ✅
    - [x] GET `/payroll/tax-config` - 所有税务配置 ✅
  - [x] Payroll run endpoints:
    - [x] POST `/payroll/runs/create-or-get` - 创建或获取 run ✅
    - [x] PATCH `/payroll/runs/{id}/records/{record_id}` - 更新记录 ✅
    - [x] POST `/payroll/runs/{id}/recalculate` - 重新计算 ✅
    - [x] POST `/payroll/runs/{id}/sync-employees` - 同步员工 ✅
    - [x] POST `/payroll/runs/{id}/employees` - 添加员工 ✅
    - [x] DELETE `/payroll/runs/{id}/employees/{employee_id}` - 移除员工 ✅
    - [x] DELETE `/payroll/runs/{id}` - 删除 run ✅
    - [x] POST `/payroll/runs/{id}/finalize` - 完成 run ✅
    - [x] POST `/payroll/runs/{id}/approve` - 批准 run ✅ (runs.py:536)
    - [x] GET `/payroll/runs` - 列出 runs ✅ (前端直查 Supabase)
    - [x] GET `/payroll/runs/{id}` - 获取详情 ✅ (前端直查 Supabase)
  - [x] Paystub endpoints ✅:
    - [x] GET `/payroll/records/{record_id}/paystub-url` - Download URL ✅ (paystubs.py:74)
    - [x] POST `/payroll/runs/{run_id}/send-paystubs` - Send emails ✅ (paystubs.py:29)
  - [x] Remittance endpoints ✅:
    - [x] GET `/remittance/pd7a/{company_id}/{remittance_id}` - PD7A PDF ✅ (remittance.py)
  - [ ] Stats endpoint (Future):
    - [ ] GET `/payroll/stats` - Dashboard stats
  - [x] Register router in `__init__.py` ✅

- [ ] **Task 4.1.2**: Create encryption utility (Optional - SIN 当前存储为明文)
  - [ ] Create `backend/app/core/encryption.py`
  - [ ] Add ENCRYPTION_KEY to config

### Week 8: Frontend & Beancount

- [x] **Task 4.2.1**: Create TypeScript types ✅
  - [x] `frontend/src/lib/types/employee.ts` - Employee 类型
  - [x] `frontend/src/lib/types/payroll.ts` - PayrollRun, PayrollRecord 类型
  - [x] `frontend/src/lib/types/company.ts` - Company 类型
  - [x] `frontend/src/lib/types/pay-group.ts` - PayGroup 类型
  - [x] `frontend/src/lib/types/remittance.ts` - Remittance 类型

- [x] **Task 4.2.2**: Create Payroll Service (模块化) ✅
  - [x] `frontend/src/lib/services/payroll/index.ts` - 统一导出
  - [x] `frontend/src/lib/services/payroll/types.ts` - 类型定义
  - [x] `frontend/src/lib/services/payroll/helpers.ts` - 工具函数
  - [x] `frontend/src/lib/services/payroll/dashboard.ts` - 仪表板
  - [x] `frontend/src/lib/services/payroll/payroll-runs.ts` - Run CRUD
  - [x] `frontend/src/lib/services/payroll/pay-groups.ts` - Pay Group 查询
  - [x] `frontend/src/lib/services/payroll/calculation.ts` - 后端 API 调用

- [x] **Task 4.2.3**: Create Employee Management UI ✅
  - [x] `frontend/src/routes/(app)/employees/+page.svelte` - 员工列表
  - [x] `frontend/src/routes/(app)/employees/new/+page.svelte` - 新建员工
  - [x] `frontend/src/routes/(app)/employees/[id]/+page.svelte` - 编辑员工

- [x] **Task 4.2.4**: Create Payroll UI ✅
  - [x] `frontend/src/routes/(app)/payroll/+page.svelte` - Payroll Dashboard
  - [x] `frontend/src/routes/(app)/payroll/run/[periodEnd]/+page.svelte` - Run 详情
  - [x] `frontend/src/routes/(app)/payroll/history/+page.svelte` - 历史记录

- [ ] **Task 4.3.1**: Create Beancount Integration (Future)
  - [ ] Create `backend/app/services/payroll/beancount_integration.py`
  - [ ] `generate_payroll_transaction()`
  - [ ] `generate_employer_costs_transaction()`
  - [ ] `generate_remittance_transaction()`

**Validation:**
- [x] Payroll calculation API responds correctly ✅
- [x] Authentication required (401 without token) ✅
- [x] RLS enforces multi-tenancy ✅
- [x] Frontend displays employee list ✅
- [x] Can add/edit employees via UI ✅
- [x] Payroll run approval workflow works ✅
- [x] Paystub generation and download works ✅
- [x] Remittance period aggregation works ✅
- [ ] Beancount transactions balance (Future)
- [ ] Transactions visible in Fava (Future)

---

## Phase 5: Testing & Validation (1.5 weeks) ✅ ~95% COMPLETED

> **Status Update (2025-12-31)**: 998 tests passing, comprehensive PDOC validation complete

### Week 9: Automated Tests ✅ COMPLETED

- [x] **Task 5.1.1**: CPP Calculator Tests ✅ (28 tests)
  - [x] Test base CPP calculation
  - [x] Test CPP2 (above YMPE)
  - [x] Test annual maximums
  - [x] Test YTD tracking
  - [x] CPP Enhancement F2 calculation

- [x] **Task 5.1.2**: EI Calculator Tests ✅ (28 tests)
  - [x] Test EI premium calculation
  - [x] Test annual maximum
  - [x] Test employer premium

- [x] **Task 5.1.3**: Tax Calculator Tests ✅ (117 tests)
  - [x] Test federal tax (all brackets) - 37 tests
  - [x] Test provincial tax (all 12 provinces) - 80 tests
  - [x] Test dynamic BPA (MB, NS, YT)

- [x] **Task 5.1.4**: Integration Tests ✅ (413+ tests)
  - [x] Test complete payroll calculation - `test_payroll_engine.py` (25 tests)
  - [x] Test matrix coverage - `test_matrix.py` (308 tests)
  - [x] Test all provinces - `test_all_provinces.py` (105 tests)
  - [x] Test edge cases - `test_edge_cases.py` (23 tests)
  - [x] Test YTD calculator - `test_ytd_calculator.py` (11 tests)

- [x] **Task 5.1.5**: API Tests ✅ (102 tests) (额外)
  - [x] `test_payroll_runs.py` - 28 tests
  - [x] `test_payroll_records.py` - 17 tests
  - [x] `test_payroll_calculation.py` - 16 tests
  - [x] `test_payroll_config.py` - 17 tests
  - [x] `test_paystubs.py` - 10 tests
  - [x] `test_sick_leave.py` - 14 tests

- [x] **Task 5.1.6**: Domain-Specific Tests ✅ (106 tests) (额外)
  - [x] `test_holiday_pay_calculator.py` - 54 tests
  - [x] `test_sick_leave_service.py` - 38 tests
  - [x] Holiday pay tier1 major provinces - 14 tests

### Week 10: PDOC Validation ✅ COMPLETED

- [x] **Task 5.2.1**: CRA PDOC Validation ✅ (144 tests)
  - [x] **Tier 1**: Province Coverage (39 tests) - All 12 provinces verified
  - [x] **Tier 2**: Income Levels (38 tests) - Low/mid/high income scenarios
  - [x] **Tier 3**: CPP/EI Boundary (25 tests) - YMPE, MIE, maximums
  - [x] **Tier 4**: Special Conditions (28 tests) - RRSP, union dues, exemptions
  - [x] **Tier 5**: Federal Rate Change (14 tests) - Jan (15%) vs Jul (14%) editions
  - [x] All test cases within $0.05 variance tolerance ✅
  - [x] Jan edition fixtures (120th Edition, 15% rate)
  - [x] Jul edition fixtures (121st Edition, 14% rate)

- [x] **Task 5.2.2**: Final Quality Checks ✅
  - [x] Backend: ruff check pass (0 errors) ✅
  - [x] Backend: mypy check pass (0 errors) ✅
  - [x] Frontend: svelte-check pass (0 errors, 220 warnings) ✅
  - [x] Run full test suite - **998 passed** ✅
  - [x] Review all error messages ✅

### Test Summary

| Category | Tests | Status |
|----------|-------|--------|
| Unit Tests (CPP/EI/Tax) | 173 | ✅ Passed |
| Integration Tests | 413 | ✅ Passed |
| API Tests | 102 | ✅ Passed |
| PDOC Validation | 144 | ✅ Passed |
| Domain Tests (Holiday/Sick) | 106 | ✅ Passed |
| Other | 60 | ✅ Passed |
| **Total** | **998** | **✅ All Passed** |

**Test Coverage Goal:** > 80% ✅ (comprehensive coverage achieved)

---

## Phase 6: Year-End Processing ✅ ~95% COMPLETED

> **Reference**: See [09_year_end_processing.md](./09_year_end_processing.md) and [16_government_electronic_submission.md](./16_government_electronic_submission.md)

### T4 Generation ✅ COMPLETED

- [x] **Task 6.1**: Create T4 Data Models ✅
  - [x] Implement `T4SlipData` model (all T4 boxes) ✅ (`backend/app/models/t4.py`)
  - [x] Implement `T4Summary` model ✅
  - [x] Implement `T4SlipRecord` model with status tracking ✅
  - [x] Add SIN Luhn algorithm validation ✅ (`backend/app/utils/sin_validator.py`)
  - [x] API request/response models (camelCase) ✅

- [x] **Task 6.2**: Create T4 Aggregation Service ✅
  - [x] Implement `T4AggregationService.aggregate_employee_year()` ✅ (`backend/app/services/t4/aggregation_service.py`)
  - [x] Implement `T4AggregationService.generate_all_t4_slips()` ✅
  - [x] Implement `T4AggregationService.generate_t4_summary()` ✅
  - [x] Query completed payroll runs (approved/paid status) ✅
  - [x] Decrypt employee SIN with Luhn validation ✅

- [x] **Task 6.3**: Create T4 Output Generators ✅
  - [x] Implement T4 PDF generator (ReportLab) ✅ (`backend/app/services/t4/pdf_generator.py`)
  - [x] Implement T4 Summary PDF generator ✅
  - [x] Implement T4 XML generator (T619 schema v1.4) ✅ (`backend/app/services/t4/xml_generator.py`)
  - [x] Currency amounts formatted as cents (per CRA requirement) ✅
  - [x] Implement T4 Storage Service (DO Spaces) ✅ (`backend/app/services/t4/storage_service.py`)

- [x] **Task 6.4**: Create T4 API Endpoints ✅ (`backend/app/api/v1/t4.py`)
  - [x] GET `/t4/slips/{company_id}/{tax_year}` - List all T4 slips ✅
  - [x] POST `/t4/slips/{company_id}/{tax_year}/generate` - Generate T4 slips ✅
  - [x] GET `/t4/slips/{company_id}/{tax_year}/{employee_id}/download` - Download PDF ✅
  - [x] GET `/t4/summary/{company_id}/{tax_year}` - Get summary ✅
  - [x] POST `/t4/summary/{company_id}/{tax_year}/generate` - Generate summary ✅
  - [x] GET `/t4/summary/{company_id}/{tax_year}/download-pdf` - Download summary PDF ✅
  - [x] GET `/t4/summary/{company_id}/{tax_year}/download-xml` - Download CRA XML ✅

- [x] **Task 6.4.5**: Create T4 Database Schema ✅ (`20260101100000_add_t4_tables.sql`)
  - [x] `t4_slips` table with JSONB data, status, PDF storage ✅
  - [x] `t4_summaries` table with aggregated totals ✅
  - [x] RLS policies for multi-tenancy ✅
  - [x] Indexes on company_id, tax_year, employee_id, status ✅

- [x] **Task 6.4.6**: Create T4 Frontend ✅
  - [x] Frontend types (`frontend/src/lib/types/t4.ts`) ✅
  - [x] Frontend service (`frontend/src/lib/services/t4Service.ts`) ✅
  - [x] Frontend UI page (`frontend/src/routes/(app)/reports/t4/+page.svelte`) ✅
  - [x] Tax year selector, slip generation, PDF downloads ✅

### T4 CRA Submission (Phase 6.5 - Enterprise)

> **Note**: CRA does not provide public API. "Automatic" submission requires WAC integration.

- [ ] **Task 6.5**: CRA Submission Support (Future)
  - [ ] Pre-submission XML validation against T619 schema
  - [ ] Deep link to CRA Internet File Transfer portal
  - [ ] Submission status tracking (draft, submitted, accepted)
  - [ ] Store confirmation numbers
  - [ ] (Phase 3 - Enterprise) WAC credential storage and auto-submission

---

## Phase 7: Compliance Features 🔄 ~70% COMPLETED

> **Reference**: See [10_remittance_reporting.md](./10_remittance_reporting.md), [11_roe_generation.md](./11_roe_generation.md), and [16_government_electronic_submission.md](./16_government_electronic_submission.md)

### Remittance Reporting ✅ FULLY COMPLETED

- [x] **Task 7.1**: Create Remittance Models ✅
  - [x] Implement `RemitterType` enum (Quarterly, Regular, Threshold 1, Threshold 2) ✅
  - [x] Implement `PaymentMethod` enum (5 methods) ✅ (`backend/app/models/remittance.py`)
  - [x] Implement `RemittancePeriod` model ✅
  - [x] Implement `PD7ARemittanceVoucher` model with computed fields ✅

- [x] **Task 7.2**: Create Remittance Services ✅
  - [x] Implement `RemittancePeriodService` ✅ (`backend/app/services/remittance/period_service.py`)
  - [x] Implement `period_calculator.py` ✅ (`backend/app/services/remittance/period_calculator.py`)
  - [x] Implement due date calculation for all remitter types ✅
  - [x] Implement period bounds calculation (monthly, quarterly, threshold1) ✅
  - [x] Auto-aggregate deductions from approved payroll runs ✅
  - [ ] THRESHOLD_2 (4x monthly) - partial implementation (falls back to Threshold 1)

- [x] **Task 7.3**: Create PD7A PDF Generator ✅
  - [x] Generate PD7A Statement of Account PDF ✅ (`backend/app/services/remittance/pd7a_generator.py`)
  - [x] Include all line items (CPP, EI, Tax) ✅
  - [x] Professional formatting with ReportLab ✅

- [x] **Task 7.3.5**: Create Remittance Database Schema ✅ (`20251231240000_create_remittance_periods.sql`)
  - [x] `remittance_periods` table with full schema ✅
  - [x] RLS policies for multi-tenancy ✅
  - [x] 9 indexes for performance ✅
  - [x] Trigger for `updated_at` ✅

- [x] **Task 7.3.6**: Create Remittance API ✅ (`backend/app/api/v1/remittance.py`)
  - [x] GET `/remittance/pd7a/{company_id}/{remittance_id}` - Download PD7A PDF ✅

- [x] **Task 7.3.7**: Create Remittance Frontend ✅
  - [x] Frontend types (`frontend/src/lib/types/remittance.ts`) ✅
  - [x] Frontend service (`frontend/src/lib/services/remittanceService.ts`) ✅
  - [x] Penalty calculation helpers ✅
  - [x] **Frontend UI** ✅ (`frontend/src/routes/(app)/remittance/+page.svelte`)
    - [x] Year selector, Upcoming Remittance card (overdue/due soon states)
    - [x] Summary cards (YTD, Completed, On-Time Rate, Pending)
    - [x] Remittance History table with expandable rows
    - [x] MarkAsPaidModal component
    - [x] PD7A PDF download integration

### ROE Generation

- [ ] **Task 7.4**: Create ROE Data Models
  - [ ] Implement `ROEReasonCode` enum (A-Z codes)
  - [ ] Implement `ROEPayPeriod` model
  - [ ] Implement `RecordOfEmployment` model with validation
  - [ ] Test validation logic (comments required for E, K, M, Z)

- [ ] **Task 7.5**: Create ROE Generation Service
  - [ ] Implement insurable earnings calculation (53 weeks lookback)
  - [ ] Implement `generate_roe()` method
  - [ ] Handle vacation pay and other monies
  - [ ] Test with sample payroll data

- [ ] **Task 7.6**: Create ROE Output Generators
  - [ ] Implement ROE XML generator (ROE Web Payroll Extract format)
  - [ ] Generate `.BLK` file extension
  - [ ] Implement ROE PDF generator (employee copy)
  - [ ] Validate against ROE Web schema (XSD)
  - [ ] Test with ROE Web demo site

- [ ] **Task 7.7**: Create ROE API Endpoints
  - [ ] POST `/roe/generate/{ledger_id}/{employee_id}`
  - [ ] GET `/roe/list/{ledger_id}`
  - [ ] GET `/roe/{roe_id}/download-pdf`
  - [ ] GET `/roe/{roe_id}/download-xml`

### ROE Service Canada Submission (Phase 7.5 - Enterprise)

> **Note**: Service Canada provides Payroll Extract batch upload. More integration-friendly than CRA.

- [ ] **Task 7.8**: ROE Web Submission Support
  - [ ] Pre-submission XML validation against ROE Web schema
  - [ ] Deep link to ROE Web Payroll Extract portal
  - [ ] Submission status tracking (draft, submitted, passed, failed)
  - [ ] Serial number import from ROE Web
  - [ ] Amended ROE support
  - [ ] (Phase 3 - Enterprise) ROE Web credential storage and auto-submission

### Garnishment Handling (Future)

- [ ] **Task 7.9**: Create Garnishment Service
  - [ ] Implement garnishment types (federal, provincial, child support)
  - [ ] Implement garnishment calculation
  - [ ] Implement garnishment deduction priority
  - [ ] Add garnishment API endpoints

---

## Phase 8: Government Electronic Submission Summary

> **Reference**: See [16_government_electronic_submission.md](./16_government_electronic_submission.md) for comprehensive documentation.

### Implementation Phases for Government Submissions

| Phase | T4 (CRA) | ROE (Service Canada) | Remittance (CRA) |
|-------|----------|----------------------|------------------|
| **Phase 1 (MVP)** | Generate XML + PDF, manual upload | Generate .BLK + PDF, manual upload | Generate PD7A PDF |
| **Phase 2** | Validate + deep links | Validate + status tracking | Deep links to My Business Account |
| **Phase 3 (Enterprise)** | WAC auto-submission | ROE Web auto-submission | Pre-authorized debit setup |

### Key Technical Requirements

| System | Format | Schema | Deadline |
|--------|--------|--------|----------|
| **CRA T4** | XML (T619) | xmlschm1-25-4 | Feb 28 |
| **ROE Web** | XML (.BLK) | ROE Web v2.0 | 5 days after interruption |
| **PD7A** | PDF | N/A | 15th of following month |

### 2025 Compliance Changes

1. **Electronic Filing Threshold**: > 5 slips must file electronically (as of Jan 2024)
2. **T619 Schema Update**: New format required starting Jan 2025
3. **Single Return Type**: Each CRA submission can only contain one type (e.g., only T4)

---

## 🎯 Project Completion Criteria (MVP)

### Functional Requirements
- [x] Calculates CPP (base + CPP2) correctly ✅
- [x] Calculates EI correctly ✅
- [x] Calculates federal income tax correctly ✅
- [x] Calculates provincial tax for all 12 provinces ✅
- [x] Generates compliant PDF paystubs ✅
- [x] Stores paystubs in DigitalOcean Spaces ✅
- [ ] Integrates with Beancount ledger (Future)
- [x] Supports 4 pay frequencies ✅
- [x] Handles YTD tracking and maximums ✅
- [x] Frontend UI for employee management ✅
- [x] Sick leave calculation (各省规则) ✅ (额外)

### Technical Requirements
- [x] Supabase tables with RLS ✅
- [x] Repository-Service-API pattern ✅
- [x] Type hints on all functions ✅
- [x] Pydantic models for all data ✅
- [x] Decimal type for monetary values ✅
- [x] Svelte 5 Runes syntax ✅
- [x] API documentation (OpenAPI) ✅

### Quality Requirements
- [x] Test coverage > 80% ✅
- [x] Quality checks pass (ruff, mypy - 0 errors) ✅
- [x] PDOC validation passed (variance < $1) ✅
- [ ] No critical bugs

---

## 📊 Risk Register

| Risk | Impact | Mitigation | Status |
|------|--------|------------|--------|
| Tax rate changes | High | Version config file | ⬜ |
| PDOC validation fails | High | Use exact T4127 formulas | ⬜ |
| Province-specific bugs | Medium | Test all 12 provinces | ⬜ |
| Decimal rounding errors | Medium | Use Python Decimal | ⬜ |
| DO Spaces connectivity | Low | Use pre-signed URLs | ⬜ |

---

## 📝 Notes & Decisions

**Key Decisions**:
1. Using T4127 Option 1 (annual tax method)
2. Excluding Quebec (separate system required)
3. Using Supabase PostgreSQL (not Firestore)
4. Using DigitalOcean Spaces (not Google Drive)
5. Using Svelte 5 Runes syntax
6. Using Repository-Service-API pattern
7. Encrypting SIN at rest

**Architecture References**:
- Invoice system (similar pattern)
- Document files (DO Spaces storage)
- Company info (Supabase + RLS)

---

## 🎉 Sign-Off

- [x] **Phase 1 Complete** - Date: 2025-12-20
- [x] **Phase 2 Complete** - Date: 2025-12-26
- [x] **Phase 3 Complete** - Date: 2025-12-29
- [x] **Phase 4 Complete** - Date: 2026-01-02 ✅ (approve_payroll_run + paystub download)
- [x] **Phase 5 Complete** - Date: 2025-12-31 - **998 tests passed** ✅
- [x] **Phase 6 Complete (~95%)** - Date: 2026-01-02 ✅ (T4 完整实现，仅缺 CRA WAC 提交)
- [x] **Phase 7 Partial (~70%)** - Date: 2026-01-02 - Remittance 完整实现，仅缺 ROE
- [ ] **MVP COMPLETE** - Signed: _______ Date: _______ (待 ROE 实现)

---

**Estimated Duration**: 8-10 weeks (MVP)
**Extended Scope**: +4 weeks (T4, ROE, Garnishments)
