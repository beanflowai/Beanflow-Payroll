-- =============================================================================
-- MIGRATION: Add standard_hours_per_week to employees
-- =============================================================================
-- Description: Add standard hours per week field for salaried employees
--   - Used for ROE (Record of Employment) insurable hours calculation
--   - Used for pay stub display (hours @ rate format)
--   - Default 40h for full-time employees
-- =============================================================================

-- Add standard_hours_per_week column to employees table
ALTER TABLE employees
ADD COLUMN standard_hours_per_week NUMERIC(5,2) DEFAULT 40.00;

-- Add constraint for valid hour range (1-60 hours)
ALTER TABLE employees
ADD CONSTRAINT chk_standard_hours_range
CHECK (standard_hours_per_week IS NULL OR (standard_hours_per_week >= 1 AND standard_hours_per_week <= 60));

-- Add comment explaining the field purpose
COMMENT ON COLUMN employees.standard_hours_per_week IS
    'Standard contractual hours per week. Used for ROE insurable hours calculation and pay stub display. Default 40h for full-time. Range: 1-60 hours.';

-- Update the v_employee_details view to include the new column
-- Must DROP first because PostgreSQL doesn't allow column reordering with CREATE OR REPLACE
DROP VIEW IF EXISTS public.v_employee_details;
CREATE VIEW public.v_employee_details WITH (security_invoker = on) AS
SELECT
    e.id, e.user_id, e.first_name, e.last_name, e.sin_encrypted, e.email,
    e.province_of_employment, e.pay_frequency, e.employment_type,
    e.annual_salary, e.hourly_rate,
    e.standard_hours_per_week,
    e.federal_additional_claims, e.provincial_additional_claims,
    e.is_cpp_exempt, e.is_ei_exempt, e.cpp2_exempt,
    e.hire_date, e.termination_date,
    e.date_of_birth,
    e.vacation_config, e.vacation_balance,
    e.sick_balance,
    e.tags,
    e.initial_ytd_cpp, e.initial_ytd_cpp2, e.initial_ytd_ei, e.initial_ytd_year,
    e.portal_status, e.portal_invited_at, e.portal_last_login_at,
    e.created_at, e.updated_at,
    e.company_id, e.pay_group_id,
    e.address_street, e.address_city, e.address_postal_code, e.occupation,
    c.company_name, c.province AS company_province,
    c.address_street AS company_address_street,
    c.address_city AS company_address_city,
    c.address_postal_code AS company_address_postal_code,
    pg.name AS pay_group_name,
    pg.next_period_end AS pay_group_next_period_end
FROM employees e
LEFT JOIN companies c ON e.company_id = c.id
LEFT JOIN pay_groups pg ON e.pay_group_id = pg.id;

COMMENT ON VIEW public.v_employee_details IS
    'Employee details view with company and pay group info. Uses security_invoker to enforce RLS.';
