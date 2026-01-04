/**
 * Tests for Payroll Run Employee Functions
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock modules
const mockApiPost = vi.fn();
const mockApiDelete = vi.fn();
const mockGetCurrentUserId = vi.fn();

vi.mock('$lib/api/client', () => ({
	api: {
		get post() {
			return mockApiPost;
		},
		get delete() {
			return mockApiDelete;
		}
	}
}));

vi.mock('./helpers', () => ({
	get getCurrentUserId() {
		return mockGetCurrentUserId;
	}
}));

import { syncEmployeesToRun, addEmployeeToRun, removeEmployeeFromRun } from './run-employees';

describe('Payroll Run Employees', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		mockGetCurrentUserId.mockReturnValue('test-user-id');
	});

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

	describe('addEmployeeToRun', () => {
		it('adds employee and returns result', async () => {
			mockApiPost.mockResolvedValue({
				employeeId: 'emp-1',
				employeeName: 'John Doe'
			});

			const result = await addEmployeeToRun('run-123', 'emp-1');

			expect(mockApiPost).toHaveBeenCalledWith('/payroll/runs/run-123/employees', {
				employeeId: 'emp-1'
			});
			expect(result.data?.employeeId).toBe('emp-1');
			expect(result.data?.employeeName).toBe('John Doe');
		});
	});

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
});
