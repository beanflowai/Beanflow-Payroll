-- Add pay_group_ids column to payroll_runs table
-- This allows filtering payroll runs by pay group and tracking
-- which pay groups are associated with each payroll run.

-- Add the column as TEXT[] (array of text)
ALTER TABLE payroll_runs
ADD COLUMN IF NOT EXISTS pay_group_ids TEXT[] DEFAULT '{}';

-- Add comment for documentation
COMMENT ON COLUMN payroll_runs.pay_group_ids IS 'Array of pay group IDs associated with this payroll run';

-- Add index for efficient filtering
CREATE INDEX IF NOT EXISTS idx_payroll_runs_pay_group_ids
ON payroll_runs USING GIN (pay_group_ids);
