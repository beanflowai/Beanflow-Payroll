-- Migration: Add portal status tracking to employees table
-- Purpose: Track employee portal invitation and access status

-- Add portal_status column with check constraint
ALTER TABLE employees ADD COLUMN IF NOT EXISTS portal_status TEXT DEFAULT 'not_set'
    CHECK (portal_status IN ('not_set', 'invited', 'active', 'disabled'));

-- Add portal tracking timestamps
ALTER TABLE employees ADD COLUMN IF NOT EXISTS portal_invited_at TIMESTAMPTZ;
ALTER TABLE employees ADD COLUMN IF NOT EXISTS portal_last_login_at TIMESTAMPTZ;

-- Index for filtering by portal status (useful for employer dashboard)
CREATE INDEX IF NOT EXISTS idx_employees_portal_status ON employees(portal_status);

-- Add comment for documentation
COMMENT ON COLUMN employees.portal_status IS 'Employee portal access status: not_set, invited, active, disabled';
COMMENT ON COLUMN employees.portal_invited_at IS 'Timestamp when portal invitation was sent';
COMMENT ON COLUMN employees.portal_last_login_at IS 'Timestamp of last portal login';
