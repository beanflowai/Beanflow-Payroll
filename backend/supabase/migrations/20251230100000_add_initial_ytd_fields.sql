-- =============================================================================
-- ADD INITIAL YTD FIELDS FOR TRANSFERRED EMPLOYEES
-- =============================================================================
-- Description: Adds initial YTD CPP/EI fields for employees who transferred
--              mid-year from another employer. This prevents over-deduction
--              of CPP/EI contributions that have annual maximums.
--
-- Note: Income tax does NOT need initial values because:
--       - Cumulative Averaging handles mid-year transfers automatically
--       - Year-end T4 will reconcile any differences
--
-- Author: BeanFlow Payroll Team
-- Date: 2025-12-30
-- =============================================================================

-- Add initial YTD fields to employees table
ALTER TABLE employees
  ADD COLUMN IF NOT EXISTS initial_ytd_cpp NUMERIC(10, 2) DEFAULT 0,
  ADD COLUMN IF NOT EXISTS initial_ytd_cpp2 NUMERIC(10, 2) DEFAULT 0,
  ADD COLUMN IF NOT EXISTS initial_ytd_ei NUMERIC(10, 2) DEFAULT 0,
  ADD COLUMN IF NOT EXISTS initial_ytd_year INTEGER DEFAULT NULL;

-- Add check constraint to ensure non-negative values
ALTER TABLE employees
  ADD CONSTRAINT chk_initial_ytd_cpp_non_negative CHECK (initial_ytd_cpp >= 0),
  ADD CONSTRAINT chk_initial_ytd_cpp2_non_negative CHECK (initial_ytd_cpp2 >= 0),
  ADD CONSTRAINT chk_initial_ytd_ei_non_negative CHECK (initial_ytd_ei >= 0);

-- Add comments explaining the purpose of each field
COMMENT ON COLUMN employees.initial_ytd_cpp IS
  'Prior CPP contributions from previous employer this year (for transferred employees). Used to prevent exceeding annual maximum.';

COMMENT ON COLUMN employees.initial_ytd_cpp2 IS
  'Prior CPP2 (enhanced) contributions from previous employer this year. Only applies to income above YMPE threshold (~$71,300).';

COMMENT ON COLUMN employees.initial_ytd_ei IS
  'Prior EI premiums from previous employer this year (for transferred employees). Used to prevent exceeding annual maximum.';

COMMENT ON COLUMN employees.initial_ytd_year IS
  'Tax year for which initial YTD values apply. Values are only used when this matches the current tax year.';
