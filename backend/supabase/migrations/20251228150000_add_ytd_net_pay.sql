-- Add ytd_net_pay column to payroll_records table
-- This stores the cumulative net pay for accurate YTD display

ALTER TABLE payroll_records ADD COLUMN IF NOT EXISTS ytd_net_pay NUMERIC(14, 2) DEFAULT 0;

-- Add comment for documentation
COMMENT ON COLUMN payroll_records.ytd_net_pay IS 'Year-to-date cumulative net pay (sum of all net_pay from Jan 1)';
