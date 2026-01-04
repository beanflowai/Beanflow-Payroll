/**
 * Tests for Pay Groups Service
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
	}),
	DEFAULT_EARNINGS_CONFIG: {},
	DEFAULT_TAXABLE_BENEFITS_CONFIG: {},
	DEFAULT_DEDUCTIONS_CONFIG: {},
	DEFAULT_OVERTIME_POLICY: {},
	DEFAULT_GROUP_BENEFITS: {}
}));

import { supabase } from '$lib/api/supabase';
import {
	getPayGroupsForPeriodEnd,
	getPayGroupsWithEmployeesForPeriodEnd,
	getPayGroupsForPayDate,
	getPayGroupsWithEmployeesForPayDate
} from './pay-groups';
import { getCurrentUserId } from './helpers';

const mockSupabase = vi.mocked(supabase);
const mockGetCurrentUserId = vi.mocked(getCurrentUserId);

describe('getPayGroupsForPeriodEnd', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		mockGetCurrentUserId.mockReturnValue('user-123');
	});

	it('returns null when no pay groups found', async () => {
		const mockFrom = vi.fn().mockImplementation((table: string) => {
			if (table === 'v_pay_group_summary') {
				return {
					select: vi.fn().mockReturnValue({
						eq: vi.fn().mockResolvedValue({
							data: [],
							error: null
						})
					})
				};
			}
			return {};
		});

		mockSupabase.from.mockImplementation(mockFrom);

		const result = await getPayGroupsForPeriodEnd('2025-01-31');

		expect(result.data).toBeNull();
		expect(result.error).toBeNull();
	});

	it('returns pay groups with calculated pay date', async () => {
		const payGroupData = [
			{
				id: 'pg-1',
				name: 'Salaried',
				pay_frequency: 'bi_weekly',
				employment_type: 'full_time',
				employee_count: 5
			}
		];

		const mockFrom = vi.fn().mockImplementation((table: string) => {
			if (table === 'v_pay_group_summary') {
				return {
					select: vi.fn().mockReturnValue({
						eq: vi.fn().mockResolvedValue({
							data: payGroupData,
							error: null
						})
					})
				};
			}
			if (table === 'payroll_runs') {
				return {
					select: vi.fn().mockReturnValue({
						eq: vi.fn().mockReturnValue({
							maybeSingle: vi.fn().mockResolvedValue({
								data: null,
								error: null
							})
						})
					})
				};
			}
			return {};
		});

		mockSupabase.from.mockImplementation(mockFrom);

		const result = await getPayGroupsForPeriodEnd('2025-01-31');

		expect(result.data).not.toBeNull();
		expect(result.data!.periodEnd).toBe('2025-01-31');
		expect(result.data!.payDate).toBe('2025-02-06');
		expect(result.data!.payGroups).toHaveLength(1);
		expect(result.data!.totalEmployees).toBe(5);
	});

	it('includes existing run info', async () => {
		const payGroupData = [
			{
				id: 'pg-1',
				name: 'Salaried',
				pay_frequency: 'bi_weekly',
				employment_type: 'full_time',
				employee_count: 5
			}
		];

		const mockFrom = vi.fn().mockImplementation((table: string) => {
			if (table === 'v_pay_group_summary') {
				return {
					select: vi.fn().mockReturnValue({
						eq: vi.fn().mockResolvedValue({
							data: payGroupData,
							error: null
						})
					})
				};
			}
			if (table === 'payroll_runs') {
				return {
					select: vi.fn().mockReturnValue({
						eq: vi.fn().mockReturnValue({
							maybeSingle: vi.fn().mockResolvedValue({
								data: { id: 'run-123', status: 'draft' },
								error: null
							})
						})
					})
				};
			}
			return {};
		});

		mockSupabase.from.mockImplementation(mockFrom);

		const result = await getPayGroupsForPeriodEnd('2025-01-31');

		expect(result.data!.runId).toBe('run-123');
		expect(result.data!.runStatus).toBe('draft');
	});

	it('handles query error', async () => {
		const mockFrom = vi.fn().mockImplementation(() => ({
			select: vi.fn().mockReturnValue({
				eq: vi.fn().mockResolvedValue({
					data: null,
					error: { message: 'Database error' }
				})
			})
		}));

		mockSupabase.from.mockImplementation(mockFrom);

		const result = await getPayGroupsForPeriodEnd('2025-01-31');

		expect(result.data).toBeNull();
		expect(result.error).toBe('Database error');
	});

	it('handles exception', async () => {
		mockGetCurrentUserId.mockImplementation(() => {
			throw new Error('Auth error');
		});

		const result = await getPayGroupsForPeriodEnd('2025-01-31');

		expect(result.data).toBeNull();
		expect(result.error).toBe('Auth error');
	});

	it('handles null employee_count', async () => {
		const payGroupData = [
			{
				id: 'pg-1',
				name: 'Empty',
				pay_frequency: 'bi_weekly',
				employment_type: 'full_time',
				employee_count: null
			}
		];

		const mockFrom = vi.fn().mockImplementation((table: string) => {
			if (table === 'v_pay_group_summary') {
				return {
					select: vi.fn().mockReturnValue({
						eq: vi.fn().mockResolvedValue({
							data: payGroupData,
							error: null
						})
					})
				};
			}
			if (table === 'payroll_runs') {
				return {
					select: vi.fn().mockReturnValue({
						eq: vi.fn().mockReturnValue({
							maybeSingle: vi.fn().mockResolvedValue({
								data: null,
								error: null
							})
						})
					})
				};
			}
			return {};
		});

		mockSupabase.from.mockImplementation(mockFrom);

		const result = await getPayGroupsForPeriodEnd('2025-01-31');

		expect(result.data!.totalEmployees).toBe(0);
	});
});

describe('getPayGroupsWithEmployeesForPeriodEnd', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		mockGetCurrentUserId.mockReturnValue('user-123');
	});

	it('returns null when no pay groups found', async () => {
		const mockFrom = vi.fn().mockImplementation((table: string) => {
			if (table === 'v_pay_group_summary') {
				return {
					select: vi.fn().mockReturnValue({
						eq: vi.fn().mockResolvedValue({
							data: [],
							error: null
						})
					})
				};
			}
			return {};
		});

		mockSupabase.from.mockImplementation(mockFrom);

		const result = await getPayGroupsWithEmployeesForPeriodEnd('2025-01-31');

		expect(result.data).toBeNull();
		expect(result.error).toBeNull();
	});

	it('returns pay groups with employees', async () => {
		const payGroupData = [
			{
				id: 'pg-1',
				name: 'Salaried',
				pay_frequency: 'bi_weekly',
				employment_type: 'full_time',
				leave_enabled: true,
				overtime_policy: null,
				group_benefits: null,
				earnings_config: null,
				taxable_benefits_config: null,
				deductions_config: null
			}
		];

		const employeeData = [
			{
				id: 'emp-1',
				first_name: 'John',
				last_name: 'Doe',
				province_of_employment: 'ON',
				pay_group_id: 'pg-1',
				annual_salary: 78000,
				hourly_rate: null
			}
		];

		const mockFrom = vi.fn().mockImplementation((table: string) => {
			if (table === 'v_pay_group_summary') {
				return {
					select: vi.fn().mockReturnValue({
						eq: vi.fn().mockResolvedValue({
							data: payGroupData,
							error: null
						})
					})
				};
			}
			if (table === 'employees') {
				return {
					select: vi.fn().mockReturnValue({
						eq: vi.fn().mockReturnValue({
							eq: vi.fn().mockReturnValue({
								eq: vi.fn().mockReturnValue({
									is: vi.fn().mockReturnValue({
										order: vi.fn().mockReturnValue({
											order: vi.fn().mockResolvedValue({
												data: employeeData,
												error: null
											})
										})
									})
								})
							})
						})
					})
				};
			}
			if (table === 'statutory_holidays') {
				return {
					select: vi.fn().mockReturnValue({
						gte: vi.fn().mockReturnValue({
							lte: vi.fn().mockReturnValue({
								in: vi.fn().mockReturnValue({
									eq: vi.fn().mockResolvedValue({
										data: [],
										error: null
									})
								})
							})
						})
					})
				};
			}
			return {};
		});

		mockSupabase.from.mockImplementation(mockFrom);

		const result = await getPayGroupsWithEmployeesForPeriodEnd('2025-01-31');

		expect(result.data).not.toBeNull();
		expect(result.data!.periodEnd).toBe('2025-01-31');
		expect(result.data!.payGroups).toHaveLength(1);
		expect(result.data!.payGroups[0].employees).toHaveLength(1);
		expect(result.data!.payGroups[0].employees[0].firstName).toBe('John');
		expect(result.data!.totalEmployees).toBe(1);
	});

	it('identifies hourly employees correctly', async () => {
		const payGroupData = [
			{
				id: 'pg-1',
				name: 'Hourly',
				pay_frequency: 'bi_weekly',
				employment_type: 'full_time'
			}
		];

		const employeeData = [
			{
				id: 'emp-1',
				first_name: 'Jane',
				last_name: 'Smith',
				province_of_employment: 'BC',
				pay_group_id: 'pg-1',
				annual_salary: null,
				hourly_rate: 25
			}
		];

		const mockFrom = vi.fn().mockImplementation((table: string) => {
			if (table === 'v_pay_group_summary') {
				return {
					select: vi.fn().mockReturnValue({
						eq: vi.fn().mockResolvedValue({
							data: payGroupData,
							error: null
						})
					})
				};
			}
			if (table === 'employees') {
				return {
					select: vi.fn().mockReturnValue({
						eq: vi.fn().mockReturnValue({
							eq: vi.fn().mockReturnValue({
								eq: vi.fn().mockReturnValue({
									is: vi.fn().mockReturnValue({
										order: vi.fn().mockReturnValue({
											order: vi.fn().mockResolvedValue({
												data: employeeData,
												error: null
											})
										})
									})
								})
							})
						})
					})
				};
			}
			if (table === 'statutory_holidays') {
				return {
					select: vi.fn().mockReturnValue({
						gte: vi.fn().mockReturnValue({
							lte: vi.fn().mockReturnValue({
								in: vi.fn().mockReturnValue({
									eq: vi.fn().mockResolvedValue({
										data: [],
										error: null
									})
								})
							})
						})
					})
				};
			}
			return {};
		});

		mockSupabase.from.mockImplementation(mockFrom);

		const result = await getPayGroupsWithEmployeesForPeriodEnd('2025-01-31');

		expect(result.data!.payGroups[0].employees[0].compensationType).toBe('hourly');
		expect(result.data!.payGroups[0].employees[0].hourlyRate).toBe(25);
	});

	it('includes statutory holidays for employee provinces', async () => {
		const payGroupData = [
			{
				id: 'pg-1',
				name: 'Mixed',
				pay_frequency: 'bi_weekly',
				employment_type: 'full_time'
			}
		];

		const employeeData = [
			{
				id: 'emp-1',
				first_name: 'John',
				last_name: 'Doe',
				province_of_employment: 'ON',
				pay_group_id: 'pg-1',
				annual_salary: 78000,
				hourly_rate: null
			}
		];

		const holidayData = [
			{
				holiday_date: '2025-01-20',
				name: 'Family Day',
				province: 'ON'
			}
		];

		const mockFrom = vi.fn().mockImplementation((table: string) => {
			if (table === 'v_pay_group_summary') {
				return {
					select: vi.fn().mockReturnValue({
						eq: vi.fn().mockResolvedValue({
							data: payGroupData,
							error: null
						})
					})
				};
			}
			if (table === 'employees') {
				return {
					select: vi.fn().mockReturnValue({
						eq: vi.fn().mockReturnValue({
							eq: vi.fn().mockReturnValue({
								eq: vi.fn().mockReturnValue({
									is: vi.fn().mockReturnValue({
										order: vi.fn().mockReturnValue({
											order: vi.fn().mockResolvedValue({
												data: employeeData,
												error: null
											})
										})
									})
								})
							})
						})
					})
				};
			}
			if (table === 'statutory_holidays') {
				return {
					select: vi.fn().mockReturnValue({
						gte: vi.fn().mockReturnValue({
							lte: vi.fn().mockReturnValue({
								in: vi.fn().mockReturnValue({
									eq: vi.fn().mockResolvedValue({
										data: holidayData,
										error: null
									})
								})
							})
						})
					})
				};
			}
			return {};
		});

		mockSupabase.from.mockImplementation(mockFrom);

		const result = await getPayGroupsWithEmployeesForPeriodEnd('2025-01-31');

		expect(result.data!.holidays).toHaveLength(1);
		expect(result.data!.holidays[0].name).toBe('Family Day');
	});

	it('handles pay group query error', async () => {
		const mockFrom = vi.fn().mockImplementation(() => ({
			select: vi.fn().mockReturnValue({
				eq: vi.fn().mockResolvedValue({
					data: null,
					error: { message: 'Query failed' }
				})
			})
		}));

		mockSupabase.from.mockImplementation(mockFrom);

		const result = await getPayGroupsWithEmployeesForPeriodEnd('2025-01-31');

		expect(result.data).toBeNull();
		expect(result.error).toBe('Query failed');
	});

	it('continues when employee query fails for one pay group', async () => {
		const payGroupData = [
			{ id: 'pg-1', name: 'Group1', pay_frequency: 'bi_weekly', employment_type: 'full_time' },
			{ id: 'pg-2', name: 'Group2', pay_frequency: 'bi_weekly', employment_type: 'full_time' }
		];

		let employeeQueryCount = 0;

		const mockFrom = vi.fn().mockImplementation((table: string) => {
			if (table === 'v_pay_group_summary') {
				return {
					select: vi.fn().mockReturnValue({
						eq: vi.fn().mockResolvedValue({
							data: payGroupData,
							error: null
						})
					})
				};
			}
			if (table === 'employees') {
				employeeQueryCount++;
				if (employeeQueryCount === 1) {
					// First query fails
					return {
						select: vi.fn().mockReturnValue({
							eq: vi.fn().mockReturnValue({
								eq: vi.fn().mockReturnValue({
									eq: vi.fn().mockReturnValue({
										is: vi.fn().mockReturnValue({
											order: vi.fn().mockReturnValue({
												order: vi.fn().mockResolvedValue({
													data: null,
													error: { message: 'Query failed' }
												})
											})
										})
									})
								})
							})
						})
					};
				}
				// Second query succeeds
				return {
					select: vi.fn().mockReturnValue({
						eq: vi.fn().mockReturnValue({
							eq: vi.fn().mockReturnValue({
								eq: vi.fn().mockReturnValue({
									is: vi.fn().mockReturnValue({
										order: vi.fn().mockReturnValue({
											order: vi.fn().mockResolvedValue({
												data: [
													{
														id: 'emp-1',
														first_name: 'Jane',
														last_name: 'Smith',
														province_of_employment: 'BC',
														pay_group_id: 'pg-2',
														annual_salary: 50000,
														hourly_rate: null
													}
												],
												error: null
											})
										})
									})
								})
							})
						})
					})
				};
			}
			if (table === 'statutory_holidays') {
				return {
					select: vi.fn().mockReturnValue({
						gte: vi.fn().mockReturnValue({
							lte: vi.fn().mockReturnValue({
								in: vi.fn().mockReturnValue({
									eq: vi.fn().mockResolvedValue({
										data: [],
										error: null
									})
								})
							})
						})
					})
				};
			}
			return {};
		});

		mockSupabase.from.mockImplementation(mockFrom);

		const result = await getPayGroupsWithEmployeesForPeriodEnd('2025-01-31');

		expect(result.data).not.toBeNull();
		expect(result.data!.payGroups).toHaveLength(1);
		expect(result.data!.totalEmployees).toBe(1);
	});

	it('handles exception', async () => {
		mockGetCurrentUserId.mockImplementation(() => {
			throw new Error('Unexpected error');
		});

		const result = await getPayGroupsWithEmployeesForPeriodEnd('2025-01-31');

		expect(result.data).toBeNull();
		expect(result.error).toBe('Unexpected error');
	});

	it('skips holiday query when no provinces', async () => {
		const payGroupData = [
			{
				id: 'pg-1',
				name: 'Empty',
				pay_frequency: 'bi_weekly',
				employment_type: 'full_time'
			}
		];

		const mockFrom = vi.fn().mockImplementation((table: string) => {
			if (table === 'v_pay_group_summary') {
				return {
					select: vi.fn().mockReturnValue({
						eq: vi.fn().mockResolvedValue({
							data: payGroupData,
							error: null
						})
					})
				};
			}
			if (table === 'employees') {
				return {
					select: vi.fn().mockReturnValue({
						eq: vi.fn().mockReturnValue({
							eq: vi.fn().mockReturnValue({
								eq: vi.fn().mockReturnValue({
									is: vi.fn().mockReturnValue({
										order: vi.fn().mockReturnValue({
											order: vi.fn().mockResolvedValue({
												data: [],
												error: null
											})
										})
									})
								})
							})
						})
					})
				};
			}
			return {};
		});

		mockSupabase.from.mockImplementation(mockFrom);

		const result = await getPayGroupsWithEmployeesForPeriodEnd('2025-01-31');

		expect(result.data!.holidays).toEqual([]);
	});
});

describe('deprecated aliases', () => {
	it('getPayGroupsForPayDate is alias for getPayGroupsForPeriodEnd', () => {
		expect(getPayGroupsForPayDate).toBe(getPayGroupsForPeriodEnd);
	});

	it('getPayGroupsWithEmployeesForPayDate is alias for getPayGroupsWithEmployeesForPeriodEnd', () => {
		expect(getPayGroupsWithEmployeesForPayDate).toBe(getPayGroupsWithEmployeesForPeriodEnd);
	});
});
