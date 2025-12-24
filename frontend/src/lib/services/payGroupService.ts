/**
 * Pay Group Service - Direct Supabase CRUD operations
 *
 * This service handles CRUD operations for pay groups directly
 * via the Supabase client.
 */

import { supabase } from '$lib/api/supabase';
import type {
	PayGroup,
	PayFrequency,
	EmploymentType,
	PeriodStartDay,
	StatutoryDefaults,
	OvertimePolicy,
	WcbConfig,
	GroupBenefits,
	EarningsConfig,
	TaxableBenefitsConfig,
	DeductionsConfig
} from '$lib/types/pay-group';
import {
	DEFAULT_EARNINGS_CONFIG,
	DEFAULT_TAXABLE_BENEFITS_CONFIG,
	DEFAULT_DEDUCTIONS_CONFIG
} from '$lib/types/pay-group';
import { authState } from '$lib/stores/auth.svelte';

const TABLE_NAME = 'pay_groups';

/**
 * Database pay group record (snake_case from Supabase)
 */
export interface DbPayGroup {
	id: string;
	company_id: string;
	name: string;
	description: string | null;
	pay_frequency: PayFrequency;
	employment_type: EmploymentType;
	next_pay_date: string;
	period_start_day: PeriodStartDay;
	leave_enabled: boolean;
	statutory_defaults: StatutoryDefaults;
	overtime_policy: OvertimePolicy;
	wcb_config: WcbConfig;
	group_benefits: GroupBenefits;
	earnings_config: EarningsConfig;
	taxable_benefits_config: TaxableBenefitsConfig;
	deductions_config: DeductionsConfig;
	created_at: string;
	updated_at: string;
}

/**
 * Pay group creation input
 */
export interface PayGroupCreateInput {
	company_id: string;
	name: string;
	description?: string;
	pay_frequency: PayFrequency;
	employment_type?: EmploymentType;
	next_pay_date: string;
	period_start_day?: PeriodStartDay;
	leave_enabled?: boolean;
	statutory_defaults?: StatutoryDefaults;
	overtime_policy?: OvertimePolicy;
	wcb_config?: WcbConfig;
	group_benefits?: GroupBenefits;
	earnings_config?: EarningsConfig;
	taxable_benefits_config?: TaxableBenefitsConfig;
	deductions_config?: DeductionsConfig;
}

/**
 * Pay group update input (all fields optional)
 */
export interface PayGroupUpdateInput {
	name?: string;
	description?: string;
	pay_frequency?: PayFrequency;
	employment_type?: EmploymentType;
	next_pay_date?: string;
	period_start_day?: PeriodStartDay;
	leave_enabled?: boolean;
	statutory_defaults?: StatutoryDefaults;
	overtime_policy?: OvertimePolicy;
	wcb_config?: WcbConfig;
	group_benefits?: GroupBenefits;
	earnings_config?: EarningsConfig;
	taxable_benefits_config?: TaxableBenefitsConfig;
	deductions_config?: DeductionsConfig;
}

/**
 * Convert DB record to UI PayGroup
 */
export function dbPayGroupToUi(db: DbPayGroup): PayGroup {
	return {
		id: db.id,
		companyId: db.company_id,
		name: db.name,
		description: db.description ?? undefined,
		payFrequency: db.pay_frequency,
		employmentType: db.employment_type,
		nextPayDate: db.next_pay_date,
		periodStartDay: db.period_start_day,
		leaveEnabled: db.leave_enabled,
		statutoryDefaults: db.statutory_defaults,
		overtimePolicy: db.overtime_policy,
		wcbConfig: db.wcb_config,
		groupBenefits: db.group_benefits,
		earningsConfig: db.earnings_config ?? DEFAULT_EARNINGS_CONFIG,
		taxableBenefitsConfig: db.taxable_benefits_config ?? DEFAULT_TAXABLE_BENEFITS_CONFIG,
		deductionsConfig: db.deductions_config ?? DEFAULT_DEDUCTIONS_CONFIG,
		createdAt: db.created_at,
		updatedAt: db.updated_at
	};
}

/**
 * Get current user's user_id
 */
function getCurrentUserId(): string {
	const user = authState.user;
	if (!user) throw new Error('User not authenticated');
	return user.id;
}

export interface PayGroupServiceResult<T> {
	data: T | null;
	error: string | null;
}

export interface PayGroupListResult {
	data: PayGroup[];
	count: number;
	error: string | null;
}

export interface PayGroupListOptions {
	company_id?: string;
	pay_frequency?: PayFrequency;
	employment_type?: EmploymentType;
	limit?: number;
	offset?: number;
}

/**
 * Pay group with employee count (from view)
 */
export interface PayGroupWithCount extends PayGroup {
	employeeCount: number;
	companyName?: string;
}

/**
 * List pay groups for a company
 */
export async function listPayGroups(
	options: PayGroupListOptions = {}
): Promise<PayGroupListResult> {
	const { company_id, pay_frequency, employment_type, limit = 100, offset = 0 } = options;

	try {
		getCurrentUserId(); // Verify authenticated

		let query = supabase.from(TABLE_NAME).select('*', { count: 'exact' });

		if (company_id) {
			query = query.eq('company_id', company_id);
		}

		if (pay_frequency) {
			query = query.eq('pay_frequency', pay_frequency);
		}

		if (employment_type) {
			query = query.eq('employment_type', employment_type);
		}

		const { data, error, count } = await query
			.order('name')
			.range(offset, offset + limit - 1);

		if (error) {
			console.error('Failed to list pay groups:', error);
			return { data: [], count: 0, error: error.message };
		}

		const payGroups: PayGroup[] = (data as DbPayGroup[]).map(dbPayGroupToUi);

		return { data: payGroups, count: count ?? 0, error: null };
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to list pay groups';
		return { data: [], count: 0, error: message };
	}
}

/**
 * List pay groups with employee counts (using view)
 */
export async function listPayGroupsWithCounts(
	companyId: string
): Promise<{ data: PayGroupWithCount[]; error: string | null }> {
	try {
		getCurrentUserId(); // Verify authenticated

		const { data, error } = await supabase
			.from('v_pay_group_summary')
			.select('*')
			.eq('company_id', companyId)
			.order('name');

		if (error) {
			console.error('Failed to list pay groups with counts:', error);
			return { data: [], error: error.message };
		}

		const payGroups: PayGroupWithCount[] = (data as (DbPayGroup & { employee_count: number; company_name: string })[]).map((db) => ({
			...dbPayGroupToUi(db),
			employeeCount: db.employee_count ?? 0,
			companyName: db.company_name
		}));

		return { data: payGroups, error: null };
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to list pay groups with counts';
		return { data: [], error: message };
	}
}

/**
 * Get a single pay group by ID
 */
export async function getPayGroup(payGroupId: string): Promise<PayGroupServiceResult<PayGroup>> {
	try {
		getCurrentUserId(); // Verify authenticated

		const { data, error } = await supabase
			.from(TABLE_NAME)
			.select('*')
			.eq('id', payGroupId)
			.single();

		if (error) {
			console.error('Failed to get pay group:', error);
			return { data: null, error: error.message };
		}

		return {
			data: dbPayGroupToUi(data as DbPayGroup),
			error: null
		};
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to get pay group';
		return { data: null, error: message };
	}
}

/**
 * Create a new pay group
 */
export async function createPayGroup(
	input: PayGroupCreateInput
): Promise<PayGroupServiceResult<PayGroup>> {
	try {
		getCurrentUserId(); // Verify authenticated

		const record = {
			company_id: input.company_id,
			name: input.name,
			description: input.description ?? null,
			pay_frequency: input.pay_frequency,
			employment_type: input.employment_type ?? 'full_time',
			next_pay_date: input.next_pay_date,
			period_start_day: input.period_start_day ?? 'monday',
			leave_enabled: input.leave_enabled ?? true,
			statutory_defaults: input.statutory_defaults ?? {
				cppExemptByDefault: false,
				cpp2ExemptByDefault: false,
				eiExemptByDefault: false
			},
			overtime_policy: input.overtime_policy ?? {
				bankTimeEnabled: false,
				bankTimeRate: 1.5,
				bankTimeExpiryMonths: 3,
				requireWrittenAgreement: true
			},
			wcb_config: input.wcb_config ?? {
				enabled: false,
				assessmentRate: 0
			},
			group_benefits: input.group_benefits ?? {
				enabled: false,
				health: { enabled: false, employeeDeduction: 0, employerContribution: 0, isTaxable: false },
				dental: { enabled: false, employeeDeduction: 0, employerContribution: 0, isTaxable: false },
				vision: { enabled: false, employeeDeduction: 0, employerContribution: 0, isTaxable: false },
				lifeInsurance: { enabled: false, employeeDeduction: 0, employerContribution: 0, isTaxable: false, coverageAmount: 0 },
				disability: { enabled: false, employeeDeduction: 0, employerContribution: 0, isTaxable: false }
			},
			earnings_config: input.earnings_config ?? DEFAULT_EARNINGS_CONFIG,
			taxable_benefits_config: input.taxable_benefits_config ?? DEFAULT_TAXABLE_BENEFITS_CONFIG,
			deductions_config: input.deductions_config ?? DEFAULT_DEDUCTIONS_CONFIG
		};

		const { data, error } = await supabase.from(TABLE_NAME).insert(record).select().single();

		if (error) {
			console.error('Failed to create pay group:', error);
			return { data: null, error: error.message };
		}

		return {
			data: dbPayGroupToUi(data as DbPayGroup),
			error: null
		};
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to create pay group';
		return { data: null, error: message };
	}
}

/**
 * Update an existing pay group
 */
export async function updatePayGroup(
	payGroupId: string,
	input: PayGroupUpdateInput
): Promise<PayGroupServiceResult<PayGroup>> {
	try {
		getCurrentUserId(); // Verify authenticated

		// Build update object, only including defined fields
		const updateData: Record<string, unknown> = {};

		if (input.name !== undefined) updateData.name = input.name;
		if (input.description !== undefined) updateData.description = input.description;
		if (input.pay_frequency !== undefined) updateData.pay_frequency = input.pay_frequency;
		if (input.employment_type !== undefined) updateData.employment_type = input.employment_type;
		if (input.next_pay_date !== undefined) updateData.next_pay_date = input.next_pay_date;
		if (input.period_start_day !== undefined) updateData.period_start_day = input.period_start_day;
		if (input.leave_enabled !== undefined) updateData.leave_enabled = input.leave_enabled;
		if (input.statutory_defaults !== undefined)
			updateData.statutory_defaults = input.statutory_defaults;
		if (input.overtime_policy !== undefined) updateData.overtime_policy = input.overtime_policy;
		if (input.wcb_config !== undefined) updateData.wcb_config = input.wcb_config;
		if (input.group_benefits !== undefined) updateData.group_benefits = input.group_benefits;
		if (input.earnings_config !== undefined)
			updateData.earnings_config = input.earnings_config;
		if (input.taxable_benefits_config !== undefined)
			updateData.taxable_benefits_config = input.taxable_benefits_config;
		if (input.deductions_config !== undefined)
			updateData.deductions_config = input.deductions_config;

		const { data, error } = await supabase
			.from(TABLE_NAME)
			.update(updateData)
			.eq('id', payGroupId)
			.select()
			.single();

		if (error) {
			console.error('Failed to update pay group:', error);
			return { data: null, error: error.message };
		}

		return {
			data: dbPayGroupToUi(data as DbPayGroup),
			error: null
		};
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to update pay group';
		return { data: null, error: message };
	}
}

/**
 * Delete a pay group (hard delete)
 */
export async function deletePayGroup(payGroupId: string): Promise<{ error: string | null }> {
	try {
		getCurrentUserId(); // Verify authenticated

		const { error } = await supabase.from(TABLE_NAME).delete().eq('id', payGroupId);

		if (error) {
			console.error('Failed to delete pay group:', error);
			return { error: error.message };
		}

		return { error: null };
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to delete pay group';
		return { error: message };
	}
}

/**
 * Get pay group count for a company
 */
export async function getPayGroupCount(companyId: string): Promise<number> {
	try {
		getCurrentUserId(); // Verify authenticated

		const { count, error } = await supabase
			.from(TABLE_NAME)
			.select('id', { count: 'exact', head: true })
			.eq('company_id', companyId);

		if (error) {
			console.error('Failed to get pay group count:', error);
			return 0;
		}

		return count ?? 0;
	} catch {
		return 0;
	}
}

/**
 * Get pay groups matching employee attributes (for filtering during payroll run)
 */
export async function getMatchingPayGroups(
	companyId: string,
	payFrequency: PayFrequency,
	employmentType: EmploymentType
): Promise<PayGroupListResult> {
	try {
		getCurrentUserId(); // Verify authenticated

		const { data, error, count } = await supabase
			.from(TABLE_NAME)
			.select('*', { count: 'exact' })
			.eq('company_id', companyId)
			.eq('pay_frequency', payFrequency)
			.eq('employment_type', employmentType)
			.order('name');

		if (error) {
			console.error('Failed to get matching pay groups:', error);
			return { data: [], count: 0, error: error.message };
		}

		const payGroups: PayGroup[] = (data as DbPayGroup[]).map(dbPayGroupToUi);

		return { data: payGroups, count: count ?? 0, error: null };
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to get matching pay groups';
		return { data: [], count: 0, error: message };
	}
}

/**
 * Duplicate a pay group with a new name
 */
export async function duplicatePayGroup(
	payGroupId: string,
	newName: string
): Promise<PayGroupServiceResult<PayGroup>> {
	try {
		// Get the original pay group
		const { data: original, error: getError } = await getPayGroup(payGroupId);

		if (getError || !original) {
			return { data: null, error: getError ?? 'Pay group not found' };
		}

		// Create a new pay group with the same settings
		return createPayGroup({
			company_id: original.companyId,
			name: newName,
			description: original.description,
			pay_frequency: original.payFrequency,
			employment_type: original.employmentType,
			next_pay_date: original.nextPayDate,
			period_start_day: original.periodStartDay,
			leave_enabled: original.leaveEnabled,
			statutory_defaults: original.statutoryDefaults,
			overtime_policy: original.overtimePolicy,
			wcb_config: original.wcbConfig,
			group_benefits: original.groupBenefits,
			earnings_config: original.earningsConfig,
			taxable_benefits_config: original.taxableBenefitsConfig,
			deductions_config: original.deductionsConfig
		});
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to duplicate pay group';
		return { data: null, error: message };
	}
}
