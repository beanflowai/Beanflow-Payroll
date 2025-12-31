-- =============================================================================
-- REMITTANCE PERIODS TABLE
-- =============================================================================
-- Description: Tracks CRA remittance obligations and payment recording
-- Reference: docs/10_remittance_reporting.md
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Table: remittance_periods
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS remittance_periods (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign Key to Company
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,

    -- Multi-tenancy
    user_id TEXT NOT NULL,

    -- Remitter Configuration (snapshot at time of creation)
    remitter_type TEXT NOT NULL CHECK (
        remitter_type IN ('quarterly', 'regular', 'threshold_1', 'threshold_2')
    ),

    -- Period Information
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    due_date DATE NOT NULL,

    -- Employee Deductions
    cpp_employee NUMERIC(12, 2) DEFAULT 0,
    ei_employee NUMERIC(12, 2) DEFAULT 0,
    federal_tax NUMERIC(12, 2) DEFAULT 0,
    provincial_tax NUMERIC(12, 2) DEFAULT 0,

    -- Employer Portions
    cpp_employer NUMERIC(12, 2) DEFAULT 0,
    ei_employer NUMERIC(12, 2) DEFAULT 0,

    -- Generated Column: Total Remittance
    total_amount NUMERIC(14, 2) GENERATED ALWAYS AS (
        cpp_employee + cpp_employer +
        ei_employee + ei_employer +
        federal_tax + provincial_tax
    ) STORED,

    -- Payment Tracking
    status TEXT DEFAULT 'pending' CHECK (
        status IN ('pending', 'due_soon', 'overdue', 'paid', 'paid_late')
    ),
    paid_date DATE,
    payment_method TEXT CHECK (
        payment_method IS NULL OR payment_method IN (
            'my_payment', 'pre_authorized_debit', 'online_banking',
            'wire_transfer', 'cheque'
        )
    ),
    confirmation_number TEXT,
    notes TEXT,

    -- Penalty (calculated if overdue)
    days_overdue INTEGER DEFAULT 0,
    penalty_rate NUMERIC(5, 4) DEFAULT 0,
    penalty_amount NUMERIC(10, 2) DEFAULT 0,

    -- Linked Payroll Runs (for audit)
    payroll_run_ids UUID[] DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT chk_period_dates CHECK (period_end >= period_start),
    CONSTRAINT chk_due_date CHECK (due_date > period_end),
    CONSTRAINT unique_company_period UNIQUE (company_id, period_start, period_end)
);

-- -----------------------------------------------------------------------------
-- Indexes
-- -----------------------------------------------------------------------------

-- Primary query path
CREATE INDEX idx_remittance_company ON remittance_periods(company_id);

-- User multi-tenancy
CREATE INDEX idx_remittance_user ON remittance_periods(user_id);

-- Status queries (dashboard)
CREATE INDEX idx_remittance_status ON remittance_periods(status);

-- Due date sorting
CREATE INDEX idx_remittance_due_date ON remittance_periods(due_date);

-- Pending remittances (common filter)
CREATE INDEX idx_remittance_pending ON remittance_periods(company_id, status)
    WHERE status IN ('pending', 'due_soon', 'overdue');

-- -----------------------------------------------------------------------------
-- Row Level Security
-- -----------------------------------------------------------------------------

ALTER TABLE remittance_periods ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own remittance_periods"
    ON remittance_periods FOR SELECT
    USING (user_id = auth.uid()::text);

CREATE POLICY "Users can insert own remittance_periods"
    ON remittance_periods FOR INSERT
    WITH CHECK (user_id = auth.uid()::text);

CREATE POLICY "Users can update own remittance_periods"
    ON remittance_periods FOR UPDATE
    USING (user_id = auth.uid()::text);

CREATE POLICY "Users can delete own remittance_periods"
    ON remittance_periods FOR DELETE
    USING (user_id = auth.uid()::text);

-- -----------------------------------------------------------------------------
-- Triggers
-- -----------------------------------------------------------------------------

CREATE TRIGGER update_remittance_periods_updated_at
    BEFORE UPDATE ON remittance_periods
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
