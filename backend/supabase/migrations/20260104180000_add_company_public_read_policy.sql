-- =============================================================================
-- ADD PUBLIC READ POLICY FOR COMPANY SLUG (EMPLOYEE PORTAL LOGIN)
-- =============================================================================
-- Description: Creates a secure view exposing only necessary company fields
--              for the employee portal login page to display company name/logo.
--              This prevents exposing sensitive company data to public users.
-- Author: BeanFlow Payroll Team
-- Date: 2026-01-04
-- =============================================================================

-- Create a view that only exposes safe public fields
-- This is more secure than a blanket RLS policy on the full companies table
CREATE OR REPLACE VIEW public_company_portal_info AS
SELECT
    id,
    company_name,
    slug,
    logo_url
FROM companies
WHERE slug IS NOT NULL;

-- Grant public access to this view only
GRANT SELECT ON public_company_portal_info TO anon;
GRANT SELECT ON public_company_portal_info TO authenticated;

-- Add comment explaining the view's purpose
COMMENT ON VIEW public_company_portal_info IS
    'Public-facing view for employee portal login. Only exposes id, company_name, slug, logo_url.';
