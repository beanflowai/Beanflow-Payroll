-- =============================================================================
-- CREATE ASSETS STORAGE BUCKET
-- =============================================================================
-- Description: Creates public storage bucket for company assets (logos, etc.)
-- Author: BeanFlow Payroll Team
-- Date: 2025-12-28
-- =============================================================================

-- Create the assets bucket for storing company logos and other assets
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'assets',
    'assets',
    true,  -- Public bucket for logos
    2097152,  -- 2MB file size limit
    ARRAY['image/png', 'image/jpeg', 'image/gif', 'image/webp', 'image/svg+xml']
)
ON CONFLICT (id) DO NOTHING;

-- Allow authenticated users to upload to company-logos folder
CREATE POLICY "Authenticated users can upload company logos"
ON storage.objects
FOR INSERT
TO authenticated
WITH CHECK (
    bucket_id = 'assets'
    AND (storage.foldername(name))[1] = 'company-logos'
);

-- Allow authenticated users to update their uploads
CREATE POLICY "Authenticated users can update company logos"
ON storage.objects
FOR UPDATE
TO authenticated
USING (
    bucket_id = 'assets'
    AND (storage.foldername(name))[1] = 'company-logos'
);

-- Allow authenticated users to delete their uploads
CREATE POLICY "Authenticated users can delete company logos"
ON storage.objects
FOR DELETE
TO authenticated
USING (
    bucket_id = 'assets'
    AND (storage.foldername(name))[1] = 'company-logos'
);

-- Allow public read access to all assets (logos need to be publicly accessible for PDFs)
CREATE POLICY "Public read access to assets"
ON storage.objects
FOR SELECT
TO public
USING (bucket_id = 'assets');
