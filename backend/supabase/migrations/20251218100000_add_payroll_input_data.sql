-- =============================================================================
-- Add input_data and is_modified columns to payroll_records table
-- =============================================================================
-- Description: Supports editing payroll data in draft state
-- Author: BeanFlow Payroll Team
-- Date: 2025-12-18
-- =============================================================================

-- Add input_data column to store original input data for recalculation
-- Structure:
-- {
--   "regularHours": 80,
--   "overtimeHours": 5,
--   "leaveEntries": [{"type": "vacation", "hours": 8}],
--   "holidayWorkEntries": [],
--   "adjustments": [{"type": "bonus", "amount": 100, "description": "...", "taxable": true}],
--   "overrides": {"regularPay": null, "overtimePay": null}
-- }
ALTER TABLE payroll_records
ADD COLUMN IF NOT EXISTS input_data JSONB DEFAULT NULL;

-- Add is_modified flag to track if record has been edited since last calculation
ALTER TABLE payroll_records
ADD COLUMN IF NOT EXISTS is_modified BOOLEAN DEFAULT FALSE;

-- Add comment for documentation
COMMENT ON COLUMN payroll_records.input_data IS 'Original input data for recalculation (hours, leave, adjustments, overrides)';
COMMENT ON COLUMN payroll_records.is_modified IS 'True if record has been edited since last calculation';
