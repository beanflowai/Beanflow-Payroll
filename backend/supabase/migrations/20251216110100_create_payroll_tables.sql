-- =============================================================================
-- PAYROLL MODULE - DATABASE SCHEMA
-- =============================================================================
-- Description: Creates tables for employee management and payroll processing
-- Author: BeanFlow Payroll Team
-- Date: 2025-12-16
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
-- Employee master data for payroll processing
-- Stores TD1 claim amounts, salary info, and payroll configuration

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

-- Indexes for employees
CREATE INDEX IF NOT EXISTS idx_employees_user_ledger
    ON employees(user_id, ledger_id);

CREATE INDEX IF NOT EXISTS idx_employees_province
    ON employees(province_of_employment);

CREATE INDEX IF NOT EXISTS idx_employees_active
    ON employees(user_id, ledger_id)
    WHERE termination_date IS NULL;

-- RLS Policy for employees
ALTER TABLE employees ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can access own employees"
    ON employees
    FOR ALL
    USING (user_id = current_setting('app.current_user_id', TRUE));

-- Trigger for updated_at
CREATE TRIGGER update_employees_updated_at
    BEFORE UPDATE ON employees
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- PAYROLL_RUNS TABLE
-- =============================================================================
-- Payroll run header - groups all employee payments for a pay period

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

-- Indexes for payroll_runs
CREATE INDEX IF NOT EXISTS idx_payroll_runs_user_ledger
    ON payroll_runs(user_id, ledger_id);

CREATE INDEX IF NOT EXISTS idx_payroll_runs_status
    ON payroll_runs(status);

CREATE INDEX IF NOT EXISTS idx_payroll_runs_pay_date
    ON payroll_runs(pay_date DESC);

CREATE INDEX IF NOT EXISTS idx_payroll_runs_period
    ON payroll_runs(user_id, ledger_id, period_start, period_end);

-- RLS Policy for payroll_runs
ALTER TABLE payroll_runs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can access own payroll runs"
    ON payroll_runs
    FOR ALL
    USING (user_id = current_setting('app.current_user_id', TRUE));

-- Trigger for updated_at
CREATE TRIGGER update_payroll_runs_updated_at
    BEFORE UPDATE ON payroll_runs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- PAYROLL_RECORDS TABLE
-- =============================================================================
-- Individual employee pay record for each payroll run

CREATE TABLE IF NOT EXISTS payroll_records (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign Keys
    payroll_run_id UUID NOT NULL REFERENCES payroll_runs(id) ON DELETE CASCADE,
    employee_id UUID NOT NULL REFERENCES employees(id),

    -- Multi-tenancy (denormalized for RLS)
    user_id TEXT NOT NULL,
    ledger_id TEXT NOT NULL,

    -- Earnings
    gross_regular NUMERIC(12, 2) NOT NULL,
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

    -- Vacation Tracking
    vacation_accrued NUMERIC(10, 2) DEFAULT 0,
    vacation_hours_taken NUMERIC(6, 2) DEFAULT 0,

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

-- Indexes for payroll_records
CREATE INDEX IF NOT EXISTS idx_payroll_records_run
    ON payroll_records(payroll_run_id);

CREATE INDEX IF NOT EXISTS idx_payroll_records_employee
    ON payroll_records(employee_id);

CREATE INDEX IF NOT EXISTS idx_payroll_records_user_ledger
    ON payroll_records(user_id, ledger_id);

CREATE INDEX IF NOT EXISTS idx_payroll_records_paystub
    ON payroll_records(paystub_storage_key)
    WHERE paystub_storage_key IS NOT NULL;

-- RLS Policy for payroll_records
ALTER TABLE payroll_records ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can access own payroll records"
    ON payroll_records
    FOR ALL
    USING (user_id = current_setting('app.current_user_id', TRUE));
