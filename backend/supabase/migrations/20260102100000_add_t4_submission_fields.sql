-- T4 CRA Submission Tracking Fields
-- Adds fields to track CRA submission status for T4 summaries

-- Add submission tracking fields to t4_summaries table
ALTER TABLE t4_summaries ADD COLUMN IF NOT EXISTS cra_confirmation_number TEXT;
ALTER TABLE t4_summaries ADD COLUMN IF NOT EXISTS submitted_at TIMESTAMPTZ;
ALTER TABLE t4_summaries ADD COLUMN IF NOT EXISTS submitted_by TEXT;
ALTER TABLE t4_summaries ADD COLUMN IF NOT EXISTS submission_notes TEXT;

-- Add comment for documentation
COMMENT ON COLUMN t4_summaries.cra_confirmation_number IS 'CRA confirmation number received after successful T4 submission';
COMMENT ON COLUMN t4_summaries.submitted_at IS 'Timestamp when T4 was submitted to CRA';
COMMENT ON COLUMN t4_summaries.submitted_by IS 'User who submitted the T4 to CRA';
COMMENT ON COLUMN t4_summaries.submission_notes IS 'Optional notes about the CRA submission';

-- Add index on confirmation number for lookup performance
CREATE INDEX IF NOT EXISTS idx_t4_summaries_cra_confirmation
  ON t4_summaries(cra_confirmation_number)
  WHERE cra_confirmation_number IS NOT NULL;
