-- Support Ticket System Tables
-- Migration: 20260102200000_add_ticket_tables.sql

-- =============================================================================
-- Main Tickets Table
-- =============================================================================
CREATE TABLE support_tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,           -- Submitter (Supabase Auth UID)
    company_id UUID REFERENCES companies(id),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'resolved', 'closed')),
    priority TEXT DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE support_tickets IS 'Support tickets submitted by users';
COMMENT ON COLUMN support_tickets.user_id IS 'Supabase Auth user ID of ticket submitter';
COMMENT ON COLUMN support_tickets.status IS 'Ticket status: open, in_progress, resolved, closed';
COMMENT ON COLUMN support_tickets.priority IS 'Ticket priority: low, normal, high, urgent';

-- =============================================================================
-- Ticket Attachments Table (Images)
-- =============================================================================
CREATE TABLE ticket_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id UUID NOT NULL REFERENCES support_tickets(id) ON DELETE CASCADE,
    file_name TEXT NOT NULL,
    storage_key TEXT NOT NULL,       -- Supabase Storage key
    file_size INTEGER,
    mime_type TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE ticket_attachments IS 'File attachments for support tickets';
COMMENT ON COLUMN ticket_attachments.storage_key IS 'Supabase Storage key for file retrieval';

-- =============================================================================
-- Ticket Replies Table
-- =============================================================================
CREATE TABLE ticket_replies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id UUID NOT NULL REFERENCES support_tickets(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,
    is_staff BOOLEAN DEFAULT FALSE,  -- Distinguish user vs admin replies
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE ticket_replies IS 'Replies/comments on support tickets';
COMMENT ON COLUMN ticket_replies.is_staff IS 'TRUE if reply is from support staff';

-- =============================================================================
-- Indexes
-- =============================================================================
CREATE INDEX idx_tickets_user_id ON support_tickets(user_id);
CREATE INDEX idx_tickets_company_id ON support_tickets(company_id);
CREATE INDEX idx_tickets_status ON support_tickets(status);
CREATE INDEX idx_tickets_created_at ON support_tickets(created_at DESC);

CREATE INDEX idx_ticket_attachments_ticket_id ON ticket_attachments(ticket_id);
CREATE INDEX idx_ticket_replies_ticket_id ON ticket_replies(ticket_id);
CREATE INDEX idx_ticket_replies_created_at ON ticket_replies(created_at);

-- =============================================================================
-- RLS Policies
-- =============================================================================

-- Enable RLS
ALTER TABLE support_tickets ENABLE ROW LEVEL SECURITY;
ALTER TABLE ticket_attachments ENABLE ROW LEVEL SECURITY;
ALTER TABLE ticket_replies ENABLE ROW LEVEL SECURITY;

-- Support Tickets Policies
CREATE POLICY "Users can view own tickets" ON support_tickets
    FOR SELECT USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert own tickets" ON support_tickets
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can update own tickets" ON support_tickets
    FOR UPDATE USING (auth.uid()::text = user_id);

-- Ticket Attachments Policies (inherit from parent ticket)
CREATE POLICY "Users can view own ticket attachments" ON ticket_attachments
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM support_tickets
            WHERE id = ticket_attachments.ticket_id
            AND user_id = auth.uid()::text
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

CREATE POLICY "Users can delete own ticket attachments" ON ticket_attachments
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM support_tickets
            WHERE id = ticket_attachments.ticket_id
            AND user_id = auth.uid()::text
        )
    );

-- Ticket Replies Policies (inherit from parent ticket)
CREATE POLICY "Users can view replies on own tickets" ON ticket_replies
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM support_tickets
            WHERE id = ticket_replies.ticket_id
            AND user_id = auth.uid()::text
        )
    );

CREATE POLICY "Users can insert replies on own tickets" ON ticket_replies
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM support_tickets
            WHERE id = ticket_replies.ticket_id
            AND user_id = auth.uid()::text
        )
    );

-- =============================================================================
-- Updated At Trigger
-- =============================================================================
CREATE OR REPLACE FUNCTION update_support_ticket_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_support_ticket_updated_at
    BEFORE UPDATE ON support_tickets
    FOR EACH ROW
    EXECUTE FUNCTION update_support_ticket_updated_at();

-- Also update ticket updated_at when a reply is added
CREATE OR REPLACE FUNCTION update_ticket_on_reply()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE support_tickets
    SET updated_at = NOW()
    WHERE id = NEW.ticket_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_ticket_on_reply
    AFTER INSERT ON ticket_replies
    FOR EACH ROW
    EXECUTE FUNCTION update_ticket_on_reply();

-- =============================================================================
-- Storage Bucket for Ticket Attachments
-- =============================================================================
-- Note: Run this in Supabase Dashboard SQL Editor or via storage API
-- INSERT INTO storage.buckets (id, name, public)
-- VALUES ('ticket-attachments', 'ticket-attachments', false)
-- ON CONFLICT DO NOTHING;
