/**
 * Tests for ticketService
 */

import { describe, expect, it, vi, beforeEach } from 'vitest';

// Mock supabase
vi.mock('$lib/api/supabase', () => ({
	supabase: {
		from: vi.fn(),
		storage: {
			from: vi.fn()
		},
		auth: {
			getUser: vi.fn()
		}
	}
}));

// Mock ticket type converters
vi.mock('$lib/types/ticket', () => ({
	ticketFromDB: vi.fn((db) => ({
		id: db.id,
		userId: db.user_id,
		companyId: db.company_id,
		title: db.title,
		description: db.description,
		priority: db.priority,
		status: db.status,
		createdAt: db.created_at,
		updatedAt: db.updated_at
	})),
	attachmentFromDB: vi.fn((db) => ({
		id: db.id,
		ticketId: db.ticket_id,
		fileName: db.file_name,
		storageKey: db.storage_key,
		fileSize: db.file_size,
		mimeType: db.mime_type,
		createdAt: db.created_at
	})),
	replyFromDB: vi.fn((db) => ({
		id: db.id,
		ticketId: db.ticket_id,
		userId: db.user_id,
		content: db.content,
		isStaff: db.is_staff,
		createdAt: db.created_at
	}))
}));

import { supabase } from '$lib/api/supabase';
import {
	getTickets,
	getTicket,
	createTicket,
	uploadAttachment,
	getAttachmentUrl,
	deleteAttachment,
	addReply,
	formatFileSize,
	isAllowedFileType,
	isWithinSizeLimit,
	getFileValidationError,
	checkIsAdmin,
	updateTicketStatus,
	addStaffReply,
	getTicketStats
} from './ticketService';

const mockSupabase = vi.mocked(supabase);

// Sample DB ticket data
const sampleDbTicket = {
	id: 'ticket-123',
	user_id: 'user-456',
	company_id: 'company-789',
	title: 'Test Ticket',
	description: 'Test description',
	priority: 'normal',
	status: 'open',
	created_at: '2025-01-01T00:00:00Z',
	updated_at: '2025-01-01T00:00:00Z'
};

// Helper to create mock query builder
function createMockQueryBuilder(response: { data: unknown; error: unknown; count?: number }) {
	const builder = {
		select: vi.fn().mockReturnThis(),
		insert: vi.fn().mockReturnThis(),
		update: vi.fn().mockReturnThis(),
		delete: vi.fn().mockReturnThis(),
		eq: vi.fn().mockReturnThis(),
		order: vi.fn().mockReturnThis(),
		single: vi.fn().mockResolvedValue(response),
		then: vi.fn((resolve) => resolve(response))
	};
	return builder;
}

describe('getTickets', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('fetches all tickets', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: [
				{
					...sampleDbTicket,
					ticket_attachments: [{ count: 2 }],
					ticket_replies: [{ count: 3 }]
				}
			],
			error: null
		});
		mockBuilder.order.mockImplementation(() => ({
			...mockBuilder,
			then: (resolve: (value: unknown) => void) =>
				resolve({
					data: [
						{
							...sampleDbTicket,
							ticket_attachments: [{ count: 2 }],
							ticket_replies: [{ count: 3 }]
						}
					],
					error: null
				})
		}));
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await getTickets();

		expect(mockSupabase.from).toHaveBeenCalledWith('support_tickets');
		expect(result).toHaveLength(1);
		expect(result[0].replyCount).toBe(3);
	});

	it('filters by status', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: [],
			error: null
		});
		mockBuilder.order.mockImplementation(() => ({
			...mockBuilder,
			then: (resolve: (value: unknown) => void) => resolve({ data: [], error: null })
		}));
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		await getTickets('open');

		expect(mockBuilder.eq).toHaveBeenCalledWith('status', 'open');
	});

	it('throws on error', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: { message: 'Database error' }
		});
		mockBuilder.order.mockImplementation(() => ({
			...mockBuilder,
			then: (resolve: (value: unknown) => void) =>
				resolve({ data: null, error: { message: 'Database error' } })
		}));
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		await expect(getTickets()).rejects.toThrow('Failed to fetch tickets');
	});
});

describe('getTicket', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('fetches single ticket with attachments and replies', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: {
				...sampleDbTicket,
				ticket_attachments: [
					{
						id: 'att-1',
						ticket_id: 'ticket-123',
						file_name: 'test.png',
						storage_key: 'key-1',
						file_size: 1024,
						mime_type: 'image/png',
						created_at: '2025-01-01T00:00:00Z'
					}
				],
				ticket_replies: [
					{
						id: 'reply-1',
						ticket_id: 'ticket-123',
						user_id: 'user-456',
						content: 'Test reply',
						is_staff: false,
						created_at: '2025-01-01T00:00:00Z'
					}
				]
			},
			error: null
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		// Mock storage for signed URL
		const mockStorage = {
			createSignedUrl: vi.fn().mockResolvedValue({
				data: { signedUrl: 'https://storage.example.com/signed-url' },
				error: null
			})
		};
		mockSupabase.storage.from = vi.fn().mockReturnValue(mockStorage);

		const result = await getTicket('ticket-123');

		expect(mockSupabase.from).toHaveBeenCalledWith('support_tickets');
		expect(mockBuilder.eq).toHaveBeenCalledWith('id', 'ticket-123');
		expect(result?.id).toBe('ticket-123');
		expect(result?.attachments).toHaveLength(1);
		expect(result?.replies).toHaveLength(1);
	});

	it('returns null when ticket not found (PGRST116)', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: { code: 'PGRST116', message: 'Not found' }
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await getTicket('non-existent');

		expect(result).toBeNull();
	});

	it('throws on other errors', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: { code: 'OTHER', message: 'Database error' }
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		await expect(getTicket('ticket-123')).rejects.toThrow('Failed to fetch ticket');
	});
});

describe('createTicket', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('creates a new ticket', async () => {
		mockSupabase.auth.getUser.mockResolvedValue({
			data: { user: { id: 'user-456' } },
			error: null
		} as unknown as ReturnType<typeof supabase.auth.getUser>);

		const mockBuilder = createMockQueryBuilder({
			data: sampleDbTicket,
			error: null
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await createTicket({
			title: 'Test Ticket',
			description: 'Test description',
			priority: 'normal'
		});

		expect(mockBuilder.insert).toHaveBeenCalled();
		expect(result.id).toBe('ticket-123');
	});

	it('creates ticket with company ID', async () => {
		mockSupabase.auth.getUser.mockResolvedValue({
			data: { user: { id: 'user-456' } },
			error: null
		} as unknown as ReturnType<typeof supabase.auth.getUser>);

		const mockBuilder = createMockQueryBuilder({
			data: sampleDbTicket,
			error: null
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		await createTicket({ title: 'Test', description: 'Test' }, 'company-789');

		expect(mockBuilder.insert).toHaveBeenCalledWith(
			expect.objectContaining({
				company_id: 'company-789'
			})
		);
	});

	it('throws when not authenticated', async () => {
		mockSupabase.auth.getUser.mockResolvedValue({
			data: { user: null },
			error: null
		} as unknown as ReturnType<typeof supabase.auth.getUser>);

		await expect(
			createTicket({ title: 'Test', description: 'Test' })
		).rejects.toThrow('User not authenticated');
	});
});

describe('uploadAttachment', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('rejects non-image files', async () => {
		const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });

		await expect(uploadAttachment('ticket-123', file)).rejects.toThrow('File type');
	});

	it('rejects files larger than 5MB', async () => {
		const largeContent = new ArrayBuffer(6 * 1024 * 1024);
		const file = new File([largeContent], 'large.png', { type: 'image/png' });

		await expect(uploadAttachment('ticket-123', file)).rejects.toThrow('5MB');
	});

	it('rejects when max attachments reached', async () => {
		const file = new File(['test'], 'test.png', { type: 'image/png' });

		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: null,
			count: 5
		});
		mockBuilder.eq.mockImplementation(() => ({
			...mockBuilder,
			then: (resolve: (value: unknown) => void) => resolve({ count: 5, error: null })
		}));
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		await expect(uploadAttachment('ticket-123', file)).rejects.toThrow('Maximum 5 attachments');
	});
});

describe('getAttachmentUrl', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('returns signed URL', async () => {
		const mockStorage = {
			createSignedUrl: vi.fn().mockResolvedValue({
				data: { signedUrl: 'https://storage.example.com/signed-url' },
				error: null
			})
		};
		mockSupabase.storage.from = vi.fn().mockReturnValue(mockStorage);

		const result = await getAttachmentUrl('user-123/ticket-456/file.png');

		expect(result).toBe('https://storage.example.com/signed-url');
	});

	it('returns undefined on error', async () => {
		const mockStorage = {
			createSignedUrl: vi.fn().mockResolvedValue({
				data: null,
				error: { message: 'Not found' }
			})
		};
		mockSupabase.storage.from = vi.fn().mockReturnValue(mockStorage);

		const result = await getAttachmentUrl('invalid-key');

		expect(result).toBeUndefined();
	});
});

describe('deleteAttachment', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('deletes attachment from storage and database', async () => {
		// Mock fetch attachment to get storage key
		const mockBuilder = createMockQueryBuilder({
			data: { storage_key: 'user-123/ticket-456/file.png' },
			error: null
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		// Mock storage delete
		const mockStorage = {
			remove: vi.fn().mockResolvedValue({ error: null })
		};
		mockSupabase.storage.from = vi.fn().mockReturnValue(mockStorage);

		// Mock delete from database (second call to supabase.from)
		const deleteBuilder = createMockQueryBuilder({ data: null, error: null });
		deleteBuilder.eq.mockImplementation(() => ({
			...deleteBuilder,
			then: (resolve: (value: unknown) => void) => resolve({ error: null })
		}));

		let callCount = 0;
		mockSupabase.from.mockImplementation(() => {
			callCount++;
			if (callCount === 1) return mockBuilder as unknown as ReturnType<typeof supabase.from>;
			return deleteBuilder as unknown as ReturnType<typeof supabase.from>;
		});

		await deleteAttachment('att-123');

		expect(mockStorage.remove).toHaveBeenCalledWith(['user-123/ticket-456/file.png']);
	});

	it('throws when attachment not found', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: { message: 'Not found' }
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		await expect(deleteAttachment('non-existent')).rejects.toThrow('Failed to find attachment');
	});
});

describe('addReply', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('adds a reply to ticket', async () => {
		mockSupabase.auth.getUser.mockResolvedValue({
			data: { user: { id: 'user-456' } },
			error: null
		} as unknown as ReturnType<typeof supabase.auth.getUser>);

		const mockBuilder = createMockQueryBuilder({
			data: {
				id: 'reply-1',
				ticket_id: 'ticket-123',
				user_id: 'user-456',
				content: 'Test reply',
				is_staff: false,
				created_at: '2025-01-01T00:00:00Z'
			},
			error: null
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await addReply('ticket-123', 'Test reply');

		expect(mockBuilder.insert).toHaveBeenCalledWith(
			expect.objectContaining({
				ticket_id: 'ticket-123',
				content: 'Test reply',
				is_staff: false
			})
		);
		expect(result.id).toBe('reply-1');
	});

	it('throws when not authenticated', async () => {
		mockSupabase.auth.getUser.mockResolvedValue({
			data: { user: null },
			error: null
		} as unknown as ReturnType<typeof supabase.auth.getUser>);

		await expect(addReply('ticket-123', 'Test')).rejects.toThrow('User not authenticated');
	});
});

describe('formatFileSize', () => {
	it('formats bytes', () => {
		expect(formatFileSize(500)).toBe('500 B');
	});

	it('formats kilobytes', () => {
		expect(formatFileSize(1536)).toBe('1.5 KB');
	});

	it('formats megabytes', () => {
		expect(formatFileSize(2.5 * 1024 * 1024)).toBe('2.5 MB');
	});

	it('handles null', () => {
		expect(formatFileSize(null)).toBe('Unknown size');
	});
});

describe('isAllowedFileType', () => {
	it('allows JPEG', () => {
		const file = new File([''], 'test.jpg', { type: 'image/jpeg' });
		expect(isAllowedFileType(file)).toBe(true);
	});

	it('allows PNG', () => {
		const file = new File([''], 'test.png', { type: 'image/png' });
		expect(isAllowedFileType(file)).toBe(true);
	});

	it('allows GIF', () => {
		const file = new File([''], 'test.gif', { type: 'image/gif' });
		expect(isAllowedFileType(file)).toBe(true);
	});

	it('allows WebP', () => {
		const file = new File([''], 'test.webp', { type: 'image/webp' });
		expect(isAllowedFileType(file)).toBe(true);
	});

	it('rejects PDF', () => {
		const file = new File([''], 'test.pdf', { type: 'application/pdf' });
		expect(isAllowedFileType(file)).toBe(false);
	});
});

describe('isWithinSizeLimit', () => {
	it('accepts small files', () => {
		const file = new File(['test'], 'small.png', { type: 'image/png' });
		expect(isWithinSizeLimit(file)).toBe(true);
	});

	it('rejects large files', () => {
		const largeContent = new ArrayBuffer(6 * 1024 * 1024);
		const file = new File([largeContent], 'large.png', { type: 'image/png' });
		expect(isWithinSizeLimit(file)).toBe(false);
	});
});

describe('getFileValidationError', () => {
	it('returns null for valid file', () => {
		const file = new File(['test'], 'test.png', { type: 'image/png' });
		expect(getFileValidationError(file)).toBeNull();
	});

	it('returns error for invalid type', () => {
		const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
		expect(getFileValidationError(file)).toContain('File type not allowed');
	});

	it('returns error for large file', () => {
		const largeContent = new ArrayBuffer(6 * 1024 * 1024);
		const file = new File([largeContent], 'large.png', { type: 'image/png' });
		expect(getFileValidationError(file)).toContain('File too large');
	});
});

describe('checkIsAdmin', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('returns true for admin user', async () => {
		mockSupabase.auth.getUser.mockResolvedValue({
			data: { user: { id: 'user-456' } },
			error: null
		} as unknown as ReturnType<typeof supabase.auth.getUser>);

		const mockBuilder = createMockQueryBuilder({
			data: { is_admin: true },
			error: null
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await checkIsAdmin();

		expect(result).toBe(true);
	});

	it('returns false for non-admin user', async () => {
		mockSupabase.auth.getUser.mockResolvedValue({
			data: { user: { id: 'user-456' } },
			error: null
		} as unknown as ReturnType<typeof supabase.auth.getUser>);

		const mockBuilder = createMockQueryBuilder({
			data: { is_admin: false },
			error: null
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await checkIsAdmin();

		expect(result).toBe(false);
	});

	it('returns false when not authenticated', async () => {
		mockSupabase.auth.getUser.mockResolvedValue({
			data: { user: null },
			error: null
		} as unknown as ReturnType<typeof supabase.auth.getUser>);

		const result = await checkIsAdmin();

		expect(result).toBe(false);
	});
});

describe('updateTicketStatus', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('updates ticket status', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: { ...sampleDbTicket, status: 'in_progress' },
			error: null
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await updateTicketStatus('ticket-123', 'in_progress');

		expect(mockBuilder.update).toHaveBeenCalledWith({ status: 'in_progress' });
		expect(result.status).toBe('in_progress');
	});

	it('throws on error', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: { message: 'Update failed' }
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		await expect(updateTicketStatus('ticket-123', 'closed')).rejects.toThrow(
			'Failed to update ticket status'
		);
	});
});

describe('addStaffReply', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('adds staff reply with is_staff=true', async () => {
		mockSupabase.auth.getUser.mockResolvedValue({
			data: { user: { id: 'admin-user' } },
			error: null
		} as unknown as ReturnType<typeof supabase.auth.getUser>);

		const mockBuilder = createMockQueryBuilder({
			data: {
				id: 'reply-2',
				ticket_id: 'ticket-123',
				user_id: 'admin-user',
				content: 'Staff response',
				is_staff: true,
				created_at: '2025-01-01T00:00:00Z'
			},
			error: null
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await addStaffReply('ticket-123', 'Staff response');

		expect(mockBuilder.insert).toHaveBeenCalledWith(
			expect.objectContaining({
				is_staff: true
			})
		);
		expect(result.isStaff).toBe(true);
	});
});

describe('getTicketStats', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('calculates ticket statistics', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: [
				{ status: 'open' },
				{ status: 'open' },
				{ status: 'in_progress' },
				{ status: 'resolved' },
				{ status: 'closed' }
			],
			error: null
		});
		mockBuilder.select.mockImplementation(() => ({
			...mockBuilder,
			then: (resolve: (value: unknown) => void) =>
				resolve({
					data: [
						{ status: 'open' },
						{ status: 'open' },
						{ status: 'in_progress' },
						{ status: 'resolved' },
						{ status: 'closed' }
					],
					error: null
				})
		}));
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await getTicketStats();

		expect(result.total).toBe(5);
		expect(result.open).toBe(2);
		expect(result.inProgress).toBe(1);
		expect(result.resolved).toBe(1);
		expect(result.closed).toBe(1);
	});

	it('throws on error', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: { message: 'Database error' }
		});
		mockBuilder.select.mockImplementation(() => ({
			...mockBuilder,
			then: (resolve: (value: unknown) => void) =>
				resolve({ data: null, error: { message: 'Database error' } })
		}));
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		await expect(getTicketStats()).rejects.toThrow('Failed to fetch ticket stats');
	});
});
