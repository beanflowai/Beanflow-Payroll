-- Migration: Add RPC function for atomic compensation update
-- Purpose: Ensure transactional consistency when updating employee compensation
-- This function performs all three operations in a single database transaction:
-- 1. Close current active record (set end_date)
-- 2. Insert new compensation record
-- 3. Sync current values to employees table

CREATE OR REPLACE FUNCTION update_employee_compensation(
    p_employee_id UUID,
    p_compensation_type TEXT,
    p_annual_salary NUMERIC,
    p_hourly_rate NUMERIC,
    p_effective_date DATE,
    p_change_reason TEXT DEFAULT NULL
)
RETURNS SETOF employee_compensation_history
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_current_effective_date DATE;
    v_employee_user_id TEXT;
BEGIN
    -- =========================================================================
    -- Security: Validate employee ownership
    -- Ensure the calling user owns the employee (via auth.uid())
    -- This prevents unauthorized access even with SECURITY DEFINER
    -- =========================================================================
    SELECT user_id INTO v_employee_user_id
    FROM employees
    WHERE id = p_employee_id;

    IF v_employee_user_id IS NULL THEN
        RAISE EXCEPTION 'Employee not found: %', p_employee_id;
    END IF;

    -- Check if current user owns this employee
    -- auth.uid() returns the authenticated user's ID from JWT
    IF v_employee_user_id != auth.uid()::text THEN
        RAISE EXCEPTION 'Access denied: You do not have permission to modify this employee''s compensation';
    END IF;

    -- Validate compensation type
    IF p_compensation_type NOT IN ('salary', 'hourly') THEN
        RAISE EXCEPTION 'Invalid compensation type: %. Must be "salary" or "hourly"', p_compensation_type;
    END IF;

    -- Validate compensation amount based on type
    IF p_compensation_type = 'salary' AND (p_annual_salary IS NULL OR p_annual_salary <= 0) THEN
        RAISE EXCEPTION 'Annual salary is required and must be positive for salary compensation type';
    END IF;

    IF p_compensation_type = 'hourly' AND (p_hourly_rate IS NULL OR p_hourly_rate <= 0) THEN
        RAISE EXCEPTION 'Hourly rate is required and must be positive for hourly compensation type';
    END IF;

    -- Get current active record's effective date for validation
    SELECT effective_date INTO v_current_effective_date
    FROM employee_compensation_history
    WHERE employee_id = p_employee_id AND end_date IS NULL
    FOR UPDATE;  -- Lock the row to prevent concurrent updates

    -- Validate: new effective date must be after current effective date
    IF v_current_effective_date IS NOT NULL AND p_effective_date <= v_current_effective_date THEN
        RAISE EXCEPTION 'New effective date (%) must be after current effective date (%)',
            p_effective_date, v_current_effective_date;
    END IF;

    -- Step 1: Close current active record (set end_date to day before new effective date)
    UPDATE employee_compensation_history
    SET end_date = p_effective_date - INTERVAL '1 day'
    WHERE employee_id = p_employee_id AND end_date IS NULL;

    -- Step 2: Insert new compensation record and return it
    RETURN QUERY
    INSERT INTO employee_compensation_history (
        employee_id,
        compensation_type,
        annual_salary,
        hourly_rate,
        effective_date,
        change_reason
    ) VALUES (
        p_employee_id,
        p_compensation_type,
        CASE WHEN p_compensation_type = 'salary' THEN p_annual_salary ELSE NULL END,
        CASE WHEN p_compensation_type = 'hourly' THEN p_hourly_rate ELSE NULL END,
        p_effective_date,
        p_change_reason
    )
    RETURNING *;

    -- Step 3: Sync current compensation to employees table
    UPDATE employees
    SET
        annual_salary = CASE WHEN p_compensation_type = 'salary' THEN p_annual_salary ELSE NULL END,
        hourly_rate = CASE WHEN p_compensation_type = 'hourly' THEN p_hourly_rate ELSE NULL END
    WHERE id = p_employee_id;

END;
$$;

-- Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION update_employee_compensation TO authenticated;

-- Add comment for documentation
COMMENT ON FUNCTION update_employee_compensation IS
'Atomically updates employee compensation with history tracking.
Validates that new effective date is after current record.
Closes current active record, creates new record, and syncs to employees table.
All operations are performed in a single transaction.';
