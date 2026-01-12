-- =============================================================================
-- MIGRATION: UPDATE SUPPORT TICKETS WITH PRODUCT AND VISIBILITY
-- =============================================================================
-- Description: Adds product selection and public visibility to tickets
-- =============================================================================

-- 1. Add columns with defaults and constraints
ALTER TABLE support_tickets 
ADD COLUMN IF NOT EXISTS product TEXT DEFAULT 'payroll' CHECK (product IN ('payroll', 'bookkeeping')),
ADD COLUMN IF NOT EXISTS is_public BOOLEAN DEFAULT FALSE;

-- 2. Add performance indexes
CREATE INDEX IF NOT EXISTS idx_tickets_product ON support_tickets(product);
CREATE INDEX IF NOT EXISTS idx_tickets_is_public ON support_tickets(is_public);

-- 3. Update RLS policies for SELECT
-- We need to allow public tickets to be viewed by anyone (even unauthenticated users)
-- if they are marked as public.

DROP POLICY IF EXISTS "Users can view own tickets or admin can view all" ON support_tickets;

CREATE POLICY "Users can view own, admin all, or anyone public tickets" ON support_tickets
    FOR SELECT USING (
        (auth.uid()::text = user_id) 
        OR is_admin() 
        OR (is_public = TRUE)
    );

-- 4. Update RLS policies for SELECT on ticket_attachments
DROP POLICY IF EXISTS "Users can view own ticket attachments or admin can view all" ON ticket_attachments;

CREATE POLICY "Users can view attachments for own, admin all, or public tickets" ON ticket_attachments
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM support_tickets 
            WHERE id = ticket_attachments.ticket_id 
            AND (user_id = auth.uid()::text OR is_admin() OR is_public = TRUE)
        )
    );

-- 5. Update RLS policies for SELECT on ticket_replies
DROP POLICY IF EXISTS "Users can view replies on own tickets or admin can view all" ON ticket_replies;

CREATE POLICY "Users can view replies for own, admin all, or public tickets" ON ticket_replies
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM support_tickets 
            WHERE id = ticket_replies.ticket_id 
            AND (user_id = auth.uid()::text OR is_admin() OR is_public = TRUE)
        )
    );

-- Log the change
COMMENT ON COLUMN support_tickets.product IS 'Product category for the ticket (payroll, bookkeeping)';
COMMENT ON COLUMN support_tickets.is_public IS 'Whether the ticket is visible to everyone';
