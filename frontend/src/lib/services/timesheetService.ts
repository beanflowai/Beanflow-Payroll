import type { TimesheetEntry, TimesheetResponse } from '$lib/types/payroll';
import { supabase } from '$lib/api/supabase';

export interface TimesheetServiceResult {
	data: TimesheetResponse | null;
	error: string | null;
}

/**
 * Get timesheet entries for a payroll record
 */
export async function getTimesheetEntries(payrollRecordId: string): Promise<TimesheetServiceResult> {
	try {
		const { data, error } = await supabase
			.from('timesheet_entries')
			.select('*')
			.eq('payroll_record_id', payrollRecordId)
			.order('work_date');

		if (error) {
			console.error('Failed to fetch timesheet entries:', error);
			return { data: null, error: error.message };
		}

		const entries: TimesheetEntry[] = (data || []).map((row) => ({
			id: row.id,
			workDate: row.work_date,
			regularHours: Number(row.regular_hours),
			overtimeHours: Number(row.overtime_hours)
		}));

		const totalRegularHours = entries.reduce((sum, e) => sum + e.regularHours, 0);
		const totalOvertimeHours = entries.reduce((sum, e) => sum + e.overtimeHours, 0);
		const daysWorked = entries.filter((e) => e.regularHours > 0 || e.overtimeHours > 0).length;

		return {
			data: {
				entries,
				summary: {
					totalRegularHours,
					totalOvertimeHours,
					daysWorked
				}
			},
			error: null
		};
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to fetch timesheet entries';
		console.error('Unexpected error:', err);
		return { data: null, error: message };
	}
}

/**
 * Update timesheet entries for a payroll record (batch upsert)
 * Uses upsert with onConflict to handle atomic updates without delete-then-insert race condition
 */
export async function updateTimesheetEntries(
	payrollRecordId: string,
	entries: TimesheetEntry[]
): Promise<TimesheetServiceResult> {
	try {
		// First, get the payroll record to get employee_id and company_id
		const { data: recordData, error: recordError } = await supabase
			.from('payroll_records')
			.select('employee_id, companies!inner(id)')
			.eq('id', payrollRecordId)
			.single();

		if (recordError || !recordData) {
			return { data: null, error: 'Payroll record not found' };
		}

		const employeeId = recordData.employee_id;
		// Handle Supabase's response type for joined data
		const companies = recordData.companies as any;
		const companyId = Array.isArray(companies) ? companies[0]?.id : companies?.id;
		if (!companyId) {
			return { data: null, error: 'Company not found' };
		}

		// Filter to entries with actual hours (don't store zero-hour entries)
		const entriesToUpsert = entries.filter((e) => e.regularHours > 0 || e.overtimeHours > 0);

		// Get existing entries to identify which ones to delete (entries that were previously saved but now have 0 hours)
		const { data: existingEntries, error: fetchError } = await supabase
			.from('timesheet_entries')
			.select('work_date')
			.eq('payroll_record_id', payrollRecordId);

		if (fetchError) {
			console.error('Failed to fetch existing entries:', fetchError);
			return { data: null, error: fetchError.message };
		}

		const existingDates = new Set((existingEntries || []).map((e) => e.work_date));
		const newDates = new Set(entriesToUpsert.map((e) => e.workDate));

		// Delete entries that now have 0 hours (exist in DB but not in new entries)
		const datesToDelete = [...existingDates].filter((date) => !newDates.has(date));
		if (datesToDelete.length > 0) {
			const { error: deleteError } = await supabase
				.from('timesheet_entries')
				.delete()
				.eq('payroll_record_id', payrollRecordId)
				.in('work_date', datesToDelete);

			if (deleteError) {
				console.error('Failed to delete zero-hour entries:', deleteError);
				return { data: null, error: deleteError.message };
			}
		}

		// Upsert entries with hours (atomic operation - updates if exists, inserts if not)
		if (entriesToUpsert.length > 0) {
			const { error: upsertError } = await supabase
				.from('timesheet_entries')
				.upsert(
					entriesToUpsert.map((e) => ({
						company_id: companyId,
						employee_id: employeeId,
						payroll_record_id: payrollRecordId,
						work_date: e.workDate,
						regular_hours: e.regularHours,
						overtime_hours: e.overtimeHours
					})),
					{
						// Use the unique constraint for conflict resolution
						onConflict: 'employee_id,payroll_record_id,work_date'
					}
				);

			if (upsertError) {
				console.error('Failed to upsert entries:', upsertError);
				return { data: null, error: upsertError.message };
			}
		}

		// Return updated data
		return getTimesheetEntries(payrollRecordId);
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to update timesheet entries';
		console.error('Unexpected error:', err);
		return { data: null, error: message };
	}
}

/**
 * Clear all timesheet entries for a payroll record
 */
export async function clearTimesheetEntries(
	payrollRecordId: string
): Promise<{ error: string | null }> {
	try {
		const { error } = await supabase
			.from('timesheet_entries')
			.delete()
			.eq('payroll_record_id', payrollRecordId);

		if (error) {
			console.error('Failed to clear entries:', error);
			return { error: error.message };
		}

		return { error: null };
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to clear timesheet entries';
		console.error('Unexpected error:', err);
		return { error: message };
	}
}

// ===== Overtime Calculation API =====

import { api } from '$lib/api/client';

/**
 * Request model for overtime calculation
 */
export interface OvertimeCalculateRequest {
	province: string;
	entries: Array<{
		date: string;
		totalHours: number;
		isHoliday: boolean;
	}>;
}

/**
 * Response model for overtime calculation
 */
export interface OvertimeCalculateResponse {
	regularHours: number;
	overtimeHours: number;
	doubleTimeHours: number;
	error?: string; // Present if calculation failed
}

/**
 * Calculate overtime split for daily hours using backend API.
 * This replaces the frontend-only calculation for accuracy and consistency.
 *
 * @param request - Province code and daily hours entries
 * @returns Calculated regular, overtime, and double-time hours
 * @throws Error if API call fails
 */
export async function calculateOvertimeSplit(
	request: OvertimeCalculateRequest
): Promise<OvertimeCalculateResponse> {
	try {
		return await api.post<OvertimeCalculateResponse>('/overtime/calculate', request);
	} catch (error) {
		console.error('Failed to calculate overtime:', error);
		// Return error in response so UI can handle gracefully
		// This allows UI to show error state while preserving last valid values
		const message = error instanceof Error ? error.message : 'Failed to calculate overtime';
		return {
			regularHours: 0,
			overtimeHours: 0,
			doubleTimeHours: 0,
			error: message
		};
	}
}

