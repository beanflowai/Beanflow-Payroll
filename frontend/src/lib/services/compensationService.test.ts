/**
 * Tests for Compensation Service
 */

import { describe, expect, it, vi, beforeEach } from 'vitest';

// Mock modules before imports
vi.mock('$lib/api/supabase', () => ({
	supabase: {
		from: vi.fn()
	}
}));

vi.mock('$lib/api/client', () => ({
	api: {
		post: vi.fn()
	}
}));

import { supabase } from '$lib/api/supabase';
import { api } from '$lib/api/client';
import {
	getCompensationHistory,
	getCurrentCompensation,
	getCompensationAtDate,
	updateCompensation
} from './compensationService';

const mockSupabase = vi.mocked(supabase);
const mockApi = vi.mocked(api);

const sampleDbRecord = {
	id: 'comp-1',
	employee_id: 'emp-123',
	compensation_type: 'salary' as const,
	annual_salary: 78000,
	hourly_rate: null,
	effective_date: '2025-01-01',
	end_date: null,
	change_reason: 'Annual raise',
	created_at: '2025-01-01T00:00:00Z'
};

const expectedModel = {
	id: 'comp-1',
	employeeId: 'emp-123',
	compensationType: 'salary',
	annualSalary: 78000,
	hourlyRate: null,
	effectiveDate: '2025-01-01',
	endDate: null,
	changeReason: 'Annual raise',
	createdAt: '2025-01-01T00:00:00Z'
};

describe('getCompensationHistory', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('returns compensation history sorted by effective date', async () => {
		const mockData = [
			{ ...sampleDbRecord, id: 'comp-2', effective_date: '2025-01-01' },
			{ ...sampleDbRecord, id: 'comp-1', effective_date: '2024-01-01', end_date: '2024-12-31' }
		];

		mockSupabase.from.mockReturnValue({
			select: vi.fn().mockReturnValue({
				eq: vi.fn().mockReturnValue({
					order: vi.fn().mockResolvedValue({
						data: mockData,
						error: null
					})
				})
			})
		} as never);

		const result = await getCompensationHistory('emp-123');

		expect(result.data).toHaveLength(2);
		expect(result.data![0].id).toBe('comp-2');
		expect(result.error).toBeNull();
	});

	it('returns empty array when no history exists', async () => {
		mockSupabase.from.mockReturnValue({
			select: vi.fn().mockReturnValue({
				eq: vi.fn().mockReturnValue({
					order: vi.fn().mockResolvedValue({
						data: [],
						error: null
					})
				})
			})
		} as never);

		const result = await getCompensationHistory('emp-123');

		expect(result.data).toEqual([]);
		expect(result.error).toBeNull();
	});

	it('returns error on query failure', async () => {
		mockSupabase.from.mockReturnValue({
			select: vi.fn().mockReturnValue({
				eq: vi.fn().mockReturnValue({
					order: vi.fn().mockResolvedValue({
						data: null,
						error: { message: 'Database error' }
					})
				})
			})
		} as never);

		const result = await getCompensationHistory('emp-123');

		expect(result.data).toBeNull();
		expect(result.error).toBeInstanceOf(Error);
		expect(result.error!.message).toBe('Database error');
	});

	it('handles exception', async () => {
		mockSupabase.from.mockImplementation(() => {
			throw new Error('Unexpected error');
		});

		const result = await getCompensationHistory('emp-123');

		expect(result.data).toBeNull();
		expect(result.error!.message).toBe('Unexpected error');
	});

	it('handles non-Error exception', async () => {
		mockSupabase.from.mockImplementation(() => {
			throw 'String error';
		});

		const result = await getCompensationHistory('emp-123');

		expect(result.data).toBeNull();
		expect(result.error!.message).toBe('Unknown error');
	});

	it('maps database fields to camelCase', async () => {
		mockSupabase.from.mockReturnValue({
			select: vi.fn().mockReturnValue({
				eq: vi.fn().mockReturnValue({
					order: vi.fn().mockResolvedValue({
						data: [sampleDbRecord],
						error: null
					})
				})
			})
		} as never);

		const result = await getCompensationHistory('emp-123');

		expect(result.data![0]).toEqual(expectedModel);
	});
});

describe('getCurrentCompensation', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('returns current compensation record', async () => {
		mockSupabase.from.mockReturnValue({
			select: vi.fn().mockReturnValue({
				eq: vi.fn().mockReturnValue({
					is: vi.fn().mockReturnValue({
						single: vi.fn().mockResolvedValue({
							data: sampleDbRecord,
							error: null
						})
					})
				})
			})
		} as never);

		const result = await getCurrentCompensation('emp-123');

		expect(result.data).toEqual(expectedModel);
		expect(result.error).toBeNull();
	});

	it('returns null when no current compensation exists (PGRST116)', async () => {
		mockSupabase.from.mockReturnValue({
			select: vi.fn().mockReturnValue({
				eq: vi.fn().mockReturnValue({
					is: vi.fn().mockReturnValue({
						single: vi.fn().mockResolvedValue({
							data: null,
							error: { code: 'PGRST116', message: 'No rows found' }
						})
					})
				})
			})
		} as never);

		const result = await getCurrentCompensation('emp-123');

		expect(result.data).toBeNull();
		expect(result.error).toBeNull();
	});

	it('returns error on other query failure', async () => {
		mockSupabase.from.mockReturnValue({
			select: vi.fn().mockReturnValue({
				eq: vi.fn().mockReturnValue({
					is: vi.fn().mockReturnValue({
						single: vi.fn().mockResolvedValue({
							data: null,
							error: { code: 'PGRST100', message: 'Query error' }
						})
					})
				})
			})
		} as never);

		const result = await getCurrentCompensation('emp-123');

		expect(result.data).toBeNull();
		expect(result.error!.message).toBe('Query error');
	});

	it('handles exception', async () => {
		mockSupabase.from.mockImplementation(() => {
			throw new Error('Network error');
		});

		const result = await getCurrentCompensation('emp-123');

		expect(result.data).toBeNull();
		expect(result.error!.message).toBe('Network error');
	});

	it('handles non-Error exception', async () => {
		mockSupabase.from.mockImplementation(() => {
			throw 'String error';
		});

		const result = await getCurrentCompensation('emp-123');

		expect(result.data).toBeNull();
		expect(result.error!.message).toBe('Unknown error');
	});
});

describe('getCompensationAtDate', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('returns compensation active at specific date', async () => {
		mockSupabase.from.mockReturnValue({
			select: vi.fn().mockReturnValue({
				eq: vi.fn().mockReturnValue({
					lte: vi.fn().mockReturnValue({
						or: vi.fn().mockReturnValue({
							order: vi.fn().mockReturnValue({
								limit: vi.fn().mockReturnValue({
									single: vi.fn().mockResolvedValue({
										data: sampleDbRecord,
										error: null
									})
								})
							})
						})
					})
				})
			})
		} as never);

		const result = await getCompensationAtDate('emp-123', '2025-06-15');

		expect(result.data).toEqual(expectedModel);
		expect(result.error).toBeNull();
	});

	it('returns null when no compensation exists at date (PGRST116)', async () => {
		mockSupabase.from.mockReturnValue({
			select: vi.fn().mockReturnValue({
				eq: vi.fn().mockReturnValue({
					lte: vi.fn().mockReturnValue({
						or: vi.fn().mockReturnValue({
							order: vi.fn().mockReturnValue({
								limit: vi.fn().mockReturnValue({
									single: vi.fn().mockResolvedValue({
										data: null,
										error: { code: 'PGRST116', message: 'No rows found' }
									})
								})
							})
						})
					})
				})
			})
		} as never);

		const result = await getCompensationAtDate('emp-123', '2020-01-01');

		expect(result.data).toBeNull();
		expect(result.error).toBeNull();
	});

	it('returns error on other query failure', async () => {
		mockSupabase.from.mockReturnValue({
			select: vi.fn().mockReturnValue({
				eq: vi.fn().mockReturnValue({
					lte: vi.fn().mockReturnValue({
						or: vi.fn().mockReturnValue({
							order: vi.fn().mockReturnValue({
								limit: vi.fn().mockReturnValue({
									single: vi.fn().mockResolvedValue({
										data: null,
										error: { code: 'PGRST100', message: 'Query error' }
									})
								})
							})
						})
					})
				})
			})
		} as never);

		const result = await getCompensationAtDate('emp-123', '2025-06-15');

		expect(result.data).toBeNull();
		expect(result.error!.message).toBe('Query error');
	});

	it('handles exception', async () => {
		mockSupabase.from.mockImplementation(() => {
			throw new Error('Network error');
		});

		const result = await getCompensationAtDate('emp-123', '2025-06-15');

		expect(result.data).toBeNull();
		expect(result.error!.message).toBe('Network error');
	});

	it('handles non-Error exception', async () => {
		mockSupabase.from.mockImplementation(() => {
			throw 'String error';
		});

		const result = await getCompensationAtDate('emp-123', '2025-06-15');

		expect(result.data).toBeNull();
		expect(result.error!.message).toBe('Unknown error');
	});
});

describe('updateCompensation', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('updates compensation via API', async () => {
		const updateData = {
			compensationType: 'salary' as const,
			annualSalary: 85000,
			effectiveDate: '2025-07-01',
			changeReason: 'Promotion'
		};

		mockApi.post.mockResolvedValue(expectedModel);

		const result = await updateCompensation('emp-123', updateData);

		expect(mockApi.post).toHaveBeenCalledWith('/employees/emp-123/compensation', updateData);
		expect(result.data).toEqual(expectedModel);
		expect(result.error).toBeNull();
	});

	it('returns error on API failure', async () => {
		mockApi.post.mockRejectedValue(new Error('API error'));

		const result = await updateCompensation('emp-123', {
			compensationType: 'salary',
			annualSalary: 85000,
			effectiveDate: '2025-07-01'
		});

		expect(result.data).toBeNull();
		expect(result.error!.message).toBe('API error');
	});

	it('returns generic error on non-Error exception', async () => {
		mockApi.post.mockRejectedValue('String error');

		const result = await updateCompensation('emp-123', {
			compensationType: 'hourly',
			hourlyRate: 30,
			effectiveDate: '2025-07-01'
		});

		expect(result.data).toBeNull();
		expect(result.error!.message).toBe('Failed to update compensation');
	});
});
