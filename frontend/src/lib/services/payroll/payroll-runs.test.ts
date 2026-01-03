/**
 * Tests for Payroll Runs Service
 * Mocks Supabase and API client to test business logic
 */

import { describe, it, expect, vi, beforeEach, type Mock } from 'vitest';
import type { PayrollRunStatus } from '$lib/types/payroll';

// Mock modules using factory functions that return the mock objects
const mockSupabaseFrom = vi.fn();
const mockApiGet = vi.fn();
const mockApiPost = vi.fn();
const mockApiPatch = vi.fn();
const mockApiDelete = vi.fn();
const mockGetCurrentUserId = vi.fn();
const mockGetCurrentCompanyId = vi.fn();

vi.mock('$lib/api/supabase', () => {
	return {
		supabase: {
			get from() {
				return mockSupabaseFrom;
			}
		}
	};
});

vi.mock('$lib/api/client', () => {
	return {
		api: {
			get get() { return mockApiGet; },
			get post() { return mockApiPost; },
			get patch() { return mockApiPatch; },
			get delete() { return mockApiDelete; }
		}
	};
});

vi.mock('./helpers', () => {
	return {
		get getCurrentUserId() { return mockGetCurrentUserId; },
		get getCurrentCompanyId() { return mockGetCurrentCompanyId; },
		ensureAuthenticated: vi.fn()
	};
});

// Import after mocks are set up
import {
	getPayrollRunByPayDate,
	updatePayrollRunStatus,
	approvePayrollRun,
	cancelPayrollRun,
	listPayrollRuns,
	updatePayrollRecord,
	recalculatePayrollRun,
	finalizePayrollRun,
	revertToDraft,
	checkHasModifiedRecords,
	syncEmployeesToRun,
	createOrGetPayrollRun,
	addEmployeeToRun,
	removeEmployeeFromRun,
	getPaystubDownloadUrl,
	deletePayrollRun,
	sendPaystubs
} from './payroll-runs';

// Helper to create mock Supabase query chain
function createMockSupabaseQuery(options: {
	data?: unknown;
	error?: { message: string } | null;
	count?: number | null;
}) {
	const { data = null, error = null, count = null } = options;

	const mockChain: Record<string, unknown> = {};

	// All chainable methods return the same chain
	const chainMethods = ['select', 'eq', 'neq', 'in', 'not', 'gte', 'lte', 'order', 'update', 'insert', 'delete'];
	chainMethods.forEach(method => {
		mockChain[method] = vi.fn(() => mockChain);
	});

	// Terminal methods that resolve to data
	mockChain.single = vi.fn(() => Promise.resolve({ data, error }));
	mockChain.maybeSingle = vi.fn(() => Promise.resolve({ data, error }));

	// limit() returns a promise that resolves to data
	mockChain.limit = vi.fn(() => Promise.resolve({ data, error }));

	// range() returns a promise that resolves to data with count
	mockChain.range = vi.fn(() => Promise.resolve({ data, error, count }));

	return mockChain;
}

// Sample test data - using numbers to match actual DB behavior
const mockDbPayrollRun = {
	id: 'run-123',
	user_id: 'test-user-id',
	company_id: 'test-company-id',
	period_start: '2025-01-01',
	period_end: '2025-01-15',
	pay_date: '2025-01-20',
	status: 'draft' as PayrollRunStatus,
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

describe('Payroll Runs Service', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		// Reset mocks to default implementations
		mockGetCurrentUserId.mockReturnValue('test-user-id');
		mockGetCurrentCompanyId.mockReturnValue('test-company-id');
	});

	// ===========================================
	// getPayrollRunByPayDate Tests
	// ===========================================
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

	// ===========================================
	// updatePayrollRunStatus Tests
	// ===========================================
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
			mockQuery.single = vi.fn(() => Promise.resolve({
				data: null,
				error: { message: 'Update failed' }
			}));

			mockSupabaseFrom.mockReturnValue(mockQuery);

			const result = await updatePayrollRunStatus('run-123', 'approved');

			expect(result.data).toBeNull();
			expect(result.error).toBe('Update failed');
		});
	});

	// ===========================================
	// cancelPayrollRun Tests
	// ===========================================
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

	// ===========================================
	// listPayrollRuns Tests
	// ===========================================
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
			// totalDeductions = totalGross - totalNetPay
			expect(run.totalDeductions).toBe(10000 - 7000);
			// totalPayrollCost = totalGross + totalEmployerCost
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

	// ===========================================
	// approvePayrollRun Tests
	// ===========================================
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
			mockQuery.maybeSingle = vi.fn(() => Promise.resolve({
				data: { ...mockDbPayrollRun, status: 'approved' },
				error: null
			}));

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

	// ===========================================
	// recalculatePayrollRun Tests
	// ===========================================
	describe('recalculatePayrollRun', () => {
		it('calls backend recalculate endpoint', async () => {
			mockApiPost.mockResolvedValue({});

			const mockQuery = createMockSupabaseQuery({
				data: mockDbPayrollRun,
				error: null
			});
			mockQuery.maybeSingle = vi.fn(() => Promise.resolve({
				data: mockDbPayrollRun,
				error: null
			}));

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

	// ===========================================
	// finalizePayrollRun Tests
	// ===========================================
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

	// ===========================================
	// revertToDraft Tests
	// ===========================================
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

	// ===========================================
	// checkHasModifiedRecords Tests
	// ===========================================
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

	// ===========================================
	// syncEmployeesToRun Tests
	// ===========================================
	describe('syncEmployeesToRun', () => {
		it('calls sync-employees endpoint and returns result', async () => {
			mockApiPost.mockResolvedValue({
				addedCount: 2,
				addedEmployees: [
					{ employee_id: 'emp-1', employee_name: 'John Doe' },
					{ employee_id: 'emp-2', employee_name: 'Jane Smith' }
				],
				run: {
					id: 'run-123',
					payDate: '2025-01-20',
					status: 'draft',
					totalEmployees: 7,
					totalGross: 15000,
					totalNetPay: 10500
				}
			});

			const result = await syncEmployeesToRun('run-123');

			expect(mockApiPost).toHaveBeenCalledWith('/payroll/runs/run-123/sync-employees', {});
			expect(result.data?.addedCount).toBe(2);
			expect(result.data?.addedEmployees).toHaveLength(2);
		});
	});

	// ===========================================
	// createOrGetPayrollRun Tests
	// ===========================================
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

	// ===========================================
	// addEmployeeToRun Tests
	// ===========================================
	describe('addEmployeeToRun', () => {
		it('adds employee and returns result', async () => {
			mockApiPost.mockResolvedValue({
				employeeId: 'emp-1',
				employeeName: 'John Doe'
			});

			const result = await addEmployeeToRun('run-123', 'emp-1');

			expect(mockApiPost).toHaveBeenCalledWith('/payroll/runs/run-123/employees', { employeeId: 'emp-1' });
			expect(result.data?.employeeId).toBe('emp-1');
			expect(result.data?.employeeName).toBe('John Doe');
		});
	});

	// ===========================================
	// removeEmployeeFromRun Tests
	// ===========================================
	describe('removeEmployeeFromRun', () => {
		it('removes employee and returns result', async () => {
			mockApiDelete.mockResolvedValue({
				removed: true,
				employeeId: 'emp-1'
			});

			const result = await removeEmployeeFromRun('run-123', 'emp-1');

			expect(mockApiDelete).toHaveBeenCalledWith('/payroll/runs/run-123/employees/emp-1');
			expect(result.data?.removed).toBe(true);
		});
	});

	// ===========================================
	// getPaystubDownloadUrl Tests
	// ===========================================
	describe('getPaystubDownloadUrl', () => {
		it('returns presigned URL for paystub', async () => {
			mockApiGet.mockResolvedValue({
				storageKey: 'paystubs/2025/01/record-1.pdf',
				downloadUrl: 'https://storage.example.com/signed-url',
				expiresIn: 3600
			});

			const result = await getPaystubDownloadUrl('record-1');

			expect(mockApiGet).toHaveBeenCalledWith('/payroll/records/record-1/paystub-url');
			expect(result.data?.downloadUrl).toContain('signed-url');
		});
	});

	// ===========================================
	// deletePayrollRun Tests
	// ===========================================
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

	// ===========================================
	// sendPaystubs Tests
	// ===========================================
	describe('sendPaystubs', () => {
		it('sends paystubs and returns result', async () => {
			mockApiPost.mockResolvedValue({
				sent: 5,
				sent_record_ids: ['r1', 'r2', 'r3', 'r4', 'r5'],
				errors: null
			});

			const result = await sendPaystubs('run-123');

			expect(mockApiPost).toHaveBeenCalledWith('/payroll/runs/run-123/send-paystubs', {});
			expect(result.data?.sent).toBe(5);
			expect(result.data?.errors).toBeNull();
		});

		it('returns partial success with errors', async () => {
			mockApiPost.mockResolvedValue({
				sent: 3,
				sent_record_ids: ['r1', 'r2', 'r3'],
				errors: ['Failed to send to emp-4', 'Failed to send to emp-5']
			});

			const result = await sendPaystubs('run-123');

			expect(result.data?.sent).toBe(3);
			expect(result.data?.errors).toHaveLength(2);
		});
	});

	// ===========================================
	// updatePayrollRecord Tests
	// ===========================================
	describe('updatePayrollRecord', () => {
		it('sends correct request body for hours update', async () => {
			mockApiPatch.mockResolvedValue({});

			const mockQuery = createMockSupabaseQuery({
				data: mockDbPayrollRun,
				error: null
			});
			mockQuery.maybeSingle = vi.fn(() => Promise.resolve({
				data: mockDbPayrollRun,
				error: null
			}));

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
			mockQuery.maybeSingle = vi.fn(() => Promise.resolve({
				data: mockDbPayrollRun,
				error: null
			}));

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
			mockQuery.maybeSingle = vi.fn(() => Promise.resolve({
				data: mockDbPayrollRun,
				error: null
			}));

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
				adjustments: [{
					id: 'adj-1',
					type: 'bonus',
					amount: 500,
					description: 'Performance bonus',
					taxable: true
				}]
			});

			expect(mockApiPatch).toHaveBeenCalledWith(
				'/payroll/runs/run-123/records/record-1',
				expect.objectContaining({
					adjustments: [{
						type: 'bonus',
						amount: 500,
						description: 'Performance bonus',
						taxable: true
					}]
				})
			);
		});
	});
});
