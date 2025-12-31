-- Create statutory_holidays table for Canadian payroll
-- Stores statutory holidays by province for 2025-2027

CREATE TABLE statutory_holidays (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  province TEXT NOT NULL,           -- 'ON', 'BC', 'AB', etc.
  holiday_date DATE NOT NULL,
  name TEXT NOT NULL,
  name_fr TEXT,                     -- French name (optional)
  year INTEGER NOT NULL,
  is_statutory BOOLEAN DEFAULT TRUE,  -- TRUE = mandatory, FALSE = optional
  calculation_rule TEXT,            -- For moveable holidays (e.g., 'last_monday_may_before_25')
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(province, holiday_date)
);

-- Indexes for efficient querying
CREATE INDEX idx_holidays_province_year ON statutory_holidays(province, year);
CREATE INDEX idx_holidays_date_range ON statutory_holidays(holiday_date);
CREATE INDEX idx_holidays_province_date ON statutory_holidays(province, holiday_date, is_statutory);

-- Add comment for documentation
COMMENT ON TABLE statutory_holidays IS 'Canadian statutory holidays by province, excluding Quebec';
COMMENT ON COLUMN statutory_holidays.province IS 'Province code: AB, BC, MB, NB, NL, NS, NT, NU, ON, PE, SK, YT';
COMMENT ON COLUMN statutory_holidays.is_statutory IS 'TRUE = mandatory paid holiday, FALSE = optional/employer discretion';

-- Enable RLS
ALTER TABLE statutory_holidays ENABLE ROW LEVEL SECURITY;

-- Everyone can read holidays (public data)
CREATE POLICY "Holidays are readable by everyone"
  ON statutory_holidays FOR SELECT USING (true);

-- Only service role can insert/update (for migrations and admin)
CREATE POLICY "Only service role can modify holidays"
  ON statutory_holidays FOR ALL
  USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');

-- =============================================
-- 2025 STATUTORY HOLIDAYS DATA
-- Based on docs/08_holidays_vacation.md
-- =============================================

-- New Year's Day - Jan 1, 2025 (All provinces)
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

-- Family Day / Louis Riel Day / Islander Day / Heritage Day - Feb 17, 2025 (3rd Monday)
INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory, calculation_rule) VALUES
  ('AB', '2025-02-17', 'Family Day', 2025, TRUE, 'third_monday_february'),
  ('BC', '2025-02-17', 'Family Day', 2025, TRUE, 'third_monday_february'),
  ('NB', '2025-02-17', 'Family Day', 2025, TRUE, 'third_monday_february'),
  ('ON', '2025-02-17', 'Family Day', 2025, TRUE, 'third_monday_february'),
  ('SK', '2025-02-17', 'Family Day', 2025, TRUE, 'third_monday_february'),
  ('MB', '2025-02-17', 'Louis Riel Day', 2025, TRUE, 'third_monday_february'),
  ('PE', '2025-02-17', 'Islander Day', 2025, TRUE, 'third_monday_february'),
  ('NS', '2025-02-17', 'Heritage Day', 2025, TRUE, 'third_monday_february');

-- Good Friday - Apr 18, 2025 (All provinces)
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

-- Easter Monday - Apr 21, 2025 (NU only, AB optional)
INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory, calculation_rule) VALUES
  ('NU', '2025-04-21', 'Easter Monday', 2025, TRUE, 'easter_plus_1'),
  ('AB', '2025-04-21', 'Easter Monday', 2025, FALSE, 'easter_plus_1');

-- Victoria Day - May 19, 2025 (Last Monday before May 25)
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

-- Canada Day - Jul 1, 2025 (All provinces, NL calls it Memorial Day)
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

-- Nunavut Day - Jul 9, 2025 (NU only)
INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory) VALUES
  ('NU', '2025-07-09', 'Nunavut Day', 2025, TRUE);

-- Civic Holiday / BC Day / Saskatchewan Day - Aug 4, 2025 (1st Monday in August)
INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory, calculation_rule) VALUES
  ('BC', '2025-08-04', 'British Columbia Day', 2025, TRUE, 'first_monday_august'),
  ('NT', '2025-08-04', 'Civic Holiday', 2025, TRUE, 'first_monday_august'),
  ('NU', '2025-08-04', 'Civic Holiday', 2025, TRUE, 'first_monday_august'),
  ('SK', '2025-08-04', 'Saskatchewan Day', 2025, TRUE, 'first_monday_august'),
  ('AB', '2025-08-04', 'Heritage Day', 2025, FALSE, 'first_monday_august');

-- Labour Day - Sep 1, 2025 (All provinces, 1st Monday in September)
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

-- Thanksgiving - Oct 13, 2025 (2nd Monday in October)
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

-- Christmas Day - Dec 25, 2025 (All provinces)
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

-- Boxing Day - Dec 26, 2025 (ON statutory, AB optional)
INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory) VALUES
  ('ON', '2025-12-26', 'Boxing Day', 2025, TRUE),
  ('AB', '2025-12-26', 'Boxing Day', 2025, FALSE);

-- =============================================
-- 2026 STATUTORY HOLIDAYS DATA
-- =============================================

-- New Year's Day - Jan 1, 2026 (All provinces)
INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory) VALUES
  ('AB', '2026-01-01', 'New Year''s Day', 2026, TRUE),
  ('BC', '2026-01-01', 'New Year''s Day', 2026, TRUE),
  ('MB', '2026-01-01', 'New Year''s Day', 2026, TRUE),
  ('NB', '2026-01-01', 'New Year''s Day', 2026, TRUE),
  ('NL', '2026-01-01', 'New Year''s Day', 2026, TRUE),
  ('NS', '2026-01-01', 'New Year''s Day', 2026, TRUE),
  ('NT', '2026-01-01', 'New Year''s Day', 2026, TRUE),
  ('NU', '2026-01-01', 'New Year''s Day', 2026, TRUE),
  ('ON', '2026-01-01', 'New Year''s Day', 2026, TRUE),
  ('PE', '2026-01-01', 'New Year''s Day', 2026, TRUE),
  ('SK', '2026-01-01', 'New Year''s Day', 2026, TRUE),
  ('YT', '2026-01-01', 'New Year''s Day', 2026, TRUE);

-- Family Day / Louis Riel Day / Islander Day / Heritage Day - Feb 16, 2026
INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory, calculation_rule) VALUES
  ('AB', '2026-02-16', 'Family Day', 2026, TRUE, 'third_monday_february'),
  ('BC', '2026-02-16', 'Family Day', 2026, TRUE, 'third_monday_february'),
  ('NB', '2026-02-16', 'Family Day', 2026, TRUE, 'third_monday_february'),
  ('ON', '2026-02-16', 'Family Day', 2026, TRUE, 'third_monday_february'),
  ('SK', '2026-02-16', 'Family Day', 2026, TRUE, 'third_monday_february'),
  ('MB', '2026-02-16', 'Louis Riel Day', 2026, TRUE, 'third_monday_february'),
  ('PE', '2026-02-16', 'Islander Day', 2026, TRUE, 'third_monday_february'),
  ('NS', '2026-02-16', 'Heritage Day', 2026, TRUE, 'third_monday_february');

-- Good Friday - Apr 3, 2026 (All provinces)
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

-- Easter Monday - Apr 6, 2026 (NU only, AB optional)
INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory, calculation_rule) VALUES
  ('NU', '2026-04-06', 'Easter Monday', 2026, TRUE, 'easter_plus_1'),
  ('AB', '2026-04-06', 'Easter Monday', 2026, FALSE, 'easter_plus_1');

-- Victoria Day - May 18, 2026
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

-- Canada Day - Jul 1, 2026 (All provinces)
INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory) VALUES
  ('AB', '2026-07-01', 'Canada Day', 2026, TRUE),
  ('BC', '2026-07-01', 'Canada Day', 2026, TRUE),
  ('MB', '2026-07-01', 'Canada Day', 2026, TRUE),
  ('NB', '2026-07-01', 'Canada Day', 2026, TRUE),
  ('NL', '2026-07-01', 'Memorial Day', 2026, TRUE),
  ('NS', '2026-07-01', 'Canada Day', 2026, TRUE),
  ('NT', '2026-07-01', 'Canada Day', 2026, TRUE),
  ('NU', '2026-07-01', 'Canada Day', 2026, TRUE),
  ('ON', '2026-07-01', 'Canada Day', 2026, TRUE),
  ('PE', '2026-07-01', 'Canada Day', 2026, TRUE),
  ('SK', '2026-07-01', 'Canada Day', 2026, TRUE),
  ('YT', '2026-07-01', 'Canada Day', 2026, TRUE);

-- Nunavut Day - Jul 9, 2026 (NU only)
INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory) VALUES
  ('NU', '2026-07-09', 'Nunavut Day', 2026, TRUE);

-- Civic Holiday / BC Day / Saskatchewan Day - Aug 3, 2026
INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory, calculation_rule) VALUES
  ('BC', '2026-08-03', 'British Columbia Day', 2026, TRUE, 'first_monday_august'),
  ('NT', '2026-08-03', 'Civic Holiday', 2026, TRUE, 'first_monday_august'),
  ('NU', '2026-08-03', 'Civic Holiday', 2026, TRUE, 'first_monday_august'),
  ('SK', '2026-08-03', 'Saskatchewan Day', 2026, TRUE, 'first_monday_august'),
  ('AB', '2026-08-03', 'Heritage Day', 2026, FALSE, 'first_monday_august');

-- Labour Day - Sep 7, 2026 (All provinces)
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

-- National Day for Truth and Reconciliation - Sep 30, 2026
INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory) VALUES
  ('BC', '2026-09-30', 'National Day for Truth and Reconciliation', 2026, TRUE),
  ('MB', '2026-09-30', 'National Day for Truth and Reconciliation', 2026, TRUE),
  ('NU', '2026-09-30', 'National Day for Truth and Reconciliation', 2026, TRUE),
  ('PE', '2026-09-30', 'National Day for Truth and Reconciliation', 2026, TRUE),
  ('YT', '2026-09-30', 'National Day for Truth and Reconciliation', 2026, TRUE),
  ('AB', '2026-09-30', 'National Day for Truth and Reconciliation', 2026, FALSE);

-- Thanksgiving - Oct 12, 2026
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

-- Remembrance Day - Nov 11, 2026
INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory) VALUES
  ('AB', '2026-11-11', 'Remembrance Day', 2026, TRUE),
  ('BC', '2026-11-11', 'Remembrance Day', 2026, TRUE),
  ('NL', '2026-11-11', 'Remembrance Day', 2026, TRUE),
  ('NT', '2026-11-11', 'Remembrance Day', 2026, TRUE),
  ('NU', '2026-11-11', 'Remembrance Day', 2026, TRUE),
  ('PE', '2026-11-11', 'Remembrance Day', 2026, TRUE),
  ('SK', '2026-11-11', 'Remembrance Day', 2026, TRUE),
  ('YT', '2026-11-11', 'Remembrance Day', 2026, TRUE);

-- Christmas Day - Dec 25, 2026 (All provinces)
INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory) VALUES
  ('AB', '2026-12-25', 'Christmas Day', 2026, TRUE),
  ('BC', '2026-12-25', 'Christmas Day', 2026, TRUE),
  ('MB', '2026-12-25', 'Christmas Day', 2026, TRUE),
  ('NB', '2026-12-25', 'Christmas Day', 2026, TRUE),
  ('NL', '2026-12-25', 'Christmas Day', 2026, TRUE),
  ('NS', '2026-12-25', 'Christmas Day', 2026, TRUE),
  ('NT', '2026-12-25', 'Christmas Day', 2026, TRUE),
  ('NU', '2026-12-25', 'Christmas Day', 2026, TRUE),
  ('ON', '2026-12-25', 'Christmas Day', 2026, TRUE),
  ('PE', '2026-12-25', 'Christmas Day', 2026, TRUE),
  ('SK', '2026-12-25', 'Christmas Day', 2026, TRUE),
  ('YT', '2026-12-25', 'Christmas Day', 2026, TRUE);

-- Boxing Day - Dec 26, 2026 (ON statutory, AB optional)
INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory) VALUES
  ('ON', '2026-12-26', 'Boxing Day', 2026, TRUE),
  ('AB', '2026-12-26', 'Boxing Day', 2026, FALSE);
