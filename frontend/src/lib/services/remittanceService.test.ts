/**
 * Tests for remittanceService
 */

import { describe, expect, it, vi, beforeEach } from 'vitest';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock URL methods
global.URL.createObjectURL = vi.fn(() => 'blob:test-url');
global.URL.revokeObjectURL = vi.fn();

// Mock document methods
const mockLink = {
	href: '',
	download: '',
	click: vi.fn()
};
vi.spyOn(document, 'createElement').mockReturnValue(mockLink as unknown as HTMLAnchorElement);
vi.spyOn(document.body, 'appendChild').mockImplementation(() => mockLink as unknown as Node);
vi.spyOn(document.body, 'removeChild').mockImplementation(() => mockLink as unknown as Node);

// Mock supabase
vi.mock('$lib/api/supabase', () => ({
	supabase: {
		from: vi.fn(),
		auth: {
			getSession: vi.fn()
		}
	}
}));

// Mock auth store
vi.mock('$lib/stores/auth.svelte', () => ({
	authState: {
		user: { id: 'test-user-id' }
	}
}));

import { supabase } from '$lib/api/supabase';
import {
	listRemittancePeriods,
	getRemittancePeriod,
	createRemittancePeriod,
	recordPayment,
	deleteRemittancePeriod,
	getRemittanceSummary,
	downloadPD7A,
	getPD7ADownloadUrl
} from './remittanceService';

const mockSupabase = vi.mocked(supabase);

// Sample DB remittance period
const sampleDbPeriod = {
	id: 'period-123',
	company_id: 'company-456',
	user_id: 'test-user-id',
	remitter_type: 'regular' as const,
	period_start: '2025-01-01',
	period_end: '2025-01-31',
	due_date: '2025-02-15',
	cpp_employee: 1000,
	cpp_employer: 1000,
	ei_employee: 500,
	ei_employer: 700,
	federal_tax: 3000,
	provincial_tax: 1500,
	total_amount: 7700,
	status: 'pending' as const,
	paid_date: null,
	payment_method: null,
	confirmation_number: null,
	notes: null,
	days_overdue: 0,
	penalty_rate: 0,
	penalty_amount: 0,
	payroll_run_ids: ['run-1', 'run-2'],
	created_at: '2025-01-15T00:00:00Z',
	updated_at: '2025-01-15T00:00:00Z'
};

// Helper to create mock query builder
function createMockQueryBuilder(response: { data: unknown; error: unknown; count?: number }) {
	const builder = {
		select: vi.fn().mockReturnThis(),
		insert: vi.fn().mockReturnThis(),
		update: vi.fn().mockReturnThis(),
		delete: vi.fn().mockReturnThis(),
		eq: vi.fn().mockReturnThis(),
		gte: vi.fn().mockReturnThis(),
		lte: vi.fn().mockReturnThis(),
		order: vi.fn().mockReturnThis(),
		range: vi.fn().mockReturnThis(),
		single: vi.fn().mockResolvedValue(response),
		then: vi.fn((resolve) => resolve({ ...response, count: response.count ?? 0 }))
	};

	// Chain range to return the final response
	builder.range.mockImplementation(() => ({
		...builder,
		then: (resolve: (value: unknown) => void) =>
			resolve({ ...response, count: response.count ?? 0 })
	}));

	return builder;
}

describe('listRemittancePeriods', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('lists remittance periods', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: [sampleDbPeriod],
			error: null,
			count: 1
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await listRemittancePeriods('company-456');

		expect(mockSupabase.from).toHaveBeenCalledWith('remittance_periods');
		expect(result.error).toBeNull();
		expect(result.data).toHaveLength(1);
		expect(result.data[0].id).toBe('period-123');
		expect(result.count).toBe(1);
	});

	it('filters by year', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: [],
			error: null,
			count: 0
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		await listRemittancePeriods('company-456', { year: 2025 });

		expect(mockBuilder.gte).toHaveBeenCalledWith('period_start', '2025-01-01');
		expect(mockBuilder.lte).toHaveBeenCalledWith('period_end', '2025-12-31');
	});

	it('filters by status', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: [],
			error: null,
			count: 0
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		await listRemittancePeriods('company-456', { status: 'paid' });

		expect(mockBuilder.eq).toHaveBeenCalledWith('status', 'paid');
	});

	it('returns error on failure', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: { message: 'Database error' },
			count: 0
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await listRemittancePeriods('company-456');

		expect(result.error).toBe('Database error');
		expect(result.data).toEqual([]);
	});
});

describe('getRemittancePeriod', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('gets single period by ID', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: sampleDbPeriod,
			error: null
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await getRemittancePeriod('period-123');

		expect(result.error).toBeNull();
		expect(result.data?.id).toBe('period-123');
		expect(result.data?.totalAmount).toBe(7700);
	});

	it('returns error when not found', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: { message: 'Not found' }
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await getRemittancePeriod('non-existent');

		expect(result.error).toBe('Not found');
		expect(result.data).toBeNull();
	});
});

describe('createRemittancePeriod', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('creates a new period', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: sampleDbPeriod,
			error: null
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await createRemittancePeriod({
			company_id: 'company-456',
			remitter_type: 'regular',
			period_start: '2025-01-01',
			period_end: '2025-01-31',
			due_date: '2025-02-15'
		});

		expect(mockBuilder.insert).toHaveBeenCalled();
		expect(result.error).toBeNull();
		expect(result.data?.id).toBe('period-123');
	});

	it('uses default values for optional fields', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: sampleDbPeriod,
			error: null
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		await createRemittancePeriod({
			company_id: 'company-456',
			remitter_type: 'regular',
			period_start: '2025-01-01',
			period_end: '2025-01-31',
			due_date: '2025-02-15'
		});

		expect(mockBuilder.insert).toHaveBeenCalledWith(
			expect.objectContaining({
				cpp_employee: 0,
				cpp_employer: 0,
				ei_employee: 0,
				ei_employer: 0,
				federal_tax: 0,
				provincial_tax: 0,
				payroll_run_ids: []
			})
		);
	});

	it('returns error on failure', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: { message: 'Insert failed' }
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await createRemittancePeriod({
			company_id: 'company-456',
			remitter_type: 'regular',
			period_start: '2025-01-01',
			period_end: '2025-01-31',
			due_date: '2025-02-15'
		});

		expect(result.error).toBe('Insert failed');
	});
});

describe('recordPayment', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('records on-time payment', async () => {
		// First call to get existing period (due date check)
		const fetchBuilder = createMockQueryBuilder({
			data: { due_date: '2025-02-15' },
			error: null
		});

		// Second call to update
		const updateBuilder = createMockQueryBuilder({
			data: { ...sampleDbPeriod, status: 'paid', paid_date: '2025-02-10' },
			error: null
		});

		let callCount = 0;
		mockSupabase.from.mockImplementation(() => {
			callCount++;
			if (callCount === 1) return fetchBuilder as unknown as ReturnType<typeof supabase.from>;
			return updateBuilder as unknown as ReturnType<typeof supabase.from>;
		});

		const result = await recordPayment('period-123', {
			paid_date: '2025-02-10',
			payment_method: 'online_banking',
			confirmation_number: 'PAY-123'
		});

		expect(updateBuilder.update).toHaveBeenCalledWith(
			expect.objectContaining({
				status: 'paid',
				paid_date: '2025-02-10',
				payment_method: 'online_banking',
				confirmation_number: 'PAY-123'
			})
		);
		expect(result.error).toBeNull();
	});

	it('records late payment', async () => {
		// First call to get existing period
		const fetchBuilder = createMockQueryBuilder({
			data: { due_date: '2025-02-15' },
			error: null
		});

		// Second call to update
		const updateBuilder = createMockQueryBuilder({
			data: { ...sampleDbPeriod, status: 'paid_late', paid_date: '2025-02-20' },
			error: null
		});

		let callCount = 0;
		mockSupabase.from.mockImplementation(() => {
			callCount++;
			if (callCount === 1) return fetchBuilder as unknown as ReturnType<typeof supabase.from>;
			return updateBuilder as unknown as ReturnType<typeof supabase.from>;
		});

		const result = await recordPayment('period-123', {
			paid_date: '2025-02-20', // After due date
			payment_method: 'online_banking'
		});

		expect(updateBuilder.update).toHaveBeenCalledWith(
			expect.objectContaining({
				status: 'paid_late'
			})
		);
		expect(result.error).toBeNull();
	});

	it('returns error when period not found', async () => {
		const fetchBuilder = createMockQueryBuilder({
			data: null,
			error: { message: 'Not found' }
		});
		mockSupabase.from.mockReturnValue(
			fetchBuilder as unknown as ReturnType<typeof supabase.from>
		);

		const result = await recordPayment('non-existent', {
			paid_date: '2025-02-10',
			payment_method: 'online_banking'
		});

		expect(result.error).toBe('Not found');
	});
});

describe('deleteRemittancePeriod', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('deletes a period', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: null
		});
		mockBuilder.eq.mockImplementation(() => ({
			...mockBuilder,
			eq: vi.fn().mockImplementation(() => ({
				then: (resolve: (value: unknown) => void) => resolve({ error: null })
			}))
		}));
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await deleteRemittancePeriod('period-123');

		expect(mockSupabase.from).toHaveBeenCalledWith('remittance_periods');
		expect(mockBuilder.delete).toHaveBeenCalled();
		expect(result.error).toBeNull();
	});

	it('returns error on failure', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: { message: 'Delete failed' }
		});
		mockBuilder.eq.mockImplementation(() => ({
			...mockBuilder,
			eq: vi.fn().mockImplementation(() => ({
				then: (resolve: (value: unknown) => void) =>
					resolve({ error: { message: 'Delete failed' } })
			}))
		}));
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await deleteRemittancePeriod('period-123');

		expect(result.error).toBe('Delete failed');
	});
});

describe('getRemittanceSummary', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('calculates summary statistics', async () => {
		const periods = [
			{ ...sampleDbPeriod, status: 'paid', total_amount: 5000 },
			{ ...sampleDbPeriod, id: 'period-2', status: 'paid_late', total_amount: 3000 },
			{ ...sampleDbPeriod, id: 'period-3', status: 'pending', total_amount: 7700 },
			{ ...sampleDbPeriod, id: 'period-4', status: 'overdue', total_amount: 8000 }
		];

		const mockBuilder = createMockQueryBuilder({
			data: periods,
			error: null,
			count: 4
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await getRemittanceSummary('company-456', 2025);

		expect(result.error).toBeNull();
		expect(result.data?.year).toBe(2025);
		expect(result.data?.ytdRemitted).toBe(8000); // paid + paid_late
		expect(result.data?.totalRemittances).toBe(4);
		expect(result.data?.completedRemittances).toBe(2);
		expect(result.data?.pendingCount).toBe(2);
		expect(result.data?.pendingAmount).toBe(15700); // pending + overdue
	});

	it('handles empty periods', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: [],
			error: null,
			count: 0
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await getRemittanceSummary('company-456', 2025);

		expect(result.error).toBeNull();
		expect(result.data?.totalRemittances).toBe(0);
		expect(result.data?.onTimeRate).toBe(1.0); // Default when no payments
	});

	it('returns error on failure', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: { message: 'Database error' },
			count: 0
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await getRemittanceSummary('company-456', 2025);

		expect(result.error).toBe('Database error');
	});
});

describe('downloadPD7A', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		mockLink.click.mockClear();
	});

	it('downloads PDF successfully', async () => {
		mockSupabase.auth.getSession.mockResolvedValue({
			data: { session: { access_token: 'test-token' } },
			error: null
		} as unknown as ReturnType<typeof supabase.auth.getSession>);

		const mockBlob = new Blob(['pdf content'], { type: 'application/pdf' });
		mockFetch.mockResolvedValueOnce({
			ok: true,
			headers: new Headers({ 'Content-Disposition': 'filename=PD7A_2025_01.pdf' }),
			blob: () => Promise.resolve(mockBlob)
		});

		const result = await downloadPD7A('company-456', 'period-123');

		expect(result.error).toBeNull();
		expect(mockLink.click).toHaveBeenCalled();
	});

	it('returns error when not authenticated', async () => {
		mockSupabase.auth.getSession.mockResolvedValue({
			data: { session: null },
			error: null
		} as unknown as ReturnType<typeof supabase.auth.getSession>);

		const result = await downloadPD7A('company-456', 'period-123');

		expect(result.error).toBe('Not authenticated');
	});

	it('returns error on download failure', async () => {
		mockSupabase.auth.getSession.mockResolvedValue({
			data: { session: { access_token: 'test-token' } },
			error: null
		} as unknown as ReturnType<typeof supabase.auth.getSession>);

		mockFetch.mockResolvedValueOnce({
			ok: false,
			status: 404,
			text: () => Promise.resolve('Not found')
		});

		const result = await downloadPD7A('company-456', 'period-123');

		expect(result.error).toContain('404');
	});

	it('handles network error', async () => {
		mockSupabase.auth.getSession.mockResolvedValue({
			data: { session: { access_token: 'test-token' } },
			error: null
		} as unknown as ReturnType<typeof supabase.auth.getSession>);

		mockFetch.mockRejectedValueOnce(new Error('Network failed'));

		const result = await downloadPD7A('company-456', 'period-123');

		expect(result.error).toBe('Network failed');
	});
});

describe('getPD7ADownloadUrl', () => {
	it('returns correct URL format', () => {
		const url = getPD7ADownloadUrl('company-456', 'period-123');

		expect(url).toBe('/api/v1/remittance/pd7a/company-456/period-123');
	});
});
