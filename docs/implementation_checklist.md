# Canadian Payroll Implementation - Master Checklist

**Project**: BeanFlow Payroll (Standalone Product)
**Scope**: All provinces/territories except Quebec
**Timeline**: 8-10 weeks

> **Last Updated**: 2025-12-18
> **Architecture Version**: v3.2 (Standalone Product)

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
| **Phase 0: Frontend Setup** | 🔄 In Progress | 2025-12-16 | | Auth + 基础布局已完成 |
| Phase 1: Data Layer | 🔄 In Progress | 2025-12-16 | | ~70% 完成 (见下方详情) |
| Phase 2: Calculations | ⬜ Not Started | | | CPP/EI/Tax calculators |
| Phase 3: Paystub | ⬜ Not Started | | | PDF + DO Spaces storage |
| Phase 4: API & Integration | 🔄 In Progress | 2025-12-16 | | 前端类型和服务已完成 |
| Phase 5: Testing | ⬜ Not Started | | | Unit + Integration + PDOC |
| Phase 6: Year-End (Future) | ⬜ Not Started | | | T4 generation |
| Phase 7: Compliance (Future) | ⬜ Not Started | | | ROE, Remittance |

**Status Legend**: ⬜ Not Started | 🔄 In Progress | ✅ Completed | ⚠️ Blocked

---

## 🏗️ Architecture Update (2025-12-16)

采用**混合架构**：简单 CRUD 直连 Supabase，复杂计算走 FastAPI。

详见 [00_architecture_overview.md](./00_architecture_overview.md)

### 额外实现 (超出原计划)

以下内容已实现但未在原 checklist 中列出：

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
    - [x] YMPE = $71,200
    - [x] YAMPE = $76,000
    - [x] Basic exemption = $3,500
    - [x] Rate = 5.95%
    - [x] Additional rate = 1%
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

## Phase 2: Core Calculation Engine (3 weeks)

### Week 3: CPP & EI Calculators

- [ ] **Task 2.1.1**: Create `backend/app/services/payroll/cpp_calculator.py`
  - [ ] Create CPPCalculator class
  - [ ] Implement `calculate_base_cpp()`:
    - [ ] Apply $3,500 basic exemption
    - [ ] Calculate at 5.95% rate
    - [ ] Check annual maximum
    - [ ] Handle YTD tracking
  - [ ] Implement `calculate_additional_cpp()` (CPP2):
    - [ ] Only for income above YMPE
    - [ ] Calculate at 1% rate
    - [ ] Up to YAMPE
  - [ ] Implement `get_employer_contribution()` (equals employee)

- [ ] **Task 2.1.2**: Create `backend/app/services/payroll/ei_calculator.py`
  - [ ] Create EICalculator class
  - [ ] Implement `calculate_ei_premium()`:
    - [ ] Apply 1.70% rate
    - [ ] Check MIE limit
    - [ ] Check maximum premium
    - [ ] Handle YTD tracking
  - [ ] Implement `get_employer_premium()` (1.4x employee)

### Week 4-5: Tax Calculators

- [ ] **Task 2.2.1**: Create `backend/app/services/payroll/federal_tax_calculator.py`
  - [ ] Create FederalTaxCalculator class
  - [ ] Implement `calculate_annual_taxable_income()`
  - [ ] Implement tax credit calculations (K1, K2, K4)
  - [ ] Implement `calculate_federal_tax()` using T4127 formula

- [ ] **Task 2.2.2**: Create `backend/app/services/payroll/provincial_tax_calculator.py`
  - [ ] Create ProvincialTaxCalculator class
  - [ ] Implement `get_basic_personal_amount()` (static + dynamic)
  - [ ] Implement provincial credit calculations
  - [ ] Implement `calculate_provincial_tax()`
  - [ ] Handle Ontario surtax/health premium
  - [ ] Handle BC tax reduction
  - [ ] Handle Alberta K5P credit

### Week 5: Payroll Engine

- [ ] **Task 2.3.1**: Create `backend/app/services/payroll/payroll_engine.py`
  - [ ] Create PayrollEngine class
  - [ ] Implement `calculate_payroll()`:
    - [ ] Orchestrate all calculators
    - [ ] Handle exemptions
    - [ ] Calculate net pay
    - [ ] Build result object

**Validation:**
- [ ] CPP matches PDOC for test cases
- [ ] EI matches PDOC for test cases
- [ ] Federal tax matches PDOC
- [ ] Provincial tax matches for all 12 provinces
- [ ] Payroll engine produces correct totals

---

## Phase 3: Paystub Generation (1.5 weeks)

### Week 6: PDF Generation & Storage

- [ ] **Task 3.1.1**: Add dependencies
  - [ ] Run `uv add reportlab`
  - [ ] Run `uv sync`

- [ ] **Task 3.1.2**: Create `backend/app/services/payroll/paystub_generator.py`
  - [ ] Create PaystubGenerator class
  - [ ] Implement `generate_paystub_bytes()`:
    - [ ] Header section (employer name)
    - [ ] Employee info section
    - [ ] Earnings table
    - [ ] Deductions table
    - [ ] Summary (net pay)
    - [ ] YTD totals
    - [ ] Vacation section (Ontario)
    - [ ] Employer contributions (BC)
    - [ ] Footer
  - [ ] Implement `generate_paystub_file()` (optional)

- [ ] **Task 3.1.3**: Create `backend/app/services/payroll/paystub_storage.py` (NEW)
  - [ ] Create PaystubStorage class (DO Spaces)
  - [ ] Implement `_build_storage_key()` - Path pattern
  - [ ] Implement `save_paystub()` - Upload to DO Spaces
  - [ ] Implement `get_download_url()` - Pre-signed URL (15 min)
  - [ ] Implement `list_paystubs_for_employee()`
  - [ ] Implement `delete_paystub()`
  - [ ] Implement `paystub_exists()`

**Validation:**
- [ ] PDF generates without errors
- [ ] All mandatory fields present
- [ ] Numbers formatted correctly ($X,XXX.XX)
- [ ] SIN masked (***-***-XXX)
- [ ] Upload to DO Spaces works
- [ ] Pre-signed URLs work
- [ ] Can list paystubs by employee/year

---

## Phase 4: API & Integration (2 weeks)

### Week 7: Service Layer (NEW)

- [ ] **Task 4.0.1**: Create `backend/app/services/payroll/__init__.py`

- [ ] **Task 4.0.2**: Create `backend/app/services/payroll/employee_service.py`
  - [ ] Create EmployeeService class
  - [ ] Implement SIN encryption/decryption
  - [ ] Implement `create_employee()` with validation
  - [ ] Implement `get_employee()`
  - [ ] Implement `list_employees()`
  - [ ] Implement `update_employee()`
  - [ ] Implement `terminate_employee()`

- [ ] **Task 4.0.3**: Create `backend/app/services/payroll/payroll_service.py`
  - [ ] Create PayrollService class
  - [ ] Implement `create_payroll_run()`
  - [ ] Implement `calculate_payroll_run()`
  - [ ] Implement `approve_payroll_run()`:
    - [ ] Generate paystubs
    - [ ] Create Beancount transactions
    - [ ] Update status
  - [ ] Implement `list_payroll_runs()`
  - [ ] Implement `get_remittance_summary()`

### Week 7: Backend API

- [ ] **Task 4.1.1**: Create `backend/app/api/v1/payroll.py`
  - [ ] Create request/response models (camelCase)
  - [ ] Employee endpoints:
    - [ ] POST `/payroll/employees` - Create
    - [ ] GET `/payroll/employees` - List
    - [ ] GET `/payroll/employees/{id}` - Get
    - [ ] PATCH `/payroll/employees/{id}` - Update
    - [ ] POST `/payroll/employees/{id}/terminate` - Terminate
  - [ ] Payroll calculation endpoints:
    - [ ] POST `/payroll/calculate` - Single calculation
  - [ ] Payroll run endpoints:
    - [ ] POST `/payroll/runs` - Create run
    - [ ] POST `/payroll/runs/{id}/calculate` - Calculate
    - [ ] POST `/payroll/runs/{id}/approve` - Approve
    - [ ] GET `/payroll/runs` - List
    - [ ] GET `/payroll/runs/{id}` - Get
  - [ ] Paystub endpoints:
    - [ ] GET `/payroll/paystubs/{employee_id}` - List
    - [ ] GET `/payroll/paystubs/{employee_id}/{record_id}/download` - Download URL
  - [ ] Remittance endpoints:
    - [ ] GET `/payroll/remittances/summary` - Monthly summary
  - [ ] Stats endpoint:
    - [ ] GET `/payroll/stats` - Dashboard stats
  - [ ] Register router in `__init__.py`

- [ ] **Task 4.1.2**: Create encryption utility
  - [ ] Create `backend/app/core/encryption.py`:
    - [ ] `encrypt_sin()`
    - [ ] `decrypt_sin()`
    - [ ] `mask_sin()`
  - [ ] Add ENCRYPTION_KEY to config

### Week 8: Frontend & Beancount

- [ ] **Task 4.2.1**: Create TypeScript types
  - [ ] Create `frontend/src/lib/types/payroll.ts`:
    - [ ] Province type
    - [ ] PayFrequency type
    - [ ] Employee interface
    - [ ] PayrollRun interface
    - [ ] PayrollCalculationResult interface

- [ ] **Task 4.2.2**: Create API client
  - [ ] Create `frontend/src/lib/api/payroll.ts`:
    - [ ] `listEmployees()`
    - [ ] `createEmployee()`
    - [ ] `getEmployee()`
    - [ ] `listPayrollRuns()`
    - [ ] `createPayrollRun()`
    - [ ] `calculatePayroll()`

- [ ] **Task 4.2.3**: Create Employee Management UI (Svelte 5)
  - [ ] Create `frontend/src/routes/(app)/payroll/+page.svelte` (dashboard)
  - [ ] Create `frontend/src/routes/(app)/payroll/employees/+page.svelte`:
    - [ ] Use `$state`, `$effect`, `$derived` (Runes)
    - [ ] Employee list table
    - [ ] Add employee modal
    - [ ] Province/frequency dropdowns
    - [ ] Form validation
    - [ ] Loading/error states
  - [ ] Style with TailwindCSS

- [ ] **Task 4.3.1**: Create Beancount Integration
  - [ ] Create `backend/app/services/payroll/beancount_integration.py`:
    - [ ] Create PayrollBeancountIntegration class
    - [ ] `generate_payroll_transaction()`:
      - [ ] Expenses:Payroll:Salaries:Gross
      - [ ] Liabilities:Payroll:CPP
      - [ ] Liabilities:Payroll:EI
      - [ ] Liabilities:Payroll:Tax:Federal
      - [ ] Liabilities:Payroll:Tax:Provincial
      - [ ] Assets:Bank:Operating
    - [ ] `generate_employer_costs_transaction()`
    - [ ] `generate_remittance_transaction()`
    - [ ] `generate_account_definitions()`

**Validation:**
- [ ] All API endpoints respond correctly
- [ ] Authentication required (401 without token)
- [ ] RLS enforces multi-tenancy
- [ ] Frontend displays employee list
- [ ] Can add/edit employees via UI
- [ ] Beancount transactions balance
- [ ] Transactions visible in Fava

---

## Phase 5: Testing & Validation (1.5 weeks)

### Week 9: Automated Tests

- [ ] **Task 5.1.1**: CPP Calculator Tests
  - [ ] Test base CPP calculation
  - [ ] Test CPP2 (above YMPE)
  - [ ] Test annual maximums
  - [ ] Test YTD tracking

- [ ] **Task 5.1.2**: EI Calculator Tests
  - [ ] Test EI premium calculation
  - [ ] Test annual maximum
  - [ ] Test employer premium

- [ ] **Task 5.1.3**: Tax Calculator Tests
  - [ ] Test federal tax (all brackets)
  - [ ] Test provincial tax (all 12 provinces)
  - [ ] Test dynamic BPA (MB, NS, YT)

- [ ] **Task 5.1.4**: Integration Tests
  - [ ] Test complete payroll calculation
  - [ ] Test payroll run workflow
  - [ ] Test paystub generation
  - [ ] Test API endpoints

### Week 10: Manual Testing & Validation

- [ ] **Task 5.2.1**: CRA PDOC Validation
  - [ ] Test Case 1: Ontario, $60k annual, bi-weekly
  - [ ] Test Case 2: Alberta, $120k annual, monthly
  - [ ] Test Case 3: Nova Scotia, low income
  - [ ] Document results (variance < $1)

- [ ] **Task 5.2.2**: Final Quality Checks
  - [ ] Run `bash scripts/quality-check-backend.sh`
  - [ ] Run `bash scripts/quality-check-frontend.sh`
  - [ ] Run full test suite
  - [ ] Review all error messages

**Test Coverage Goal:** > 80%

---

## Phase 6: Year-End Processing (Future - 2 weeks)

### T4 Generation

- [ ] Create T4 data models
- [ ] Create T4 aggregation service
- [ ] Create T4 PDF generator
- [ ] Create T4 XML generator (CRA format)
- [ ] Add T4 API endpoints

---

## Phase 7: Compliance Features (Future - 2 weeks)

### Remittance & ROE

- [ ] Create remittance reporting service
- [ ] Create ROE generation service
- [ ] Create garnishment handling
- [ ] Add compliance API endpoints

---

## 🎯 Project Completion Criteria (MVP)

### Functional Requirements
- [ ] Calculates CPP (base + CPP2) correctly
- [ ] Calculates EI correctly
- [ ] Calculates federal income tax correctly
- [ ] Calculates provincial tax for all 12 provinces
- [ ] Generates compliant PDF paystubs
- [ ] Stores paystubs in DigitalOcean Spaces
- [ ] Integrates with Beancount ledger
- [ ] Supports 4 pay frequencies
- [ ] Handles YTD tracking and maximums
- [ ] Frontend UI for employee management

### Technical Requirements
- [ ] Supabase tables with RLS
- [ ] Repository-Service-API pattern
- [ ] Type hints on all functions
- [ ] Pydantic models for all data
- [ ] Decimal type for monetary values
- [ ] Svelte 5 Runes syntax
- [ ] API documentation (OpenAPI)

### Quality Requirements
- [ ] Test coverage > 80%
- [ ] Quality checks pass (black, ruff, mypy)
- [ ] PDOC validation passed (variance < $1)
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

- [ ] **Phase 1 Complete** - Signed: _______ Date: _______
- [ ] **Phase 2 Complete** - Signed: _______ Date: _______
- [ ] **Phase 3 Complete** - Signed: _______ Date: _______
- [ ] **Phase 4 Complete** - Signed: _______ Date: _______
- [ ] **Phase 5 Complete** - Signed: _______ Date: _______
- [ ] **MVP COMPLETE** - Signed: _______ Date: _______

---

**Estimated Duration**: 8-10 weeks (MVP)
**Extended Scope**: +4 weeks (T4, ROE, Garnishments)
