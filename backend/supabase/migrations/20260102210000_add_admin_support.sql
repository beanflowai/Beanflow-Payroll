-- Admin Support for Ticket System
-- Migration: 20260102210000_add_admin_support.sql

-- =============================================================================
-- User Profiles Table (for admin flag)
-- =============================================================================
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT,
    full_name TEXT,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE user_profiles IS 'Extended user profile with admin flag';
COMMENT ON COLUMN user_profiles.is_admin IS 'TRUE if user is a platform admin';

-- Index for admin lookups
CREATE INDEX idx_user_profiles_is_admin ON user_profiles(is_admin) WHERE is_admin = TRUE;

-- RLS for user_profiles
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- Users can read their own profile
CREATE POLICY "Users can view own profile" ON user_profiles
    FOR SELECT USING (auth.uid() = id);

-- Users can update their own profile
CREATE POLICY "Users can update own profile" ON user_profiles
    FOR UPDATE USING (auth.uid() = id);

-- =============================================================================
-- Trigger: Prevent is_admin changes via API
-- Only direct DB access (service role) can change is_admin
-- =============================================================================
CREATE OR REPLACE FUNCTION prevent_is_admin_change()
RETURNS TRIGGER AS $$
BEGIN
    -- If is_admin is being changed, block it
    IF OLD.is_admin IS DISTINCT FROM NEW.is_admin THEN
        RAISE EXCEPTION 'Cannot modify is_admin field. Admin status can only be changed via direct database access.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER enforce_is_admin_immutable
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW
    WHEN (OLD.is_admin IS DISTINCT FROM NEW.is_admin)
    EXECUTE FUNCTION prevent_is_admin_change();

-- =============================================================================
-- Helper Function: Check if current user is admin
-- =============================================================================
CREATE OR REPLACE FUNCTION is_admin()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM user_profiles
        WHERE id = auth.uid()
        AND is_admin = TRUE
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER STABLE;

COMMENT ON FUNCTION is_admin() IS 'Returns TRUE if current user is an admin';

-- =============================================================================
-- Update Ticket RLS Policies for Admin Access
-- =============================================================================

-- Drop existing policies
DROP POLICY IF EXISTS "Users can view own tickets" ON support_tickets;
DROP POLICY IF EXISTS "Users can insert own tickets" ON support_tickets;
DROP POLICY IF EXISTS "Users can update own tickets" ON support_tickets;

-- Recreate with admin access
CREATE POLICY "Users can view own tickets or admin can view all" ON support_tickets
    FOR SELECT USING (
        auth.uid()::text = user_id
        OR is_admin()
    );

CREATE POLICY "Users can insert own tickets" ON support_tickets
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can update own tickets or admin can update all" ON support_tickets
    FOR UPDATE
    USING (
        auth.uid()::text = user_id
        OR is_admin()
    )
    WITH CHECK (
        -- Ensure user_id matches original owner (enforced via trigger below)
        -- WITH CHECK validates the NEW row - we use trigger to compare with OLD
        auth.uid()::text = user_id
        OR is_admin()
    );

-- =============================================================================
-- Trigger: Prevent user_id changes on support_tickets
-- This prevents ownership transfer attacks where a user changes user_id to another user
-- =============================================================================
CREATE OR REPLACE FUNCTION prevent_ticket_user_id_change()
RETURNS TRIGGER AS $$
BEGIN
    -- If user_id is being changed, block it
    IF OLD.user_id IS DISTINCT FROM NEW.user_id THEN
        RAISE EXCEPTION 'Cannot modify ticket owner. Ticket ownership cannot be transferred.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER enforce_ticket_user_id_immutable
    BEFORE UPDATE ON support_tickets
    FOR EACH ROW
    WHEN (OLD.user_id IS DISTINCT FROM NEW.user_id)
    EXECUTE FUNCTION prevent_ticket_user_id_change();

-- =============================================================================
-- Update Ticket Attachments RLS for Admin Access
-- =============================================================================

DROP POLICY IF EXISTS "Users can view own ticket attachments" ON ticket_attachments;
DROP POLICY IF EXISTS "Users can insert attachments for own tickets" ON ticket_attachments;

CREATE POLICY "Users can view own ticket attachments or admin can view all" ON ticket_attachments
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM support_tickets
            WHERE id = ticket_attachments.ticket_id
            AND (user_id = auth.uid()::text OR is_admin())
        )
    );

CREATE POLICY "Users can insert attachments for own tickets" ON ticket_attachments
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM support_tickets
            WHERE id = ticket_attachments.ticket_id
            AND user_id = auth.uid()::text
        )
    );

-- =============================================================================
-- Update Ticket Replies RLS for Admin Access
-- =============================================================================

DROP POLICY IF EXISTS "Users can view replies on own tickets" ON ticket_replies;
DROP POLICY IF EXISTS "Users can insert replies on own tickets" ON ticket_replies;

CREATE POLICY "Users can view replies on own tickets or admin can view all" ON ticket_replies
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM support_tickets
            WHERE id = ticket_replies.ticket_id
            AND (user_id = auth.uid()::text OR is_admin())
        )
    );

-- Users can reply to their own tickets, admins can reply to any ticket
CREATE POLICY "Users can insert replies on own tickets or admin on any" ON ticket_replies
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM support_tickets
            WHERE id = ticket_replies.ticket_id
            AND (user_id = auth.uid()::text OR is_admin())
        )
    );

-- =============================================================================
-- Auto-create user profile on first sign-in
-- =============================================================================
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO user_profiles (id, email, full_name, is_admin)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.raw_user_meta_data->>'name', ''),
        FALSE
    )
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to auto-create profile
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION handle_new_user();

-- =============================================================================
-- Seed: Make current test users admin (adjust as needed)
-- You can manually set admin status:
-- UPDATE user_profiles SET is_admin = TRUE WHERE email = 'your@email.com';
-- =============================================================================
