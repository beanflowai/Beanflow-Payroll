-- =============================================================================
-- CONSOLIDATED MIGRATION 002: COMPENSATION HISTORY
-- =============================================================================
-- Description: Employee compensation history tracking with atomic update RPC
-- =============================================================================

-- Create compensation history table
CREATE TABLE employee_compensation_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    compensation_type TEXT NOT NULL CHECK (compensation_type IN ('salary', 'hourly')),
    annual_salary NUMERIC(12, 2),
    hourly_rate NUMERIC(10, 2),
    effective_date DATE NOT NULL,
    end_date DATE,
    change_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT valid_compensation CHECK (
        (compensation_type = 'salary' AND annual_salary IS NOT NULL) OR
        (compensation_type = 'hourly' AND hourly_rate IS NOT NULL)
    ),
    CONSTRAINT valid_date_range CHECK (end_date IS NULL OR end_date >= effective_date)
);

-- Indexes
CREATE INDEX idx_comp_history_employee ON employee_compensation_history(employee_id);
CREATE INDEX idx_comp_history_effective ON employee_compensation_history(employee_id, effective_date DESC);

-- Unique partial index: only one active record per employee
CREATE UNIQUE INDEX idx_compensation_active_per_employee
    ON employee_compensation_history(employee_id) WHERE end_date IS NULL;

-- RLS
ALTER TABLE employee_compensation_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage their employees compensation history"
    ON employee_compensation_history FOR ALL
    USING (employee_id IN (SELECT id FROM employees WHERE user_id = auth.uid()::text));

-- =============================================================================
-- RPC: Atomic compensation update
-- =============================================================================

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
    -- Security: Validate employee ownership
    SELECT user_id INTO v_employee_user_id FROM employees WHERE id = p_employee_id;

    IF v_employee_user_id IS NULL THEN
        RAISE EXCEPTION 'Employee not found: %', p_employee_id;
    END IF;

    IF v_employee_user_id != auth.uid()::text THEN
        RAISE EXCEPTION 'Access denied: You do not have permission to modify this employee''s compensation';
    END IF;

    -- Validate compensation type
    IF p_compensation_type NOT IN ('salary', 'hourly') THEN
        RAISE EXCEPTION 'Invalid compensation type: %. Must be "salary" or "hourly"', p_compensation_type;
    END IF;

    IF p_compensation_type = 'salary' AND (p_annual_salary IS NULL OR p_annual_salary <= 0) THEN
        RAISE EXCEPTION 'Annual salary is required and must be positive for salary compensation type';
    END IF;

    IF p_compensation_type = 'hourly' AND (p_hourly_rate IS NULL OR p_hourly_rate <= 0) THEN
        RAISE EXCEPTION 'Hourly rate is required and must be positive for hourly compensation type';
    END IF;

    -- Get current active record's effective date
    SELECT effective_date INTO v_current_effective_date
    FROM employee_compensation_history
    WHERE employee_id = p_employee_id AND end_date IS NULL
    FOR UPDATE;

    IF v_current_effective_date IS NOT NULL AND p_effective_date <= v_current_effective_date THEN
        RAISE EXCEPTION 'New effective date (%) must be after current effective date (%)',
            p_effective_date, v_current_effective_date;
    END IF;

    -- Close current active record
    UPDATE employee_compensation_history
    SET end_date = p_effective_date - INTERVAL '1 day'
    WHERE employee_id = p_employee_id AND end_date IS NULL;

    -- Insert new record
    RETURN QUERY
    INSERT INTO employee_compensation_history (
        employee_id, compensation_type, annual_salary, hourly_rate, effective_date, change_reason
    ) VALUES (
        p_employee_id, p_compensation_type,
        CASE WHEN p_compensation_type = 'salary' THEN p_annual_salary ELSE NULL END,
        CASE WHEN p_compensation_type = 'hourly' THEN p_hourly_rate ELSE NULL END,
        p_effective_date, p_change_reason
    )
    RETURNING *;

    -- Sync to employees table
    UPDATE employees SET
        annual_salary = CASE WHEN p_compensation_type = 'salary' THEN p_annual_salary ELSE NULL END,
        hourly_rate = CASE WHEN p_compensation_type = 'hourly' THEN p_hourly_rate ELSE NULL END
    WHERE id = p_employee_id;
END;
$$;

GRANT EXECUTE ON FUNCTION update_employee_compensation TO authenticated;

COMMENT ON FUNCTION update_employee_compensation IS
    'Atomically updates employee compensation with history tracking.';
