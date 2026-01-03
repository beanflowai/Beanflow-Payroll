/**
 * Tests for Payroll Run Lifecycle Functions
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock modules
const mockSupabaseFrom = vi.fn();
const mockApiPost = vi.fn();
const mockApiDelete = vi.fn();
const mockGetCurrentUserId = vi.fn();
const mockGetCurrentCompanyId = vi.fn();

vi.mock('$lib/api/supabase', () => ({
	supabase: {
		get from() { return mockSupabaseFrom; }
	}
}));

vi.mock('$lib/api/client', () => ({
	api: {
		get post() { return mockApiPost; },
		get delete() { return mockApiDelete; }
	}
}));

vi.mock('./helpers', () => ({
	get getCurrentUserId() { return mockGetCurrentUserId; },
	get getCurrentCompanyId() { return mockGetCurrentCompanyId; }
}));

import {
	createOrGetPayrollRun,
	deletePayrollRun
} from './run-lifecycle';

// Helper to create mock Supabase query chain
function createMockSupabaseQuery(options: {
	data?: unknown;
	error?: { message: string } | null;
}) {
	const { data = null, error = null } = options;
	const mockChain: Record<string, unknown> = {};
	const chainMethods = ['select', 'eq', 'neq', 'in', 'not', 'gte', 'lte', 'order', 'update', 'insert', 'delete'];
	chainMethods.forEach(method => {
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

describe('Payroll Run Lifecycle', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		mockGetCurrentUserId.mockReturnValue('test-user-id');
		mockGetCurrentCompanyId.mockReturnValue('test-company-id');
	});

	describe('createOrGetPayrollRun', () => {
		it('creates new run when none exists', async () => {
			mockApiPost.mockResolvedValue({
				run: {
					id: 'run-new',
					payDate: '2025-01-20',
					status: 'draft',
					totalEmployees: 5,
					totalGross: 10000,
					totalCppEmployee: 500,
					totalCppEmployer: 500,
					totalEiEmployee: 200,
					totalEiEmployer: 280,
					totalFederalTax: 1500,
					totalProvincialTax: 800,
					totalNetPay: 7000,
					totalEmployerCost: 780
				},
				created: true,
				recordsCount: 5
			});

			const mockQuery = createMockSupabaseQuery({
				data: [mockDbPayrollRun],
				error: null
			});

			mockSupabaseFrom.mockReturnValue(mockQuery);

			const result = await createOrGetPayrollRun('2025-01-20');

			expect(mockApiPost).toHaveBeenCalledWith('/payroll/runs/create-or-get', { payDate: '2025-01-20' });
			expect(result.data?.created).toBe(true);
		});

		it('returns existing run when one exists', async () => {
			mockApiPost.mockResolvedValue({
				run: {
					id: 'run-123',
					payDate: '2025-01-20',
					status: 'draft',
					totalEmployees: 5,
					totalGross: 10000,
					totalCppEmployee: 500,
					totalCppEmployer: 500,
					totalEiEmployee: 200,
					totalEiEmployer: 280,
					totalFederalTax: 1500,
					totalProvincialTax: 800,
					totalNetPay: 7000,
					totalEmployerCost: 780
				},
				created: false,
				recordsCount: 5
			});

			const mockQuery = createMockSupabaseQuery({
				data: [mockDbPayrollRun],
				error: null
			});

			mockSupabaseFrom.mockReturnValue(mockQuery);

			const result = await createOrGetPayrollRun('2025-01-20');

			expect(result.data?.created).toBe(false);
		});
	});

	describe('deletePayrollRun', () => {
		it('deletes draft run and returns result', async () => {
			mockApiDelete.mockResolvedValue({
				deleted: true,
				runId: 'run-123'
			});

			const result = await deletePayrollRun('run-123');

			expect(mockApiDelete).toHaveBeenCalledWith('/payroll/runs/run-123');
			expect(result.data?.deleted).toBe(true);
		});
	});
});
