-- =============================================================================
-- CONSOLIDATED MIGRATION 004: TAX, REMITTANCE, AND T4
-- =============================================================================
-- Description: Employee tax claims, remittance periods, T4 slips and summaries
-- =============================================================================

-- =============================================================================
-- EMPLOYEE TAX CLAIMS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS employee_tax_claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    tax_year INTEGER NOT NULL,
    federal_bpa DECIMAL(10,2) NOT NULL,
    federal_additional_claims DECIMAL(10,2) DEFAULT 0,
    provincial_bpa DECIMAL(10,2) NOT NULL,
    provincial_additional_claims DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(employee_id, tax_year)
);

CREATE INDEX IF NOT EXISTS idx_employee_tax_claims_lookup ON employee_tax_claims(employee_id, tax_year);
CREATE INDEX IF NOT EXISTS idx_employee_tax_claims_company ON employee_tax_claims(company_id, tax_year);

ALTER TABLE employee_tax_claims ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can access their company tax claims" ON employee_tax_claims
    FOR ALL USING (user_id = auth.uid());

CREATE OR REPLACE FUNCTION update_employee_tax_claims_updated_at()
RETURNS TRIGGER AS $$ BEGIN NEW.updated_at = NOW(); RETURN NEW; END; $$ LANGUAGE plpgsql;

CREATE TRIGGER employee_tax_claims_updated_at
    BEFORE UPDATE ON employee_tax_claims FOR EACH ROW
    EXECUTE FUNCTION update_employee_tax_claims_updated_at();

COMMENT ON TABLE employee_tax_claims IS 'Stores TD1 tax claims by year for each employee. BPA values are read-only and come from tax configuration.';

-- =============================================================================
-- REMITTANCE PERIODS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS remittance_periods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,
    remitter_type TEXT NOT NULL CHECK (remitter_type IN ('quarterly', 'regular', 'threshold_1', 'threshold_2')),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    due_date DATE NOT NULL,
    cpp_employee NUMERIC(12, 2) DEFAULT 0,
    ei_employee NUMERIC(12, 2) DEFAULT 0,
    federal_tax NUMERIC(12, 2) DEFAULT 0,
    provincial_tax NUMERIC(12, 2) DEFAULT 0,
    cpp_employer NUMERIC(12, 2) DEFAULT 0,
    ei_employer NUMERIC(12, 2) DEFAULT 0,
    total_amount NUMERIC(14, 2) GENERATED ALWAYS AS (
        cpp_employee + cpp_employer + ei_employee + ei_employer + federal_tax + provincial_tax
    ) STORED,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'due_soon', 'overdue', 'paid', 'paid_late')),
    paid_date DATE,
    payment_method TEXT CHECK (payment_method IS NULL OR payment_method IN (
        'my_payment', 'pre_authorized_debit', 'online_banking', 'wire_transfer', 'cheque'
    )),
    confirmation_number TEXT,
    notes TEXT,
    days_overdue INTEGER DEFAULT 0,
    penalty_rate NUMERIC(5, 4) DEFAULT 0,
    penalty_amount NUMERIC(10, 2) DEFAULT 0,
    payroll_run_ids UUID[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT chk_period_dates CHECK (period_end >= period_start),
    CONSTRAINT chk_due_date CHECK (due_date > period_end),
    CONSTRAINT unique_company_period UNIQUE (company_id, period_start, period_end)
);

CREATE INDEX idx_remittance_company ON remittance_periods(company_id);
CREATE INDEX idx_remittance_user ON remittance_periods(user_id);
CREATE INDEX idx_remittance_status ON remittance_periods(status);
CREATE INDEX idx_remittance_due_date ON remittance_periods(due_date);
CREATE INDEX idx_remittance_pending ON remittance_periods(company_id, status) WHERE status IN ('pending', 'due_soon', 'overdue');

ALTER TABLE remittance_periods ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own remittance_periods" ON remittance_periods FOR SELECT USING (user_id = auth.uid()::text);
CREATE POLICY "Users can insert own remittance_periods" ON remittance_periods FOR INSERT WITH CHECK (user_id = auth.uid()::text);
CREATE POLICY "Users can update own remittance_periods" ON remittance_periods FOR UPDATE USING (user_id = auth.uid()::text);
CREATE POLICY "Users can delete own remittance_periods" ON remittance_periods FOR DELETE USING (user_id = auth.uid()::text);

CREATE TRIGGER update_remittance_periods_updated_at
    BEFORE UPDATE ON remittance_periods FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- T4 SLIPS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS t4_slips (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    tax_year INTEGER NOT NULL,
    slip_number INTEGER,
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'generated', 'amended', 'filed')),
    slip_data JSONB NOT NULL,
    pdf_storage_key TEXT,
    pdf_generated_at TIMESTAMPTZ,
    original_slip_id UUID REFERENCES t4_slips(id),
    amendment_number INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_employee_year_slip UNIQUE (company_id, employee_id, tax_year, amendment_number)
);

CREATE INDEX IF NOT EXISTS idx_t4_slips_company_year ON t4_slips(company_id, tax_year);
CREATE INDEX IF NOT EXISTS idx_t4_slips_employee ON t4_slips(employee_id);
CREATE INDEX IF NOT EXISTS idx_t4_slips_status ON t4_slips(status);
CREATE INDEX IF NOT EXISTS idx_t4_slips_user ON t4_slips(user_id);

ALTER TABLE t4_slips ENABLE ROW LEVEL SECURITY;

CREATE POLICY t4_slips_select ON t4_slips FOR SELECT USING (auth.uid()::text = user_id);
CREATE POLICY t4_slips_insert ON t4_slips FOR INSERT WITH CHECK (auth.uid()::text = user_id);
CREATE POLICY t4_slips_update ON t4_slips FOR UPDATE USING (auth.uid()::text = user_id);
CREATE POLICY t4_slips_delete ON t4_slips FOR DELETE USING (auth.uid()::text = user_id);

-- =============================================================================
-- T4 SUMMARIES TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS t4_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,
    tax_year INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'generated', 'amended', 'filed')),
    total_number_of_t4_slips INTEGER NOT NULL DEFAULT 0,
    total_employment_income NUMERIC(15,2) NOT NULL DEFAULT 0,
    total_cpp_contributions NUMERIC(15,2) NOT NULL DEFAULT 0,
    total_cpp2_contributions NUMERIC(15,2) NOT NULL DEFAULT 0,
    total_ei_premiums NUMERIC(15,2) NOT NULL DEFAULT 0,
    total_income_tax_deducted NUMERIC(15,2) NOT NULL DEFAULT 0,
    total_union_dues NUMERIC(15,2) NOT NULL DEFAULT 0,
    total_cpp_employer NUMERIC(15,2) NOT NULL DEFAULT 0,
    total_ei_employer NUMERIC(15,2) NOT NULL DEFAULT 0,
    remittance_difference NUMERIC(15,2) NOT NULL DEFAULT 0,
    pdf_storage_key TEXT,
    xml_storage_key TEXT,
    generated_at TIMESTAMPTZ,
    -- CRA submission tracking
    cra_confirmation_number TEXT,
    submitted_at TIMESTAMPTZ,
    submitted_by TEXT,
    submission_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_company_year_summary UNIQUE (company_id, tax_year)
);

CREATE INDEX IF NOT EXISTS idx_t4_summaries_company ON t4_summaries(company_id);
CREATE INDEX IF NOT EXISTS idx_t4_summaries_year ON t4_summaries(tax_year);
CREATE INDEX IF NOT EXISTS idx_t4_summaries_user ON t4_summaries(user_id);
CREATE INDEX IF NOT EXISTS idx_t4_summaries_cra_confirmation ON t4_summaries(cra_confirmation_number) WHERE cra_confirmation_number IS NOT NULL;

ALTER TABLE t4_summaries ENABLE ROW LEVEL SECURITY;

CREATE POLICY t4_summaries_select ON t4_summaries FOR SELECT USING (auth.uid()::text = user_id);
CREATE POLICY t4_summaries_insert ON t4_summaries FOR INSERT WITH CHECK (auth.uid()::text = user_id);
CREATE POLICY t4_summaries_update ON t4_summaries FOR UPDATE USING (auth.uid()::text = user_id);
CREATE POLICY t4_summaries_delete ON t4_summaries FOR DELETE USING (auth.uid()::text = user_id);

-- T4 updated_at triggers
CREATE OR REPLACE FUNCTION update_t4_updated_at()
RETURNS TRIGGER AS $$ BEGIN NEW.updated_at = NOW(); RETURN NEW; END; $$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_t4_slips_updated_at BEFORE UPDATE ON t4_slips FOR EACH ROW EXECUTE FUNCTION update_t4_updated_at();
CREATE TRIGGER trigger_t4_summaries_updated_at BEFORE UPDATE ON t4_summaries FOR EACH ROW EXECUTE FUNCTION update_t4_updated_at();

COMMENT ON TABLE t4_slips IS 'T4 Statement of Remuneration Paid - individual employee slips';
COMMENT ON TABLE t4_summaries IS 'T4 Summary - aggregated totals for employer submission to CRA';
