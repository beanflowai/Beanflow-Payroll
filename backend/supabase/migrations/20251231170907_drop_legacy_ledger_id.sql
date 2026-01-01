-- Drop legacy ledger_id columns
-- These columns are no longer used - replaced by company_id foreign keys
-- Migration: 20251228110000_simplify_ledger_to_company.sql already:
--   1. Added company_id columns to payroll tables
--   2. Migrated data from ledger_id to company_id
--   3. Made ledger_id nullable
--   4. Updated RLS policies to use user_id instead of ledger_id

-- Step 1: Drop view that depends on ledger_id
DROP VIEW IF EXISTS public.v_employee_details;

-- Step 2: Drop ledger_id columns from tables
ALTER TABLE employees DROP COLUMN IF EXISTS ledger_id;
ALTER TABLE payroll_runs DROP COLUMN IF EXISTS ledger_id;
ALTER TABLE payroll_records DROP COLUMN IF EXISTS ledger_id;

-- Step 3: Recreate the view without ledger_id
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

COMMENT ON VIEW public.v_employee_details IS
  'Employee details view with company and pay group info. Uses security_invoker to enforce RLS of querying user.';

-- Note: companies.bookkeeping_ledger_id is intentionally KEPT
-- It stores the external bookkeeping system's ledger ID for integration
