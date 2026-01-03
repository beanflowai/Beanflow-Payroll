-- Profile Change Requests Table
-- Migration: 20260104110000_create_profile_change_requests.sql
-- Purpose: Track employee profile change requests requiring employer approval

-- =============================================================================
-- Main Table
-- =============================================================================
CREATE TABLE profile_change_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    company_id UUID NOT NULL REFERENCES companies(id),
    user_id TEXT NOT NULL,                  -- Employer's user_id for RLS
    change_type TEXT NOT NULL CHECK (change_type IN ('tax_info', 'bank_info')),
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    current_values JSONB NOT NULL,          -- Snapshot of current values
    requested_values JSONB NOT NULL,        -- Requested new values
    attachments TEXT[],                     -- Array of storage keys (e.g., void cheque)
    submitted_at TIMESTAMPTZ DEFAULT NOW(),
    reviewed_at TIMESTAMPTZ,
    reviewed_by TEXT,                       -- Reviewer's user_id
    rejection_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE profile_change_requests IS 'Employee-initiated profile changes requiring employer approval';
COMMENT ON COLUMN profile_change_requests.change_type IS 'Type of change: tax_info (TD1 claims), bank_info (direct deposit)';
COMMENT ON COLUMN profile_change_requests.status IS 'Request status: pending, approved, rejected';
COMMENT ON COLUMN profile_change_requests.current_values IS 'JSON snapshot of current values before change';
COMMENT ON COLUMN profile_change_requests.requested_values IS 'JSON of requested new values';
COMMENT ON COLUMN profile_change_requests.attachments IS 'Array of Supabase Storage keys for supporting documents';

-- =============================================================================
-- Indexes
-- =============================================================================
CREATE INDEX idx_profile_changes_employee_id ON profile_change_requests(employee_id);
CREATE INDEX idx_profile_changes_company_id ON profile_change_requests(company_id);
CREATE INDEX idx_profile_changes_user_id ON profile_change_requests(user_id);
CREATE INDEX idx_profile_changes_status ON profile_change_requests(status);
CREATE INDEX idx_profile_changes_submitted_at ON profile_change_requests(submitted_at DESC);

-- =============================================================================
-- Updated At Trigger
-- =============================================================================
CREATE TRIGGER update_profile_change_requests_updated_at
    BEFORE UPDATE ON profile_change_requests
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- RLS Policies
-- =============================================================================
ALTER TABLE profile_change_requests ENABLE ROW LEVEL SECURITY;

-- Employers can view change requests for their employees
CREATE POLICY "Employers can view change requests" ON profile_change_requests
    FOR SELECT USING (auth.uid()::text = user_id);

-- Employees can view their own change requests (via email matching)
CREATE POLICY "Employees can view own change requests" ON profile_change_requests
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM employees
            WHERE id = profile_change_requests.employee_id
            AND email = (SELECT email FROM auth.users WHERE id = auth.uid())
        )
    );

-- Employees can insert their own change requests
CREATE POLICY "Employees can insert own change requests" ON profile_change_requests
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM employees
            WHERE id = profile_change_requests.employee_id
            AND email = (SELECT email FROM auth.users WHERE id = auth.uid())
        )
    );

-- Employers can update change requests (approve/reject)
CREATE POLICY "Employers can update change requests" ON profile_change_requests
    FOR UPDATE USING (auth.uid()::text = user_id);
