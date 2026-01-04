/**
 * Tests for Payroll Run Status Functions
 */

import { describe, it, expect, vi, beforeEach, type Mock } from 'vitest';

// Mock modules
const mockSupabaseFrom = vi.fn();
const mockApiPost = vi.fn();
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

import {
	updatePayrollRunStatus,
	approvePayrollRun,
	cancelPayrollRun,
	finalizePayrollRun,
	revertToDraft
} from './run-status';

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

describe('Payroll Run Status', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		mockGetCurrentUserId.mockReturnValue('test-user-id');
		mockGetCurrentCompanyId.mockReturnValue('test-company-id');
	});

	describe('updatePayrollRunStatus', () => {
		it('updates status successfully', async () => {
			const updateMockQuery = createMockSupabaseQuery({
				data: { ...mockDbPayrollRun, status: 'pending_approval' },
				error: null
			});

			const getMockQuery = createMockSupabaseQuery({
				data: [{ ...mockDbPayrollRun, status: 'pending_approval' }],
				error: null
			});

			let callCount = 0;
			mockSupabaseFrom.mockImplementation(() => {
				callCount++;
				if (callCount === 1) return updateMockQuery;
				return getMockQuery;
			});

			await updatePayrollRunStatus('run-123', 'pending_approval');

			expect(mockSupabaseFrom).toHaveBeenCalledWith('payroll_runs');
		});

		it('adds approval info when approving', async () => {
			const updateMockQuery = createMockSupabaseQuery({
				data: { ...mockDbPayrollRun, status: 'approved' },
				error: null
			});

			const getMockQuery = createMockSupabaseQuery({
				data: [{ ...mockDbPayrollRun, status: 'approved' }],
				error: null
			});

			let callCount = 0;
			mockSupabaseFrom.mockImplementation(() => {
				callCount++;
				if (callCount === 1) return updateMockQuery;
				return getMockQuery;
			});

			await updatePayrollRunStatus('run-123', 'approved');

			expect(updateMockQuery.update).toHaveBeenCalled();
			const updateCall = (updateMockQuery.update as Mock).mock.calls[0][0];
			expect(updateCall.status).toBe('approved');
			expect(updateCall.approved_by).toBe('test-user-id');
			expect(updateCall.approved_at).toBeDefined();
		});

		it('returns error when update fails', async () => {
			const mockQuery = createMockSupabaseQuery({
				data: null,
				error: { message: 'Update failed' }
			});
			mockQuery.single = vi.fn(() =>
				Promise.resolve({
					data: null,
					error: { message: 'Update failed' }
				})
			);

			mockSupabaseFrom.mockReturnValue(mockQuery);

			const result = await updatePayrollRunStatus('run-123', 'approved');

			expect(result.data).toBeNull();
			expect(result.error).toBe('Update failed');
		});
	});

	describe('cancelPayrollRun', () => {
		it('calls updatePayrollRunStatus with cancelled status', async () => {
			const updateMockQuery = createMockSupabaseQuery({
				data: { ...mockDbPayrollRun, status: 'cancelled' },
				error: null
			});

			const getMockQuery = createMockSupabaseQuery({
				data: [{ ...mockDbPayrollRun, status: 'cancelled' }],
				error: null
			});

			let callCount = 0;
			mockSupabaseFrom.mockImplementation(() => {
				callCount++;
				if (callCount === 1) return updateMockQuery;
				return getMockQuery;
			});

			await cancelPayrollRun('run-123');

			expect(updateMockQuery.update).toHaveBeenCalled();
			const updateCall = (updateMockQuery.update as Mock).mock.calls[0][0];
			expect(updateCall.status).toBe('cancelled');
		});
	});

	describe('approvePayrollRun', () => {
		it('calls backend API and returns updated run', async () => {
			mockApiPost.mockResolvedValue({
				id: 'run-123',
				payDate: '2025-01-20',
				status: 'approved',
				totalEmployees: 5,
				totalGross: 10000,
				totalNetPay: 7000,
				paystubsGenerated: 5,
				paystubErrors: null
			});

			const mockQuery = createMockSupabaseQuery({
				data: { ...mockDbPayrollRun, status: 'approved' },
				error: null
			});
			mockQuery.maybeSingle = vi.fn(() =>
				Promise.resolve({
					data: { ...mockDbPayrollRun, status: 'approved' },
					error: null
				})
			);

			const getMockQuery = createMockSupabaseQuery({
				data: [{ ...mockDbPayrollRun, status: 'approved' }],
				error: null
			});

			let callCount = 0;
			mockSupabaseFrom.mockImplementation(() => {
				callCount++;
				if (callCount === 1) return mockQuery;
				return getMockQuery;
			});

			await approvePayrollRun('run-123');

			expect(mockApiPost).toHaveBeenCalledWith('/payroll/runs/run-123/approve', {});
		});

		it('returns error when API call fails', async () => {
			mockApiPost.mockRejectedValue(new Error('API error'));

			const result = await approvePayrollRun('run-123');

			expect(result.data).toBeNull();
			expect(result.error).toBe('API error');
		});
	});

	describe('finalizePayrollRun', () => {
		it('updates status to pending_approval', async () => {
			const updateMockQuery = createMockSupabaseQuery({
				data: { ...mockDbPayrollRun, status: 'pending_approval' },
				error: null
			});

			const getMockQuery = createMockSupabaseQuery({
				data: [{ ...mockDbPayrollRun, status: 'pending_approval' }],
				error: null
			});

			let callCount = 0;
			mockSupabaseFrom.mockImplementation(() => {
				callCount++;
				if (callCount === 1) return updateMockQuery;
				return getMockQuery;
			});

			await finalizePayrollRun('run-123');

			expect(updateMockQuery.update).toHaveBeenCalled();
			const updateCall = (updateMockQuery.update as Mock).mock.calls[0][0];
			expect(updateCall.status).toBe('pending_approval');
		});
	});

	describe('revertToDraft', () => {
		it('reverts pending_approval run to draft', async () => {
			const checkMockQuery = createMockSupabaseQuery({
				data: { status: 'pending_approval' },
				error: null
			});

			const updateMockQuery = createMockSupabaseQuery({
				data: { ...mockDbPayrollRun, status: 'draft' },
				error: null
			});

			const getMockQuery = createMockSupabaseQuery({
				data: [{ ...mockDbPayrollRun, status: 'draft' }],
				error: null
			});

			let callCount = 0;
			mockSupabaseFrom.mockImplementation(() => {
				callCount++;
				if (callCount === 1) return checkMockQuery;
				if (callCount === 2) return updateMockQuery;
				return getMockQuery;
			});

			await revertToDraft('run-123');

			expect(mockSupabaseFrom).toHaveBeenCalledWith('payroll_runs');
		});

		it('returns error if run is not in pending_approval status', async () => {
			const checkMockQuery = createMockSupabaseQuery({
				data: { status: 'approved' },
				error: null
			});

			mockSupabaseFrom.mockReturnValue(checkMockQuery);

			const result = await revertToDraft('run-123');

			expect(result.data).toBeNull();
			expect(result.error).toContain("Cannot revert: payroll run is in 'approved' status");
		});
	});
});
