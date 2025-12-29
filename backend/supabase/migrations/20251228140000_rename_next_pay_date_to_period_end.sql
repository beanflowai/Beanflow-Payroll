-- Migration: Rename next_pay_date to next_period_end
-- Purpose: Change Pay Group from storing next pay date to storing next period end date
--          Pay date will be auto-calculated as period_end + 6 days (Saskatchewan requirement)
--
-- Changes:
--   - Rename pay_groups.next_pay_date to next_period_end
--   - Convert existing data: next_period_end = next_pay_date - 6 days
--   - Update v_employee_details view
--   - Update v_pay_group_summary view
--
-- Background:
--   Saskatchewan law requires paying employees within 6 days of pay period end.
--   By storing period_end instead of pay_date, we can enforce this constraint automatically.

-- Step 1: Drop dependent views
DROP VIEW IF EXISTS public.v_employee_details;
DROP VIEW IF EXISTS public.v_pay_group_summary;

-- Step 2: Rename column
ALTER TABLE pay_groups RENAME COLUMN next_pay_date TO next_period_end;

-- Step 3: Convert existing data (subtract 6 days to get period end from old pay date)
UPDATE pay_groups SET next_period_end = next_period_end - INTERVAL '6 days';

-- Step 4: Add comment explaining the new column
COMMENT ON COLUMN pay_groups.next_period_end IS
  'Next pay period end date. Pay date is auto-calculated as period_end + 6 days (Saskatchewan law)';

-- Step 5: Recreate v_employee_details view with renamed column
CREATE VIEW public.v_employee_details AS
SELECT
  e.id,
  e.user_id,
  e.ledger_id,
  e.first_name,
  e.last_name,
  e.sin_encrypted,
  e.email,
  e.province_of_employment,
  e.pay_frequency,
  e.employment_type,
  e.annual_salary,
  e.hourly_rate,
  e.federal_additional_claims,
  e.provincial_additional_claims,
  e.is_cpp_exempt,
  e.is_ei_exempt,
  e.cpp2_exempt,
  e.rrsp_per_period,
  e.union_dues_per_period,
  e.hire_date,
  e.termination_date,
  e.vacation_config,
  e.vacation_balance,
  e.created_at,
  e.updated_at,
  e.company_id,
  e.pay_group_id,
  e.address_street,
  e.address_city,
  e.address_postal_code,
  e.occupation,
  -- Joined fields
  c.company_name,
  c.province AS company_province,
  c.address_street AS company_address_street,
  c.address_city AS company_address_city,
  c.address_postal_code AS company_address_postal_code,
  pg.name AS pay_group_name,
  pg.next_period_end AS pay_group_next_period_end
FROM
  employees e
  LEFT JOIN companies c ON e.company_id = c.id
  LEFT JOIN pay_groups pg ON e.pay_group_id = pg.id;

-- Step 6: Recreate v_pay_group_summary view with renamed column
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
FROM
    pay_groups pg
    JOIN companies c ON pg.company_id = c.id
    LEFT JOIN employees e ON e.pay_group_id = pg.id AND e.termination_date IS NULL
GROUP BY
    pg.id,
    c.company_name;
