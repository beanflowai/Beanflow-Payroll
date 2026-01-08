/**
 * Tests for employeeService
 */

import { describe, expect, it, vi, beforeEach } from 'vitest';

// Mock the supabase client
vi.mock('$lib/api/supabase', () => ({
	supabase: {
		from: vi.fn()
	}
}));

// Mock the API client
vi.mock('$lib/api/client', () => ({
	api: {
		get: vi.fn(),
		post: vi.fn(),
		put: vi.fn()
	},
	APIError: class APIError extends Error {
		constructor(
			message: string,
			public status: number
		) {
			super(message);
		}
	}
}));

// Mock the auth store
vi.mock('$lib/stores/auth.svelte', () => ({
	authState: {
		user: { id: 'test-user-id' }
	}
}));

// Mock the company store
vi.mock('$lib/stores/company.svelte', () => ({
	getCurrentCompanyId: vi.fn(() => 'test-company-id')
}));

import { supabase } from '$lib/api/supabase';
import { api, APIError } from '$lib/api/client';
import {
	maskSin,
	listEmployees,
	getEmployee,
	createEmployee,
	updateEmployee,
	terminateEmployee,
	deleteEmployee,
	getEmployeeCount,
	getEmployeesByProvince,
	getEmployeesByPayFrequency,
	getEmployeesByPayGroup,
	getUnassignedEmployees,
	assignEmployeesToPayGroup,
	removeEmployeeFromPayGroup,
	checkEmployeeHasPayrollRecords,
	getEmployeeTaxClaims,
	getEmployeeTaxClaimByYear,
	createEmployeeTaxClaim,
	updateEmployeeTaxClaim,
	createEmployeeTaxClaimViaApi,
	updateEmployeeTaxClaimViaApi,
	getEmployeeTaxClaimsViaApi
} from './employeeService';

const mockSupabase = vi.mocked(supabase);
const mockApi = vi.mocked(api);

// Helper to create a mock query builder
function createMockQueryBuilder(response: { data: unknown; error: unknown; count?: number }) {
	const builder = {
		select: vi.fn().mockReturnThis(),
		insert: vi.fn().mockReturnThis(),
		update: vi.fn().mockReturnThis(),
		delete: vi.fn().mockReturnThis(),
		eq: vi.fn().mockReturnThis(),
		is: vi.fn().mockReturnThis(),
		in: vi.fn().mockReturnThis(),
		order: vi.fn().mockReturnThis(),
		range: vi.fn().mockReturnThis(),
		limit: vi.fn().mockReturnThis(),
		single: vi.fn().mockResolvedValue(response),
		execute: vi.fn().mockResolvedValue(response)
	};

	// For range/order calls that don't end with single
	builder.range.mockImplementation(() => ({
		...builder,
		then: (resolve: (value: unknown) => void) =>
			resolve({ ...response, count: response.count ?? 0 })
	}));

	// For order at the end
	builder.order.mockImplementation(() => ({
		...builder,
		then: (resolve: (value: unknown) => void) =>
			resolve({ ...response, count: response.count ?? 0 })
	}));

	// For select with head: true
	builder.limit.mockImplementation(() => ({
		...builder,
		then: (resolve: (value: unknown) => void) =>
			resolve({ ...response, count: response.count ?? 0 })
	}));

	return builder;
}

// Sample DB employee data
const sampleDbEmployee = {
	id: 'emp-123',
	user_id: 'test-user-id',
	first_name: 'John',
	last_name: 'Doe',
	sin_encrypted: 'encrypted-sin',
	email: 'john@example.com',
	province_of_employment: 'ON',
	pay_frequency: 'bi_weekly',
	employment_type: 'full_time',
	address_street: '123 Main St',
	address_city: 'Toronto',
	address_postal_code: 'M5V1A1',
	occupation: 'Developer',
	annual_salary: 100000,
	hourly_rate: null,
	federal_additional_claims: 0,
	provincial_additional_claims: 0,
	is_cpp_exempt: false,
	is_ei_exempt: false,
	cpp2_exempt: false,
	hire_date: '2024-01-01',
	termination_date: null,
	vacation_config: { payout_method: 'accrual', vacation_rate: '0.04' },
	vacation_balance: 5,
	sick_balance: 3,
	tags: [],
	pay_group_id: null,
	initial_ytd_cpp: 0,
	initial_ytd_cpp2: 0,
	initial_ytd_ei: 0,
	initial_ytd_year: null,
	portal_status: 'not_set',
	portal_invited_at: null,
	portal_last_login_at: null,
	created_at: '2024-01-01T00:00:00Z',
	updated_at: '2024-01-01T00:00:00Z'
};

describe('maskSin', () => {
	it('returns masked SIN', () => {
		expect(maskSin('encrypted-data')).toBe('***-***-***');
	});
});

describe('listEmployees', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('lists employees with default options', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: [sampleDbEmployee],
			error: null,
			count: 1
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await listEmployees();

		expect(mockSupabase.from).toHaveBeenCalledWith('employees');
		expect(result.error).toBeNull();
		expect(result.data).toHaveLength(1);
		expect(result.data[0].firstName).toBe('John');
		expect(result.count).toBe(1);
	});

	it('filters active employees only by default', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: [],
			error: null,
			count: 0
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		await listEmployees();

		expect(mockBuilder.is).toHaveBeenCalledWith('termination_date', null);
	});

	it('can include terminated employees', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: [],
			error: null,
			count: 0
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		await listEmployees({ activeOnly: false });

		expect(mockBuilder.is).not.toHaveBeenCalledWith('termination_date', null);
	});

	it('filters by province when provided', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: [],
			error: null,
			count: 0
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		await listEmployees({ province: 'BC' });

		expect(mockBuilder.eq).toHaveBeenCalledWith('province_of_employment', 'BC');
	});

	it('returns error on failure', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: { message: 'Database error' },
			count: 0
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await listEmployees();

		expect(result.error).toBe('Database error');
		expect(result.data).toEqual([]);
	});
});

describe('getEmployee', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('gets a single employee by ID', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: sampleDbEmployee,
			error: null
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await getEmployee('emp-123');

		expect(mockSupabase.from).toHaveBeenCalledWith('employees');
		expect(mockBuilder.eq).toHaveBeenCalledWith('id', 'emp-123');
		expect(result.error).toBeNull();
		expect(result.data?.id).toBe('emp-123');
	});

	it('returns error when employee not found', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: { message: 'Not found' }
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await getEmployee('non-existent');

		expect(result.error).toBe('Not found');
		expect(result.data).toBeNull();
	});
});

describe('createEmployee', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('creates a new employee', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: sampleDbEmployee,
			error: null
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await createEmployee({
			first_name: 'John',
			last_name: 'Doe',
			sin: '123456789',
			email: 'john@example.com',
			province_of_employment: 'ON',
			pay_frequency: 'bi_weekly',
			federal_additional_claims: 0,
			provincial_additional_claims: 0,
			hire_date: '2024-01-01'
		});

		expect(mockSupabase.from).toHaveBeenCalledWith('employees');
		expect(mockBuilder.insert).toHaveBeenCalled();
		expect(result.error).toBeNull();
		expect(result.data?.firstName).toBe('John');
	});

	it('returns error on create failure', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: { message: 'Duplicate SIN' }
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await createEmployee({
			first_name: 'John',
			last_name: 'Doe',
			sin: '123456789',
			province_of_employment: 'ON',
			pay_frequency: 'bi_weekly',
			federal_additional_claims: 0,
			provincial_additional_claims: 0,
			hire_date: '2024-01-01'
		});

		expect(result.error).toBe('Duplicate SIN');
		expect(result.data).toBeNull();
	});
});

describe('updateEmployee', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('updates an employee', async () => {
		const updatedEmployee = { ...sampleDbEmployee, first_name: 'Jane' };
		const mockBuilder = createMockQueryBuilder({
			data: updatedEmployee,
			error: null
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await updateEmployee('emp-123', { first_name: 'Jane' });

		expect(mockSupabase.from).toHaveBeenCalledWith('employees');
		expect(mockBuilder.update).toHaveBeenCalled();
		expect(result.error).toBeNull();
		expect(result.data?.firstName).toBe('Jane');
	});

	it('returns error on update failure', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: { message: 'Update failed' }
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await updateEmployee('emp-123', { first_name: 'Jane' });

		expect(result.error).toBe('Update failed');
		expect(result.data).toBeNull();
	});
});

describe('terminateEmployee', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('terminates an employee by setting termination date', async () => {
		const terminatedEmployee = { ...sampleDbEmployee, termination_date: '2024-12-31' };
		const mockBuilder = createMockQueryBuilder({
			data: terminatedEmployee,
			error: null
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await terminateEmployee('emp-123', '2024-12-31');

		expect(mockBuilder.update).toHaveBeenCalled();
		expect(result.data?.terminationDate).toBe('2024-12-31');
		expect(result.data?.status).toBe('terminated');
	});
});

describe('deleteEmployee', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('deletes an employee', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: null
		});
		// Override the delete chain
		mockBuilder.delete = vi.fn().mockReturnValue({
			eq: vi.fn().mockReturnThis(),
			then: (resolve: (value: unknown) => void) => resolve({ error: null })
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await deleteEmployee('emp-123');

		expect(mockSupabase.from).toHaveBeenCalledWith('employees');
		expect(result.error).toBeNull();
	});

	it('returns error on delete failure', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: { message: 'Cannot delete' }
		});
		mockBuilder.delete = vi.fn().mockReturnValue({
			eq: vi.fn().mockReturnThis(),
			then: (resolve: (value: unknown) => void) => resolve({ error: { message: 'Cannot delete' } })
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await deleteEmployee('emp-123');

		expect(result.error).toBe('Cannot delete');
	});
});

describe('getEmployeeCount', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('gets active employee count', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: null,
			count: 5
		});
		// For count query with head: true
		mockBuilder.is.mockImplementation(() => ({
			...mockBuilder,
			then: (resolve: (value: unknown) => void) => resolve({ count: 5, error: null })
		}));
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const count = await getEmployeeCount();

		expect(count).toBe(5);
		expect(mockBuilder.is).toHaveBeenCalledWith('termination_date', null);
	});

	it('returns 0 on error', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: { message: 'Error' },
			count: 0
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const count = await getEmployeeCount();

		expect(count).toBe(0);
	});
});

describe('getEmployeesByProvince', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('returns employees grouped by province', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: [
				{ province_of_employment: 'ON' },
				{ province_of_employment: 'ON' },
				{ province_of_employment: 'BC' }
			],
			error: null
		});
		mockBuilder.order = vi.fn().mockReturnThis();
		mockBuilder.is.mockImplementation(() => ({
			...mockBuilder,
			then: (resolve: (value: unknown) => void) =>
				resolve({
					data: [
						{ province_of_employment: 'ON' },
						{ province_of_employment: 'ON' },
						{ province_of_employment: 'BC' }
					],
					error: null
				})
		}));
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await getEmployeesByProvince();

		expect(result.ON).toBe(2);
		expect(result.BC).toBe(1);
	});

	it('returns empty object on error', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: { message: 'Error' }
		});
		mockBuilder.is.mockImplementation(() => ({
			...mockBuilder,
			then: (resolve: (value: unknown) => void) =>
				resolve({
					data: null,
					error: { message: 'Error' }
				})
		}));
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await getEmployeesByProvince();

		expect(result).toEqual({});
	});
});

describe('getEmployeesByPayFrequency', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('returns employees grouped by pay frequency', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: [
				{ pay_frequency: 'bi_weekly' },
				{ pay_frequency: 'bi_weekly' },
				{ pay_frequency: 'monthly' }
			],
			error: null
		});
		mockBuilder.is.mockImplementation(() => ({
			...mockBuilder,
			then: (resolve: (value: unknown) => void) =>
				resolve({
					data: [
						{ pay_frequency: 'bi_weekly' },
						{ pay_frequency: 'bi_weekly' },
						{ pay_frequency: 'monthly' }
					],
					error: null
				})
		}));
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await getEmployeesByPayFrequency();

		expect(result.bi_weekly).toBe(2);
		expect(result.monthly).toBe(1);
	});
});

describe('getEmployeesByPayGroup', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('gets employees by pay group', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: [sampleDbEmployee],
			error: null,
			count: 1
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await getEmployeesByPayGroup('group-123');

		expect(mockBuilder.eq).toHaveBeenCalledWith('pay_group_id', 'group-123');
		expect(result.data).toHaveLength(1);
	});
});

describe('getUnassignedEmployees', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('gets employees without pay group', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: [{ ...sampleDbEmployee, pay_group_id: null }],
			error: null,
			count: 1
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await getUnassignedEmployees();

		expect(mockBuilder.is).toHaveBeenCalledWith('pay_group_id', null);
		expect(result.data).toHaveLength(1);
	});

	it('applies employment type filter', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: [],
			error: null,
			count: 0
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		await getUnassignedEmployees({ employmentType: 'full_time' });

		expect(mockBuilder.eq).toHaveBeenCalledWith('employment_type', 'full_time');
	});

	it('applies pay frequency filter', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: [],
			error: null,
			count: 0
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		await getUnassignedEmployees({ payFrequency: 'bi_weekly' });

		expect(mockBuilder.eq).toHaveBeenCalledWith('pay_frequency', 'bi_weekly');
	});
});

describe('assignEmployeesToPayGroup', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('assigns employees to pay group', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: null
		});
		mockBuilder.in.mockImplementation(() => ({
			...mockBuilder,
			then: (resolve: (value: unknown) => void) => resolve({ error: null })
		}));
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const mockPayGroup = {
			id: 'group-123',
			payFrequency: 'bi_weekly' as const,
			employmentType: 'full_time' as const,
			compensationType: 'salary' as const,
			province: 'SK' as const
		};

		const result = await assignEmployeesToPayGroup(['emp-1', 'emp-2'], mockPayGroup);

		expect(mockBuilder.update).toHaveBeenCalledWith({ pay_group_id: 'group-123' });
		expect(mockBuilder.in).toHaveBeenCalledWith('id', ['emp-1', 'emp-2']);
		expect(result.error).toBeNull();
	});
});

describe('removeEmployeeFromPayGroup', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('removes employee from pay group', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: null
		});
		mockBuilder.eq.mockImplementation(() => ({
			...mockBuilder,
			then: (resolve: (value: unknown) => void) => resolve({ error: null })
		}));
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await removeEmployeeFromPayGroup('emp-123');

		expect(mockBuilder.update).toHaveBeenCalledWith({ pay_group_id: null });
		expect(result.error).toBeNull();
	});
});

describe('checkEmployeeHasPayrollRecords', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('returns true if employee has payroll records', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: null,
			count: 5
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await checkEmployeeHasPayrollRecords('emp-123');

		expect(mockSupabase.from).toHaveBeenCalledWith('payroll_records');
		expect(result).toBe(true);
	});

	it('returns false if employee has no payroll records', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: null,
			count: 0
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await checkEmployeeHasPayrollRecords('emp-123');

		expect(result).toBe(false);
	});

	it('returns false on error', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: { message: 'Error' },
			count: 0
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await checkEmployeeHasPayrollRecords('emp-123');

		expect(result).toBe(false);
	});
});

// Tax Claims Tests
const sampleDbTaxClaim = {
	id: 'claim-123',
	employee_id: 'emp-123',
	company_id: 'test-company-id',
	user_id: 'test-user-id',
	tax_year: 2025,
	federal_bpa: 16129,
	federal_additional_claims: 1000,
	provincial_bpa: 12747,
	provincial_additional_claims: 500,
	created_at: '2024-01-01T00:00:00Z',
	updated_at: '2024-01-01T00:00:00Z'
};

describe('getEmployeeTaxClaims', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('gets all tax claims for an employee', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: [sampleDbTaxClaim],
			error: null
		});
		mockBuilder.order.mockImplementation(() => ({
			...mockBuilder,
			then: (resolve: (value: unknown) => void) =>
				resolve({
					data: [sampleDbTaxClaim],
					error: null
				})
		}));
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await getEmployeeTaxClaims('emp-123');

		expect(mockSupabase.from).toHaveBeenCalledWith('employee_tax_claims');
		expect(result.error).toBeNull();
		expect(result.data).toHaveLength(1);
		expect(result.data?.[0].taxYear).toBe(2025);
	});
});

describe('getEmployeeTaxClaimByYear', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('gets tax claim for a specific year', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: sampleDbTaxClaim,
			error: null
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await getEmployeeTaxClaimByYear('emp-123', 2025);

		expect(mockBuilder.eq).toHaveBeenCalledWith('tax_year', 2025);
		expect(result.error).toBeNull();
		expect(result.data?.federalBpa).toBe(16129);
	});
});

describe('createEmployeeTaxClaim', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('creates a new tax claim', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: sampleDbTaxClaim,
			error: null
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await createEmployeeTaxClaim('emp-123', 2025, 16129, 12747, 1000, 500);

		expect(mockSupabase.from).toHaveBeenCalledWith('employee_tax_claims');
		expect(mockBuilder.insert).toHaveBeenCalled();
		expect(result.error).toBeNull();
	});
});

describe('updateEmployeeTaxClaim', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('updates tax claim additional claims', async () => {
		const updatedClaim = { ...sampleDbTaxClaim, federal_additional_claims: 2000 };
		const mockBuilder = createMockQueryBuilder({
			data: updatedClaim,
			error: null
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await updateEmployeeTaxClaim('emp-123', 2025, { federalAdditionalClaims: 2000 });

		expect(mockBuilder.update).toHaveBeenCalled();
		expect(result.error).toBeNull();
	});

	it('returns error when no fields to update', async () => {
		const result = await updateEmployeeTaxClaim('emp-123', 2025, {});

		expect(result.error).toBe('No fields to update');
	});
});

// API-based tax claim functions
describe('createEmployeeTaxClaimViaApi', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('creates tax claim via API', async () => {
		mockApi.post.mockResolvedValueOnce({
			id: 'claim-123',
			employee_id: 'emp-123',
			company_id: 'test-company-id',
			tax_year: 2025,
			federal_bpa: 16129,
			federal_additional_claims: 0,
			provincial_bpa: 12747,
			provincial_additional_claims: 0,
			created_at: '2024-01-01T00:00:00Z',
			updated_at: '2024-01-01T00:00:00Z'
		});

		const result = await createEmployeeTaxClaimViaApi('emp-123', 2025);

		expect(mockApi.post).toHaveBeenCalledWith('/employees/emp-123/tax-claims', {
			tax_year: 2025,
			federal_additional_claims: 0,
			provincial_additional_claims: 0
		});
		expect(result.error).toBeNull();
		expect(result.data?.taxYear).toBe(2025);
	});

	it('handles 409 conflict error', async () => {
		mockApi.post.mockRejectedValueOnce(new APIError('Conflict', 409));

		const result = await createEmployeeTaxClaimViaApi('emp-123', 2025);

		expect(result.error).toContain('already exists');
	});

	it('handles other API errors', async () => {
		mockApi.post.mockRejectedValueOnce(new APIError('Server error', 500));

		const result = await createEmployeeTaxClaimViaApi('emp-123', 2025);

		expect(result.error).toBe('Server error');
	});
});

describe('updateEmployeeTaxClaimViaApi', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('updates tax claim via API', async () => {
		mockApi.put.mockResolvedValueOnce({
			id: 'claim-123',
			employee_id: 'emp-123',
			company_id: 'test-company-id',
			tax_year: 2025,
			federal_bpa: 16129,
			federal_additional_claims: 2000,
			provincial_bpa: 12747,
			provincial_additional_claims: 0,
			created_at: '2024-01-01T00:00:00Z',
			updated_at: '2024-01-01T00:00:00Z'
		});

		const result = await updateEmployeeTaxClaimViaApi('emp-123', 2025, {
			federalAdditionalClaims: 2000
		});

		expect(mockApi.put).toHaveBeenCalledWith('/employees/emp-123/tax-claims/2025', {
			federal_additional_claims: 2000
		});
		expect(result.error).toBeNull();
		expect(result.data?.federalAdditionalClaims).toBe(2000);
	});

	it('can request BPA recalculation', async () => {
		mockApi.put.mockResolvedValueOnce({
			id: 'claim-123',
			employee_id: 'emp-123',
			company_id: 'test-company-id',
			tax_year: 2025,
			federal_bpa: 16500,
			federal_additional_claims: 0,
			provincial_bpa: 13000,
			provincial_additional_claims: 0,
			created_at: '2024-01-01T00:00:00Z',
			updated_at: '2024-01-01T00:00:00Z'
		});

		await updateEmployeeTaxClaimViaApi('emp-123', 2025, {}, true);

		expect(mockApi.put).toHaveBeenCalledWith('/employees/emp-123/tax-claims/2025', {
			recalculate_bpa: true
		});
	});
});

describe('getEmployeeTaxClaimsViaApi', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('gets tax claims via API', async () => {
		mockApi.get.mockResolvedValueOnce([
			{
				id: 'claim-123',
				employee_id: 'emp-123',
				company_id: 'test-company-id',
				tax_year: 2025,
				federal_bpa: 16129,
				federal_additional_claims: 0,
				provincial_bpa: 12747,
				provincial_additional_claims: 0,
				created_at: '2024-01-01T00:00:00Z',
				updated_at: '2024-01-01T00:00:00Z'
			}
		]);

		const result = await getEmployeeTaxClaimsViaApi('emp-123');

		expect(mockApi.get).toHaveBeenCalledWith('/employees/emp-123/tax-claims');
		expect(result.error).toBeNull();
		expect(result.data).toHaveLength(1);
		expect(result.data?.[0].federalTotalClaim).toBe(16129);
	});

	it('handles API errors', async () => {
		mockApi.get.mockRejectedValueOnce(new APIError('Not found', 404));

		const result = await getEmployeeTaxClaimsViaApi('emp-123');

		expect(result.error).toBe('Not found');
	});
});
