/**
 * Tests for Payroll Calculation Service
 */

import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';

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

vi.mock('./helpers', () => ({
	getCurrentUserId: vi.fn(() => 'user-123'),
	getCurrentCompanyId: vi.fn(() => 'company-456'),
	getProvincialBpa: vi.fn(() => '12747.00')
}));

vi.mock('./pay-groups', () => ({
	getPayGroupsWithEmployeesForPayDate: vi.fn()
}));

vi.mock('./run-queries', () => ({
	getPayrollRunByPayDate: vi.fn()
}));

import { supabase } from '$lib/api/supabase';
import { api } from '$lib/api/client';
import { startPayrollRun } from './calculation';
import { getPayGroupsWithEmployeesForPayDate } from './pay-groups';
import { getPayrollRunByPayDate } from './run-queries';

const mockSupabase = vi.mocked(supabase);
const mockApi = vi.mocked(api);
const mockGetPayGroups = vi.mocked(getPayGroupsWithEmployeesForPayDate);
const mockGetPayrollRun = vi.mocked(getPayrollRunByPayDate);

describe('startPayrollRun', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	afterEach(() => {
		vi.resetAllMocks();
	});

	const samplePayGroups = {
		periodEnd: '2025-01-31',
		payDate: '2025-02-06',
		payGroups: [
			{
				id: 'pg-1',
				name: 'Salaried Employees',
				payFrequency: 'bi_weekly' as const,
				employmentType: 'full_time' as const,
				periodStart: '2025-01-18',
				periodEnd: '2025-01-31',
				employees: [
					{
						id: 'emp-1',
						firstName: 'John',
						lastName: 'Doe',
						province: 'ON',
						payGroupId: 'pg-1',
						annualSalary: 78000,
						hourlyRate: null,
						compensationType: 'salaried' as const
					}
				],
				leaveEnabled: true,
				overtimePolicy: {},
				groupBenefits: {},
				earningsConfig: {},
				taxableBenefitsConfig: {},
				deductionsConfig: {}
			}
		],
		totalEmployees: 1,
		holidays: []
	};

	const sampleBatchResponse = {
		results: [
			{
				employee_id: 'emp-1',
				gross_regular: '3000.00',
				gross_overtime: '0.00',
				holiday_pay: '0.00',
				holiday_premium_pay: '0.00',
				vacation_pay: '0.00',
				other_earnings: '0.00',
				cpp_base: '150.00',
				cpp_additional: '0.00',
				ei_employee: '50.00',
				federal_tax: '400.00',
				provincial_tax: '200.00',
				rrsp: '0.00',
				union_dues: '0.00',
				garnishments: '0.00',
				other_deductions: '0.00',
				cpp_employer: '150.00',
				ei_employer: '70.00',
				new_ytd_gross: '3000.00',
				new_ytd_cpp: '150.00',
				new_ytd_ei: '50.00'
			}
		],
		summary: {
			total_gross: '3000.00',
			total_cpp_employee: '150.00',
			total_cpp_employer: '150.00',
			total_ei_employee: '50.00',
			total_ei_employer: '70.00',
			total_federal_tax: '400.00',
			total_provincial_tax: '200.00',
			total_net_pay: '2200.00',
			total_employer_costs: '3220.00'
		}
	};

	it('returns error when no pay groups found', async () => {
		mockGetPayGroups.mockResolvedValue({
			data: null,
			error: 'No pay groups found'
		});

		const result = await startPayrollRun('2025-02-06');

		expect(result.data).toBeNull();
		expect(result.error).toBe('No pay groups found');
	});

	it('returns error when no employees to process', async () => {
		mockGetPayGroups.mockResolvedValue({
			data: {
				...samplePayGroups,
				payGroups: [{ ...samplePayGroups.payGroups[0], employees: [] }],
				totalEmployees: 0
			},
			error: null
		});

		const result = await startPayrollRun('2025-02-06');

		expect(result.data).toBeNull();
		expect(result.error).toBe('No employees to process for this pay date');
	});

	it('returns error when hours missing for hourly employee', async () => {
		mockGetPayGroups.mockResolvedValue({
			data: {
				...samplePayGroups,
				payGroups: [
					{
						...samplePayGroups.payGroups[0],
						employees: [
							{
								id: 'emp-hourly',
								firstName: 'Jane',
								lastName: 'Smith',
								province: 'BC',
								payGroupId: 'pg-1',
								annualSalary: null,
								hourlyRate: 25,
								compensationType: 'hourly' as const
							}
						]
					}
				]
			},
			error: null
		});

		const result = await startPayrollRun('2025-02-06');

		expect(result.data).toBeNull();
		expect(result.error).toContain('Missing hours input for hourly employee');
	});

	it('returns error when backend calculation fails', async () => {
		mockGetPayGroups.mockResolvedValue({
			data: samplePayGroups,
			error: null
		});

		mockApi.post.mockRejectedValue(new Error('API timeout'));

		const result = await startPayrollRun('2025-02-06');

		expect(result.data).toBeNull();
		expect(result.error).toContain('Calculation failed');
	});

	it('successfully creates payroll run for salaried employees', async () => {
		mockGetPayGroups.mockResolvedValue({
			data: samplePayGroups,
			error: null
		});

		mockApi.post.mockResolvedValue(sampleBatchResponse);

		// Mock payroll_runs insert
		const mockInsertRun = vi.fn().mockReturnValue({
			select: vi.fn().mockReturnValue({
				single: vi.fn().mockResolvedValue({
					data: { id: 'run-123' },
					error: null
				})
			})
		});

		// Mock payroll_records insert
		const mockInsertRecords = vi.fn().mockResolvedValue({
			error: null
		});

		mockSupabase.from.mockImplementation((table: string) => {
			if (table === 'payroll_runs') {
				return { insert: mockInsertRun } as never;
			}
			if (table === 'payroll_records') {
				return { insert: mockInsertRecords } as never;
			}
			return {} as never;
		});

		mockGetPayrollRun.mockResolvedValue({
			data: {
				id: 'run-123',
				status: 'draft',
				periodStart: '2025-01-18',
				periodEnd: '2025-01-31',
				payDate: '2025-02-06',
				totalEmployees: 1,
				totalGross: 3000,
				totalNetPay: 2200,
				payrollRecords: [],
				payGroups: []
			},
			error: null
		});

		const result = await startPayrollRun('2025-02-06');

		expect(mockApi.post).toHaveBeenCalledWith('/payroll/calculate/batch', {
			employees: expect.arrayContaining([
				expect.objectContaining({
					employee_id: 'emp-1',
					province: 'ON',
					pay_frequency: 'bi_weekly'
				})
			]),
			include_details: false
		});
		expect(result.data).not.toBeNull();
		expect(result.error).toBeNull();
	});

	it('successfully processes hourly employees with hours input', async () => {
		const hourlyEmployee = {
			id: 'emp-hourly',
			firstName: 'Jane',
			lastName: 'Smith',
			province: 'BC',
			payGroupId: 'pg-1',
			annualSalary: null,
			hourlyRate: 25,
			compensationType: 'hourly' as const
		};

		mockGetPayGroups.mockResolvedValue({
			data: {
				...samplePayGroups,
				payGroups: [
					{
						...samplePayGroups.payGroups[0],
						employees: [hourlyEmployee]
					}
				]
			},
			error: null
		});

		mockApi.post.mockResolvedValue({
			...sampleBatchResponse,
			results: [
				{
					...sampleBatchResponse.results[0],
					employee_id: 'emp-hourly',
					gross_regular: '2000.00',
					gross_overtime: '187.50'
				}
			]
		});

		const mockInsertRun = vi.fn().mockReturnValue({
			select: vi.fn().mockReturnValue({
				single: vi.fn().mockResolvedValue({
					data: { id: 'run-123' },
					error: null
				})
			})
		});

		const mockInsertRecords = vi.fn().mockResolvedValue({ error: null });

		mockSupabase.from.mockImplementation((table: string) => {
			if (table === 'payroll_runs') {
				return { insert: mockInsertRun } as never;
			}
			if (table === 'payroll_records') {
				return { insert: mockInsertRecords } as never;
			}
			return {} as never;
		});

		mockGetPayrollRun.mockResolvedValue({
			data: { id: 'run-123', status: 'draft' } as never,
			error: null
		});

		const result = await startPayrollRun('2025-02-06', [
			{
				employeeId: 'emp-hourly',
				regularHours: 80,
				overtimeHours: 5
			}
		]);

		expect(mockApi.post).toHaveBeenCalledWith('/payroll/calculate/batch', {
			employees: expect.arrayContaining([
				expect.objectContaining({
					employee_id: 'emp-hourly',
					gross_regular: '2000.00',
					gross_overtime: '187.50'
				})
			]),
			include_details: false
		});
		expect(result.error).toBeNull();
	});

	it('returns error when payroll run insert fails', async () => {
		mockGetPayGroups.mockResolvedValue({
			data: samplePayGroups,
			error: null
		});

		mockApi.post.mockResolvedValue(sampleBatchResponse);

		const mockInsertRun = vi.fn().mockReturnValue({
			select: vi.fn().mockReturnValue({
				single: vi.fn().mockResolvedValue({
					data: null,
					error: { message: 'Database error' }
				})
			})
		});

		mockSupabase.from.mockImplementation((table: string) => {
			if (table === 'payroll_runs') {
				return { insert: mockInsertRun } as never;
			}
			return {} as never;
		});

		const result = await startPayrollRun('2025-02-06');

		expect(result.data).toBeNull();
		expect(result.error).toBe('Database error');
	});

	it('cleans up run when payroll records insert fails', async () => {
		mockGetPayGroups.mockResolvedValue({
			data: samplePayGroups,
			error: null
		});

		mockApi.post.mockResolvedValue(sampleBatchResponse);

		const mockDeleteRun = vi.fn().mockReturnValue({
			eq: vi.fn().mockResolvedValue({ error: null })
		});

		const mockInsertRun = vi.fn().mockReturnValue({
			select: vi.fn().mockReturnValue({
				single: vi.fn().mockResolvedValue({
					data: { id: 'run-123' },
					error: null
				})
			})
		});

		const mockInsertRecords = vi.fn().mockResolvedValue({
			error: { message: 'Record insert failed' }
		});

		mockSupabase.from.mockImplementation((table: string) => {
			if (table === 'payroll_runs') {
				return {
					insert: mockInsertRun,
					delete: mockDeleteRun
				} as never;
			}
			if (table === 'payroll_records') {
				return { insert: mockInsertRecords } as never;
			}
			return {} as never;
		});

		const result = await startPayrollRun('2025-02-06');

		expect(mockDeleteRun).toHaveBeenCalled();
		expect(result.data).toBeNull();
		expect(result.error).toBe('Record insert failed');
	});

	it('handles different pay frequencies correctly', async () => {
		const weeklyPayGroup = {
			...samplePayGroups,
			payGroups: [
				{
					...samplePayGroups.payGroups[0],
					payFrequency: 'weekly' as const
				}
			]
		};

		mockGetPayGroups.mockResolvedValue({
			data: weeklyPayGroup,
			error: null
		});

		mockApi.post.mockResolvedValue(sampleBatchResponse);

		const mockInsertRun = vi.fn().mockReturnValue({
			select: vi.fn().mockReturnValue({
				single: vi.fn().mockResolvedValue({
					data: { id: 'run-123' },
					error: null
				})
			})
		});

		const mockInsertRecords = vi.fn().mockResolvedValue({ error: null });

		mockSupabase.from.mockImplementation((table: string) => {
			if (table === 'payroll_runs') {
				return { insert: mockInsertRun } as never;
			}
			if (table === 'payroll_records') {
				return { insert: mockInsertRecords } as never;
			}
			return {} as never;
		});

		mockGetPayrollRun.mockResolvedValue({
			data: { id: 'run-123' } as never,
			error: null
		});

		await startPayrollRun('2025-02-06');

		expect(mockApi.post).toHaveBeenCalledWith('/payroll/calculate/batch', {
			employees: expect.arrayContaining([
				expect.objectContaining({
					pay_frequency: 'weekly',
					// Weekly: 78000 / 52 = 1500
					gross_regular: '1500.00'
				})
			]),
			include_details: false
		});
	});

	it('handles semi_monthly pay frequency', async () => {
		const semiMonthlyPayGroup = {
			...samplePayGroups,
			payGroups: [
				{
					...samplePayGroups.payGroups[0],
					payFrequency: 'semi_monthly' as const
				}
			]
		};

		mockGetPayGroups.mockResolvedValue({
			data: semiMonthlyPayGroup,
			error: null
		});

		mockApi.post.mockResolvedValue(sampleBatchResponse);

		const mockInsertRun = vi.fn().mockReturnValue({
			select: vi.fn().mockReturnValue({
				single: vi.fn().mockResolvedValue({
					data: { id: 'run-123' },
					error: null
				})
			})
		});

		const mockInsertRecords = vi.fn().mockResolvedValue({ error: null });

		mockSupabase.from.mockImplementation((table: string) => {
			if (table === 'payroll_runs') {
				return { insert: mockInsertRun } as never;
			}
			if (table === 'payroll_records') {
				return { insert: mockInsertRecords } as never;
			}
			return {} as never;
		});

		mockGetPayrollRun.mockResolvedValue({
			data: { id: 'run-123' } as never,
			error: null
		});

		await startPayrollRun('2025-02-06');

		expect(mockApi.post).toHaveBeenCalledWith('/payroll/calculate/batch', {
			employees: expect.arrayContaining([
				expect.objectContaining({
					pay_frequency: 'semi_monthly',
					// Semi-monthly: 78000 / 24 = 3250
					gross_regular: '3250.00'
				})
			]),
			include_details: false
		});
	});

	it('handles monthly pay frequency', async () => {
		const monthlyPayGroup = {
			...samplePayGroups,
			payGroups: [
				{
					...samplePayGroups.payGroups[0],
					payFrequency: 'monthly' as const
				}
			]
		};

		mockGetPayGroups.mockResolvedValue({
			data: monthlyPayGroup,
			error: null
		});

		mockApi.post.mockResolvedValue(sampleBatchResponse);

		const mockInsertRun = vi.fn().mockReturnValue({
			select: vi.fn().mockReturnValue({
				single: vi.fn().mockResolvedValue({
					data: { id: 'run-123' },
					error: null
				})
			})
		});

		const mockInsertRecords = vi.fn().mockResolvedValue({ error: null });

		mockSupabase.from.mockImplementation((table: string) => {
			if (table === 'payroll_runs') {
				return { insert: mockInsertRun } as never;
			}
			if (table === 'payroll_records') {
				return { insert: mockInsertRecords } as never;
			}
			return {} as never;
		});

		mockGetPayrollRun.mockResolvedValue({
			data: { id: 'run-123' } as never,
			error: null
		});

		await startPayrollRun('2025-02-06');

		expect(mockApi.post).toHaveBeenCalledWith('/payroll/calculate/batch', {
			employees: expect.arrayContaining([
				expect.objectContaining({
					pay_frequency: 'monthly',
					// Monthly: 78000 / 12 = 6500
					gross_regular: '6500.00'
				})
			]),
			include_details: false
		});
	});

	it('handles unexpected errors', async () => {
		mockGetPayGroups.mockRejectedValue(new Error('Network error'));

		const result = await startPayrollRun('2025-02-06');

		expect(result.data).toBeNull();
		expect(result.error).toBe('Network error');
	});

	it('handles non-Error exceptions', async () => {
		mockGetPayGroups.mockRejectedValue('String error');

		const result = await startPayrollRun('2025-02-06');

		expect(result.data).toBeNull();
		expect(result.error).toBe('Failed to start payroll run');
	});
});
