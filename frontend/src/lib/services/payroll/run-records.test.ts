/**
 * Tests for Payroll Run Record Functions
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock modules
const mockSupabaseFrom = vi.fn();
const mockApiPost = vi.fn();
const mockApiPatch = vi.fn();
const mockGetCurrentUserId = vi.fn();
const mockGetCurrentCompanyId = vi.fn();

vi.mock('$lib/api/supabase', () => ({
	supabase: {
		get from() {
			return mockSupabaseFrom;
		}
	}
}));

vi.mock('$lib/api/client', () => ({
	api: {
		get post() {
			return mockApiPost;
		},
		get patch() {
			return mockApiPatch;
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

import { updatePayrollRecord, recalculatePayrollRun, checkHasModifiedRecords } from './run-records';

// Helper to create mock Supabase query chain
function createMockSupabaseQuery(options: { data?: unknown; error?: { message: string } | null }) {
	const { data = null, error = null } = options;
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

describe('Payroll Run Records', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		mockGetCurrentUserId.mockReturnValue('test-user-id');
		mockGetCurrentCompanyId.mockReturnValue('test-company-id');
	});

	describe('recalculatePayrollRun', () => {
		it('calls backend recalculate endpoint', async () => {
			mockApiPost.mockResolvedValue({});

			const mockQuery = createMockSupabaseQuery({
				data: mockDbPayrollRun,
				error: null
			});
			mockQuery.maybeSingle = vi.fn(() =>
				Promise.resolve({
					data: mockDbPayrollRun,
					error: null
				})
			);

			const getMockQuery = createMockSupabaseQuery({
				data: [mockDbPayrollRun],
				error: null
			});

			let callCount = 0;
			mockSupabaseFrom.mockImplementation(() => {
				callCount++;
				if (callCount === 1) return mockQuery;
				return getMockQuery;
			});

			await recalculatePayrollRun('run-123');

			expect(mockApiPost).toHaveBeenCalledWith('/payroll/runs/run-123/recalculate', {});
		});
	});

	describe('checkHasModifiedRecords', () => {
		it('returns true when modified records exist', async () => {
			const mockQuery = createMockSupabaseQuery({
				data: [{ id: 'record-1' }],
				error: null
			});

			mockSupabaseFrom.mockReturnValue(mockQuery);

			const result = await checkHasModifiedRecords('run-123');

			expect(result.data).toBe(true);
			expect(mockQuery.eq).toHaveBeenCalledWith('is_modified', true);
		});

		it('returns false when no modified records exist', async () => {
			const mockQuery = createMockSupabaseQuery({
				data: [],
				error: null
			});

			mockSupabaseFrom.mockReturnValue(mockQuery);

			const result = await checkHasModifiedRecords('run-123');

			expect(result.data).toBe(false);
		});
	});

	describe('updatePayrollRecord', () => {
		it('sends correct request body for hours update', async () => {
			mockApiPatch.mockResolvedValue({});

			const mockQuery = createMockSupabaseQuery({
				data: mockDbPayrollRun,
				error: null
			});
			mockQuery.maybeSingle = vi.fn(() =>
				Promise.resolve({
					data: mockDbPayrollRun,
					error: null
				})
			);

			const getMockQuery = createMockSupabaseQuery({
				data: [mockDbPayrollRun],
				error: null
			});

			let callCount = 0;
			mockSupabaseFrom.mockImplementation(() => {
				callCount++;
				if (callCount === 1) return mockQuery;
				return getMockQuery;
			});

			await updatePayrollRecord('run-123', 'record-1', {
				regularHours: 80,
				overtimeHours: 5
			});

			expect(mockApiPatch).toHaveBeenCalledWith(
				'/payroll/runs/run-123/records/record-1',
				expect.objectContaining({
					regularHours: 80,
					overtimeHours: 5
				})
			);
		});

		it('sends correct request body for leave entries', async () => {
			mockApiPatch.mockResolvedValue({});

			const mockQuery = createMockSupabaseQuery({
				data: mockDbPayrollRun,
				error: null
			});
			mockQuery.maybeSingle = vi.fn(() =>
				Promise.resolve({
					data: mockDbPayrollRun,
					error: null
				})
			);

			const getMockQuery = createMockSupabaseQuery({
				data: [mockDbPayrollRun],
				error: null
			});

			let callCount = 0;
			mockSupabaseFrom.mockImplementation(() => {
				callCount++;
				if (callCount === 1) return mockQuery;
				return getMockQuery;
			});

			await updatePayrollRecord('run-123', 'record-1', {
				leaveEntries: [{ type: 'vacation', hours: 8 }]
			});

			expect(mockApiPatch).toHaveBeenCalledWith(
				'/payroll/runs/run-123/records/record-1',
				expect.objectContaining({
					leaveEntries: [{ type: 'vacation', hours: 8 }]
				})
			);
		});

		it('sends correct request body for adjustments', async () => {
			mockApiPatch.mockResolvedValue({});

			const mockQuery = createMockSupabaseQuery({
				data: mockDbPayrollRun,
				error: null
			});
			mockQuery.maybeSingle = vi.fn(() =>
				Promise.resolve({
					data: mockDbPayrollRun,
					error: null
				})
			);

			const getMockQuery = createMockSupabaseQuery({
				data: [mockDbPayrollRun],
				error: null
			});

			let callCount = 0;
			mockSupabaseFrom.mockImplementation(() => {
				callCount++;
				if (callCount === 1) return mockQuery;
				return getMockQuery;
			});

			await updatePayrollRecord('run-123', 'record-1', {
				adjustments: [
					{
						id: 'adj-1',
						type: 'bonus',
						amount: 500,
						description: 'Performance bonus',
						taxable: true
					}
				]
			});

			expect(mockApiPatch).toHaveBeenCalledWith(
				'/payroll/runs/run-123/records/record-1',
				expect.objectContaining({
					adjustments: [
						{
							type: 'bonus',
							amount: 500,
							description: 'Performance bonus',
							taxable: true
						}
					]
				})
			);
		});
	});
});
