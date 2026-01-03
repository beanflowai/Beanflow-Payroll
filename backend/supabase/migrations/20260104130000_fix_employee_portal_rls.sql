-- Migration: Fix RLS policies for Employee Portal access
-- Purpose: Fix "permission denied for table users" error by using auth.jwt() instead of querying auth.users
-- Date: 2026-01-04

-- =============================================================================
-- Drop problematic policies that query auth.users directly
-- =============================================================================

DROP POLICY IF EXISTS "Employees can view own record via email" ON employees;
DROP POLICY IF EXISTS "Employees can update own record via email" ON employees;
DROP POLICY IF EXISTS "Employees can view own payroll records via email" ON payroll_records;
DROP POLICY IF EXISTS "Employees can view own t4 slips via email" ON t4_slips;
DROP POLICY IF EXISTS "Employees can view payroll runs via email" ON payroll_runs;

-- =============================================================================
-- Recreate policies using auth.jwt() instead of querying auth.users table
-- auth.jwt() ->> 'email' returns the email from the JWT token directly
-- =============================================================================

-- Employees can view their own record (matched by email from JWT)
CREATE POLICY "Employees can view own record via email" ON employees
    FOR SELECT USING (
        email = (auth.jwt() ->> 'email')
    );

-- Employees can update their own record (for personal info updates)
CREATE POLICY "Employees can update own record via email" ON employees
    FOR UPDATE USING (
        email = (auth.jwt() ->> 'email')
    );

-- Employees can view their own payroll records
CREATE POLICY "Employees can view own payroll records via email" ON payroll_records
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM employees
            WHERE employees.id = payroll_records.employee_id
            AND employees.email = (auth.jwt() ->> 'email')
        )
    );

-- Employees can view their own T4 slips
CREATE POLICY "Employees can view own t4 slips via email" ON t4_slips
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM employees
            WHERE employees.id = t4_slips.employee_id
            AND employees.email = (auth.jwt() ->> 'email')
        )
    );

-- Employees can view payroll runs (needed for joining with payroll_records)
CREATE POLICY "Employees can view payroll runs via email" ON payroll_runs
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM payroll_records pr
            JOIN employees e ON e.id = pr.employee_id
            WHERE pr.payroll_run_id = payroll_runs.id
            AND e.email = (auth.jwt() ->> 'email')
        )
    );
