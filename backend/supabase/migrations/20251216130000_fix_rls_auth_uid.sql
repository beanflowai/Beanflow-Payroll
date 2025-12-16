-- =============================================================================
-- FIX RLS POLICIES - Use auth.uid() for Supabase frontend SDK
-- =============================================================================
-- The original policies used current_setting('app.current_user_id') which
-- requires manual setup per request. This migration updates them to use
-- auth.uid() which works automatically with Supabase Auth.
-- =============================================================================

-- Drop existing policies
DROP POLICY IF EXISTS "Users can access own employees" ON employees;
DROP POLICY IF EXISTS "Users can access own payroll runs" ON payroll_runs;
DROP POLICY IF EXISTS "Users can access own payroll records" ON payroll_records;
DROP POLICY IF EXISTS "Users can access own companies" ON companies;
DROP POLICY IF EXISTS "Users can access own pay groups" ON pay_groups;

-- =============================================================================
-- EMPLOYEES - RLS Policies
-- =============================================================================
CREATE POLICY "Users can view own employees"
    ON employees FOR SELECT
    USING (user_id = auth.uid()::text);

CREATE POLICY "Users can insert own employees"
    ON employees FOR INSERT
    WITH CHECK (user_id = auth.uid()::text);

CREATE POLICY "Users can update own employees"
    ON employees FOR UPDATE
    USING (user_id = auth.uid()::text)
    WITH CHECK (user_id = auth.uid()::text);

CREATE POLICY "Users can delete own employees"
    ON employees FOR DELETE
    USING (user_id = auth.uid()::text);

-- =============================================================================
-- PAYROLL_RUNS - RLS Policies
-- =============================================================================
CREATE POLICY "Users can view own payroll runs"
    ON payroll_runs FOR SELECT
    USING (user_id = auth.uid()::text);

CREATE POLICY "Users can insert own payroll runs"
    ON payroll_runs FOR INSERT
    WITH CHECK (user_id = auth.uid()::text);

CREATE POLICY "Users can update own payroll runs"
    ON payroll_runs FOR UPDATE
    USING (user_id = auth.uid()::text)
    WITH CHECK (user_id = auth.uid()::text);

CREATE POLICY "Users can delete own payroll runs"
    ON payroll_runs FOR DELETE
    USING (user_id = auth.uid()::text);

-- =============================================================================
-- PAYROLL_RECORDS - RLS Policies
-- =============================================================================
CREATE POLICY "Users can view own payroll records"
    ON payroll_records FOR SELECT
    USING (user_id = auth.uid()::text);

CREATE POLICY "Users can insert own payroll records"
    ON payroll_records FOR INSERT
    WITH CHECK (user_id = auth.uid()::text);

CREATE POLICY "Users can update own payroll records"
    ON payroll_records FOR UPDATE
    USING (user_id = auth.uid()::text)
    WITH CHECK (user_id = auth.uid()::text);

CREATE POLICY "Users can delete own payroll records"
    ON payroll_records FOR DELETE
    USING (user_id = auth.uid()::text);

-- =============================================================================
-- COMPANIES - RLS Policies
-- =============================================================================
CREATE POLICY "Users can view own companies"
    ON companies FOR SELECT
    USING (user_id = auth.uid()::text);

CREATE POLICY "Users can insert own companies"
    ON companies FOR INSERT
    WITH CHECK (user_id = auth.uid()::text);

CREATE POLICY "Users can update own companies"
    ON companies FOR UPDATE
    USING (user_id = auth.uid()::text)
    WITH CHECK (user_id = auth.uid()::text);

CREATE POLICY "Users can delete own companies"
    ON companies FOR DELETE
    USING (user_id = auth.uid()::text);

-- =============================================================================
-- PAY_GROUPS - RLS Policies (via company relationship)
-- =============================================================================
CREATE POLICY "Users can view own pay groups"
    ON pay_groups FOR SELECT
    USING (
        company_id IN (
            SELECT id FROM companies WHERE user_id = auth.uid()::text
        )
    );

CREATE POLICY "Users can insert own pay groups"
    ON pay_groups FOR INSERT
    WITH CHECK (
        company_id IN (
            SELECT id FROM companies WHERE user_id = auth.uid()::text
        )
    );

CREATE POLICY "Users can update own pay groups"
    ON pay_groups FOR UPDATE
    USING (
        company_id IN (
            SELECT id FROM companies WHERE user_id = auth.uid()::text
        )
    )
    WITH CHECK (
        company_id IN (
            SELECT id FROM companies WHERE user_id = auth.uid()::text
        )
    );

CREATE POLICY "Users can delete own pay groups"
    ON pay_groups FOR DELETE
    USING (
        company_id IN (
            SELECT id FROM companies WHERE user_id = auth.uid()::text
        )
    );
