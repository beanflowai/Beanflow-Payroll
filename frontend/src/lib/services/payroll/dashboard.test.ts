/**
 * Tests for Payroll Dashboard Service
 */

import { describe, expect, it, vi, beforeEach } from 'vitest';

// Mock modules before imports
vi.mock('$lib/api/supabase', () => ({
	supabase: {
		from: vi.fn()
	}
}));

vi.mock('./helpers', () => ({
	getCurrentUserId: vi.fn(() => 'user-123'),
	getCurrentCompanyId: vi.fn(() => 'company-456')
}));

vi.mock('$lib/types/pay-group', () => ({
	calculatePayDate: vi.fn((periodEnd: string) => {
		const date = new Date(periodEnd);
		date.setDate(date.getDate() + 6);
		return date.toISOString().split('T')[0];
	})
}));

vi.mock('./run-queries', () => ({
	listPayrollRuns: vi.fn()
}));

import { supabase } from '$lib/api/supabase';
import {
	checkPayrollPageStatus,
	getUpcomingPeriods,
	getPayrollDashboardStats,
	getRecentCompletedRuns
} from './dashboard';
import { getCurrentUserId } from './helpers';
import { listPayrollRuns } from './run-queries';

const mockSupabase = vi.mocked(supabase);
const mockGetCurrentUserId = vi.mocked(getCurrentUserId);
const mockListPayrollRuns = vi.mocked(listPayrollRuns);

describe('checkPayrollPageStatus', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('returns no_pay_groups when no pay groups exist', async () => {
		const mockSelect = vi.fn().mockReturnValue({
			eq: vi.fn().mockReturnValue({
				limit: vi.fn().mockResolvedValue({
					data: [],
					error: null
				})
			})
		});

		mockSupabase.from.mockReturnValue({
			select: mockSelect
		} as never);

		const result = await checkPayrollPageStatus();

		expect(result.data).toEqual({ status: 'no_pay_groups' });
		expect(result.error).toBeNull();
	});

	it('returns no_employees when pay groups exist but no employees', async () => {
		const mockSelect = vi.fn().mockReturnValue({
			eq: vi.fn().mockReturnValue({
				limit: vi.fn().mockResolvedValue({
					data: [
						{ id: 'pg-1', employee_count: 0 },
						{ id: 'pg-2', employee_count: 0 }
					],
					error: null
				})
			})
		});

		mockSupabase.from.mockReturnValue({
			select: mockSelect
		} as never);

		const result = await checkPayrollPageStatus();

		expect(result.data).toEqual({
			status: 'no_employees',
			payGroupCount: 2
		});
		expect(result.error).toBeNull();
	});

	it('returns ready when pay groups and employees exist', async () => {
		const mockSelect = vi.fn().mockReturnValue({
			eq: vi.fn().mockReturnValue({
				limit: vi.fn().mockResolvedValue({
					data: [
						{ id: 'pg-1', employee_count: 5 },
						{ id: 'pg-2', employee_count: 3 }
					],
					error: null
				})
			})
		});

		mockSupabase.from.mockReturnValue({
			select: mockSelect
		} as never);

		const result = await checkPayrollPageStatus();

		expect(result.data).toEqual({
			status: 'ready',
			payGroupCount: 2,
			employeeCount: 8
		});
		expect(result.error).toBeNull();
	});

	it('returns error when query fails', async () => {
		const mockSelect = vi.fn().mockReturnValue({
			eq: vi.fn().mockReturnValue({
				limit: vi.fn().mockResolvedValue({
					data: null,
					error: { message: 'Database connection failed' }
				})
			})
		});

		mockSupabase.from.mockReturnValue({
			select: mockSelect
		} as never);

		const result = await checkPayrollPageStatus();

		expect(result.data).toBeNull();
		expect(result.error).toBe('Database connection failed');
	});

	it('handles exception', async () => {
		mockGetCurrentUserId.mockImplementation(() => {
			throw new Error('User not authenticated');
		});

		const result = await checkPayrollPageStatus();

		expect(result.data).toBeNull();
		expect(result.error).toBe('User not authenticated');
	});

	it('handles null employee_count', async () => {
		// Reset mock to return proper value
		mockGetCurrentUserId.mockReturnValue('user-123');

		const mockSelect = vi.fn().mockReturnValue({
			eq: vi.fn().mockReturnValue({
				limit: vi.fn().mockResolvedValue({
					data: [
						{ id: 'pg-1', employee_count: null },
						{ id: 'pg-2', employee_count: 5 }
					],
					error: null
				})
			})
		});

		mockSupabase.from.mockReturnValue({
			select: mockSelect
		} as never);

		const result = await checkPayrollPageStatus();

		expect(result.data).toEqual({
			status: 'ready',
			payGroupCount: 2,
			employeeCount: 5
		});
	});
});

describe('getUpcomingPeriods', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		mockGetCurrentUserId.mockReturnValue('user-123');
	});

	it('returns empty array when no pay groups exist', async () => {
		const mockSelect = vi.fn().mockReturnValue({
			eq: vi.fn().mockReturnValue({
				order: vi.fn().mockResolvedValue({
					data: [],
					error: null
				})
			})
		});

		mockSupabase.from.mockReturnValue({
			select: mockSelect
		} as never);

		const result = await getUpcomingPeriods();

		expect(result.data).toEqual([]);
		expect(result.error).toBeNull();
	});

	it('groups pay groups by period_end', async () => {
		const payGroupData = [
			{
				id: 'pg-1',
				name: 'Salaried',
				pay_frequency: 'bi_weekly',
				employment_type: 'full_time',
				next_period_end: '2025-01-31',
				employee_count: 5
			},
			{
				id: 'pg-2',
				name: 'Hourly',
				pay_frequency: 'bi_weekly',
				employment_type: 'full_time',
				next_period_end: '2025-01-31',
				employee_count: 3
			}
		];

		const mockFrom = vi.fn().mockImplementation((table: string) => {
			if (table === 'v_pay_group_summary') {
				return {
					select: vi.fn().mockReturnValue({
						eq: vi.fn().mockReturnValue({
							order: vi.fn().mockResolvedValue({
								data: payGroupData,
								error: null
							})
						})
					})
				};
			}
			if (table === 'payroll_runs') {
				return {
					select: vi.fn().mockReturnValue({
						eq: vi.fn().mockReturnValue({
							in: vi.fn().mockResolvedValue({
								data: [],
								error: null
							})
						})
					})
				};
			}
			return {};
		});

		mockSupabase.from.mockImplementation(mockFrom);

		const result = await getUpcomingPeriods();

		expect(result.data).toHaveLength(1);
		expect(result.data![0].periodEnd).toBe('2025-01-31');
		expect(result.data![0].totalEmployees).toBe(8);
		expect(result.data![0].payGroups).toHaveLength(2);
	});

	it('includes existing payroll run info', async () => {
		const payGroupData = [
			{
				id: 'pg-1',
				name: 'Salaried',
				pay_frequency: 'bi_weekly',
				employment_type: 'full_time',
				next_period_end: '2025-01-31',
				employee_count: 5
			}
		];

		const runData = [{ id: 'run-123', period_end: '2025-01-31', status: 'draft' }];

		const mockFrom = vi.fn().mockImplementation((table: string) => {
			if (table === 'v_pay_group_summary') {
				return {
					select: vi.fn().mockReturnValue({
						eq: vi.fn().mockReturnValue({
							order: vi.fn().mockResolvedValue({
								data: payGroupData,
								error: null
							})
						})
					})
				};
			}
			if (table === 'payroll_runs') {
				return {
					select: vi.fn().mockReturnValue({
						eq: vi.fn().mockReturnValue({
							in: vi.fn().mockResolvedValue({
								data: runData,
								error: null
							})
						})
					})
				};
			}
			return {};
		});

		mockSupabase.from.mockImplementation(mockFrom);

		const result = await getUpcomingPeriods();

		expect(result.data![0].runId).toBe('run-123');
		expect(result.data![0].runStatus).toBe('draft');
	});

	it('skips pay groups with null next_period_end', async () => {
		const payGroupData = [
			{
				id: 'pg-1',
				name: 'Valid',
				next_period_end: '2025-01-31',
				employee_count: 5
			},
			{
				id: 'pg-2',
				name: 'No Period',
				next_period_end: null,
				employee_count: 3
			}
		];

		const mockFrom = vi.fn().mockImplementation((table: string) => {
			if (table === 'v_pay_group_summary') {
				return {
					select: vi.fn().mockReturnValue({
						eq: vi.fn().mockReturnValue({
							order: vi.fn().mockResolvedValue({
								data: payGroupData,
								error: null
							})
						})
					})
				};
			}
			if (table === 'payroll_runs') {
				return {
					select: vi.fn().mockReturnValue({
						eq: vi.fn().mockReturnValue({
							in: vi.fn().mockResolvedValue({
								data: [],
								error: null
							})
						})
					})
				};
			}
			return {};
		});

		mockSupabase.from.mockImplementation(mockFrom);

		const result = await getUpcomingPeriods();

		expect(result.data).toHaveLength(1);
		expect(result.data![0].totalEmployees).toBe(5);
	});

	it('handles query error', async () => {
		const mockSelect = vi.fn().mockReturnValue({
			eq: vi.fn().mockReturnValue({
				order: vi.fn().mockResolvedValue({
					data: null,
					error: { message: 'Query failed' }
				})
			})
		});

		mockSupabase.from.mockReturnValue({
			select: mockSelect
		} as never);

		const result = await getUpcomingPeriods();

		expect(result.data).toBeNull();
		expect(result.error).toBe('Query failed');
	});

	it('handles exception', async () => {
		mockGetCurrentUserId.mockImplementation(() => {
			throw new Error('Authentication error');
		});

		const result = await getUpcomingPeriods();

		expect(result.data).toBeNull();
		expect(result.error).toBe('Authentication error');
	});

	it('sorts periods by period_end date', async () => {
		const payGroupData = [
			{
				id: 'pg-2',
				name: 'Later',
				next_period_end: '2025-02-14',
				employee_count: 3
			},
			{
				id: 'pg-1',
				name: 'Earlier',
				next_period_end: '2025-01-31',
				employee_count: 5
			}
		];

		const mockFrom = vi.fn().mockImplementation((table: string) => {
			if (table === 'v_pay_group_summary') {
				return {
					select: vi.fn().mockReturnValue({
						eq: vi.fn().mockReturnValue({
							order: vi.fn().mockResolvedValue({
								data: payGroupData,
								error: null
							})
						})
					})
				};
			}
			if (table === 'payroll_runs') {
				return {
					select: vi.fn().mockReturnValue({
						eq: vi.fn().mockReturnValue({
							in: vi.fn().mockResolvedValue({
								data: [],
								error: null
							})
						})
					})
				};
			}
			return {};
		});

		mockSupabase.from.mockImplementation(mockFrom);

		const result = await getUpcomingPeriods();

		expect(result.data).toHaveLength(2);
		expect(result.data![0].periodEnd).toBe('2025-01-31');
		expect(result.data![1].periodEnd).toBe('2025-02-14');
	});
});

describe('getPayrollDashboardStats', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		mockGetCurrentUserId.mockReturnValue('user-123');
	});

	it('returns stats with upcoming periods', async () => {
		const payGroupData = [
			{
				id: 'pg-1',
				name: 'Salaried',
				next_period_end: '2025-01-31',
				employee_count: 5
			}
		];

		const mockFrom = vi.fn().mockImplementation((table: string) => {
			if (table === 'v_pay_group_summary') {
				return {
					select: vi.fn().mockReturnValue({
						eq: vi.fn().mockReturnValue({
							order: vi.fn().mockResolvedValue({
								data: payGroupData,
								error: null
							})
						})
					})
				};
			}
			if (table === 'payroll_runs') {
				return {
					select: vi.fn().mockReturnValue({
						eq: vi.fn().mockReturnValue({
							in: vi.fn().mockResolvedValue({
								data: [],
								error: null
							})
						})
					})
				};
			}
			return {};
		});

		mockSupabase.from.mockImplementation(mockFrom);

		const result = await getPayrollDashboardStats();

		expect(result.data).not.toBeNull();
		expect(result.data!.upcomingCount).toBe(1);
		expect(result.data!.nextPayDate).toBe('2025-01-31');
		expect(result.data!.nextPayDateEmployees).toBe(5);
	});

	it('returns empty stats when no periods', async () => {
		const mockSelect = vi.fn().mockReturnValue({
			eq: vi.fn().mockReturnValue({
				order: vi.fn().mockResolvedValue({
					data: [],
					error: null
				})
			})
		});

		mockSupabase.from.mockReturnValue({
			select: mockSelect
		} as never);

		const result = await getPayrollDashboardStats();

		expect(result.data).not.toBeNull();
		expect(result.data!.upcomingCount).toBe(0);
		expect(result.data!.nextPayDate).toBeNull();
		expect(result.data!.nextPayDateEmployees).toBe(0);
	});

	it('handles error from getUpcomingPeriods', async () => {
		const mockSelect = vi.fn().mockReturnValue({
			eq: vi.fn().mockReturnValue({
				order: vi.fn().mockResolvedValue({
					data: null,
					error: { message: 'Database error' }
				})
			})
		});

		mockSupabase.from.mockReturnValue({
			select: mockSelect
		} as never);

		const result = await getPayrollDashboardStats();

		expect(result.data).toBeNull();
		expect(result.error).toBe('Database error');
	});

	it('handles exception', async () => {
		mockGetCurrentUserId.mockImplementation(() => {
			throw new Error('Unexpected error');
		});

		const result = await getPayrollDashboardStats();

		expect(result.data).toBeNull();
		expect(result.error).toBe('Unexpected error');
	});
});

describe('getRecentCompletedRuns', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('calls listPayrollRuns with correct options', async () => {
		mockListPayrollRuns.mockResolvedValue({
			data: [],
			error: null
		});

		await getRecentCompletedRuns(5);

		expect(mockListPayrollRuns).toHaveBeenCalledWith({
			excludeStatuses: ['draft', 'pending_approval', 'cancelled'],
			limit: 5,
			offset: 0
		});
	});

	it('uses default limit of 5', async () => {
		mockListPayrollRuns.mockResolvedValue({
			data: [],
			error: null
		});

		await getRecentCompletedRuns();

		expect(mockListPayrollRuns).toHaveBeenCalledWith(
			expect.objectContaining({
				limit: 5
			})
		);
	});

	it('returns completed runs', async () => {
		const mockRuns = [
			{ id: 'run-1', status: 'approved', payDate: '2025-01-31' },
			{ id: 'run-2', status: 'paid', payDate: '2025-01-17' }
		];

		mockListPayrollRuns.mockResolvedValue({
			data: mockRuns as never,
			error: null
		});

		const result = await getRecentCompletedRuns();

		expect(result.data).toHaveLength(2);
		expect(result.error).toBeNull();
	});

	it('returns error when listPayrollRuns fails', async () => {
		mockListPayrollRuns.mockResolvedValue({
			data: null,
			error: 'Query failed'
		});

		const result = await getRecentCompletedRuns();

		expect(result.data).toBeNull();
		expect(result.error).toBe('Query failed');
	});

	it('handles exception', async () => {
		mockListPayrollRuns.mockRejectedValue(new Error('Network error'));

		const result = await getRecentCompletedRuns();

		expect(result.data).toBeNull();
		expect(result.error).toBe('Network error');
	});
});
