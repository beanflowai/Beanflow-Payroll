-- =============================================================================
-- SICK LEAVE TRACKING & EMPLOYEE TAGS - DATABASE SCHEMA UPDATE
-- =============================================================================
-- Description: Adds sick leave tracking fields to payroll_records and employees,
--              plus tags array for employee categorization
-- Author: BeanFlow Payroll Team
-- Date: 2025-12-17
-- =============================================================================

-- =============================================================================
-- PAYROLL_RECORDS TABLE - ADD SICK LEAVE FIELDS
-- =============================================================================

-- Add sick hours taken field
ALTER TABLE payroll_records
    ADD COLUMN IF NOT EXISTS sick_hours_taken NUMERIC(6, 2) DEFAULT 0;

-- Add sick pay paid field
ALTER TABLE payroll_records
    ADD COLUMN IF NOT EXISTS sick_pay_paid NUMERIC(10, 2) DEFAULT 0;

-- Add paystub sent tracking fields
ALTER TABLE payroll_records
    ADD COLUMN IF NOT EXISTS paystub_sent_to TEXT;

ALTER TABLE payroll_records
    ADD COLUMN IF NOT EXISTS paystub_sent_at TIMESTAMPTZ;

-- =============================================================================
-- EMPLOYEES TABLE - ADD SICK BALANCE AND TAGS
-- =============================================================================

-- Add sick leave balance field
ALTER TABLE employees
    ADD COLUMN IF NOT EXISTS sick_balance NUMERIC(12, 2) DEFAULT 0;

-- Add tags array for employee categorization
ALTER TABLE employees
    ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT '{}';

-- Create index for tags (GIN index for array operations)
CREATE INDEX IF NOT EXISTS idx_employees_tags ON employees USING GIN(tags);

-- =============================================================================
-- UPDATE VIEW: v_employee_details to include new fields
-- =============================================================================

-- Drop and recreate the view to include new fields
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
    e.sick_balance,
    e.tags,
    e.created_at,
    e.updated_at,
    e.company_id,
    e.pay_group_id,
    c.company_name,
    c.province AS company_province,
    pg.name AS pay_group_name,
    pg.next_pay_date AS pay_group_next_pay_date
FROM
    employees e
    LEFT JOIN companies c ON e.company_id = c.id
    LEFT JOIN pay_groups pg ON e.pay_group_id = pg.id;
