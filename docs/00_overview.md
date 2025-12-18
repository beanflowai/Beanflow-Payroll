# Canadian Payroll System - Implementation Overview

**Project**: BeanFlow Payroll (Standalone Product)
**Scope**: All Canadian provinces/territories except Quebec
**Reference**: CRA T4127 (121st Edition, July 2025)
**Difficulty**: 5/10
**Timeline**: 8-10 weeks

> **Last Updated**: 2025-12-07
> **Architecture Version**: v3.0 (Standalone Product)

---

## 🚀 Product Strategy: Standalone Payroll Application

### Key Decision: Independent Product

**BeanFlow Payroll** is designed as a **standalone product**, separate from BeanFlow Bookkeeping:

| Aspect | BeanFlow Payroll | BeanFlow Bookkeeping |
|--------|------------------|---------------------|
| **Domain** | `payroll.beanflow.com` | `app.beanflow.com` |
| **Target Users** | Small business owners, HR staff, Accountants managing client payroll | Accountants, Bookkeepers, Business owners |
| **Billing** | Independent subscription | Independent subscription |
| **Frontend** | Standalone SvelteKit app | Existing frontend |
| **Data** | Isolated payroll tables | Beancount ledgers |

### Rationale

This follows the industry-standard model (similar to Gusto, Wagepoint):

1. **Different User Needs**: Payroll users focus on employee management, tax compliance, and paystubs. Bookkeeping users focus on transactions, reports, and financial statements.

2. **Independent Value**: Users can use Payroll without needing Bookkeeping, and vice versa.

3. **Market Positioning**: Can target payroll-specific customers who may not need full bookkeeping.

4. **Optional Integration**: Users who have both products can link them via "Run Payroll" → generate journal entries in Bookkeeping.

### Shared Infrastructure

While the products are separate, they share:

| Component | Sharing Strategy |
|-----------|-----------------|
| **Authentication** | Shared Google OAuth, same user accounts |
| **Database** | Shared Supabase instance, separate tables/schemas |
| **User Management** | Shared users table with feature flags |
| **Backend** | Shared FastAPI with `/payroll/` route prefix |
| **Component Library** | Shared UI components (design system) |

### Integration Points

```
┌─────────────────────────────────────────────────────────────────┐
│                    Shared Infrastructure                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ Supabase        │  │ Auth (Google)   │  │ User Accounts   │  │
│  │ PostgreSQL      │  │ Shared OAuth    │  │ + Feature Flags │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
          │                                          │
          ▼                                          ▼
┌─────────────────────────┐         ┌─────────────────────────────┐
│   BeanFlow Payroll      │         │   BeanFlow Bookkeeping      │
│   payroll.beanflow.com  │         │   app.beanflow.com          │
├─────────────────────────┤         ├─────────────────────────────┤
│ • Employee management   │         │ • Transaction records       │
│ • Payroll calculations  │         │ • Invoice management        │
│ • Paystub generation    │         │ • Financial reports         │
│ • CRA compliance        │         │ • AI assistant              │
│ • Remittance tracking   │         │ • Beancount ledgers         │
│                         │         │                             │
│ [Optional Integration]  │ ─────►  │ Payroll Journal Entries:    │
│ "Run Payroll" button    │         │ • Wages Expense (Dr)        │
│ Links to Bookkeeping    │         │ • CPP/EI Payable (Cr)       │
│ company if connected    │         │ • Tax Payable (Cr)          │
│                         │         │ • Wages Payable (Cr)        │
└─────────────────────────┘         └─────────────────────────────┘
```

---

## 🔄 Architecture Updates

**Important**: This plan has been updated to reflect standalone product architecture:

| Component | Previous Plan | Current Architecture |
|-----------|--------------|---------------------|
| **Product Model** | Module in BeanFlow | **Standalone Product** |
| **Frontend** | Embedded in `/payroll/` route | **Separate SvelteKit app** |
| **Domain** | Same as main app | **`payroll.beanflow.com`** |
| **Billing** | Shared subscription | **Independent subscription** |
| **Database** | Firestore | **Supabase (PostgreSQL)** |
| **File Storage** | Google Drive | **DigitalOcean Spaces** |
| **API Pattern** | Direct service calls | **Repository-Service-API 3-layer** |
| **Multi-tenancy** | Basic | **RLS + user_id** |

See `14_standalone_architecture.md` for detailed frontend architecture.

---

## 📋 Project Objectives

### Core Features (MVP)
1. ✅ Employee payroll calculation (CPP, EI, Federal/Provincial Tax)
2. ✅ Support for 12 jurisdictions (AB, BC, MB, NB, NL, NS, NT, NU, ON, PE, SK, YT)
3. ✅ PDF paystub generation (stored in DigitalOcean Spaces)
4. ✅ Beancount ledger integration
5. ✅ Employer remittance tracking
6. ✅ Holiday and vacation pay calculation

### Out of Scope (Future Phases)
- ❌ T4 annual tax form generation (Phase 6)
- ❌ ROE (Record of Employment) (Phase 7)
- ❌ Direct CRA e-filing
- ❌ Quebec payroll (requires separate system)
- 📋 **Payment processing** - See `15_payment_integration.md` (Plooto API 集成规划中)

---

## 🗺️ Implementation Phases

| Phase | Document | Focus Area | Duration | Complexity |
|-------|----------|-----------|----------|------------|
| **Phase 1** | `01_phase1_data_layer.md` | Supabase Schema & Tax Tables | 2 weeks | Low |
| **Phase 2** | `02_phase2_calculations.md` | CPP/EI/Tax Calculators | 3 weeks | Medium |
| **Phase 3** | `03_phase3_paystub.md` | PDF Generation & DO Spaces Storage | 1.5 weeks | Low |
| **Phase 4** | `04_phase4_api_integration.md` | REST API & Svelte 5 Frontend | 2 weeks | Medium |
| **Phase 5** | `05_phase5_testing.md` | Testing & Validation | 1.5 weeks | Medium |
| **Phase 6** | `09_year_end_processing.md` | T4 Generation (Future) | 2 weeks | High |
| **Phase 7** | `11_roe_generation.md` | ROE Generation (Future) | 1.5 weeks | High |

### Supporting Documents
| Document | Description |
|----------|-------------|
| `06_configuration_architecture.md` | Tax tables JSON configuration |
| `07_ui_design.md` | Frontend UI specifications |
| `08_holidays_vacation.md` | Holiday & vacation pay logic |
| `10_remittance_reporting.md` | CRA remittance calculations |
| `12_garnishments_deductions.md` | Garnishment handling |
| `13_database_schema.md` | Complete Supabase schema |
| `14_standalone_architecture.md` | Standalone frontend architecture |
| `15_payment_integration.md` | **NEW** - Plooto API 支付集成 (PAD/EFT/CRA) |
| `implementation_checklist.md` | Master progress tracker |

---

## 📚 Reference Documents

### Required Reading
1. **CRA T4127** (Payroll Deductions Formulas)
   - Location: `backend/rag/cra_tax/t4127-jul-25e.pdf`
   - Key Sections:
     - Chapter 4: Tax calculation formulas (Option 1)
     - Chapter 6: CPP calculations
     - Chapter 7: EI calculations
     - Chapter 8: Tables (rates, thresholds, constants)

2. **CRA T4001** (Employers' Guide)
   - Business rules and edge cases
   - Remittance schedules

3. **Provincial TD1 Forms**
   - Federal TD1, TD1-AB, TD1-ON, TD1-BC, etc.
   - Personal tax credit claim amounts

---

## 🏗️ Architecture Overview (v2.0)

### Database Layer (Supabase)

```sql
-- Core Payroll Tables
employees           -- Employee master data
payroll_runs        -- Payroll run headers
payroll_records     -- Individual pay records
payroll_ytd         -- Year-to-date tracking (optional, can derive)

-- All tables include:
--   user_id, ledger_id  (multi-tenancy)
--   RLS policies        (security)
--   created_at, updated_at (audit)
```

### Backend Structure

```
backend/app/
├── repositories/payroll/           # NEW: Data Access Layer
│   ├── employee_repository.py
│   ├── payroll_run_repository.py
│   └── payroll_record_repository.py
├── services/payroll/
│   ├── tax_tables_2025.py          # Phase 1: All tax rates/constants
│   ├── cpp_calculator.py           # Phase 2: CPP calculations
│   ├── ei_calculator.py            # Phase 2: EI calculations
│   ├── federal_tax_calculator.py   # Phase 2: Federal tax
│   ├── provincial_tax_calculator.py # Phase 2: Provincial/territorial tax
│   ├── payroll_engine.py           # Phase 2: Main orchestrator
│   ├── employee_service.py         # NEW: Business logic layer
│   ├── payroll_service.py          # NEW: Payroll orchestration
│   ├── paystub_generator.py        # Phase 3: PDF generation
│   ├── paystub_storage.py          # Phase 3: DO Spaces storage
│   ├── holiday_service.py          # Holiday pay calculations
│   └── vacation_service.py         # Vacation pay calculations
├── models/
│   └── payroll.py                  # Phase 1: Pydantic models
└── api/v1/
    └── payroll.py                  # Phase 4: REST endpoints

backend/supabase/migrations/
└── YYYYMMDD_create_payroll_tables.sql  # Phase 1: Database schema
```

### Frontend Structure (Standalone SvelteKit App)

**Location**: `payroll-frontend/` (separate from main `frontend/`)

```
payroll-frontend/                    # NEW: Standalone Payroll Frontend
├── src/
│   ├── routes/
│   │   ├── +layout.svelte          # Payroll-specific layout
│   │   ├── +page.svelte            # Dashboard / Home
│   │   ├── (auth)/
│   │   │   ├── login/+page.svelte  # Shared Google OAuth
│   │   │   └── callback/+page.svelte
│   │   ├── (app)/
│   │   │   ├── +layout.svelte      # Authenticated layout
│   │   │   ├── dashboard/+page.svelte
│   │   │   ├── employees/
│   │   │   │   ├── +page.svelte    # Employee list
│   │   │   │   └── [id]/+page.svelte
│   │   │   ├── payroll/
│   │   │   │   ├── +page.svelte    # Current pay period
│   │   │   │   └── history/+page.svelte
│   │   │   ├── reports/
│   │   │   │   └── +page.svelte    # Remittance reports
│   │   │   └── settings/
│   │   │       ├── +page.svelte    # Company settings
│   │   │       └── integration/+page.svelte  # Link to Bookkeeping
│   ├── lib/
│   │   ├── components/             # Payroll-specific components
│   │   ├── stores/                 # Svelte stores
│   │   ├── types/                  # TypeScript interfaces
│   │   ├── api/                    # API client (shared backend)
│   │   └── shared/                 # Symlink or copy from main frontend
│   └── app.css                     # Shared design system import
├── static/
├── package.json
├── svelte.config.js
├── tailwind.config.js              # Extends shared config
└── vite.config.ts
```

**Shared Resources** (from main `frontend/`):
- Design system CSS (`lib/styles/design-system/`)
- Base components (`lib/components/v2-current/base/`)
- Icon components (`lib/components/v2-current/icons/`)
- Auth utilities

See `14_standalone_architecture.md` for detailed setup instructions.

### Storage Architecture

```
DigitalOcean Spaces
└── {bucket}/
    └── {user_id}/{ledger_id}/payroll/
        ├── paystubs/{year}/
        │   └── {employee_id}_{pay_date}.pdf
        └── reports/{year}/
            └── remittance_{month}.pdf
```

---

## 🎯 Key Technical Decisions

### 1. Tax Calculation Method
**Choice**: CRA T4127 Option 1 (Annual Tax Method)
- **Why**: Simpler than Option 2 (cumulative averaging)
- **Tradeoff**: Less precise for variable income, but acceptable for MVP

### 2. Decimal Precision
**Choice**: Python `Decimal` type for all monetary values
- **Why**: Avoid float rounding errors (e.g., `0.1 + 0.2 ≠ 0.3`)
- **Example**: `Decimal("2000.00")` not `2000.00`

### 3. Province Support
**Choice**: Implement 12 provinces/territories, exclude Quebec
- **Why**: Quebec has completely different system (QPP, QPIP, Revenu Quebec)
- **Complexity**: Quebec would double implementation time

### 4. Data Storage
**Choice**: Supabase PostgreSQL with Row Level Security
- **Why**: Consistent with current architecture, strong typing, RLS for multi-tenancy
- **Migration**: All new payroll data goes to Supabase, not Firestore

### 5. File Storage
**Choice**: DigitalOcean Spaces for paystub PDFs
- **Why**: Consistent with existing document storage pattern
- **Pattern**: Pre-signed URLs for secure download

### 6. Frontend Framework
**Choice**: Svelte 5 with Runes syntax
- **Why**: Current project standard
- **Pattern**: `$state`, `$effect`, `$derived` for reactivity

### 7. API Architecture
**Choice**: Repository-Service-API three-layer pattern
- **Why**: Consistent with existing patterns (invoices, documents)
- **Benefits**: Testability, separation of concerns

---

## 📊 Complexity Breakdown

### Why 5/10 Difficulty?

**Easy Parts (2/10)**:
- ✅ Official formulas provided (no guesswork)
- ✅ All tax tables in T4127 document
- ✅ Pydantic handles data validation
- ✅ PDF libraries well-documented
- ✅ Existing patterns to follow (invoices, documents)

**Medium Parts (5/10)**:
- ⚠️ 12 provinces = lots of data entry
- ⚠️ Special cases (Ontario surtax, Alberta K5P, BC tax reduction)
- ⚠️ Dynamic BPA formulas (MB, NS, YT)
- ⚠️ YTD tracking for accurate tax calculation
- ⚠️ SIN encryption for security

**Complex Parts (7/10 if included)**:
- 🔴 Quebec (not in scope)
- 🔴 T4 generation (Phase 6)
- 🔴 ROE complex scenarios (Phase 7)

---

## 🔐 Security Considerations

### SIN (Social Insurance Number) Handling

```python
# SIN must be encrypted at rest
from app.core.encryption import encrypt_sin, decrypt_sin

# Store encrypted
employee.sin_encrypted = encrypt_sin(raw_sin)

# Display masked
def mask_sin(sin: str) -> str:
    return f"***-***-{sin[-3:]}"  # Show last 3 digits only
```

### Access Control
- All payroll endpoints require `ledger_access` verification
- Payroll data is isolated by `user_id` + `ledger_id`
- RLS policies enforce database-level security

---

## 🚀 Getting Started

### Step 1: Read This Overview
Understand the project scope and architecture.

### Step 2: Review Current Architecture
```bash
# Key files to understand
cat backend/app/repositories/invoice_repository.py  # Repository pattern
cat backend/app/services/firestore/invoice_service.py  # Service pattern
cat backend/app/api/v1/invoices.py  # API pattern
```

### Step 3: Review T4127 Document
Familiarize yourself with:
- Table 8.1 (tax rates, page 18)
- Table 8.2 (other amounts, page 19)
- CPP/EI calculation sections

### Step 4: Follow Phase Guides
Proceed through phases sequentially:
1. **Phase 1**: Database schema + Tax tables
2. **Phase 2**: Calculation logic (CPP, EI, taxes)
3. **Phase 3**: Output generation (paystubs)
4. **Phase 4**: User interface (API, frontend)
5. **Phase 5**: Quality assurance (testing)

---

## 📝 Using These Guides with LLM Code Agents

Each phase document contains:

1. **Context**: What this phase accomplishes
2. **Prerequisites**: What must be done first
3. **LLM Agent Prompts**: Copy-paste instructions for AI assistants
4. **Validation Criteria**: How to verify success
5. **Common Issues**: Known pitfalls and solutions

### How to Use Prompts

```bash
# Example workflow with Claude Code
1. Load relevant skill: /skill backend-development
2. Open phase guide (e.g., 01_phase1_data_layer.md)
3. Copy "Task X.X" section
4. Agent generates code following project patterns
5. Run validation: bash scripts/quality-check-backend.sh
6. If tests pass, proceed to next task
7. If tests fail, review "Common Issues" section
```

---

## ✅ Success Criteria

The payroll system is complete when:

- [ ] Supabase tables created with RLS policies
- [ ] All 12 provinces calculate correctly
- [ ] CPP/EI deductions match CRA PDOC calculator
- [ ] Federal/Provincial taxes accurate (±$1 due to rounding)
- [ ] Paystubs contain all mandatory fields
- [ ] Paystubs stored in DigitalOcean Spaces
- [ ] YTD totals accumulate correctly
- [ ] Employer remittance amounts calculated
- [ ] Integration tests pass for all provinces
- [ ] Manual test with real employee data successful
- [ ] Quality checks pass (`bash scripts/quality-check.sh`)

---

## 📞 Support & Resources

### Official CRA Resources
- **PDOC Calculator**: https://www.canada.ca/en/revenue-agency/services/e-services/digital-services-businesses/payroll-deductions-online-calculator.html
- **Payroll Help**: https://www.canada.ca/en/revenue-agency/services/tax/businesses/topics/payroll.html

### Project Resources
- **Reference Doc**: `backend/rag/cra_tax/t4127-jul-25e.pdf`
- **Implementation Guides**: `docs/planning/payroll/`
- **Project Skills**: `.claude/skills/` (backend-development, accounting-standards, etc.)

### Related Skills
When developing payroll features, consider loading these Claude Code skills:
- `backend-development` - Core coding standards
- `backend-architecture` - Service layer patterns
- `backend-async-patterns` - Async operations
- `accounting-standards` - Beancount account naming
- `testing-strategy` - Test writing guidelines

---

**Next**: Proceed to [Phase 1: Data Layer](./01_phase1_data_layer.md)
