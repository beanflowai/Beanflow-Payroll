-- Add onboarding_progress JSONB column to companies table
ALTER TABLE companies
ADD COLUMN onboarding_progress JSONB DEFAULT '{
  "completedSteps": [],
  "dismissedAt": null,
  "lastUpdated": null
}'::JSONB;

-- Create index for efficient querying
CREATE INDEX idx_companies_onboarding ON companies
  USING GIN ((onboarding_progress->'completedSteps'));

COMMENT ON COLUMN companies.onboarding_progress IS
  'Tracks onboarding progress: completedSteps array, dismissedAt timestamp, lastUpdated timestamp';
