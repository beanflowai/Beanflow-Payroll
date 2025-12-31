# Database Schema - Payroll Module

**Last Updated**: 2025-12-31
**Database**: Supabase (PostgreSQL)

---

## Overview

The payroll module uses multiple tables stored in Supabase PostgreSQL:

| Table | Description | Row Count Estimate |
|-------|-------------|-------------------|
| `employees` | Employee master data | 10-500 per ledger |
| `employee_compensation_history` | Salary/rate change history | 1-10 per employee |
| `payroll_runs` | Payroll run headers | 12-52 per year |
| `payroll_records` | Individual pay records | employees × runs |
| `companies` | Company configuration | 1-5 per user |
| `pay_groups` | Pay group policies | 1-10 per company |

All tables follow the project's multi-tenancy pattern with `user_id` and `ledger_id` columns, and Row Level Security (RLS) policies.

---

## Entity Relationship Diagram

```
┌─────────────────┐
│    employees    │
├─────────────────┤
│ id (PK)         │
│ user_id         │
│ ledger_id       │
│ sin_encrypted   │
│ province        │
│ pay_frequency   │
│ annual_salary   │◄─── synced from current compensation
│ hourly_rate     │◄─── synced from current compensation
│ ...             │
└────────┬────────┘
         │
         ├───────────────────────────────────────┐
         │ 1:N                                   │ 1:N
         │                                       │
         ▼                                       ▼
┌────────────────────────────┐     ┌─────────────────────────────────┐
│ employee_compensation_     │     │         payroll_records         │
│ history                    │     ├─────────────────────────────────┤
├────────────────────────────┤     │ id (PK)                         │
│ id (PK)                    │     │ employee_id (FK)────────────────┘
│ employee_id (FK)───────────┘     │ payroll_run_id (FK)◄──────┐
│ compensation_type          │     │ user_id         │   N:1   │
│ annual_salary              │     │ ledger_id       │         │
│ hourly_rate                │     │ earnings...     │         │
│ effective_date             │     │ deductions...   │         │
│ end_date (NULL=current)    │     │ net_pay         │         │
│ change_reason              │     └─────────────────┘         │
└────────────────────────────┘                                 │
                                            ┌──────────────────┘
                                            │
                                   ┌────────┴────────┐
                                   │  payroll_runs   │
                                   ├─────────────────┤
                                   │ id (PK)         │
                                   │ user_id         │
                                   │ ledger_id       │
                                   │ period_start    │
                                   │ period_end      │
                                   │ pay_date        │
                                   │ status          │
                                   │ totals...       │
                                   └─────────────────┘
```

---

## Table: employees

Stores employee master data including personal information, compensation, and tax claim amounts.

### Schema

```sql
CREATE TABLE IF NOT EXISTS employees (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Multi-tenancy (required for all queries)
    user_id TEXT NOT NULL,
    ledger_id TEXT NOT NULL,

    -- Personal Information
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    sin_encrypted TEXT NOT NULL,  -- Encrypted SIN (Fernet)
    email TEXT,

    -- Employment Details
    province_of_employment TEXT NOT NULL CHECK (
        province_of_employment IN (
            'AB', 'BC', 'MB', 'NB', 'NL', 'NS',
            'NT', 'NU', 'ON', 'PE', 'SK', 'YT'
        )
    ),
    pay_frequency TEXT NOT NULL CHECK (
        pay_frequency IN ('weekly', 'bi_weekly', 'semi_monthly', 'monthly')
    ),
    employment_type TEXT DEFAULT 'full_time' CHECK (
        employment_type IN ('full_time', 'part_time', 'contract', 'casual')
    ),

    -- Compensation (one required)
    annual_salary NUMERIC(12, 2),
    hourly_rate NUMERIC(10, 2),

    -- TD1 Claim Amounts (from employee's TD1 form)
    federal_claim_amount NUMERIC(12, 2) NOT NULL,
    provincial_claim_amount NUMERIC(12, 2) NOT NULL,

    -- Exemptions
    is_cpp_exempt BOOLEAN DEFAULT FALSE,
    is_ei_exempt BOOLEAN DEFAULT FALSE,
    cpp2_exempt BOOLEAN DEFAULT FALSE,  -- CPT30 form

    -- Optional Per-Period Deductions
    rrsp_per_period NUMERIC(10, 2) DEFAULT 0,
    union_dues_per_period NUMERIC(10, 2) DEFAULT 0,

    -- Employment Dates
    hire_date DATE NOT NULL,
    termination_date DATE,  -- NULL = active employee

    -- Vacation Configuration (flexible JSONB)
    vacation_config JSONB DEFAULT '{"payout_method": "accrual", "vacation_rate": "0.04"}'::JSONB,
    vacation_balance NUMERIC(12, 2) DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT chk_salary_or_hourly CHECK (
        annual_salary IS NOT NULL OR hourly_rate IS NOT NULL
    ),
    CONSTRAINT unique_employee_sin UNIQUE (user_id, ledger_id, sin_encrypted)
);
```

### Indexes

```sql
-- Primary query path (most queries filter by user + ledger)
CREATE INDEX IF NOT EXISTS idx_employees_user_ledger
    ON employees(user_id, ledger_id);

-- Province filter (for reporting)
CREATE INDEX IF NOT EXISTS idx_employees_province
    ON employees(province_of_employment);

-- Active employees only (common filter)
CREATE INDEX IF NOT EXISTS idx_employees_active
    ON employees(user_id, ledger_id)
    WHERE termination_date IS NULL;
```

### RLS Policy

```sql
ALTER TABLE employees ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can access own employees"
    ON employees
    FOR ALL
    USING (user_id = current_setting('app.current_user_id', TRUE));
```

### Vacation Config JSONB Structure

```json
{
  "payout_method": "accrual",     // accrual | pay_as_you_go | lump_sum
  "vacation_rate": "0.04",        // 4% (< 5 years) or 6% (5+ years)
  "lump_sum_month": null          // 1-12 if lump_sum method
}
```

---

## Table: employee_compensation_history (Added 2025-12-31)

Tracks employee salary/hourly rate changes over time. Instead of overwriting compensation values, each change creates a new history record with an effective date.

### Design Philosophy

- **History Tracking**: Every compensation change is preserved with effective dates
- **Atomic Updates**: RPC function ensures transactional consistency
- **Sync to Employees**: Current compensation is always synced to `employees` table for quick access
- **Audit Trail**: `change_reason` field documents why each change was made

### Schema

```sql
CREATE TABLE employee_compensation_history (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign Key
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,

    -- Compensation Details
    compensation_type TEXT NOT NULL CHECK (compensation_type IN ('salary', 'hourly')),
    annual_salary NUMERIC(12, 2),
    hourly_rate NUMERIC(10, 2),

    -- Effective Period
    effective_date DATE NOT NULL,
    end_date DATE,  -- NULL = currently active

    -- Audit
    change_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),

    -- Constraints
    CONSTRAINT valid_compensation CHECK (
        (compensation_type = 'salary' AND annual_salary IS NOT NULL) OR
        (compensation_type = 'hourly' AND hourly_rate IS NOT NULL)
    ),
    CONSTRAINT valid_date_range CHECK (end_date IS NULL OR end_date >= effective_date)
);
```

### Indexes

```sql
-- Primary query path: get employee's compensation history
CREATE INDEX idx_comp_history_employee
    ON employee_compensation_history(employee_id);

-- Effective date lookup (descending for "current" queries)
CREATE INDEX idx_comp_history_effective
    ON employee_compensation_history(employee_id, effective_date DESC);
```

### RLS Policy

```sql
ALTER TABLE employee_compensation_history ENABLE ROW LEVEL SECURITY;

-- Users can only access their own employees' compensation history
CREATE POLICY "Users can manage their employees compensation history"
ON employee_compensation_history
FOR ALL
USING (
    employee_id IN (SELECT id FROM employees WHERE user_id = auth.uid()::text)
);
```

### RPC Function: update_employee_compensation

Atomic function that ensures transactional consistency when updating employee compensation.

```sql
CREATE OR REPLACE FUNCTION update_employee_compensation(
    p_employee_id UUID,
    p_compensation_type TEXT,
    p_annual_salary NUMERIC,
    p_hourly_rate NUMERIC,
    p_effective_date DATE,
    p_change_reason TEXT DEFAULT NULL
)
RETURNS SETOF employee_compensation_history
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    -- Security: Validate employee ownership via auth.uid()

    -- Validation: compensation type and amount

    -- Validation: new effective date must be after current effective date

    -- Step 1: Close current active record (set end_date)
    UPDATE employee_compensation_history
    SET end_date = p_effective_date - INTERVAL '1 day'
    WHERE employee_id = p_employee_id AND end_date IS NULL;

    -- Step 2: Insert new compensation record
    INSERT INTO employee_compensation_history (...) VALUES (...);

    -- Step 3: Sync current compensation to employees table
    UPDATE employees
    SET annual_salary = ..., hourly_rate = ...
    WHERE id = p_employee_id;
END;
$$;

-- Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION update_employee_compensation TO authenticated;
```

**Function Behavior**:

| Step | Description |
|------|-------------|
| 1. Validate ownership | Ensures caller owns the employee via `auth.uid()` |
| 2. Validate effective date | New date must be after current record's effective date |
| 3. Close current record | Sets `end_date` to day before new effective date |
| 4. Insert new record | Creates new compensation record with `end_date = NULL` |
| 5. Sync to employees | Updates `annual_salary`/`hourly_rate` in employees table |

### Usage Example

```sql
-- Update employee to new salary effective 2025-02-01
SELECT * FROM update_employee_compensation(
    p_employee_id := '550e8400-e29b-41d4-a716-446655440000',
    p_compensation_type := 'salary',
    p_annual_salary := 75000.00,
    p_hourly_rate := NULL,
    p_effective_date := '2025-02-01',
    p_change_reason := 'Annual performance review - 10% raise'
);
```

### Data Migration

Existing compensation data was migrated from `employees` table:

```sql
INSERT INTO employee_compensation_history (...)
SELECT
    id,
    CASE WHEN annual_salary IS NOT NULL THEN 'salary' ELSE 'hourly' END,
    annual_salary,
    hourly_rate,
    COALESCE(hire_date, created_at::date),
    'Initial migration from employees table',
    created_at
FROM employees
WHERE annual_salary IS NOT NULL OR hourly_rate IS NOT NULL;
```

---

## Table: payroll_runs

Stores payroll run headers with period information and aggregated totals.

### Schema

```sql
CREATE TABLE IF NOT EXISTS payroll_runs (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Multi-tenancy
    user_id TEXT NOT NULL,
    ledger_id TEXT NOT NULL,

    -- Period Information
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    pay_date DATE NOT NULL,

    -- Status (state machine)
    status TEXT DEFAULT 'draft' CHECK (
        status IN (
            'draft',              -- Initial state, can add/remove employees
            'calculating',        -- Processing deductions
            'pending_approval',   -- Ready for review
            'approved',           -- Paystubs generated, Beancount entries created
            'paid',               -- Payment sent
            'cancelled'           -- Voided
        )
    ),

    -- Summary Totals (aggregated from payroll_records)
    total_employees INTEGER DEFAULT 0,
    total_gross NUMERIC(14, 2) DEFAULT 0,
    total_cpp_employee NUMERIC(12, 2) DEFAULT 0,
    total_cpp_employer NUMERIC(12, 2) DEFAULT 0,
    total_ei_employee NUMERIC(12, 2) DEFAULT 0,
    total_ei_employer NUMERIC(12, 2) DEFAULT 0,
    total_federal_tax NUMERIC(12, 2) DEFAULT 0,
    total_provincial_tax NUMERIC(12, 2) DEFAULT 0,
    total_net_pay NUMERIC(14, 2) DEFAULT 0,
    total_employer_cost NUMERIC(14, 2) DEFAULT 0,

    -- Beancount Integration
    beancount_transaction_ids TEXT[],  -- Array of transaction IDs

    -- Approval Tracking
    approved_by TEXT,
    approved_at TIMESTAMPTZ,

    -- Notes
    notes TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT chk_period_dates CHECK (period_end >= period_start),
    CONSTRAINT chk_pay_date CHECK (pay_date >= period_end)
);
```

### Indexes

```sql
-- Primary query path
CREATE INDEX IF NOT EXISTS idx_payroll_runs_user_ledger
    ON payroll_runs(user_id, ledger_id);

-- Status filter (common for dashboard)
CREATE INDEX IF NOT EXISTS idx_payroll_runs_status
    ON payroll_runs(status);

-- Recent runs (sorted listing)
CREATE INDEX IF NOT EXISTS idx_payroll_runs_pay_date
    ON payroll_runs(pay_date DESC);

-- Period lookup (duplicate detection)
CREATE INDEX IF NOT EXISTS idx_payroll_runs_period
    ON payroll_runs(user_id, ledger_id, period_start, period_end);
```

### RLS Policy

```sql
ALTER TABLE payroll_runs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can access own payroll runs"
    ON payroll_runs
    FOR ALL
    USING (user_id = current_setting('app.current_user_id', TRUE));
```

### Status State Machine

```
                    ┌──────────────┐
                    │    draft     │
                    └──────┬───────┘
                           │ calculate_payroll_run()
                           ▼
                    ┌──────────────┐
                    │ calculating  │
                    └──────┬───────┘
                           │ (automatic)
                           ▼
                    ┌──────────────────┐
                    │ pending_approval │
                    └──────┬───────────┘
                           │ approve_payroll_run()
            ┌──────────────┴──────────────┐
            ▼                              ▼
     ┌──────────────┐              ┌──────────────┐
     │   approved   │              │  cancelled   │
     └──────┬───────┘              └──────────────┘
            │ mark_as_paid()
            ▼
     ┌──────────────┐
     │     paid     │
     └──────────────┘
```

---

## Table: payroll_records

Stores individual pay records for each employee in a payroll run.

### Schema

```sql
CREATE TABLE IF NOT EXISTS payroll_records (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign Keys
    payroll_run_id UUID NOT NULL REFERENCES payroll_runs(id) ON DELETE CASCADE,
    employee_id UUID NOT NULL REFERENCES employees(id),

    -- Multi-tenancy (denormalized for RLS)
    user_id TEXT NOT NULL,
    ledger_id TEXT NOT NULL,

    -- Hours Worked (for hourly employees)
    regular_hours_worked NUMERIC(6, 2),  -- NULL for salaried employees
    overtime_hours_worked NUMERIC(6, 2) DEFAULT 0,
    hourly_rate_snapshot NUMERIC(10, 2),  -- Snapshot of hourly rate at time of payroll

    -- Earnings
    gross_regular NUMERIC(12, 2) NOT NULL,  -- For salary: annual/periods; For hourly: hours × rate
    gross_overtime NUMERIC(10, 2) DEFAULT 0,
    holiday_pay NUMERIC(10, 2) DEFAULT 0,
    holiday_premium_pay NUMERIC(10, 2) DEFAULT 0,
    vacation_pay_paid NUMERIC(10, 2) DEFAULT 0,
    other_earnings NUMERIC(10, 2) DEFAULT 0,

    -- Employee Deductions
    cpp_employee NUMERIC(10, 2) DEFAULT 0,
    cpp_additional NUMERIC(10, 2) DEFAULT 0,  -- CPP2 (above YMPE)
    ei_employee NUMERIC(10, 2) DEFAULT 0,
    federal_tax NUMERIC(10, 2) DEFAULT 0,
    provincial_tax NUMERIC(10, 2) DEFAULT 0,
    rrsp NUMERIC(10, 2) DEFAULT 0,
    union_dues NUMERIC(10, 2) DEFAULT 0,
    garnishments NUMERIC(10, 2) DEFAULT 0,
    other_deductions NUMERIC(10, 2) DEFAULT 0,

    -- Employer Costs
    cpp_employer NUMERIC(10, 2) DEFAULT 0,
    ei_employer NUMERIC(10, 2) DEFAULT 0,

    -- Generated Columns (computed automatically)
    total_gross NUMERIC(12, 2) GENERATED ALWAYS AS (
        gross_regular + gross_overtime + holiday_pay +
        holiday_premium_pay + vacation_pay_paid + other_earnings
    ) STORED,

    total_deductions NUMERIC(12, 2) GENERATED ALWAYS AS (
        cpp_employee + cpp_additional + ei_employee +
        federal_tax + provincial_tax + rrsp +
        union_dues + garnishments + other_deductions
    ) STORED,

    net_pay NUMERIC(12, 2) GENERATED ALWAYS AS (
        (gross_regular + gross_overtime + holiday_pay +
         holiday_premium_pay + vacation_pay_paid + other_earnings) -
        (cpp_employee + cpp_additional + ei_employee +
         federal_tax + provincial_tax + rrsp +
         union_dues + garnishments + other_deductions)
    ) STORED,

    total_employer_cost NUMERIC(12, 2) GENERATED ALWAYS AS (
        cpp_employer + ei_employer
    ) STORED,

    -- YTD Snapshot (captured at record creation)
    ytd_gross NUMERIC(14, 2) DEFAULT 0,
    ytd_cpp NUMERIC(10, 2) DEFAULT 0,
    ytd_ei NUMERIC(10, 2) DEFAULT 0,
    ytd_federal_tax NUMERIC(12, 2) DEFAULT 0,
    ytd_provincial_tax NUMERIC(12, 2) DEFAULT 0,
    ytd_net_pay NUMERIC(12, 2) DEFAULT 0,  -- Added 2025-12-28

    -- Vacation Tracking
    vacation_accrued NUMERIC(10, 2) DEFAULT 0,
    vacation_hours_taken NUMERIC(6, 2) DEFAULT 0,

    -- Draft Flow Support (Added 2025-12-23)
    input_data JSONB,                    -- Original input data for recalculation
    is_modified BOOLEAN DEFAULT FALSE,   -- Whether record has been modified since last calculation

    -- Calculation Details (for audit/debugging)
    calculation_details JSONB,

    -- Paystub Storage
    paystub_storage_key TEXT,  -- DO Spaces object key
    paystub_generated_at TIMESTAMPTZ,

    -- Timestamp
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT unique_employee_per_run UNIQUE (payroll_run_id, employee_id)
);
```

### Indexes

```sql
-- Primary query: records for a run
CREATE INDEX IF NOT EXISTS idx_payroll_records_run
    ON payroll_records(payroll_run_id);

-- Employee history
CREATE INDEX IF NOT EXISTS idx_payroll_records_employee
    ON payroll_records(employee_id);

-- Multi-tenancy path
CREATE INDEX IF NOT EXISTS idx_payroll_records_user_ledger
    ON payroll_records(user_id, ledger_id);

-- Paystub lookup
CREATE INDEX IF NOT EXISTS idx_payroll_records_paystub
    ON payroll_records(paystub_storage_key)
    WHERE paystub_storage_key IS NOT NULL;
```

### RLS Policy

```sql
ALTER TABLE payroll_records ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can access own payroll records"
    ON payroll_records
    FOR ALL
    USING (user_id = current_setting('app.current_user_id', TRUE));
```

### Calculation Details JSONB Structure

```json
{
  "gross_calculation": {
    "type": "hourly",           // "salary" | "hourly"
    "regular_hours": 40.0,      // Only for hourly employees
    "overtime_hours": 5.0,      // Overtime hours worked
    "hourly_rate": "25.00",     // Snapshot of hourly rate
    "overtime_rate": "37.50",   // 1.5x hourly rate
    "regular_pay": "1000.00",   // hours × rate
    "overtime_pay": "187.50"    // OT hours × OT rate
  },
  "cpp": {
    "pensionable_earnings": "2307.69",
    "prorated_exemption": "134.62",
    "base_cpp": "129.35",
    "cpp2": "0.00",
    "at_maximum": false
  },
  "ei": {
    "insurable_earnings": "2307.69",
    "premium": "39.23",
    "at_maximum": false
  },
  "federal_tax": {
    "annual_income": "60000.00",
    "bracket": 2,
    "rate": "0.205",
    "k_constant": "2725.00",
    "k1_credit": "2419.35",
    "k2_credit": "252.87",
    "k4_credit": "220.65",
    "annual_tax": "7156.13",
    "per_period_tax": "275.24"
  },
  "provincial_tax": {
    "province": "ON",
    "annual_income": "60000.00",
    "bracket": 2,
    "rate": "0.0915",
    "bpa": "12747.00",
    "annual_tax": "4386.05",
    "surtax": "0.00",
    "health_premium": "600.00",
    "per_period_tax": "191.77"
  },
  "calculated_at": "2025-01-15T10:30:00Z"
}
```

### input_data JSONB Structure (Added 2025-12-23)

Stores the original input data used for payroll calculation, enabling recalculation when values are modified in Draft state.

```json
{
  "regularHours": 80,
  "overtimeHours": 5,
  "leaveEntries": [
    { "type": "vacation", "hours": 8 }
  ],
  "holidayWorkEntries": [
    { "holidayDate": "2025-12-25", "holidayName": "Christmas Day", "hoursWorked": 8 }
  ],
  "adjustments": [
    { "type": "bonus", "amount": 500, "description": "Q4 Performance", "taxable": true }
  ],
  "overrides": {
    "regularPay": null,
    "overtimePay": null,
    "holidayPay": null
  }
}
```

**Field Descriptions**:
| Field | Type | Description |
|-------|------|-------------|
| `regularHours` | number | Regular hours worked (hourly employees) |
| `overtimeHours` | number | Overtime hours worked |
| `leaveEntries` | array | Leave taken (vacation, sick) |
| `holidayWorkEntries` | array | Hours worked on statutory holidays |
| `adjustments` | array | One-time adjustments (bonus, retro pay, etc.) |
| `overrides` | object | Manual overrides for calculated pay values |

**Usage**:
- Stored when payroll run transitions to `draft` status
- Used by backend to recalculate deductions when records are modified
- `is_modified` flag set to `true` when input_data changes, cleared after recalculation

---

## Helper Function: updated_at Trigger

```sql
-- Create function if not exists
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to employees
CREATE TRIGGER update_employees_updated_at
    BEFORE UPDATE ON employees
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Apply to payroll_runs
CREATE TRIGGER update_payroll_runs_updated_at
    BEFORE UPDATE ON payroll_runs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

---

## Migration File Template

Save as: `backend/supabase/migrations/YYYYMMDDHHMMSS_create_payroll_tables.sql`

```sql
-- =============================================================================
-- PAYROLL MODULE - DATABASE SCHEMA
-- =============================================================================
-- Description: Creates tables for employee management and payroll processing
-- Author: BeanFlow-LLM Team
-- Date: YYYY-MM-DD
-- =============================================================================

-- Ensure helper function exists
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- EMPLOYEES TABLE
-- =============================================================================
-- [Full CREATE TABLE statement from above]

-- =============================================================================
-- PAYROLL_RUNS TABLE
-- =============================================================================
-- [Full CREATE TABLE statement from above]

-- =============================================================================
-- PAYROLL_RECORDS TABLE
-- =============================================================================
-- [Full CREATE TABLE statement from above]

-- =============================================================================
-- INDEXES
-- =============================================================================
-- [All CREATE INDEX statements from above]

-- =============================================================================
-- ROW LEVEL SECURITY
-- =============================================================================
-- [All RLS policies from above]

-- =============================================================================
-- TRIGGERS
-- =============================================================================
-- [All trigger statements from above]
```

---

## Verification Queries

After applying the migration, run these queries to verify:

```sql
-- 1. Check tables exist
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('employees', 'payroll_runs', 'payroll_records');

-- 2. Check RLS is enabled
SELECT tablename, rowsecurity
FROM pg_tables
WHERE tablename IN ('employees', 'payroll_runs', 'payroll_records');

-- 3. Check generated columns
SELECT column_name, generation_expression
FROM information_schema.columns
WHERE table_name = 'payroll_records'
AND is_generated = 'ALWAYS';

-- 4. Check indexes
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename IN ('employees', 'payroll_runs', 'payroll_records');

-- 5. Check constraints
SELECT conname, contype, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid IN (
    'employees'::regclass,
    'payroll_runs'::regclass,
    'payroll_records'::regclass
);
```

---

## Data Types Reference

| PostgreSQL Type | Python Type | Pydantic Type | Example |
|-----------------|-------------|---------------|---------|
| UUID | str / UUID | UUID | `gen_random_uuid()` |
| TEXT | str | str | `'John'` |
| NUMERIC(12,2) | Decimal | Decimal | `Decimal("2000.00")` |
| DATE | date | date | `date(2025, 1, 15)` |
| TIMESTAMPTZ | datetime | datetime | `datetime.now(UTC)` |
| BOOLEAN | bool | bool | `True` |
| JSONB | dict | dict | `{"key": "value"}` |
| TEXT[] | list[str] | list[str] | `["id1", "id2"]` |

---

## Performance Considerations

### Query Patterns

Most common queries and their expected paths:

1. **List active employees for a ledger**
   ```sql
   SELECT * FROM employees
   WHERE user_id = ? AND ledger_id = ? AND termination_date IS NULL
   ORDER BY last_name, first_name;
   -- Uses: idx_employees_active
   ```

2. **Get payroll run with records**
   ```sql
   SELECT r.*, pr.*
   FROM payroll_runs r
   JOIN payroll_records pr ON pr.payroll_run_id = r.id
   WHERE r.id = ? AND r.user_id = ?;
   -- Uses: PK on payroll_runs, idx_payroll_records_run
   ```

3. **Employee pay history**
   ```sql
   SELECT pr.*, p.pay_date
   FROM payroll_records pr
   JOIN payroll_runs p ON p.id = pr.payroll_run_id
   WHERE pr.employee_id = ?
   ORDER BY p.pay_date DESC;
   -- Uses: idx_payroll_records_employee
   ```

### Estimated Row Counts

| Table | Per Ledger | Growth Rate |
|-------|-----------|-------------|
| employees | 10-500 | Low (staff changes) |
| payroll_runs | 12-52/year | Linear (pay frequency) |
| payroll_records | employees × runs | Linear |

For a company with 50 employees, bi-weekly pay:
- employees: 50 rows
- payroll_runs: 26/year
- payroll_records: 1,300/year (50 × 26)

After 5 years: ~6,500 payroll_records per ledger.

---

---

## Table: companies (Added 2025-12-16)

Stores company information, CRA remittance configuration, and bookkeeping integration.

### Schema

```sql
CREATE TABLE IF NOT EXISTS companies (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Multi-tenancy
    user_id TEXT NOT NULL,

    -- Company Information
    company_name TEXT NOT NULL,
    business_number CHAR(9) NOT NULL,  -- 9-digit CRA Business Number
    payroll_account_number CHAR(15) NOT NULL,  -- e.g., 123456789RP0001
    province TEXT NOT NULL CHECK (
        province IN (
            'AB', 'BC', 'MB', 'NB', 'NL', 'NS',
            'NT', 'NU', 'ON', 'PE', 'SK', 'YT'
        )
    ),

    -- CRA Remittance Configuration
    remitter_type TEXT NOT NULL DEFAULT 'regular' CHECK (
        remitter_type IN ('quarterly', 'regular', 'threshold_1', 'threshold_2')
    ),

    -- Payroll Preferences
    auto_calculate_deductions BOOLEAN DEFAULT TRUE,
    send_paystub_emails BOOLEAN DEFAULT FALSE,

    -- Bookkeeping Integration
    bookkeeping_ledger_id TEXT,
    bookkeeping_ledger_name TEXT,
    bookkeeping_connected_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT unique_company_per_user UNIQUE (user_id, business_number)
);
```

### Remitter Types

| Type | AMWA Range | Frequency |
|------|-----------|-----------|
| quarterly | < $3,000 | 4 times/year |
| regular | $3,000 - $24,999 | Monthly |
| threshold_1 | $25,000 - $99,999 | Twice monthly |
| threshold_2 | >= $100,000 | Up to 4x monthly |

---

## Table: pay_groups (Updated 2025-12-28)

Pay Group "Policy Template" - defines payroll configuration for groups of employees.

### Schema

```sql
CREATE TABLE IF NOT EXISTS pay_groups (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign Key to Company
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,

    -- Basic Info
    name TEXT NOT NULL,
    description TEXT,
    pay_frequency TEXT NOT NULL CHECK (
        pay_frequency IN ('weekly', 'bi_weekly', 'semi_monthly', 'monthly')
    ),
    employment_type TEXT NOT NULL DEFAULT 'full_time' CHECK (
        employment_type IN ('full_time', 'part_time')
    ),

    -- Pay Schedule (renamed 2025-12-28: next_pay_date → next_period_end)
    next_period_end DATE NOT NULL,  -- Period end date; pay date calculated based on province
    period_start_day TEXT NOT NULL DEFAULT 'monday',

    -- Leave Policy
    leave_enabled BOOLEAN DEFAULT TRUE,

    -- Tax Calculation Configuration
    tax_calculation_method TEXT NOT NULL DEFAULT 'annualization' CHECK (
        tax_calculation_method IN ('annualization', 'cumulative_averaging')
    ),

    -- Policy Configurations (JSONB)
    statutory_defaults JSONB DEFAULT '{
        "cppExemptByDefault": false,
        "cpp2ExemptByDefault": false,
        "eiExemptByDefault": false
    }'::JSONB,

    overtime_policy JSONB DEFAULT '{
        "bankTimeEnabled": false,
        "bankTimeRate": 1.5,
        "bankTimeExpiryMonths": 3,
        "requireWrittenAgreement": true
    }'::JSONB,

    wcb_config JSONB DEFAULT '{"enabled": false, "assessmentRate": 0}'::JSONB,

    group_benefits JSONB DEFAULT '{"enabled": false}'::JSONB,

    -- === Structured Configurations (CRA Compliant) - Added 2025-12-24 ===
    earnings_config JSONB DEFAULT '{...}'::JSONB,           -- See EarningsConfig below
    taxable_benefits_config JSONB DEFAULT '{...}'::JSONB,   -- See TaxableBenefitsConfig below
    deductions_config JSONB DEFAULT '{...}'::JSONB,         -- See DeductionsConfig below

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT unique_pay_group_name_per_company UNIQUE (company_id, name)
);
```

### New JSONB Configuration Columns (Added 2025-12-24)

These structured configuration columns replace the former `custom_deductions` column and provide CRA-compliant categorization:

| Column | Description |
|--------|-------------|
| `earnings_config` | Bonus, commission, allowances, custom earnings configuration |
| `taxable_benefits_config` | Automobile, housing, travel assistance, other taxable benefits |
| `deductions_config` | RRSP, union dues, garnishments, custom deductions |

See [docs/15_earnings_deductions_config.md](./15_earnings_deductions_config.md) for complete type definitions and CRA compliance details.

### Employee Foreign Keys

employees 表新增外键关联：

```sql
ALTER TABLE employees
    ADD COLUMN IF NOT EXISTS company_id UUID REFERENCES companies(id) ON DELETE SET NULL;

ALTER TABLE employees
    ADD COLUMN IF NOT EXISTS pay_group_id UUID REFERENCES pay_groups(id) ON DELETE SET NULL;
```

---

## Entity Relationship (Updated)

```
┌─────────────────┐
│    companies    │
├─────────────────┤
│ id (PK)         │
│ user_id         │
│ company_name    │
│ remitter_type   │
└────────┬────────┘
         │ 1:N
         ▼
┌─────────────────┐
│   pay_groups    │
├─────────────────┤
│ id (PK)         │
│ company_id (FK) │
│ name            │
│ pay_frequency   │
│ policies (JSONB)│
└────────┬────────┘
         │ (policy template)
         │
┌────────┴────────┐
│    employees    │
├─────────────────┤
│ id (PK)         │
│ company_id (FK) │──────────┐
│ pay_group_id(FK)│          │
│ ...             │          │
└────────┬────────┘          │
         │ 1:N               │
         ▼                   │
┌─────────────────┐         │
│ payroll_records │         │
├─────────────────┤         │
│ employee_id (FK)├─────────┘
│ payroll_run_id  │
└─────────────────┘
```

---

## Related Documents

- [Architecture Overview](./00_architecture_overview.md) - System architecture
- [Phase 1: Data Layer](./01_phase1_data_layer.md) - Implementation guide
- [Phase 4: API Integration](./04_phase4_api_integration.md) - Repository patterns
- [Implementation Checklist](./implementation_checklist.md) - Progress tracker
