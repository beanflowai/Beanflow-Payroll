/**
 * Employee Service - Direct Supabase CRUD operations
 *
 * This service handles simple CRUD operations for employees directly
 * via the Supabase client. Complex calculations are handled by the backend API.
 */

import { supabase } from '$lib/api/supabase';
import { api, APIError } from '$lib/api/client';
import type {
	DbEmployee,
	DbEmployeeTaxClaim,
	EmployeeCreateInput,
	EmployeeUpdateInput,
	EmployeeTaxClaim,
	TaxClaimUpdateInput,
	Employee,
	Province,
	PayFrequency,
	EmploymentType
} from '$lib/types/employee';
import { dbEmployeeToUi, dbTaxClaimToUi } from '$lib/types/employee';
import { authState } from '$lib/stores/auth.svelte';
import { getCurrentCompanyId as getCompanyIdFromStore } from '$lib/stores/company.svelte';

// Re-export the conversion function for convenience
export { dbEmployeeToUi } from '$lib/types/employee';

const TABLE_NAME = 'employees';

/**
 * Helper to mask SIN for display (***-***-XXX)
 */
export function maskSin(sinEncrypted: string): string {
	// Since SIN is encrypted, we can't derive last 3 digits
	// In production, this would be handled by the backend
	return '***-***-***';
}

/**
 * Get current company ID from company store
 */
function getCurrentCompanyId(): string {
	return getCompanyIdFromStore();
}

/**
 * Get current user's user_id
 */
function getCurrentUserId(): string {
	const user = authState.user;
	if (!user) throw new Error('User not authenticated');
	return user.id;
}

export interface EmployeeListOptions {
	activeOnly?: boolean;
	province?: Province;
	limit?: number;
	offset?: number;
}

export interface EmployeeServiceResult<T> {
	data: T | null;
	error: string | null;
}

export interface EmployeeListResult {
	data: Employee[];
	count: number;
	error: string | null;
}

/**
 * List employees for the current user/company
 */
export async function listEmployees(
	options: EmployeeListOptions = {}
): Promise<EmployeeListResult> {
	const { activeOnly = true, province, limit = 100, offset = 0 } = options;

	try {
		const userId = getCurrentUserId();
		const companyId = getCurrentCompanyId();

		let query = supabase
			.from(TABLE_NAME)
			.select('*', { count: 'exact' })
			.eq('user_id', userId)
			.eq('company_id', companyId);

		if (activeOnly) {
			query = query.is('termination_date', null);
		}

		if (province) {
			query = query.eq('province_of_employment', province);
		}

		const { data, error, count } = await query
			.order('last_name')
			.order('first_name')
			.range(offset, offset + limit - 1);

		if (error) {
			console.error('Failed to list employees:', error);
			return { data: [], count: 0, error: error.message };
		}

		// Convert DB format to UI format
		const employees: Employee[] = (data as DbEmployee[]).map((db) =>
			dbEmployeeToUi(db, maskSin(db.sin_encrypted))
		);

		return { data: employees, count: count ?? 0, error: null };
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to list employees';
		return { data: [], count: 0, error: message };
	}
}

/**
 * Get a single employee by ID
 */
export async function getEmployee(employeeId: string): Promise<EmployeeServiceResult<Employee>> {
	try {
		const userId = getCurrentUserId();
		const companyId = getCurrentCompanyId();

		const { data, error } = await supabase
			.from(TABLE_NAME)
			.select('*')
			.eq('user_id', userId)
			.eq('company_id', companyId)
			.eq('id', employeeId)
			.single();

		if (error) {
			console.error('Failed to get employee:', error);
			return { data: null, error: error.message };
		}

		const db = data as DbEmployee;
		return {
			data: dbEmployeeToUi(db, maskSin(db.sin_encrypted)),
			error: null
		};
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to get employee';
		return { data: null, error: message };
	}
}

/**
 * Create a new employee
 *
 * Note: In production, SIN encryption should be handled by the backend
 * For now, we're storing it as-is (the backend API should encrypt it)
 */
export async function createEmployee(
	input: EmployeeCreateInput
): Promise<EmployeeServiceResult<Employee>> {
	try {
		const userId = getCurrentUserId();
		const companyId = getCurrentCompanyId();

		// Prepare the record with user/ledger IDs
		const record = {
			user_id: userId,
			company_id: companyId,
			first_name: input.first_name,
			last_name: input.last_name,
			sin_encrypted: input.sin, // In production, this should be encrypted by backend
			email: input.email ?? null,
			province_of_employment: input.province_of_employment,
			pay_frequency: input.pay_frequency,
			employment_type: input.employment_type ?? 'full_time',
			annual_salary: input.annual_salary ?? null,
			hourly_rate: input.hourly_rate ?? null,
			federal_additional_claims: input.federal_additional_claims,
			provincial_additional_claims: input.provincial_additional_claims,
			is_cpp_exempt: input.is_cpp_exempt ?? false,
			is_ei_exempt: input.is_ei_exempt ?? false,
			cpp2_exempt: input.cpp2_exempt ?? false,
			hire_date: input.hire_date,
			termination_date: input.termination_date ?? null,
			vacation_config: input.vacation_config ?? {
				payout_method: 'accrual',
				vacation_rate: '0.04'  // Default to 4% (standard minimum)
			},
			vacation_balance: input.vacation_balance ?? 0,
			// Initial YTD for transferred employees
			initial_ytd_cpp: input.initial_ytd_cpp ?? 0,
			initial_ytd_cpp2: input.initial_ytd_cpp2 ?? 0,
			initial_ytd_ei: input.initial_ytd_ei ?? 0,
			initial_ytd_year: input.initial_ytd_year ?? null
		};

		const { data, error } = await supabase.from(TABLE_NAME).insert(record).select().single();

		if (error) {
			console.error('Failed to create employee:', error);
			return { data: null, error: error.message };
		}

		const db = data as DbEmployee;
		return {
			data: dbEmployeeToUi(db, maskSin(db.sin_encrypted)),
			error: null
		};
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to create employee';
		return { data: null, error: message };
	}
}

/**
 * Update an existing employee
 */
export async function updateEmployee(
	employeeId: string,
	input: EmployeeUpdateInput
): Promise<EmployeeServiceResult<Employee>> {
	try {
		const userId = getCurrentUserId();
		const companyId = getCurrentCompanyId();

		// Build update object, only including defined fields
		const updateData: Record<string, unknown> = {};

		if (input.first_name !== undefined) updateData.first_name = input.first_name;
		if (input.last_name !== undefined) updateData.last_name = input.last_name;
		if (input.email !== undefined) updateData.email = input.email;
		// Address fields
		if (input.address_street !== undefined) updateData.address_street = input.address_street;
		if (input.address_city !== undefined) updateData.address_city = input.address_city;
		if (input.address_postal_code !== undefined) updateData.address_postal_code = input.address_postal_code;
		if (input.occupation !== undefined) updateData.occupation = input.occupation;
		if (input.province_of_employment !== undefined)
			updateData.province_of_employment = input.province_of_employment;
		if (input.pay_frequency !== undefined) updateData.pay_frequency = input.pay_frequency;
		if (input.employment_type !== undefined) updateData.employment_type = input.employment_type;
		if (input.annual_salary !== undefined) updateData.annual_salary = input.annual_salary;
		if (input.hourly_rate !== undefined) updateData.hourly_rate = input.hourly_rate;
		if (input.federal_additional_claims !== undefined)
			updateData.federal_additional_claims = input.federal_additional_claims;
		if (input.provincial_additional_claims !== undefined)
			updateData.provincial_additional_claims = input.provincial_additional_claims;
		if (input.is_cpp_exempt !== undefined) updateData.is_cpp_exempt = input.is_cpp_exempt;
		if (input.is_ei_exempt !== undefined) updateData.is_ei_exempt = input.is_ei_exempt;
		if (input.cpp2_exempt !== undefined) updateData.cpp2_exempt = input.cpp2_exempt;
		if (input.hire_date !== undefined) updateData.hire_date = input.hire_date;
		if (input.termination_date !== undefined) updateData.termination_date = input.termination_date;
		if (input.vacation_config !== undefined) updateData.vacation_config = input.vacation_config;
		if (input.vacation_balance !== undefined) updateData.vacation_balance = input.vacation_balance;
		// Initial YTD for transferred employees
		if (input.initial_ytd_cpp !== undefined) updateData.initial_ytd_cpp = input.initial_ytd_cpp;
		if (input.initial_ytd_cpp2 !== undefined) updateData.initial_ytd_cpp2 = input.initial_ytd_cpp2;
		if (input.initial_ytd_ei !== undefined) updateData.initial_ytd_ei = input.initial_ytd_ei;
		if (input.initial_ytd_year !== undefined) updateData.initial_ytd_year = input.initial_ytd_year;

		const { data, error } = await supabase
			.from(TABLE_NAME)
			.update(updateData)
			.eq('user_id', userId)
			.eq('company_id', companyId)
			.eq('id', employeeId)
			.select()
			.single();

		if (error) {
			console.error('Failed to update employee:', error);
			return { data: null, error: error.message };
		}

		const db = data as DbEmployee;
		return {
			data: dbEmployeeToUi(db, maskSin(db.sin_encrypted)),
			error: null
		};
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to update employee';
		return { data: null, error: message };
	}
}

/**
 * Terminate an employee (soft delete)
 */
export async function terminateEmployee(
	employeeId: string,
	terminationDate: string
): Promise<EmployeeServiceResult<Employee>> {
	return updateEmployee(employeeId, { termination_date: terminationDate });
}

/**
 * Delete an employee (hard delete - use with caution)
 */
export async function deleteEmployee(employeeId: string): Promise<{ error: string | null }> {
	try {
		const userId = getCurrentUserId();
		const companyId = getCurrentCompanyId();

		const { error } = await supabase
			.from(TABLE_NAME)
			.delete()
			.eq('user_id', userId)
			.eq('company_id', companyId)
			.eq('id', employeeId);

		if (error) {
			console.error('Failed to delete employee:', error);
			return { error: error.message };
		}

		return { error: null };
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to delete employee';
		return { error: message };
	}
}

/**
 * Get employee count
 */
export async function getEmployeeCount(activeOnly = true): Promise<number> {
	try {
		const userId = getCurrentUserId();
		const companyId = getCurrentCompanyId();

		let query = supabase
			.from(TABLE_NAME)
			.select('id', { count: 'exact', head: true })
			.eq('user_id', userId)
			.eq('company_id', companyId);

		if (activeOnly) {
			query = query.is('termination_date', null);
		}

		const { count, error } = await query;

		if (error) {
			console.error('Failed to get employee count:', error);
			return 0;
		}

		return count ?? 0;
	} catch {
		return 0;
	}
}

/**
 * Get employees grouped by province (for stats)
 */
export async function getEmployeesByProvince(): Promise<Record<Province, number>> {
	try {
		const userId = getCurrentUserId();
		const companyId = getCurrentCompanyId();

		const { data, error } = await supabase
			.from(TABLE_NAME)
			.select('province_of_employment')
			.eq('user_id', userId)
			.eq('company_id', companyId)
			.is('termination_date', null);

		if (error) {
			console.error('Failed to get employees by province:', error);
			return {} as Record<Province, number>;
		}

		const counts: Record<string, number> = {};
		for (const row of data ?? []) {
			const province = row.province_of_employment as Province;
			counts[province] = (counts[province] ?? 0) + 1;
		}

		return counts as Record<Province, number>;
	} catch {
		return {} as Record<Province, number>;
	}
}

/**
 * Get employees grouped by pay frequency (for stats)
 */
export async function getEmployeesByPayFrequency(): Promise<Record<PayFrequency, number>> {
	try {
		const userId = getCurrentUserId();
		const companyId = getCurrentCompanyId();

		const { data, error } = await supabase
			.from(TABLE_NAME)
			.select('pay_frequency')
			.eq('user_id', userId)
			.eq('company_id', companyId)
			.is('termination_date', null);

		if (error) {
			console.error('Failed to get employees by pay frequency:', error);
			return {} as Record<PayFrequency, number>;
		}

		const counts: Record<string, number> = {};
		for (const row of data ?? []) {
			const freq = row.pay_frequency as PayFrequency;
			counts[freq] = (counts[freq] ?? 0) + 1;
		}

		return counts as Record<PayFrequency, number>;
	} catch {
		return {} as Record<PayFrequency, number>;
	}
}

// ===========================================
// Pay Group Assignment Functions
// ===========================================

/**
 * Get employees assigned to a specific pay group
 */
export async function getEmployeesByPayGroup(
	payGroupId: string
): Promise<EmployeeListResult> {
	try {
		const userId = getCurrentUserId();
		const companyId = getCurrentCompanyId();

		const { data, error, count } = await supabase
			.from(TABLE_NAME)
			.select('*', { count: 'exact' })
			.eq('user_id', userId)
			.eq('company_id', companyId)
			.eq('pay_group_id', payGroupId)
			.is('termination_date', null)
			.order('last_name')
			.order('first_name');

		if (error) {
			console.error('Failed to get employees by pay group:', error);
			return { data: [], count: 0, error: error.message };
		}

		const employees: Employee[] = (data as DbEmployee[]).map((db) =>
			dbEmployeeToUi(db, maskSin(db.sin_encrypted))
		);

		return { data: employees, count: count ?? 0, error: null };
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to get employees by pay group';
		return { data: [], count: 0, error: message };
	}
}

/**
 * Filters for getting unassigned employees
 */
export interface UnassignedEmployeeFilters {
	employmentType?: EmploymentType;
	payFrequency?: PayFrequency;
}

/**
 * Get employees not assigned to any pay group
 * Optionally filter by employment type and pay frequency for pay group matching
 */
export async function getUnassignedEmployees(
	filters?: UnassignedEmployeeFilters
): Promise<EmployeeListResult> {
	try {
		const userId = getCurrentUserId();
		const companyId = getCurrentCompanyId();

		let query = supabase
			.from(TABLE_NAME)
			.select('*', { count: 'exact' })
			.eq('user_id', userId)
			.eq('company_id', companyId)
			.is('pay_group_id', null)
			.is('termination_date', null);

		// Apply optional filters for pay group matching
		if (filters?.employmentType) {
			query = query.eq('employment_type', filters.employmentType);
		}
		if (filters?.payFrequency) {
			query = query.eq('pay_frequency', filters.payFrequency);
		}

		const { data, error, count } = await query.order('last_name').order('first_name');

		if (error) {
			console.error('Failed to get unassigned employees:', error);
			return { data: [], count: 0, error: error.message };
		}

		const employees: Employee[] = (data as DbEmployee[]).map((db) =>
			dbEmployeeToUi(db, maskSin(db.sin_encrypted))
		);

		return { data: employees, count: count ?? 0, error: null };
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to get unassigned employees';
		return { data: [], count: 0, error: message };
	}
}

/**
 * Assign multiple employees to a pay group
 */
export async function assignEmployeesToPayGroup(
	employeeIds: string[],
	payGroupId: string
): Promise<{ error: string | null }> {
	try {
		const userId = getCurrentUserId();
		const companyId = getCurrentCompanyId();

		const { error } = await supabase
			.from(TABLE_NAME)
			.update({ pay_group_id: payGroupId })
			.eq('user_id', userId)
			.eq('company_id', companyId)
			.in('id', employeeIds);

		if (error) {
			console.error('Failed to assign employees to pay group:', error);
			return { error: error.message };
		}

		return { error: null };
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to assign employees';
		return { error: message };
	}
}

/**
 * Remove an employee from their pay group (set pay_group_id to null)
 */
export async function removeEmployeeFromPayGroup(
	employeeId: string
): Promise<{ error: string | null }> {
	try {
		const userId = getCurrentUserId();
		const companyId = getCurrentCompanyId();

		const { error } = await supabase
			.from(TABLE_NAME)
			.update({ pay_group_id: null })
			.eq('user_id', userId)
			.eq('company_id', companyId)
			.eq('id', employeeId);

		if (error) {
			console.error('Failed to remove employee from pay group:', error);
			return { error: error.message };
		}

		return { error: null };
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to remove employee from pay group';
		return { error: message };
	}
}

// ===========================================
// Payroll Record Check Functions
// ===========================================

/**
 * Check if an employee has any payroll records.
 * Used to determine if vacation balance can be manually edited.
 * If employee has payroll records, balance should be managed by the payroll system.
 */
export async function checkEmployeeHasPayrollRecords(
	employeeId: string
): Promise<boolean> {
	try {
		const { count, error } = await supabase
			.from('payroll_records')
			.select('id', { count: 'exact', head: true })
			.eq('employee_id', employeeId)
			.limit(1);

		if (error) {
			console.error('Failed to check payroll records:', error);
			return false; // On error, default to allowing edit
		}

		return (count ?? 0) > 0;
	} catch {
		return false;
	}
}

// =============================================================================
// Tax Claims Functions (TD1 by year)
// =============================================================================

const TAX_CLAIMS_TABLE = 'employee_tax_claims';

export type TaxClaimServiceResult<T> = {
	data: T | null;
	error: string | null;
};

/**
 * Get all tax claims for an employee, ordered by year descending
 */
export async function getEmployeeTaxClaims(
	employeeId: string
): Promise<TaxClaimServiceResult<EmployeeTaxClaim[]>> {
	try {
		const userId = getCurrentUserId();

		const { data, error } = await supabase
			.from(TAX_CLAIMS_TABLE)
			.select('*')
			.eq('employee_id', employeeId)
			.eq('user_id', userId)
			.order('tax_year', { ascending: false });

		if (error) {
			console.error('Failed to fetch tax claims:', error);
			return { data: null, error: error.message };
		}

		return {
			data: (data as DbEmployeeTaxClaim[]).map(dbTaxClaimToUi),
			error: null
		};
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to fetch tax claims';
		return { data: null, error: message };
	}
}

/**
 * Get tax claim for a specific year
 */
export async function getEmployeeTaxClaimByYear(
	employeeId: string,
	taxYear: number
): Promise<TaxClaimServiceResult<EmployeeTaxClaim>> {
	try {
		const userId = getCurrentUserId();
		const companyId = getCurrentCompanyId();

		const { data, error } = await supabase
			.from(TAX_CLAIMS_TABLE)
			.select('*')
			.eq('employee_id', employeeId)
			.eq('user_id', userId)
			.eq('company_id', companyId)
			.eq('tax_year', taxYear)
			.single();

		if (error) {
			console.error('Failed to fetch tax claim:', error);
			return { data: null, error: error.message };
		}

		return {
			data: dbTaxClaimToUi(data as DbEmployeeTaxClaim),
			error: null
		};
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to fetch tax claim';
		return { data: null, error: message };
	}
}

/**
 * Create tax claim record for a specific year
 */
export async function createEmployeeTaxClaim(
	employeeId: string,
	taxYear: number,
	federalBpa: number,
	provincialBpa: number,
	federalAdditionalClaims: number = 0,
	provincialAdditionalClaims: number = 0
): Promise<TaxClaimServiceResult<EmployeeTaxClaim>> {
	try {
		const userId = getCurrentUserId();
		const companyId = getCurrentCompanyId();

		const record = {
			employee_id: employeeId,
			company_id: companyId,
			user_id: userId,
			tax_year: taxYear,
			federal_bpa: federalBpa,
			federal_additional_claims: federalAdditionalClaims,
			provincial_bpa: provincialBpa,
			provincial_additional_claims: provincialAdditionalClaims
		};

		const { data, error } = await supabase
			.from(TAX_CLAIMS_TABLE)
			.insert(record)
			.select()
			.single();

		if (error) {
			console.error('Failed to create tax claim:', error);
			return { data: null, error: error.message };
		}

		return {
			data: dbTaxClaimToUi(data as DbEmployeeTaxClaim),
			error: null
		};
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to create tax claim';
		return { data: null, error: message };
	}
}

/**
 * Update tax claim additional claims for a specific year
 * Note: BPA values are read-only and cannot be updated
 */
export async function updateEmployeeTaxClaim(
	employeeId: string,
	taxYear: number,
	input: TaxClaimUpdateInput
): Promise<TaxClaimServiceResult<EmployeeTaxClaim>> {
	try {
		const userId = getCurrentUserId();
		const companyId = getCurrentCompanyId();

		// Only allow updating additional claims (BPA is read-only)
		const updateData: Record<string, number> = {};
		if (input.federalAdditionalClaims !== undefined) {
			updateData.federal_additional_claims = input.federalAdditionalClaims;
		}
		if (input.provincialAdditionalClaims !== undefined) {
			updateData.provincial_additional_claims = input.provincialAdditionalClaims;
		}

		if (Object.keys(updateData).length === 0) {
			return { data: null, error: 'No fields to update' };
		}

		const { data, error } = await supabase
			.from(TAX_CLAIMS_TABLE)
			.update(updateData)
			.eq('employee_id', employeeId)
			.eq('user_id', userId)
			.eq('company_id', companyId)
			.eq('tax_year', taxYear)
			.select()
			.single();

		if (error) {
			console.error('Failed to update tax claim:', error);
			return { data: null, error: error.message };
		}

		return {
			data: dbTaxClaimToUi(data as DbEmployeeTaxClaim),
			error: null
		};
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to update tax claim';
		return { data: null, error: message };
	}
}

/**
 * Ensure tax claims exist for an employee for the current and previous year.
 * Creates records if they don't exist with BPA values from tax config.
 */
export async function ensureTaxClaimsForEmployee(
	employeeId: string,
	province: Province,
	federalBpa2026: number,
	federalBpa2025: number,
	provincialBpa2026: number,
	provincialBpa2025: number,
	existingFederalClaims: number = 0,
	existingProvincialClaims: number = 0
): Promise<void> {
	const currentYear = new Date().getFullYear();
	const previousYear = currentYear - 1;

	// Check and create for current year
	const currentResult = await getEmployeeTaxClaimByYear(employeeId, currentYear);
	if (!currentResult.data) {
		await createEmployeeTaxClaim(
			employeeId,
			currentYear,
			federalBpa2026,
			provincialBpa2026,
			existingFederalClaims,
			existingProvincialClaims
		);
	}

	// Check and create for previous year
	const previousResult = await getEmployeeTaxClaimByYear(employeeId, previousYear);
	if (!previousResult.data) {
		await createEmployeeTaxClaim(
			employeeId,
			previousYear,
			federalBpa2025,
			provincialBpa2025,
			existingFederalClaims,
			existingProvincialClaims
		);
	}
}

// =============================================================================
// Tax Claims API Functions (Backend API - BPA derived server-side)
// =============================================================================

/**
 * Backend API response format for tax claims
 */
interface ApiTaxClaim {
	id: string;
	employee_id: string;
	company_id: string;
	tax_year: number;
	federal_bpa: number;
	federal_additional_claims: number;
	provincial_bpa: number;
	provincial_additional_claims: number;
	created_at: string;
	updated_at: string;
}

/**
 * Convert API response to UI format
 */
function apiTaxClaimToUi(api: ApiTaxClaim): EmployeeTaxClaim {
	return {
		id: api.id,
		employeeId: api.employee_id,
		companyId: api.company_id,
		taxYear: api.tax_year,
		federalBpa: api.federal_bpa,
		federalAdditionalClaims: api.federal_additional_claims,
		federalTotalClaim: api.federal_bpa + api.federal_additional_claims,
		provincialBpa: api.provincial_bpa,
		provincialAdditionalClaims: api.provincial_additional_claims,
		provincialTotalClaim: api.provincial_bpa + api.provincial_additional_claims,
		createdAt: api.created_at,
		updatedAt: api.updated_at
	};
}

/**
 * Create tax claim via backend API (BPA derived server-side).
 * This is the preferred method as it ensures BPA values come from
 * the authoritative tax configuration on the server.
 */
export async function createEmployeeTaxClaimViaApi(
	employeeId: string,
	taxYear: number,
	federalAdditionalClaims: number = 0,
	provincialAdditionalClaims: number = 0
): Promise<TaxClaimServiceResult<EmployeeTaxClaim>> {
	try {
		const response = await api.post<ApiTaxClaim>(`/employees/${employeeId}/tax-claims`, {
			tax_year: taxYear,
			federal_additional_claims: federalAdditionalClaims,
			provincial_additional_claims: provincialAdditionalClaims
		});

		return {
			data: apiTaxClaimToUi(response),
			error: null
		};
	} catch (err) {
		if (err instanceof APIError) {
			// Handle conflict (claim already exists)
			if (err.status === 409) {
				return { data: null, error: `Tax claim already exists for year ${taxYear}` };
			}
			return { data: null, error: err.message };
		}
		const message = err instanceof Error ? err.message : 'Failed to create tax claim via API';
		return { data: null, error: message };
	}
}

/**
 * Update tax claim via backend API.
 * By default, only additional claims can be updated.
 * Set recalculateBpa=true to refresh BPA values from tax config (e.g., after province change).
 */
export async function updateEmployeeTaxClaimViaApi(
	employeeId: string,
	taxYear: number,
	input: TaxClaimUpdateInput,
	recalculateBpa: boolean = false
): Promise<TaxClaimServiceResult<EmployeeTaxClaim>> {
	try {
		const body: Record<string, number | boolean> = {};
		if (input.federalAdditionalClaims !== undefined) {
			body.federal_additional_claims = input.federalAdditionalClaims;
		}
		if (input.provincialAdditionalClaims !== undefined) {
			body.provincial_additional_claims = input.provincialAdditionalClaims;
		}
		if (recalculateBpa) {
			body.recalculate_bpa = true;
		}

		const response = await api.put<ApiTaxClaim>(
			`/employees/${employeeId}/tax-claims/${taxYear}`,
			body
		);

		return {
			data: apiTaxClaimToUi(response),
			error: null
		};
	} catch (err) {
		if (err instanceof APIError) {
			return { data: null, error: err.message };
		}
		const message = err instanceof Error ? err.message : 'Failed to update tax claim via API';
		return { data: null, error: message };
	}
}

/**
 * Get tax claims via backend API.
 */
export async function getEmployeeTaxClaimsViaApi(
	employeeId: string
): Promise<TaxClaimServiceResult<EmployeeTaxClaim[]>> {
	try {
		const response = await api.get<ApiTaxClaim[]>(`/employees/${employeeId}/tax-claims`);

		return {
			data: response.map(apiTaxClaimToUi),
			error: null
		};
	} catch (err) {
		if (err instanceof APIError) {
			return { data: null, error: err.message };
		}
		const message = err instanceof Error ? err.message : 'Failed to fetch tax claims via API';
		return { data: null, error: message };
	}
}
