-- =============================================================================
-- SICK LEAVE CONFIGURATION & BALANCE TRACKING - DATABASE SCHEMA
-- =============================================================================
-- Description: Adds sick leave configuration table for province-level rules
--              and employee sick leave balance tracking per year
-- Author: BeanFlow Payroll Team
-- Date: 2025-12-29
-- Reference: docs/08_holidays_vacation.md Task 8.7
-- =============================================================================

-- =============================================================================
-- SICK LEAVE CONFIGURATION TABLE (Province-Level Rules)
-- =============================================================================

CREATE TABLE IF NOT EXISTS sick_leave_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    province_code VARCHAR(10) NOT NULL,  -- 'BC', 'ON', 'Federal', etc.
    paid_days_per_year INTEGER NOT NULL DEFAULT 0,
    unpaid_days_per_year INTEGER NOT NULL DEFAULT 0,
    waiting_period_days INTEGER NOT NULL DEFAULT 0,  -- Days of employment before eligible
    allows_carryover BOOLEAN NOT NULL DEFAULT FALSE,
    max_carryover_days INTEGER NOT NULL DEFAULT 0,
    accrual_method VARCHAR(20) NOT NULL DEFAULT 'immediate',  -- 'immediate' or 'monthly'
    -- For monthly accrual (Federal): initial days after qualifying period
    initial_days_after_qualifying INTEGER DEFAULT 0,
    -- For monthly accrual: days earned per month after initial
    days_per_month_after_initial INTEGER DEFAULT 0,
    effective_date DATE NOT NULL DEFAULT '2025-01-01',
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(province_code, effective_date)
);

-- Create index for province lookup
CREATE INDEX IF NOT EXISTS idx_sick_leave_configs_province ON sick_leave_configs(province_code);

-- =============================================================================
-- INSERT DEFAULT PROVINCIAL SICK LEAVE CONFIGURATIONS (2025)
-- =============================================================================

INSERT INTO sick_leave_configs (
    province_code, paid_days_per_year, unpaid_days_per_year, waiting_period_days,
    allows_carryover, max_carryover_days, accrual_method,
    initial_days_after_qualifying, days_per_month_after_initial,
    effective_date, notes
) VALUES
    -- British Columbia: 5 paid + 3 unpaid, 90 day waiting period
    ('BC', 5, 3, 90, FALSE, 0, 'immediate', 0, 0, '2025-01-01',
     'BC Employment Standards Act - Average day''s pay calculation'),

    -- Ontario: 0 paid + 3 unpaid (IDEL days)
    ('ON', 0, 3, 0, FALSE, 0, 'immediate', 0, 0, '2025-01-01',
     'Ontario ESA - Infectious Disease Emergency Leave (IDEL)'),

    -- Alberta: No statutory sick leave
    ('AB', 0, 0, 0, FALSE, 0, 'immediate', 0, 0, '2025-01-01',
     'No statutory sick leave in Alberta'),

    -- Manitoba: No statutory paid sick leave
    ('MB', 0, 0, 0, FALSE, 0, 'immediate', 0, 0, '2025-01-01',
     'No statutory paid sick leave in Manitoba'),

    -- Saskatchewan: No statutory sick leave
    ('SK', 0, 0, 0, FALSE, 0, 'immediate', 0, 0, '2025-01-01',
     'No statutory sick leave in Saskatchewan'),

    -- New Brunswick: 5 unpaid days
    ('NB', 0, 5, 0, FALSE, 0, 'immediate', 0, 0, '2025-01-01',
     'New Brunswick ESA - 5 unpaid sick days'),

    -- Nova Scotia: 3 unpaid days
    ('NS', 0, 3, 0, FALSE, 0, 'immediate', 0, 0, '2025-01-01',
     'Nova Scotia Labour Standards - 3 unpaid sick days'),

    -- Prince Edward Island: 3 unpaid days
    ('PE', 0, 3, 0, FALSE, 0, 'immediate', 0, 0, '2025-01-01',
     'PEI Employment Standards - 3 unpaid sick days'),

    -- Newfoundland & Labrador: 7 unpaid days
    ('NL', 0, 7, 0, FALSE, 0, 'immediate', 0, 0, '2025-01-01',
     'NL Labour Standards - 7 unpaid sick days'),

    -- Northwest Territories: 5 unpaid days
    ('NT', 0, 5, 0, FALSE, 0, 'immediate', 0, 0, '2025-01-01',
     'NWT Employment Standards - 5 unpaid sick days'),

    -- Nunavut: 5 unpaid days
    ('NU', 0, 5, 0, FALSE, 0, 'immediate', 0, 0, '2025-01-01',
     'Nunavut Labour Standards - 5 unpaid sick days'),

    -- Yukon: No statutory sick leave
    ('YT', 0, 0, 0, FALSE, 0, 'immediate', 0, 0, '2025-01-01',
     'No statutory sick leave in Yukon'),

    -- Federal (Canada Labour Code): 10 paid days, 30 day waiting, monthly accrual
    ('Federal', 10, 0, 30, TRUE, 10, 'monthly', 3, 1, '2025-01-01',
     'Canada Labour Code s.239 - 3 days after 30-day period, +1/month, max 10, carryover allowed')

ON CONFLICT (province_code, effective_date) DO NOTHING;

-- =============================================================================
-- EMPLOYEE SICK LEAVE BALANCE TABLE (Per-Year Tracking)
-- =============================================================================

CREATE TABLE IF NOT EXISTS employee_sick_leave_balances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    year INTEGER NOT NULL,

    -- Entitlement (calculated based on province config)
    paid_days_entitled NUMERIC(4, 2) NOT NULL DEFAULT 0,
    unpaid_days_entitled NUMERIC(4, 2) NOT NULL DEFAULT 0,

    -- Usage tracking
    paid_days_used NUMERIC(4, 2) NOT NULL DEFAULT 0,
    unpaid_days_used NUMERIC(4, 2) NOT NULL DEFAULT 0,

    -- Carryover from previous year (Federal only)
    carried_over_days NUMERIC(4, 2) NOT NULL DEFAULT 0,

    -- Eligibility tracking
    eligibility_date DATE,  -- When employee becomes eligible (hire_date + waiting_period)
    is_eligible BOOLEAN DEFAULT FALSE,

    -- Accrual tracking (for monthly accrual like Federal)
    last_accrual_date DATE,
    accrued_days_ytd NUMERIC(4, 2) NOT NULL DEFAULT 0,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(employee_id, year)
);

-- Create indexes for efficient lookups
CREATE INDEX IF NOT EXISTS idx_employee_sick_leave_balances_employee ON employee_sick_leave_balances(employee_id);
CREATE INDEX IF NOT EXISTS idx_employee_sick_leave_balances_year ON employee_sick_leave_balances(year);
CREATE INDEX IF NOT EXISTS idx_employee_sick_leave_balances_employee_year ON employee_sick_leave_balances(employee_id, year);

-- =============================================================================
-- SICK LEAVE USAGE HISTORY TABLE (Audit Trail)
-- =============================================================================

CREATE TABLE IF NOT EXISTS sick_leave_usage_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    balance_id UUID NOT NULL REFERENCES employee_sick_leave_balances(id) ON DELETE CASCADE,
    payroll_record_id UUID REFERENCES payroll_records(id) ON DELETE SET NULL,

    -- Usage details
    usage_date DATE NOT NULL,
    hours_taken NUMERIC(6, 2) NOT NULL,
    days_taken NUMERIC(4, 2) NOT NULL,  -- hours / 8 typically
    is_paid BOOLEAN NOT NULL DEFAULT TRUE,

    -- Payment calculation
    average_day_pay NUMERIC(10, 2),
    sick_pay_amount NUMERIC(10, 2),
    calculation_method VARCHAR(50),  -- 'bc_30_day_avg', 'federal_20_day_avg', etc.

    -- Metadata
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_sick_leave_usage_employee ON sick_leave_usage_history(employee_id);
CREATE INDEX IF NOT EXISTS idx_sick_leave_usage_date ON sick_leave_usage_history(usage_date);

-- =============================================================================
-- RLS POLICIES
-- =============================================================================

-- Enable RLS on new tables
ALTER TABLE sick_leave_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE employee_sick_leave_balances ENABLE ROW LEVEL SECURITY;
ALTER TABLE sick_leave_usage_history ENABLE ROW LEVEL SECURITY;

-- sick_leave_configs: Read-only for all authenticated users (config is shared)
CREATE POLICY "Authenticated users can read sick leave configs"
    ON sick_leave_configs FOR SELECT
    TO authenticated
    USING (true);

-- employee_sick_leave_balances: Users can only access their own employees' balances
CREATE POLICY "Users can read their employees sick leave balances"
    ON employee_sick_leave_balances FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM employees e
            WHERE e.id = employee_sick_leave_balances.employee_id
            AND e.user_id = auth.uid()::text
        )
    );

CREATE POLICY "Users can insert their employees sick leave balances"
    ON employee_sick_leave_balances FOR INSERT
    TO authenticated
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM employees e
            WHERE e.id = employee_sick_leave_balances.employee_id
            AND e.user_id = auth.uid()::text
        )
    );

CREATE POLICY "Users can update their employees sick leave balances"
    ON employee_sick_leave_balances FOR UPDATE
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM employees e
            WHERE e.id = employee_sick_leave_balances.employee_id
            AND e.user_id = auth.uid()::text
        )
    );

-- sick_leave_usage_history: Users can only access their own employees' history
CREATE POLICY "Users can read their employees sick leave history"
    ON sick_leave_usage_history FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM employees e
            WHERE e.id = sick_leave_usage_history.employee_id
            AND e.user_id = auth.uid()::text
        )
    );

CREATE POLICY "Users can insert their employees sick leave history"
    ON sick_leave_usage_history FOR INSERT
    TO authenticated
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM employees e
            WHERE e.id = sick_leave_usage_history.employee_id
            AND e.user_id = auth.uid()::text
        )
    );

-- =============================================================================
-- TRIGGER: Auto-update updated_at timestamp
-- =============================================================================

-- For sick_leave_configs
CREATE TRIGGER update_sick_leave_configs_updated_at
    BEFORE UPDATE ON sick_leave_configs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- For employee_sick_leave_balances
CREATE TRIGGER update_employee_sick_leave_balances_updated_at
    BEFORE UPDATE ON employee_sick_leave_balances
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON TABLE sick_leave_configs IS 'Province-level sick leave configuration including paid/unpaid days, waiting periods, and carryover rules';
COMMENT ON TABLE employee_sick_leave_balances IS 'Per-year sick leave balance tracking for each employee';
COMMENT ON TABLE sick_leave_usage_history IS 'Audit trail of sick leave usage with payment details';

COMMENT ON COLUMN sick_leave_configs.accrual_method IS 'immediate: full entitlement from eligibility date. monthly: gradual accrual (Federal)';
COMMENT ON COLUMN sick_leave_configs.initial_days_after_qualifying IS 'For monthly accrual: days granted immediately after qualifying period (Federal: 3)';
COMMENT ON COLUMN sick_leave_configs.days_per_month_after_initial IS 'For monthly accrual: additional days per month (Federal: 1)';
COMMENT ON COLUMN employee_sick_leave_balances.carried_over_days IS 'Days carried over from previous year (Federal only, max 10)';
