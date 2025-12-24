-- Add structured configurations to pay_groups table
-- Replaces custom_deductions with three new JSONB columns:
-- - earnings_config
-- - taxable_benefits_config
-- - deductions_config

-- Add new columns
ALTER TABLE pay_groups
ADD COLUMN IF NOT EXISTS earnings_config JSONB DEFAULT '{
    "enabled": false,
    "bonus": {"enabled": false, "discretionaryEnabled": false, "nonDiscretionaryEnabled": false, "defaultTaxable": true},
    "commission": {"enabled": false, "calculationType": "fixed", "defaultAmount": 0, "requiresSalesInput": false, "includeInOvertimeBase": false},
    "expenseReimbursement": {"enabled": false, "requireReceipts": true, "categories": []},
    "allowances": [],
    "customEarnings": []
}'::JSONB;

ALTER TABLE pay_groups
ADD COLUMN IF NOT EXISTS taxable_benefits_config JSONB DEFAULT '{
    "enabled": false,
    "automobile": {"enabled": false, "vehicleCost": 0, "isLeased": false, "daysAvailablePerMonth": 30, "personalKilometers": 0, "useOperatingExpenseBenefit": false, "operatingExpenseRate": 0.34, "includesGstHst": true, "gstHstRate": 0.13},
    "housing": {"enabled": false, "monthlyValue": 0, "includesUtilities": false},
    "travelAssistance": {"enabled": false, "isPrescribedZone": false, "isIntermediateZone": false, "annualValue": 0, "tripsPerYear": 2},
    "boardLodging": {"enabled": false, "valueType": "daily", "value": 0, "isSubsidized": false},
    "groupLifeInsurance": {"enabled": false, "coverageAmount": 0, "employerPremium": 0, "employeePremium": 0, "useCraRates": true},
    "customBenefits": []
}'::JSONB;

ALTER TABLE pay_groups
ADD COLUMN IF NOT EXISTS deductions_config JSONB DEFAULT '{
    "enabled": true,
    "rrsp": {"enabled": false, "calculationType": "fixed", "amount": 0, "employerMatchEnabled": false, "respectAnnualLimit": true, "isDefaultEnabled": false},
    "unionDues": {"enabled": false, "calculationType": "fixed", "amount": 0, "isDefaultEnabled": false},
    "garnishments": {"enabled": true, "allowGarnishments": true},
    "charitableDonations": {"enabled": false, "approvedCharities": [], "isDefaultEnabled": false},
    "customDeductions": []
}'::JSONB;

-- Migrate data from custom_deductions to deductions_config.customDeductions
UPDATE pay_groups
SET deductions_config = jsonb_set(
    deductions_config,
    '{customDeductions}',
    COALESCE(custom_deductions, '[]'::jsonb)
)
WHERE custom_deductions IS NOT NULL AND custom_deductions != '[]'::jsonb;

-- Drop view first (it depends on custom_deductions column)
DROP VIEW IF EXISTS public.v_pay_group_summary;

-- Drop old column
ALTER TABLE pay_groups DROP COLUMN IF EXISTS custom_deductions;

CREATE VIEW public.v_pay_group_summary WITH (security_invoker = on) AS
SELECT
    pg.id,
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
    pg.earnings_config,
    pg.taxable_benefits_config,
    pg.deductions_config,
    pg.created_at,
    pg.updated_at,
    c.company_name,
    COUNT(e.id) AS employee_count
FROM
    pay_groups pg
    JOIN companies c ON pg.company_id = c.id
    LEFT JOIN employees e ON e.pay_group_id = pg.id AND e.termination_date IS NULL
GROUP BY
    pg.id,
    c.company_name;
