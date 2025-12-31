-- Add 2027 statutory holidays data
-- Moveable holiday dates for 2027:
-- - Easter Sunday: March 28
-- - Good Friday: March 26 (Easter - 2)
-- - Easter Monday: March 29 (Easter + 1)
-- - Family Day: February 15 (3rd Monday in February)
-- - Victoria Day: May 24 (Last Monday before May 25)
-- - BC Day/Civic Holiday: August 2 (1st Monday in August)
-- - Labour Day: September 6 (1st Monday in September)
-- - Thanksgiving: October 11 (2nd Monday in October)

-- =============================================
-- 2027 STATUTORY HOLIDAYS DATA
-- =============================================

-- New Year's Day - Jan 1, 2027 (All provinces)
INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory) VALUES
  ('AB', '2027-01-01', 'New Year''s Day', 2027, TRUE),
  ('BC', '2027-01-01', 'New Year''s Day', 2027, TRUE),
  ('MB', '2027-01-01', 'New Year''s Day', 2027, TRUE),
  ('NB', '2027-01-01', 'New Year''s Day', 2027, TRUE),
  ('NL', '2027-01-01', 'New Year''s Day', 2027, TRUE),
  ('NS', '2027-01-01', 'New Year''s Day', 2027, TRUE),
  ('NT', '2027-01-01', 'New Year''s Day', 2027, TRUE),
  ('NU', '2027-01-01', 'New Year''s Day', 2027, TRUE),
  ('ON', '2027-01-01', 'New Year''s Day', 2027, TRUE),
  ('PE', '2027-01-01', 'New Year''s Day', 2027, TRUE),
  ('SK', '2027-01-01', 'New Year''s Day', 2027, TRUE),
  ('YT', '2027-01-01', 'New Year''s Day', 2027, TRUE);

-- Family Day / Louis Riel Day / Islander Day / Heritage Day - Feb 15, 2027
INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory, calculation_rule) VALUES
  ('AB', '2027-02-15', 'Family Day', 2027, TRUE, 'third_monday_february'),
  ('BC', '2027-02-15', 'Family Day', 2027, TRUE, 'third_monday_february'),
  ('NB', '2027-02-15', 'Family Day', 2027, TRUE, 'third_monday_february'),
  ('ON', '2027-02-15', 'Family Day', 2027, TRUE, 'third_monday_february'),
  ('SK', '2027-02-15', 'Family Day', 2027, TRUE, 'third_monday_february'),
  ('MB', '2027-02-15', 'Louis Riel Day', 2027, TRUE, 'third_monday_february'),
  ('PE', '2027-02-15', 'Islander Day', 2027, TRUE, 'third_monday_february'),
  ('NS', '2027-02-15', 'Heritage Day', 2027, TRUE, 'third_monday_february');

-- Good Friday - Mar 26, 2027 (All provinces)
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

-- Easter Monday - Mar 29, 2027 (NU only, AB optional)
INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory, calculation_rule) VALUES
  ('NU', '2027-03-29', 'Easter Monday', 2027, TRUE, 'easter_plus_1'),
  ('AB', '2027-03-29', 'Easter Monday', 2027, FALSE, 'easter_plus_1');

-- Victoria Day - May 24, 2027
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

-- Canada Day - Jul 1, 2027 (All provinces)
INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory) VALUES
  ('AB', '2027-07-01', 'Canada Day', 2027, TRUE),
  ('BC', '2027-07-01', 'Canada Day', 2027, TRUE),
  ('MB', '2027-07-01', 'Canada Day', 2027, TRUE),
  ('NB', '2027-07-01', 'Canada Day', 2027, TRUE),
  ('NL', '2027-07-01', 'Memorial Day', 2027, TRUE),
  ('NS', '2027-07-01', 'Canada Day', 2027, TRUE),
  ('NT', '2027-07-01', 'Canada Day', 2027, TRUE),
  ('NU', '2027-07-01', 'Canada Day', 2027, TRUE),
  ('ON', '2027-07-01', 'Canada Day', 2027, TRUE),
  ('PE', '2027-07-01', 'Canada Day', 2027, TRUE),
  ('SK', '2027-07-01', 'Canada Day', 2027, TRUE),
  ('YT', '2027-07-01', 'Canada Day', 2027, TRUE);

-- Nunavut Day - Jul 9, 2027 (NU only)
INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory) VALUES
  ('NU', '2027-07-09', 'Nunavut Day', 2027, TRUE);

-- Civic Holiday / BC Day / Saskatchewan Day - Aug 2, 2027
INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory, calculation_rule) VALUES
  ('BC', '2027-08-02', 'British Columbia Day', 2027, TRUE, 'first_monday_august'),
  ('NT', '2027-08-02', 'Civic Holiday', 2027, TRUE, 'first_monday_august'),
  ('NU', '2027-08-02', 'Civic Holiday', 2027, TRUE, 'first_monday_august'),
  ('SK', '2027-08-02', 'Saskatchewan Day', 2027, TRUE, 'first_monday_august'),
  ('AB', '2027-08-02', 'Heritage Day', 2027, FALSE, 'first_monday_august');

-- Labour Day - Sep 6, 2027 (All provinces)
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

-- National Day for Truth and Reconciliation - Sep 30, 2027
INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory) VALUES
  ('BC', '2027-09-30', 'National Day for Truth and Reconciliation', 2027, TRUE),
  ('MB', '2027-09-30', 'National Day for Truth and Reconciliation', 2027, TRUE),
  ('NU', '2027-09-30', 'National Day for Truth and Reconciliation', 2027, TRUE),
  ('PE', '2027-09-30', 'National Day for Truth and Reconciliation', 2027, TRUE),
  ('YT', '2027-09-30', 'National Day for Truth and Reconciliation', 2027, TRUE),
  ('AB', '2027-09-30', 'National Day for Truth and Reconciliation', 2027, FALSE);

-- Thanksgiving - Oct 11, 2027
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

-- Remembrance Day - Nov 11, 2027
INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory) VALUES
  ('AB', '2027-11-11', 'Remembrance Day', 2027, TRUE),
  ('BC', '2027-11-11', 'Remembrance Day', 2027, TRUE),
  ('NL', '2027-11-11', 'Remembrance Day', 2027, TRUE),
  ('NT', '2027-11-11', 'Remembrance Day', 2027, TRUE),
  ('NU', '2027-11-11', 'Remembrance Day', 2027, TRUE),
  ('PE', '2027-11-11', 'Remembrance Day', 2027, TRUE),
  ('SK', '2027-11-11', 'Remembrance Day', 2027, TRUE),
  ('YT', '2027-11-11', 'Remembrance Day', 2027, TRUE);

-- Christmas Day - Dec 25, 2027 (All provinces)
INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory) VALUES
  ('AB', '2027-12-25', 'Christmas Day', 2027, TRUE),
  ('BC', '2027-12-25', 'Christmas Day', 2027, TRUE),
  ('MB', '2027-12-25', 'Christmas Day', 2027, TRUE),
  ('NB', '2027-12-25', 'Christmas Day', 2027, TRUE),
  ('NL', '2027-12-25', 'Christmas Day', 2027, TRUE),
  ('NS', '2027-12-25', 'Christmas Day', 2027, TRUE),
  ('NT', '2027-12-25', 'Christmas Day', 2027, TRUE),
  ('NU', '2027-12-25', 'Christmas Day', 2027, TRUE),
  ('ON', '2027-12-25', 'Christmas Day', 2027, TRUE),
  ('PE', '2027-12-25', 'Christmas Day', 2027, TRUE),
  ('SK', '2027-12-25', 'Christmas Day', 2027, TRUE),
  ('YT', '2027-12-25', 'Christmas Day', 2027, TRUE);

-- Boxing Day - Dec 26, 2027 (ON statutory, AB optional)
INSERT INTO statutory_holidays (province, holiday_date, name, year, is_statutory) VALUES
  ('ON', '2027-12-26', 'Boxing Day', 2027, TRUE),
  ('AB', '2027-12-26', 'Boxing Day', 2027, FALSE);
