/**
 * Remittance Service - Direct Supabase CRUD operations
 *
 * Handles remittance period management for CRA payroll deduction tracking.
 * Complex operations (PDF generation) use backend API.
 */

import { supabase } from '$lib/api/supabase';
import type {
	RemittancePeriod,
	RemittanceSummary,
	RemittanceStatus,
	PaymentMethod
} from '$lib/types/remittance';
import type { RemitterType } from '$lib/types/company';
import { authState } from '$lib/stores/auth.svelte';

const TABLE_NAME = 'remittance_periods';

// =============================================================================
// Database Types (snake_case)
// =============================================================================

interface DbRemittancePeriod {
	id: string;
	company_id: string;
	user_id: string;
	remitter_type: RemitterType;
	period_start: string;
	period_end: string;
	due_date: string;
	cpp_employee: number;
	cpp_employer: number;
	ei_employee: number;
	ei_employer: number;
	federal_tax: number;
	provincial_tax: number;
	total_amount: number;
	status: RemittanceStatus;
	paid_date: string | null;
	payment_method: PaymentMethod | null;
	confirmation_number: string | null;
	notes: string | null;
	days_overdue: number;
	penalty_rate: number;
	penalty_amount: number;
	payroll_run_ids: string[];
	created_at: string;
	updated_at: string;
}

// =============================================================================
// Type Conversion
// =============================================================================

/**
 * Convert DB record (snake_case) to UI type (camelCase)
 */
function dbToUi(db: DbRemittancePeriod): RemittancePeriod {
	return {
		id: db.id,
		companyId: db.company_id,
		remitterType: db.remitter_type,
		periodStart: db.period_start,
		periodEnd: db.period_end,
		periodLabel: formatPeriodLabel(db.remitter_type, db.period_start, db.period_end),
		dueDate: db.due_date,
		cppEmployee: db.cpp_employee,
		cppEmployer: db.cpp_employer,
		eiEmployee: db.ei_employee,
		eiEmployer: db.ei_employer,
		federalTax: db.federal_tax,
		provincialTax: db.provincial_tax,
		totalAmount: db.total_amount,
		status: db.status,
		paidDate: db.paid_date,
		paymentMethod: db.payment_method,
		confirmationNumber: db.confirmation_number,
		notes: db.notes,
		daysOverdue: db.days_overdue,
		penaltyRate: db.penalty_rate,
		penaltyAmount: db.penalty_amount,
		payrollRunIds: db.payroll_run_ids,
		createdAt: db.created_at,
		updatedAt: db.updated_at
	};
}

/**
 * Format period label based on remitter type
 */
function formatPeriodLabel(
	remitterType: RemitterType,
	periodStart: string,
	periodEnd: string
): string {
	const start = new Date(periodStart);
	const end = new Date(periodEnd);
	const monthNames = [
		'January', 'February', 'March', 'April', 'May', 'June',
		'July', 'August', 'September', 'October', 'November', 'December'
	];

	switch (remitterType) {
		case 'quarterly': {
			const quarter = Math.ceil((end.getMonth() + 1) / 3);
			return `Q${quarter} ${end.getFullYear()}`;
		}
		case 'regular':
			return `${monthNames[end.getMonth()]} ${end.getFullYear()}`;
		case 'threshold_1':
		case 'threshold_2': {
			const monthShort = monthNames[end.getMonth()].substring(0, 3);
			return `${monthShort} ${start.getDate()}-${end.getDate()}`;
		}
		default:
			return `${monthNames[end.getMonth()]} ${end.getFullYear()}`;
	}
}

// =============================================================================
// Helper Functions
// =============================================================================

function getCurrentUserId(): string {
	const user = authState.user;
	if (!user) throw new Error('User not authenticated');
	return user.id;
}

// =============================================================================
// Service Result Types
// =============================================================================

export interface RemittanceServiceResult<T> {
	data: T | null;
	error: string | null;
}

export interface RemittanceListResult {
	data: RemittancePeriod[];
	count: number;
	error: string | null;
}

export interface RemittanceListOptions {
	year?: number;
	status?: RemittanceStatus;
	limit?: number;
	offset?: number;
}

// =============================================================================
// Create Input Types
// =============================================================================

export interface RemittancePeriodCreateInput {
	company_id: string;
	remitter_type: RemitterType;
	period_start: string;
	period_end: string;
	due_date: string;
	cpp_employee?: number;
	cpp_employer?: number;
	ei_employee?: number;
	ei_employer?: number;
	federal_tax?: number;
	provincial_tax?: number;
	payroll_run_ids?: string[];
}

export interface RecordPaymentInput {
	paid_date: string;
	payment_method: PaymentMethod;
	confirmation_number?: string;
	notes?: string;
}

// =============================================================================
// CRUD Operations
// =============================================================================

/**
 * List remittance periods for a company
 */
export async function listRemittancePeriods(
	companyId: string,
	options: RemittanceListOptions = {}
): Promise<RemittanceListResult> {
	const { year, status, limit = 100, offset = 0 } = options;

	try {
		const userId = getCurrentUserId();

		let query = supabase
			.from(TABLE_NAME)
			.select('*', { count: 'exact' })
			.eq('user_id', userId)
			.eq('company_id', companyId);

		// Year filter
		if (year) {
			query = query
				.gte('period_start', `${year}-01-01`)
				.lte('period_end', `${year}-12-31`);
		}

		// Status filter
		if (status) {
			query = query.eq('status', status);
		}

		const { data, error, count } = await query
			.order('due_date', { ascending: false })
			.range(offset, offset + limit - 1);

		if (error) {
			console.error('Failed to list remittance periods:', error);
			return { data: [], count: 0, error: error.message };
		}

		const periods = (data as DbRemittancePeriod[]).map(dbToUi);
		return { data: periods, count: count ?? 0, error: null };
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to list remittance periods';
		return { data: [], count: 0, error: message };
	}
}

/**
 * Get a single remittance period by ID
 */
export async function getRemittancePeriod(
	periodId: string
): Promise<RemittanceServiceResult<RemittancePeriod>> {
	try {
		const userId = getCurrentUserId();

		const { data, error } = await supabase
			.from(TABLE_NAME)
			.select('*')
			.eq('user_id', userId)
			.eq('id', periodId)
			.single();

		if (error) {
			console.error('Failed to get remittance period:', error);
			return { data: null, error: error.message };
		}

		return { data: dbToUi(data as DbRemittancePeriod), error: null };
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to get remittance period';
		return { data: null, error: message };
	}
}

/**
 * Create a new remittance period
 */
export async function createRemittancePeriod(
	input: RemittancePeriodCreateInput
): Promise<RemittanceServiceResult<RemittancePeriod>> {
	try {
		const userId = getCurrentUserId();

		const record = {
			user_id: userId,
			company_id: input.company_id,
			remitter_type: input.remitter_type,
			period_start: input.period_start,
			period_end: input.period_end,
			due_date: input.due_date,
			cpp_employee: input.cpp_employee ?? 0,
			cpp_employer: input.cpp_employer ?? 0,
			ei_employee: input.ei_employee ?? 0,
			ei_employer: input.ei_employer ?? 0,
			federal_tax: input.federal_tax ?? 0,
			provincial_tax: input.provincial_tax ?? 0,
			payroll_run_ids: input.payroll_run_ids ?? []
		};

		const { data, error } = await supabase
			.from(TABLE_NAME)
			.insert(record)
			.select()
			.single();

		if (error) {
			console.error('Failed to create remittance period:', error);
			return { data: null, error: error.message };
		}

		return { data: dbToUi(data as DbRemittancePeriod), error: null };
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to create remittance period';
		return { data: null, error: message };
	}
}

/**
 * Record payment for a remittance period
 */
export async function recordPayment(
	periodId: string,
	input: RecordPaymentInput
): Promise<RemittanceServiceResult<RemittancePeriod>> {
	try {
		const userId = getCurrentUserId();

		// Get existing period to check due date
		const { data: existing, error: fetchError } = await supabase
			.from(TABLE_NAME)
			.select('due_date')
			.eq('user_id', userId)
			.eq('id', periodId)
			.single();

		if (fetchError) {
			return { data: null, error: fetchError.message };
		}

		// Determine if paid late
		const dueDate = new Date(existing.due_date);
		const paidDate = new Date(input.paid_date);
		const isLate = paidDate > dueDate;
		const newStatus: RemittanceStatus = isLate ? 'paid_late' : 'paid';

		const updateData = {
			status: newStatus,
			paid_date: input.paid_date,
			payment_method: input.payment_method,
			confirmation_number: input.confirmation_number ?? null,
			notes: input.notes ?? null
		};

		const { data, error } = await supabase
			.from(TABLE_NAME)
			.update(updateData)
			.eq('user_id', userId)
			.eq('id', periodId)
			.select()
			.single();

		if (error) {
			console.error('Failed to record payment:', error);
			return { data: null, error: error.message };
		}

		return { data: dbToUi(data as DbRemittancePeriod), error: null };
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to record payment';
		return { data: null, error: message };
	}
}

/**
 * Delete a remittance period
 */
export async function deleteRemittancePeriod(
	periodId: string
): Promise<{ error: string | null }> {
	try {
		const userId = getCurrentUserId();

		const { error } = await supabase
			.from(TABLE_NAME)
			.delete()
			.eq('user_id', userId)
			.eq('id', periodId);

		if (error) {
			console.error('Failed to delete remittance period:', error);
			return { error: error.message };
		}

		return { error: null };
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to delete remittance period';
		return { error: message };
	}
}

// =============================================================================
// Summary & Statistics
// =============================================================================

/**
 * Get remittance summary for a company/year
 */
export async function getRemittanceSummary(
	companyId: string,
	year: number
): Promise<RemittanceServiceResult<RemittanceSummary>> {
	try {
		const { data: periods, error } = await listRemittancePeriods(companyId, { year });

		if (error) {
			return { data: null, error };
		}

		const paidStatuses: RemittanceStatus[] = ['paid', 'paid_late'];
		const pendingStatuses: RemittanceStatus[] = ['pending', 'due_soon', 'overdue'];

		const paidPeriods = periods.filter(p => paidStatuses.includes(p.status));
		const pendingPeriods = periods.filter(p => pendingStatuses.includes(p.status));
		const onTimePeriods = periods.filter(p => p.status === 'paid');

		const summary: RemittanceSummary = {
			year,
			ytdRemitted: paidPeriods.reduce((sum, p) => sum + p.totalAmount, 0),
			totalRemittances: periods.length,
			completedRemittances: paidPeriods.length,
			onTimeRate: paidPeriods.length > 0
				? onTimePeriods.length / paidPeriods.length
				: 1.0,
			pendingAmount: pendingPeriods.reduce((sum, p) => sum + p.totalAmount, 0),
			pendingCount: pendingPeriods.length
		};

		return { data: summary, error: null };
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to get remittance summary';
		return { data: null, error: message };
	}
}

// =============================================================================
// PDF Download URL (Backend API)
// =============================================================================

/**
 * Get the URL for downloading PD7A PDF voucher
 * This calls the backend API endpoint
 */
export function getPD7ADownloadUrl(companyId: string, periodId: string): string {
	return `/api/v1/remittance/pd7a/${companyId}/${periodId}`;
}
