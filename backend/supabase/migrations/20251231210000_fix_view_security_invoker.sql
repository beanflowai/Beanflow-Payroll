-- Migration: Fix v_employee_details view security
-- Issue: View was defined without security_invoker, defaulting to SECURITY DEFINER
-- Fix: Recreate view with security_invoker = on to enforce RLS of querying user

-- Drop and recreate v_employee_details with security_invoker
DROP VIEW IF EXISTS public.v_employee_details;

CREATE VIEW public.v_employee_details WITH (security_invoker = on) AS
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

-- Add comment explaining the security setting
COMMENT ON VIEW public.v_employee_details IS
  'Employee details view with company and pay group info. Uses security_invoker to enforce RLS of querying user.';
