-- =============================================================================
-- ADD EMPLOYEE SNAPSHOTS TO PAYROLL_RECORDS
-- =============================================================================
-- Description: Add snapshot fields to preserve employee data at time of payroll
-- Author: BeanFlow Payroll Team
-- Date: 2025-12-24
-- =============================================================================
--
-- Problem: payroll_records currently JOINs employees table to get name/province
-- If employee changes name or province after payroll, historical records show
-- new data instead of what was calculated at time of payroll.
--
-- Solution: Store snapshots of employee data at time of payroll creation
-- =============================================================================

-- Add snapshot columns to payroll_records
ALTER TABLE payroll_records
ADD COLUMN IF NOT EXISTS employee_name_snapshot TEXT,        -- "First Last" format
ADD COLUMN IF NOT EXISTS province_snapshot TEXT,             -- Province at calculation time
ADD COLUMN IF NOT EXISTS annual_salary_snapshot NUMERIC(12,2), -- Salaried employee annual salary
ADD COLUMN IF NOT EXISTS hourly_rate_snapshot NUMERIC(12,2),  -- Hourly employee rate
ADD COLUMN IF NOT EXISTS pay_group_id_snapshot UUID,         -- Pay group ID at calculation time
ADD COLUMN IF NOT EXISTS pay_group_name_snapshot TEXT;       -- Pay group name at calculation time

-- Add comment explaining usage
COMMENT ON COLUMN payroll_records.employee_name_snapshot IS
    'Employee full name at time of payroll creation. Format: "First Last"';

COMMENT ON COLUMN payroll_records.province_snapshot IS
    'Province of employment at time of payroll calculation. Tax rates depend on this.';

COMMENT ON COLUMN payroll_records.annual_salary_snapshot IS
    'Annual salary for salaried employees at time of payroll. NULL for hourly employees.';

COMMENT ON COLUMN payroll_records.hourly_rate_snapshot IS
    'Hourly rate for hourly employees at time of payroll. NULL for salaried employees.';

COMMENT ON COLUMN payroll_records.pay_group_id_snapshot IS
    'Pay group ID at time of payroll creation. Employee may move groups later.';

COMMENT ON COLUMN payroll_records.pay_group_name_snapshot IS
    'Pay group name at time of payroll creation. For display purposes.';

-- Create index for querying by pay group snapshot (useful for reporting)
CREATE INDEX IF NOT EXISTS idx_payroll_records_pay_group_snapshot
    ON payroll_records(pay_group_id_snapshot)
    WHERE pay_group_id_snapshot IS NOT NULL;
