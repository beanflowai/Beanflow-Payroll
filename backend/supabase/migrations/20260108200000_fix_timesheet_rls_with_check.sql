-- Migration: Fix RLS policy for timesheet_entries to add WITH CHECK
-- This prevents updating company_id to a different company

-- Drop the existing update policy
drop policy if exists "Users can update own company timesheet entries" on timesheet_entries;

-- Recreate with WITH CHECK to prevent company_id modification
create policy "Users can update own company timesheet entries"
  on timesheet_entries for update
  using (company_id in (select id from companies where user_id = auth.uid()::text))
  with check (company_id in (select id from companies where user_id = auth.uid()::text));
