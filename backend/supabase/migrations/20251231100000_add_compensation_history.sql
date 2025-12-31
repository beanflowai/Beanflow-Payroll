-- Migration: Add employee compensation history table
-- Purpose: Track salary/hourly rate changes over time instead of overwriting

-- 1. Create compensation history table
CREATE TABLE employee_compensation_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,

    -- Compensation details
    compensation_type TEXT NOT NULL CHECK (compensation_type IN ('salary', 'hourly')),
    annual_salary NUMERIC(12, 2),
    hourly_rate NUMERIC(10, 2),

    -- Effective period
    effective_date DATE NOT NULL,
    end_date DATE,  -- NULL = currently active

    -- Audit
    change_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),

    -- Constraints
    CONSTRAINT valid_compensation CHECK (
        (compensation_type = 'salary' AND annual_salary IS NOT NULL) OR
        (compensation_type = 'hourly' AND hourly_rate IS NOT NULL)
    ),
    CONSTRAINT valid_date_range CHECK (end_date IS NULL OR end_date >= effective_date)
);

-- 2. Create indexes for efficient queries
CREATE INDEX idx_comp_history_employee ON employee_compensation_history(employee_id);
CREATE INDEX idx_comp_history_effective ON employee_compensation_history(employee_id, effective_date DESC);

-- 3. Enable RLS
ALTER TABLE employee_compensation_history ENABLE ROW LEVEL SECURITY;

-- 4. RLS Policy - users can only access their own employees' compensation history
CREATE POLICY "Users can manage their employees compensation history"
ON employee_compensation_history
FOR ALL
USING (
    employee_id IN (SELECT id FROM employees WHERE user_id = auth.uid()::text)
);

-- 5. Migrate existing compensation data from employees table
INSERT INTO employee_compensation_history (
    employee_id,
    compensation_type,
    annual_salary,
    hourly_rate,
    effective_date,
    change_reason,
    created_at
)
SELECT
    id,
    CASE WHEN annual_salary IS NOT NULL THEN 'salary' ELSE 'hourly' END,
    annual_salary,
    hourly_rate,
    COALESCE(hire_date, created_at::date),
    'Initial migration from employees table',
    created_at
FROM employees
WHERE annual_salary IS NOT NULL OR hourly_rate IS NOT NULL;
