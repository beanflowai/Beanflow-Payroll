-- =============================================================================
-- CONSOLIDATED MIGRATION 003: STATUTORY DATA
-- =============================================================================
-- Description: Statutory holidays + Sick leave balance tables
-- Note: sick_leave_configs table NOT created (loaded from JSON files)
-- =============================================================================

-- =============================================================================
-- STATUTORY HOLIDAYS TABLE
-- =============================================================================

CREATE TABLE statutory_holidays (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    province TEXT NOT NULL,
    holiday_date DATE NOT NULL,
    name TEXT NOT NULL,
    name_fr TEXT,
    year INTEGER NOT NULL,
    is_statutory BOOLEAN DEFAULT TRUE,
    calculation_rule TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(province, holiday_date)
);

-- Indexes
CREATE INDEX idx_holidays_province_year ON statutory_holidays(province, year);
CREATE INDEX idx_holidays_date_range ON statutory_holidays(holiday_date);
CREATE INDEX idx_holidays_province_date ON statutory_holidays(province, holiday_date, is_statutory);

-- RLS
ALTER TABLE statutory_holidays ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Holidays are readable by everyone" ON statutory_holidays
    FOR SELECT USING (true);

CREATE POLICY "Only service role can modify holidays" ON statutory_holidays
    FOR ALL USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

COMMENT ON TABLE statutory_holidays IS 'Canadian statutory holidays by province, excluding Quebec';

-- =============================================================================
-- 2025 STATUTORY HOLIDAYS DATA
-- =============================================================================

-- New Year's Day - Jan 1, 2025
INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory) VALUES
    ('AB', '2025-01-01', 'New Year''s Day', 2025, TRUE),
    ('BC', '2025-01-01', 'New Year''s Day', 2025, TRUE),
    ('MB', '2025-01-01', 'New Year''s Day', 2025, TRUE),
    ('NB', '2025-01-01', 'New Year''s Day', 2025, TRUE),
    ('NL', '2025-01-01', 'New Year''s Day', 2025, TRUE),
    ('NS', '2025-01-01', 'New Year''s Day', 2025, TRUE),
    ('NT', '2025-01-01', 'New Year''s Day', 2025, TRUE),
    ('NU', '2025-01-01', 'New Year''s Day', 2025, TRUE),
    ('ON', '2025-01-01', 'New Year''s Day', 2025, TRUE),
    ('PE', '2025-01-01', 'New Year''s Day', 2025, TRUE),
    ('SK', '2025-01-01', 'New Year''s Day', 2025, TRUE),
    ('YT', '2025-01-01', 'New Year''s Day', 2025, TRUE);

-- Family Day / Louis Riel Day / Islander Day / Heritage Day - Feb 17, 2025
INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory, calculation_rule) VALUES
    ('AB', '2025-02-17', 'Family Day', 2025, TRUE, 'third_monday_february'),
    ('BC', '2025-02-17', 'Family Day', 2025, TRUE, 'third_monday_february'),
    ('NB', '2025-02-17', 'Family Day', 2025, TRUE, 'third_monday_february'),
    ('ON', '2025-02-17', 'Family Day', 2025, TRUE, 'third_monday_february'),
    ('SK', '2025-02-17', 'Family Day', 2025, TRUE, 'third_monday_february'),
    ('MB', '2025-02-17', 'Louis Riel Day', 2025, TRUE, 'third_monday_february'),
    ('PE', '2025-02-17', 'Islander Day', 2025, TRUE, 'third_monday_february'),
    ('NS', '2025-02-17', 'Heritage Day', 2025, TRUE, 'third_monday_february');

-- Good Friday - Apr 18, 2025
INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory, calculation_rule) VALUES
    ('AB', '2025-04-18', 'Good Friday', 2025, TRUE, 'easter_minus_2'),
    ('BC', '2025-04-18', 'Good Friday', 2025, TRUE, 'easter_minus_2'),
    ('MB', '2025-04-18', 'Good Friday', 2025, TRUE, 'easter_minus_2'),
    ('NB', '2025-04-18', 'Good Friday', 2025, TRUE, 'easter_minus_2'),
    ('NL', '2025-04-18', 'Good Friday', 2025, TRUE, 'easter_minus_2'),
    ('NS', '2025-04-18', 'Good Friday', 2025, TRUE, 'easter_minus_2'),
    ('NT', '2025-04-18', 'Good Friday', 2025, TRUE, 'easter_minus_2'),
    ('NU', '2025-04-18', 'Good Friday', 2025, TRUE, 'easter_minus_2'),
    ('ON', '2025-04-18', 'Good Friday', 2025, TRUE, 'easter_minus_2'),
    ('PE', '2025-04-18', 'Good Friday', 2025, TRUE, 'easter_minus_2'),
    ('SK', '2025-04-18', 'Good Friday', 2025, TRUE, 'easter_minus_2'),
    ('YT', '2025-04-18', 'Good Friday', 2025, TRUE, 'easter_minus_2');

-- Easter Monday - Apr 21, 2025
INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory, calculation_rule) VALUES
    ('NU', '2025-04-21', 'Easter Monday', 2025, TRUE, 'easter_plus_1'),
    ('AB', '2025-04-21', 'Easter Monday', 2025, FALSE, 'easter_plus_1');

-- Victoria Day - May 19, 2025
INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory, calculation_rule) VALUES
    ('AB', '2025-05-19', 'Victoria Day', 2025, TRUE, 'last_monday_before_may_25'),
    ('BC', '2025-05-19', 'Victoria Day', 2025, TRUE, 'last_monday_before_may_25'),
    ('MB', '2025-05-19', 'Victoria Day', 2025, TRUE, 'last_monday_before_may_25'),
    ('NB', '2025-05-19', 'Victoria Day', 2025, TRUE, 'last_monday_before_may_25'),
    ('NT', '2025-05-19', 'Victoria Day', 2025, TRUE, 'last_monday_before_may_25'),
    ('NU', '2025-05-19', 'Victoria Day', 2025, TRUE, 'last_monday_before_may_25'),
    ('ON', '2025-05-19', 'Victoria Day', 2025, TRUE, 'last_monday_before_may_25'),
    ('PE', '2025-05-19', 'Victoria Day', 2025, TRUE, 'last_monday_before_may_25'),
    ('SK', '2025-05-19', 'Victoria Day', 2025, TRUE, 'last_monday_before_may_25'),
    ('YT', '2025-05-19', 'Victoria Day', 2025, TRUE, 'last_monday_before_may_25');

-- Canada Day - Jul 1, 2025
INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory) VALUES
    ('AB', '2025-07-01', 'Canada Day', 2025, TRUE),
    ('BC', '2025-07-01', 'Canada Day', 2025, TRUE),
    ('MB', '2025-07-01', 'Canada Day', 2025, TRUE),
    ('NB', '2025-07-01', 'Canada Day', 2025, TRUE),
    ('NL', '2025-07-01', 'Memorial Day', 2025, TRUE),
    ('NS', '2025-07-01', 'Canada Day', 2025, TRUE),
    ('NT', '2025-07-01', 'Canada Day', 2025, TRUE),
    ('NU', '2025-07-01', 'Canada Day', 2025, TRUE),
    ('ON', '2025-07-01', 'Canada Day', 2025, TRUE),
    ('PE', '2025-07-01', 'Canada Day', 2025, TRUE),
    ('SK', '2025-07-01', 'Canada Day', 2025, TRUE),
    ('YT', '2025-07-01', 'Canada Day', 2025, TRUE);

-- Nunavut Day - Jul 9, 2025
INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory) VALUES
    ('NU', '2025-07-09', 'Nunavut Day', 2025, TRUE);

-- Civic Holiday / BC Day / Saskatchewan Day - Aug 4, 2025
INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory, calculation_rule) VALUES
    ('BC', '2025-08-04', 'British Columbia Day', 2025, TRUE, 'first_monday_august'),
    ('NT', '2025-08-04', 'Civic Holiday', 2025, TRUE, 'first_monday_august'),
    ('NU', '2025-08-04', 'Civic Holiday', 2025, TRUE, 'first_monday_august'),
    ('SK', '2025-08-04', 'Saskatchewan Day', 2025, TRUE, 'first_monday_august'),
    ('AB', '2025-08-04', 'Heritage Day', 2025, FALSE, 'first_monday_august');

-- Labour Day - Sep 1, 2025
INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory, calculation_rule) VALUES
    ('AB', '2025-09-01', 'Labour Day', 2025, TRUE, 'first_monday_september'),
    ('BC', '2025-09-01', 'Labour Day', 2025, TRUE, 'first_monday_september'),
    ('MB', '2025-09-01', 'Labour Day', 2025, TRUE, 'first_monday_september'),
    ('NB', '2025-09-01', 'Labour Day', 2025, TRUE, 'first_monday_september'),
    ('NL', '2025-09-01', 'Labour Day', 2025, TRUE, 'first_monday_september'),
    ('NS', '2025-09-01', 'Labour Day', 2025, TRUE, 'first_monday_september'),
    ('NT', '2025-09-01', 'Labour Day', 2025, TRUE, 'first_monday_september'),
    ('NU', '2025-09-01', 'Labour Day', 2025, TRUE, 'first_monday_september'),
    ('ON', '2025-09-01', 'Labour Day', 2025, TRUE, 'first_monday_september'),
    ('PE', '2025-09-01', 'Labour Day', 2025, TRUE, 'first_monday_september'),
    ('SK', '2025-09-01', 'Labour Day', 2025, TRUE, 'first_monday_september'),
    ('YT', '2025-09-01', 'Labour Day', 2025, TRUE, 'first_monday_september');

-- National Day for Truth and Reconciliation - Sep 30, 2025
INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory) VALUES
    ('BC', '2025-09-30', 'National Day for Truth and Reconciliation', 2025, TRUE),
    ('MB', '2025-09-30', 'National Day for Truth and Reconciliation', 2025, TRUE),
    ('NU', '2025-09-30', 'National Day for Truth and Reconciliation', 2025, TRUE),
    ('PE', '2025-09-30', 'National Day for Truth and Reconciliation', 2025, TRUE),
    ('YT', '2025-09-30', 'National Day for Truth and Reconciliation', 2025, TRUE),
    ('AB', '2025-09-30', 'National Day for Truth and Reconciliation', 2025, FALSE);

-- Thanksgiving - Oct 13, 2025
INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory, calculation_rule) VALUES
    ('AB', '2025-10-13', 'Thanksgiving Day', 2025, TRUE, 'second_monday_october'),
    ('BC', '2025-10-13', 'Thanksgiving Day', 2025, TRUE, 'second_monday_october'),
    ('MB', '2025-10-13', 'Thanksgiving Day', 2025, TRUE, 'second_monday_october'),
    ('NB', '2025-10-13', 'Thanksgiving Day', 2025, TRUE, 'second_monday_october'),
    ('NT', '2025-10-13', 'Thanksgiving Day', 2025, TRUE, 'second_monday_october'),
    ('NU', '2025-10-13', 'Thanksgiving Day', 2025, TRUE, 'second_monday_october'),
    ('ON', '2025-10-13', 'Thanksgiving Day', 2025, TRUE, 'second_monday_october'),
    ('PE', '2025-10-13', 'Thanksgiving Day', 2025, TRUE, 'second_monday_october'),
    ('SK', '2025-10-13', 'Thanksgiving Day', 2025, TRUE, 'second_monday_october'),
    ('YT', '2025-10-13', 'Thanksgiving Day', 2025, TRUE, 'second_monday_october');

-- Remembrance Day - Nov 11, 2025
INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory) VALUES
    ('AB', '2025-11-11', 'Remembrance Day', 2025, TRUE),
    ('BC', '2025-11-11', 'Remembrance Day', 2025, TRUE),
    ('NL', '2025-11-11', 'Remembrance Day', 2025, TRUE),
    ('NT', '2025-11-11', 'Remembrance Day', 2025, TRUE),
    ('NU', '2025-11-11', 'Remembrance Day', 2025, TRUE),
    ('PE', '2025-11-11', 'Remembrance Day', 2025, TRUE),
    ('SK', '2025-11-11', 'Remembrance Day', 2025, TRUE),
    ('YT', '2025-11-11', 'Remembrance Day', 2025, TRUE);

-- Christmas Day - Dec 25, 2025
INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory) VALUES
    ('AB', '2025-12-25', 'Christmas Day', 2025, TRUE),
    ('BC', '2025-12-25', 'Christmas Day', 2025, TRUE),
    ('MB', '2025-12-25', 'Christmas Day', 2025, TRUE),
    ('NB', '2025-12-25', 'Christmas Day', 2025, TRUE),
    ('NL', '2025-12-25', 'Christmas Day', 2025, TRUE),
    ('NS', '2025-12-25', 'Christmas Day', 2025, TRUE),
    ('NT', '2025-12-25', 'Christmas Day', 2025, TRUE),
    ('NU', '2025-12-25', 'Christmas Day', 2025, TRUE),
    ('ON', '2025-12-25', 'Christmas Day', 2025, TRUE),
    ('PE', '2025-12-25', 'Christmas Day', 2025, TRUE),
    ('SK', '2025-12-25', 'Christmas Day', 2025, TRUE),
    ('YT', '2025-12-25', 'Christmas Day', 2025, TRUE);

-- Boxing Day - Dec 26, 2025
INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory) VALUES
    ('ON', '2025-12-26', 'Boxing Day', 2025, TRUE),
    ('AB', '2025-12-26', 'Boxing Day', 2025, FALSE);

-- =============================================================================
-- 2026 STATUTORY HOLIDAYS DATA (abbreviated - same pattern)
-- =============================================================================

INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory) VALUES
    ('AB', '2026-01-01', 'New Year''s Day', 2026, TRUE), ('BC', '2026-01-01', 'New Year''s Day', 2026, TRUE),
    ('MB', '2026-01-01', 'New Year''s Day', 2026, TRUE), ('NB', '2026-01-01', 'New Year''s Day', 2026, TRUE),
    ('NL', '2026-01-01', 'New Year''s Day', 2026, TRUE), ('NS', '2026-01-01', 'New Year''s Day', 2026, TRUE),
    ('NT', '2026-01-01', 'New Year''s Day', 2026, TRUE), ('NU', '2026-01-01', 'New Year''s Day', 2026, TRUE),
    ('ON', '2026-01-01', 'New Year''s Day', 2026, TRUE), ('PE', '2026-01-01', 'New Year''s Day', 2026, TRUE),
    ('SK', '2026-01-01', 'New Year''s Day', 2026, TRUE), ('YT', '2026-01-01', 'New Year''s Day', 2026, TRUE);

INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory, calculation_rule) VALUES
    ('AB', '2026-02-16', 'Family Day', 2026, TRUE, 'third_monday_february'),
    ('BC', '2026-02-16', 'Family Day', 2026, TRUE, 'third_monday_february'),
    ('NB', '2026-02-16', 'Family Day', 2026, TRUE, 'third_monday_february'),
    ('ON', '2026-02-16', 'Family Day', 2026, TRUE, 'third_monday_february'),
    ('SK', '2026-02-16', 'Family Day', 2026, TRUE, 'third_monday_february'),
    ('MB', '2026-02-16', 'Louis Riel Day', 2026, TRUE, 'third_monday_february'),
    ('PE', '2026-02-16', 'Islander Day', 2026, TRUE, 'third_monday_february'),
    ('NS', '2026-02-16', 'Heritage Day', 2026, TRUE, 'third_monday_february');

INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory, calculation_rule) VALUES
    ('AB', '2026-04-03', 'Good Friday', 2026, TRUE, 'easter_minus_2'),
    ('BC', '2026-04-03', 'Good Friday', 2026, TRUE, 'easter_minus_2'),
    ('MB', '2026-04-03', 'Good Friday', 2026, TRUE, 'easter_minus_2'),
    ('NB', '2026-04-03', 'Good Friday', 2026, TRUE, 'easter_minus_2'),
    ('NL', '2026-04-03', 'Good Friday', 2026, TRUE, 'easter_minus_2'),
    ('NS', '2026-04-03', 'Good Friday', 2026, TRUE, 'easter_minus_2'),
    ('NT', '2026-04-03', 'Good Friday', 2026, TRUE, 'easter_minus_2'),
    ('NU', '2026-04-03', 'Good Friday', 2026, TRUE, 'easter_minus_2'),
    ('ON', '2026-04-03', 'Good Friday', 2026, TRUE, 'easter_minus_2'),
    ('PE', '2026-04-03', 'Good Friday', 2026, TRUE, 'easter_minus_2'),
    ('SK', '2026-04-03', 'Good Friday', 2026, TRUE, 'easter_minus_2'),
    ('YT', '2026-04-03', 'Good Friday', 2026, TRUE, 'easter_minus_2');

INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory, calculation_rule) VALUES
    ('NU', '2026-04-06', 'Easter Monday', 2026, TRUE, 'easter_plus_1'),
    ('AB', '2026-04-06', 'Easter Monday', 2026, FALSE, 'easter_plus_1');

INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory, calculation_rule) VALUES
    ('AB', '2026-05-18', 'Victoria Day', 2026, TRUE, 'last_monday_before_may_25'),
    ('BC', '2026-05-18', 'Victoria Day', 2026, TRUE, 'last_monday_before_may_25'),
    ('MB', '2026-05-18', 'Victoria Day', 2026, TRUE, 'last_monday_before_may_25'),
    ('NB', '2026-05-18', 'Victoria Day', 2026, TRUE, 'last_monday_before_may_25'),
    ('NT', '2026-05-18', 'Victoria Day', 2026, TRUE, 'last_monday_before_may_25'),
    ('NU', '2026-05-18', 'Victoria Day', 2026, TRUE, 'last_monday_before_may_25'),
    ('ON', '2026-05-18', 'Victoria Day', 2026, TRUE, 'last_monday_before_may_25'),
    ('PE', '2026-05-18', 'Victoria Day', 2026, TRUE, 'last_monday_before_may_25'),
    ('SK', '2026-05-18', 'Victoria Day', 2026, TRUE, 'last_monday_before_may_25'),
    ('YT', '2026-05-18', 'Victoria Day', 2026, TRUE, 'last_monday_before_may_25');

INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory) VALUES
    ('AB', '2026-07-01', 'Canada Day', 2026, TRUE), ('BC', '2026-07-01', 'Canada Day', 2026, TRUE),
    ('MB', '2026-07-01', 'Canada Day', 2026, TRUE), ('NB', '2026-07-01', 'Canada Day', 2026, TRUE),
    ('NL', '2026-07-01', 'Memorial Day', 2026, TRUE), ('NS', '2026-07-01', 'Canada Day', 2026, TRUE),
    ('NT', '2026-07-01', 'Canada Day', 2026, TRUE), ('NU', '2026-07-01', 'Canada Day', 2026, TRUE),
    ('ON', '2026-07-01', 'Canada Day', 2026, TRUE), ('PE', '2026-07-01', 'Canada Day', 2026, TRUE),
    ('SK', '2026-07-01', 'Canada Day', 2026, TRUE), ('YT', '2026-07-01', 'Canada Day', 2026, TRUE),
    ('NU', '2026-07-09', 'Nunavut Day', 2026, TRUE);

INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory, calculation_rule) VALUES
    ('BC', '2026-08-03', 'British Columbia Day', 2026, TRUE, 'first_monday_august'),
    ('NT', '2026-08-03', 'Civic Holiday', 2026, TRUE, 'first_monday_august'),
    ('NU', '2026-08-03', 'Civic Holiday', 2026, TRUE, 'first_monday_august'),
    ('SK', '2026-08-03', 'Saskatchewan Day', 2026, TRUE, 'first_monday_august'),
    ('AB', '2026-08-03', 'Heritage Day', 2026, FALSE, 'first_monday_august');

INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory, calculation_rule) VALUES
    ('AB', '2026-09-07', 'Labour Day', 2026, TRUE, 'first_monday_september'),
    ('BC', '2026-09-07', 'Labour Day', 2026, TRUE, 'first_monday_september'),
    ('MB', '2026-09-07', 'Labour Day', 2026, TRUE, 'first_monday_september'),
    ('NB', '2026-09-07', 'Labour Day', 2026, TRUE, 'first_monday_september'),
    ('NL', '2026-09-07', 'Labour Day', 2026, TRUE, 'first_monday_september'),
    ('NS', '2026-09-07', 'Labour Day', 2026, TRUE, 'first_monday_september'),
    ('NT', '2026-09-07', 'Labour Day', 2026, TRUE, 'first_monday_september'),
    ('NU', '2026-09-07', 'Labour Day', 2026, TRUE, 'first_monday_september'),
    ('ON', '2026-09-07', 'Labour Day', 2026, TRUE, 'first_monday_september'),
    ('PE', '2026-09-07', 'Labour Day', 2026, TRUE, 'first_monday_september'),
    ('SK', '2026-09-07', 'Labour Day', 2026, TRUE, 'first_monday_september'),
    ('YT', '2026-09-07', 'Labour Day', 2026, TRUE, 'first_monday_september');

INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory) VALUES
    ('BC', '2026-09-30', 'National Day for Truth and Reconciliation', 2026, TRUE),
    ('MB', '2026-09-30', 'National Day for Truth and Reconciliation', 2026, TRUE),
    ('NU', '2026-09-30', 'National Day for Truth and Reconciliation', 2026, TRUE),
    ('PE', '2026-09-30', 'National Day for Truth and Reconciliation', 2026, TRUE),
    ('YT', '2026-09-30', 'National Day for Truth and Reconciliation', 2026, TRUE),
    ('AB', '2026-09-30', 'National Day for Truth and Reconciliation', 2026, FALSE);

INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory, calculation_rule) VALUES
    ('AB', '2026-10-12', 'Thanksgiving Day', 2026, TRUE, 'second_monday_october'),
    ('BC', '2026-10-12', 'Thanksgiving Day', 2026, TRUE, 'second_monday_october'),
    ('MB', '2026-10-12', 'Thanksgiving Day', 2026, TRUE, 'second_monday_october'),
    ('NB', '2026-10-12', 'Thanksgiving Day', 2026, TRUE, 'second_monday_october'),
    ('NT', '2026-10-12', 'Thanksgiving Day', 2026, TRUE, 'second_monday_october'),
    ('NU', '2026-10-12', 'Thanksgiving Day', 2026, TRUE, 'second_monday_october'),
    ('ON', '2026-10-12', 'Thanksgiving Day', 2026, TRUE, 'second_monday_october'),
    ('PE', '2026-10-12', 'Thanksgiving Day', 2026, TRUE, 'second_monday_october'),
    ('SK', '2026-10-12', 'Thanksgiving Day', 2026, TRUE, 'second_monday_october'),
    ('YT', '2026-10-12', 'Thanksgiving Day', 2026, TRUE, 'second_monday_october');

INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory) VALUES
    ('AB', '2026-11-11', 'Remembrance Day', 2026, TRUE), ('BC', '2026-11-11', 'Remembrance Day', 2026, TRUE),
    ('NL', '2026-11-11', 'Remembrance Day', 2026, TRUE), ('NT', '2026-11-11', 'Remembrance Day', 2026, TRUE),
    ('NU', '2026-11-11', 'Remembrance Day', 2026, TRUE), ('PE', '2026-11-11', 'Remembrance Day', 2026, TRUE),
    ('SK', '2026-11-11', 'Remembrance Day', 2026, TRUE), ('YT', '2026-11-11', 'Remembrance Day', 2026, TRUE);

INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory) VALUES
    ('AB', '2026-12-25', 'Christmas Day', 2026, TRUE), ('BC', '2026-12-25', 'Christmas Day', 2026, TRUE),
    ('MB', '2026-12-25', 'Christmas Day', 2026, TRUE), ('NB', '2026-12-25', 'Christmas Day', 2026, TRUE),
    ('NL', '2026-12-25', 'Christmas Day', 2026, TRUE), ('NS', '2026-12-25', 'Christmas Day', 2026, TRUE),
    ('NT', '2026-12-25', 'Christmas Day', 2026, TRUE), ('NU', '2026-12-25', 'Christmas Day', 2026, TRUE),
    ('ON', '2026-12-25', 'Christmas Day', 2026, TRUE), ('PE', '2026-12-25', 'Christmas Day', 2026, TRUE),
    ('SK', '2026-12-25', 'Christmas Day', 2026, TRUE), ('YT', '2026-12-25', 'Christmas Day', 2026, TRUE);

INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory) VALUES
    ('ON', '2026-12-26', 'Boxing Day', 2026, TRUE), ('AB', '2026-12-26', 'Boxing Day', 2026, FALSE);

-- 2027 holidays (abbreviated)
INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory) VALUES
    ('AB', '2027-01-01', 'New Year''s Day', 2027, TRUE), ('BC', '2027-01-01', 'New Year''s Day', 2027, TRUE),
    ('MB', '2027-01-01', 'New Year''s Day', 2027, TRUE), ('NB', '2027-01-01', 'New Year''s Day', 2027, TRUE),
    ('NL', '2027-01-01', 'New Year''s Day', 2027, TRUE), ('NS', '2027-01-01', 'New Year''s Day', 2027, TRUE),
    ('NT', '2027-01-01', 'New Year''s Day', 2027, TRUE), ('NU', '2027-01-01', 'New Year''s Day', 2027, TRUE),
    ('ON', '2027-01-01', 'New Year''s Day', 2027, TRUE), ('PE', '2027-01-01', 'New Year''s Day', 2027, TRUE),
    ('SK', '2027-01-01', 'New Year''s Day', 2027, TRUE), ('YT', '2027-01-01', 'New Year''s Day', 2027, TRUE);

INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory, calculation_rule) VALUES
    ('AB', '2027-02-15', 'Family Day', 2027, TRUE, 'third_monday_february'),
    ('BC', '2027-02-15', 'Family Day', 2027, TRUE, 'third_monday_february'),
    ('NB', '2027-02-15', 'Family Day', 2027, TRUE, 'third_monday_february'),
    ('ON', '2027-02-15', 'Family Day', 2027, TRUE, 'third_monday_february'),
    ('SK', '2027-02-15', 'Family Day', 2027, TRUE, 'third_monday_february'),
    ('MB', '2027-02-15', 'Louis Riel Day', 2027, TRUE, 'third_monday_february'),
    ('PE', '2027-02-15', 'Islander Day', 2027, TRUE, 'third_monday_february'),
    ('NS', '2027-02-15', 'Heritage Day', 2027, TRUE, 'third_monday_february');

INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory, calculation_rule) VALUES
    ('AB', '2027-03-26', 'Good Friday', 2027, TRUE, 'easter_minus_2'),
    ('BC', '2027-03-26', 'Good Friday', 2027, TRUE, 'easter_minus_2'),
    ('MB', '2027-03-26', 'Good Friday', 2027, TRUE, 'easter_minus_2'),
    ('NB', '2027-03-26', 'Good Friday', 2027, TRUE, 'easter_minus_2'),
    ('NL', '2027-03-26', 'Good Friday', 2027, TRUE, 'easter_minus_2'),
    ('NS', '2027-03-26', 'Good Friday', 2027, TRUE, 'easter_minus_2'),
    ('NT', '2027-03-26', 'Good Friday', 2027, TRUE, 'easter_minus_2'),
    ('NU', '2027-03-26', 'Good Friday', 2027, TRUE, 'easter_minus_2'),
    ('ON', '2027-03-26', 'Good Friday', 2027, TRUE, 'easter_minus_2'),
    ('PE', '2027-03-26', 'Good Friday', 2027, TRUE, 'easter_minus_2'),
    ('SK', '2027-03-26', 'Good Friday', 2027, TRUE, 'easter_minus_2'),
    ('YT', '2027-03-26', 'Good Friday', 2027, TRUE, 'easter_minus_2');

INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory, calculation_rule) VALUES
    ('NU', '2027-03-29', 'Easter Monday', 2027, TRUE, 'easter_plus_1'),
    ('AB', '2027-03-29', 'Easter Monday', 2027, FALSE, 'easter_plus_1');

INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory, calculation_rule) VALUES
    ('AB', '2027-05-24', 'Victoria Day', 2027, TRUE, 'last_monday_before_may_25'),
    ('BC', '2027-05-24', 'Victoria Day', 2027, TRUE, 'last_monday_before_may_25'),
    ('MB', '2027-05-24', 'Victoria Day', 2027, TRUE, 'last_monday_before_may_25'),
    ('NB', '2027-05-24', 'Victoria Day', 2027, TRUE, 'last_monday_before_may_25'),
    ('NT', '2027-05-24', 'Victoria Day', 2027, TRUE, 'last_monday_before_may_25'),
    ('NU', '2027-05-24', 'Victoria Day', 2027, TRUE, 'last_monday_before_may_25'),
    ('ON', '2027-05-24', 'Victoria Day', 2027, TRUE, 'last_monday_before_may_25'),
    ('PE', '2027-05-24', 'Victoria Day', 2027, TRUE, 'last_monday_before_may_25'),
    ('SK', '2027-05-24', 'Victoria Day', 2027, TRUE, 'last_monday_before_may_25'),
    ('YT', '2027-05-24', 'Victoria Day', 2027, TRUE, 'last_monday_before_may_25');

INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory) VALUES
    ('AB', '2027-07-01', 'Canada Day', 2027, TRUE), ('BC', '2027-07-01', 'Canada Day', 2027, TRUE),
    ('MB', '2027-07-01', 'Canada Day', 2027, TRUE), ('NB', '2027-07-01', 'Canada Day', 2027, TRUE),
    ('NL', '2027-07-01', 'Memorial Day', 2027, TRUE), ('NS', '2027-07-01', 'Canada Day', 2027, TRUE),
    ('NT', '2027-07-01', 'Canada Day', 2027, TRUE), ('NU', '2027-07-01', 'Canada Day', 2027, TRUE),
    ('ON', '2027-07-01', 'Canada Day', 2027, TRUE), ('PE', '2027-07-01', 'Canada Day', 2027, TRUE),
    ('SK', '2027-07-01', 'Canada Day', 2027, TRUE), ('YT', '2027-07-01', 'Canada Day', 2027, TRUE),
    ('NU', '2027-07-09', 'Nunavut Day', 2027, TRUE);

INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory, calculation_rule) VALUES
    ('BC', '2027-08-02', 'British Columbia Day', 2027, TRUE, 'first_monday_august'),
    ('NT', '2027-08-02', 'Civic Holiday', 2027, TRUE, 'first_monday_august'),
    ('NU', '2027-08-02', 'Civic Holiday', 2027, TRUE, 'first_monday_august'),
    ('SK', '2027-08-02', 'Saskatchewan Day', 2027, TRUE, 'first_monday_august'),
    ('AB', '2027-08-02', 'Heritage Day', 2027, FALSE, 'first_monday_august');

INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory, calculation_rule) VALUES
    ('AB', '2027-09-06', 'Labour Day', 2027, TRUE, 'first_monday_september'),
    ('BC', '2027-09-06', 'Labour Day', 2027, TRUE, 'first_monday_september'),
    ('MB', '2027-09-06', 'Labour Day', 2027, TRUE, 'first_monday_september'),
    ('NB', '2027-09-06', 'Labour Day', 2027, TRUE, 'first_monday_september'),
    ('NL', '2027-09-06', 'Labour Day', 2027, TRUE, 'first_monday_september'),
    ('NS', '2027-09-06', 'Labour Day', 2027, TRUE, 'first_monday_september'),
    ('NT', '2027-09-06', 'Labour Day', 2027, TRUE, 'first_monday_september'),
    ('NU', '2027-09-06', 'Labour Day', 2027, TRUE, 'first_monday_september'),
    ('ON', '2027-09-06', 'Labour Day', 2027, TRUE, 'first_monday_september'),
    ('PE', '2027-09-06', 'Labour Day', 2027, TRUE, 'first_monday_september'),
    ('SK', '2027-09-06', 'Labour Day', 2027, TRUE, 'first_monday_september'),
    ('YT', '2027-09-06', 'Labour Day', 2027, TRUE, 'first_monday_september');

INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory) VALUES
    ('BC', '2027-09-30', 'National Day for Truth and Reconciliation', 2027, TRUE),
    ('MB', '2027-09-30', 'National Day for Truth and Reconciliation', 2027, TRUE),
    ('NU', '2027-09-30', 'National Day for Truth and Reconciliation', 2027, TRUE),
    ('PE', '2027-09-30', 'National Day for Truth and Reconciliation', 2027, TRUE),
    ('YT', '2027-09-30', 'National Day for Truth and Reconciliation', 2027, TRUE),
    ('AB', '2027-09-30', 'National Day for Truth and Reconciliation', 2027, FALSE);

INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory, calculation_rule) VALUES
    ('AB', '2027-10-11', 'Thanksgiving Day', 2027, TRUE, 'second_monday_october'),
    ('BC', '2027-10-11', 'Thanksgiving Day', 2027, TRUE, 'second_monday_october'),
    ('MB', '2027-10-11', 'Thanksgiving Day', 2027, TRUE, 'second_monday_october'),
    ('NB', '2027-10-11', 'Thanksgiving Day', 2027, TRUE, 'second_monday_october'),
    ('NT', '2027-10-11', 'Thanksgiving Day', 2027, TRUE, 'second_monday_october'),
    ('NU', '2027-10-11', 'Thanksgiving Day', 2027, TRUE, 'second_monday_october'),
    ('ON', '2027-10-11', 'Thanksgiving Day', 2027, TRUE, 'second_monday_october'),
    ('PE', '2027-10-11', 'Thanksgiving Day', 2027, TRUE, 'second_monday_october'),
    ('SK', '2027-10-11', 'Thanksgiving Day', 2027, TRUE, 'second_monday_october'),
    ('YT', '2027-10-11', 'Thanksgiving Day', 2027, TRUE, 'second_monday_october');

INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory) VALUES
    ('AB', '2027-11-11', 'Remembrance Day', 2027, TRUE), ('BC', '2027-11-11', 'Remembrance Day', 2027, TRUE),
    ('NL', '2027-11-11', 'Remembrance Day', 2027, TRUE), ('NT', '2027-11-11', 'Remembrance Day', 2027, TRUE),
    ('NU', '2027-11-11', 'Remembrance Day', 2027, TRUE), ('PE', '2027-11-11', 'Remembrance Day', 2027, TRUE),
    ('SK', '2027-11-11', 'Remembrance Day', 2027, TRUE), ('YT', '2027-11-11', 'Remembrance Day', 2027, TRUE);

INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory) VALUES
    ('AB', '2027-12-25', 'Christmas Day', 2027, TRUE), ('BC', '2027-12-25', 'Christmas Day', 2027, TRUE),
    ('MB', '2027-12-25', 'Christmas Day', 2027, TRUE), ('NB', '2027-12-25', 'Christmas Day', 2027, TRUE),
    ('NL', '2027-12-25', 'Christmas Day', 2027, TRUE), ('NS', '2027-12-25', 'Christmas Day', 2027, TRUE),
    ('NT', '2027-12-25', 'Christmas Day', 2027, TRUE), ('NU', '2027-12-25', 'Christmas Day', 2027, TRUE),
    ('ON', '2027-12-25', 'Christmas Day', 2027, TRUE), ('PE', '2027-12-25', 'Christmas Day', 2027, TRUE),
    ('SK', '2027-12-25', 'Christmas Day', 2027, TRUE), ('YT', '2027-12-25', 'Christmas Day', 2027, TRUE);

INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory) VALUES
    ('ON', '2027-12-26', 'Boxing Day', 2027, TRUE), ('AB', '2027-12-26', 'Boxing Day', 2027, FALSE);

-- =============================================================================
-- SICK LEAVE BALANCE TABLES (config loaded from JSON files)
-- =============================================================================

CREATE TABLE IF NOT EXISTS employee_sick_leave_balances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    year INTEGER NOT NULL,
    paid_days_entitled NUMERIC(4, 2) NOT NULL DEFAULT 0,
    unpaid_days_entitled NUMERIC(4, 2) NOT NULL DEFAULT 0,
    paid_days_used NUMERIC(4, 2) NOT NULL DEFAULT 0,
    unpaid_days_used NUMERIC(4, 2) NOT NULL DEFAULT 0,
    carried_over_days NUMERIC(4, 2) NOT NULL DEFAULT 0,
    eligibility_date DATE,
    is_eligible BOOLEAN DEFAULT FALSE,
    last_accrual_date DATE,
    accrued_days_ytd NUMERIC(4, 2) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(employee_id, year)
);

CREATE INDEX IF NOT EXISTS idx_employee_sick_leave_balances_employee ON employee_sick_leave_balances(employee_id);
CREATE INDEX IF NOT EXISTS idx_employee_sick_leave_balances_year ON employee_sick_leave_balances(year);
CREATE INDEX IF NOT EXISTS idx_employee_sick_leave_balances_employee_year ON employee_sick_leave_balances(employee_id, year);

ALTER TABLE employee_sick_leave_balances ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read their employees sick leave balances" ON employee_sick_leave_balances
    FOR SELECT TO authenticated USING (
        EXISTS (SELECT 1 FROM employees e WHERE e.id = employee_sick_leave_balances.employee_id AND e.user_id = auth.uid()::text)
    );
CREATE POLICY "Users can insert their employees sick leave balances" ON employee_sick_leave_balances
    FOR INSERT TO authenticated WITH CHECK (
        EXISTS (SELECT 1 FROM employees e WHERE e.id = employee_sick_leave_balances.employee_id AND e.user_id = auth.uid()::text)
    );
CREATE POLICY "Users can update their employees sick leave balances" ON employee_sick_leave_balances
    FOR UPDATE TO authenticated USING (
        EXISTS (SELECT 1 FROM employees e WHERE e.id = employee_sick_leave_balances.employee_id AND e.user_id = auth.uid()::text)
    );

CREATE TRIGGER update_employee_sick_leave_balances_updated_at
    BEFORE UPDATE ON employee_sick_leave_balances FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Sick leave usage history
CREATE TABLE IF NOT EXISTS sick_leave_usage_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    balance_id UUID NOT NULL REFERENCES employee_sick_leave_balances(id) ON DELETE CASCADE,
    payroll_record_id UUID REFERENCES payroll_records(id) ON DELETE SET NULL,
    usage_date DATE NOT NULL,
    hours_taken NUMERIC(6, 2) NOT NULL,
    days_taken NUMERIC(4, 2) NOT NULL,
    is_paid BOOLEAN NOT NULL DEFAULT TRUE,
    average_day_pay NUMERIC(10, 2),
    sick_pay_amount NUMERIC(10, 2),
    calculation_method VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sick_leave_usage_employee ON sick_leave_usage_history(employee_id);
CREATE INDEX IF NOT EXISTS idx_sick_leave_usage_date ON sick_leave_usage_history(usage_date);

ALTER TABLE sick_leave_usage_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read their employees sick leave history" ON sick_leave_usage_history
    FOR SELECT TO authenticated USING (
        EXISTS (SELECT 1 FROM employees e WHERE e.id = sick_leave_usage_history.employee_id AND e.user_id = auth.uid()::text)
    );
CREATE POLICY "Users can insert their employees sick leave history" ON sick_leave_usage_history
    FOR INSERT TO authenticated WITH CHECK (
        EXISTS (SELECT 1 FROM employees e WHERE e.id = sick_leave_usage_history.employee_id AND e.user_id = auth.uid()::text)
    );

COMMENT ON TABLE employee_sick_leave_balances IS 'Per-year sick leave balance tracking for each employee. Province configs loaded from JSON files.';
COMMENT ON TABLE sick_leave_usage_history IS 'Audit trail of sick leave usage with payment details';
