-- Migration: Add RLS policies for Employee Portal access
-- Purpose: Allow employees to access their own data via email matching
-- Date: 2026-01-04

-- =============================================================================
-- Employees Table: Allow employees to view and update their own record
-- =============================================================================

-- Employees can view their own record (matched by email)
CREATE POLICY "Employees can view own record via email" ON employees
    FOR SELECT USING (
        email = (SELECT email FROM auth.users WHERE id = auth.uid())
    );

-- Employees can update their own record (for personal info updates)
CREATE POLICY "Employees can update own record via email" ON employees
    FOR UPDATE USING (
        email = (SELECT email FROM auth.users WHERE id = auth.uid())
    );

-- =============================================================================
-- Payroll Records Table: Allow employees to view their own paystubs
-- =============================================================================

-- Employees can view their own payroll records
CREATE POLICY "Employees can view own payroll records via email" ON payroll_records
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM employees
            WHERE employees.id = payroll_records.employee_id
            AND employees.email = (SELECT email FROM auth.users WHERE id = auth.uid())
        )
    );

-- =============================================================================
-- T4 Slips Table: Allow employees to view their own T4 documents
-- =============================================================================

-- Employees can view their own T4 slips
CREATE POLICY "Employees can view own t4 slips via email" ON t4_slips
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM employees
            WHERE employees.id = t4_slips.employee_id
            AND employees.email = (SELECT email FROM auth.users WHERE id = auth.uid())
        )
    );

-- =============================================================================
-- Payroll Runs Table: Allow employees to view runs associated with their records
-- =============================================================================

-- Employees can view payroll runs (needed for joining with payroll_records)
CREATE POLICY "Employees can view payroll runs via email" ON payroll_runs
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM payroll_records pr
            JOIN employees e ON e.id = pr.employee_id
            WHERE pr.payroll_run_id = payroll_runs.id
            AND e.email = (SELECT email FROM auth.users WHERE id = auth.uid())
        )
    );

-- =============================================================================
-- Documentation
-- =============================================================================

COMMENT ON POLICY "Employees can view own record via email" ON employees IS
    'Employee Portal: Allows authenticated employees to view their own employee record by matching auth.users.email with employees.email';

COMMENT ON POLICY "Employees can update own record via email" ON employees IS
    'Employee Portal: Allows authenticated employees to update their own personal information';

COMMENT ON POLICY "Employees can view own payroll records via email" ON payroll_records IS
    'Employee Portal: Allows authenticated employees to view their own paystubs';

COMMENT ON POLICY "Employees can view own t4 slips via email" ON t4_slips IS
    'Employee Portal: Allows authenticated employees to view their own T4 tax documents';

COMMENT ON POLICY "Employees can view payroll runs via email" ON payroll_runs IS
    'Employee Portal: Allows authenticated employees to view payroll runs associated with their records (for paystub display)';
