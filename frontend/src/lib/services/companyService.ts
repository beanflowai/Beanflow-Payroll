/**
 * Company Service - Direct Supabase CRUD operations
 *
 * This service handles CRUD operations for companies directly
 * via the Supabase client.
 */

import { supabase } from '$lib/api/supabase';
import type { CompanyProfile, RemitterType } from '$lib/types/company';
import type { Province } from '$lib/types/employee';
import { authState } from '$lib/stores/auth.svelte';

const TABLE_NAME = 'companies';

/**
 * Database company record (snake_case from Supabase)
 */
export interface DbCompany {
	id: string;
	user_id: string;
	company_name: string;
	business_number: string;
	payroll_account_number: string;
	province: Province;
	remitter_type: RemitterType;
	auto_calculate_deductions: boolean;
	send_paystub_emails: boolean;
	bookkeeping_ledger_id: string | null;
	bookkeeping_ledger_name: string | null;
	bookkeeping_connected_at: string | null;
	created_at: string;
	updated_at: string;
}

/**
 * Company creation input
 */
export interface CompanyCreateInput {
	company_name: string;
	business_number: string;
	payroll_account_number: string;
	province: Province;
	remitter_type?: RemitterType;
	auto_calculate_deductions?: boolean;
	send_paystub_emails?: boolean;
}

/**
 * Company update input (all fields optional)
 */
export interface CompanyUpdateInput {
	company_name?: string;
	business_number?: string;
	payroll_account_number?: string;
	province?: Province;
	remitter_type?: RemitterType;
	auto_calculate_deductions?: boolean;
	send_paystub_emails?: boolean;
	bookkeeping_ledger_id?: string | null;
	bookkeeping_ledger_name?: string | null;
	bookkeeping_connected_at?: string | null;
}

/**
 * Convert DB record to UI CompanyProfile
 */
export function dbCompanyToUi(db: DbCompany): CompanyProfile {
	return {
		id: db.id,
		userId: db.user_id,
		companyName: db.company_name,
		businessNumber: db.business_number,
		payrollAccountNumber: db.payroll_account_number,
		province: db.province,
		remitterType: db.remitter_type,
		autoCalculateDeductions: db.auto_calculate_deductions,
		sendPaystubEmails: db.send_paystub_emails,
		bookkeepingLedgerId: db.bookkeeping_ledger_id,
		bookkeepingLedgerName: db.bookkeeping_ledger_name,
		bookkeepingConnectedAt: db.bookkeeping_connected_at,
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

export interface CompanyServiceResult<T> {
	data: T | null;
	error: string | null;
}

export interface CompanyListResult {
	data: CompanyProfile[];
	count: number;
	error: string | null;
}

export interface CompanyListOptions {
	province?: Province;
	search?: string;
	limit?: number;
	offset?: number;
}

/**
 * List companies for the current user
 */
export async function listCompanies(
	options: CompanyListOptions = {}
): Promise<CompanyListResult> {
	const { province, search, limit = 100, offset = 0 } = options;

	try {
		const userId = getCurrentUserId();

		let query = supabase
			.from(TABLE_NAME)
			.select('*', { count: 'exact' })
			.eq('user_id', userId);

		if (province) {
			query = query.eq('province', province);
		}

		if (search) {
			query = query.ilike('company_name', `%${search}%`);
		}

		const { data, error, count } = await query
			.order('company_name')
			.range(offset, offset + limit - 1);

		if (error) {
			console.error('Failed to list companies:', error);
			return { data: [], count: 0, error: error.message };
		}

		const companies: CompanyProfile[] = (data as DbCompany[]).map(dbCompanyToUi);

		return { data: companies, count: count ?? 0, error: null };
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to list companies';
		return { data: [], count: 0, error: message };
	}
}

/**
 * Get a single company by ID
 */
export async function getCompany(companyId: string): Promise<CompanyServiceResult<CompanyProfile>> {
	try {
		const userId = getCurrentUserId();

		const { data, error } = await supabase
			.from(TABLE_NAME)
			.select('*')
			.eq('user_id', userId)
			.eq('id', companyId)
			.single();

		if (error) {
			console.error('Failed to get company:', error);
			return { data: null, error: error.message };
		}

		return {
			data: dbCompanyToUi(data as DbCompany),
			error: null
		};
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to get company';
		return { data: null, error: message };
	}
}

/**
 * Create a new company
 */
export async function createCompany(
	input: CompanyCreateInput
): Promise<CompanyServiceResult<CompanyProfile>> {
	try {
		const userId = getCurrentUserId();

		const record = {
			user_id: userId,
			company_name: input.company_name,
			business_number: input.business_number,
			payroll_account_number: input.payroll_account_number,
			province: input.province,
			remitter_type: input.remitter_type ?? 'regular',
			auto_calculate_deductions: input.auto_calculate_deductions ?? true,
			send_paystub_emails: input.send_paystub_emails ?? false
		};

		const { data, error } = await supabase.from(TABLE_NAME).insert(record).select().single();

		if (error) {
			console.error('Failed to create company:', error);
			return { data: null, error: error.message };
		}

		return {
			data: dbCompanyToUi(data as DbCompany),
			error: null
		};
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to create company';
		return { data: null, error: message };
	}
}

/**
 * Update an existing company
 */
export async function updateCompany(
	companyId: string,
	input: CompanyUpdateInput
): Promise<CompanyServiceResult<CompanyProfile>> {
	try {
		const userId = getCurrentUserId();

		// Build update object, only including defined fields
		const updateData: Record<string, unknown> = {};

		if (input.company_name !== undefined) updateData.company_name = input.company_name;
		if (input.business_number !== undefined) updateData.business_number = input.business_number;
		if (input.payroll_account_number !== undefined)
			updateData.payroll_account_number = input.payroll_account_number;
		if (input.province !== undefined) updateData.province = input.province;
		if (input.remitter_type !== undefined) updateData.remitter_type = input.remitter_type;
		if (input.auto_calculate_deductions !== undefined)
			updateData.auto_calculate_deductions = input.auto_calculate_deductions;
		if (input.send_paystub_emails !== undefined)
			updateData.send_paystub_emails = input.send_paystub_emails;
		if (input.bookkeeping_ledger_id !== undefined)
			updateData.bookkeeping_ledger_id = input.bookkeeping_ledger_id;
		if (input.bookkeeping_ledger_name !== undefined)
			updateData.bookkeeping_ledger_name = input.bookkeeping_ledger_name;
		if (input.bookkeeping_connected_at !== undefined)
			updateData.bookkeeping_connected_at = input.bookkeeping_connected_at;

		const { data, error } = await supabase
			.from(TABLE_NAME)
			.update(updateData)
			.eq('user_id', userId)
			.eq('id', companyId)
			.select()
			.single();

		if (error) {
			console.error('Failed to update company:', error);
			return { data: null, error: error.message };
		}

		return {
			data: dbCompanyToUi(data as DbCompany),
			error: null
		};
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to update company';
		return { data: null, error: message };
	}
}

/**
 * Delete a company (hard delete)
 */
export async function deleteCompany(companyId: string): Promise<{ error: string | null }> {
	try {
		const userId = getCurrentUserId();

		const { error } = await supabase
			.from(TABLE_NAME)
			.delete()
			.eq('user_id', userId)
			.eq('id', companyId);

		if (error) {
			console.error('Failed to delete company:', error);
			return { error: error.message };
		}

		return { error: null };
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to delete company';
		return { error: message };
	}
}

/**
 * Get company count
 */
export async function getCompanyCount(): Promise<number> {
	try {
		const userId = getCurrentUserId();

		const { count, error } = await supabase
			.from(TABLE_NAME)
			.select('id', { count: 'exact', head: true })
			.eq('user_id', userId);

		if (error) {
			console.error('Failed to get company count:', error);
			return 0;
		}

		return count ?? 0;
	} catch {
		return 0;
	}
}

/**
 * Get or create the default company for a user
 * (For single-company scenarios during development)
 */
export async function getOrCreateDefaultCompany(): Promise<CompanyServiceResult<CompanyProfile>> {
	const { data: companies, error: listError } = await listCompanies({ limit: 1 });

	if (listError) {
		return { data: null, error: listError };
	}

	if (companies.length > 0) {
		return { data: companies[0], error: null };
	}

	// No company exists, return null (caller should create one)
	return { data: null, error: null };
}
