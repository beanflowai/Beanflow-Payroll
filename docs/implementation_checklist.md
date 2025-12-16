# Canadian Payroll Implementation - Master Checklist

**Project**: BeanFlow Payroll (Standalone Product)
**Scope**: All provinces/territories except Quebec
**Timeline**: 8-10 weeks

> **Last Updated**: 2025-12-07
> **Architecture Version**: v3.0 (Standalone Product)

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
| **Phase 0: Frontend Setup** | ⬜ Not Started | | | Standalone SvelteKit app |
| Phase 1: Data Layer | ⬜ Not Started | | | Supabase migrations + Tax tables |
| Phase 2: Calculations | ⬜ Not Started | | | CPP/EI/Tax calculators |
| Phase 3: Paystub | ⬜ Not Started | | | PDF + DO Spaces storage |
| Phase 4: API & Integration | ⬜ Not Started | | | REST API + UI components |
| Phase 5: Testing | ⬜ Not Started | | | Unit + Integration + PDOC |
| Phase 6: Year-End (Future) | ⬜ Not Started | | | T4 generation |
| Phase 7: Compliance (Future) | ⬜ Not Started | | | ROE, Remittance |

**Status Legend**: ⬜ Not Started | 🔄 In Progress | ✅ Completed | ⚠️ Blocked

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

- [ ] **Task 1.0.1**: Create Supabase migration for payroll tables
  - [ ] Create migration file: `backend/supabase/migrations/YYYYMMDD_create_payroll_tables.sql`
  - [ ] Create `employees` table:
    - [ ] Basic fields (id, user_id, ledger_id, names)
    - [ ] SIN encrypted storage
    - [ ] Employment details (province, pay_frequency)
    - [ ] TD1 claim amounts
    - [ ] Exemption flags (cpp, ei, cpp2)
    - [ ] Vacation config (JSONB)
    - [ ] Timestamps
    - [ ] Indexes (user_ledger, province, active)
  - [ ] Create `payroll_runs` table:
    - [ ] Period info (start, end, pay_date)
    - [ ] Status enum (draft, calculating, pending_approval, approved, paid)
    - [ ] Summary totals (all deduction types)
    - [ ] Beancount transaction IDs array
    - [ ] Approval tracking
    - [ ] Timestamps
  - [ ] Create `payroll_records` table:
    - [ ] Foreign keys (payroll_run_id, employee_id)
    - [ ] Earnings fields
    - [ ] Deduction fields
    - [ ] Generated columns (total_gross, total_deductions, net_pay)
    - [ ] YTD snapshot fields
    - [ ] Vacation tracking
    - [ ] Paystub storage key
  - [ ] Add RLS policies for all tables
  - [ ] Add updated_at triggers

- [ ] **Task 1.0.2**: Apply and verify migration
  - [ ] Run `supabase db push` or `supabase migration up`
  - [ ] Verify tables exist in database
  - [ ] Verify RLS is enabled
  - [ ] Verify generated columns work

### Week 1: Repository Layer (NEW)

- [ ] **Task 1.1.1**: Create Employee Repository
  - [ ] Create `backend/app/repositories/payroll/__init__.py`
  - [ ] Create `backend/app/repositories/payroll/employee_repository.py`:
    - [ ] `create_employee()` - Insert with multi-tenancy
    - [ ] `get_employee_by_id()` - Single fetch
    - [ ] `list_employees()` - With filters (active, province)
    - [ ] `update_employee()` - Partial update
    - [ ] `terminate_employee()` - Soft delete
    - [ ] `get_employee_count()` - Count query
    - [ ] `update_vacation_balance()` - Balance update

- [ ] **Task 1.1.2**: Create Payroll Run Repository
  - [ ] Create `backend/app/repositories/payroll/payroll_run_repository.py`:
    - [ ] `create_payroll_run()`
    - [ ] `get_payroll_run_by_id()`
    - [ ] `list_payroll_runs()` - With status/year filter
    - [ ] `update_payroll_run_status()`
    - [ ] `update_payroll_run_totals()`

- [ ] **Task 1.1.3**: Create Payroll Record Repository
  - [ ] Create `backend/app/repositories/payroll/payroll_record_repository.py`:
    - [ ] `create_payroll_record()`
    - [ ] `get_records_for_run()`
    - [ ] `get_records_for_employee()`
    - [ ] `update_paystub_key()`

### Week 2: Tax Tables

- [ ] **Task 1.2.1**: Create `backend/app/services/payroll/tax_tables_2025.py`
  - [ ] Import dependencies (Decimal, Pydantic)
  - [ ] Define TaxBracket model
  - [ ] Define ProvinceTaxConfig model
  - [ ] Create FEDERAL_TAX_CONFIG (5 brackets from T4127 Table 8.1)
  - [ ] Create CPP_CONFIG_2025:
    - [ ] YMPE = $71,200
    - [ ] YAMPE = $76,000
    - [ ] Basic exemption = $3,500
    - [ ] Rate = 5.95%
    - [ ] Additional rate = 1%
  - [ ] Create EI_CONFIG_2025:
    - [ ] MIE = $65,000
    - [ ] Employee rate = 1.70%
    - [ ] Employer rate = 2.38% (1.4x)
  - [ ] Add all 12 provinces to PROVINCIAL_TAX_CONFIGS:
    - [ ] AB (Alberta) - 6 brackets
    - [ ] BC (British Columbia) - 7 brackets
    - [ ] MB (Manitoba) - 3 brackets + dynamic BPA
    - [ ] NB (New Brunswick) - 4 brackets
    - [ ] NL (Newfoundland) - 8 brackets
    - [ ] NS (Nova Scotia) - 5 brackets + dynamic BPA
    - [ ] NT (Northwest Territories) - 4 brackets
    - [ ] NU (Nunavut) - 4 brackets
    - [ ] ON (Ontario) - 5 brackets + surtax/health premium
    - [ ] PE (Prince Edward Island) - 5 brackets
    - [ ] SK (Saskatchewan) - 3 brackets
    - [ ] YT (Yukon) - 5 brackets + dynamic BPA
  - [ ] Implement helper functions:
    - [ ] `find_tax_bracket()`
    - [ ] `get_province_config()`
  - [ ] Implement dynamic BPA functions:
    - [ ] `calculate_bpamb()` (Manitoba)
    - [ ] `calculate_bpans()` (Nova Scotia)
    - [ ] `calculate_bpayt()` (Yukon)
  - [ ] Add `validate_tax_tables()` function

### Week 2: Data Models

- [ ] **Task 1.3.1**: Create `backend/app/models/payroll.py`
  - [ ] Create Province enum (12 values, exclude QC)
  - [ ] Create PayPeriodFrequency enum with `periods_per_year` property
  - [ ] Create PayrollRunStatus enum
  - [ ] Create EmploymentType enum
  - [ ] Create VacationPayoutMethod enum
  - [ ] Create VacationConfig model
  - [ ] Create Employee models (Base, Create, Response)
  - [ ] Create PayrollRun models (Base, Create, Response)
  - [ ] Create PayrollRecord model
  - [ ] Create PayrollCalculationRequest model
  - [ ] Create PayrollCalculationResult model

**Validation:**
- [ ] Migration applies without errors
- [ ] RLS policies working
- [ ] Repository methods work (manual test)
- [ ] All 12 provinces in config
- [ ] Tax tables validate on import
- [ ] Pydantic models pass type checking

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
