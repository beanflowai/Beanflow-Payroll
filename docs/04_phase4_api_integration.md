# Phase 4: API & Integration

**Complexity**: Medium
**Prerequisites**: Phase 1-3 completed

> **Last Updated**: 2025-12-31
> **Architecture Version**: v2.0 (Supabase + Repository-Service-API pattern)

---

## Objectives

Create REST API endpoints and frontend UI for payroll operations following project patterns.

### Deliverables

1. ✅ **Payroll Service layer** (business logic)
2. ✅ FastAPI endpoints for payroll (following existing patterns)
3. ✅ Employee management API with RLS
4. ✅ Pay period/payroll run API
5. ✅ Draft payroll run management API (create-or-get, add/remove employees, sync, delete)
6. ✅ Frontend **Svelte 5** components (using Runes)
7. ✅ Beancount ledger integration (using existing `BeancountService`)
8. ✅ Employee snapshot mechanism for historical accuracy

---

## Architecture Overview

### Three-Layer Pattern

```
API Layer (FastAPI)           → backend/app/api/v1/payroll.py
    ↓
Service Layer (Business Logic) → backend/app/services/payroll/
    ↓
Repository Layer (Data Access) → backend/app/repositories/payroll/
    ↓
Database (Supabase PostgreSQL)
```

### Reference Patterns

| Pattern | Reference File | Description |
|---------|---------------|-------------|
| API endpoints | `backend/app/api/v1/invoices.py` | Endpoint structure, decorators |
| Service layer | `backend/app/services/firestore/invoice_service.py` | Business logic |
| Repository | `backend/app/repositories/invoice_repository.py` | Data access |

---

## Task 4.1: Payroll Service Layer

### Files

| File | Purpose |
|------|---------|
| `backend/app/services/payroll/__init__.py` | Module init |
| `backend/app/services/payroll/employee_service.py` | Employee CRUD, SIN encryption |
| `backend/app/services/payroll/payroll_service.py` | Payroll run operations |
| `backend/app/core/encryption.py` | SIN encryption/decryption helpers |

### EmployeeService Responsibilities

- **SIN handling**: Encrypt before storage, decrypt for masking
- **Business validation**: Salary/hourly rate requirements
- **Data transformation**: API models ↔ DB records
- **Soft delete**: Termination with date preservation

### Key Methods

| Method | Description |
|--------|-------------|
| `create_employee()` | Create with SIN encryption |
| `get_employee()` | Get with masked SIN |
| `list_employees()` | Filter by active/province |
| `update_employee()` | Partial update (no SIN) |
| `terminate_employee()` | Soft delete with date |

### SIN Encryption

- Uses Fernet symmetric encryption
- Requires `ENCRYPTION_KEY` environment variable
- Stored as `sin_encrypted` in database
- Displayed as `***-***-XXX` (masked)

---

## Task 4.2: Payroll API Endpoints

### File Location

`backend/app/api/v1/payroll.py`

### Employee Endpoints

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| POST | `/payroll/employees` | Create employee | edit |
| GET | `/payroll/employees` | List employees | view |
| GET | `/payroll/employees/{id}` | Get employee | view |
| PATCH | `/payroll/employees/{id}` | Update employee | edit |
| POST | `/payroll/employees/{id}/terminate` | Terminate employee | edit |

### Compensation Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/payroll/employees/{id}/compensation` | Update compensation with history |
| GET | `/payroll/employees/{id}/compensation` | Get compensation history |

### Payroll Calculation

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/payroll/calculate` | Calculate single payroll deductions |

### Payroll Run Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/payroll/runs` | Create payroll run |
| GET | `/payroll/runs` | List payroll runs |
| GET | `/payroll/runs/{id}` | Get payroll run details |
| POST | `/payroll/runs/{id}/calculate` | Calculate all employees |
| POST | `/payroll/runs/{id}/approve` | Approve and finalize |

### Draft Run Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/payroll/runs/create-or-get` | Create or get draft run for pay date |
| POST | `/payroll/runs/{id}/sync-employees` | Sync new employees to draft |
| POST | `/payroll/runs/{id}/employees` | Add employee to draft |
| DELETE | `/payroll/runs/{id}/employees/{eid}` | Remove employee from draft |
| DELETE | `/payroll/runs/{id}` | Delete draft run |
| POST | `/payroll/runs/{id}/recalculate` | Recalculate all deductions |
| POST | `/payroll/runs/{id}/finalize` | Transition to pending_approval |

### Paystub Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/payroll/paystubs/{employee_id}` | List employee paystubs |
| GET | `/payroll/paystubs/{employee_id}/{record_id}/download` | Get download URL |

### Other Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/payroll/remittances/summary` | Monthly remittance summary |
| GET | `/payroll/stats` | Dashboard statistics |

### Overtime Calculation Endpoints (Added 2026-01-08)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/overtime/calculate` | Calculate regular/overtime split for daily hours |

**Request Model**:
```typescript
interface OvertimeCalculateRequest {
  province: string;                    // Province code (e.g., 'ON', 'BC')
  entries: DailyHoursEntry[];
}

interface DailyHoursEntry {
  date: string;                        // ISO date (YYYY-MM-DD)
  totalHours: number;                  // Total hours (0-24)
  isHoliday?: boolean;                 // Whether this day is a holiday
}
```

**Response Model**:
```typescript
interface OvertimeCalculateResponse {
  regularHours: number;                // Total regular hours
  overtimeHours: number;               // Total overtime hours (1.5x rate)
  doubleTimeHours: number;             // Total double-time hours (2x rate, BC only)
}
```

**Province-Specific Rules**:
- **ON, QC, MB, etc.**: Weekly threshold only (typically 44h or 40h/week)
- **AB, BC, NT, NU, YT**: Daily threshold (8h/day) + weekly threshold
- **BC Special**: Double-time for hours > 12/day

**Service**: `backend/app/services/overtime_calculator.py`

### API Field Naming

All API request/response models use **camelCase** (project standard):
- `firstName`, `lastName`, `sinMasked`
- `provinceOfEmployment`, `payFrequency`
- `annualSalary`, `hourlyRate`
- `federalClaimAmount`, `provincialClaimAmount`

Internal models use **snake_case**.

---

## Task 4.3: Frontend Employee Management

### Files

| File | Purpose |
|------|---------|
| `frontend/src/routes/(app)/payroll/+page.svelte` | Payroll dashboard |
| `frontend/src/routes/(app)/payroll/employees/+page.svelte` | Employee list |
| `frontend/src/lib/types/payroll.ts` | TypeScript types |
| `frontend/src/lib/api/payroll.ts` | API client |

### Svelte 5 Patterns

Use Runes syntax:
- `$state()` for reactive state
- `$derived()` for computed values
- `$effect()` for side effects

### Reference Components

- `frontend/src/routes/(app)/invoices/+page.svelte` - Page pattern
- `frontend/src/lib/api/invoices.ts` - API client pattern

### Key UI Features

- Employee table with status badges
- Add employee modal with form validation
- SIN input with pattern validation (`XXX-XXX-XXX`)
- Province and pay frequency dropdowns
- Federal/Provincial claim amount inputs

---

## Task 4.4: Beancount Integration

### File Location

`backend/app/services/payroll/beancount_integration.py`

### Account Structure

```
Expenses:
  Expenses:Payroll:Salaries:Gross        # Employee gross pay
  Expenses:Payroll:Benefits:CPP          # Employer CPP contribution
  Expenses:Payroll:Benefits:EI           # Employer EI contribution

Liabilities (amounts to remit):
  Liabilities:Payroll:CPP                # Employee + Employer CPP
  Liabilities:Payroll:EI                 # Employee + Employer EI
  Liabilities:Payroll:Tax:Federal        # Federal tax withheld
  Liabilities:Payroll:Tax:Provincial     # Provincial tax withheld
  Liabilities:Payroll:Deductions:RRSP    # RRSP contributions
  Liabilities:Payroll:Deductions:Union   # Union dues

Assets:
  Assets:Bank:Operating                  # Net pay disbursement
```

### Transaction Types

| Method | Purpose |
|--------|---------|
| `generate_payroll_transaction()` | Individual employee pay record |
| `generate_employer_costs_transaction()` | Employer CPP/EI contributions |
| `generate_remittance_transaction()` | CRA remittance payment |
| `generate_account_definitions()` | Account open directives |

### Integration Point

Called from `PayrollService.approve_payroll_run()` when finalizing a payroll run.

---

## Employee Snapshot Mechanism

When creating payroll records, the system stores a snapshot of employee data at payroll time for historical accuracy.

### Snapshot Fields (in `payroll_records`)

| Field | Purpose |
|-------|---------|
| `snapshot_name` | Employee full name at payroll time |
| `snapshot_province` | Province of employment at payroll time |
| `snapshot_salary` | Annual salary at payroll time |
| `snapshot_pay_group_name` | Pay group name at payroll time |

### Usage

- Display historical payroll data using snapshot fields
- Fallback to current employee data if snapshot missing
- Ensures paystubs reflect accurate historical information

### Migration

`20251224240000_add_employee_snapshots.sql`

---

## Validation Checklist

- [ ] Employee service created with SIN encryption
- [ ] All API endpoints respond correctly
- [ ] Employee CRUD operations work
- [ ] Payroll calculation endpoint accurate
- [ ] Frontend displays employees (Svelte 5 Runes)
- [ ] Can add/edit employees via UI
- [ ] Beancount transactions formatted correctly
- [ ] Transactions use proper account naming
- [ ] Payroll run workflow works (draft → calculate → approve)
- [ ] Overtime calculation API works with province-specific rules
- [ ] Timesheet entries can be created and retrieved
- [ ] Timesheet modal UI allows daily hours entry

---

**Next**: [Phase 5: Testing & Validation](./05_phase5_testing.md)
