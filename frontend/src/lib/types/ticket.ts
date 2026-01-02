/**
 * Support Ticket System - Type Definitions
 *
 * Types for support ticket management using Supabase directly.
 */

// =============================================================================
// Enums and Constants
// =============================================================================

export type TicketStatus = 'open' | 'in_progress' | 'resolved' | 'closed';
export type TicketPriority = 'low' | 'normal' | 'high' | 'urgent';

/**
 * Status display configuration
 */
export const TICKET_STATUS_INFO: Record<
	TicketStatus,
	{ label: string; icon: string; colorClass: string }
> = {
	open: {
		label: 'Open',
		icon: 'fa-circle-dot',
		colorClass: 'bg-primary-100 text-primary-700'
	},
	in_progress: {
		label: 'In Progress',
		icon: 'fa-spinner',
		colorClass: 'bg-warning-100 text-warning-700'
	},
	resolved: {
		label: 'Resolved',
		icon: 'fa-check-circle',
		colorClass: 'bg-success-100 text-success-700'
	},
	closed: {
		label: 'Closed',
		icon: 'fa-times-circle',
		colorClass: 'bg-surface-100 text-surface-600'
	}
};

/**
 * Priority display configuration
 */
export const TICKET_PRIORITY_INFO: Record<
	TicketPriority,
	{ label: string; icon: string; colorClass: string }
> = {
	low: {
		label: 'Low',
		icon: 'fa-arrow-down',
		colorClass: 'bg-surface-100 text-surface-600'
	},
	normal: {
		label: 'Normal',
		icon: 'fa-minus',
		colorClass: 'bg-primary-100 text-primary-700'
	},
	high: {
		label: 'High',
		icon: 'fa-arrow-up',
		colorClass: 'bg-warning-100 text-warning-700'
	},
	urgent: {
		label: 'Urgent',
		icon: 'fa-exclamation',
		colorClass: 'bg-error-100 text-error-700'
	}
};

// =============================================================================
// Database Models (snake_case - matching Supabase)
// =============================================================================

/**
 * Support ticket from database
 */
export interface TicketDB {
	id: string;
	user_id: string;
	company_id: string | null;
	title: string;
	description: string;
	status: TicketStatus;
	priority: TicketPriority;
	created_at: string;
	updated_at: string;
}

/**
 * Ticket attachment from database
 */
export interface TicketAttachmentDB {
	id: string;
	ticket_id: string;
	file_name: string;
	storage_key: string;
	file_size: number | null;
	mime_type: string | null;
	created_at: string;
}

/**
 * Ticket reply from database
 */
export interface TicketReplyDB {
	id: string;
	ticket_id: string;
	user_id: string;
	is_staff: boolean;
	content: string;
	created_at: string;
}

// =============================================================================
// Frontend Models (camelCase - for UI)
// =============================================================================

/**
 * Support ticket for UI
 */
export interface Ticket {
	id: string;
	userId: string;
	companyId: string | null;
	title: string;
	description: string;
	status: TicketStatus;
	priority: TicketPriority;
	createdAt: string;
	updatedAt: string;
	// Optional relations
	attachments?: TicketAttachment[];
	replies?: TicketReply[];
	replyCount?: number;
}

/**
 * Ticket attachment for UI
 */
export interface TicketAttachment {
	id: string;
	ticketId: string;
	fileName: string;
	storageKey: string;
	fileSize: number | null;
	mimeType: string | null;
	createdAt: string;
	// Computed
	url?: string;
}

/**
 * Ticket reply for UI
 */
export interface TicketReply {
	id: string;
	ticketId: string;
	userId: string;
	isStaff: boolean;
	content: string;
	createdAt: string;
}

// =============================================================================
// Request Types
// =============================================================================

/**
 * Create ticket request
 */
export interface TicketCreateInput {
	title: string;
	description: string;
	priority?: TicketPriority;
}

/**
 * Create reply request
 */
export interface TicketReplyInput {
	content: string;
}

/**
 * Pending attachment (before ticket is created)
 */
export interface PendingAttachment {
	file: File;
	preview: string;
	uploading?: boolean;
	error?: string;
}

// =============================================================================
// Conversion Utilities
// =============================================================================

/**
 * Convert database ticket to frontend model
 */
export function ticketFromDB(db: TicketDB): Ticket {
	return {
		id: db.id,
		userId: db.user_id,
		companyId: db.company_id,
		title: db.title,
		description: db.description,
		status: db.status,
		priority: db.priority,
		createdAt: db.created_at,
		updatedAt: db.updated_at
	};
}

/**
 * Convert database attachment to frontend model
 */
export function attachmentFromDB(db: TicketAttachmentDB): TicketAttachment {
	return {
		id: db.id,
		ticketId: db.ticket_id,
		fileName: db.file_name,
		storageKey: db.storage_key,
		fileSize: db.file_size,
		mimeType: db.mime_type,
		createdAt: db.created_at
	};
}

/**
 * Convert database reply to frontend model
 */
export function replyFromDB(db: TicketReplyDB): TicketReply {
	return {
		id: db.id,
		ticketId: db.ticket_id,
		userId: db.user_id,
		isStaff: db.is_staff,
		content: db.content,
		createdAt: db.created_at
	};
}
