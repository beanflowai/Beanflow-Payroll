-- Migration: Remove optional deductions from employees
-- Reason: RRSP and union dues should be managed by Pay Group Policy
-- Employee-level deductions add complexity without providing value

-- Step 1: Drop the dependent view first
DROP VIEW IF EXISTS public.v_employee_details;

-- Step 2: Recreate the view WITHOUT rrsp_per_period and union_dues_per_period
-- Note: ledger_id was already dropped in 20251231170907_drop_legacy_ledger_id.sql
CREATE VIEW public.v_employee_details WITH (security_invoker = on) AS
SELECT
  e.id,
  e.user_id,
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
  -- Removed: e.rrsp_per_period (being dropped)
  -- Removed: e.union_dues_per_period (being dropped)
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
  -- Initial YTD fields for transferred employees
  e.initial_ytd_cpp,
  e.initial_ytd_cpp2,
  e.initial_ytd_ei,
  e.initial_ytd_year,
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

-- Add comment explaining the security setting
COMMENT ON VIEW public.v_employee_details IS
  'Employee details view with company and pay group info. Uses security_invoker to enforce RLS of querying user.';

-- Step 3: Now safely drop the columns
ALTER TABLE employees DROP COLUMN IF EXISTS rrsp_per_period;
ALTER TABLE employees DROP COLUMN IF EXISTS union_dues_per_period;
