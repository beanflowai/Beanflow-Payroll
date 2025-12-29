-- =============================================================================
-- REMOVE UNUSED sick_leave_configs TABLE
-- =============================================================================
-- Description: Removes the sick_leave_configs table as configurations are now
--              loaded from JSON files at backend/config/sick_leave/
-- Author: BeanFlow Payroll Team
-- Date: 2025-12-29
-- Reference: docs/08_holidays_vacation.md Task 8.7
--
-- WHY: The sick_leave_configs table was created but never actually used.
--      The API reads configurations from JSON files instead, which supports:
--      - Mid-year version changes (e.g., Ontario June 2025 changes)
--      - No database dependency for configuration
--      - Easier version control and deployment
--
-- PRESERVED TABLES:
-- - employee_sick_leave_balances: Stores employee-specific balance data (used)
-- - sick_leave_usage_history: Audit trail of sick leave usage (used)
-- =============================================================================

-- Drop trigger first (depends on the table)
DROP TRIGGER IF EXISTS update_sick_leave_configs_updated_at ON sick_leave_configs;

-- Drop RLS policy
DROP POLICY IF EXISTS "Authenticated users can read sick leave configs" ON sick_leave_configs;

-- Drop index
DROP INDEX IF EXISTS idx_sick_leave_configs_province;

-- Drop the table
DROP TABLE IF EXISTS sick_leave_configs;

-- Update comments
COMMENT ON TABLE employee_sick_leave_balances IS
    'Per-year sick leave balance tracking for each employee. Province configs loaded from JSON files.';
