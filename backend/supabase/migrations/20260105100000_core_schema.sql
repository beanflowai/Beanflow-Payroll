-- =============================================================================
-- CONSOLIDATED MIGRATION 001: CORE SCHEMA
-- =============================================================================
-- Description: Core tables for Beanflow Payroll
--   - companies, pay_groups, employees, payroll_runs, payroll_records
--   - All RLS policies using auth.uid()
--   - Helper functions and triggers
-- =============================================================================

-- Ensure helper function exists
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- COMPANIES TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    company_name TEXT NOT NULL,
    business_number CHAR(9) NOT NULL,
    payroll_account_number CHAR(15) NOT NULL,
    province TEXT NOT NULL CHECK (
        province IN ('AB', 'BC', 'MB', 'NB', 'NL', 'NS', 'NT', 'NU', 'ON', 'PE', 'SK', 'YT')
    ),
    remitter_type TEXT NOT NULL DEFAULT 'regular' CHECK (
        remitter_type IN ('quarterly', 'regular', 'threshold_1', 'threshold_2')
    ),
    auto_calculate_deductions BOOLEAN DEFAULT TRUE,
    send_paystub_emails BOOLEAN DEFAULT FALSE,
    -- Bookkeeping integration
    bookkeeping_ledger_id TEXT,
    bookkeeping_ledger_name TEXT,
    bookkeeping_connected_at TIMESTAMPTZ,
    ledger_id TEXT,
    -- Address
    address_street TEXT,
    address_city TEXT,
    address_postal_code TEXT,
    -- Branding
    logo_url TEXT,
    -- Portal routing
    slug TEXT NOT NULL,
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_company_per_user UNIQUE (user_id, business_number)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_companies_user_id ON companies(user_id);
CREATE INDEX IF NOT EXISTS idx_companies_ledger_id ON companies(ledger_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_companies_slug ON companies(slug) WHERE slug IS NOT NULL;

-- RLS
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own companies" ON companies FOR SELECT
    USING (user_id = auth.uid()::text);
CREATE POLICY "Users can insert own companies" ON companies FOR INSERT
    WITH CHECK (user_id = auth.uid()::text);
CREATE POLICY "Users can update own companies" ON companies FOR UPDATE
    USING (user_id = auth.uid()::text);
CREATE POLICY "Users can delete own companies" ON companies FOR DELETE
    USING (user_id = auth.uid()::text);

-- Trigger
CREATE TRIGGER update_companies_updated_at
    BEFORE UPDATE ON companies FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Slug generation function
CREATE OR REPLACE FUNCTION generate_company_slug(p_company_name TEXT, p_company_id UUID)
RETURNS TEXT AS $$
DECLARE
    v_base_slug TEXT;
    v_slug TEXT;
    v_counter INTEGER := 0;
BEGIN
    v_base_slug := LOWER(
        REGEXP_REPLACE(
            REGEXP_REPLACE(TRIM(p_company_name), '[^a-zA-Z0-9\s-]', '', 'g'),
            '\s+', '-', 'g'
        )
    );
    v_base_slug := REGEXP_REPLACE(v_base_slug, '-+', '-', 'g');
    v_base_slug := TRIM(BOTH '-' FROM v_base_slug);
    IF v_base_slug = '' OR v_base_slug IS NULL THEN
        v_base_slug := 'company';
    END IF;
    v_slug := v_base_slug;
    WHILE EXISTS (SELECT 1 FROM companies WHERE slug = v_slug AND id != p_company_id) LOOP
        v_counter := v_counter + 1;
        v_slug := v_base_slug || '-' || v_counter;
    END LOOP;
    RETURN v_slug;
END;
$$ LANGUAGE plpgsql;

-- Auto-generate slug on insert
CREATE OR REPLACE FUNCTION set_company_slug()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.slug IS NULL OR NEW.slug = '' THEN
        NEW.slug := generate_company_slug(NEW.company_name, COALESCE(NEW.id, gen_random_uuid()));
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_set_company_slug
    BEFORE INSERT ON companies FOR EACH ROW
    EXECUTE FUNCTION set_company_slug();

-- =============================================================================
-- PAY_GROUPS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS pay_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    pay_frequency TEXT NOT NULL CHECK (
        pay_frequency IN ('weekly', 'bi_weekly', 'semi_monthly', 'monthly')
    ),
    employment_type TEXT NOT NULL DEFAULT 'full_time' CHECK (
        employment_type IN ('full_time', 'part_time')
    ),
    next_period_end DATE NOT NULL,
    period_start_day TEXT NOT NULL DEFAULT 'monday' CHECK (
        period_start_day IN (
            'sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday',
            '1st_and_16th', '15th_and_last', '1st_of_month', '15th_of_month', 'last_day_of_month'
        )
    ),
    leave_enabled BOOLEAN DEFAULT TRUE,
    tax_calculation_method TEXT NOT NULL DEFAULT 'annualization'
        CHECK (tax_calculation_method IN ('annualization', 'cumulative_averaging')),
    overtime_policy JSONB DEFAULT '{"bank_time_enabled": false, "bank_time_rate": 1.5, "bank_time_expiry_months": 3, "require_written_agreement": true}'::JSONB,
    wcb_config JSONB DEFAULT '{"enabled": false, "assessment_rate": 0}'::JSONB,
    group_benefits JSONB DEFAULT '{"enabled": false}'::JSONB,
    earnings_config JSONB DEFAULT '{"enabled": false}'::JSONB,
    taxable_benefits_config JSONB DEFAULT '{"enabled": false}'::JSONB,
    deductions_config JSONB DEFAULT '{"enabled": true, "rrsp": {"enabled": false}, "unionDues": {"enabled": false}, "garnishments": {"enabled": true}}'::JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_pay_group_name_per_company UNIQUE (company_id, name)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_pay_groups_company_id ON pay_groups(company_id);
CREATE INDEX IF NOT EXISTS idx_pay_groups_frequency_type ON pay_groups(pay_frequency, employment_type);

-- RLS
ALTER TABLE pay_groups ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own pay groups" ON pay_groups FOR SELECT
    USING (company_id IN (SELECT id FROM companies WHERE user_id = auth.uid()::text));
CREATE POLICY "Users can insert own pay groups" ON pay_groups FOR INSERT
    WITH CHECK (company_id IN (SELECT id FROM companies WHERE user_id = auth.uid()::text));
CREATE POLICY "Users can update own pay groups" ON pay_groups FOR UPDATE
    USING (company_id IN (SELECT id FROM companies WHERE user_id = auth.uid()::text))
    WITH CHECK (company_id IN (SELECT id FROM companies WHERE user_id = auth.uid()::text));
CREATE POLICY "Users can delete own pay groups" ON pay_groups FOR DELETE
    USING (company_id IN (SELECT id FROM companies WHERE user_id = auth.uid()::text));

-- Trigger
CREATE TRIGGER update_pay_groups_updated_at
    BEFORE UPDATE ON pay_groups FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- EMPLOYEES TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS employees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    company_id UUID REFERENCES companies(id) ON DELETE SET NULL,
    pay_group_id UUID REFERENCES pay_groups(id) ON DELETE SET NULL,
    -- Personal Information
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    sin_encrypted TEXT NOT NULL,
    email TEXT,
    -- Address
    address_street TEXT,
    address_city TEXT,
    address_postal_code TEXT,
    occupation TEXT,
    -- Employment Details
    province_of_employment TEXT NOT NULL CHECK (
        province_of_employment IN ('AB', 'BC', 'MB', 'NB', 'NL', 'NS', 'NT', 'NU', 'ON', 'PE', 'SK', 'YT')
    ),
    pay_frequency TEXT NOT NULL CHECK (
        pay_frequency IN ('weekly', 'bi_weekly', 'semi_monthly', 'monthly')
    ),
    employment_type TEXT DEFAULT 'full_time' CHECK (
        employment_type IN ('full_time', 'part_time', 'contract', 'casual')
    ),
    -- Compensation
    annual_salary NUMERIC(12, 2),
    hourly_rate NUMERIC(10, 2),
    -- TD1 Claims (additional claims beyond BPA)
    federal_additional_claims NUMERIC(12, 2) NOT NULL DEFAULT 0,
    provincial_additional_claims NUMERIC(12, 2) NOT NULL DEFAULT 0,
    -- Exemptions
    is_cpp_exempt BOOLEAN DEFAULT FALSE,
    is_ei_exempt BOOLEAN DEFAULT FALSE,
    cpp2_exempt BOOLEAN DEFAULT FALSE,
    -- Initial YTD (for mid-year transfers)
    initial_ytd_cpp NUMERIC(10, 2) DEFAULT 0,
    initial_ytd_cpp2 NUMERIC(10, 2) DEFAULT 0,
    initial_ytd_ei NUMERIC(10, 2) DEFAULT 0,
    initial_ytd_year INTEGER DEFAULT NULL,
    -- Employment Dates
    hire_date DATE NOT NULL,
    termination_date DATE,
    -- Vacation
    vacation_config JSONB DEFAULT '{"payout_method": "accrual", "vacation_rate": "0.04"}'::JSONB,
    vacation_balance NUMERIC(12, 2) DEFAULT 0,
    -- Sick Leave
    sick_balance NUMERIC(12, 2) DEFAULT 0,
    -- Tags
    tags TEXT[] DEFAULT '{}',
    -- Portal
    portal_status TEXT DEFAULT 'not_set' CHECK (portal_status IN ('not_set', 'invited', 'active', 'disabled')),
    portal_invited_at TIMESTAMPTZ,
    portal_last_login_at TIMESTAMPTZ,
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    -- Constraints
    CONSTRAINT chk_salary_or_hourly CHECK (annual_salary IS NOT NULL OR hourly_rate IS NOT NULL),
    CONSTRAINT unique_employee_sin UNIQUE (user_id, company_id, sin_encrypted),
    CONSTRAINT chk_initial_ytd_cpp_non_negative CHECK (initial_ytd_cpp >= 0),
    CONSTRAINT chk_initial_ytd_cpp2_non_negative CHECK (initial_ytd_cpp2 >= 0),
    CONSTRAINT chk_initial_ytd_ei_non_negative CHECK (initial_ytd_ei >= 0)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_employees_user_id ON employees(user_id);
CREATE INDEX IF NOT EXISTS idx_employees_company_id ON employees(company_id);
CREATE INDEX IF NOT EXISTS idx_employees_pay_group_id ON employees(pay_group_id);
CREATE INDEX IF NOT EXISTS idx_employees_province ON employees(province_of_employment);
CREATE INDEX IF NOT EXISTS idx_employees_active ON employees(user_id, company_id) WHERE termination_date IS NULL;
CREATE INDEX IF NOT EXISTS idx_employees_tags ON employees USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_employees_portal_status ON employees(portal_status);

-- RLS
ALTER TABLE employees ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own employees" ON employees FOR SELECT
    USING (user_id = auth.uid()::text);
CREATE POLICY "Users can insert own employees" ON employees FOR INSERT
    WITH CHECK (user_id = auth.uid()::text);
CREATE POLICY "Users can update own employees" ON employees FOR UPDATE
    USING (user_id = auth.uid()::text);
CREATE POLICY "Users can delete own employees" ON employees FOR DELETE
    USING (user_id = auth.uid()::text);

-- Trigger
CREATE TRIGGER update_employees_updated_at
    BEFORE UPDATE ON employees FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- PAYROLL_RUNS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS payroll_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    company_id UUID REFERENCES companies(id),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    pay_date DATE NOT NULL,
    status TEXT DEFAULT 'draft' CHECK (
        status IN ('draft', 'calculating', 'pending_approval', 'approved', 'paid', 'cancelled')
    ),
    -- Summary Totals
    total_employees INTEGER DEFAULT 0,
    total_gross NUMERIC(14, 2) DEFAULT 0,
    total_cpp_employee NUMERIC(12, 2) DEFAULT 0,
    total_cpp_employer NUMERIC(12, 2) DEFAULT 0,
    total_ei_employee NUMERIC(12, 2) DEFAULT 0,
    total_ei_employer NUMERIC(12, 2) DEFAULT 0,
    total_federal_tax NUMERIC(12, 2) DEFAULT 0,
    total_provincial_tax NUMERIC(12, 2) DEFAULT 0,
    total_net_pay NUMERIC(14, 2) DEFAULT 0,
    total_employer_cost NUMERIC(14, 2) DEFAULT 0,
    -- Beancount Integration
    beancount_transaction_ids TEXT[],
    -- Approval
    approved_by TEXT,
    approved_at TIMESTAMPTZ,
    notes TEXT,
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    -- Constraints
    CONSTRAINT chk_period_dates CHECK (period_end >= period_start),
    CONSTRAINT chk_pay_date CHECK (pay_date >= period_end)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_payroll_runs_user_id ON payroll_runs(user_id);
CREATE INDEX IF NOT EXISTS idx_payroll_runs_company_id ON payroll_runs(company_id);
CREATE INDEX IF NOT EXISTS idx_payroll_runs_status ON payroll_runs(status);
CREATE INDEX IF NOT EXISTS idx_payroll_runs_pay_date ON payroll_runs(pay_date DESC);
CREATE INDEX IF NOT EXISTS idx_payroll_runs_period ON payroll_runs(user_id, company_id, period_start, period_end);

-- RLS
ALTER TABLE payroll_runs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own payroll_runs" ON payroll_runs FOR SELECT
    USING (user_id = auth.uid()::text);
CREATE POLICY "Users can insert own payroll_runs" ON payroll_runs FOR INSERT
    WITH CHECK (user_id = auth.uid()::text);
CREATE POLICY "Users can update own payroll_runs" ON payroll_runs FOR UPDATE
    USING (user_id = auth.uid()::text);
CREATE POLICY "Users can delete own payroll_runs" ON payroll_runs FOR DELETE
    USING (user_id = auth.uid()::text);

-- Trigger
CREATE TRIGGER update_payroll_runs_updated_at
    BEFORE UPDATE ON payroll_runs FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- PAYROLL_RECORDS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS payroll_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payroll_run_id UUID NOT NULL REFERENCES payroll_runs(id) ON DELETE CASCADE,
    employee_id UUID NOT NULL REFERENCES employees(id),
    user_id TEXT NOT NULL,
    company_id UUID REFERENCES companies(id),
    -- Hours worked
    regular_hours_worked NUMERIC(6, 2),
    overtime_hours_worked NUMERIC(6, 2) DEFAULT 0,
    -- Earnings
    gross_regular NUMERIC(12, 2) NOT NULL,
    gross_overtime NUMERIC(10, 2) DEFAULT 0,
    holiday_pay NUMERIC(10, 2) DEFAULT 0,
    holiday_premium_pay NUMERIC(10, 2) DEFAULT 0,
    vacation_pay_paid NUMERIC(10, 2) DEFAULT 0,
    other_earnings NUMERIC(10, 2) DEFAULT 0,
    -- Sick leave
    sick_hours_taken NUMERIC(6, 2) DEFAULT 0,
    sick_pay_paid NUMERIC(10, 2) DEFAULT 0,
    -- Employee Deductions
    cpp_employee NUMERIC(10, 2) DEFAULT 0,
    cpp_additional NUMERIC(10, 2) DEFAULT 0,
    ei_employee NUMERIC(10, 2) DEFAULT 0,
    federal_tax NUMERIC(10, 2) DEFAULT 0,
    provincial_tax NUMERIC(10, 2) DEFAULT 0,
    rrsp NUMERIC(10, 2) DEFAULT 0,
    union_dues NUMERIC(10, 2) DEFAULT 0,
    garnishments NUMERIC(10, 2) DEFAULT 0,
    other_deductions NUMERIC(10, 2) DEFAULT 0,
    -- Employer Costs
    cpp_employer NUMERIC(10, 2) DEFAULT 0,
    ei_employer NUMERIC(10, 2) DEFAULT 0,
    -- Generated Columns
    total_gross NUMERIC(12, 2) GENERATED ALWAYS AS (
        gross_regular + gross_overtime + holiday_pay + holiday_premium_pay + vacation_pay_paid + other_earnings
    ) STORED,
    total_deductions NUMERIC(12, 2) GENERATED ALWAYS AS (
        cpp_employee + cpp_additional + ei_employee + federal_tax + provincial_tax + rrsp + union_dues + garnishments + other_deductions
    ) STORED,
    net_pay NUMERIC(12, 2) GENERATED ALWAYS AS (
        (gross_regular + gross_overtime + holiday_pay + holiday_premium_pay + vacation_pay_paid + other_earnings) -
        (cpp_employee + cpp_additional + ei_employee + federal_tax + provincial_tax + rrsp + union_dues + garnishments + other_deductions)
    ) STORED,
    total_employer_cost NUMERIC(12, 2) GENERATED ALWAYS AS (cpp_employer + ei_employer) STORED,
    -- YTD Snapshot
    ytd_gross NUMERIC(14, 2) DEFAULT 0,
    ytd_cpp NUMERIC(10, 2) DEFAULT 0,
    ytd_ei NUMERIC(10, 2) DEFAULT 0,
    ytd_federal_tax NUMERIC(12, 2) DEFAULT 0,
    ytd_provincial_tax NUMERIC(12, 2) DEFAULT 0,
    ytd_net_pay NUMERIC(14, 2) DEFAULT 0,
    -- Vacation
    vacation_accrued NUMERIC(10, 2) DEFAULT 0,
    vacation_hours_taken NUMERIC(6, 2) DEFAULT 0,
    -- Employee Snapshots
    employee_name_snapshot TEXT,
    province_snapshot TEXT,
    annual_salary_snapshot NUMERIC(12, 2),
    hourly_rate_snapshot NUMERIC(12, 2),
    pay_group_id_snapshot UUID,
    pay_group_name_snapshot TEXT,
    -- Input Data & Calculation
    input_data JSONB DEFAULT NULL,
    is_modified BOOLEAN DEFAULT FALSE,
    calculation_details JSONB,
    -- Paystub
    paystub_storage_key TEXT,
    paystub_generated_at TIMESTAMPTZ,
    paystub_sent_to TEXT,
    paystub_sent_at TIMESTAMPTZ,
    -- Timestamp
    created_at TIMESTAMPTZ DEFAULT NOW(),
    -- Constraints
    CONSTRAINT unique_employee_per_run UNIQUE (payroll_run_id, employee_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_payroll_records_run ON payroll_records(payroll_run_id);
CREATE INDEX IF NOT EXISTS idx_payroll_records_employee ON payroll_records(employee_id);
CREATE INDEX IF NOT EXISTS idx_payroll_records_user_id ON payroll_records(user_id);
CREATE INDEX IF NOT EXISTS idx_payroll_records_company_id ON payroll_records(company_id);
CREATE INDEX IF NOT EXISTS idx_payroll_records_paystub ON payroll_records(paystub_storage_key) WHERE paystub_storage_key IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_payroll_records_hourly ON payroll_records(employee_id) WHERE regular_hours_worked IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_payroll_records_pay_group_snapshot ON payroll_records(pay_group_id_snapshot) WHERE pay_group_id_snapshot IS NOT NULL;

-- RLS
ALTER TABLE payroll_records ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own payroll_records" ON payroll_records FOR SELECT
    USING (user_id = auth.uid()::text);
CREATE POLICY "Users can insert own payroll_records" ON payroll_records FOR INSERT
    WITH CHECK (user_id = auth.uid()::text);
CREATE POLICY "Users can update own payroll_records" ON payroll_records FOR UPDATE
    USING (user_id = auth.uid()::text);
CREATE POLICY "Users can delete own payroll_records" ON payroll_records FOR DELETE
    USING (user_id = auth.uid()::text);

-- =============================================================================
-- VIEWS
-- =============================================================================

-- Employee details view
CREATE VIEW public.v_employee_details WITH (security_invoker = on) AS
SELECT
    e.id, e.user_id, e.first_name, e.last_name, e.sin_encrypted, e.email,
    e.province_of_employment, e.pay_frequency, e.employment_type,
    e.annual_salary, e.hourly_rate,
    e.federal_additional_claims, e.provincial_additional_claims,
    e.is_cpp_exempt, e.is_ei_exempt, e.cpp2_exempt,
    e.hire_date, e.termination_date,
    e.vacation_config, e.vacation_balance,
    e.created_at, e.updated_at,
    e.company_id, e.pay_group_id,
    e.address_street, e.address_city, e.address_postal_code, e.occupation,
    e.initial_ytd_cpp, e.initial_ytd_cpp2, e.initial_ytd_ei, e.initial_ytd_year,
    c.company_name, c.province AS company_province,
    c.address_street AS company_address_street,
    c.address_city AS company_address_city,
    c.address_postal_code AS company_address_postal_code,
    pg.name AS pay_group_name,
    pg.next_period_end AS pay_group_next_period_end
FROM employees e
LEFT JOIN companies c ON e.company_id = c.id
LEFT JOIN pay_groups pg ON e.pay_group_id = pg.id;

COMMENT ON VIEW public.v_employee_details IS
    'Employee details view with company and pay group info. Uses security_invoker to enforce RLS.';

-- Pay group summary view
CREATE VIEW public.v_pay_group_summary WITH (security_invoker = on) AS
SELECT
    pg.id, pg.company_id, pg.name, pg.description,
    pg.pay_frequency, pg.employment_type, pg.next_period_end, pg.period_start_day,
    pg.leave_enabled, pg.tax_calculation_method,
    pg.overtime_policy, pg.wcb_config, pg.group_benefits,
    pg.earnings_config, pg.taxable_benefits_config, pg.deductions_config,
    pg.created_at, pg.updated_at,
    c.company_name,
    COUNT(e.id) AS employee_count
FROM pay_groups pg
JOIN companies c ON pg.company_id = c.id
LEFT JOIN employees e ON e.pay_group_id = pg.id AND e.termination_date IS NULL
GROUP BY pg.id, c.company_name;

-- Public company portal info view
CREATE OR REPLACE VIEW public_company_portal_info AS
SELECT id, company_name, slug, logo_url
FROM companies WHERE slug IS NOT NULL;

GRANT SELECT ON public_company_portal_info TO anon;
GRANT SELECT ON public_company_portal_info TO authenticated;

COMMENT ON VIEW public_company_portal_info IS
    'Public-facing view for employee portal login. Only exposes id, company_name, slug, logo_url.';

-- =============================================================================
-- STORAGE BUCKET FOR ASSETS
-- =============================================================================

INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'assets', 'assets', true, 2097152,
    ARRAY['image/png', 'image/jpeg', 'image/gif', 'image/webp', 'image/svg+xml']
)
ON CONFLICT (id) DO NOTHING;

-- Storage policies
CREATE POLICY "Authenticated users can upload company logos" ON storage.objects
    FOR INSERT TO authenticated
    WITH CHECK (bucket_id = 'assets' AND (storage.foldername(name))[1] = 'company-logos');

CREATE POLICY "Authenticated users can update company logos" ON storage.objects
    FOR UPDATE TO authenticated
    USING (bucket_id = 'assets' AND (storage.foldername(name))[1] = 'company-logos');

CREATE POLICY "Authenticated users can delete company logos" ON storage.objects
    FOR DELETE TO authenticated
    USING (bucket_id = 'assets' AND (storage.foldername(name))[1] = 'company-logos');

CREATE POLICY "Public read access to assets" ON storage.objects
    FOR SELECT TO public
    USING (bucket_id = 'assets');
