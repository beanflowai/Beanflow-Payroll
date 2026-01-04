/**
 * Tests for Payroll Run Query Functions
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock modules
const mockSupabaseFrom = vi.fn();
const mockGetCurrentUserId = vi.fn();
const mockGetCurrentCompanyId = vi.fn();

vi.mock('$lib/api/supabase', () => ({
	supabase: {
		get from() {
			return mockSupabaseFrom;
		}
	}
}));

vi.mock('./helpers', () => ({
	get getCurrentUserId() {
		return mockGetCurrentUserId;
	},
	get getCurrentCompanyId() {
		return mockGetCurrentCompanyId;
	}
}));

import { getPayrollRunByPayDate, listPayrollRuns } from './run-queries';

// Helper to create mock Supabase query chain
function createMockSupabaseQuery(options: {
	data?: unknown;
	error?: { message: string } | null;
	count?: number | null;
}) {
	const { data = null, error = null, count = null } = options;
	const mockChain: Record<string, unknown> = {};
	const chainMethods = [
		'select',
		'eq',
		'neq',
		'in',
		'not',
		'gte',
		'lte',
		'order',
		'update',
		'insert',
		'delete'
	];
	chainMethods.forEach((method) => {
		mockChain[method] = vi.fn(() => mockChain);
	});
	mockChain.single = vi.fn(() => Promise.resolve({ data, error }));
	mockChain.maybeSingle = vi.fn(() => Promise.resolve({ data, error }));
	mockChain.limit = vi.fn(() => Promise.resolve({ data, error }));
	mockChain.range = vi.fn(() => Promise.resolve({ data, error, count }));
	return mockChain;
}

const mockDbPayrollRun = {
	id: 'run-123',
	user_id: 'test-user-id',
	company_id: 'test-company-id',
	period_start: '2025-01-01',
	period_end: '2025-01-15',
	pay_date: '2025-01-20',
	status: 'draft',
	total_employees: 5,
	total_gross: 10000,
	total_cpp_employee: 500,
	total_cpp_employer: 500,
	total_ei_employee: 200,
	total_ei_employer: 280,
	total_federal_tax: 1500,
	total_provincial_tax: 800,
	total_net_pay: 7000,
	total_employer_cost: 780,
	created_at: '2025-01-01T00:00:00Z',
	updated_at: '2025-01-01T00:00:00Z'
};

describe('Payroll Run Queries', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		mockGetCurrentUserId.mockReturnValue('test-user-id');
		mockGetCurrentCompanyId.mockReturnValue('test-company-id');
	});

	describe('getPayrollRunByPayDate', () => {
		it('returns null when no payroll run exists for the date', async () => {
			const mockQuery = createMockSupabaseQuery({ data: [], error: null });
			mockSupabaseFrom.mockReturnValue(mockQuery);

			const result = await getPayrollRunByPayDate('2025-01-20');

			expect(result.data).toBeNull();
			expect(result.error).toBeNull();
		});

		it('returns error when supabase query fails', async () => {
			const mockQuery = createMockSupabaseQuery({
				data: null,
				error: { message: 'Database connection failed' }
			});
			mockSupabaseFrom.mockReturnValue(mockQuery);

			const result = await getPayrollRunByPayDate('2025-01-20');

			expect(result.data).toBeNull();
			expect(result.error).toBe('Database connection failed');
		});

		it('returns error when user is not authenticated', async () => {
			mockGetCurrentUserId.mockImplementation(() => {
				throw new Error('User not authenticated');
			});

			const result = await getPayrollRunByPayDate('2025-01-20');

			expect(result.data).toBeNull();
			expect(result.error).toBe('User not authenticated');
		});
	});

	describe('listPayrollRuns', () => {
		it('returns paginated list of payroll runs', async () => {
			const mockRuns = [mockDbPayrollRun, { ...mockDbPayrollRun, id: 'run-456' }];
			const mockQuery = createMockSupabaseQuery({
				data: mockRuns,
				error: null,
				count: 2
			});

			mockSupabaseFrom.mockReturnValue(mockQuery);

			const result = await listPayrollRuns({ limit: 20, offset: 0 });

			expect(result.error).toBeNull();
			expect(result.data).toHaveLength(2);
			expect(result.count).toBe(2);
		});

		it('filters by status when provided', async () => {
			const mockQuery = createMockSupabaseQuery({
				data: [mockDbPayrollRun],
				error: null,
				count: 1
			});

			mockSupabaseFrom.mockReturnValue(mockQuery);

			await listPayrollRuns({ status: 'draft' });

			expect(mockQuery.eq).toHaveBeenCalledWith('status', 'draft');
		});

		it('excludes statuses when provided', async () => {
			const mockQuery = createMockSupabaseQuery({
				data: [mockDbPayrollRun],
				error: null,
				count: 1
			});

			mockSupabaseFrom.mockReturnValue(mockQuery);

			await listPayrollRuns({ excludeStatuses: ['cancelled', 'paid'] });

			expect(mockQuery.not).toHaveBeenCalledWith('status', 'in', '(cancelled,paid)');
		});

		it('converts snake_case to camelCase in response', async () => {
			const mockQuery = createMockSupabaseQuery({
				data: [mockDbPayrollRun],
				error: null,
				count: 1
			});

			mockSupabaseFrom.mockReturnValue(mockQuery);

			const result = await listPayrollRuns();

			expect(result.data[0]).toHaveProperty('periodEnd', '2025-01-15');
			expect(result.data[0]).toHaveProperty('payDate', '2025-01-20');
			expect(result.data[0]).toHaveProperty('totalEmployees', 5);
		});

		it('calculates derived fields correctly', async () => {
			const mockQuery = createMockSupabaseQuery({
				data: [mockDbPayrollRun],
				error: null,
				count: 1
			});

			mockSupabaseFrom.mockReturnValue(mockQuery);

			const result = await listPayrollRuns();

			const run = result.data[0];
			expect(run.totalDeductions).toBe(10000 - 7000);
			expect(run.totalPayrollCost).toBe(10000 + 780);
		});

		it('returns empty array on error', async () => {
			const mockQuery = createMockSupabaseQuery({
				data: null,
				error: { message: 'Query failed' }
			});
			mockQuery.range = vi.fn(() => Promise.reject(new Error('Query failed')));

			mockSupabaseFrom.mockReturnValue(mockQuery);

			const result = await listPayrollRuns();

			expect(result.data).toEqual([]);
			expect(result.count).toBe(0);
			expect(result.error).toBe('Query failed');
		});
	});
});
