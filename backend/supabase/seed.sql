-- =============================================================================
-- SEED DATA: Sample Company & Employees for Development/Testing
-- =============================================================================
-- Usage:
--   1. Login to Supabase Dashboard -> SQL Editor
--   2. Run: SELECT auth.uid();  (to get your user ID)
--   3. Replace YOUR_USER_ID_HERE below with your actual UUID
--   4. Run this entire script
-- =============================================================================

-- Step 1: Set your user ID here (replace with your auth.uid())
DO $$
DECLARE
    my_user_id TEXT := '007b69c8-9727-403d-b4f2-c2e5d96c086f';  -- <-- REPLACE THIS
    company_uuid UUID;
BEGIN

-- Step 2: Insert sample company
INSERT INTO companies (
    user_id,
    company_name, business_number, payroll_account_number,
    province, remitter_type,
    auto_calculate_deductions, send_paystub_emails
) VALUES (
    my_user_id,
    'Acme Corporation', '123456789', '123456789RP0001',
    'ON', 'regular',
    TRUE, FALSE
) RETURNING id INTO company_uuid;

RAISE NOTICE 'Inserted company with ID: %', company_uuid;

-- Step 3: Insert sample employees
-- Note: federal_additional_claims and provincial_additional_claims store amounts BEYOND BPA
-- BPA is fetched dynamically from tax tables based on pay_date
INSERT INTO employees (
    user_id, company_id,
    first_name, last_name, sin_encrypted, email,
    province_of_employment, pay_frequency, employment_type,
    annual_salary, hourly_rate,
    federal_additional_claims, provincial_additional_claims,
    is_cpp_exempt, is_ei_exempt, cpp2_exempt,
    hire_date, termination_date,
    vacation_config, vacation_balance
) VALUES
-- Sarah Johnson - ON, Salaried, Active, no additional claims
(
    my_user_id, company_uuid,
    'Sarah', 'Johnson', 'enc_123456789', 'sarah.johnson@example.com',
    'ON', 'bi_weekly', 'full_time',
    85000, NULL,
    0, 0,
    FALSE, FALSE, FALSE,
    '2024-03-15', NULL,
    '{"payout_method": "accrual", "vacation_rate": "0.04"}'::jsonb, 1234.56
),
-- Michael Chen - BC, Hourly, Active, no additional claims
(
    my_user_id, company_uuid,
    'Michael', 'Chen', 'enc_987654321', 'michael.chen@example.com',
    'BC', 'bi_weekly', 'full_time',
    NULL, 45,
    0, 0,
    FALSE, FALSE, FALSE,
    '2023-08-01', NULL,
    '{"payout_method": "pay_as_you_go", "vacation_rate": "0.04"}'::jsonb, 0
),
-- Emily Davis - ON, Salaried, Part-time, Active, no additional claims
(
    my_user_id, company_uuid,
    'Emily', 'Davis', 'enc_456789123', 'emily.davis@example.com',
    'ON', 'semi_monthly', 'part_time',
    52000, NULL,
    0, 0,
    FALSE, FALSE, FALSE,
    '2024-01-10', NULL,
    '{"payout_method": "accrual", "vacation_rate": "0.04"}'::jsonb, 520
),
-- James Wilson - AB, Salaried, CPP/EI Exempt, no additional claims
(
    my_user_id, company_uuid,
    'James', 'Wilson', 'enc_321654987', 'james.wilson@example.com',
    'AB', 'monthly', 'full_time',
    96000, NULL,
    0, 0,
    TRUE, TRUE, TRUE,
    '2024-06-01', NULL,
    '{"payout_method": "lump_sum", "vacation_rate": "0.06"}'::jsonb, 2880
),
-- Lisa Thompson - ON, Salaried, Terminated, no additional claims
(
    my_user_id, company_uuid,
    'Lisa', 'Thompson', 'enc_789123456', 'lisa.thompson@example.com',
    'ON', 'bi_weekly', 'full_time',
    72000, NULL,
    0, 0,
    FALSE, FALSE, FALSE,
    '2022-05-15', '2024-11-30',
    '{"payout_method": "accrual", "vacation_rate": "0.06"}'::jsonb, 0
);

RAISE NOTICE 'Inserted 5 sample employees for user: %', my_user_id;

END $$;

-- Verify insertions
SELECT 'Company' as type, id::text, company_name as name FROM companies
UNION ALL
SELECT 'Employee', id::text, first_name || ' ' || last_name FROM employees
ORDER BY type, name;
