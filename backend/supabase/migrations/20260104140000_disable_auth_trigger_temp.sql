-- Migration: Temporarily disable auth user trigger for debugging
-- Purpose: Test if the trigger is causing "Database error saving new user"
-- Date: 2026-01-04

-- Disable the trigger
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

-- NOTE: To re-enable, run:
-- CREATE TRIGGER on_auth_user_created
--     AFTER INSERT ON auth.users
--     FOR EACH ROW
--     EXECUTE FUNCTION handle_new_user();
