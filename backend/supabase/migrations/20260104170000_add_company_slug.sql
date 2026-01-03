-- =============================================================================
-- ADD COMPANY SLUG FOR EMPLOYEE PORTAL
-- =============================================================================
-- Description: Adds URL-friendly slug to companies table for employee portal routing
-- Author: BeanFlow Payroll Team
-- Date: 2026-01-04
-- =============================================================================

-- Add slug column
ALTER TABLE companies ADD COLUMN IF NOT EXISTS slug TEXT;

-- Create unique index (only on non-null values)
CREATE UNIQUE INDEX IF NOT EXISTS idx_companies_slug ON companies(slug) WHERE slug IS NOT NULL;

-- Add comment
COMMENT ON COLUMN companies.slug IS 'URL-friendly identifier for employee portal (e.g., acme-corp)';

-- =============================================================================
-- AUTO-GENERATE SLUGS FOR EXISTING COMPANIES
-- =============================================================================

-- Function to generate a unique slug
CREATE OR REPLACE FUNCTION generate_company_slug(p_company_name TEXT, p_company_id UUID)
RETURNS TEXT AS $$
DECLARE
    v_base_slug TEXT;
    v_slug TEXT;
    v_counter INTEGER := 0;
BEGIN
    -- Generate base slug: lowercase, remove special chars, replace spaces with hyphens
    v_base_slug := LOWER(
        REGEXP_REPLACE(
            REGEXP_REPLACE(
                TRIM(p_company_name),
                '[^a-zA-Z0-9\s-]', '', 'g'  -- Remove special characters
            ),
            '\s+', '-', 'g'  -- Replace spaces with hyphens
        )
    );

    -- Remove leading/trailing hyphens and collapse multiple hyphens
    v_base_slug := REGEXP_REPLACE(v_base_slug, '-+', '-', 'g');
    v_base_slug := TRIM(BOTH '-' FROM v_base_slug);

    -- Handle empty slug (fallback to 'company')
    IF v_base_slug = '' OR v_base_slug IS NULL THEN
        v_base_slug := 'company';
    END IF;

    -- Try the base slug first
    v_slug := v_base_slug;

    -- Check for uniqueness, add suffix if needed
    WHILE EXISTS (
        SELECT 1 FROM companies
        WHERE slug = v_slug AND id != p_company_id
    ) LOOP
        v_counter := v_counter + 1;
        v_slug := v_base_slug || '-' || v_counter;
    END LOOP;

    RETURN v_slug;
END;
$$ LANGUAGE plpgsql;

-- Update existing companies with auto-generated slugs
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN SELECT id, company_name FROM companies WHERE slug IS NULL
    LOOP
        UPDATE companies
        SET slug = generate_company_slug(r.company_name, r.id)
        WHERE id = r.id;
    END LOOP;
END $$;

-- Make slug NOT NULL after populating existing records
ALTER TABLE companies ALTER COLUMN slug SET NOT NULL;

-- Add trigger to auto-generate slug on INSERT if not provided
CREATE OR REPLACE FUNCTION set_company_slug()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.slug IS NULL OR NEW.slug = '' THEN
        NEW.slug := generate_company_slug(NEW.company_name, COALESCE(NEW.id, gen_random_uuid()));
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_set_company_slug
    BEFORE INSERT ON companies
    FOR EACH ROW
    EXECUTE FUNCTION set_company_slug();

-- =============================================================================
-- RLS POLICY FOR EMPLOYEE PORTAL ACCESS
-- =============================================================================
-- Allow employees to read their company's slug (for portal routing)

CREATE POLICY "Employees can read own company slug"
    ON companies
    FOR SELECT
    USING (
        id IN (
            SELECT company_id FROM employees
            WHERE email = current_setting('request.jwt.claims', true)::json->>'email'
        )
    );
