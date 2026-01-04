/**
 * Support Ticket Service - Supabase Operations
 *
 * Handles all ticket-related operations directly with Supabase.
 */

import { supabase } from '$lib/api/supabase';
import type {
	Ticket,
	TicketAttachment,
	TicketReply,
	TicketDB,
	TicketAttachmentDB,
	TicketReplyDB,
	TicketCreateInput,
	TicketStatus
} from '$lib/types/ticket';
import {
	ticketFromDB as convertTicket,
	attachmentFromDB as convertAttachment,
	replyFromDB as convertReply
} from '$lib/types/ticket';

// Storage bucket name
const STORAGE_BUCKET = 'ticket-attachments';

// Allowed file types
const ALLOWED_MIME_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB
const MAX_ATTACHMENTS_PER_TICKET = 5;

// =============================================================================
// Ticket Operations
// =============================================================================

/**
 * Get all tickets for the current user
 */
export async function getTickets(status?: TicketStatus): Promise<Ticket[]> {
	let query = supabase
		.from('support_tickets')
		.select(
			`
			*,
			ticket_attachments(count),
			ticket_replies(count)
		`
		)
		.order('created_at', { ascending: false });

	if (status) {
		query = query.eq('status', status);
	}

	const { data, error } = await query;

	if (error) {
		console.error('Error fetching tickets:', error);
		throw new Error(`Failed to fetch tickets: ${error.message}`);
	}

	return (data || []).map(
		(
			row: TicketDB & {
				ticket_attachments: { count: number }[];
				ticket_replies: { count: number }[];
			}
		) => ({
			...convertTicket(row),
			replyCount: row.ticket_replies?.[0]?.count || 0
		})
	);
}

/**
 * Get a single ticket with attachments and replies
 */
export async function getTicket(ticketId: string): Promise<Ticket | null> {
	const { data, error } = await supabase
		.from('support_tickets')
		.select(
			`
			*,
			ticket_attachments(*),
			ticket_replies(*)
		`
		)
		.eq('id', ticketId)
		.single();

	if (error) {
		if (error.code === 'PGRST116') {
			return null; // Not found
		}
		console.error('Error fetching ticket:', error);
		throw new Error(`Failed to fetch ticket: ${error.message}`);
	}

	if (!data) return null;

	const ticket = convertTicket(data as TicketDB);

	// Convert attachments and add signed URLs
	const attachments: TicketAttachment[] = await Promise.all(
		((data.ticket_attachments as TicketAttachmentDB[]) || []).map(async (att) => {
			const attachment = convertAttachment(att);
			attachment.url = await getAttachmentUrl(attachment.storageKey);
			return attachment;
		})
	);

	// Convert replies and sort by date
	const replies: TicketReply[] = ((data.ticket_replies as TicketReplyDB[]) || [])
		.map((r) => convertReply(r))
		.sort((a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime());

	return {
		...ticket,
		attachments,
		replies,
		replyCount: replies.length
	};
}

/**
 * Create a new ticket
 */
export async function createTicket(input: TicketCreateInput, companyId?: string): Promise<Ticket> {
	const {
		data: { user }
	} = await supabase.auth.getUser();

	if (!user) {
		throw new Error('User not authenticated');
	}

	const { data, error } = await supabase
		.from('support_tickets')
		.insert({
			user_id: user.id,
			company_id: companyId || null,
			title: input.title,
			description: input.description,
			priority: input.priority || 'normal',
			status: 'open'
		})
		.select()
		.single();

	if (error) {
		console.error('Error creating ticket:', error);
		throw new Error(`Failed to create ticket: ${error.message}`);
	}

	return convertTicket(data as TicketDB);
}

// =============================================================================
// Attachment Operations
// =============================================================================

/**
 * Upload an attachment for a ticket
 */
export async function uploadAttachment(ticketId: string, file: File): Promise<TicketAttachment> {
	// Validate file
	if (!ALLOWED_MIME_TYPES.includes(file.type)) {
		throw new Error(`File type ${file.type} is not allowed. Allowed types: JPEG, PNG, GIF, WebP`);
	}

	if (file.size > MAX_FILE_SIZE) {
		throw new Error(`File size exceeds ${MAX_FILE_SIZE / 1024 / 1024}MB limit`);
	}

	// Check existing attachments count
	const { count, error: countError } = await supabase
		.from('ticket_attachments')
		.select('*', { count: 'exact', head: true })
		.eq('ticket_id', ticketId);

	if (countError) {
		throw new Error(`Failed to check attachments: ${countError.message}`);
	}

	if ((count || 0) >= MAX_ATTACHMENTS_PER_TICKET) {
		throw new Error(`Maximum ${MAX_ATTACHMENTS_PER_TICKET} attachments per ticket`);
	}

	const {
		data: { user }
	} = await supabase.auth.getUser();

	if (!user) {
		throw new Error('User not authenticated');
	}

	// Generate unique filename
	const timestamp = Date.now();
	const safeFileName = file.name.replace(/[^a-zA-Z0-9.-]/g, '_');
	const storageKey = `${user.id}/${ticketId}/${timestamp}_${safeFileName}`;

	// Upload to storage
	const { error: uploadError } = await supabase.storage
		.from(STORAGE_BUCKET)
		.upload(storageKey, file, {
			cacheControl: '3600',
			upsert: false
		});

	if (uploadError) {
		console.error('Error uploading file:', uploadError);
		throw new Error(`Failed to upload file: ${uploadError.message}`);
	}

	// Create attachment record
	const { data, error: insertError } = await supabase
		.from('ticket_attachments')
		.insert({
			ticket_id: ticketId,
			file_name: file.name,
			storage_key: storageKey,
			file_size: file.size,
			mime_type: file.type
		})
		.select()
		.single();

	if (insertError) {
		// Try to clean up uploaded file
		await supabase.storage.from(STORAGE_BUCKET).remove([storageKey]);
		throw new Error(`Failed to save attachment: ${insertError.message}`);
	}

	const attachment = convertAttachment(data as TicketAttachmentDB);
	attachment.url = await getAttachmentUrl(storageKey);

	return attachment;
}

/**
 * Get signed URL for an attachment
 */
export async function getAttachmentUrl(storageKey: string): Promise<string | undefined> {
	const { data, error } = await supabase.storage
		.from(STORAGE_BUCKET)
		.createSignedUrl(storageKey, 3600); // 1 hour expiry

	if (error) {
		console.error('Error getting signed URL:', error);
		return undefined;
	}

	return data.signedUrl;
}

/**
 * Delete an attachment
 */
export async function deleteAttachment(attachmentId: string): Promise<void> {
	// Get attachment to find storage key
	const { data: attachment, error: fetchError } = await supabase
		.from('ticket_attachments')
		.select('storage_key')
		.eq('id', attachmentId)
		.single();

	if (fetchError) {
		throw new Error(`Failed to find attachment: ${fetchError.message}`);
	}

	// Delete from storage
	const { error: storageError } = await supabase.storage
		.from(STORAGE_BUCKET)
		.remove([attachment.storage_key]);

	if (storageError) {
		console.error('Error deleting from storage:', storageError);
		// Continue to delete record even if storage deletion fails
	}

	// Delete record
	const { error: deleteError } = await supabase
		.from('ticket_attachments')
		.delete()
		.eq('id', attachmentId);

	if (deleteError) {
		throw new Error(`Failed to delete attachment: ${deleteError.message}`);
	}
}

// =============================================================================
// Reply Operations
// =============================================================================

/**
 * Add a reply to a ticket
 */
export async function addReply(ticketId: string, content: string): Promise<TicketReply> {
	const {
		data: { user }
	} = await supabase.auth.getUser();

	if (!user) {
		throw new Error('User not authenticated');
	}

	const { data, error } = await supabase
		.from('ticket_replies')
		.insert({
			ticket_id: ticketId,
			user_id: user.id,
			content: content.trim(),
			is_staff: false // Regular users are not staff
		})
		.select()
		.single();

	if (error) {
		console.error('Error adding reply:', error);
		throw new Error(`Failed to add reply: ${error.message}`);
	}

	return convertReply(data as TicketReplyDB);
}

// =============================================================================
// Utility Functions
// =============================================================================

/**
 * Format file size for display
 */
export function formatFileSize(bytes: number | null): string {
	if (bytes === null) return 'Unknown size';
	if (bytes < 1024) return `${bytes} B`;
	if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
	return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/**
 * Check if a file is an allowed image type
 */
export function isAllowedFileType(file: File): boolean {
	return ALLOWED_MIME_TYPES.includes(file.type);
}

/**
 * Check if a file is within size limit
 */
export function isWithinSizeLimit(file: File): boolean {
	return file.size <= MAX_FILE_SIZE;
}

/**
 * Get validation error for a file
 */
export function getFileValidationError(file: File): string | null {
	if (!isAllowedFileType(file)) {
		return `File type not allowed. Accepted: JPEG, PNG, GIF, WebP`;
	}
	if (!isWithinSizeLimit(file)) {
		return `File too large. Maximum size: ${MAX_FILE_SIZE / 1024 / 1024}MB`;
	}
	return null;
}

// =============================================================================
// Admin Operations
// =============================================================================

/**
 * Check if current user is an admin
 */
export async function checkIsAdmin(): Promise<boolean> {
	const {
		data: { user }
	} = await supabase.auth.getUser();

	if (!user) {
		return false;
	}

	const { data, error } = await supabase
		.from('user_profiles')
		.select('is_admin')
		.eq('id', user.id)
		.single();

	if (error || !data) {
		return false;
	}

	return data.is_admin === true;
}

/**
 * Update ticket status (admin only)
 */
export async function updateTicketStatus(ticketId: string, status: TicketStatus): Promise<Ticket> {
	const { data, error } = await supabase
		.from('support_tickets')
		.update({ status })
		.eq('id', ticketId)
		.select()
		.single();

	if (error) {
		console.error('Error updating ticket status:', error);
		throw new Error(`Failed to update ticket status: ${error.message}`);
	}

	return convertTicket(data as TicketDB);
}

/**
 * Add a staff reply to a ticket (admin only)
 */
export async function addStaffReply(ticketId: string, content: string): Promise<TicketReply> {
	const {
		data: { user }
	} = await supabase.auth.getUser();

	if (!user) {
		throw new Error('User not authenticated');
	}

	const { data, error } = await supabase
		.from('ticket_replies')
		.insert({
			ticket_id: ticketId,
			user_id: user.id,
			content: content.trim(),
			is_staff: true // Staff reply
		})
		.select()
		.single();

	if (error) {
		console.error('Error adding staff reply:', error);
		throw new Error(`Failed to add reply: ${error.message}`);
	}

	return convertReply(data as TicketReplyDB);
}

/**
 * Get ticket statistics for admin dashboard
 */
export async function getTicketStats(): Promise<{
	total: number;
	open: number;
	inProgress: number;
	resolved: number;
	closed: number;
}> {
	const { data, error } = await supabase.from('support_tickets').select('status');

	if (error) {
		console.error('Error fetching ticket stats:', error);
		throw new Error(`Failed to fetch ticket stats: ${error.message}`);
	}

	const stats = {
		total: data?.length || 0,
		open: 0,
		inProgress: 0,
		resolved: 0,
		closed: 0
	};

	data?.forEach((ticket) => {
		switch (ticket.status) {
			case 'open':
				stats.open++;
				break;
			case 'in_progress':
				stats.inProgress++;
				break;
			case 'resolved':
				stats.resolved++;
				break;
			case 'closed':
				stats.closed++;
				break;
		}
	});

	return stats;
}
