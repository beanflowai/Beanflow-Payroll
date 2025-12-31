-- Migration: Add unique constraint for active compensation record
-- Purpose: Ensure each employee has at most one active (end_date = NULL) compensation record
-- This prevents data corruption from concurrent updates

-- 1. Add partial unique index to prevent multiple active records per employee
-- PostgreSQL partial unique index: only enforces uniqueness where condition is true
CREATE UNIQUE INDEX IF NOT EXISTS idx_compensation_active_per_employee
ON employee_compensation_history(employee_id)
WHERE end_date IS NULL;

-- Note: This constraint will fail if there are already multiple active records
-- for the same employee. If migration fails, clean up duplicate records first:
--
-- SELECT employee_id, COUNT(*)
-- FROM employee_compensation_history
-- WHERE end_date IS NULL
-- GROUP BY employee_id
-- HAVING COUNT(*) > 1;
