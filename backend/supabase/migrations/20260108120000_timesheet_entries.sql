-- Migration: timesheet_entries table for daily time tracking
-- This table stores daily regular/overtime hours for hourly employees
-- Data is used for audit, compliance, and future holiday pay calculations

-- Create table
create table timesheet_entries (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references companies(id) on delete cascade,
  employee_id uuid not null references employees(id) on delete cascade,
  payroll_record_id uuid references payroll_records(id) on delete set null,

  work_date date not null,
  regular_hours numeric(5,2) not null default 0 check (regular_hours >= 0),
  overtime_hours numeric(5,2) not null default 0 check (overtime_hours >= 0),

  -- Audit fields
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  created_by uuid references auth.users(id),

  -- Unique constraint: one entry per employee per payroll record per date
  unique(employee_id, payroll_record_id, work_date)
);

-- Indexes for query performance
create index idx_timesheet_entries_employee on timesheet_entries(employee_id);
create index idx_timesheet_entries_payroll_record on timesheet_entries(payroll_record_id);
create index idx_timesheet_entries_work_date on timesheet_entries(work_date);
create index idx_timesheet_entries_company on timesheet_entries(company_id);

-- Enable Row Level Security
alter table timesheet_entries enable row level security;

-- RLS Policies: Users can only access their own company's timesheet entries
create policy "Users can view own company timesheet entries"
  on timesheet_entries for select
  using (company_id in (select id from companies where user_id = auth.uid()::text));

create policy "Users can insert own company timesheet entries"
  on timesheet_entries for insert
  with check (company_id in (select id from companies where user_id = auth.uid()::text));

create policy "Users can update own company timesheet entries"
  on timesheet_entries for update
  using (company_id in (select id from companies where user_id = auth.uid()::text));

create policy "Users can delete own company timesheet entries"
  on timesheet_entries for delete
  using (company_id in (select id from companies where user_id = auth.uid()::text));

-- Trigger: auto-update updated_at column
create trigger update_timesheet_entries_updated_at
  before update on timesheet_entries
  for each row execute function update_updated_at_column();
