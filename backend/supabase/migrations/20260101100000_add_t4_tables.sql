-- T4 Year-End Processing Tables
-- Creates tables for T4 slip storage and T4 summary reporting

-- =============================================================================
-- T4 Slips Table
-- =============================================================================

CREATE TABLE IF NOT EXISTS t4_slips (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    tax_year INTEGER NOT NULL,
    slip_number INTEGER,

    -- Status tracking
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'generated', 'amended', 'filed')),

    -- T4 Box Data (stored as JSONB for flexibility)
    slip_data JSONB NOT NULL,

    -- Storage
    pdf_storage_key TEXT,
    pdf_generated_at TIMESTAMPTZ,

    -- Amendment tracking
    original_slip_id UUID REFERENCES t4_slips(id),
    amendment_number INTEGER NOT NULL DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT unique_employee_year_slip UNIQUE (company_id, employee_id, tax_year, amendment_number)
);

-- Indexes for T4 slips
CREATE INDEX IF NOT EXISTS idx_t4_slips_company_year ON t4_slips(company_id, tax_year);
CREATE INDEX IF NOT EXISTS idx_t4_slips_employee ON t4_slips(employee_id);
CREATE INDEX IF NOT EXISTS idx_t4_slips_status ON t4_slips(status);
CREATE INDEX IF NOT EXISTS idx_t4_slips_user ON t4_slips(user_id);

-- =============================================================================
-- T4 Summaries Table
-- =============================================================================

CREATE TABLE IF NOT EXISTS t4_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,
    tax_year INTEGER NOT NULL,

    -- Status
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'generated', 'amended', 'filed')),

    -- Summary totals
    total_number_of_t4_slips INTEGER NOT NULL DEFAULT 0,
    total_employment_income NUMERIC(15,2) NOT NULL DEFAULT 0,
    total_cpp_contributions NUMERIC(15,2) NOT NULL DEFAULT 0,
    total_cpp2_contributions NUMERIC(15,2) NOT NULL DEFAULT 0,
    total_ei_premiums NUMERIC(15,2) NOT NULL DEFAULT 0,
    total_income_tax_deducted NUMERIC(15,2) NOT NULL DEFAULT 0,
    total_union_dues NUMERIC(15,2) NOT NULL DEFAULT 0,

    -- Employer contributions
    total_cpp_employer NUMERIC(15,2) NOT NULL DEFAULT 0,
    total_ei_employer NUMERIC(15,2) NOT NULL DEFAULT 0,

    -- Reconciliation
    remittance_difference NUMERIC(15,2) NOT NULL DEFAULT 0,

    -- Storage
    pdf_storage_key TEXT,
    xml_storage_key TEXT,
    generated_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT unique_company_year_summary UNIQUE (company_id, tax_year)
);

-- Indexes for T4 summaries
CREATE INDEX IF NOT EXISTS idx_t4_summaries_company ON t4_summaries(company_id);
CREATE INDEX IF NOT EXISTS idx_t4_summaries_year ON t4_summaries(tax_year);
CREATE INDEX IF NOT EXISTS idx_t4_summaries_user ON t4_summaries(user_id);

-- =============================================================================
-- Triggers for updated_at
-- =============================================================================

CREATE OR REPLACE FUNCTION update_t4_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_t4_slips_updated_at
    BEFORE UPDATE ON t4_slips
    FOR EACH ROW
    EXECUTE FUNCTION update_t4_updated_at();

CREATE TRIGGER trigger_t4_summaries_updated_at
    BEFORE UPDATE ON t4_summaries
    FOR EACH ROW
    EXECUTE FUNCTION update_t4_updated_at();

-- =============================================================================
-- Row Level Security (RLS)
-- =============================================================================

ALTER TABLE t4_slips ENABLE ROW LEVEL SECURITY;
ALTER TABLE t4_summaries ENABLE ROW LEVEL SECURITY;

-- T4 Slips policies
CREATE POLICY t4_slips_select ON t4_slips
    FOR SELECT
    USING (auth.uid()::text = user_id);

CREATE POLICY t4_slips_insert ON t4_slips
    FOR INSERT
    WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY t4_slips_update ON t4_slips
    FOR UPDATE
    USING (auth.uid()::text = user_id);

CREATE POLICY t4_slips_delete ON t4_slips
    FOR DELETE
    USING (auth.uid()::text = user_id);

-- T4 Summaries policies
CREATE POLICY t4_summaries_select ON t4_summaries
    FOR SELECT
    USING (auth.uid()::text = user_id);

CREATE POLICY t4_summaries_insert ON t4_summaries
    FOR INSERT
    WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY t4_summaries_update ON t4_summaries
    FOR UPDATE
    USING (auth.uid()::text = user_id);

CREATE POLICY t4_summaries_delete ON t4_summaries
    FOR DELETE
    USING (auth.uid()::text = user_id);

-- =============================================================================
-- Comments
-- =============================================================================

COMMENT ON TABLE t4_slips IS 'T4 Statement of Remuneration Paid - individual employee slips';
COMMENT ON TABLE t4_summaries IS 'T4 Summary - aggregated totals for employer submission to CRA';

COMMENT ON COLUMN t4_slips.slip_data IS 'JSONB containing all T4 box data (box_14, box_16, etc.)';
COMMENT ON COLUMN t4_slips.amendment_number IS '0 for original, 1+ for amendments';
COMMENT ON COLUMN t4_summaries.remittance_difference IS 'Difference between calculated and remitted amounts for reconciliation';
