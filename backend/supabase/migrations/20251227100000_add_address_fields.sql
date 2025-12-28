-- =============================================================================
-- ADD ADDRESS FIELDS TO EMPLOYEES AND COMPANIES
-- =============================================================================
-- Description: Adds address fields for paystub generation
-- Author: BeanFlow Payroll Team
-- Date: 2025-12-27
-- =============================================================================

-- =============================================================================
-- EMPLOYEES TABLE - Add address fields
-- =============================================================================

-- Street address (can include unit/suite number)
ALTER TABLE employees ADD COLUMN IF NOT EXISTS address_street TEXT;

-- City
ALTER TABLE employees ADD COLUMN IF NOT EXISTS address_city TEXT;

-- Postal code (format: A1A 1A1)
ALTER TABLE employees ADD COLUMN IF NOT EXISTS address_postal_code TEXT;

-- Occupation/Job title (for paystub display)
ALTER TABLE employees ADD COLUMN IF NOT EXISTS occupation TEXT;

-- Note: province_of_employment already exists and can be used as province for address


-- =============================================================================
-- COMPANIES TABLE - Add address fields
-- =============================================================================

-- Street address (can include unit/suite number)
ALTER TABLE companies ADD COLUMN IF NOT EXISTS address_street TEXT;

-- City
ALTER TABLE companies ADD COLUMN IF NOT EXISTS address_city TEXT;

-- Postal code (format: A1A 1A1)
ALTER TABLE companies ADD COLUMN IF NOT EXISTS address_postal_code TEXT;

-- Note: province already exists and can be used for address


-- =============================================================================
-- UPDATE VIEW - v_employee_details to include new fields
-- =============================================================================

DROP VIEW IF EXISTS public.v_employee_details;

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
  e.federal_claim_amount,
  e.provincial_claim_amount,
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
  -- New address fields
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


-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON COLUMN employees.address_street IS 'Employee street address including unit/suite number';
COMMENT ON COLUMN employees.address_city IS 'Employee city';
COMMENT ON COLUMN employees.address_postal_code IS 'Employee postal code (format: A1A 1A1)';
COMMENT ON COLUMN employees.occupation IS 'Employee job title/occupation for paystub display';

COMMENT ON COLUMN companies.address_street IS 'Company street address including unit/suite number';
COMMENT ON COLUMN companies.address_city IS 'Company city';
COMMENT ON COLUMN companies.address_postal_code IS 'Company postal code (format: A1A 1A1)';
