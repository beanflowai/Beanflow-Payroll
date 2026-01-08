-- =============================================================================
-- MIGRATION: Add province field to pay_groups
-- =============================================================================
-- Description: Adds province field to pay_groups table to enable:
--   - Province-specific holiday display per pay group
--   - Employee assignment validation (same province only)
--   - Default value inherited from company's province
-- =============================================================================

-- Add province column to pay_groups with default from company
ALTER TABLE pay_groups
ADD COLUMN province TEXT;

-- Update existing pay_groups with their company's province (default to ON if null)
UPDATE pay_groups pg
SET province = COALESCE(c.province, 'ON')
FROM companies c
WHERE pg.company_id = c.id;

-- Now add NOT NULL constraint and CHECK constraint
ALTER TABLE pay_groups
ALTER COLUMN province SET NOT NULL;

ALTER TABLE pay_groups
ADD CONSTRAINT pay_groups_province_check CHECK (
    province IN ('AB', 'BC', 'MB', 'NB', 'NL', 'NS', 'NT', 'NU', 'ON', 'PE', 'SK', 'YT')
);

-- Add index for province queries
CREATE INDEX IF NOT EXISTS idx_pay_groups_province ON pay_groups(province);

-- =============================================================================
-- Update v_pay_group_summary view to include province
-- =============================================================================
DROP VIEW IF EXISTS public.v_pay_group_summary;

CREATE VIEW public.v_pay_group_summary WITH (security_invoker = on) AS
SELECT
    pg.id, pg.company_id, pg.name, pg.description,
    pg.pay_frequency, pg.employment_type, pg.next_period_end,
    pg.period_start_day, pg.leave_enabled,
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
    'Pay group summary with employee count and province. Uses security_invoker to enforce RLS.';

-- =============================================================================
-- Add trigger to default province from company on INSERT
-- =============================================================================
CREATE OR REPLACE FUNCTION set_pay_group_province_default()
RETURNS TRIGGER AS $$
BEGIN
    -- If province is not provided, default to company's province
    IF NEW.province IS NULL THEN
        SELECT province INTO NEW.province
        FROM companies
        WHERE id = NEW.company_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_set_pay_group_province
    BEFORE INSERT ON pay_groups FOR EACH ROW
    EXECUTE FUNCTION set_pay_group_province_default();
