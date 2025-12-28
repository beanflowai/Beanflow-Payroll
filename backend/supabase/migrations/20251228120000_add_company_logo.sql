-- =============================================================================
-- ADD COMPANY LOGO URL
-- =============================================================================
-- Description: Adds logo_url column to companies table for paystub branding
-- Author: BeanFlow Payroll Team
-- Date: 2025-12-28
-- =============================================================================

-- Add logo_url column to companies table
-- Stores the URL to company logo image (stored in Supabase Storage)
ALTER TABLE companies
    ADD COLUMN IF NOT EXISTS logo_url TEXT;

-- Add comment for documentation
COMMENT ON COLUMN companies.logo_url IS 'URL to company logo image stored in Supabase Storage, used for paystub branding';
