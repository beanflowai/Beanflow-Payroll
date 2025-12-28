-- =============================================================================
-- MIGRATION: Simplify Multi-Tenancy from ledger_id to company_id
-- =============================================================================
-- Description: Migrate payroll system from user_id + ledger_id to user_id + company_id
-- Before: user_id + ledger_id + company_id
-- After:  user_id + company_id
-- =============================================================================

-- Step 1: Give companies table a ledger_id for backward compatibility and Bookkeeping integration
ALTER TABLE companies
ADD COLUMN IF NOT EXISTS ledger_id TEXT;

-- Set ledger_id = id::text (use company ID as ledger identifier)
UPDATE companies SET ledger_id = id::text WHERE ledger_id IS NULL;

-- Step 2: Add company_id to payroll_runs
ALTER TABLE payroll_runs
ADD COLUMN IF NOT EXISTS company_id UUID REFERENCES companies(id);

-- Step 3: Add company_id to payroll_records
ALTER TABLE payroll_records
ADD COLUMN IF NOT EXISTS company_id UUID REFERENCES companies(id);

-- Step 4: Migrate data - Get company_id from employees for payroll_records
UPDATE payroll_records pr
SET company_id = (
  SELECT e.company_id
  FROM employees e
  WHERE e.id = pr.employee_id
)
WHERE pr.company_id IS NULL;

-- Step 4b: Fallback - If employee doesn't exist, get company_id from user's first company
UPDATE payroll_records pr
SET company_id = (
  SELECT c.id
  FROM companies c
  WHERE c.user_id = pr.user_id
  ORDER BY c.created_at ASC
  LIMIT 1
)
WHERE pr.company_id IS NULL;

-- Step 5: Migrate payroll_runs company_id from payroll_records
UPDATE payroll_runs pr
SET company_id = (
  SELECT DISTINCT rec.company_id
  FROM payroll_records rec
  WHERE rec.payroll_run_id = pr.id
  LIMIT 1
)
WHERE pr.company_id IS NULL;

-- Step 5b: Fallback - If no records exist, get company_id from user's first company
UPDATE payroll_runs pr
SET company_id = (
  SELECT c.id
  FROM companies c
  WHERE c.user_id = pr.user_id
  ORDER BY c.created_at ASC
  LIMIT 1
)
WHERE pr.company_id IS NULL;

-- Step 6: Verify no NULL company_id values remain (raise warning if any exist)
DO $$
DECLARE
  null_records_count INTEGER;
  null_runs_count INTEGER;
BEGIN
  SELECT COUNT(*) INTO null_records_count FROM payroll_records WHERE company_id IS NULL;
  SELECT COUNT(*) INTO null_runs_count FROM payroll_runs WHERE company_id IS NULL;

  IF null_records_count > 0 THEN
    RAISE WARNING 'Migration warning: % payroll_records still have NULL company_id', null_records_count;
  END IF;

  IF null_runs_count > 0 THEN
    RAISE WARNING 'Migration warning: % payroll_runs still have NULL company_id', null_runs_count;
  END IF;
END $$;

-- Step 7: Remove NOT NULL constraint on ledger_id (no longer required)
ALTER TABLE payroll_runs ALTER COLUMN ledger_id DROP NOT NULL;
ALTER TABLE payroll_records ALTER COLUMN ledger_id DROP NOT NULL;

-- Step 8: Create indexes for company_id
CREATE INDEX IF NOT EXISTS idx_payroll_runs_company_id ON payroll_runs(company_id);
CREATE INDEX IF NOT EXISTS idx_payroll_records_company_id ON payroll_records(company_id);
CREATE INDEX IF NOT EXISTS idx_companies_ledger_id ON companies(ledger_id);

-- =============================================================================
-- Step 9: Update RLS Policies - Simplify to user_id only
-- =============================================================================

-- payroll_runs policies
DROP POLICY IF EXISTS "Users can access own payroll runs" ON payroll_runs;
DROP POLICY IF EXISTS "Users can view own payroll_runs" ON payroll_runs;
DROP POLICY IF EXISTS "Users can insert own payroll_runs" ON payroll_runs;
DROP POLICY IF EXISTS "Users can update own payroll_runs" ON payroll_runs;
DROP POLICY IF EXISTS "Users can delete own payroll_runs" ON payroll_runs;

CREATE POLICY "Users can view own payroll_runs"
    ON payroll_runs FOR SELECT
    USING (user_id = auth.uid()::text);

CREATE POLICY "Users can insert own payroll_runs"
    ON payroll_runs FOR INSERT
    WITH CHECK (user_id = auth.uid()::text);

CREATE POLICY "Users can update own payroll_runs"
    ON payroll_runs FOR UPDATE
    USING (user_id = auth.uid()::text);

CREATE POLICY "Users can delete own payroll_runs"
    ON payroll_runs FOR DELETE
    USING (user_id = auth.uid()::text);

-- payroll_records policies
DROP POLICY IF EXISTS "Users can access own payroll records" ON payroll_records;
DROP POLICY IF EXISTS "Users can view own payroll_records" ON payroll_records;
DROP POLICY IF EXISTS "Users can insert own payroll_records" ON payroll_records;
DROP POLICY IF EXISTS "Users can update own payroll_records" ON payroll_records;
DROP POLICY IF EXISTS "Users can delete own payroll_records" ON payroll_records;

CREATE POLICY "Users can view own payroll_records"
    ON payroll_records FOR SELECT
    USING (user_id = auth.uid()::text);

CREATE POLICY "Users can insert own payroll_records"
    ON payroll_records FOR INSERT
    WITH CHECK (user_id = auth.uid()::text);

CREATE POLICY "Users can update own payroll_records"
    ON payroll_records FOR UPDATE
    USING (user_id = auth.uid()::text);

CREATE POLICY "Users can delete own payroll_records"
    ON payroll_records FOR DELETE
    USING (user_id = auth.uid()::text);

-- employees policies
DROP POLICY IF EXISTS "Users can access own employees" ON employees;
DROP POLICY IF EXISTS "Users can view own employees" ON employees;
DROP POLICY IF EXISTS "Users can insert own employees" ON employees;
DROP POLICY IF EXISTS "Users can update own employees" ON employees;
DROP POLICY IF EXISTS "Users can delete own employees" ON employees;

CREATE POLICY "Users can view own employees"
    ON employees FOR SELECT
    USING (user_id = auth.uid()::text);

CREATE POLICY "Users can insert own employees"
    ON employees FOR INSERT
    WITH CHECK (user_id = auth.uid()::text);

CREATE POLICY "Users can update own employees"
    ON employees FOR UPDATE
    USING (user_id = auth.uid()::text);

CREATE POLICY "Users can delete own employees"
    ON employees FOR DELETE
    USING (user_id = auth.uid()::text);

-- companies policies (also update to use auth.uid())
DROP POLICY IF EXISTS "Users can access own companies" ON companies;
DROP POLICY IF EXISTS "Users can view own companies" ON companies;
DROP POLICY IF EXISTS "Users can insert own companies" ON companies;
DROP POLICY IF EXISTS "Users can update own companies" ON companies;
DROP POLICY IF EXISTS "Users can delete own companies" ON companies;

CREATE POLICY "Users can view own companies"
    ON companies FOR SELECT
    USING (user_id = auth.uid()::text);

CREATE POLICY "Users can insert own companies"
    ON companies FOR INSERT
    WITH CHECK (user_id = auth.uid()::text);

CREATE POLICY "Users can update own companies"
    ON companies FOR UPDATE
    USING (user_id = auth.uid()::text);

CREATE POLICY "Users can delete own companies"
    ON companies FOR DELETE
    USING (user_id = auth.uid()::text);

-- =============================================================================
-- Note: Not dropping ledger_id columns for rollback safety
-- Can be removed in a future migration after verification
-- =============================================================================
