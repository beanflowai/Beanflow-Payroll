-- =============================================================================
-- FIX EMPLOYEE TAX CLAIMS RLS POLICY
-- =============================================================================
-- Description: Fix incomplete RLS policy that blocks INSERT operations
-- =============================================================================

-- Drop existing incomplete policy
DROP POLICY IF EXISTS "Users can view own tax_claims" ON employee_tax_claims;
DROP POLICY IF EXISTS "Users can insert own tax_claims" ON employee_tax_claims;
DROP POLICY IF EXISTS "Users can update own tax_claims" ON employee_tax_claims;
DROP POLICY IF EXISTS "Users can delete own tax_claims" ON employee_tax_claims;

-- Create correct policies
-- Note: auth.uid() returns UUID type natively in Supabase, no cast needed
CREATE POLICY "Users can view own tax_claims" ON employee_tax_claims
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users can insert own tax_claims" ON employee_tax_claims
    FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update own tax_claims" ON employee_tax_claims
    FOR UPDATE USING (user_id = auth.uid());

CREATE POLICY "Users can delete own tax_claims" ON employee_tax_claims
    FOR DELETE USING (user_id = auth.uid());
