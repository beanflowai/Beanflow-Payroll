-- =============================================================================
-- DROP UNIQUE CONSTRAINT ON COMPANIES TABLE
-- =============================================================================
-- Description: Remove the unique_company_per_user constraint to allow
--              multiple companies with the same business number per user.
--              This aligns with the frontend which doesn't enforce BN validation.
-- =============================================================================

-- Drop the unique constraint
ALTER TABLE companies DROP CONSTRAINT IF EXISTS unique_company_per_user;
