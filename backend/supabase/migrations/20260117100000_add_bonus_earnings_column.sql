-- Migration: Add bonus_earnings column to payroll_records
-- Purpose: Support separate bonus earnings for proper bonus tax method calculation
-- Date: 2026-01-17

-- Add bonus_earnings column
ALTER TABLE public.payroll_records
ADD COLUMN IF NOT EXISTS bonus_earnings NUMERIC(10, 2) DEFAULT 0;

-- Update computed columns to include bonus_earnings in total_gross
-- First drop the existing generated columns
ALTER TABLE public.payroll_records DROP COLUMN IF EXISTS total_gross;
ALTER TABLE public.payroll_records DROP COLUMN IF EXISTS net_pay;

-- Recreate total_gross including bonus_earnings
ALTER TABLE public.payroll_records
ADD COLUMN total_gross NUMERIC(12, 2) GENERATED ALWAYS AS (
    gross_regular + gross_overtime + holiday_pay + holiday_premium_pay + vacation_pay_paid + other_earnings + bonus_earnings
) STORED;

-- Recreate net_pay
ALTER TABLE public.payroll_records
ADD COLUMN net_pay NUMERIC(12, 2) GENERATED ALWAYS AS (
    (gross_regular + gross_overtime + holiday_pay + holiday_premium_pay + vacation_pay_paid + other_earnings + bonus_earnings) -
    (cpp_employee + COALESCE(cpp_additional, 0) + ei_employee + federal_tax + provincial_tax + other_deductions)
) STORED;

-- Add comment for documentation
COMMENT ON COLUMN public.payroll_records.bonus_earnings IS 'Bonus/lump-sum earnings taxed using bonus tax method (separate from other_earnings)';
