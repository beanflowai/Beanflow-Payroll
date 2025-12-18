-- =============================================================================
-- ADD HOURS WORKED FIELDS TO PAYROLL_RECORDS
-- =============================================================================
-- Description: Adds fields to track hours worked for hourly employees
-- Author: BeanFlow Payroll Team
-- Date: 2025-12-17
-- =============================================================================

-- Add hours worked fields to payroll_records table
-- These fields are used for hourly employees to track actual hours worked
-- and to snapshot the hourly rate at the time of payroll

ALTER TABLE payroll_records
ADD COLUMN IF NOT EXISTS regular_hours_worked NUMERIC(6, 2),
ADD COLUMN IF NOT EXISTS overtime_hours_worked NUMERIC(6, 2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS hourly_rate_snapshot NUMERIC(10, 2);

-- Add comments for documentation
COMMENT ON COLUMN payroll_records.regular_hours_worked IS 'Regular hours worked for hourly employees. NULL for salaried employees.';
COMMENT ON COLUMN payroll_records.overtime_hours_worked IS 'Overtime hours worked. Default 0.';
COMMENT ON COLUMN payroll_records.hourly_rate_snapshot IS 'Snapshot of hourly rate at time of payroll. NULL for salaried employees.';

-- Create index for querying hourly employees
CREATE INDEX IF NOT EXISTS idx_payroll_records_hourly
    ON payroll_records(employee_id)
    WHERE regular_hours_worked IS NOT NULL;
