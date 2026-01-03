-- Migration: Re-enable auth user trigger
-- Date: 2026-01-04

-- Re-enable the trigger
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION handle_new_user();
