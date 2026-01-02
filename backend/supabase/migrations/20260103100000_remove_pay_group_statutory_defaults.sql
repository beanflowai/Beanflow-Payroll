-- Migration: Remove statutory_defaults from pay_groups
-- Reason: Statutory defaults are never used by payroll engine (only employee-level exemptions are used)
-- This eliminates confusion and reduces complexity

-- Step 1: Drop the dependent view first
DROP VIEW IF EXISTS public.v_pay_group_summary;

-- Step 2: Recreate the view WITHOUT statutory_defaults
CREATE VIEW public.v_pay_group_summary WITH (security_invoker = on) AS
SELECT
    pg.id,
    pg.company_id,
    pg.name,
    pg.description,
    pg.pay_frequency,
    pg.employment_type,
    pg.next_period_end,
    pg.period_start_day,
    pg.leave_enabled,
    -- Removed: pg.statutory_defaults (being dropped)
    pg.overtime_policy,
    pg.wcb_config,
    pg.group_benefits,
    pg.earnings_config,
    pg.taxable_benefits_config,
    pg.deductions_config,
    pg.created_at,
    pg.updated_at,
    c.company_name,
    COUNT(e.id) AS employee_count
FROM
    pay_groups pg
    JOIN companies c ON pg.company_id = c.id
    LEFT JOIN employees e ON e.pay_group_id = pg.id AND e.termination_date IS NULL
GROUP BY
    pg.id,
    c.company_name;

-- Step 3: Now safely drop the column
ALTER TABLE pay_groups DROP COLUMN IF EXISTS statutory_defaults;
