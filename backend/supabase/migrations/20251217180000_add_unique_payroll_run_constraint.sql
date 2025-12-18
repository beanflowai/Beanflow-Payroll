-- =============================================================================
-- ADD UNIQUE CONSTRAINT TO PAYROLL_RUNS
-- =============================================================================
-- Prevents duplicate payroll runs for the same pay date within a tenant.
-- This fixes the 406 error caused by .single() returning multiple rows.
-- =============================================================================

-- Add unique constraint to prevent duplicate payroll runs per pay date
ALTER TABLE payroll_runs
ADD CONSTRAINT unique_payroll_run_per_pay_date
UNIQUE (user_id, ledger_id, pay_date);
