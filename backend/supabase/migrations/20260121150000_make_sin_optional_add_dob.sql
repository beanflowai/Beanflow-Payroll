-- =============================================================================
-- MIGRATION: Make SIN optional and add date_of_birth column
-- =============================================================================
-- Description:
--   1. Make sin_encrypted column nullable (allow employees without SIN)
--   2. Remove unique constraint on SIN (allow duplicate SINs)
--   3. Add date_of_birth column for CPP calculations
-- =============================================================================

-- Make SIN nullable (allow employees without SIN)
ALTER TABLE employees ALTER COLUMN sin_encrypted DROP NOT NULL;

-- Remove unique constraint on SIN (allow multiple employees to have same/no SIN)
ALTER TABLE employees DROP CONSTRAINT IF EXISTS unique_employee_sin;

-- Add date_of_birth column for CPP calculations
ALTER TABLE employees ADD COLUMN date_of_birth DATE;
