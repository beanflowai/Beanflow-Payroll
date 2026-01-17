-- Migration: Add tax breakdown columns to payroll_records
-- Purpose: Support separate display of tax on income vs bonus (PDOC-style)
-- Date: 2026-01-17

-- Add tax breakdown columns for federal tax
ALTER TABLE public.payroll_records
ADD COLUMN IF NOT EXISTS federal_tax_on_income NUMERIC(10, 2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS federal_tax_on_bonus NUMERIC(10, 2) DEFAULT 0;

-- Add tax breakdown columns for provincial tax
ALTER TABLE public.payroll_records
ADD COLUMN IF NOT EXISTS provincial_tax_on_income NUMERIC(10, 2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS provincial_tax_on_bonus NUMERIC(10, 2) DEFAULT 0;

-- Add comments for documentation
COMMENT ON COLUMN public.payroll_records.federal_tax_on_income IS 'Federal tax calculated on regular income using annualization method';
COMMENT ON COLUMN public.payroll_records.federal_tax_on_bonus IS 'Federal tax calculated on bonus using marginal rate method';
COMMENT ON COLUMN public.payroll_records.provincial_tax_on_income IS 'Provincial tax calculated on regular income using annualization method';
COMMENT ON COLUMN public.payroll_records.provincial_tax_on_bonus IS 'Provincial tax calculated on bonus using marginal rate method';
