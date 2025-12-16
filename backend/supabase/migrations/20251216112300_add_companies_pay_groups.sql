-- =============================================================================
-- COMPANIES & PAY GROUPS - DATABASE SCHEMA
-- =============================================================================
-- Description: Creates companies and pay_groups tables, adds foreign keys to employees
-- Author: BeanFlow Payroll Team
-- Date: 2025-12-16
-- =============================================================================

-- =============================================================================
-- COMPANIES TABLE
-- =============================================================================
-- Company information, CRA remittance configuration, and bookkeeping integration

CREATE TABLE IF NOT EXISTS companies (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Multi-tenancy
    user_id TEXT NOT NULL,

    -- Company Information
    company_name TEXT NOT NULL,
    business_number CHAR(9) NOT NULL,  -- 9-digit CRA Business Number
    payroll_account_number CHAR(15) NOT NULL,  -- e.g., 123456789RP0001
    province TEXT NOT NULL CHECK (
        province IN (
            'AB', 'BC', 'MB', 'NB', 'NL', 'NS',
            'NT', 'NU', 'ON', 'PE', 'SK', 'YT'
        )
    ),

    -- CRA Remittance Configuration
    remitter_type TEXT NOT NULL DEFAULT 'regular' CHECK (
        remitter_type IN ('quarterly', 'regular', 'threshold_1', 'threshold_2')
    ),

    -- Payroll Preferences
    auto_calculate_deductions BOOLEAN DEFAULT TRUE,
    send_paystub_emails BOOLEAN DEFAULT FALSE,

    -- Bookkeeping Integration
    bookkeeping_ledger_id TEXT,
    bookkeeping_ledger_name TEXT,
    bookkeeping_connected_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT unique_company_per_user UNIQUE (user_id, business_number)
);

-- Indexes for companies
CREATE INDEX IF NOT EXISTS idx_companies_user_id ON companies(user_id);

-- RLS Policy for companies
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can access own companies"
    ON companies
    FOR ALL
    USING (user_id = current_setting('app.current_user_id', TRUE));

-- Trigger for updated_at
CREATE TRIGGER update_companies_updated_at
    BEFORE UPDATE ON companies
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- =============================================================================
-- PAY_GROUPS TABLE
-- =============================================================================
-- Pay Group "Policy Template" - defines payroll configuration for groups of employees

CREATE TABLE IF NOT EXISTS pay_groups (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign Key to Company
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,

    -- Basic Info
    name TEXT NOT NULL,
    description TEXT,
    pay_frequency TEXT NOT NULL CHECK (
        pay_frequency IN ('weekly', 'bi_weekly', 'semi_monthly', 'monthly')
    ),
    employment_type TEXT NOT NULL DEFAULT 'full_time' CHECK (
        employment_type IN ('full_time', 'part_time')
    ),

    -- Pay Schedule
    next_pay_date DATE NOT NULL,
    period_start_day TEXT NOT NULL DEFAULT 'monday' CHECK (
        period_start_day IN (
            'sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday',
            '1st_and_16th', '15th_and_last',
            '1st_of_month', '15th_of_month', 'last_day_of_month'
        )
    ),

    -- Leave Policy
    leave_enabled BOOLEAN DEFAULT TRUE,

    -- Statutory Deduction Defaults (JSONB)
    statutory_defaults JSONB DEFAULT '{
        "cpp_exempt_by_default": false,
        "cpp2_exempt_by_default": false,
        "ei_exempt_by_default": false
    }'::JSONB,

    -- Overtime & Bank Time Policy (JSONB)
    overtime_policy JSONB DEFAULT '{
        "bank_time_enabled": false,
        "bank_time_rate": 1.5,
        "bank_time_expiry_months": 3,
        "require_written_agreement": true
    }'::JSONB,

    -- WCB/Workers Compensation Config (JSONB)
    wcb_config JSONB DEFAULT '{
        "enabled": false,
        "assessment_rate": 0
    }'::JSONB,

    -- Group Benefits (JSONB)
    group_benefits JSONB DEFAULT '{
        "enabled": false,
        "health": {"enabled": false, "employee_deduction": 0, "employer_contribution": 0, "is_taxable": false},
        "dental": {"enabled": false, "employee_deduction": 0, "employer_contribution": 0, "is_taxable": false},
        "vision": {"enabled": false, "employee_deduction": 0, "employer_contribution": 0, "is_taxable": false},
        "life_insurance": {"enabled": false, "employee_deduction": 0, "employer_contribution": 0, "is_taxable": false, "coverage_amount": 0},
        "disability": {"enabled": false, "employee_deduction": 0, "employer_contribution": 0, "is_taxable": false}
    }'::JSONB,

    -- Custom Deductions (JSONB Array)
    custom_deductions JSONB DEFAULT '[]'::JSONB,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT unique_pay_group_name_per_company UNIQUE (company_id, name)
);

-- Indexes for pay_groups
CREATE INDEX IF NOT EXISTS idx_pay_groups_company_id ON pay_groups(company_id);
CREATE INDEX IF NOT EXISTS idx_pay_groups_frequency_type ON pay_groups(pay_frequency, employment_type);

-- RLS Policy for pay_groups (via company)
ALTER TABLE pay_groups ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can access own pay groups"
    ON pay_groups
    FOR ALL
    USING (
        company_id IN (
            SELECT id FROM companies
            WHERE user_id = current_setting('app.current_user_id', TRUE)
        )
    );

-- Trigger for updated_at
CREATE TRIGGER update_pay_groups_updated_at
    BEFORE UPDATE ON pay_groups
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- =============================================================================
-- ALTER EMPLOYEES TABLE - Add Foreign Keys
-- =============================================================================

-- Add company_id column (required after migration)
ALTER TABLE employees
    ADD COLUMN IF NOT EXISTS company_id UUID REFERENCES companies(id) ON DELETE SET NULL;

-- Add pay_group_id column (optional - for filtering matching pay groups)
ALTER TABLE employees
    ADD COLUMN IF NOT EXISTS pay_group_id UUID REFERENCES pay_groups(id) ON DELETE SET NULL;

-- Create indexes for the new foreign keys
CREATE INDEX IF NOT EXISTS idx_employees_company_id ON employees(company_id);
CREATE INDEX IF NOT EXISTS idx_employees_pay_group_id ON employees(pay_group_id);


-- =============================================================================
-- HELPER VIEWS (Optional - for common queries)
-- =============================================================================

-- View: Active employees with company and pay group info
create view public.v_employee_details as
select
  e.id,
  e.user_id,
  e.ledger_id,
  e.first_name,
  e.last_name,
  e.sin_encrypted,
  e.email,
  e.province_of_employment,
  e.pay_frequency,
  e.employment_type,
  e.annual_salary,
  e.hourly_rate,
  e.federal_claim_amount,
  e.provincial_claim_amount,
  e.is_cpp_exempt,
  e.is_ei_exempt,
  e.cpp2_exempt,
  e.rrsp_per_period,
  e.union_dues_per_period,
  e.hire_date,
  e.termination_date,
  e.vacation_config,
  e.vacation_balance,
  e.created_at,
  e.updated_at,
  e.company_id,
  e.pay_group_id,
  c.company_name,
  c.province as company_province,
  pg.name as pay_group_name,
  pg.next_pay_date as pay_group_next_pay_date
from
  employees e
  left join companies c on e.company_id = c.id
  left join pay_groups pg on e.pay_group_id = pg.id;

-- View: Pay group summary with employee counts
create view public.v_pay_group_summary with (security_invoker = on) as
 SELECT pg.id,
    pg.company_id,
    pg.name,
    pg.description,
    pg.pay_frequency,
    pg.employment_type,
    pg.next_pay_date,
    pg.period_start_day,
    pg.leave_enabled,
    pg.statutory_defaults,
    pg.overtime_policy,
    pg.wcb_config,
    pg.group_benefits,
    pg.custom_deductions,
    pg.created_at,
    pg.updated_at,
    c.company_name,
    count(e.id) AS employee_count
   FROM pay_groups pg
     JOIN companies c ON pg.company_id = c.id
     LEFT JOIN employees e ON e.pay_group_id = pg.id AND e.termination_date IS NULL
  GROUP BY pg.id, c.company_name;
