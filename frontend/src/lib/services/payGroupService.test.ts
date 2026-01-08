/**
 * Tests for payGroupService
 */

import { describe, expect, it, vi, beforeEach } from 'vitest';

// Mock the supabase client
vi.mock('$lib/api/supabase', () => ({
	supabase: {
		from: vi.fn()
	}
}));

// Mock the auth store
vi.mock('$lib/stores/auth.svelte', () => ({
	authState: {
		user: { id: 'test-user-id' }
	}
}));

import { supabase } from '$lib/api/supabase';
import {
	dbPayGroupToUi,
	listPayGroups,
	listPayGroupsWithCounts,
	getPayGroup,
	createPayGroup,
	updatePayGroup,
	deletePayGroup,
	getPayGroupCount,
	getMatchingPayGroups,
	duplicatePayGroup
} from './payGroupService';
import type { DbPayGroup } from './payGroupService';

const mockSupabase = vi.mocked(supabase);

// Helper to create a mock query builder
function createMockQueryBuilder(response: { data: unknown; error: unknown; count?: number }) {
	const builder = {
		select: vi.fn().mockReturnThis(),
		insert: vi.fn().mockReturnThis(),
		update: vi.fn().mockReturnThis(),
		delete: vi.fn().mockReturnThis(),
		eq: vi.fn().mockReturnThis(),
		order: vi.fn().mockReturnThis(),
		range: vi.fn().mockReturnThis(),
		single: vi.fn().mockResolvedValue(response),
		execute: vi.fn().mockResolvedValue(response)
	};

	// For range calls
	builder.range.mockImplementation(() => ({
		...builder,
		then: (resolve: (value: unknown) => void) =>
			resolve({ ...response, count: response.count ?? 0 })
	}));

	// For order at the end
	builder.order.mockImplementation(() => ({
		...builder,
		range: builder.range,
		then: (resolve: (value: unknown) => void) =>
			resolve({ ...response, count: response.count ?? 0 })
	}));

	return builder;
}

// Sample DB pay group data
const sampleDbPayGroup: DbPayGroup = {
	id: 'pg-123',
	company_id: 'company-123',
	name: 'Salaried Employees',
	description: 'Full-time salaried staff',
	pay_frequency: 'bi_weekly',
	employment_type: 'full_time',
	compensation_type: 'salary',
	next_period_end: '2025-01-15',
	period_start_day: 'monday',
	leave_enabled: true,
	tax_calculation_method: 'cumulative',
	overtime_policy: {
		bankTimeEnabled: false,
		bankTimeRate: 1.5,
		bankTimeExpiryMonths: 3,
		requireWrittenAgreement: true
	},
	wcb_config: {
		enabled: true,
		assessmentRate: 1.5
	},
	group_benefits: {
		enabled: true,
		health: { enabled: true, employeeDeduction: 50, employerContribution: 100, isTaxable: false },
		dental: { enabled: true, employeeDeduction: 25, employerContribution: 50, isTaxable: false },
		vision: { enabled: false, employeeDeduction: 0, employerContribution: 0, isTaxable: false },
		lifeInsurance: {
			enabled: false,
			employeeDeduction: 0,
			employerContribution: 0,
			isTaxable: false,
			coverageAmount: 0
		},
		disability: {
			enabled: false,
			employeeDeduction: 0,
			employerContribution: 0,
			isTaxable: false
		}
	},
	earnings_config: { enabled: false, types: {} },
	taxable_benefits_config: { enabled: false, types: {} },
	deductions_config: { enabled: false, types: {} },
	created_at: '2024-01-01T00:00:00Z',
	updated_at: '2024-01-01T00:00:00Z'
};

describe('dbPayGroupToUi', () => {
	it('converts DB pay group to UI format', () => {
		const result = dbPayGroupToUi(sampleDbPayGroup);

		expect(result.id).toBe('pg-123');
		expect(result.companyId).toBe('company-123');
		expect(result.name).toBe('Salaried Employees');
		expect(result.description).toBe('Full-time salaried staff');
		expect(result.payFrequency).toBe('bi_weekly');
		expect(result.employmentType).toBe('full_time');
		expect(result.nextPeriodEnd).toBe('2025-01-15');
		expect(result.periodStartDay).toBe('monday');
		expect(result.leaveEnabled).toBe(true);
		expect(result.taxCalculationMethod).toBe('cumulative');
	});

	it('handles null description', () => {
		const payGroupWithNullDesc = { ...sampleDbPayGroup, description: null };
		const result = dbPayGroupToUi(payGroupWithNullDesc);

		expect(result.description).toBeUndefined();
	});
});

describe('listPayGroups', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('lists pay groups with default options', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: [sampleDbPayGroup],
			error: null,
			count: 1
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await listPayGroups();

		expect(mockSupabase.from).toHaveBeenCalledWith('pay_groups');
		expect(result.error).toBeNull();
		expect(result.data).toHaveLength(1);
		expect(result.data[0].name).toBe('Salaried Employees');
	});

	it('filters by company_id when provided', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: [],
			error: null,
			count: 0
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		await listPayGroups({ company_id: 'company-123' });

		expect(mockBuilder.eq).toHaveBeenCalledWith('company_id', 'company-123');
	});

	it('filters by pay_frequency when provided', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: [],
			error: null,
			count: 0
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		await listPayGroups({ pay_frequency: 'monthly' });

		expect(mockBuilder.eq).toHaveBeenCalledWith('pay_frequency', 'monthly');
	});

	it('filters by employment_type when provided', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: [],
			error: null,
			count: 0
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		await listPayGroups({ employment_type: 'part_time' });

		expect(mockBuilder.eq).toHaveBeenCalledWith('employment_type', 'part_time');
	});

	it('returns error on failure', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: { message: 'Database error' },
			count: 0
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await listPayGroups();

		expect(result.error).toBe('Database error');
		expect(result.data).toEqual([]);
	});
});

describe('listPayGroupsWithCounts', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('lists pay groups with employee counts', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: [{ ...sampleDbPayGroup, employee_count: 5, company_name: 'Test Company' }],
			error: null
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await listPayGroupsWithCounts('company-123');

		expect(mockSupabase.from).toHaveBeenCalledWith('v_pay_group_summary');
		expect(result.error).toBeNull();
		expect(result.data).toHaveLength(1);
		expect(result.data[0].employeeCount).toBe(5);
		expect(result.data[0].companyName).toBe('Test Company');
	});

	it('returns error on failure', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: { message: 'View error' }
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await listPayGroupsWithCounts('company-123');

		expect(result.error).toBe('View error');
		expect(result.data).toEqual([]);
	});
});

describe('getPayGroup', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('gets a single pay group by ID', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: sampleDbPayGroup,
			error: null
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await getPayGroup('pg-123');

		expect(mockSupabase.from).toHaveBeenCalledWith('pay_groups');
		expect(mockBuilder.eq).toHaveBeenCalledWith('id', 'pg-123');
		expect(result.error).toBeNull();
		expect(result.data?.id).toBe('pg-123');
	});

	it('returns error when pay group not found', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: { message: 'Not found' }
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await getPayGroup('non-existent');

		expect(result.error).toBe('Not found');
		expect(result.data).toBeNull();
	});
});

describe('createPayGroup', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('creates a new pay group', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: sampleDbPayGroup,
			error: null
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await createPayGroup({
			company_id: 'company-123',
			name: 'Salaried Employees',
			pay_frequency: 'bi_weekly',
			next_period_end: '2025-01-15'
		});

		expect(mockSupabase.from).toHaveBeenCalledWith('pay_groups');
		expect(mockBuilder.insert).toHaveBeenCalled();
		expect(result.error).toBeNull();
		expect(result.data?.name).toBe('Salaried Employees');
	});

	it('uses default values for optional fields', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: sampleDbPayGroup,
			error: null
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		await createPayGroup({
			company_id: 'company-123',
			name: 'Test Group',
			pay_frequency: 'weekly',
			next_period_end: '2025-01-15'
		});

		expect(mockBuilder.insert).toHaveBeenCalledWith(
			expect.objectContaining({
				employment_type: 'full_time',
				period_start_day: 'monday',
				leave_enabled: true
			})
		);
	});

	it('returns error on create failure', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: { message: 'Duplicate name' }
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await createPayGroup({
			company_id: 'company-123',
			name: 'Test',
			pay_frequency: 'weekly',
			next_period_end: '2025-01-15'
		});

		expect(result.error).toBe('Duplicate name');
		expect(result.data).toBeNull();
	});
});

describe('updatePayGroup', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('updates a pay group', async () => {
		const updatedPayGroup = { ...sampleDbPayGroup, name: 'Updated Name' };
		const mockBuilder = createMockQueryBuilder({
			data: updatedPayGroup,
			error: null
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await updatePayGroup('pg-123', { name: 'Updated Name' });

		expect(mockSupabase.from).toHaveBeenCalledWith('pay_groups');
		expect(mockBuilder.update).toHaveBeenCalled();
		expect(result.error).toBeNull();
		expect(result.data?.name).toBe('Updated Name');
	});

	it('only updates provided fields', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: sampleDbPayGroup,
			error: null
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		await updatePayGroup('pg-123', { name: 'New Name', leave_enabled: false });

		expect(mockBuilder.update).toHaveBeenCalledWith({
			name: 'New Name',
			leave_enabled: false
		});
	});

	it('returns error on update failure', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: { message: 'Update failed' }
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await updatePayGroup('pg-123', { name: 'New Name' });

		expect(result.error).toBe('Update failed');
		expect(result.data).toBeNull();
	});
});

describe('deletePayGroup', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('deletes a pay group', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: null
		});
		mockBuilder.eq.mockImplementation(() => ({
			...mockBuilder,
			then: (resolve: (value: unknown) => void) => resolve({ error: null })
		}));
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await deletePayGroup('pg-123');

		expect(mockSupabase.from).toHaveBeenCalledWith('pay_groups');
		expect(mockBuilder.delete).toHaveBeenCalled();
		expect(result.error).toBeNull();
	});

	it('returns error on delete failure', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: { message: 'Cannot delete' }
		});
		mockBuilder.eq.mockImplementation(() => ({
			...mockBuilder,
			then: (resolve: (value: unknown) => void) => resolve({ error: { message: 'Cannot delete' } })
		}));
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await deletePayGroup('pg-123');

		expect(result.error).toBe('Cannot delete');
	});
});

describe('getPayGroupCount', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('gets pay group count for a company', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: null,
			count: 3
		});
		mockBuilder.eq.mockImplementation(() => ({
			...mockBuilder,
			then: (resolve: (value: unknown) => void) => resolve({ count: 3, error: null })
		}));
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const count = await getPayGroupCount('company-123');

		expect(count).toBe(3);
		expect(mockBuilder.eq).toHaveBeenCalledWith('company_id', 'company-123');
	});

	it('returns 0 on error', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: { message: 'Error' },
			count: 0
		});
		mockBuilder.eq.mockImplementation(() => ({
			...mockBuilder,
			then: (resolve: (value: unknown) => void) =>
				resolve({ count: null, error: { message: 'Error' } })
		}));
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const count = await getPayGroupCount('company-123');

		expect(count).toBe(0);
	});
});

describe('getMatchingPayGroups', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('gets pay groups matching criteria', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: [sampleDbPayGroup],
			error: null,
			count: 1
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await getMatchingPayGroups('company-123', 'bi_weekly', 'full_time');

		expect(mockBuilder.eq).toHaveBeenCalledWith('company_id', 'company-123');
		expect(mockBuilder.eq).toHaveBeenCalledWith('pay_frequency', 'bi_weekly');
		expect(mockBuilder.eq).toHaveBeenCalledWith('employment_type', 'full_time');
		expect(result.data).toHaveLength(1);
	});

	it('returns error on failure', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: { message: 'Query failed' },
			count: 0
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await getMatchingPayGroups('company-123', 'weekly', 'part_time');

		expect(result.error).toBe('Query failed');
	});
});

describe('duplicatePayGroup', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('duplicates a pay group with new name', async () => {
		// First call: get original
		// Second call: create new
		const callCount = { count: 0 };

		const mockBuilder = createMockQueryBuilder({
			data: sampleDbPayGroup,
			error: null
		});

		mockSupabase.from.mockImplementation(() => {
			callCount.count++;
			return mockBuilder as unknown as ReturnType<typeof supabase.from>;
		});

		const result = await duplicatePayGroup('pg-123', 'Copy of Salaried Employees');

		expect(result.error).toBeNull();
		expect(mockBuilder.insert).toHaveBeenCalled();
	});

	it('returns error when original not found', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: { message: 'Not found' }
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await duplicatePayGroup('non-existent', 'Copy');

		expect(result.error).toBe('Not found');
		expect(result.data).toBeNull();
	});
});
