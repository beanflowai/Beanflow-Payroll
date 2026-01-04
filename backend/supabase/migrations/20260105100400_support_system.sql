-- =============================================================================
-- CONSOLIDATED MIGRATION 005: SUPPORT SYSTEM
-- =============================================================================
-- Description: User profiles, support tickets, and admin functionality
-- =============================================================================

-- =============================================================================
-- USER PROFILES TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT,
    full_name TEXT,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_user_profiles_is_admin ON user_profiles(is_admin) WHERE is_admin = TRUE;

ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own profile" ON user_profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON user_profiles FOR UPDATE USING (auth.uid() = id);

-- Prevent is_admin changes via API
CREATE OR REPLACE FUNCTION prevent_is_admin_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.is_admin IS DISTINCT FROM NEW.is_admin THEN
        RAISE EXCEPTION 'Cannot modify is_admin field. Admin status can only be changed via direct database access.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER enforce_is_admin_immutable
    BEFORE UPDATE ON user_profiles FOR EACH ROW
    WHEN (OLD.is_admin IS DISTINCT FROM NEW.is_admin)
    EXECUTE FUNCTION prevent_is_admin_change();

-- is_admin helper function
CREATE OR REPLACE FUNCTION is_admin()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (SELECT 1 FROM user_profiles WHERE id = auth.uid() AND is_admin = TRUE);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER STABLE;

COMMENT ON FUNCTION is_admin() IS 'Returns TRUE if current user is an admin';

-- Auto-create profile on signup (with exception handling)
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
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users FOR EACH ROW
    EXECUTE FUNCTION handle_new_user();

COMMENT ON TABLE user_profiles IS 'Extended user profile with admin flag';

-- =============================================================================
-- SUPPORT TICKETS TABLE
-- =============================================================================

CREATE TABLE support_tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    company_id UUID REFERENCES companies(id),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'resolved', 'closed')),
    priority TEXT DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_tickets_user_id ON support_tickets(user_id);
CREATE INDEX idx_tickets_company_id ON support_tickets(company_id);
CREATE INDEX idx_tickets_status ON support_tickets(status);
CREATE INDEX idx_tickets_created_at ON support_tickets(created_at DESC);

ALTER TABLE support_tickets ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own tickets or admin can view all" ON support_tickets
    FOR SELECT USING (auth.uid()::text = user_id OR is_admin());

CREATE POLICY "Users can insert own tickets" ON support_tickets
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can update own tickets or admin can update all" ON support_tickets
    FOR UPDATE USING (auth.uid()::text = user_id OR is_admin())
    WITH CHECK (auth.uid()::text = user_id OR is_admin());

-- Prevent ownership transfer
CREATE OR REPLACE FUNCTION prevent_ticket_user_id_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.user_id IS DISTINCT FROM NEW.user_id THEN
        RAISE EXCEPTION 'Cannot modify ticket owner. Ticket ownership cannot be transferred.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER enforce_ticket_user_id_immutable
    BEFORE UPDATE ON support_tickets FOR EACH ROW
    WHEN (OLD.user_id IS DISTINCT FROM NEW.user_id)
    EXECUTE FUNCTION prevent_ticket_user_id_change();

CREATE OR REPLACE FUNCTION update_support_ticket_updated_at()
RETURNS TRIGGER AS $$ BEGIN NEW.updated_at = NOW(); RETURN NEW; END; $$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_support_ticket_updated_at
    BEFORE UPDATE ON support_tickets FOR EACH ROW
    EXECUTE FUNCTION update_support_ticket_updated_at();

COMMENT ON TABLE support_tickets IS 'Support tickets submitted by users';

-- =============================================================================
-- TICKET ATTACHMENTS TABLE
-- =============================================================================

CREATE TABLE ticket_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id UUID NOT NULL REFERENCES support_tickets(id) ON DELETE CASCADE,
    file_name TEXT NOT NULL,
    storage_key TEXT NOT NULL,
    file_size INTEGER,
    mime_type TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_ticket_attachments_ticket_id ON ticket_attachments(ticket_id);

ALTER TABLE ticket_attachments ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own ticket attachments or admin can view all" ON ticket_attachments
    FOR SELECT USING (
        EXISTS (SELECT 1 FROM support_tickets WHERE id = ticket_attachments.ticket_id AND (user_id = auth.uid()::text OR is_admin()))
    );

CREATE POLICY "Users can insert attachments for own tickets" ON ticket_attachments
    FOR INSERT WITH CHECK (
        EXISTS (SELECT 1 FROM support_tickets WHERE id = ticket_attachments.ticket_id AND user_id = auth.uid()::text)
    );

CREATE POLICY "Users can delete own ticket attachments" ON ticket_attachments
    FOR DELETE USING (
        EXISTS (SELECT 1 FROM support_tickets WHERE id = ticket_attachments.ticket_id AND user_id = auth.uid()::text)
    );

COMMENT ON TABLE ticket_attachments IS 'File attachments for support tickets';

-- =============================================================================
-- TICKET REPLIES TABLE
-- =============================================================================

CREATE TABLE ticket_replies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id UUID NOT NULL REFERENCES support_tickets(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,
    is_staff BOOLEAN DEFAULT FALSE,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_ticket_replies_ticket_id ON ticket_replies(ticket_id);
CREATE INDEX idx_ticket_replies_created_at ON ticket_replies(created_at);

ALTER TABLE ticket_replies ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view replies on own tickets or admin can view all" ON ticket_replies
    FOR SELECT USING (
        EXISTS (SELECT 1 FROM support_tickets WHERE id = ticket_replies.ticket_id AND (user_id = auth.uid()::text OR is_admin()))
    );

CREATE POLICY "Users can insert replies on own tickets or admin on any" ON ticket_replies
    FOR INSERT WITH CHECK (
        EXISTS (SELECT 1 FROM support_tickets WHERE id = ticket_replies.ticket_id AND (user_id = auth.uid()::text OR is_admin()))
    );

-- Update ticket updated_at when reply is added
CREATE OR REPLACE FUNCTION update_ticket_on_reply()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE support_tickets SET updated_at = NOW() WHERE id = NEW.ticket_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_ticket_on_reply
    AFTER INSERT ON ticket_replies FOR EACH ROW
    EXECUTE FUNCTION update_ticket_on_reply();

COMMENT ON TABLE ticket_replies IS 'Replies/comments on support tickets';
