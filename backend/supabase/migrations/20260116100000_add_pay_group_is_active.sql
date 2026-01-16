-- ============================================================================
-- Migration: Add is_active field to pay_groups for soft delete functionality
-- ============================================================================
-- Pay groups with associated data (employees or payroll runs) can only be
-- deactivated (soft delete), while pay groups without associated data can
-- be permanently deleted (hard delete).
-- ============================================================================

-- 1. Add is_active column with default TRUE
-- ============================================================================
ALTER TABLE pay_groups
ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;

COMMENT ON COLUMN pay_groups.is_active IS
    'Soft delete flag. TRUE = active (default), FALSE = inactive (soft deleted). '
    'Inactive pay groups do not appear in payroll run selections or employee dropdowns.';

-- 2. Add index for efficient filtering by is_active status
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_pay_groups_is_active
ON pay_groups(company_id, is_active);

-- 3. Update v_pay_group_summary view to include is_active
-- ============================================================================
DROP VIEW IF EXISTS public.v_pay_group_summary;

CREATE VIEW public.v_pay_group_summary WITH (security_invoker = on) AS
SELECT
    pg.id, pg.company_id, pg.name, pg.description,
    pg.pay_frequency, pg.employment_type, pg.compensation_type,
    pg.next_period_end, pg.period_start_day, pg.leave_enabled,
    pg.tax_calculation_method,
    pg.overtime_policy, pg.wcb_config, pg.group_benefits,
    pg.earnings_config, pg.taxable_benefits_config, pg.deductions_config,
    pg.province,
    pg.is_active,
    pg.created_at, pg.updated_at,
    c.company_name,
    COUNT(e.id) AS employee_count
FROM pay_groups pg
JOIN companies c ON pg.company_id = c.id
LEFT JOIN employees e ON e.pay_group_id = pg.id AND e.termination_date IS NULL
GROUP BY pg.id, c.company_name;

COMMENT ON VIEW public.v_pay_group_summary IS
    'Pay group summary with employee count, is_active status, province, and compensation_type. Uses security_invoker to enforce RLS.';
