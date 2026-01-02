-- Migration: Add employee_tax_claims table for year-specific TD1 claims
-- Reason: BPA changes annually, employees' situations may change each year,
-- and historical payroll calculations need historical claims data

-- Create the employee_tax_claims table
CREATE TABLE IF NOT EXISTS employee_tax_claims (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    tax_year INTEGER NOT NULL,

    -- Federal TD1
    federal_bpa DECIMAL(10,2) NOT NULL,           -- From config, read-only in UI
    federal_additional_claims DECIMAL(10,2) DEFAULT 0,
    -- Note: total_claim is calculated as bpa + additional_claims in application layer

    -- Provincial TD1
    provincial_bpa DECIMAL(10,2) NOT NULL,        -- From config, read-only in UI
    provincial_additional_claims DECIMAL(10,2) DEFAULT 0,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Unique constraint: one record per employee per year
    UNIQUE(employee_id, tax_year)
);

-- Index for efficient lookups
CREATE INDEX IF NOT EXISTS idx_employee_tax_claims_lookup ON employee_tax_claims(employee_id, tax_year);
CREATE INDEX IF NOT EXISTS idx_employee_tax_claims_company ON employee_tax_claims(company_id, tax_year);

-- RLS Policy
ALTER TABLE employee_tax_claims ENABLE ROW LEVEL SECURITY;

-- Policy: Users can access their own company's tax claims
CREATE POLICY "Users can access their company tax claims" ON employee_tax_claims
    FOR ALL USING (user_id = auth.uid());

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_employee_tax_claims_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER employee_tax_claims_updated_at
    BEFORE UPDATE ON employee_tax_claims
    FOR EACH ROW
    EXECUTE FUNCTION update_employee_tax_claims_updated_at();

-- Note: No backfill of existing employees
-- Tax claims are created on-demand by the application when running payroll.
-- This ensures BPA values are correctly derived from tax configuration
-- based on each employee's province, rather than using incorrect placeholder values.
--
-- The application will create tax claim records with proper BPA values when:
-- 1. User creates a new employee
-- 2. User runs payroll for the first time in a tax year
-- 3. User explicitly manages tax claims through the UI

COMMENT ON TABLE employee_tax_claims IS 'Stores TD1 tax claims by year for each employee. BPA values are read-only and come from tax configuration.';
COMMENT ON COLUMN employee_tax_claims.federal_bpa IS 'Federal Basic Personal Amount for the tax year (from tax config, read-only)';
COMMENT ON COLUMN employee_tax_claims.federal_additional_claims IS 'Additional federal TD1 claims (employee-entered)';
COMMENT ON COLUMN employee_tax_claims.provincial_bpa IS 'Provincial Basic Personal Amount for the tax year (from tax config, read-only)';
COMMENT ON COLUMN employee_tax_claims.provincial_additional_claims IS 'Additional provincial TD1 claims (employee-entered)';
