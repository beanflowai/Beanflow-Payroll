-- Add tax_calculation_method column to pay_groups
-- Supports CRA T4127 Option 1 (Annualization) and Option 2 (Cumulative Averaging)

ALTER TABLE pay_groups
    ADD COLUMN IF NOT EXISTS tax_calculation_method TEXT NOT NULL DEFAULT 'annualization'
    CHECK (tax_calculation_method IN ('annualization', 'cumulative_averaging'));

COMMENT ON COLUMN pay_groups.tax_calculation_method IS
    'CRA T4127 tax calculation method: annualization (Option 1) or cumulative_averaging (Option 2)';

-- Update the view to include tax_calculation_method
DROP VIEW IF EXISTS public.v_pay_group_summary;

CREATE VIEW public.v_pay_group_summary WITH (security_invoker = on) AS
SELECT
    pg.id,
    pg.company_id,
    pg.name,
    pg.description,
    pg.pay_frequency,
    pg.employment_type,
    pg.next_pay_date,
    pg.period_start_day,
    pg.leave_enabled,
    pg.tax_calculation_method,
    pg.statutory_defaults,
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
FROM pay_groups pg
JOIN companies c ON pg.company_id = c.id
LEFT JOIN employees e ON e.pay_group_id = pg.id AND e.termination_date IS NULL
GROUP BY pg.id, c.company_name;
