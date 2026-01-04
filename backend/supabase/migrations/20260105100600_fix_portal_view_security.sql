-- =============================================================================
-- MIGRATION 007: FIX PORTAL VIEW SECURITY
-- =============================================================================
-- Description: Fix public_company_portal_info view to use SECURITY INVOKER
--              and add RLS policy for anonymous access
-- =============================================================================

-- Drop and recreate view with security_invoker = true
DROP VIEW IF EXISTS public_company_portal_info;

CREATE VIEW public_company_portal_info
WITH (security_invoker = true) AS
SELECT id, company_name, slug, logo_url
FROM companies
WHERE slug IS NOT NULL;

-- Re-grant permissions
GRANT SELECT ON public_company_portal_info TO anon;
GRANT SELECT ON public_company_portal_info TO authenticated;

COMMENT ON VIEW public_company_portal_info IS
    'Public-facing view for employee portal login. Uses SECURITY INVOKER with explicit RLS policy.';

-- Add RLS policy to allow anonymous users to read companies with slugs (for portal lookup)
CREATE POLICY "Anonymous can view companies with slug for portal" ON companies
    FOR SELECT TO anon
    USING (slug IS NOT NULL);
