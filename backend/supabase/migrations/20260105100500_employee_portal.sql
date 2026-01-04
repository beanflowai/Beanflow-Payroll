-- =============================================================================
-- CONSOLIDATED MIGRATION 006: EMPLOYEE PORTAL
-- =============================================================================
-- Description: Profile change requests and employee portal RLS policies
-- Note: portal_status fields are already in employees table (core_schema)
-- =============================================================================

-- =============================================================================
-- PROFILE CHANGE REQUESTS TABLE
-- =============================================================================

CREATE TABLE profile_change_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    company_id UUID NOT NULL REFERENCES companies(id),
    user_id TEXT NOT NULL,
    change_type TEXT NOT NULL CHECK (change_type IN ('tax_info', 'bank_info')),
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    current_values JSONB NOT NULL,
    requested_values JSONB NOT NULL,
    attachments TEXT[],
    submitted_at TIMESTAMPTZ DEFAULT NOW(),
    reviewed_at TIMESTAMPTZ,
    reviewed_by TEXT,
    rejection_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_profile_changes_employee_id ON profile_change_requests(employee_id);
CREATE INDEX idx_profile_changes_company_id ON profile_change_requests(company_id);
CREATE INDEX idx_profile_changes_user_id ON profile_change_requests(user_id);
CREATE INDEX idx_profile_changes_status ON profile_change_requests(status);
CREATE INDEX idx_profile_changes_submitted_at ON profile_change_requests(submitted_at DESC);

ALTER TABLE profile_change_requests ENABLE ROW LEVEL SECURITY;

-- Employers can view/update change requests for their employees
CREATE POLICY "Employers can view change requests" ON profile_change_requests
    FOR SELECT USING (auth.uid()::text = user_id);

CREATE POLICY "Employers can update change requests" ON profile_change_requests
    FOR UPDATE USING (auth.uid()::text = user_id);

-- Employees can view their own change requests (via JWT email)
CREATE POLICY "Employees can view own change requests" ON profile_change_requests
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM employees
            WHERE id = profile_change_requests.employee_id
            AND email = (auth.jwt() ->> 'email')
        )
    );

-- Employees can insert their own change requests
CREATE POLICY "Employees can insert own change requests" ON profile_change_requests
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM employees
            WHERE id = profile_change_requests.employee_id
            AND email = (auth.jwt() ->> 'email')
        )
    );

CREATE TRIGGER update_profile_change_requests_updated_at
    BEFORE UPDATE ON profile_change_requests FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE profile_change_requests IS 'Employee-initiated profile changes requiring employer approval';

-- =============================================================================
-- EMPLOYEE PORTAL RLS POLICIES
-- =============================================================================
-- These policies allow employees to access their own records via email matching
-- Uses auth.jwt() ->> 'email' (not auth.users table query) to avoid permission errors

-- Employees can view their own record
CREATE POLICY "Employees can view own record via email" ON employees
    FOR SELECT USING (email = (auth.jwt() ->> 'email'));

-- Employees can update their own record (for personal info updates)
CREATE POLICY "Employees can update own record via email" ON employees
    FOR UPDATE USING (email = (auth.jwt() ->> 'email'));

-- Employees can view their own payroll records
CREATE POLICY "Employees can view own payroll records via email" ON payroll_records
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM employees
            WHERE employees.id = payroll_records.employee_id
            AND employees.email = (auth.jwt() ->> 'email')
        )
    );

-- Employees can view their own T4 slips
CREATE POLICY "Employees can view own t4 slips via email" ON t4_slips
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM employees
            WHERE employees.id = t4_slips.employee_id
            AND employees.email = (auth.jwt() ->> 'email')
        )
    );

-- Employees can view payroll runs (needed for joining with payroll_records)
CREATE POLICY "Employees can view payroll runs via email" ON payroll_runs
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM payroll_records pr
            JOIN employees e ON e.id = pr.employee_id
            WHERE pr.payroll_run_id = payroll_runs.id
            AND e.email = (auth.jwt() ->> 'email')
        )
    );

-- Employees can read their company's slug (for portal routing)
CREATE POLICY "Employees can read own company slug" ON companies
    FOR SELECT USING (
        id IN (
            SELECT company_id FROM employees
            WHERE email = (auth.jwt() ->> 'email')
        )
    );
