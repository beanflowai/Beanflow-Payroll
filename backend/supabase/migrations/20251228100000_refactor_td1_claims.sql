-- Migration: Refactor TD1 Claims Data Model
-- Purpose: Store Additional Claims separately from BPA
--          BPA will be dynamically fetched from tax tables based on pay_date
--
-- Changes:
--   - Add federal_additional_claims and provincial_additional_claims columns
--   - Remove federal_claim_amount and provincial_claim_amount columns
--   - Update v_employee_details view
--
-- Background:
--   Previously stored Total Claim Amount (BPA + Additional Claims mixed together)
--   This caused incorrect tax calculations when BPA varies by tax year edition
--   (e.g., SK 2025 has BPA $18,991 in Jan edition vs $19,991 in Jul edition)

-- Step 1: Drop dependent view first
DROP VIEW IF EXISTS public.v_employee_details;

-- Step 2: Add new columns for additional claims
ALTER TABLE employees
  ADD COLUMN federal_additional_claims NUMERIC(12, 2) NOT NULL DEFAULT 0,
  ADD COLUMN provincial_additional_claims NUMERIC(12, 2) NOT NULL DEFAULT 0;

-- Step 3: Add comments
COMMENT ON COLUMN employees.federal_additional_claims IS 'TD1 Federal: Additional personal amounts beyond BPA';
COMMENT ON COLUMN employees.provincial_additional_claims IS 'TD1 Provincial: Additional personal amounts beyond BPA';

-- Step 4: Drop old columns (development stage - no backward compatibility needed)
ALTER TABLE employees
  DROP COLUMN federal_claim_amount,
  DROP COLUMN provincial_claim_amount;

-- Step 5: Recreate view with new columns
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
  pg.next_pay_date AS pay_group_next_pay_date
FROM
  employees e
  LEFT JOIN companies c ON e.company_id = c.id
  LEFT JOIN pay_groups pg ON e.pay_group_id = pg.id;
