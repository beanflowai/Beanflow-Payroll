-- =============================================================================
-- MIGRATION 008: FIX FUNCTION SEARCH_PATH
-- =============================================================================
-- Description: Add SET search_path = '' to all functions for security
-- =============================================================================

-- 1. update_updated_at_column (core_schema)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SET search_path = '';

-- 2. generate_company_slug (core_schema)
CREATE OR REPLACE FUNCTION generate_company_slug(p_company_name TEXT, p_company_id UUID)
RETURNS TEXT AS $$
DECLARE
    base_slug TEXT;
    final_slug TEXT;
    counter INTEGER := 0;
BEGIN
    base_slug := lower(regexp_replace(trim(p_company_name), '[^a-zA-Z0-9]+', '-', 'g'));
    base_slug := regexp_replace(base_slug, '^-+|-+$', '', 'g');
    IF length(base_slug) < 2 THEN
        base_slug := 'company';
    END IF;
    final_slug := base_slug;
    WHILE EXISTS (SELECT 1 FROM public.companies WHERE slug = final_slug AND id != p_company_id) LOOP
        counter := counter + 1;
        final_slug := base_slug || '-' || counter;
    END LOOP;
    RETURN final_slug;
END;
$$ LANGUAGE plpgsql SET search_path = '';

-- 3. set_company_slug (core_schema)
CREATE OR REPLACE FUNCTION set_company_slug()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.slug IS NULL OR NEW.slug = '' THEN
        NEW.slug := public.generate_company_slug(NEW.company_name, NEW.id);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SET search_path = '';

-- 4. update_employee_compensation (compensation_history)
CREATE OR REPLACE FUNCTION update_employee_compensation(
    p_employee_id UUID,
    p_compensation_type TEXT,
    p_annual_salary NUMERIC,
    p_hourly_rate NUMERIC,
    p_effective_date DATE,
    p_change_reason TEXT DEFAULT NULL
)
RETURNS SETOF public.employee_compensation_history
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    v_current_effective_date DATE;
    v_employee_user_id TEXT;
BEGIN
    -- Security: Validate employee ownership
    SELECT user_id INTO v_employee_user_id FROM public.employees WHERE id = p_employee_id;

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
    FROM public.employee_compensation_history
    WHERE employee_id = p_employee_id AND end_date IS NULL
    FOR UPDATE;

    IF v_current_effective_date IS NOT NULL AND p_effective_date <= v_current_effective_date THEN
        RAISE EXCEPTION 'New effective date (%) must be after current effective date (%)',
            p_effective_date, v_current_effective_date;
    END IF;

    -- Close current active record
    UPDATE public.employee_compensation_history
    SET end_date = p_effective_date - INTERVAL '1 day'
    WHERE employee_id = p_employee_id AND end_date IS NULL;

    -- Insert new record
    RETURN QUERY
    INSERT INTO public.employee_compensation_history (
        employee_id, compensation_type, annual_salary, hourly_rate, effective_date, change_reason
    ) VALUES (
        p_employee_id, p_compensation_type,
        CASE WHEN p_compensation_type = 'salary' THEN p_annual_salary ELSE NULL END,
        CASE WHEN p_compensation_type = 'hourly' THEN p_hourly_rate ELSE NULL END,
        p_effective_date, p_change_reason
    )
    RETURNING *;

    -- Sync to employees table
    UPDATE public.employees SET
        annual_salary = CASE WHEN p_compensation_type = 'salary' THEN p_annual_salary ELSE NULL END,
        hourly_rate = CASE WHEN p_compensation_type = 'hourly' THEN p_hourly_rate ELSE NULL END
    WHERE id = p_employee_id;
END;
$$;

-- 5. update_employee_tax_claims_updated_at (tax_remittance_t4)
CREATE OR REPLACE FUNCTION update_employee_tax_claims_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SET search_path = '';

-- 6. update_t4_updated_at (tax_remittance_t4)
CREATE OR REPLACE FUNCTION update_t4_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SET search_path = '';

-- 7. prevent_is_admin_change (support_system)
CREATE OR REPLACE FUNCTION prevent_is_admin_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.is_admin IS DISTINCT FROM NEW.is_admin THEN
        RAISE EXCEPTION 'Cannot modify is_admin field. Admin status can only be changed via direct database access.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SET search_path = '';

-- 8. is_admin (support_system)
CREATE OR REPLACE FUNCTION is_admin()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (SELECT 1 FROM public.user_profiles WHERE id = auth.uid() AND is_admin = TRUE);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER STABLE SET search_path = '';

-- 9. handle_new_user (support_system)
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    BEGIN
        INSERT INTO public.user_profiles (id, email, full_name, is_admin)
        VALUES (
            NEW.id, NEW.email,
            COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.raw_user_meta_data->>'name', ''),
            FALSE
        )
        ON CONFLICT (id) DO NOTHING;
    EXCEPTION WHEN OTHERS THEN
        RAISE WARNING 'handle_new_user failed for %: %', NEW.email, SQLERRM;
    END;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = '';

-- 10. prevent_ticket_user_id_change (support_system)
CREATE OR REPLACE FUNCTION prevent_ticket_user_id_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.user_id IS DISTINCT FROM NEW.user_id THEN
        RAISE EXCEPTION 'Cannot modify ticket owner. Ticket ownership cannot be transferred.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SET search_path = '';

-- 11. update_support_ticket_updated_at (support_system)
CREATE OR REPLACE FUNCTION update_support_ticket_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SET search_path = '';

-- 12. update_ticket_on_reply (support_system)
CREATE OR REPLACE FUNCTION update_ticket_on_reply()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE public.support_tickets SET updated_at = NOW() WHERE id = NEW.ticket_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SET search_path = '';
