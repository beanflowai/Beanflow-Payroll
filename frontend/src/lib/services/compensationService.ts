/**
 * Compensation Service
 *
 * Handles employee compensation history operations.
 * - Read operations: Direct Supabase client (simple queries)
 * - Write operations: Backend API (transactional updates)
 */

import { supabase } from '$lib/api/supabase';
import { api } from '$lib/api/client';
import type {
	CompensationHistory,
	CompensationHistoryCreate
} from '$lib/types/compensation';

const TABLE_NAME = 'employee_compensation_history';

/**
 * Get compensation history for an employee.
 * Returns all historical records sorted by effective date (newest first).
 */
export async function getCompensationHistory(
	employeeId: string
): Promise<{ data: CompensationHistory[] | null; error: Error | null }> {
	try {
		const { data, error } = await supabase
			.from(TABLE_NAME)
			.select('*')
			.eq('employee_id', employeeId)
			.order('effective_date', { ascending: false });

		if (error) {
			return { data: null, error: new Error(error.message) };
		}

		// Convert snake_case DB fields to camelCase
		const history: CompensationHistory[] = (data || []).map(mapDbToModel);

		return { data: history, error: null };
	} catch (err) {
		return {
			data: null,
			error: err instanceof Error ? err : new Error('Unknown error')
		};
	}
}

/**
 * Get current (active) compensation for an employee.
 * Returns the record where end_date is null.
 */
export async function getCurrentCompensation(
	employeeId: string
): Promise<{ data: CompensationHistory | null; error: Error | null }> {
	try {
		const { data, error } = await supabase
			.from(TABLE_NAME)
			.select('*')
			.eq('employee_id', employeeId)
			.is('end_date', null)
			.single();

		if (error) {
			// PGRST116 = no rows found, not an error
			if (error.code === 'PGRST116') {
				return { data: null, error: null };
			}
			return { data: null, error: new Error(error.message) };
		}

		return { data: mapDbToModel(data), error: null };
	} catch (err) {
		return {
			data: null,
			error: err instanceof Error ? err : new Error('Unknown error')
		};
	}
}

/**
 * Get compensation at a specific date for an employee.
 * Finds the record that was active on that date.
 */
export async function getCompensationAtDate(
	employeeId: string,
	date: string // YYYY-MM-DD
): Promise<{ data: CompensationHistory | null; error: Error | null }> {
	try {
		const { data, error } = await supabase
			.from(TABLE_NAME)
			.select('*')
			.eq('employee_id', employeeId)
			.lte('effective_date', date)
			.or(`end_date.is.null,end_date.gte.${date}`)
			.order('effective_date', { ascending: false })
			.limit(1)
			.single();

		if (error) {
			// PGRST116 = no rows found
			if (error.code === 'PGRST116') {
				return { data: null, error: null };
			}
			return { data: null, error: new Error(error.message) };
		}

		return { data: mapDbToModel(data), error: null };
	} catch (err) {
		return {
			data: null,
			error: err instanceof Error ? err : new Error('Unknown error')
		};
	}
}

/**
 * Update employee compensation.
 * Uses Backend API to ensure transactional consistency.
 */
export async function updateCompensation(
	employeeId: string,
	data: CompensationHistoryCreate
): Promise<{ data: CompensationHistory | null; error: Error | null }> {
	try {
		const result = await api.post<CompensationHistory>(
			`/employees/${employeeId}/compensation`,
			data
		);
		return { data: result, error: null };
	} catch (err) {
		return {
			data: null,
			error: err instanceof Error ? err : new Error('Failed to update compensation')
		};
	}
}

// =============================================================================
// Helper Functions
// =============================================================================

interface DbCompensationRecord {
	id: string;
	employee_id: string;
	compensation_type: 'salary' | 'hourly';
	annual_salary: number | null;
	hourly_rate: number | null;
	effective_date: string;
	end_date: string | null;
	change_reason: string | null;
	created_at: string;
}

/**
 * Map database record (snake_case) to model (camelCase)
 */
function mapDbToModel(record: DbCompensationRecord): CompensationHistory {
	return {
		id: record.id,
		employeeId: record.employee_id,
		compensationType: record.compensation_type,
		annualSalary: record.annual_salary,
		hourlyRate: record.hourly_rate,
		effectiveDate: record.effective_date,
		endDate: record.end_date,
		changeReason: record.change_reason,
		createdAt: record.created_at
	};
}
