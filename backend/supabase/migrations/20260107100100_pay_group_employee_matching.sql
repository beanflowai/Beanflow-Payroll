-- Migration: Pay Group Employee Matching Enhancement
-- Description:
--   1. Extend pay_groups.employment_type to support 5 types (full_time, part_time, seasonal, contract, casual)
--   2. Add compensation_type field to pay_groups (salary, hourly)
-- Date: 2026-01-07

-- ============================================================================
-- PRE-MIGRATION VALIDATION
-- ============================================================================

-- Verify no existing data has employment_type values outside the new allowed set
DO $$
DECLARE
    invalid_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO invalid_count FROM pay_groups
    WHERE employment_type NOT IN ('full_time', 'part_time', 'seasonal', 'contract', 'casual');

    IF invalid_count > 0 THEN
        RAISE EXCEPTION 'Found % pay_groups with invalid employment_type values. Please fix data before running migration.', invalid_count;
    END IF;
END $$;

-- ============================================================================
-- 1. Extend pay_groups.employment_type to support 5 types
-- ============================================================================

-- Drop the existing constraint
ALTER TABLE pay_groups
DROP CONSTRAINT IF EXISTS pay_groups_employment_type_check;

-- Add new constraint with 5 types
ALTER TABLE pay_groups
ADD CONSTRAINT pay_groups_employment_type_check
CHECK (employment_type IN ('full_time', 'part_time', 'seasonal', 'contract', 'casual'));

-- ============================================================================
-- 1.5. Extend employees.employment_type to support 5 types
-- ============================================================================

-- Verify no existing data has employment_type values outside the new allowed set
DO $$
DECLARE
    invalid_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO invalid_count FROM employees
    WHERE employment_type NOT IN ('full_time', 'part_time', 'seasonal', 'contract', 'casual');

    IF invalid_count > 0 THEN
        RAISE EXCEPTION 'Found % employees with invalid employment_type values. Please fix data before running migration.', invalid_count;
    END IF;
END $$;

-- Drop the existing constraint
ALTER TABLE employees
DROP CONSTRAINT IF EXISTS employees_employment_type_check;

-- Add new constraint with 5 types
ALTER TABLE employees
ADD CONSTRAINT employees_employment_type_check
CHECK (employment_type IN ('full_time', 'part_time', 'seasonal', 'contract', 'casual'));

-- ============================================================================
-- 2. Add compensation_type column to pay_groups
-- ============================================================================

ALTER TABLE pay_groups
ADD COLUMN IF NOT EXISTS compensation_type TEXT NOT NULL DEFAULT 'salary'
CHECK (compensation_type IN ('salary', 'hourly'));

-- Create index for the new column (useful for filtering)
CREATE INDEX IF NOT EXISTS idx_pay_groups_compensation_type ON pay_groups(compensation_type);

-- ============================================================================
-- 3. Update the pay_groups_with_counts view to include new field
-- ============================================================================

DROP VIEW IF EXISTS pay_groups_with_counts;

CREATE VIEW pay_groups_with_counts AS
SELECT
    pg.id,
    pg.company_id,
    pg.name,
    pg.description,
    pg.pay_frequency,
    pg.employment_type,
    pg.compensation_type,
    pg.next_period_end,
    pg.period_start_day,
    pg.leave_enabled,
    pg.tax_calculation_method,
    pg.overtime_policy,
    pg.wcb_config,
    pg.group_benefits,
    pg.earnings_config,
    pg.taxable_benefits_config,
    pg.deductions_config,
    pg.province,
    pg.created_at,
    pg.updated_at,
    COALESCE(employee_counts.count, 0) AS employee_count
FROM pay_groups pg
LEFT JOIN (
    SELECT pay_group_id, COUNT(*) AS count
    FROM employees
    WHERE termination_date IS NULL
    GROUP BY pay_group_id
) employee_counts ON pg.id = employee_counts.pay_group_id;

-- ============================================================================
-- 4. Update v_pay_group_summary view to include compensation_type
-- ============================================================================

DROP VIEW IF EXISTS public.v_pay_group_summary;

CREATE VIEW public.v_pay_group_summary WITH (security_invoker = on) AS
SELECT
    pg.id, pg.company_id, pg.name, pg.description,
    pg.pay_frequency, pg.employment_type, pg.compensation_type,
    pg.next_period_end, pg.period_start_day, pg.leave_enabled,
    pg.overtime_policy, pg.wcb_config, pg.group_benefits,
    pg.earnings_config, pg.taxable_benefits_config, pg.deductions_config,
    pg.province,
    pg.created_at, pg.updated_at,
    c.company_name,
    COUNT(e.id) AS employee_count
FROM pay_groups pg
JOIN companies c ON pg.company_id = c.id
LEFT JOIN employees e ON e.pay_group_id = pg.id AND e.termination_date IS NULL
GROUP BY pg.id, c.company_name;

COMMENT ON VIEW public.v_pay_group_summary IS
    'Pay group summary with employee count, province, and compensation_type. Uses security_invoker to enforce RLS.';

-- ============================================================================
-- 5. Comment for documentation
-- ============================================================================

COMMENT ON COLUMN pay_groups.compensation_type IS 'Compensation type for employees in this pay group: salary (annual) or hourly';
COMMENT ON COLUMN pay_groups.employment_type IS 'Employment type: full_time, part_time, seasonal, contract, or casual';
